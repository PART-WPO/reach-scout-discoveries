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
        self.assertEqual(p["historical_crossref_screened"],614)
        self.assertEqual(p["verified_existing_reach_public_identities"],433)
        self.assertEqual(p["ambiguous_reach_identification"],47)
        self.assertEqual(p["index_negative_originals_pending_funding"],134)
        self.assertEqual(p["distinct_crossref_expansions_verified_complete"],0)
        self.assertEqual(p["terminal_dispositions_under_evidence_repair"],12)
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
