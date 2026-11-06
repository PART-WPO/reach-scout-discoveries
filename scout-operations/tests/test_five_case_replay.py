"""Exercise real Scout decisions for five known research pathways, with zero writes."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from replay_five_scout_cases import build,CASE_DOIS

class FiveRealCaseReplay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=build(live_metadata=False)
    def test_all_five_paths_execute_without_publishing(self):
        r=self.report
        self.assertEqual(r["case_count"],5)
        self.assertEqual(r["passed"],5)
        self.assertEqual(r["failed"],0)
        self.assertEqual(r["new_public_candidates_created"],0)
        self.assertEqual(r["reviewer_csv_writes"],0)
        self.assertEqual(r["private_hub_imports"],"NOT_VERIFIED")
        self.assertEqual(r["human_approvals"],"NOT_VERIFIED")
        self.assertEqual(r["expansion_seed_closures"],0)
        self.assertEqual(r["formal_historical_statuses_mutated"],0)
    def test_real_result_by_doi(self):
        expected={
          "published_with_uncertain_project":"VALIDATED_EXISTING_NEEDS_INVESTIGATION_DRAFT",
          "publication_with_missing_award_bridge":"HOLD_UNVERIFIED_PROJECT_CONTEXT",
          "dataset_with_recovered_registry_metadata":"METADATA_VERIFIED_PROJECT_UNRESOLVED",
          "preprint_guard":"PREPRINT_HOLD",
          "already_cataloged_published_version":"EXISTING_IN_REACH",
        }
        cases={x["case"]:x for x in self.report["cases"]}
        self.assertEqual(len(cases),len(expected))
        for name,decision in expected.items():
            with self.subTest(name=name):
                self.assertEqual(cases[name]["observed"],decision)
                self.assertTrue(cases[name]["verified"])
                self.assertTrue(cases[name]["source_sha256"])
    def test_evidence_coverage_and_cached_metadata(self):
        r=self.report
        self.assertGreaterEqual(r["source_evidence_files"],28)
        self.assertGreaterEqual(r["source_note_events"],33)
        self.assertGreaterEqual(r["doi_recovery_cached_success"],4)
        e=next(x for x in r["cases"] if x["doi"]==CASE_DOIS["ecmwf_metadata_recovery"])
        self.assertEqual(e["new_api_calls_for_cached_metadata"],0)

if __name__=="__main__":unittest.main()
