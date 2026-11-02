#!/usr/bin/env python3
"""Generate an actionable monthly original-output decision queue and independent
API-seeded expansion worklist. Research recommendations only: no approvals,
unverified Hub claims, terminal dispositions, or drafts are created here.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TERMINAL = {"already_in_reach", "staged_for_hub_import", "forwarded_to_hub", "metadata_update_forwarded",
            "no_action", "human_metadata_needed"}
OPEN = {"awaiting_research", "investigating", "needs_more_research"}
EXPANSION_STATUSES = {"awaiting_independent_verification", "investigating",
                      "needs_more_research", "ready_for_draft_review",
                      "already_in_reach", "no_action", "staged_for_human_review",
                      "pending_human_intake"}
REQUIRED_GATE_KEYS = {"same_project_wpo_funding_verified", "all_reach_and_scout_identities_checked",
                      "distinct_output_or_canonical_version_verified", "required_metadata_verified"}


def read(root, relative):
    return json.loads((root / relative).read_text(encoding="utf-8"))


def classify(entry):
    """Never infer Hub eligibility from merely matching an award or a DOI."""
    status = entry["status"]
    if status in TERMINAL:
        return "research_terminal", False, []
    if status not in OPEN:
        raise ValueError("Unsupported monthly research status: " + status)

    research = entry.get("substantive_research") or {}
    funding = research.get("funding_assessment") or {}
    identity = research.get("identity_and_related_outputs") or {}
    gate = entry.get("original_output_gate") or {}
    if gate:
        if not REQUIRED_GATE_KEYS.issubset(gate):
            raise ValueError("Incomplete explicit original-output gate: " + entry["identity"])
        if not isinstance(gate.get("checked_sources"), list):
            raise ValueError("Missing gate evidence sources: " + entry["identity"])
    ready = bool(gate and all(gate.get(k) is True for k in REQUIRED_GATE_KEYS)
                 and len(gate["checked_sources"]) >= 2
                 and all(isinstance(s, str) and s.startswith("https://") for s in gate["checked_sources"]))
    if ready:
        return "prepare_validated_candidate_draft", True, []

    blockers = []
    if identity.get("historical_review_unit") or identity.get("duplicate_cross_cohort_seed"):
        return "reconcile_existing_review_unit", False, [
            "One historical concept/version or human-review family exists: never stage a second candidate for this DOI family."
        ]
    if funding.get("same_project_verified") is True:
        if not gate.get("all_reach_and_scout_identities_checked"):
            blockers.append("Finish complete REACH and Scout secondary-link, alternate-DOI, and version-identity dedup.")
        if not gate.get("required_metadata_verified"):
            blockers.append("Verify required output metadata and source-specific publication/release date.")
        if not gate.get("distinct_output_or_canonical_version_verified"):
            blockers.append("Verify distinct work identity and canonical DOI/version.")
        return "original_fast_path_final_checks", False, blockers

    blockers.append("Resolve specific original-output same-project WPO funding with public source evidence, or record a defensible no-action / human-investigation disposition.")
    if funding.get("same_project_verified") is False:
        return "funding_or_scope_decision_due", False, blockers
    return "original_first_pass_or_funding_check", False, blockers


def build(root=ROOT):
    ledger = read(root, "scout-operations/monthly-triage.json")
    expansion = read(root, "scout-operations/monthly-expansion-leads.json")
    if ledger.get("schema") != "reach-scout-monthly-triage-v1":
        raise ValueError("Unexpected monthly triage schema")
    if expansion.get("schema") != "reach-scout-monthly-expansion-leads-v1":
        raise ValueError("Unexpected monthly expansion schema")

    watch_path = root / "scout-operations/preprint-watchlist.json"
    watch = read(root, "scout-operations/preprint-watchlist.json") if watch_path.exists() else {"entries": []}
    if watch.get("schema") not in (None, "reach-scout-preprint-watchlist-v1"):
        raise ValueError("Unrecognized preprint watchlist schema")
    preprints = {"doi:" + x["preprint_doi"].lower() for x in watch.get("entries", [])}
    cases = []
    original_dois = set()
    originals = set()
    counts = {}
    for e in ledger["entries"]:
        key = (e["source_batch_id"], e["identity"])
        if key in originals:
            raise ValueError("Duplicate monthly original: " + e["identity"])
        originals.add(key)
        original_dois.add(e["identity"])
        if e["identity"].lower() in preprints or e.get("publication_status") == "preprint":
            track, draft_gate_passed, blockers = (
                "preprint_watchlist_hold", False,
                ["Do not stage the preprint DOI. Preserve its seeded research and monitor for a verified official article DOI."])
        else:
            track, draft_gate_passed, blockers = classify(e)
        if e["status"] not in TERMINAL and e.get("substantive_research"):
            # A completed first pass and substantial follow-up demand a decision,
            # NOT an automatic terminal status or invented verification.
            decision_due = True
        else:
            decision_due = False
        counts[track] = counts.get(track, 0) + 1
        cases.append({
            "source_batch_id": e["source_batch_id"],
            "identity": e["identity"],
            "cohort": e["cohort"],
            "ledger_status": e["status"],
            "decision_track": track,
            "decision_review_due": decision_due,
            "explicit_draft_gate_passed": draft_gate_passed,
            "unresolved_checks": blockers,
            "next_action": (
                "Use existing validated inbox draft workflow; no private Hub delivery may be assumed."
                if draft_gate_passed else
                "Complete only the named blocker(s), then create evidence-backed candidate / no-action / human referral; do not repeat general discovery scans."
            ),
            "source_evidence_count": len(e.get("checked_sources") or []),
            "original_review_independent_of_expansion": True,
        })

    lead_rows = []
    seen_leads = set()
    for lead in expansion["entries"]:
        identity = lead["identity"].lower()
        seed = "doi:" + lead["original_seed_doi"].lower().removeprefix("doi:")
        if identity in seen_leads:
            raise ValueError("Duplicate expansion lead: " + identity)
        if identity in original_dois:
            raise ValueError("Expansion reuses original DOI identity: " + identity)
        if seed not in original_dois:
            raise ValueError("Unknown original monthly DOI seed for " + identity)
        if lead["origin_method"] != "API-seeded expansion":
            raise ValueError("Incorrect expansion provenance for " + identity)
        if lead["status"] not in EXPANSION_STATUSES:
            raise ValueError("Unsupported expansion lead status for " + identity)
        if not lead["path_evidence_url"].startswith("https://"):
            raise ValueError("Missing seed-to-lead evidence URL for " + identity)
        if lead["status"] == "already_in_reach" and not lead.get("reach_id"):
            raise ValueError("Existing output without REACH identity: " + identity)
        seen_leads.add(identity)
        lead_rows.append({
            "identity": identity,
            "original_seed_doi": lead["original_seed_doi"],
            "status": lead["status"],
            "origin_method": "API-seeded expansion",
            "funding_verified": lead.get("project_funding_verified") is True,
            "full_identity_verified": lead.get("full_reach_and_scout_dedup_verified") is True,
            "source_evidence_url": lead["path_evidence_url"],
            "action": ("Do not restage existing REACH output" if lead["status"] == "already_in_reach"
                       else "Investigate as independent output; never block verified original monthly seed"),
        })

    order = {"preprint_watchlist_hold": 6, "prepare_validated_candidate_draft": 0, "original_fast_path_final_checks": 1,
             "funding_or_scope_decision_due": 2, "original_first_pass_or_funding_check": 3,
             "reconcile_existing_review_unit": 4, "research_terminal": 5}
    cases.sort(key=lambda x: (order[x["decision_track"]], x["identity"]))
    lead_rows.sort(key=lambda x: (x["status"] == "already_in_reach", x["identity"]))
    return {
        "schema": "reach-scout-monthly-decision-queue-v1",
        "policy": "Research routing only. Complete original-output identity/funding/metadata checks promptly, make evidence-backed decision after bounded follow-up; separately investigate linked outputs. No approvals, Hub imports, drafts, or public REACH changes are implied.",
        "original_case_count": len(cases),
        "original_track_counts": counts,
        "decision_review_due_count": sum(c["decision_review_due"] for c in cases),
        "explicit_draft_gate_passed_count": sum(c["explicit_draft_gate_passed"] for c in cases),
        "originals": cases,
        "expansion_lead_count": len(lead_rows),
        "expansion_leads_awaiting_independent_verification": sum(
            x["status"] not in {"already_in_reach", "no_action", "staged_for_human_review"} for x in lead_rows),
        "expansion_leads": lead_rows,
        "human_hub_import_status": "NOT_VERIFIED",
    }


def main():
    result = build()
    path = ROOT / "scout-operations/monthly-decision-queue.json"
    content = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if not path.exists() or path.read_text(encoding="utf-8") != content:
        path.write_text(content, encoding="utf-8")
    print("Decision queue:", result["original_case_count"], "original DOI cases,",
          result["decision_review_due_count"], "due decision review,",
          result["explicit_draft_gate_passed_count"], "explicitly draft-ready,",
          result["expansion_lead_count"], "separate leads")


if __name__ == "__main__":
    main()
