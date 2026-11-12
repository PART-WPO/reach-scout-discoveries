"""Offline regression cases for complete live REACH plus public Scout identity."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from related_output_identity import screen


def index(**kw):
    return {"manifest_sha256": "f"*64, "by_doi": {},
            "by_id": {}, **kw}


def direct(status="NO_PUBLIC_IDENTITY_MATCH", ir_status="DOI_NOT_IN_VERIFIED_IR_INDEX_UNKNOWN"):
    def check(_pub, _ir, _doi, _title, _url):
        return {"status": status, "matches": [],
                "noaa_ir_reach_check": {"status": ir_status}}
    return check


class IdentityTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = lambda root: ({"source_fingerprint": "a"*64}, {})
        self.doi = "10.5281/zenodo.12627444"

    def check(self, *, live=None, direct_fn=None, url=""):
        return screen(Path("."), self.doi, "GLStormTrends", artifact_url=url,
                      snapshot_fn=self.snapshot,
                      check_fn=direct_fn or direct(),
                      live_fn=live or (lambda: index()))

    def test_complete_negative_requires_live_and_public_inbox(self):
        result = self.check()
        self.assertEqual(result["status"], "NO_PUBLIC_IDENTITY_MATCH")
        self.assertTrue(result["checked_public_scout_manifest_and_inbox"])
        self.assertTrue(result["checked_live_complete_reach"])
        self.assertEqual(result["live_reach_manifest_sha256"], "f"*64)

    def test_inaccessible_live_index_never_means_new(self):
        def blocked():
            raise TimeoutError("no source")
        result = self.check(live=blocked)
        self.assertEqual(result["status"], "PUBLIC_IDENTITY_GATE_INCOMPLETE")
        self.assertFalse(result["checked_live_complete_reach"])

    def test_existing_scout_inbox_is_one_prior_review_unit(self):
        result = self.check(
            live=lambda: (_ for _ in ()).throw(TimeoutError("unused")),
            direct_fn=direct("IN_PUBLIC_SCOUT_QUEUE"))
        self.assertEqual(result["status"], "IN_PUBLIC_SCOUT_QUEUE")
        self.assertTrue(result["checked_public_scout_manifest_and_inbox"])

    def test_exact_live_primary_github_url_is_existing_reach(self):
        row = {"record_id": "reach-000079", "reach_uid": "reachuid-v1-example",
               "title": "Code", "output_type": "Code Release",
               "link": "https://github.com/abkenyon/GLStormTrends_2024"}
        result = self.check(
            live=lambda: index(by_id={row["record_id"]: row}),
            url="https://github.com/ABKENYON/GLStormTrends_2024.git")
        self.assertEqual(result["status"], "CONFIRMED_PUBLIC_REACH_IDENTITY")
        self.assertEqual(result["matches"][0]["record_id"], "reach-000079")

    def test_live_doi_title_disagreement_goes_to_review(self):
        row = {"record_id": "reach-000002", "title": "Other dataset",
               "link": "https://doi.org/" + self.doi}
        result = self.check(live=lambda: index(
            by_id={"reach-000002": row}, by_doi={self.doi: [row]}))
        self.assertEqual(result["status"], "BOUNDED_PUBLIC_IDENTITY_REVIEW")

    def test_ir_unavailable_is_not_clear_negative(self):
        result = self.check(direct_fn=direct(ir_status="IR_INDEX_UNAVAILABLE_HOLD"))
        self.assertEqual(result["status"], "PUBLIC_IDENTITY_GATE_INCOMPLETE")

    def test_cached_reach_positive_conflicting_live_is_hold(self):
        result = self.check(direct_fn=direct(status="CONFIRMED_PUBLIC_REACH_IDENTITY"))
        self.assertEqual(result["status"], "PUBLIC_IDENTITY_GATE_INCOMPLETE")


if __name__ == "__main__":
    unittest.main()
