"""Consumer-side, read-only human-decision awareness.

Only exact DOI-specific, previously authenticated signed feedback is
considered. Prior review is a HOLD on blindly re-proposing the same DOI,
not a claim of current public REACH publication or project ineligibility.
"""
import json
from pathlib import Path

def known_feedback_by_doi(root):
    path=Path(root)/"scout-operations/research-feedback.json"
    if not path.exists():return {}
    payload=json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema")!="reach-scout-research-feedback-v1":
        raise ValueError("Unknown reviewer feedback schema")
    if payload.get("signals") and payload.get("private_hub_connection_status")!="SIGNED_EXPORT_VALIDATED":
        raise ValueError("Reviewer signals without authenticated Hub export provenance")
    by_doi={}
    for e in payload.get("signals", []):
        if (e.get("source")!="SIGNED_PRIVATE_DISCOVERY_HUB_EXPORT"
            or e.get("private_hub_action_verified") is not True
            or e.get("automatically_staged") is True
            or not str(e.get("doi","")).startswith("10.")
            or not e.get("candidate_id") or not e.get("event_id")):
            raise ValueError("Unverified or malformed reviewer feedback signal")
        doi=e["doi"]
        old=by_doi.get(doi)
        if old is None or (e.get("reviewed_at",""),e["event_id"]) > (
                old.get("reviewed_at",""),old["event_id"]):
            by_doi[doi]=e
    return by_doi

def reviewer_hold_for_proposal(doi,known):
    e=known.get(doi)
    if not e:
        return None
    return {"status":"prior_human_review_requires_reconciliation",
            "review_event_id":e["event_id"],
            "last_private_review_code":e["decision_code"],
            "decision_source":"SIGNED_PRIVATE_HUB_EXPORT_ONLY",
            "action":"Check the prior reviewed candidate and any new version/metadata evidence before another public proposal. Do not auto-reject, approve, or infer a REACH publication."}
