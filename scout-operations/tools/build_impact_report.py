#!/usr/bin/env python3
"""Concise SHA-linked Scout impact report with honestly separated pipeline stages.

No network, no private access, no publishing to REACH/Hub/Smartsheet. This
report describes observed public evidence, not unobserved reviewer outcomes.
"""
import hashlib
import json
from collections import Counter
from pathlib import Path
from source_discovery_metrics import summary as source_discovery_summary

ROOT=Path(__file__).resolve().parents[2]
OUTPUT=ROOT/"scout-operations/scout-v2-impact-report.json"

SOURCE={
    "scorecard":"scout-operations/scout-operational-scorecard.json",
    "unified":"scout-operations/unified-source-preflight.json",
    "repair":"scout-operations/reconciliation-repair-worklist.json",
    "relevance":"scout-operations/expansion-relevance-priority.json",
    "research":"scout-operations/research-decision-rollup.json",
    "workstream":"scout-operations/active-workstream.json",
    "feedback":"scout-operations/research-feedback.json",
    "pilot_pointer":"scout-operations/index-and-project-discovery-leads.json",
    "preprints":"scout-operations/preprint-watchlist.json",
    "preprint_leads":"scout-operations/preprint-publication-leads.json",
    "noaa_ir":"scout-operations/noaa-ir/manifest.json",
    "outcome_registry":"scout-operations/research-outcome-registry.json",
    "doi_recovery":"scout-operations/reports/queued-doi-metadata/latest.json",
    "project_referrals":"scout-operations/human-project-referrals.json",
}

def source(root, rel):
    path=root/rel
    blob=path.read_bytes()
    return json.loads(blob),hashlib.sha256(blob).hexdigest()

