#!/usr/bin/env python3
"""Read-only DOI identity catalog and evidence-gated Scout case checkpoints.

Never writes to REACH, SPARK, a human-decision ledger, or the private Hub.
Only SHA-checked public source data may be indexed. No network calls.
"""
import argparse
import csv
import hashlib
import html
import json
import re
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

VERSION = "reach-scout-decision-pipeline-v2"
DOI_RE = re.compile(r"10\.\d{4,9}/[^\s\"'<>;,]+", re.I)
TITLE_TAGS = re.compile(r"<[^>]*>")
ROOT = Path(__file__).resolve().parents[2]


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha_file(path):
    return sha_bytes(path.read_bytes())


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def norm_doi(value):
    text = html.unescape(str(value or "")).strip().lower()
    text = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", text)
    m = DOI_RE.search(text)
    return m.group(0).rstrip(".,);]") if m else ""


def norm_title(value):
    value = html.unescape(TITLE_TAGS.sub(" ", str(value or "")))
    # Normalize dotted initialisms (U.S., U.S, N.W.S.) before punctuation
    # splitting, without joining unrelated words or dropping ordinary tokens.
    value = re.sub(r"(?<![A-Za-z])(?:[A-Za-z]\.)+[A-Za-z](?:\.)?(?![A-Za-z])",
                   lambda m: m.group(0).replace(".", ""), value)
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def norm_url(value):
    value = html.unescape(str(value or "")).strip()
    if not value.lower().startswith(("https://", "http://")):
        return ""
    u = urlsplit(value)
    if not u.netloc:
        return ""
    return urlunsplit((u.scheme.lower(), u.netloc.lower(), u.path.rstrip("/").lower(), "", ""))


def doi_in(value):
    return set(filter(None, (norm_doi(m.group(0)) for m in DOI_RE.finditer(str(value or "")))))


def demand(condition, message):
    if not condition:
        raise ValueError(message)


def checked_csv(root, relative, expected_hash=None, expected_count=None):
    path = root / relative
    demand(path.resolve().is_relative_to(root.resolve()), "Unsafe source path")
    demand(path.is_file(), "Source missing: " + relative)
    if expected_hash is not None:
        demand(sha_file(path) == expected_hash, "Source SHA mismatch: " + relative)
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if expected_count is not None:
        demand(len(rows) == expected_count, "Source row count mismatch: " + relative)
    return rows


def build_index(root):
    cache_path = root / "scout-operations/reach-comparison-cache/comparison-index.json"
    manifest_path = root / "scout-discoveries/manifest.json"
    cache = read_json(cache_path)
    manifest = read_json(manifest_path)
    demand(cache.get("schema") == "reach-scout-comparison-cache-v1", "Wrong REACH cache schema")
    demand(cache.get("source_repo") == "PART-WPO/reach-dashboard", "Wrong REACH source repo")
    demand(cache.get("source_records") == len(cache.get("records", [])), "Incomplete REACH cache")
    demand(len(set(x.get("reach_uid") for x in cache["records"])) == len(cache["records"]),
           "Duplicate REACH UID in comparison cache")
    demand(len(cache.get("verified_shards", [])) >= 150, "REACH comparison cache lacks full verified shards")
    demand(manifest.get("schema") == "reach-scout-discovery-feed-v1", "Wrong Scout manifest schema")
    demand(manifest.get("batch_count") == len(manifest.get("batches", [])), "Scout manifest batch count mismatch")

    refs = []
    keys = {"doi": defaultdict(list), "url": defaultdict(list), "title": defaultdict(list)}
    def add(source, identity, title, dois, urls, location):
        record = {"source": source, "identity": str(identity), "title": str(title or ""),
                  "dois": sorted(set(filter(None, dois))),
                  "urls": sorted(set(filter(None, urls))), "location": location}
        pos = len(refs)
        refs.append(record)
        for d in record["dois"]:
            keys["doi"][d].append(pos)
        for u in record["urls"]:
            keys["url"][u].append(pos)
        t = norm_title(title)
        if t:
            keys["title"][t].append(pos)

    for rec in cache["records"]:
        links = rec.get("links", []) or []
        dois = {norm_doi(x) for x in rec.get("dois", [])}
        for link in links:
            dois.update(doi_in(link))
        add("REACH", rec["reach_uid"], rec.get("title", ""),
            dois, (norm_url(x) for x in links), rec.get("detail_path", ""))

    feed_batches = manifest["batches"]
    for batch in feed_batches:
        rows = checked_csv(root, batch["path"], batch["sha256"], batch["record_count"])
        for rownum, row in enumerate(rows, 2):
            link = row.get("Output URL", "")
            d = set(doi_in(row.get("DOI", ""))) | doi_in(link)
            add("SCOUT_PUBLISHED", row.get("Candidate ID") or batch["id"] + ":" + str(rownum),
                row.get("Title", ""), d, [norm_url(link)], batch["path"] + ":" + str(rownum))

    inbox_files = []
    inbox = root / "scout-discoveries/inbox"
    demand(inbox.is_dir(), "Missing Scout inbox directory")
    for path in sorted(inbox.glob("*.csv")):
        rel = path.relative_to(root).as_posix()
        rows = checked_csv(root, rel)
        inbox_files.append({"path": rel, "sha256": sha_file(path), "rows": len(rows)})
        for rownum, row in enumerate(rows, 2):
            link = row.get("Output URL", "")
            d = set(doi_in(row.get("DOI", ""))) | doi_in(link)
            add("SCOUT_INBOX", row.get("Candidate ID") or path.name + ":" + str(rownum),
                row.get("Title", ""), d, [norm_url(link)], rel + ":" + str(rownum))
    demand(sum(x["record_count"] for x in feed_batches) == manifest.get("candidate_rows"),
           "Scout manifest total rows mismatch")
    sources = {"reach_cache_sha256": sha_file(cache_path),
               "reach_manifest_sha256": cache["source_manifest_sha256"],
               "scout_manifest_sha256": sha_file(manifest_path),
               "scout_batches": len(feed_batches), "inbox_files": inbox_files}
    return {"schema": "reach-scout-identity-index-v1", "sources": sources,
            "source_fingerprint": sha_bytes(json.dumps(sources, sort_keys=True).encode()),
            "records": refs, "keys": {k: dict(v) for k, v in keys.items()}}


