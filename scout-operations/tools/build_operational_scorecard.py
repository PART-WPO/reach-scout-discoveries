#!/usr/bin/env python3
"""Authoritative Scout phase scorecard from validated public artifacts.

Keep REACH screening, independent original research, DOI-seeded expansion,
public Scout staging, private Hub review, and public REACH insertion distinct.
Never guess private human outcomes.
"""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUTPUT=ROOT/"scout-operations/scout-operational-scorecard.json"


def load(relative, required=True):
    path=ROOT/relative
    if not path.exists():
        if required:
            raise ValueError("Missing report: "+relative)
        return None,None
    blob=path.read_bytes()
    return json.loads(blob),hashlib.sha256(blob).hexdigest()


def main():
    route,route_sha=load("scout-operations/historical-crossref-screening/actionable-routing.json")
    cross,cross_sha=load("scout-operations/historical-crossref-coverage.json")
    hist,hist_sha=load("scout-operations/historical-coverage.json")
    cross_ex,cross_ex_sha=load("scout-operations/historical-crossref-reconciliation-exceptions.json")
    hist_ex,hist_ex_sha=load("scout-operations/historical-reconciliation-exceptions.json")
    research,research_sha=load("scout-operations/research-decision-rollup.json")
    feed,feed_sha=load("scout-discoveries/manifest.json")
    index,index_sha=load("scout-operations/identity-cache/public-identity-index.json")
    preprints,preprint_sha=load("scout-operations/preprint-watchlist.json")
    expansion_relevance,relevance_sha=load("scout-operations/expansion-relevance-priority.json")
    if expansion_relevance["source_routing_sha256"]!=route_sha:
        raise ValueError("Expansion relevance priorities are stale relative to live REACH routing")
    expansion_counts=expansion_relevance["historical_crossref"]["counts"]
    if (expansion_relevance["historical_crossref"]["total_preserved_seeds"]!=route["total"]
        or sum(expansion_counts.values())!=route["total"]
        or expansion_relevance["source_crossref_manifest_sha256"]!=route["source_manifest_sha256"]
        or expansion_relevance["source_reach_cache_sha256"]!=route["reach_cache_sha256"]):
        raise ValueError("Invalid expansion priority source cohort or verified cache")
    if expansion_counts.get("PRIORITIZE_VERIFIED_WPO_SEED",0)!=route["counts"].get("CONFIRMED_IN_REACH",0):
        raise ValueError("Verified WPO exploration count differs from proven REACH identities")
    for evidence_name,relative in (("monthly_expansion_leads","scout-operations/monthly-expansion-leads.json"),
                                   ("independent_discovery_leads","scout-operations/independent-discovery-leads.json"),
                                   ("scope_reconsiderations","scout-operations/expansion-scope-reconsiderations.json")):
        source_sha=(expansion_relevance.get("other_source_sha256") or {}).get(evidence_name)
        if source_sha!=hashlib.sha256((ROOT/relative).read_bytes()).hexdigest():
            raise ValueError("Stale expansion relevance source: "+relative)
    for relative,expected_sha in (expansion_relevance.get("other_source_sha256") or {}).get("audited_scope_files",{}).items():
        if not relative.startswith("scout-operations/historical-crossref-phase2/") or hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()!=expected_sha:
            raise ValueError("Expansion scope audit checksum mismatch: "+relative)
    if route["total"]!=cross["total_distinct_dois"]:
        raise ValueError("Historical Crossref source cohort mismatch")
    if route["source_manifest_sha256"]!=cross["source_manifest_sha256"]:
        raise ValueError("Source checksum mismatch between REACH routing and research coverage")
    if sum(route["counts"].values())!=route["total"]:
        raise ValueError("Incomplete REACH classification totals")
    if cross_ex["declared_unverified_terminal_count"]!=cross["unverified_terminal_statuses"]:
        raise ValueError("Crossref repair queue mismatches coverage")
    if hist_ex["declared_unverified_terminal_count"]!=hist["unverified_terminal_statuses"]:
        raise ValueError("DataCite repair queue mismatches coverage")
    if feed["batch_count"] != len(feed["batches"]):
        raise ValueError("Scout feed manifest batch count mismatch")
    if index["sources"]["scout_manifest_sha256"]!=feed_sha:
        raise ValueError("Identity index does not match public Scout feed")
    if research["identity_index_fingerprint"]!=index["source_fingerprint"]:
        raise ValueError("Research decision rollup uses stale identity index")
    if research["automatically_staged"]!=0:
        raise ValueError("Research pipeline unexpectedly staged a candidate")
    reach_records=sum(1 for r in index["records"] if r["source"]=="REACH")
    queue_records=sum(1 for r in index["records"] if r["source"]=="SCOUT_PUBLISHED")
    inbox_records=sum(1 for r in index["records"] if r["source"]=="SCOUT_INBOX")
    if queue_records!=feed["candidate_rows"]:
        raise ValueError("Published Scout queue row count mismatches feed")
    if reach_records!=route["reach_source_records"]:
        raise ValueError("REACH identity catalog count mismatch")

    artifacts={"actionable_routing":route_sha,"crossref_research_coverage":cross_sha,
        "datacite_research_coverage":hist_sha,
        "crossref_reconciliation_exceptions":cross_ex_sha,
        "datacite_reconciliation_exceptions":hist_ex_sha,
        "research_decision_rollup":research_sha,
        "scout_published_manifest":feed_sha,
        "shared_identity_index":index_sha,
        "preprint_watchlist":preprint_sha,
        "expansion_relevance":relevance_sha}
    result={
        "schema":"reach-scout-operational-scorecard-v1",
        "source_sha256":artifacts,
        "reach_screening":{"historical_crossref_source_dois":route["total"],
            "confirmed_reach":route["counts"].get("CONFIRMED_IN_REACH",0),
            "likely_reach_needs_bounded_check":route["counts"].get("LIKELY_IN_REACH",0),
            "not_found_in_index_needs_research":route["counts"].get("NOT_FOUND_IN_REACH_INDEX",0),
            "screening_incomplete":route["counts"].get("SCREENING_INCOMPLETE",0),
            "scout_overlap_hints":route["scout_overlap_flagged"]},
        "original_research":{"historical_crossref_completed_verified":cross["originals_completed"],
            "historical_crossref_unverified_declared_completed":cross["unverified_terminal_statuses"],
            "historical_datacite_completed_verified":hist["fully_investigated"],
            "historical_datacite_unverified_declared_completed":hist["unverified_terminal_statuses"],
            "research_evidence_dois_evaluated":research["cases_evaluated"],
            "research_evidence_decisions":research["decision_counts"],
            "research_evidence_next_actions":research["next_action_counts"]},
        "separate_doi_expansion":{"historical_crossref_completed_verified":cross["seed_expansions_completed"],
            "historical_crossref_pending":cross["seed_expansion_pending"],
            "relevance_priority_counts":expansion_counts,
            "monthly_discovered_lead_priority_counts":expansion_relevance["other_discovery_sources"]["monthly_expansion"]["priority_counts"],
            "independent_discovered_lead_priority_counts":expansion_relevance["other_discovery_sources"]["independent_research"]["priority_counts"],
            "relevance_soft_deferred_not_closed":expansion_counts.get("DEFER_UNTIL_NEW_PROJECT_EVIDENCE",0),
            "research_evidence_note":"Relevance is only an exploration priority. Every DOI and prior terminal/expansion status stays recorded; soft deferral is reversible and is not completed or excluded research."},
        "review_pipeline":{"public_scout_staged_proposals":queue_records,
            "public_scout_batches":feed["batch_count"],
            "scout_inbox_draft_rows":inbox_records,
            "private_discovery_hub_imports":"NOT_VERIFIED",
            "human_reviewer_decisions":"NOT_VERIFIED",
            "public_reach_additions_from_scout":"NOT_VERIFIED",
            "public_reach_total_records":reach_records},
        "preprint_watchlist":{"tracked":preprints["metrics"]["preprints_tracked"],
            "on_hold":preprints["metrics"]["preprints_still_waiting_for_official_publication"],
            "verified_published_versions":preprints["metrics"]["preprints_with_verified_published_versions"]},
        "reconciliation":{"crossref_requires_evidence_repair":cross_ex["declared_unverified_terminal_count"],
            "datacite_requires_evidence_repair":hist_ex["declared_unverified_terminal_count"],
            "terminal_claims_automatically_overwritten":0},
        "note":"Progress metrics are stage-specific and SHA-pinned. Private Hub status and public REACH additions are not inferred from the public Scout feed."
    }
    rendered=json.dumps(result,indent=2,ensure_ascii=False)+"\n"
    if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8")!=rendered:
        OUTPUT.write_text(rendered,encoding="utf-8")
    print(json.dumps({"screened":result["reach_screening"],
                      "case_decisions":research["cases_evaluated"],
                      "reconciliation":result["reconciliation"]},indent=2))


if __name__=="__main__":
    main()
