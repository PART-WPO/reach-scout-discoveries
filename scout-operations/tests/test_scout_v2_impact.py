"""Scout 2.0 stage metrics and representative blinded evaluation checks."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from build_impact_report import build
from build_scout_v2_benchmark import create
from score_private_benchmark import score

class ReportingTests(unittest.TestCase):
    def test_stage_separation_and_source_consistency(self):
        x=build()
        p=x["pipeline"]
        source=json.loads((Path(__file__).resolve().parents[1]/
            "scout-operational-scorecard.json").read_text())
        repair=json.loads((Path(__file__).resolve().parents[1]/
            "reconciliation-repair-worklist.json").read_text())
        self.assertEqual(p["historical_crossref_screened"],source["reach_screening"]["historical_crossref_source_dois"])
        self.assertEqual(p["verified_existing_reach_public_identities"],source["reach_screening"]["confirmed_reach"])
        self.assertEqual(p["ambiguous_reach_identification"],source["reach_screening"]["likely_reach_needs_bounded_check"])
        self.assertEqual(p["index_negative_originals_pending_funding"],source["reach_screening"]["not_found_in_index_needs_research"])
        self.assertEqual(p["distinct_crossref_expansions_verified_complete"],source["separate_doi_expansion"]["historical_crossref_completed_verified"])
        self.assertEqual(p["terminal_dispositions_under_evidence_repair"],repair["unverified_terminal_cases"])
        self.assertEqual(p["source_research_events_reconciled"],
            sum(p["research_next_action_disposition_counts"].values()))
        self.assertGreaterEqual(p["source_research_notes_scanned"],p["source_evidence_decisions_evaluated"])
        self.assertEqual(p["doi_access_failures_queued_for_metadata_recovery"],
                         p["doi_metadata_recovered_in_github_action"]+p["doi_metadata_still_pending"])
        self.assertLessEqual(p["human_project_question_inbox_drafts_prevalidated"]+
                             p["human_project_question_published_public_scout_feed"],
                             p["bounded_project_questions_identified"])
        self.assertGreaterEqual(p["human_project_question_published_public_scout_feed"],0)
        self.assertEqual(p["private_human_project_imports"],"NOT_VERIFIED")
        referrals=json.loads((Path(__file__).resolve().parents[1]/"human-project-referrals.json").read_text())
        self.assertEqual(p["rapid_screen_needs_investigation_cases"],
                         referrals.get("potential_wpo_cases_quick_screened",
                                       referrals["unique_bounded_project_questions"]))
        self.assertEqual(p["rapid_screen_needs_investigation_inbox_drafts"],
                         referrals["human_referral_drafts_prevalidated"])
        self.assertLessEqual(p["human_project_question_inbox_drafts_prevalidated"]+
                             p["human_project_question_published_public_scout_feed"],
                             p["bounded_project_questions_identified"])
        self.assertEqual(p["private_hub_imports"],"NOT_VERIFIED")
        self.assertTrue(x["source_health"]["new_research_dispositions_are_not_formal_terminal_completions"])
        self.assertIn(x["source_health"]["post_research_handoff_status"],
                      {"CURRENT","SOURCE_REFRESH_NEEDED"})
        self.assertEqual(p["private_hub_imports"],"NOT_VERIFIED")
        self.assertEqual(p["verified_new_public_reach_additions_from_scout"],"NOT_VERIFIED")
        self.assertEqual(x["reviewer_quality"]["target_human_decisions_per_week"],20)
        self.assertEqual(x["reviewer_quality"]["reviewer_precision"],"NOT_MEASURED_NO_INDEPENDENT_GOLD_STANDARD")
        self.assertTrue(x["supplemental_discovery_pilot"]["research_leads_found"]>=0)
        self.assertEqual(x["supplemental_discovery_pilot"]["genuinely_wpo_eligible_outputs_verified_from_pilot"],"NOT_VERIFIED")
    def test_100_cases_without_invented_gold_labels(self):
        x=create()
        self.assertEqual(x["sample_size"],100)
        self.assertEqual(len(x["cases"]),100)
        self.assertEqual(len({c["case_id"] for c in x["cases"]}),100)
        self.assertEqual(x["human_truth_labels_collected"],0)
        self.assertEqual(x["strata_counts"],{
            "known_reach_identity":20,"ambiguous_identity":20,
            "index_negative_original":20,"preprint_version_family":10,
            "monthly_original":10,"historical_datacite":10,
            "independent":5,"monthly_related":5})
        self.assertTrue(all(c["private_independent_gold_label"]=="NOT_COLLECTED"
                            and c["private_reviewer_minutes"]=="NOT_COLLECTED" for c in x["cases"]))
        self.assertTrue(set(x["controls_source_award_ambiguity"]).issubset(
            {e["doi"] for e in x["cases"]}))
    def test_aggregate_metrics_never_expose_case_level_gold_data(self):
        b=create()
        g=[{"case_id":e["case_id"],
            # Synthetic gold agrees with predicted duplicates ONLY for the
            # privacy/aggregate-metric unit test; no actual truth is asserted.
            "gold_label":"EXISTING_IN_REACH" if e["shared_engine_preflight"] in {
                "EXISTING_IN_REACH_VERIFIED_BULK","EXISTING_IN_REACH",
                "EXISTING_IN_REACH_VERIFIED_CANONICAL_URL"}
                      else "NOT_WPO_ASSOCIATED",
            "reviewer_minutes":"3"} for e in b["cases"]]
        aggregate=score(b,g)
        self.assertEqual(aggregate["benchmark_size"],100)
        self.assertEqual(aggregate["average_review_minutes"],3)
        self.assertEqual(aggregate["duplicate_precision"],1)
        self.assertEqual(aggregate["duplicate_recall"],1)
        self.assertNotIn("cases",aggregate)
        self.assertNotIn("doi",aggregate)
        with self.assertRaisesRegex(ValueError,"100 gold-labelled"):
            score(b,g[:-1])

if __name__=="__main__":unittest.main()