def check_index_fresh(root, index):
    demand(index.get("schema") == "reach-scout-identity-index-v1", "Wrong identity index schema")
    sources = index["sources"]
    demand(sha_file(root / "scout-operations/reach-comparison-cache/comparison-index.json")
           == sources["reach_cache_sha256"], "Stale REACH comparison cache index")
    demand(sha_file(root / "scout-discoveries/manifest.json")
           == sources["scout_manifest_sha256"], "Stale Scout batch index")
    live = sorted(x.relative_to(root).as_posix() for x in (root / "scout-discoveries/inbox").glob("*.csv"))
    old = sorted(x["path"] for x in sources["inbox_files"])
    demand(live == old, "Scout inbox file list changed; rebuild identity index")
    for entry in sources["inbox_files"]:
        demand(sha_file(root / entry["path"]) == entry["sha256"],
               "Scout inbox changed; rebuild identity index: " + entry["path"])
    manifest = read_json(root / "scout-discoveries/manifest.json")
    demand(len(manifest.get("batches", [])) == sources["scout_batches"],
           "Scout manifest batch count changed")
    for batch in manifest["batches"]:
        demand(sha_file(root / batch["path"]) == batch["sha256"],
               "Published Scout batch changed without valid source checksum: " + batch["path"])
    expected = sha_bytes(json.dumps(sources, sort_keys=True).encode())
    demand(expected == index.get("source_fingerprint"), "Index source fingerprint mismatch")


