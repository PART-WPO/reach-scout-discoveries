#!/usr/bin/env python3
"""Read-only, evidence-pinned Scout decision pilot. Never stages or closes research."""
import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REG = Path("scout-operations/research-outcome-registry.json")
STRUCT = Path("scout-operations/research-decision-cases.json")
OUT = Path("scout-operations/reports/evidence-to-action-pilot.json")
SCHEMA = "scout-evidence-to-action-pilot-v1"

def digest(data):
    return hashlib.sha256(data).hexdigest()

def load(root, path):
    return json.loads((root / path).read_text(encoding="utf-8"))

def verified_file(root, rel, expected):
    path = (root / rel).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError("Missing or unsafe evidence file: " + str(rel))
    actual = digest(path.read_bytes())
    if actual != expected:
        raise ValueError("Evidence SHA mismatch: " + str(rel))
    return actual

def normalize(doi):
    s = str(doi or "").strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if s.startswith(prefix):
            s = s[len(prefix):]
    return s

def assess(case, structured, events):
    """Conservative bounded decision; statuses are suggestions, never formal dispositions."""
    doi = case["identity"]
    latest = events[-1] if events else {}
    observed = case.get("observed_dispositions", [])
    status = str(structured.get("publication_status") or "NOT_CHECKED").upper()
    matching = structured.get("primary_award_match")
    project = str(structured.get("project_attribution") or "NOT_CHECKED").upper()
    metadata = structured.get("required_metadata_verified") is True
    secondary = structured.get("secondary_identity_checked") is True
    rounds = structured.get("research_rounds", 0)
    exhausted = structured.get("research_budget_exhausted") is True
    latest_disposition = latest.get("operational_disposition", case.get("latest_operational_disposition", "UNKNOWN"))
    prior_preprint = "PREPRINT_MONTHLY_WATCH" in observed
    explicit_preprint = status == "PREPRINT" or latest_disposition == "PREPRINT_MONTHLY_WATCH"
    explicit_reach = latest_disposition == "EXISTING_IN_REACH"
    award_confirmed = matching is True and project in ("VERIFIED_SAME_PROJECT", "CONFIRMED_SAME_PROJECT")
    award_disproved = matching is False or project in ("VERIFIED_DIFFERENT_PROJECT", "DISPROVED")
    evidence_urls = list(dict.fromkeys(str(s) for s in (structured.get("checked_sources") or []) if isinstance(s, str) and s.startswith("https://")))
    gaps = []
    if not structured:
        gaps.append("NO_STRUCTURED_DECISION_EVIDENCE")
    if status not in ("PUBLISHED", "PUBLICLY_RELEASED", "PREPRINT"):
        gaps.append("OFFICIAL_PUBLICATION_STATUS_UNVERIFIED")
    if matching is not True or not award_confirmed:
        gaps.append("EXACT_PRIMARY_AWARD_AND_SAME_PROJECT_UNVERIFIED")
    if not secondary:
        gaps.append("CURRENT_REACH_SCOUT_AND_NOAA_IR_IDENTITY_UNVERIFIED")
    if not metadata:
        gaps.append("REQUIRED_METADATA_UNVERIFIED")

    # No inference that a parent award transfers to child DOI, or that public stage
    # means verified private review. Earlier preprint evidence is a contradiction
    # to investigate if the latest case explicitly says published.
    if explicit_preprint:
        disposition = "PREPRINT_MONTHLY_WATCH"
        action = "Preserve original on monthly watchlist; separately investigate any independently published child DOI."
        owner = "MONTHLY_WATCHLIST"
    elif prior_preprint and status not in ("PUBLISHED", "PUBLICLY_RELEASED"):
        disposition = "PUBLICATION_VERSION_CONFLICT"
        action = "Resolve preprint-to-published version relationship before any new original staging."
        owner = "SCOUT_TARGETED"
    elif explicit_reach:
        disposition = "EXISTING_REACH_KEEP_EXPANSION"
        action = "Do not stage duplicate original; preserve separate related-output expansion."
        owner = "SCOUT_EXPANSION"
    elif award_disproved:
        disposition = "NO_MATCHING_WPO_PROJECT_EVIDENCE"
        action = "Record tested nonmatch; reopen attribution only when independent new same-project primary-award evidence arrives."
        owner = "NEW_EVIDENCE_TRIGGER"
    elif status in ("PUBLISHED", "PUBLICLY_RELEASED") and award_confirmed and secondary and metadata:
        # Structural readiness only; a human still reviews, and source urls
        # must be present. No private Hub state assumed.
        if len(evidence_urls) >= 2:
            disposition = "PROPOSE_FOR_HUMAN_REVIEW_ONLY"
            action = "Present evidence and editable metadata to authorized human staging review; no automatic insertion."
            owner = "HUMAN_REVIEWER"
        else:
            disposition = "TARGETED_SOURCE_VERIFICATION"
            action = "Gather independent source support for recorded publication, identity and funding claims."
            owner = "SCOUT_TARGETED"
    elif latest_disposition == "BOUNDED_PROJECT_QUESTION_FOR_HUMAN" and len(evidence_urls) >= 1:
        disposition = "ONE_BOUNDED_HUMAN_QUESTION"
        action = "Show one exact project-attribution question with source evidence; no reviewer justification required."
        owner = "HUMAN_PROJECT_CHECK"
    elif exhausted or rounds >= 2:
        disposition = "BOUNDED_EVIDENCE_HOLD"
        action = "Do not rerun identical research. Reopen only on a new verified source fingerprint, exact award evidence, or official publication/identity change."
        owner = "NEW_EVIDENCE_TRIGGER"
    else:
        disposition = "TARGETED_VERIFICATION"
        action = "Investigate only the highest-priority unmet evidence gate, using previous note and source fingerprints."
        owner = "SCOUT_TARGETED"

    if not structured and disposition == "TARGETED_VERIFICATION":
        disposition = "STRUCTURED_EVIDENCE_NEEDED"
        action = "Extract structured facts from existing verified notes before initiating additional external research."
        owner = "EVIDENCE_EXTRACTION"
    return {
        "identity": doi, "latest_research_disposition": latest_disposition,
        "suggested_disposition": disposition, "next_owner": owner,
        "exact_next_action": action, "unmet_gates": gaps,
        "existing_event_count": len(events),
        "structured_case_present": bool(structured),
        "checked_source_url_count": len(evidence_urls),
        "research_budget_exhausted": exhausted,
        "automatic_hub_write": False, "formal_original_closed": False,
        "separate_expansion_closed": False,
        "private_hub_state": "NOT_VERIFIED",
        "latest_evidence_path": case.get("latest_evidence_path"),
        "latest_event_id": case.get("latest_event_id"),
    }

