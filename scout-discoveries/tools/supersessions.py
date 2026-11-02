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
        if rule.get("replacement_kind") == "review_reclassification":
            verify_review_reclassification(folder, by_id[old_id], by_id[new_id], rule)
        elif rule.get("replacement_kind") == "metadata_refresh":
            verify_metadata_refresh(folder, by_id[old_id], by_id[new_id], rule)
        elif rule.get("replacement_kind") == "reviewer_narrative_correction":
            verify_reviewer_narrative_correction(folder, by_id[old_id], by_id[new_id], rule)
        else:
            verify_rows(folder, by_id[old_id], by_id[new_id], rule["excluded_dois"])
    # One replacement CSV may consolidate several immutable one-row proposals.
    # Require EXACTLY the referenced identities, no extra candidates.
    narrative_groups = {}
    for rule in rules.values():
        if rule.get("replacement_kind") == "reviewer_narrative_correction":
            narrative_groups.setdefault(rule["replacement_id"], []).append(rule["exact_doi"].lower())
    for replacement_id, expected_dois in narrative_groups.items():
        rows = rows_for(folder, by_id[replacement_id])
        actual = [(row.get("DOI") or "").lower() for row in rows]
        if (len(actual) != len(expected_dois) or len(set(actual)) != len(actual)
                or set(actual) != set(expected_dois)):
            raise ValueError("Narrative-only replacement contains unexpected, missing or duplicate DOI identities")
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
    required = {"Brief Abstract", "Scout Discovery Rationale"}
    if not required.issubset(changed) or not changed.issubset(allowlist):
        raise ValueError("Metadata refresh may only recover the missing abstract and adjust source/review rationale")
    if original["Brief Abstract"].strip() or len(enriched["Brief Abstract"].strip()) < 60:
        raise ValueError("Metadata refresh is not a justified missing-abstract recovery")
    # An abstract recovery source need not be the funding source. Retain original
    # funding citation when the abstract comes from a separate trusted index.
    if "Funding Evidence URL" in changed and enriched["Funding Evidence URL"] != rule.get("authoritative_source_url"):
        raise ValueError("Changed funding source URL does not match documented source")
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


def verify_review_reclassification(folder, before, after, rule):
    """Review-ready classification update that is NOT a human approval.

    A completed metadata recovery can close its original NEEDS INVESTIGATION
    reason, while remaining reviewer checks stay explicit. This never changes
    a DOI, output metadata, discovered funding, confidence, source, or
    human decision; source batches remain immutable and the active manifest
    exposes only the latest checked replacement.
    """
    previous = rows_for(folder, before)
    current = rows_for(folder, after)
    if len(previous) != 1 or len(current) != 1:
        raise ValueError("Review reclassification requires one original output")
    original, updated = previous[0], current[0]
    doi = str(rule.get("exact_doi", "")).lower()
    if not doi or original.get("DOI", "").lower() != doi or updated.get("DOI", "").lower() != doi:
        raise ValueError("Review reclassification must preserve exact DOI identity")
    if set(original) != set(updated):
        raise ValueError("Review reclassification changed the canonical 24-column schema")
    changed = {k for k in original if original[k] != updated[k]}
    if changed != {"Scout Discovery Rationale"}:
        raise ValueError("Review reclassification may change only Scout rationale, not output metadata")
    from_text = original["Scout Discovery Rationale"]
    to_text = updated["Scout Discovery Rationale"]
    if ("Scout classification: NEEDS INVESTIGATION" not in from_text
        or "Scout classification: NEW CANDIDATE" not in to_text
        or "Scout finding purpose: needs_investigation" not in from_text
        or "Scout finding purpose: new_output_review" not in to_text
        or "Metadata recovery: Completed" not in from_text
        or len(original.get("Brief Abstract", "").strip()) < 60
        or "What to check before adding this output:" not in to_text):
        raise ValueError("Review reclassification lacks completed recovery, canonical transition or remaining checks")
    expected = (from_text
        .replace("Scout classification: NEEDS INVESTIGATION",
                 "Scout classification: NEW CANDIDATE", 1)
        .replace("Scout finding purpose: needs_investigation",
                 "Scout finding purpose: new_output_review", 1))
    addition = str(rule.get("review_note", "")).strip()
    if (not addition.startswith("Review classification update:")
        or len(addition) < 85
        or to_text != expected + "\n" + addition):
        raise ValueError("Review reclassification may only change canonical labels and append exact audited reason")


def verify_reviewer_narrative_correction(folder, before, after, rule):
    """Audit an append-only reviewer explanation, with no output metadata changes.

    May consolidate one-row source batches into a single replacement batch.
    Earlier batches remain immutable and their exact original SHA is checked
    by approved_batches(); no private human-review state is touched.
    """
    original_rows = rows_for(folder, before)
    candidates = rows_for(folder, after)
    doi = str(rule.get("exact_doi", "")).lower()
    if len(original_rows) != 1 or original_rows[0].get("DOI", "").lower() != doi:
        raise ValueError("Narrative correction must reference one exact original DOI")
    matched = [row for row in candidates if (row.get("DOI") or "").lower() == doi]
    if len(matched) != 1:
        raise ValueError("Narrative replacement must contain the exact original DOI once")
    old, new = original_rows[0], matched[0]
    if set(old) != set(new):
        raise ValueError("Narrative correction changed the required 24-column schema")
    changed = {key for key in old if old[key] != new[key]}
    if changed != {"Scout Discovery Rationale"}:
        raise ValueError("Narrative correction must not change output fields, routing, confidence or decisions")

    previous = old["Scout Discovery Rationale"]
    revised = new["Scout Discovery Rationale"]
    if not revised.startswith(previous + "\n"):
        raise ValueError("Narrative correction must preserve ALL original rationale verbatim")
    added = revised[len(previous) + 1:].splitlines()
    labels = ("Finding:", "What to check before adding this output:", "Reviewer question:")
    expected = [label for label in labels if not any(
        line.startswith(label) for line in previous.splitlines())]
    if len(added) != len(expected) or any(
        not line.startswith(label + " ") for line, label in zip(added, expected)):
        raise ValueError("Narrative correction may append ONLY missing reviewer-story sections")
    for label in labels:
        lines = [line for line in revised.splitlines() if line.startswith(label)]
        if len(lines) != 1 or len(lines[0]) < (80 if label != "Reviewer question:" else 65):
            raise ValueError("Narrative correction has absent, duplicated or generic reviewer explanation")
    finding = next(line for line in revised.splitlines() if line.startswith("Finding:"))
    checks = next(line for line in revised.splitlines() if line.startswith(
        "What to check before adding this output:"))
    question = next(line for line in revised.splitlines() if line.startswith("Reviewer question:"))
    if (("10." not in finding and "NOAA" not in finding)
            or "REACH" not in finding or "SPARK" not in (finding + checks + previous)
            or checks.count(" | ") < 2 or "REACH" not in checks
            or not any(token in checks.lower() for token in ("pub date", "publication date", "date basis", "posted date", "print-month", "crossref", "datacite"))
            or not question.endswith("?")):
        raise ValueError("Reviewer narrative needs DOI/award evidence, REACH comparison, specific checks and a decision question")
    if "Intake origin: Monthly API" not in revised or "Scout discovery route: Direct API" not in revised:
        raise ValueError("Narrative-only replacement must retain original Direct API monthly origin")