def lookup(index, doi="", title="", url=""):
    d, t, u = norm_doi(doi), norm_title(title), norm_url(url)
    match = defaultdict(set)
    for kind, key in (("doi", d), ("url", u), ("title", t)):
        for pos in (index["keys"][kind].get(key, []) if key else []):
            match[pos].add("exact_" + kind if kind != "title" else "normalized_title")
    found = []
    for pos, bases in sorted(match.items()):
        rec = index["records"][pos]
        found.append({"source": rec["source"], "identity": rec["identity"],
                      "title": rec["title"], "location": rec["location"],
                      "match_bases": sorted(bases)})
    # A shared identity screen must be at least as conservative as the bulk
    # gate: a DOI or URL alone is a lead, not an automatic duplicate.
    # Query title, unique source identity, and a strong identifier must agree.
    # Related datasets, preprints, and published articles must not be merged
    # merely because their titles resemble one another.
    strong = {"exact_doi", "exact_url"}
    reach = [x for x in found if x["source"] == "REACH"]
    scout = [x for x in found if x["source"].startswith("SCOUT_")]

    def uniquely_verified(group):
        return (bool(t) and len({(x["source"], x["identity"]) for x in group}) == 1
                and norm_title(group[0]["title"]) == t
                and bool(strong.intersection(group[0]["match_bases"])))

    def consistent_scout_mirrors(group):
        # GitHub may retain the same previously promoted CSV in both inbox
        # and public batches. The exact DOI/URL AND title must agree for ALL
        # matches before treating this as an existing public proposal.
        # This says nothing about private Hub import or human approval.
        return (bool(t) and bool(group)
                and all(norm_title(x["title"]) == t
                        and bool(strong.intersection(x["match_bases"]))
                        for x in group))

    if reach:
        status = ("CONFIRMED_PUBLIC_REACH_IDENTITY" if uniquely_verified(reach)
                  else "POSSIBLE_PUBLIC_REACH_MATCH")
        reason = ("UNIQUE_STRONG_IDENTIFIER_AND_TITLE" if uniquely_verified(reach)
                  else "MULTIPLE_REACH_IDENTITIES" if len({x["identity"] for x in reach}) > 1
                  else "SOURCE_TITLE_REQUIRED" if not t
                  else "IDENTIFIER_TITLE_OR_VERSION_REVIEW")
    elif scout:
        status = ("IN_PUBLIC_SCOUT_QUEUE" if consistent_scout_mirrors(scout)
                  else "POSSIBLE_SCOUT_QUEUE_MATCH")
        reason = ("CONSISTENT_SCOUT_PUBLIC_MIRRORS" if consistent_scout_mirrors(scout)
                  and len(scout) > 1 else "UNIQUE_STRONG_IDENTIFIER_AND_TITLE"
                  if consistent_scout_mirrors(scout) else "SOURCE_TITLE_REQUIRED"
                  if not t else "IDENTIFIER_TITLE_OR_VERSION_REVIEW")
    else:
        status, reason = "NO_PUBLIC_IDENTITY_MATCH", "NO_MATCH_IN_VERIFIED_PUBLIC_SNAPSHOT"
    return {"status": status, "reason": reason, "matches": found,
            "caveat": "Public snapshot only; private Hub decisions are not asserted."}


def evaluate(case, index):
    d = norm_doi(case.get("doi"))
    demand(d and norm_doi(case.get("doi")) == str(case["doi"]).lower().strip(), "Canonical DOI required")
    cohort = case.get("cohort")
    demand(cohort in {"monthly_api", "historical_crossref", "historical_datacite", "independent"},
           "Unknown cohort")
    status = str(case.get("publication_status") or "NOT_CHECKED")
    demand(status in {"PUBLISHED", "PREPRINT", "NOT_CHECKED"}, "Invalid publication status")
    award = case.get("primary_award_match")
    demand(award in {True, False, None}, "primary_award_match must be true/false/null")
    attribution = case.get("project_attribution", "NOT_CHECKED")
    demand(attribution in {"VERIFIED", "UNRESOLVED", "CONTRADICTED", "NOT_CHECKED"},
           "Invalid project_attribution")
    demand(case.get("research_rounds", 0) in (0, 1, 2), "research_rounds must be 0, 1, or 2")
    urls = case.get("checked_sources", [])
    demand(isinstance(urls, list) and all(str(x).startswith("https://") for x in urls),
           "checked_sources must be HTTPS URLs")
    seen = lookup(index, d, case.get("title", ""), case.get("url", ""))
    private = case.get("private_review_status", "NOT_VERIFIED")
    demand(private in {"NOT_VERIFIED", "NO_KNOWN_PRIOR_DECISION", "EXISTING_HUMAN_DECISION"},
           "Invalid private review status")
    explicit_link_check = case.get("secondary_identity_checked") is True
    complete = case.get("required_metadata_verified") is True
    supported = attribution == "VERIFIED" and len(set(urls)) >= 2
    note = []
    review_action = "NONE"
    if private == "EXISTING_HUMAN_DECISION":
        decision = "RESPECT_EXISTING_HUMAN_DECISION"
    elif seen["status"] == "CONFIRMED_PUBLIC_REACH_IDENTITY":
        decision = "EXISTING_IN_REACH"
    elif seen["status"] == "IN_PUBLIC_SCOUT_QUEUE":
        decision = "EXISTING_SCOUT_CANDIDATE"
    elif seen["matches"]:
        decision = "IDENTITY_REVIEW_REQUIRED"
        note.append("A title or secondary identity match requires bounded manual comparison")
    elif status == "PREPRINT":
        decision = "PREPRINT_HOLD"
    elif status != "PUBLISHED":
        decision = "PUBLICATION_STATUS_UNVERIFIED"
    elif attribution == "CONTRADICTED":
        decision = "NO_DEMONSTRATED_SAME_WPO_PROJECT"
        note.append("Contradictory project-purpose evidence; do not stage on shared grant number")
    elif award is not True:
        decision = "PRIMARY_AWARD_UNVERIFIED"
    elif cohort == "monthly_api" and case.get("structured_funding_evidence_verified") is not True:
        decision = "STRUCTURED_FUNDING_EVIDENCE_REQUIRED"
    elif cohort != "monthly_api" and not supported:
        decision = ("ATTRIBUTION_HOLD_AFTER_BOUNDED_RESEARCH"
                    if case.get("research_rounds", 0) >= 2 else "RESEARCH_PROJECT_BRIDGE")
    elif not explicit_link_check:
        decision = "CANONICAL_IDENTITY_CHECK_REQUIRED"
    elif not complete:
        decision = "METADATA_RECOVERY_REQUIRED"
    else:
        decision = "READY_FOR_VALIDATED_DRAFT_PREFLIGHT"
        review_action = "HUMAN_REVIEW_PROPOSAL"
        if private == "NOT_VERIFIED":
            note.append("Private Hub/history remains unverified; no human import or approval asserted")
    return {"doi": d, "cohort": cohort, "identity_check": seen,
            "project_attribution": attribution, "primary_award_match": award,
            "publication_status": status, "private_review_status": private,
            "research_rounds": case.get("research_rounds", 0),
            "decision": decision, "review_action": review_action, "notes": note,
            "checked_sources": sorted(set(urls)),
            "unverified_private_hub_import": True,
            "automatically_staged": False, "seed_expansion_preserved": True}