def build(root=ROOT):
    records={};shas={}
    for name,rel in SOURCE.items():
        records[name],shas[name]=source(root,rel)
    score=records["scorecard"]
    common=records["unified"]
    repair=records["repair"]
    relevance=records["relevance"]
    research=records["research"]
    workstream=records["workstream"]
    feedback=records["feedback"]
    preprints=records["preprints"]
    preprint_leads=records["preprint_leads"]
    pointer=records["pilot_pointer"]
    registry=records["outcome_registry"]
    recovery=records["doi_recovery"]
    referrals=records["project_referrals"]
    if registry.get("schema")!="reach-scout-all-lane-research-outcomes-v1":
        raise ValueError("Unexpected all-lane research outcome registry schema")
    if recovery.get("schema")!="reach-scout-doi-fallback-queue-v1":
        raise ValueError("Unexpected DOI metadata retry report schema")
    if referrals.get("schema")!="reach-scout-bounded-project-human-referral-v1":
        raise ValueError("Unexpected source-bounded human referral schema")
    if (registry["research_note_events"]!=len(registry["events"]) or
        registry["evidence_files_scanned"]!=len(registry["source_sha256"]) or
        sum(registry["operational_disposition_counts"].values())!=registry["research_note_events"]):
        raise ValueError("Missing or duplicated research outcome event")
    if registry.get("original_status_changes") or registry.get("expansion_status_changes"):
        raise ValueError("Research outcome register modified protected historical statuses")
    if recovery["doi_queue_size"]!=len(recovery["records"]):
        raise ValueError("DOI metadata-recovery queue and result count mismatch")
    if (recovery["metadata_recovered"]!=sum(x["metadata"].get("status")=="ok"
                                              for x in recovery["records"]) or
        recovery.get("new_public_scout_proposals") or recovery.get("new_reach_additions")):
        raise ValueError("DOI fallback report incorrectly reconciles recovery or review state")
    # The rapid human-investigation lane intentionally includes plausible WPO
    # search-context referrals that are NOT formal bounded human questions.
    # Count them separately; never turn a public review draft into approval.
    referral_pool=referrals.get("potential_wpo_cases_quick_screened",
                               referrals["unique_bounded_project_questions"])
    if (referral_pool!=len(referrals["referrals"]) or
        referrals["human_referral_drafts_prevalidated"]!=len(referrals["draft_paths"]) or
        referrals.get("verified_public_scout_referral_batches",0)!=len(referrals.get("published_batch_paths",[])) or
        referrals.get("new_approved_reach_outputs")):
        raise ValueError("Human funding referrals were counted as approved or incomplete")
    human_ids={e["event_id"] for e in registry["events"]
               if e.get("bounded_human_question_to_verify")}
    old_question_drafts=sum(
        r.get("source_event_id") in human_ids and
        r.get("scout_inbox_status") in (
          "VALIDATED_INBOX_DRAFT_NOT_PRIVATE_HUB",
          "EXISTING_VERIFIED_INBOX_DRAFT")
        for r in referrals["referrals"])
    old_question_published=sum(
        r.get("source_event_id") in human_ids and
        r.get("scout_inbox_status")=="PUBLISHED_PUBLIC_SCOUT_FEED_NOT_PRIVATE_HUB"
        for r in referrals["referrals"])
    if old_question_drafts + old_question_published > referrals["unique_bounded_project_questions"]:
        raise ValueError("Verified human question referrals exceed their source questions")
    # After Actions bot commits, downstream reports may temporarily reflect
    # the prior immutable registry snapshot. Flag the freshness precisely.
    recovery_fresh=(recovery["source_registry_sha256"]==shas["outcome_registry"])
    referrals_fresh=(referrals["source_outcome_event_count"]==registry["research_note_events"] and
        referrals["source_outcome_sha256"]==
        hashlib.sha256(json.dumps(registry,sort_keys=True).encode()).hexdigest())
    if any(x.get("private_hub_import")!="NOT_VERIFIED" or
           x.get("human_approval")!="NOT_VERIFIED" for x in referrals["referrals"]):
        raise ValueError("Unverified private reviewer outcome in public referral list")

    if (score.get("schema")!="reach-scout-operational-scorecard-v1"
        or common.get("schema")!="reach-scout-unified-source-preflight-v1"
        or repair.get("schema")!="reach-scout-reconciliation-repair-worklist-v1"
        or feedback.get("schema")!="reach-scout-research-feedback-v1"):
        raise ValueError("Unexpected verified Scout metrics source schema")
    if score["separate_doi_expansion"]["relevance_priority_counts"]!=relevance["historical_crossref"]["counts"]:
        raise ValueError("Stale expansion relevance metrics")
    if score["original_research"]["research_evidence_dois_evaluated"]!=research["cases_evaluated"]:
        raise ValueError("Stale research checkpoint totals")
    if repair["unverified_terminal_cases"]!=(
        score["reconciliation"]["crossref_requires_evidence_repair"]+
        score["reconciliation"]["datacite_requires_evidence_repair"]):
        raise ValueError("Missing repair case or stale historical summary")
    # The hourly workstream is a derived routing suggestion, not the
    # authoritative source of identity/relevance evidence. Report a stale
    # selector as a health warning without hiding reliable source counts.
    workstream_aligned=(workstream["historical_crossref_api"].get("seed_relevance_priority_counts")==
                        relevance["historical_crossref"]["counts"] and
                        workstream["historical_crossref_api"].get("seed_relevance_priority_ready") is True)
    if common["original_and_related_cases_preflighted"]!=sum(
        sum(m.values()) for m in common["lane_decision_counts"].values()):
        raise ValueError("Missing or duplicate preflight case counts")
    if common["identity_index_fingerprint"]!=research["identity_index_fingerprint"]:
        raise ValueError("Shared identity index fingerprint drift")
    if common["authenticated_private_review_event_dois"]!=len({x["doi"] for x in feedback.get("signals",[])}):
        raise ValueError("Private feedback or universal preflight drift")
    if any(x.get("private_hub_action_verified") is not True for x in feedback.get("signals",[])):
        raise ValueError("Unverified private decision in public feedback ledger")
    archived,archive_sha=source(root,pointer["latest_path"])
    if archive_sha!=pointer["latest_sha256"] or pointer["count"]!=len(archived["leads"]):
        raise ValueError("Supplemental Crossref lead archive SHA/count disagreement")
    if archived["new_public_scout_candidates"] or archived["new_reach_additions"]:
        raise ValueError("Supplemental research erroneously claims candidate or REACH insertion")
    if not archived.get("complete_selected_awards"):
        raise ValueError("Incomplete incremental Crossref source retrieval")
    if archived["spark_primary_awards_queried"]+archived["non_normalized_primary_identifiers_skipped"]>archived["spark_primary_awards_in_catalog"]:
        raise ValueError("Invalid SPARK primary award scope metrics")
    if score["review_pipeline"]["private_discovery_hub_imports"]!="NOT_VERIFIED":
        raise ValueError("Scorecard private Hub status must not be inferred from public feed")
    if any(s.get("private_hub_action_verified") and s.get("smartsheet_write_verified") for s in feedback.get("signals",[])):
        raise ValueError("Reviewer feedback is not proof of a Smartsheet API insert")

    actual_private=len(feedback.get("signals",[]))
    stage={
        "historical_crossref_screened":score["reach_screening"]["historical_crossref_source_dois"],
        "verified_existing_reach_public_identities":score["reach_screening"]["confirmed_reach"],
        "ambiguous_reach_identification":score["reach_screening"]["likely_reach_needs_bounded_check"],
        "index_negative_originals_pending_funding":score["reach_screening"]["not_found_in_index_needs_research"],
        "originals_verified_complete_crossref":score["original_research"]["historical_crossref_completed_verified"],
        "originals_verified_complete_datacite":score["original_research"]["historical_datacite_completed_verified"],
        "distinct_crossref_expansions_verified_complete":score["separate_doi_expansion"]["historical_crossref_completed_verified"],
        "source_evidence_decisions_evaluated":research["cases_evaluated"],
        "source_research_notes_scanned":registry["evidence_files_scanned"],
        "source_research_events_reconciled":registry["research_note_events"],
        "distinct_research_identities_with_operational_history":registry["distinct_research_identities"],
        "research_next_action_disposition_counts":registry["operational_disposition_counts"],
        "doi_access_failures_queued_for_metadata_recovery":recovery["doi_queue_size"],
        "doi_metadata_recovered_in_github_action":recovery["metadata_recovered"],
        "doi_metadata_still_pending":recovery["api_retry_or_pending"],
        "bounded_project_questions_identified":referrals["unique_bounded_project_questions"],
        "human_project_question_inbox_drafts_prevalidated":old_question_drafts,
        "rapid_screen_needs_investigation_cases":referral_pool,
        "rapid_screen_needs_investigation_inbox_drafts":referrals["human_referral_drafts_prevalidated"],
        "rapid_screen_public_referral_batches":referrals.get("verified_public_scout_referral_batches",0),
        "human_project_question_published_public_scout_feed":old_question_published,
        "private_human_project_imports":"NOT_VERIFIED",
        "original_or_related_public_preflight_cases":common["original_and_related_cases_preflighted"],
        "cross_cohort_doi_overlaps":common["cross_cohort_duplicate_doi_identities"],
        "terminal_dispositions_under_evidence_repair":repair["unverified_terminal_cases"],
        "public_scout_staged_proposal_rows":score["review_pipeline"]["public_scout_staged_proposals"],
        "public_scout_inbox_draft_rows":score["review_pipeline"]["scout_inbox_draft_rows"],
        "verified_signed_private_review_events":actual_private,
        "private_hub_connection":feedback.get("private_hub_connection_status","NOT_VERIFIED"),
        "private_hub_imports":"NOT_VERIFIED",
        "human_approvals":"NOT_VERIFIED",
        "verified_new_public_reach_additions_from_scout":"NOT_VERIFIED",
    }
    return {
        "schema":"reach-scout-v2-impact-report-v1",
        "source_sha256":dict(sorted(shas.items()))|{"supplemental_index_lead_archive":archive_sha},
        "priority_and_scope":{
            "related_output_relevance_priority_counts":relevance["historical_crossref"]["counts"],
            "phase":workstream.get("phase") if workstream_aligned else "SOURCE_RECONCILIATION_REQUIRED",
            "workstream_relevance_fresh":workstream_aligned,
            "monthly_originals_preempt_historical":True,
            "original_source_and_expansion_stages_separate":True,
        },
        "pipeline":stage,
        "source_driven_related_output_research": source_discovery_summary(root),
        "supplemental_discovery_pilot":{
            "month":pointer["month"],
            "run_mode":archived["run_mode"],
            "validated_award_queries":archived["spark_primary_awards_queried"],
            "valid_noaa_primary_awards_in_catalog":archived["valid_noaa_primary_awards_in_catalog"],
            "nonstandard_awards_skipped":archived["non_normalized_primary_identifiers_skipped"],
            "project_context_queries":archived["project_context_queries"],
            "research_leads_found":len(archived["leads"]),
            "lead_category_counts":archived["counts"],
            "genuinely_wpo_eligible_outputs_verified_from_pilot":"NOT_VERIFIED",
            "monthly_full_catalog_run_verified":archived["run_mode"]=="MONTHLY_COMPLETE_AWARD_COVERAGE",
        },
        "preprints":{
            "metrics":preprints.get("metrics",{}),
            "publication_leads_tracked":len(preprint_leads.get("entries",[])),
            "monthly_first_day_watchlist_only":True,
            "preprint_doi_new_staging_authorized":False,
        },
        "reviewer_quality":{
            "target_human_decisions_per_week":20,
            "verified_last_7_day_human_decisions":"NOT_VERIFIED" if not actual_private else "REQUIRES_TIMESTAMPED_WEEKLY_FILTER",
            "known_verified_feedback_signals":actual_private,
            "reviewer_precision":"NOT_MEASURED_NO_INDEPENDENT_GOLD_STANDARD",
            "eligible_output_recall":"NOT_MEASURED_NO_INDEPENDENT_GOLD_STANDARD",
            "reviewer_minutes_per_accepted_output":"NOT_MEASURED",
        },
        "source_health":{
            "public_reach_catalog_rows":score["review_pipeline"]["public_reach_total_records"],
            "noaa_ir_manifest_sha256":shas["noaa_ir"],
            "sha_verified_report_inputs":True,
            "workstream_selector_status":"CURRENT" if workstream_aligned else "STALE_REBUILD_REQUIRED",
            "doi_metadata_recovery_current_registry_sha":recovery_fresh,
            "project_referrals_current_registry_sha":referrals_fresh,
            "post_research_handoff_status":"CURRENT" if recovery_fresh and referrals_fresh
                                             else "SOURCE_REFRESH_NEEDED",
            "new_research_dispositions_are_not_formal_terminal_completions":True,
        },
        "notes":"Public Scout candidate rows, inbox drafts, signed reviewer feedback, private import, human approval and actual REACH publications are different events. No inferred human outcome or funded-product recovery. Counts describe currently verified public snapshots, not future performance."
    }

def main():
    report=build()
    rendered=json.dumps(report,indent=2,ensure_ascii=False)+"\n"
    if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8")!=rendered:
        OUTPUT.write_text(rendered,encoding="utf-8")
    print(json.dumps({"screened":report["pipeline"]["historical_crossref_screened"],
                      "repair":report["pipeline"]["terminal_dispositions_under_evidence_repair"],
                      "public_review_proposals":report["pipeline"]["public_scout_staged_proposal_rows"],
                      "signed_human_review":report["pipeline"]["verified_signed_private_review_events"],
                      "pilot_leads":report["supplemental_discovery_pilot"]["research_leads_found"]},indent=2))
if __name__=="__main__":main()
