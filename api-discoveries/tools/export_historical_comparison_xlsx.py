#!/usr/bin/env python3
"""Read-only historical DataCite vs Scout Excel comparison; no ingestion or approvals.

Reuses the repository's monthly OOXML exporter for deterministic Excel formatting.
The 2026-10-28 DataCite cohort remains immutable. The comparison is a refreshable
public snapshot of Scout's research ledger, NOT evidence of a human decision.
"""
import argparse
import collections
import csv
import datetime as dt
import hashlib
import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "api-discoveries" / "tools"))
import export_comparison_xlsx as excel

COHORT = "2026-10-28"
REPORT_PATH = ROOT / "api-discoveries" / "reports" / (
    "REACH_DataCite_Historical_" + COHORT + "_Scout_Comparison.xlsx"
)
SOURCE_MANIFEST = ROOT / "api-discoveries/historical/manifest.json"
SOURCE_RUN = ROOT / "api-discoveries/runs" / ("historical-datacite-" + COHORT + ".json")
TRIAGE = ROOT / "scout-operations/historical-triage.json"
SCOUT_MANIFEST = ROOT / "scout-discoveries/manifest.json"
KIND = excel.KIND

HEADERS = {
    "Historical DataCite Results": [
        "DOI", "Title", "Output Type", "NOAA Award Number(s)", "WPO Program",
        "Proposed Project", "API Publication Date", "Creators / Authors",
        "Brief Abstract", "DataCite Evidence URL", "Original API Batch",
        "API Review Status",
    ],
    "Scout DOI Comparison": [
        "DOI", "Title", "API Award Number(s)", "Scout Research Status",
        "Scout's Finding / Reason", "Already in REACH / Match",
        "WPO Awards Independently Verified", "Scout Follow-up Due",
        "Missing Evidence", "Scout Review Batch (if staged)",
        "Linked Outputs Scout Checked", "Scout Public Evidence URL",
        "Original DataCite Evidence URL", "Scout Last Updated",
    ],
    "Related Scout Findings": [
        "Original API Seed DOI", "Related Output DOI / URL", "Related Output Title",
        "Award Number(s)", "Scout Discovery Route", "Review Stage",
        "Scout Confidence", "Scout Evidence URL", "Scout Batch",
        "Source Run ID",
    ],
    "Awards with API Matches": [
        "Award Number", "Unique API DOIs", "Already in REACH",
        "Sent to Scout Review", "Metadata Update Proposed", "No Action",
        "Further Research", "Program(s)", "Project(s)",
    ],
    "Scout Status Breakdown": [
        "Scout Research Status", "Original DataCite DOIs", "What This Means",
    ],
}
excel.WIDTHS.update({
    "Summary": [38, 84],
    "Historical DataCite Results": [36, 59, 21, 43, 30, 60, 19, 40, 75, 53, 70, 34],
    "Scout DOI Comparison": [35, 58, 40, 27, 78, 49, 40, 28, 65, 76, 72, 65, 61, 24],
    "Related Scout Findings": [36, 51, 63, 39, 24, 39, 19, 61, 78, 55],
    "Awards with API Matches": [32, 18, 21, 24, 28, 17, 22, 45, 64],
    "Scout Status Breakdown": [34, 23, 89],
    "Read Me": [37, 109],
})

STATUS_TEXT = {
    "already_in_reach": "Already represented in REACH",
    "forwarded_to_hub": "Sent to Discovery Hub for review",
    "metadata_update_forwarded": "Existing REACH metadata update proposed",
    "no_action": "No addition recommended based on current evidence",
    "needs_more_research": "Further research scheduled; not cleared",
    "human_metadata_needed": "Human metadata assistance needed; not approved",
    "investigating": "Research in progress",
    "awaiting_research": "Awaiting Scout investigation",
}
STATUS_DESC = {
    "already_in_reach": "Scout located the output or its version-family in REACH; no duplicate addition is implied.",
    "forwarded_to_hub": "Scout proposed the original API DOI for human review; not approved or added to public REACH.",
    "metadata_update_forwarded": "Existing REACH output may need a change, such as adding a supported award; not a new output.",
    "no_action": "Original record was investigated and excluded or had no sufficiently supported WPO project connection.",
    "needs_more_research": "Possible output, but required dates, eligibility, unique identity or project attribution are unresolved.",
    "human_metadata_needed": "Evidence suggests a relevant output but missing required details need human help.",
    "investigating": "Not a completed research decision.",
    "awaiting_research": "Not yet investigated by Scout.",
}


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def normalized_doi(value):
    s = str(value or "").strip().lower()
    s = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", s)
    return s


def values(value):
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if value:
        return [str(value).strip()]
    return []


