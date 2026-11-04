#!/usr/bin/env python3
"""Actionable, read-only Crossref-to-REACH gate; never mutates source checkpoints.

Run after the checksum-verified REACH comparison cache and screening batches exist.
This produces a derived routing report; original research and seed-expansion
statuses, human decisions, and public Scout feed are never modified.
"""
import argparse
import csv
import io
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "scout-operations/historical-crossref-screening"
CACHE = ROOT / "scout-operations/reach-comparison-cache/comparison-index.json"
SOURCE = ROOT / "api-discoveries/historical-crossref/manifest.json"
sys.path.insert(0, str(ROOT / "scout-operations/tools"))
from decision_pipeline import build_index, lookup, norm_title

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def doi(value):
    value = str(value or "").strip().lower()
    value = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", value)
    return re.sub(r"^doi:", "", value)

def title(value):
    """Use the shared HTML/XML-aware title normalizer; never index <scp> tokens."""
    return norm_title(value)

def require(condition, message):
    if not condition:
        raise ValueError(message)

def build():
    source = json.loads(SOURCE.read_text())
    screening = json.loads((HERE / "manifest.json").read_text())
    cache = json.loads(CACHE.read_text())
    shared_identity = build_index(ROOT)  # one verified REACH+published Scout+inbox snapshot for all source DOIs
    require(shared_identity["sources"]["reach_cache_sha256"] == sha(CACHE),
            "Shared identity and Crossref routing REACH caches disagree")
    require(screening["source_manifest_sha256"] == sha(SOURCE), "Source snapshot changed")
    require(screening["counts"]["unscreened"] == 0, "Screening checkpoint incomplete")
    require(cache["schema"] == "reach-scout-comparison-cache-v1", "Wrong cache schema")
    require(cache["source_repo"] == "PART-WPO/reach-dashboard", "Wrong REACH source")
    require(len(cache["records"]) == cache["source_records"], "REACH cache row count mismatch")
    require(len({r["reach_uid"] for r in cache["records"]}) == len(cache["records"]), "Duplicate REACH UID")
    require(len(cache.get("verified_shards", [])) >= 150, "Incomplete verified REACH shard listing")
    require(all(re.fullmatch(r"[a-f0-9]{64}", s.get("sha256", "")) for s in cache["verified_shards"]), "Invalid shard digest")
    # The comparison cache is produced by the separate checksum-verifying build
    # workflow. Here we verify the cached source identity and record structure,
    # not falsely claim to have re-fetched all 150 remote shards.
    cache_sha = sha(CACHE)
    reach_by_doi, reach_by_title = {}, {}
    for r in cache["records"]:
        for d in r.get("dois", []):
            reach_by_doi.setdefault(doi(d), []).append(r)
        for link in r.get("links", []):
            m = re.search(r"(?:dx\.)?doi\.org/(10\.\d{4,9}/[^?#\s]+)", link, re.I)
            if m:
                reach_by_doi.setdefault(doi(m.group(1)), []).append(r)
        t = title(r.get("title_normalized") or r.get("title"))
        if t:
            reach_by_title.setdefault(t, []).append(r)
    source_titles = {}
    for batch in source["batches"]:
        p = ROOT / batch["path"]
        require(sha(p) == batch["sha256"], "Crossref source batch SHA mismatch")
        rows = list(csv.DictReader(io.StringIO(p.read_text(encoding="utf-8-sig"))))
        require(len(rows) == batch["record_count"], "Crossref source batch row count mismatch")
        for row in rows:
            d = doi(row.get("DOI"))
            if d:
                source_titles.setdefault(d, set()).add(title(row.get("Title")))
    original = {}
    for b in screening["batches"]:
        p = ROOT / b["path"]
        require(sha(p) == b["sha256"], "Screening batch SHA mismatch: " + str(p))
        obj = json.loads(p.read_text())
        require(obj.get("source_manifest_sha256") == sha(SOURCE), "Screening batch source mismatch")
        require(obj.get("reach_snapshot") == cache["source_csv_sha256_declared"], "Screening batch REACH snapshot mismatch")
        require(len(obj["records"]) == b["record_count"], "Screening batch row count mismatch")
        for row in obj["records"]:
            d = doi(row["doi"])
            require(d not in original, "Duplicate Crossref DOI: " + d)
            original[d] = row
    require(len(original) == screening["counts"]["total"], "Missing Crossref source records")
    results = []
    for d, prior in sorted(original.items()):
        titles = set(source_titles.get(d, set()))
        cached_title = title((prior.get("cache_screening") or {}).get("title"))
        if cached_title:
            titles.add(cached_title)
        titles.discard("")
        t = sorted(titles, key=len, reverse=True)[0] if titles else ""
        matches = {}
        for r in reach_by_doi.get(d, []):
            matches[r["reach_uid"]] = (r, True, False)
        for r in [hit for candidate in titles for hit in reach_by_title.get(candidate, [])]:
            uid = r["reach_uid"]
            previous = matches.get(uid)
            matches[uid] = (r, bool(previous and previous[1]), True)
        if prior["screening_status"] == "CONFIRMED_IN_REACH":
            outcome = "CONFIRMED_IN_REACH"
            route = "SKIP_ORIGINAL_RESEARCH_KEEP_EXPANSION_SEED"
        elif not titles:
            outcome = "SCREENING_INCOMPLETE"
            route = "RECOVER_SOURCE_TITLE_THEN_RESCREEN"
        elif any(hit_doi for _, hit_doi, _ in matches.values()):
            outcome = "LIKELY_IN_REACH"
            route = "VERIFY_MATCHED_DETAIL_ONCE"
        elif matches:
            outcome = "LIKELY_IN_REACH"
            route = "VERIFY_TITLE_VERSION_ONCE"
        else:
            outcome = "NOT_FOUND_IN_REACH_INDEX"
            route = "ADVANCE_TO_FUNDING_AND_METADATA_RESEARCH"
        shared_result = lookup(shared_identity, d, t)
        scout_queue_matches = [
            {"source": hit["source"], "identity": hit["identity"],
             "location": hit["location"], "basis": hit["match_bases"]}
            for hit in shared_result["matches"] if hit["source"].startswith("SCOUT_")
        ]
        results.append({
            "doi": d, "title": t, "outcome": outcome, "route": route,
            "scout_public_queue_matches": scout_queue_matches,
            "scout_public_queue_match_count": len(scout_queue_matches),
            "scout_overlap": bool(prior.get("scout_overlap")),
            "matches": [
                {"reach_uid": uid, "record_id": r["record_id"],
                 "doi_hit": hd, "title_hit": ht, "detail_path": r["detail_path"]}
                for uid, (r, hd, ht) in sorted(matches.items())
            ],
            "previous_screening_status": prior["screening_status"],
        })
    counts = dict(Counter(r["outcome"] for r in results))
    require(sum(counts.values()) == len(original), "Routing totals mismatch")
    return {"schema": "reach-scout-crossref-actionable-routing-v1",
            "source_manifest_sha256": sha(SOURCE),
            "screening_manifest_sha256": sha(HERE / "manifest.json"),
            "reach_cache_sha256": cache_sha,
            "reach_source_manifest_sha256": cache["source_manifest_sha256"],
            "shared_identity_index_fingerprint": shared_identity["source_fingerprint"],
            "public_scout_queue_overlap_dois": sum(bool(r["scout_public_queue_matches"]) for r in results),
            "reach_source_records": cache["source_records"],
            "total": len(results), "counts": counts,
            "scout_overlap_flagged": sum(r["scout_overlap"] for r in results),
            "note": "Negative index comparison advances investigation, not proof of global absence. Existing records remain valid expansion seeds. Likely matches need one bounded detail/version check.",
            "entries": results}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="scout-operations/historical-crossref-screening/actionable-routing.json")
    args = parser.parse_args()
    report = build()
    dest = ROOT / args.output
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"total": report["total"], "counts": report["counts"]}, indent=2))

if __name__ == "__main__":
    main()
