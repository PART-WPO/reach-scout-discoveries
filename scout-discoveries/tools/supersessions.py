"""Read a JSON-defined Scout batch replacement with audit history."""

import json
from pathlib import Path

def get_rules(folder: Path):
    path = folder / "supersessions.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "reach-scout-feed-supersessions-v1":
        raise ValueError("Unexpected replacement rules")
    return data["superseded_batches"]

def approved_batches(folder, entries):
    rules = get_rules(folder)
    by_id = {entry["id"]: entry for entry in entries}
    for old_id, rule in rules.items():
        new_id = rule["replacement_id"]
        if old_id not in by_id or new_id not in by_id:
            raise ValueError("Batch replacement missing")
        if by_id[old_id]["sha256"] != rule["original_sha256"]:
            raise ValueError("Source batch digest changed")
        if rule.get("replacement_kind") == "metadata_refresh":
            verify_metadata_refresh(folder, by_id[old_id], by_id[new_id], rule)
        else:
            verify_rows(folder, by_id[old_id], by_id[new_id], rule["excluded_dois"])
    return [e for e in entries if e["id"] not in rules]

def rows_for(folder, entry):
    import csv
    with (folder.parent / entry["path"]).open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))

def verify_rows(folder, before, after, excluded):
    old_rows = rows_for(folder, before)
    new_rows = rows_for(folder, after)
    retired = {doi.lower() for doi in excluded}
    original = {(row.get("DOI") or "").lower() for row in old_rows}
    if not retired or len(retired) != len(excluded) or not retired.issubset(original):
        raise ValueError("Invalid source DOI exclusions")
    expected = [row for row in old_rows if row["DOI"].lower() not in retired]
    if not expected or new_rows != expected:
        raise ValueError("Replacement does not retain original unaffected rows")


def verify_metadata_refresh(folder, before, after, rule):
    """Allow one exact-DOI evidence enrichment, without changing its identity.

    Existing source CSV files remain immutable. An authorized metadata refresh
    can only update a small fixed set of metadata and review-explanation fields.
    """
    old_rows = rows_for(folder, before)
    new_rows = rows_for(folder, after)
    if len(old_rows) != 1 or len(new_rows) != 1:
        raise ValueError("Metadata refresh must be exactly one source output")
    original, enriched = old_rows[0], new_rows[0]
    if original.get("DOI", "").lower() != rule.get("exact_doi", "").lower():
        raise ValueError("Metadata refresh DOI must match recorded original")
    if original.get("DOI", "").lower() != enriched.get("DOI", "").lower():
        raise ValueError("Metadata refresh cannot change the output identity")
    if set(original) != set(enriched):
        raise ValueError("Metadata refresh changed the required 24-column schema")
    changed = {key for key in original if original[key] != enriched[key]}
    allowlist = {"Brief Abstract", "Funding Evidence URL", "Scout Discovery Rationale"}
    if changed != allowlist:
        raise ValueError("Metadata refresh must change only abstract, evidence and review rationale")
    if original["Brief Abstract"].strip() or len(enriched["Brief Abstract"].strip()) < 60:
        raise ValueError("Metadata refresh is not a justified missing-abstract recovery")
    if enriched["Funding Evidence URL"] != rule.get("authoritative_source_url"):
        raise ValueError("Authoritative funding source URL does not match rule")
    rationale = enriched["Scout Discovery Rationale"]
    mandatory = (
        "Scout classification: NEEDS INVESTIGATION",
        "Scout discovery route: Direct API",
        "Intake origin: Monthly API",
        "Monthly intake: 2026-10",
        "Metadata recovery: Completed",
        "What to check before adding this output:",
        rule["authoritative_source_url"],
    )
    if any(fragment not in rationale for fragment in mandatory):
        raise ValueError("Revised rationale is missing required preserved provenance or reviewer checks")
    for key in ("Source Run ID", "Output URL", "NOAA Award Number(s)",
                "Publication Date", "Existing REACH Match", "Scout Confidence"):
        if original[key] != enriched[key]:
            raise ValueError("Metadata refresh unexpectedly changed " + key)
