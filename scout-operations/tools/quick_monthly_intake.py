#!/usr/bin/env python3
"""Rapid, risk-based monthly DOI-to-human-review intake.

Requires independently fetched, checksum-verified public REACH & SPARK snapshots.
No network calls in this script, no direct Hub insertion, no human approval.
Separate DOI-seeded research remains independent of original-review intake.
"""
import argparse
import csv
import hashlib
import html
import io
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOI = re.compile(r"10\.\d{4,9}/[^\s\"'<>;,]+", re.I)
AWARD = re.compile(r"NA\d{2}[A-Z0-9-]+", re.I)
URL = re.compile(r"https?://[^\s\"'<>]+", re.I)


class StripTags(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def clean(value):
    parser = StripTags()
    parser.feed(html.unescape(value or ""))
    return " ".join("".join(parser.parts).split())


def norm_title(value):
    return re.sub(r"[^a-z0-9]+", "", clean(value).lower())


def norm_doi(value):
    value = html.unescape(value or "").strip().lower()
    value = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", value)
    found = DOI.search(value)
    return found.group(0).rstrip(".)") if found else ""


def ids_in(text):
    return {norm_doi(m.group(0)) for m in DOI.finditer(html.unescape(text or ""))}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def verify_sha(path, expected):
    if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError("Source SHA mismatch: " + str(path))


def rows_from_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def gather_feed(root, subdir, manifest_rel, section):
    manifest_path = root / manifest_rel
    manifest = read_json(manifest_path)
    files = manifest[section]["files"] if section else manifest["batches"]
    rows = []
    for f in files:
        path = root / f["path"]
        verify_sha(path, f["sha256"])
        data = rows_from_csv(path)
        if len(data) != f.get("rows", f.get("record_count")):
            raise ValueError("Source row count mismatch: " + str(path))
        rows.extend(data)
    return rows, hashlib.sha256(manifest_path.read_bytes()).hexdigest()


def load_external(reach_root, spark_root):
    reach_index, rh = gather_feed(reach_root, "", "agent-data/manifest.json", "index")
    reach_details, _ = gather_feed(reach_root, "", "agent-data/manifest.json", "details")
    spark_index, sh = gather_feed(spark_root, "", "agent-data/manifest.json", "index")
    if len(reach_index) != read_json(reach_root / "agent-data/manifest.json")["source"]["rows"]:
        raise ValueError("Incomplete public REACH index")
    detail_ids = {e["Record ID"] for e in reach_details}
    if detail_ids != {e["Record ID"] for e in reach_index}:
        raise ValueError("REACH detail/index identities disagree")
    return reach_index, reach_details, spark_index, rh, sh


def match_reach(doi, title, url, index, details):
    """Check DOI, normalized title and full secondary/detail fields, not index only."""
    title_key = norm_title(title)
    url_key = (url or "").strip().lower().rstrip("/")
    matches = []
    for row in index + details:
        rid = row.get("Record ID", "")
        checked_cols = ("Title", "Link to Output", "Publications",
                        "Journal Article Link", "Data & Instruments", "Code",
                        "Other Knowledge Products", "Search Combined")
        candidate = "\n".join(str(row.get(k, "") or "") for k in checked_cols)
        doi_hit = doi and doi in ids_in(candidate)
        title_hit = title_key and norm_title(row.get("Title", "")) == title_key
        url_hit = url_key and any(url_key == u.rstrip(".,);").lower().rstrip("/")
                                  for u in URL.findall(candidate))
        if doi_hit or title_hit or url_hit:
            matches.append({"reach_id": rid,
                            "match_basis": "exact_doi" if doi_hit else
                            ("normalized_title" if title_hit else "exact_url")})
    return list({x["reach_id"]: x for x in matches}.values())


def check_funding(row, entry, spark):
    # The harvest has already selected SPARK PRIMARY award matches. Recheck them
    # independently against SPARK primary Award Number(s), NEVER Related Award(s).
    awards = {a.upper() for a in AWARD.findall(row.get("NOAA Award Number(s)", ""))}
    candidates = [r for r in spark if
                  awards & {x.upper() for x in AWARD.findall(r.get("Award Number(s)", ""))}]
    found = {a for r in candidates for a in AWARD.findall(r.get("Award Number(s)", ""))}
    if not awards or not awards.issubset({x.upper() for x in found}):
        return candidates, "unmatched_primary_award", ["Missing matching primary SPARK award"]
    research = entry.get("substantive_research") or {}
    assessment = research.get("funding_assessment") or {}
    # Hold only EXPLICIT contradicting source evidence, not missing independent
    # same-project proof. Lack of an acknowledgement is not a contradiction.
    reason = (assessment.get("reason", "") + " " + assessment.get("publisher_attribution", "")).lower()
    contradiction_tokens = ("different named funding purpose", "different research activities",
                            "materially different", "objectives differ", "land-site",
                            "not aqpi", "different stated project", "project-purpose mismatch",
                            "vs glore", "vs saildrone", "ocean reanalysis/sea ice")
    if any(token in reason for token in contradiction_tokens) or entry.get("funding_anomaly_verified") is True:
        return candidates, "funding_anomaly", ["Explicit conflicting funded-project attribution requires human investigation"]
    # When one source award points to multiple unrelated parent projects, keep
    # all eligible associations but require a reviewer to select the parent.
    unique = {r.get("Record ID") for r in candidates}
    if len(unique) > 1 or len(awards) > 1:
        return candidates, "multiple_project_matches", ["Check award-specific parent projects; do not assign one arbitrarily"]
    return candidates, "primary_award_matched", []


def detect_version(entry, doi):
    relation = (entry.get("substantive_research") or {}).get("identity_and_related_outputs") or {}
    if relation.get("historical_review_unit") or relation.get("duplicate_cross_cohort_seed"):
        return "existing_historical_review_family"
    if relation.get("concept_doi") and relation.get("version_doi"):
        return "concept_version_family"
    return ""


def build(root, reach_root, spark_root, write_drafts=False):
    sys.path.insert(0, str(root / "scout-discoveries/tools"))
    from prepare_batch import prepare
    source = read_json(root / "api-discoveries/manifest.json")
    ledger = read_json(root / "scout-operations/monthly-triage.json")
    reach_index, reach_details, spark, reach_hash, spark_hash = load_external(reach_root, spark_root)
    published, _ = gather_feed(root, "", "scout-discoveries/manifest.json", None)
    inbox = []
    for file in (root / "scout-discoveries/inbox").glob("*.csv"):
        inbox.extend(rows_from_csv(file))
    prior = published + inbox
    existing_dois = {norm_doi(r.get("DOI", "")) for r in prior}
    existing_titles = {norm_title(r.get("Title", "")) for r in prior}
    ledgers = {(e["source_batch_id"], e["identity"]): e for e in ledger["entries"]}
    outcomes, drafts = [], []
    for batch in source["batches"]:
        path = root / batch["path"]
        verify_sha(path, batch["sha256"])
        originals = rows_from_csv(path)
        if len(originals) != batch["record_count"]:
            raise ValueError("Monthly source row count changed")
        for raw in originals:
            doi = norm_doi(raw.get("DOI", ""))
            if not doi:
                raise ValueError("Monthly DOI missing or malformed")
            key = (batch["id"], "doi:" + doi)
            if key not in ledgers:
                raise ValueError("Missing ledger identity: " + doi)
            entry = ledgers[key]
            title = clean(raw.get("Title", ""))
            if not title:
                raise ValueError("Monthly DOI has no title")
            found = match_reach(doi, title, raw.get("Output URL"), reach_index, reach_details)
            funding_matches, funding_status, funding_issues = check_funding(raw, entry, spark)
            issues = list(funding_issues)
            if found:
                status = "already_in_reach"
            elif doi in existing_dois or norm_title(title) in existing_titles:
                status = "already_in_scout_or_inbox"
            elif detect_version(entry, doi):
                status = "cross_cohort_version_review"
                issues.append("Existing DOI/version review must not be duplicated")
            elif funding_status in {"funding_anomaly", "unmatched_primary_award"}:
                status = "funding_exception"
            else:
                missing = [label for label in ("Authors / PI", "Publication Date", "Output Type",
                                                 "Evidence URL", "Funding Evidence URL")
                           if not raw.get(label, "").strip()]
                if not raw.get("Brief Abstract", "").strip():
                    missing.append("Brief Abstract")
                if missing:
                    issues.append("Missing intake fields: " + ", ".join(missing))
                if funding_status == "multiple_project_matches":
                    status = "parent_attribution_review"
                elif missing:
                    status = "metadata_review"
                else:
                    status = "fast_track"
            project = funding_matches[0] if len(funding_matches) == 1 else None
            if project and raw.get("Suggested Parent Project", "").strip():
                if norm_title(raw["Suggested Parent Project"]) != norm_title(project["Project Title"]):
                    issues.append("Source parent and current SPARK title differ; verify")
                    if status == "fast_track":
                        status = "parent_attribution_review"
            output = {"identity": "doi:" + doi, "cohort": entry["cohort"],
                      "status": status, "api_funding_basis": funding_status,
                      "funding_awards": raw.get("NOAA Award Number(s)", ""),
                      "reach_matches": found,
                      "metadata_missing": ([x for x in ("Brief Abstract",)
                                            if not raw.get(x, "").strip()]),
                      "exceptions": issues,
                      "source_batch_id": batch["id"],
                      "review_feed_status": "NOT_STAGED",
                      "private_hub_import": "NOT_VERIFIED",
                      "expansion_required_before_intake": False}
            # No fabricated metadata, no automatic human decision. A metadata-gap
            # candidate can use existing human Needs Investigation review format
            # only if the Hub's existing validated schema accepts the blanks.
            if status in {"fast_track", "metadata_review", "parent_attribution_review"}:
                if not raw.get("Publication Date", "").strip():
                    output["status"] = "metadata_exception"
                else:
                    normalized = dict(raw)
                    normalized["Title"] = title
                    normalized["Candidate ID"] = ""
                    normalized["Principal Investigator Email(s)"] = ""
                    normalized["Existing REACH Match"] = "No DOI/normalized-title/URL match in full verified REACH index + details or published/pending Scout feed."
                    normalized["Scout Confidence"] = "Medium" if status != "fast_track" else "High"
                    normalized["Source Run ID"] = "REACH-SCOUT-MONTHLY-FAST-" + entry["cohort"].replace("-", "")
                    normalized.pop("Scout Discovery Rationale", None)
                    if not normalized.get("Principal Investigators", "").strip():
                        issues.append("PI attribution requires human verification; author names are not assumed to be PIs")
                    if project and not normalized.get("Suggested Parent Project", "").strip():
                        normalized["Suggested Parent Project"] = project["Project Title"]
                    if project and not normalized.get("Proposed Project Title", "").strip():
                        normalized["Proposed Project Title"] = project["Project Title"]
                    if project and not normalized.get("WPO Program", "").strip():
                        normalized["WPO Program"] = project.get("Managing WPO Program", "")
                    funding_source = raw.get("Funding Evidence URL", "")
                    evidence = [raw.get("Evidence URL", ""),
                                "https://github.com/PART-WPO/reach-dashboard/blob/main/agent-data/manifest.json",
                                "https://github.com/PART-WPO/SPARK/blob/main/agent-data/manifest.json"]
                    provenance = {
                        "classification": ("NEW CANDIDATE" if status == "fast_track" else "NEEDS INVESTIGATION"),
                        "route": "Direct API", "origin_method": "Direct API",
                        "path_evidence": funding_source,
                        "intake_origin": "Monthly API",
                        "monthly_intake": entry["cohort"],
                        "reach_snapshot": reach_hash,
                        "sources_checked": evidence,
                        "funding_basis": ("Crossref/DataCite structured grant number(s) "
                                          + raw.get("NOAA Award Number(s)", "") +
                                          " independently matched to SPARK PRIMARY award field. "
                                          "Human reviewer confirms exact funded project."),
                        "related_outputs_checked": "Initial monthly DOI verified independently of related-output expansion. Linked research must be tracked separately, never block intake.",
                        "notes": ["Quick intake: review original DOI before DOI-seeded research expansion",
                                  "Funding context: " + funding_status,
                                  "PI attribution from authors not assumed; human review required."]
                    }
                    if status == "metadata_review":
                        provenance["notes"].append("Missing abstract: human reviewer must recover before REACH publication.")
                    if status == "parent_attribution_review":
                        provenance["notes"].append("Multiple or ambiguous project connections: human reviewer must confirm appropriate funded project.")
                    name = batch["id"][:10] + "-monthly-fast-" + hashlib.sha256((batch["id"]+doi).encode()).hexdigest()[:14] + ".csv"
                    target = root / "scout-discoveries/inbox" / name
                    if target.exists():
                        output["review_feed_status"] = "ALREADY_IN_INBOX"
                    elif write_drafts:
                        structured = root / "scout-operations" / (".quick-monthly-" + hashlib.sha256(doi.encode()).hexdigest()[:14] + ".json")
                        structured.write_text(json.dumps({"candidates": [{"fields": normalized, "provenance": provenance}]}))
                        try:
                            prepare(structured, target)
                        finally:
                            structured.unlink(missing_ok=True)
                        drafts.append(str(target.relative_to(root)))
                        output["review_feed_status"] = "INBOX_DRAFT_PREVALIDATED"
                    else:
                        output["review_feed_status"] = "READY_FOR_VALIDATED_DRAFT"
            outcomes.append(output)
    counts = {}
    for item in outcomes:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    report = {"schema": "reach-scout-monthly-fast-intake-v1",
              "policy": "Monthly originals first; lightweight PRIMARY award provenance check and full snapshot-backed REACH/Scout duplicate screening. API grant metadata is strong review evidence, not human approval or project-level proof.",
              "reach_snapshot_sha256": reach_hash,
              "spark_snapshot_sha256": spark_hash,
              "source_monthly_records": len(outcomes),
              "counts": counts, "originals": outcomes,
              "draft_paths_created": drafts,
              "published_scout_feed_unverified_for_new_drafts": True,
              "private_hub_import": "NOT_VERIFIED",
              "reviewer_approval": "NOT_VERIFIED",
              "public_reach_updates": 0}
    report_path = root / "scout-operations/monthly-fast-intake.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print("Monthly quick intake:", len(outcomes), "DOIs,", counts,
          len(drafts), "new validated inbox drafts; no private Hub import asserted")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reach-root", type=Path, required=True)
    parser.add_argument("--spark-root", type=Path, required=True)
    parser.add_argument("--write-drafts", action="store_true")
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT / "scout-discoveries/tools"))
    build(ROOT, args.reach_root, args.spark_root, args.write_drafts)


if __name__ == "__main__":
    main()
