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
    """Count unresolved metadata research, not evidence-complete human handoffs.

    Pending Hub integration remains reportable but must not hold Scout hostage.
    """
    counts={"monthly":0,"historical":0}
    for e in (blockers or {}).get("entries", []):
        if e.get("status") not in {
            "blocked", "retry_due"
        }:
            continue
        cohort=str(e.get("cohort", "")).lower()
        if "monthly" in cohort:
            counts["monthly"]+=1
        elif "historical datacite" in cohort:
            counts["historical"]+=1
    return counts


def _monthly_expansions_pending(queue):
    """Keep source-linked monthly outputs in their own research lane."""
    return sum(1 for entry in (queue or {}).get('entries', [])
               if entry.get('status') in {'awaiting_independent_verification',
                                          'investigating', 'needs_more_research',
                                          'ready_for_draft_review'})


def _attribution_pending(queue):
    return sum(
        1 for e in (queue or {}).get("entries", [])
        if str(e.get("stage", "")).startswith(("queued_", "needs_", "pending_"))
    )


def decide(monthly_manifest,monthly_coverage,historical_manifest,historical_coverage,
           historical_manifest_sha="",monthly_triage=None,historical_triage=None,
           metadata_blockers=None,attribution_followups=None,monthly_expansion_leads=None,
           monthly_decision_queue=None,crossref_manifest=None,crossref_coverage=None,
           crossref_triage=None,crossref_manifest_sha="",crossref_routing=None,
           expansion_scope=None):
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
    monthly_expansions_pending=_monthly_expansions_pending(monthly_expansion_leads)
    original_decisions_due=sum(1 for c in (monthly_decision_queue or {}).get('originals', [])
                               if c.get('decision_review_due') and c.get('ledger_status') not in {
                                   'already_in_reach', 'forwarded_to_hub', 'metadata_update_forwarded',
                                   'no_action', 'human_metadata_needed'})
    originals_for_final_checks=sum(1 for c in (monthly_decision_queue or {}).get('originals', [])
                                  if c.get('decision_track') in {
                                      'prepare_validated_candidate_draft',
                                      'original_fast_path_final_checks'})
    # Historical Crossref is its own durable research + seed-expansion cohort.
    # Never treat a publication already in REACH/Scout as an unusable seed.
    c_total=int((crossref_coverage or {}).get("total_distinct_dois",0))
    c_done=int((crossref_coverage or {}).get("fully_investigated",0))
    c_left=int((crossref_coverage or {}).get("remaining",0))
    c_matched=bool(crossref_manifest_sha and crossref_coverage and
        crossref_coverage.get("source_manifest_sha256")==crossref_manifest_sha)
    c_unreconciled=bool(crossref_manifest) and not c_matched
    c_status=_pending(crossref_triage)
    c_initial=max(c_status["awaiting_research"]+c_status["investigating"],
                  int((crossref_coverage or {}).get("awaiting_research",0))+
                  int((crossref_coverage or {}).get("investigating",0)))
    c_seed_pending=sum(1 for e in (crossref_triage or {}).get("entries",[])
                       if e.get("seed_expansion_status") in {
                           "awaiting_exploration","investigating","needs_more_research"})
    c_followup=max(c_status["needs_more_research"],
        int((crossref_coverage or {}).get("needs_more_research",0)),
        c_left-c_initial,0)
    c_complete=(not crossref_manifest and not crossref_coverage) or bool(
        crossref_coverage and c_matched and
        crossref_coverage.get("research_complete") is True and
        c_left==0 and c_done==c_total)
    # Bulk screening is NOT original research completion. Use this verified
    # identity snapshot to avoid unnecessary original publication re-research.
    # The caller rechecks current cache and IR source hashes before supplying it.
    r_counts=(crossref_routing or {}).get("counts") or {}
    c_identity_ready=bool(c_matched and crossref_routing and
        crossref_routing.get("source_manifest_sha256")==crossref_manifest_sha and
        crossref_routing.get("total")==c_total and
        sum(r_counts.values())==c_total and
        all(isinstance(v,int) and v>=0 for v in r_counts.values()) and
        set(r_counts)<={
            "CONFIRMED_IN_REACH","LIKELY_IN_REACH",
            "NOT_FOUND_IN_REACH_INDEX","SCREENING_INCOMPLETE"})
    c_screened=c_total if c_identity_ready else 0
    scope_counts=((expansion_scope or {}).get("historical_crossref") or {}).get("counts") or {}
    scope_ready=bool(c_identity_ready and expansion_scope and
        expansion_scope.get("source_crossref_manifest_sha256")==crossref_manifest_sha and
        expansion_scope["historical_crossref"].get("total_preserved_seeds")==c_total and
        sum(scope_counts.values())==c_total and
        set(scope_counts)<={"PRIORITIZE_VERIFIED_WPO_SEED",
                            "VERIFY_WPO_PROJECT_SCOPE_FIRST",
                            "DEFER_UNTIL_NEW_PROJECT_EVIDENCE"} and
        scope_counts.get("PRIORITIZE_VERIFIED_WPO_SEED",0)==
            r_counts.get("CONFIRMED_IN_REACH",0))
    # A scheduled future retry does not make an unresolved original DOI cleared.
    # New monthly intake always preempts historical research.
    if monthly_initial:
        mode,phase="monthly_api_triage","initial_research"
        reason="Monthly API records need first-pass, output-specific investigation"
    elif monthly_followup or blockers["monthly"]:
        mode="monthly_api_triage"
        if monthly_followup and original_decisions_due:
            phase="original_decision_fast_path"
            reason="Complete bounded original-output decisions and stage fully verified candidates without waiting for independent expansion"
        else:
            phase="additional_evidence_research"
            reason="Continue unresolved monthly API specific evidence checks or metadata blockers before older awards"
    elif monthly_expansions_pending:
        mode,phase="monthly_api_triage","related_output_expansion_research"
        reason="Continue distinct API-seeded output leads with their own source and WPO funding validation; original seeds need not wait for expansion"
    elif c_initial and c_identity_ready:
        mode,phase="historical_crossref_triage","post_bulk_identity_triage"
        reason=("The historical Crossref DOI identity screen is complete: "
                +str(r_counts.get("CONFIRMED_IN_REACH",0))
                +" verified public REACH identities can skip repeated original funding searches; "
                +str(r_counts.get("LIKELY_IN_REACH",0))
                +" require narrow version/identity checks; "
                +str(r_counts.get("NOT_FOUND_IN_REACH_INDEX",0))
                +" index-negative originals need Scout queue and WPO-funding investigation. "
                "Formal original case completion and separate DOI-seeded expansions remain independent.")
    elif c_initial:
        mode,phase="historical_crossref_triage","initial_research"
        reason="Crossref research pending; first confirm fresh SHA-verified public identity routing before deeper case work"
    elif c_seed_pending or c_followup:
        mode,phase="historical_crossref_triage","seed_expansion_research"
        reason="Prioritize related-output research from historical Crossref seeds, including publications already in REACH"
    elif c_unreconciled or not c_complete:
        mode,phase="historical_crossref_triage","reconcile_research_coverage"
        reason="Historical Crossref cohort requires complete validated ledger and seed coverage"
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
    if mode=="historical_crossref_triage" and scope_ready:
        reason += (" Related-output exploration is now relevance-ranked: "
                   +str(scope_counts.get("PRIORITIZE_VERIFIED_WPO_SEED",0))
                   +" known WPO catalog seeds may receive targeted expansion; "
                   +str(scope_counts.get("VERIFY_WPO_PROJECT_SCOPE_FIRST",0))
                   +" require WPO project-scope checks first; "
                   +str(scope_counts.get("DEFER_UNTIL_NEW_PROJECT_EVIDENCE",0))
                   +" are reversibly deferred pending new attribution evidence. "
                   "All original/expansion histories remain open and unchanged.")
    return {
        "schema":"reach-scout-workstream-v1",
        "mode":mode,"phase":phase,"reason":reason,
        "switch_policy":"monthly original decisions > monthly expansion > historical Crossref original dedup + seed expansion > historical DataCite > attribution follow-ups > normal SPARK discovery",
        "monthly_api":{
            "raw_records":monthly_total,"recorded_received":monthly_received,
            "research_completed":monthly_checked,
            "remaining_or_untracked":monthly_unfinished,
            "initial_cases":monthly_initial,
            "unresolved_followups":monthly_followup,
            "original_decisions_due":original_decisions_due,
            "originals_for_final_checks":originals_for_final_checks,
            "independent_expansion_leads_pending":monthly_expansions_pending,
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
        "historical_crossref_api":{
            "raw_batch_rows":int((crossref_manifest or {}).get("candidate_rows",0)),
            "distinct_dois":c_total,"research_completed":c_done,
            "remaining_or_untracked":max(c_left,1 if c_unreconciled else 0),
            "coverage_matches_source_manifest":c_matched,
            "originals_pending_first_pass":c_total-c_screened if c_identity_ready else c_initial,
            "originals_pending_formal_research":c_initial,
            "identity_screening_complete":c_identity_ready,
            "identity_screened":c_screened,
            "identity_verified_existing_reach":r_counts.get("CONFIRMED_IN_REACH",0) if c_identity_ready else 0,
            "identity_needs_bounded_review":r_counts.get("LIKELY_IN_REACH",0) if c_identity_ready else 0,
            "identity_index_negative_to_research":r_counts.get("NOT_FOUND_IN_REACH_INDEX",0) if c_identity_ready else 0,
            "seed_expansions_pending":c_seed_pending,
            "seed_relevance_priority_ready":scope_ready,
            "seed_relevance_priority_counts":dict(sorted(scope_counts.items())) if scope_ready else {},
            "seed_expansion_soft_deferred_not_completed":
                scope_counts.get("DEFER_UNTIL_NEW_PROJECT_EVIDENCE",0) if scope_ready else 0,
            "unresolved_followups":c_followup
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
    c=read("api-discoveries/historical-crossref/manifest.json")
    cc=read("scout-operations/historical-crossref-coverage.json")
    csha=hashlib.sha256((ROOT/"api-discoveries/historical-crossref/manifest.json").read_bytes()).hexdigest() if c else ""
    routing=read("scout-operations/historical-crossref-screening/actionable-routing.json")
    # Routing is usable only against the exact current source, REACH cache
    # and official NOAA IR DOI index; otherwise fall back to verification.
    if routing:
        sources=[
            ("scout-operations/reach-comparison-cache/comparison-index.json","reach_cache_sha256"),
            ("scout-operations/noaa-ir/manifest.json","noaa_ir_manifest_sha256")]
        for relative,field in sources:
            path=ROOT/relative
            if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest()!=routing.get(field):
                routing=None
                break
    relevance=read("scout-operations/expansion-relevance-priority.json")
    if relevance:
        route_path=ROOT/"scout-operations/historical-crossref-screening/actionable-routing.json"
        if (not route_path.exists() or
            relevance.get("source_routing_sha256")!=hashlib.sha256(route_path.read_bytes()).hexdigest()):
            relevance=None
        else:
            sources=(relevance.get("other_source_sha256") or {})
            for field,relative in (
                ("monthly_expansion_leads","scout-operations/monthly-expansion-leads.json"),
                ("independent_discovery_leads","scout-operations/independent-discovery-leads.json"),
                ("scope_reconsiderations","scout-operations/expansion-scope-reconsiderations.json")):
                p=ROOT/relative
                if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()!=sources.get(field):
                    relevance=None
                    break
    result=decide(m,mc,h,hc,sha,
        monthly_triage=read("scout-operations/monthly-triage.json"),
        historical_triage=read("scout-operations/historical-triage.json"),
        metadata_blockers=read("scout-operations/metadata-blockers.json"),
        attribution_followups=read("scout-operations/attribution-followups.json"),
        monthly_expansion_leads=read("scout-operations/monthly-expansion-leads.json"),
        monthly_decision_queue=read("scout-operations/monthly-decision-queue.json"),
        crossref_manifest=c,crossref_coverage=cc,
        crossref_triage=read("scout-operations/historical-crossref-triage.json"),
        crossref_manifest_sha=csha,crossref_routing=routing,
        expansion_scope=relevance)
    new=json.dumps(result,indent=2,sort_keys=True)+"\n"
    if not OUT.exists() or OUT.read_text(encoding="utf-8")!=new:
        OUT.write_text(new,encoding="utf-8")
    print(json.dumps(result,indent=2))

if __name__=="__main__":main()