def public_url(*candidates):
    for value in candidates:
        for item in values(value):
            if item.startswith(("https://", "http://")):
                return item
    return ""


def awards(value):
    return sorted({x.strip() for x in str(value or "").split(",") if x.strip()})


def checked_csvs(manifest):
    if manifest.get("schema") != "reach-historical-api-feed-v1":
        raise ValueError("Unexpected historical DataCite manifest schema")
    seen, records = set(), []
    for batch in manifest["batches"]:
        path = str(batch["path"])
        if not re.fullmatch(r"api-discoveries/historical/batches/[\w.-]+\.csv", path):
            raise ValueError("Unsafe DataCite batch path: " + path)
        data = (ROOT / path).read_bytes()
        if hashlib.sha256(data).hexdigest() != batch["sha256"]:
            raise ValueError("Historical source checksum mismatch: " + path)
        reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig"), newline=""))
        rows = list(reader)
        if len(rows) != batch["record_count"]:
            raise ValueError("Historical source batch count mismatch: " + path)
        if not {"DOI", "Title", "NOAA Award Number(s)", "Evidence URL"}.issubset(reader.fieldnames or []):
            raise ValueError("Missing expected DataCite batch columns")
        for row in rows:
            doi = normalized_doi(row["DOI"])
            if not re.fullmatch(r"10\.\d{4,9}/[^\s]+", doi):
                raise ValueError("Unexpected historical DOI: " + doi)
            if doi in seen:
                raise ValueError("Duplicate original DOI in historical source: " + doi)
            seen.add(doi)
            row["_doi"] = doi
            row["_batch"] = path
            records.append(row)
    if len(records) != manifest["candidate_rows"]:
        raise ValueError("Historical source manifest row count mismatch")
    return sorted(records, key=lambda row: row["_doi"])


def triage_by_doi(path):
    raw = load_json(path)
    if raw.get("schema") != "reach-scout-historical-triage-v1":
        raise ValueError("Unexpected Scout historical triage schema")
    mapping = {}
    for item in raw["entries"]:
        identity = str(item.get("identity", "")).strip().lower()
        if not identity.startswith("doi:"):
            raise ValueError("Triage entry without canonical DOI identity")
        doi = normalized_doi(identity[4:])
        if doi in mapping:
            raise ValueError("Duplicate Scout triage DOI: " + doi)
        mapping[doi] = item
    return mapping


def related_scout_findings(source_dois):
    manifest = load_json(SCOUT_MANIFEST)
    results = []
    seen = set()
    for batch in manifest["batches"]:
        path = str(batch["path"])
        if not re.fullmatch(r"scout-discoveries/batches/[\w.-]+\.csv", path):
            raise ValueError("Unsafe staged Scout batch path")
        data = (ROOT / path).read_bytes()
        if hashlib.sha256(data).hexdigest() != batch["sha256"]:
            raise ValueError("Published Scout batch checksum mismatch: " + path)
        rows = list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"), newline="")))
        if len(rows) != batch["record_count"]:
            raise ValueError("Scout batch row count mismatch: " + path)
        for row in rows:
            rationale = row.get("Scout Discovery Rationale", "") or ""
            route = re.search(r"(?im)^[ \t]*Scout discovery route:[ \t]*([^\r\n]+)", rationale)
            seed = re.search(r"(?im)^[ \t]*Scout seed DOI:[ \t]*(10\.\d{4,9}/[^\s\r\n]+)", rationale)
            if not route or route.group(1).strip().lower() != "api-seeded expansion" or not seed:
                continue
            seed_doi = normalized_doi(seed.group(1))
            if seed_doi not in source_dois:
                continue
            identity = normalized_doi(row.get("DOI")) or row.get("Output URL", "").strip()
            key = (seed_doi, identity, path)
            if key in seen:
                continue
            seen.add(key)
            results.append([
                "https://doi.org/" + seed_doi,
                ("https://doi.org/" + identity) if identity.startswith("10.") else identity,
                row.get("Title", ""), row.get("NOAA Award Number(s)", ""),
                "API-seeded expansion", "Staged for human review; decision not verified",
                row.get("Scout Confidence", ""),
                public_url(row.get("Evidence URL"), row.get("Funding Evidence URL")),
                "https://github.com/PART-WPO/reach-scout-discoveries/blob/main/" + path,
                row.get("Source Run ID", ""),
            ])
    return sorted(results, key=lambda x: (x[0], x[1]))


