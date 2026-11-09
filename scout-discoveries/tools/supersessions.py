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
        if rule.get("replacement_kind") == "wpo_award_confirmation":
            verify_wpo_award_confirmation(folder, by_id[old_id], by_id[new_id], rule)
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



def verify_wpo_award_confirmation(folder, before, after, rule):
    """Reclassify exactly one existing review unit after official same-DOI 459 proof.

    Neither source batch nor research note is overwritten. A new SHA-checked
    public batch replaces the old manifest entry; a human still owns private
    review and the selection of a SPARK parent. Never mint a second DOI unit.
    """
    import hashlib
    import re

    source_path = str(rule.get("evidence_path") or "")
    evidence_dir = (folder.parent / "scout-operations/award-attribution-confirmations").resolve()
    proof_file = (folder.parent / source_path).resolve()
    if not source_path.startswith("scout-operations/award-attribution-confirmations/") or (
        proof_file.parent != evidence_dir or not proof_file.is_file()
    ):
        raise ValueError("Missing approved source-grounded WPO attribution evidence")
    proof = json.loads(proof_file.read_text(encoding="utf-8"))
    if proof.get("schema") != "reach-scout-official-wpo-award-confirmation-v1":
        raise ValueError("Invalid WPO confirmation evidence schema")
    doi = str(rule.get("exact_doi") or "").lower()
    award = str(rule.get("confirmed_wpo_award") or "").upper()
    if not re.fullmatch(r"NA\d{2}OARX?459C?\d{4,}(?:-[A-Z0-9]+)?", award):
        raise ValueError("WPO confirmation must use a complete exact OAR459 grant")
    if (doi != proof.get("doi") or award != proof.get("exact_output_wpo_award")
        or proof.get("official_metadata_provider") != "crossref"
        or proof.get("private_hub_import") != "NOT_VERIFIED"
        or proof.get("human_approval") != "NOT_VERIFIED"):
        raise ValueError("Exact DOI, official provenance or human status mismatch")
    source_url = "https://api.crossref.org/works/" + doi
    if (proof.get("publisher_deposited_funding_url") != source_url
        or rule.get("authoritative_source_url") != source_url
        or not str(proof.get("publisher_article_url") or "").startswith("https://journals.ametsoc.org/")):
        raise ValueError("Missing same-DOI publisher/Crossref source provenance")
    refs = proof.get("same_doi_funding_references") or []
    if not any(award in (x.get("award") or []) for x in refs if isinstance(x, dict)):
        raise ValueError("Crossref deposited funding references do not prove this 459 award")
    old_source_path = str(proof.get("original_research_evidence_path") or "")
    original_source = (folder.parent / old_source_path).resolve()
    if (not old_source_path.startswith("scout-operations/historical-crossref-phase2/")
        or original_source.parent != (folder.parent / "scout-operations/historical-crossref-phase2").resolve()
        or not original_source.is_file()
        or hashlib.sha256(original_source.read_bytes()).hexdigest() !=
           proof.get("original_research_evidence_sha256")):
        raise ValueError("The original append-only publisher research source has changed")
    note = json.loads(original_source.read_text(encoding="utf-8"))
    if (str(note.get("original_doi") or "").lower() != doi
        or str(note.get("structured_award") or "").upper() != award
        or proof.get("title") != note.get("title")):
        raise ValueError("Confirmed award contradicts primary original-output research")
    old_rows, new_rows = rows_for(folder, before), rows_for(folder, after)
    if len(old_rows) != 1 or len(new_rows) != 1:
        raise ValueError("WPO reclassification must be exactly one review unit")
    old, new = old_rows[0], new_rows[0]
    if (old.get("DOI", "").lower() != doi or new.get("DOI", "").lower() != doi
        or new.get("Title") != proof.get("title")
        or proof.get("original_reviewer_batch_path") != before["path"]
        or set(old) != set(new)):
        raise ValueError("WPO reclassification cannot change review identity or schema")
    changed = {k for k in old if old[k] != new[k]}
    if changed != {"NOAA Award Number(s)", "Funding Evidence URL", "Scout Discovery Rationale"}:
        raise ValueError("WPO reclassification may only change award, its proof and review narrative")
    if old["NOAA Award Number(s)"] or old["Funding Evidence URL"]:
        raise ValueError("Original review candidate already made an award claim")
    if new["NOAA Award Number(s)"] != award or new["Funding Evidence URL"] != source_url:
        raise ValueError("New verified funding field must use only this exact official 459 award")
    previous = old["Scout Discovery Rationale"]
    revised = new["Scout Discovery Rationale"]
    required_previous = (
        "Scout verification: Completed",
        "Scout classification: NEEDS INVESTIGATION",
        "Scout finding purpose: needs_investigation",
        "Scout discovery route: Independent discovery",
    )
    required_new = (
        "Scout verification: Completed",
        "Scout classification: NEW CANDIDATE",
        "Scout finding purpose: new_output_review",
        "Scout discovery route: Independent discovery",
        "Scout screening score: 70/100 (Medium)",
        "WPO funding connection: CONFIRMED",
        "Reviewer selects and verifies the SPARK parent",
        source_url, award,
        source_path,
        "Private Hub import and any prior unsynchronized review remain NOT VERIFIED.",
    )
    if any(t not in previous for t in required_previous) or any(t not in revised for t in required_new):
        raise ValueError("Official correction failed to preserve required evidence/review labels")
    for label in ("Scout discovery path evidence:", "Scout origin method:", "Scout discovery route:",
                  "Scout verification:", "Source Run ID:"):
        for line in previous.splitlines():
            if line.startswith(label) and line not in revised.splitlines():
                raise ValueError("Correction lost immutable original source provenance")
    if ("Scout classification: NEEDS INVESTIGATION" in revised or
        "Scout finding purpose: needs_investigation" in revised or
        revised.count("Reviewer question:") != 1 or
        revised.count("What to check before adding this output:") != 1 or
        proof.get("reviewer_question") not in revised):
        raise ValueError("Corrected public reviewer action or classification is ambiguous")
    if new.get("Suggested Parent Project") or new.get("Proposed Project Title"):
        raise ValueError("Do not automatically select the protected SPARK/Smartsheet parent")
    if (new["Source Run ID"] != old["Source Run ID"] or
        new["Existing REACH Match"] != old["Existing REACH Match"]):
        raise ValueError("Correction cannot change candidate identity or duplicate evidence")


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