def current_checkpoints(index, cases, root=ROOT):
    """Read ONLY the immutable revision for each exact current case+source.

    Historical revisions for the same DOI are retained but must not inflate
    current-run assertions or scorecards.
    """
    found = []
    for case in cases:
        doi = norm_doi(case.get("doi"))
        demand(doi, "Canonical DOI required to identify checkpoint")
        signature = sha_bytes(json.dumps({
            "case": case, "index": index["source_fingerprint"],
            "version": VERSION}, sort_keys=True).encode())
        id_hash = sha_bytes(doi.encode())[:16]
        path = root / "scout-operations/case-checkpoints" / ("doi-" + id_hash) / (
            "rev-" + signature[:20] + ".json")
        demand(path.is_file(), "Current case checkpoint missing: " + str(path))
        record = read_json(path)
        demand(record.get("case_input") == case and
               record.get("input_fingerprint") == signature and
               record.get("index_fingerprint") == index["source_fingerprint"],
               "Current case checkpoint fingerprint does not agree: " + str(path))
        found.append(record)
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    sub = parser.add_subparsers(dest="command", required=True)
    b = sub.add_parser("build-index")
    b.add_argument("--output", default="scout-operations/identity-cache/public-identity-index.json")
    l = sub.add_parser("lookup")
    l.add_argument("--index", default="scout-operations/identity-cache/public-identity-index.json")
    l.add_argument("--doi", default="")
    l.add_argument("--title", default="")
    l.add_argument("--url", default="")
    e = sub.add_parser("evaluate")
    e.add_argument("--index", default="scout-operations/identity-cache/public-identity-index.json")
    e.add_argument("--cases", required=True)
    e.add_argument("--output-dir", default="scout-operations/case-checkpoints")
    args = parser.parse_args()
    root = args.root.resolve()
    if args.command == "build-index":
        index = build_index(root)
        dest = root / args.output
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists() or read_json(dest) != index:
            dest.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps({"records": len(index["records"]), "sources": index["sources"]["scout_batches"],
                          "fingerprint": index["source_fingerprint"]}, indent=2))
        return
    index = read_json(root / args.index)
    check_index_fresh(root, index)
    if args.command == "lookup":
        print(json.dumps(lookup(index, args.doi, args.title, args.url), indent=2))
        return
    payload = read_json(root / args.cases)
    demand(payload.get("schema") == "reach-scout-decision-cases-v1", "Wrong decision cases schema")
    results = []
    out = root / args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    for case in payload.get("cases", []):
        evaluation = evaluate(case, index)
        signature = sha_bytes(json.dumps({"case": case, "index": index["source_fingerprint"],
                                           "version": VERSION}, sort_keys=True).encode())
        id_hash = sha_bytes(evaluation["doi"].encode())[:16]
        dest = out / ("doi-" + id_hash) / ("rev-" + signature[:20] + ".json")
        record = {"schema": "reach-scout-decision-checkpoint-v1",
                  "decision_contract": VERSION,
                  "input_fingerprint": signature, "index_fingerprint": index["source_fingerprint"],
                  "case_input": case, "evaluation": evaluation,
                  "source_case_path": args.cases,
                  "human_decision_modified": False}
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            demand(read_json(dest) == record, "Existing immutable checkpoint mismatch: " + str(dest))
        else:
            dest.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        results.append({"doi": evaluation["doi"], "decision": evaluation["decision"],
                        "checkpoint": dest.relative_to(root).as_posix()})
    print(json.dumps({"evaluated": len(results), "results": results}, indent=2))


if __name__ == "__main__":
    main()
