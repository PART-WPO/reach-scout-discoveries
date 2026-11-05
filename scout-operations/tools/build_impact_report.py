#!/usr/bin/env python3
"""Concise SHA-linked Scout impact report with honestly separated pipeline stages.

No network, no private access, no publishing to REACH/Hub/Smartsheet. This
report describes observed public evidence, not unobserved reviewer outcomes.
"""
import hashlib
import json
from collections import Counter
from pathlib import Path

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
    if workstream["historical_crossref_api"]["seed_relevance_priority_counts"]!=relevance["historical_crossref"]["counts"]:
        raise ValueError("Workstream source and relevance are inconsistent")
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
            "phase":workstream.get("phase"),
            "monthly_originals_preempt_historical":True,
            "original_source_and_expansion_stages_separate":True,
        },
        "pipeline":stage,
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
