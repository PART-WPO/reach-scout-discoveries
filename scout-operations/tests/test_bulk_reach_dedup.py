"""Deterministic bulk duplicate gate: fast-path only uniquely verified identities."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from bulk_reach_dedup import decide, summarize

class BulkReachGateTests(unittest.TestCase):
    def hit(self, *, doi=False, title=False, ir=False, uid="reachuid-v1-a"):
        return {"reach_uid":uid,"record_id":"reach-000001",
                "detail_path":"agent-data/details/part-001.csv",
                "doi_hit":doi,"title_hit":title,"official_ir_url_hit":ir}
    def classify(self,matches,ir_status="DOI_NOT_IN_VERIFIED_IR_INDEX_UNKNOWN", title=True):
        return decide(matches,{"status":ir_status},
                      title_available=title)

    def test_unique_exact_doi_and_title_fast_paths(self):
        r=self.classify([self.hit(doi=True,title=True)],ir_status="NOT_NEEDED_DIRECT_REACH")
        self.assertEqual(r["status"],"VERIFIED_EXISTING_REACH")
        self.assertEqual(r["basis"],"EXACT_REACH_DOI_AND_TITLE")
        self.assertEqual(r["verified_reach_uid"],"reachuid-v1-a")

    def test_unique_official_repository_url_and_title_fast_paths(self):
        r=self.classify([self.hit(ir=True,title=True)],
                        ir_status="VERIFIED_OFFICIAL_IR_DOI_TO_EXISTING_REACH_URL")
        self.assertEqual(r["status"],"VERIFIED_EXISTING_REACH")
        self.assertEqual(r["basis"],"VERIFIED_NOAA_IR_DOI_TO_REACH_URL_AND_TITLE")

    def test_title_only_cannot_auto_confirm(self):
        r=self.classify([self.hit(title=True)])
        self.assertEqual(r["status"],"NEEDS_IDENTITY_REVIEW")
        self.assertIsNone(r["verified_reach_uid"])

    def test_exact_doi_title_disagreement_remains_for_review(self):
        r=self.classify([self.hit(doi=True,title=False)])
        self.assertEqual(r["status"],"NEEDS_IDENTITY_REVIEW")
        self.assertEqual(r["basis"],"STRONG_IDENTITY_BUT_TITLE_OR_VERSION_DISAGREES")

    def test_ir_url_title_disagreement_remains_for_review(self):
        r=self.classify([self.hit(ir=True,title=False)],
                        ir_status="VERIFIED_OFFICIAL_IR_DOI_TO_EXISTING_REACH_URL")
        self.assertEqual(r["status"],"NEEDS_IDENTITY_REVIEW")

    def test_two_reach_uids_hold_even_with_exact_doi(self):
        r=self.classify([self.hit(doi=True,title=True),
                         self.hit(title=True,uid="reachuid-v1-b")])
        self.assertEqual(r["status"],"NEEDS_IDENTITY_REVIEW")
        self.assertEqual(r["basis"],"MULTIPLE_REACH_IDENTITIES")

    def test_ir_conflict_blocks_strong_exact_identity(self):
        r=self.classify([self.hit(doi=True,title=True)],
                        ir_status="REACH_DOI_CONFLICT_VERSION_REVIEW")
        self.assertEqual(r["status"],"NEEDS_IDENTITY_REVIEW")

    def test_ambiguous_ir_index_without_reach_hit_is_not_negative(self):
        r=self.classify([],ir_status="AMBIGUOUS_IR_DOI_HOLD")
        self.assertEqual(r["status"],"NEEDS_IDENTITY_REVIEW")

    def test_zero_hit_advances_research_not_publication(self):
        r=self.classify([])
        self.assertEqual(r["status"],"NO_PUBLIC_REACH_MATCH")
        self.assertEqual(r["route"],"ADVANCE_TO_FUNDING_AND_METADATA_RESEARCH")

    def test_missing_title_fails_closed(self):
        r=self.classify([self.hit(doi=True)],title=False)
        self.assertEqual(r["status"],"SCREENING_INCOMPLETE")

    def test_summary_requires_grounded_unique_title_consistent_identity(self):
        entry={"doi":"10.1000/one","matches":[self.hit(doi=True,title=True)],
               "bulk_identity_gate":self.classify([self.hit(doi=True,title=True)],
                                                ir_status="NOT_NEEDED_DIRECT_REACH")}
        summary=summarize([entry])
        self.assertEqual(summary["counts"],{"VERIFIED_EXISTING_REACH":1})
        bad={"doi":"10.1000/two","matches":[self.hit(doi=True,title=False)],
             "bulk_identity_gate":entry["bulk_identity_gate"]}
        with self.assertRaisesRegex(ValueError,"title agreement"):
            summarize([bad])

if __name__=="__main__":
    unittest.main()