def make_report(target):
    manifest = load_json(SOURCE_MANIFEST)
    run = load_json(SOURCE_RUN)
    source = checked_csvs(manifest)
    triage = triage_by_doi(TRIAGE)
    source_dois = {row["_doi"] for row in source}
    if source_dois != set(triage):
        missing = sorted(source_dois - set(triage))
        extra = sorted(set(triage) - source_dois)
        raise ValueError("Scout triage does not match original DataCite cohort: missing={}, extra={}".format(missing[:5], extra[:5]))
    if len(source) != run["distinct_dois"]:
        raise ValueError("Source DOI count differs from original API run summary")
    award_pairs = sum(len(awards(row["NOAA Award Number(s)"])) for row in source)
    if award_pairs != run["matched_award_output_pairs"]:
        raise ValueError("Award/DOI count differs from original API run summary")

    status_count = collections.Counter()
    source_rows, comparison = [], []
    per_award = collections.defaultdict(lambda: {
        "dois": set(), "status": collections.Counter(), "programs": set(), "projects": set()
    })
    updates = []
    for row in source:
        doi = row["_doi"]
        info = triage[doi]
        status = info.get("status", "awaiting_research")
        status_count[status] += 1
        updated = info.get("updated_at", "")
        if updated:
            updates.append(updated)
        original_awards = awards(row["NOAA Award Number(s)"])
        for award in original_awards:
            x = per_award[award]
            x["dois"].add(doi)
            x["status"][status] += 1
            x["programs"].update(awards(row.get("WPO Program", "")))
            if row.get("Proposed Project Title"):
                x["projects"].add(row["Proposed Project Title"])
        evidence = public_url(row.get("Evidence URL"), row.get("Output URL"))
        source_rows.append([
            "https://doi.org/" + doi, row.get("Title", ""),
            KIND.get(str(row.get("Output Type", "")), "Other output"),
            row.get("NOAA Award Number(s)", ""), row.get("WPO Program", ""),
            row.get("Proposed Project Title", ""),
            row.get("Publication Date", ""), row.get("Authors / PI", ""),
            row.get("Brief Abstract", ""), evidence,
            "https://github.com/PART-WPO/reach-scout-discoveries/blob/main/" + row["_batch"],
            "Unreviewed raw DataCite API record",
        ])
        staged_path = info.get("scout_batch_path", "")
        comparison.append([
            "https://doi.org/" + doi, row.get("Title", ""),
            row.get("NOAA Award Number(s)", ""),
            STATUS_TEXT.get(status, status.replace("_", " ").title()),
            info.get("research_notes", "") or info.get("reason", ""),
            info.get("reach_match", ""),
            ", ".join(values(info.get("verified_awards"))),
            info.get("next_research_at", ""),
            "; ".join(values(info.get("missing_evidence"))),
            ("https://github.com/PART-WPO/reach-scout-discoveries/blob/main/" + staged_path)
            if staged_path.startswith("scout-discoveries/batches/") else "",
            info.get("related_outputs_checked", ""),
            public_url(info.get("source_evidence_urls"), info.get("checked_sources")),
            evidence, updated,
        ])
    related = related_scout_findings(source_dois)
    status_rows = [
        [STATUS_TEXT.get(k, k.replace("_", " ").title()), n,
         STATUS_DESC.get(k, "Check Scout's public research ledger for evidence and limitations.")]
        for k,n in sorted(status_count.items(), key=lambda kv: (-kv[1], kv[0]))
    ]
    award_rows = []
    for award,x in sorted(per_award.items()):
        c = x["status"]
        award_rows.append([
            award, len(x["dois"]), c["already_in_reach"], c["forwarded_to_hub"],
            c["metadata_update_forwarded"], c["no_action"],
            c["needs_more_research"] + c["investigating"] + c["awaiting_research"]
            + c["human_metadata_needed"],
            ", ".join(sorted(x["programs"])), "; ".join(sorted(x["projects"])),
        ])
    summary = [
        ["REACH HISTORICAL DATACITE COMPARISON", "Original API findings versus Scout's current public research status"],
        ["Historical API cohort", COHORT + " (all publication years; not a publication-date window)"],
        ["Award identifiers searched in original API run", run["unique_awards_checked_per_api"]],
        ["Unique DOI records returned by DataCite", len(source)],
        ["Award + DOI matches in original API results", award_pairs],
        ["Awards with one or more API matches", len(per_award)],
        ["Raw DataCite records with API-proven full publication date", sum(bool(r.get("Publication Date")) for r in source)],
        ["Original DOIs with completed Scout research", sum(status_count[x] for x in
            ("already_in_reach", "forwarded_to_hub", "metadata_update_forwarded", "no_action"))],
        ["Original DOIs awaiting follow-up or investigation", len(source) - sum(status_count[x] for x in
            ("already_in_reach", "forwarded_to_hub", "metadata_update_forwarded", "no_action"))],
        ["Original DOIs already represented in REACH", status_count["already_in_reach"]],
        ["Original API DOIs proposed for human review", status_count["forwarded_to_hub"]],
        ["Existing REACH metadata updates proposed", status_count["metadata_update_forwarded"]],
        ["Original API DOIs with evidence-backed no action", status_count["no_action"]],
        ["Related outputs staged through Scout expansion", len(related)],
        ["Scout research snapshot latest update (UTC)", max(updates) if updates else "Not available"],
        ["Source DataCite run", run["run"]],
        ["Source SPARK snapshot SHA-256", run["SPARK_source_sha256"]],
        ["Source API batches", manifest["batch_count"]],
        ["Public REACH additions", "NOT inferred from Scout or API records; see REACH Dashboard"],
        ["Purpose", "Read-only comparison; no human decisions, approvals, Smartsheet edits, or Hub imports"],
    ]
    notes = [
        ["How to use this workbook", "Explanation"],
        ["Historical DataCite Results", "One row per distinct original DOI returned by the October 28, 2026 historical DataCite award-number search. All 188 are retained, with their source award numbers, type, title and API evidence."],
        ["Scout DOI Comparison", "Join the same original DOI to Scout's public investigation ledger. Status and rationale can change as research continues. A recommended candidate is NOT human-approved."],
        ["Related Scout Findings", "Only separately staged Scout findings that explicitly record API-seeded expansion and an original seed DOI in this historical cohort. Does not include unverified research leads or claim completeness beyond direct API searches."],
        ["Awards with API Matches", "Per-award counts of the original 188 DOIs. The full list of the 761 identifiers with zero results is NOT in the immutable CSV intake, so this tab includes only matching awards."],
        ["Scout Status Breakdown", "Research dispositions for the original DataCite records. No-action may mean a grant notice, a true duplicate/version family, unsuitable scope or insufficient project-specific attribution. Read the evidence."],
        ["Dates", "The historical raw API batches deliberately have blank publication dates until independently verified. Observation years, DOI registration dates and guessed years must NOT be used as publication dates."],
        ["Multiple awards", "One DOI may cite multiple NOAA award numbers: 188 unique DOI rows but 212 award+DOI matches. Award tab totals are not distinct publication totals."],
        ["Discovery expansion", "A related article/dataset/code found by Scout is a distinct candidate only if its identity and funding connection have been separately checked; published Hub staging does not prove approval."],
        ["Scope", "DataCite-only historical backfill, not Crossref; not a comprehensive set of all WPO outputs. Missing award metadata and grant-only matches affect recall and precision."],
        ["Source snapshot", "DataCite: api-discoveries/historical/manifest.json; original run: api-discoveries/runs/historical-datacite-2026-10-28.json; Scout: scout-operations/historical-triage.json."],
        ["Review privacy", "Does not read or infer private Discovery Hub reviewer decisions. Values reflect public Scout research ledgers only."],
        ["Automatic refresh", "The GitHub Actions historical report workflow refreshes this report on schedule; the original API CSV batches are immutable."],
        ["Data provenance", "https://github.com/PART-WPO/reach-scout-discoveries/tree/main/api-discoveries/historical"],
        ["Human review feed", "https://github.com/PART-WPO/reach-scout-discoveries/blob/main/scout-discoveries/manifest.json"],
    ]
    sheets = {
        "Summary": summary,
        "Historical DataCite Results": [HEADERS["Historical DataCite Results"]] + source_rows,
        "Scout DOI Comparison": [HEADERS["Scout DOI Comparison"]] + comparison,
        "Related Scout Findings": [HEADERS["Related Scout Findings"]] + related,
        "Awards with API Matches": [HEADERS["Awards with API Matches"]] + award_rows,
        "Scout Status Breakdown": [HEADERS["Scout Status Breakdown"]] + status_rows,
        "Read Me": notes,
    }
    # Deterministic ZIP ensures unchanged research state does not cause new commits.
    target.parent.mkdir(parents=True, exist_ok=True)
    # The comparison is a CURRENT, replaceable report. Unlike immutable source
    # batches, replacing an older report is correct when Scout's ledger changes.
    if target.exists():
        target.unlink()
    excel.make_xlsx(target, sheets)
    with __import__("zipfile").ZipFile(target) as z:
        expected = len(sheets)
        if len([n for n in z.namelist() if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", n)]) != expected:
            raise ValueError("Excel report sheet count failed post-export validation")
        if z.testzip() is not None:
            raise ValueError("Excel report ZIP validation failed")
    print(json.dumps({
        "output": str(target), "sheets": list(sheets),
        "original_dois": len(source), "award_doi_matches": award_pairs,
        "scout_triage_dois": len(triage), "staged_api_expansions": len(related),
        "status_counts": dict(status_count), "latest_research_update": max(updates) if updates else None
    }, indent=2))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", default="")
    args = p.parse_args()
    make_report(Path(args.output) if args.output else REPORT_PATH)


if __name__ == "__main__":
    main()
