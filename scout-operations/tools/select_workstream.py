#!/usr/bin/env python3
"""Choose Scout's next research workstream from GitHub-backed API backlog state.

This is a deterministic *routing recommendation*, not a Scout run, review
decision, or evidence of finished research. Runs during coverage refreshes.
"""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"scout-operations/active-workstream.json"

def read(rel):
    p=ROOT/rel
    if not p.exists():return None
    return json.loads(p.read_text(encoding="utf-8"))

def _pending(entries, key=None):
    """Count only unresolved API research entries; preserve distinct cohorts."""
    counts={"awaiting_research":0,"investigating":0,"needs_more_research":0}
    for e in (entries or {}).get("entries", []):
        status=e.get("status")
        if status in counts:
            counts[status]+=1
    return counts


def _blocker_counts(blockers):
    """A pending metadata handoff is still work; human-approved intake is not."""
    counts={"monthly":0,"historical":0}
    for e in (blockers or {}).get("entries", []):
        if e.get("status") not in {
            "blocked", "retry_due", "human_metadata_needed", "pending_hub_handoff"
        }:
            continue
        cohort=str(e.get("cohort", "")).lower()
        if "monthly" in cohort:
            counts["monthly"]+=1
        elif "historical datacite" in cohort:
            counts["historical"]+=1
    return counts


def _attribution_pending(queue):
    return sum(
        1 for e in (queue or {}).get("entries", [])
        if str(e.get("stage", "")).startswith(("queued_", "needs_", "pending_"))
    )


def decide(monthly_manifest,monthly_coverage,historical_manifest,historical_coverage,
           historical_manifest_sha="",monthly_triage=None,historical_triage=None,
           metadata_blockers=None,attribution_followups=None):
    monthly_total=int((monthly_manifest or {}).get("candidate_rows",0))
    monthly_checked=int((monthly_coverage or {}).get("checked",0))
    monthly_received=int((monthly_coverage or {}).get("received",0))
    monthly_missing=int((monthly_coverage or {}).get("missing_from_ledger",0))
    monthly_unfinished=max(0,monthly_total-monthly_checked,
                           monthly_received-monthly_checked,monthly_missing)
    m_status=_pending(monthly_triage)
    h_status=_pending(historical_triage)
    blockers=_blocker_counts(metadata_blockers)
    monthly_initial=max(
        m_status["awaiting_research"]+m_status["investigating"]+monthly_missing,
        monthly_unfinished-m_status["needs_more_research"],
        0
    )
    monthly_followup=max(m_status["needs_more_research"],
                         max(0,monthly_unfinished-monthly_initial))
    hist_rows=int((historical_manifest or {}).get("candidate_rows",0))
    h_total=int((historical_coverage or {}).get("total_distinct_dois",0))
    h_done=int((historical_coverage or {}).get("fully_investigated",0))
    h_left=int((historical_coverage or {}).get("remaining",0))
    hist_matches=bool(historical_manifest_sha and historical_coverage and
        historical_coverage.get("source_manifest_sha256")==historical_manifest_sha)
    hist_complete=(not historical_manifest and not historical_coverage) or (
        bool(historical_coverage) and hist_matches and
        historical_coverage.get("research_complete") is True and
        h_left==0 and h_done==h_total)
    historical_initial=max(
        h_status["awaiting_research"]+h_status["investigating"],
        int((historical_coverage or {}).get("awaiting_research",0))+
        int((historical_coverage or {}).get("investigating",0))
    )
    historical_followup=max(
        h_status["needs_more_research"],
        int((historical_coverage or {}).get("needs_more_research",0)),
        h_left-historical_initial,0
    )
    historical_unreconciled=(bool(historical_manifest) and not hist_matches)
    attribution_pending=_attribution_pending(attribution_followups)
    # A scheduled future retry does not make an unresolved original DOI cleared.
    # New monthly intake always preempts historical research.
    if monthly_initial:
        mode,phase="monthly_api_triage","initial_research"
        reason="Monthly API records need first-pass, output-specific investigation"
    elif monthly_followup or blockers["monthly"]:
        mode,phase="monthly_api_triage","additional_evidence_research"
        reason="Continue monthly API original-record follow-ups and linked-output evidence recovery before older awards"
    elif historical_initial:
        mode,phase="historical_api_triage","initial_research"
        reason="Historical DataCite records await their first individual investigation"
    elif historical_followup or historical_unreconciled or blockers["historical"]:
        mode,phase="historical_api_triage","additional_evidence_research"
        reason="Prioritize unresolved historical DataCite DOI follow-ups and linked-output metadata recovery; future retry dates are NOT clearance"
    elif not hist_complete:
        # Missing or incompatible coverage is a research reconciliation blocker.
        mode,phase="historical_api_triage","reconcile_research_coverage"
        reason="Historical DataCite backlog has not been defensibly closed"
    elif attribution_pending:
        mode,phase="historical_api_triage","attribution_followups"
        reason="Finish bounded API-related award-attribution follow-ups before older-award discovery"
    else:
        mode,phase="normal_historical_discovery","normal_discovery"
        reason="Monthly and historical API research and handoffs are clear"
    return {
        "schema":"reach-scout-workstream-v1",
        "mode":mode,"phase":phase,"reason":reason,
        "switch_policy":"monthly first-pass > monthly follow-ups > historical first-pass > historical follow-ups > attribution follow-ups > normal SPARK historical discovery",
        "monthly_api":{
            "raw_records":monthly_total,"recorded_received":monthly_received,
            "research_completed":monthly_checked,
            "remaining_or_untracked":monthly_unfinished,
            "initial_cases":monthly_initial,
            "unresolved_followups":monthly_followup,
            "pending_metadata_blockers_including_originals":blockers["monthly"]
        },
        "historical_api":{
            "raw_batch_rows":hist_rows,"distinct_dois":h_total,
            "research_completed":h_done,
            "remaining_or_untracked":max(h_left,1 if historical_unreconciled else 0),
            "coverage_matches_source_manifest":hist_matches,
            "initial_cases":historical_initial,
            "unresolved_followups":historical_followup,
            "pending_metadata_blockers_including_originals":blockers["historical"]
        },
        "attribution_followups_pending":attribution_pending,
        "note":"Future follow-up dates do not clear API research. Make bounded distinct-source checks now; use documented early-retry exceptions as needed. An unavailable or invalid Hub metadata-needed handoff remains outstanding. This selector does NOT conduct research, verify human approval, or launch Scout."
    }


def main():
    m=read("api-discoveries/manifest.json")
    mc=read("scout-operations/coverage.json")
    h=read("api-discoveries/historical/manifest.json")
    hc=read("scout-operations/historical-coverage.json")
    sha=hashlib.sha256((ROOT/"api-discoveries/historical/manifest.json").read_bytes()).hexdigest() if h else ""
    result=decide(m,mc,h,hc,sha,
        monthly_triage=read("scout-operations/monthly-triage.json"),
        historical_triage=read("scout-operations/historical-triage.json"),
        metadata_blockers=read("scout-operations/metadata-blockers.json"),
        attribution_followups=read("scout-operations/attribution-followups.json"))
    new=json.dumps(result,indent=2,sort_keys=True)+"\n"
    if not OUT.exists() or OUT.read_text(encoding="utf-8")!=new:
        OUT.write_text(new,encoding="utf-8")
    print(json.dumps(result,indent=2))

if __name__=="__main__":main()