def build(root=ROOT):
    reg_raw = (root / REG).read_bytes()
    struct_raw = (root / STRUCT).read_bytes()
    registry = json.loads(reg_raw)
    structured = json.loads(struct_raw)
    if not isinstance(registry.get("cases"), list) or not isinstance(registry.get("events"), list):
        raise ValueError("Registry schema or content missing")
    # This explicitly protects every source note referenced by the registry.
    event_by_id = {}
    for e in registry["events"]:
        verified_file(root, e["source_path"], e["source_sha256"])
        if e["event_id"] in event_by_id:
            raise ValueError("Duplicate research event ID")
        event_by_id[e["event_id"]] = e
    details = {}
    for c in structured["cases"]:
        key = "doi:" + normalize(c.get("doi"))
        if key in details:
            raise ValueError("Duplicate structured DOI")
        for evidence in c.get("source_evidence", []):
            verified_file(root, evidence["path"], evidence["sha256"])
        details[key] = c
    compiled = []
    ids = set()
    for c in registry["cases"]:
        key = c["identity"]
        if key in ids:
            raise ValueError("Duplicate registry identity")
        ids.add(key)
        ev = [event_by_id[x] for x in c["event_ids"]]
        if not ev or c["latest_event_id"] not in c["event_ids"]:
            raise ValueError("Inconsistent registry events for " + key)
        compiled.append(assess(c, details.get(key, {}), ev))
    if len(compiled) != registry["distinct_research_identities"]:
        raise ValueError("Registry identity count mismatch")
    counts = dict(sorted(Counter(x["suggested_disposition"] for x in compiled).items()))
    evidence_count = registry["research_note_events"]
    if evidence_count != len(event_by_id):
        raise ValueError("Registry event count mismatch")
    return {
        "schema": SCHEMA, "read_only": True,
        "registry_sha256": digest(reg_raw),
        "structured_decisions_sha256": digest(struct_raw),
        "distinct_cases_evaluated": len(compiled),
        "research_events_source_sha_verified": evidence_count,
        "structured_case_inputs": len(details),
        "unstructured_identity_cases": sum(not x["structured_case_present"] for x in compiled),
        "disposition_counts": counts,
        "new_human_review_stages": 0, "new_public_reach_additions": 0,
        "private_hub_imports": "NOT_VERIFIED",
        "policy": "Public evidence-based preliminary recommendations only; does not modify formal status, expansion, Hub, human review, or REACH.",
        "cases": compiled
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = build()
    raw = (json.dumps(report, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    if args.check:
        if not (ROOT / OUT).is_file() or (ROOT / OUT).read_bytes() != raw:
            raise SystemExit("Evidence-to-action pilot report is stale or missing")
        print("Pilot source SHA validation and deterministic report PASS")
    else:
        (ROOT / OUT).parent.mkdir(parents=True, exist_ok=True)
        (ROOT / OUT).write_bytes(raw)
        print(json.dumps({"cases": report["distinct_cases_evaluated"], "events": report["research_events_source_sha_verified"], "dispositions": report["disposition_counts"]}))

if __name__ == "__main__":
    main()
