"""Regression: avoid repeating a staged DataCite DOI or wasting a mission on API failure."""
import io
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from recover_historical_datacite import recover, _check_native_record, ROOT
from select_independent_mission_candidates import eligible
from build_crosslane_research_memory import build, mission_index


class _Page:
    def __init__(self, content):
        self.stream = io.BytesIO(content)
    def __enter__(self):
        return self.stream
    def __exit__(self, *args):
        self.stream.close()


class _FakeOpener:
    def __init__(self, body):
        self.body = body
    def open(self, request, timeout=None):
        return _Page(self.body)


class IndependentRecoveryTests(unittest.TestCase):
    doi = "10.13012/b2idb-0704763_v1"

    def test_api_failure_recovers_sha_verified_historical_source(self):
        failure = {"status": "unavailable_or_not_found",
                   "attempts": [{"provider": "datacite",
                                 "error": {"kind": "access"}}]}
        md = recover(ROOT, self.doi, failure, check_native=False)
        self.assertEqual(md["status"], "archived_source_recovered")
        self.assertEqual(md["provider"], "historical_datacite_snapshot")
        self.assertEqual(md["doi"], self.doi)
        self.assertIn("Parsivel Data", md["title"])
        self.assertIn("NA21OAR4590367", md["recorded_award_hints"])
        self.assertEqual(md["source_batch_id"],
                         "2026-10-28-historical-datacite-spark-all-part001")
        self.assertEqual(len(md["archive_manifest_sha256"]), 64)
        self.assertEqual(md["original_terminal_status"], "forwarded_to_hub")
        self.assertEqual(md["publication_status"], "NOT_RECHECKED")
        self.assertTrue(md["research_only"])
        self.assertEqual(md["pub_date"], "")
        self.assertEqual(md["attempts"], failure["attempts"])

    def test_missing_doi_keeps_unavailable_status(self):
        failure = {"status": "unavailable_or_not_found", "attempts": []}
        self.assertEqual(recover(ROOT, "10.9999/unindexed-doi", failure, check_native=False),
                         failure)

    def test_native_page_requires_exact_doi_and_trusted_host(self):
        url = "https://databank.illinois.edu/datasets/IDB-0704763"
        verified = _check_native_record(
            url, self.doi, opener=_FakeOpener(
                ("<html>DOI " + self.doi + "</html>").encode()))
        self.assertEqual(verified["result"], "LIVE_EXACT_DOI_PRESENT")
        missing = _check_native_record(
            url, self.doi, opener=_FakeOpener(b"<html>No record</html>"))
        self.assertEqual(missing["result"], "EXACT_DOI_NOT_IN_PAGE")
        unsafe = _check_native_record(
            "http://127.0.0.1/private", self.doi,
            opener=_FakeOpener(self.doi.encode()))
        self.assertEqual(unsafe["result"], "UNAPPROVED_NATIVE_HOST")

    @classmethod
    def setUpClass(cls):
        cls.index = mission_index(build())

    def test_hourly_rotates_to_another_distinct_candidate(self):
        queue = eligible(self.index, limit=5)
        self.assertGreaterEqual(len(queue), 2)
        self.assertEqual(len({x["doi"] for x in queue}), len(queue))
        self.assertNotIn(self.doi, {x["doi"] for x in queue})
        rotated = eligible(self.index, blocked=[queue[0]["doi"]], limit=5)
        self.assertNotIn(queue[0]["doi"], {x["doi"] for x in rotated})
        self.assertNotEqual(queue[0]["doi"], rotated[0]["doi"])
        self.assertLessEqual(len(rotated), 5)

    def test_historical_exception_stays_researchable(self):
        pending = {x["doi"] for x in
                   self.index["recommended_preview"]["historical_datacite_original"]}
        historical = json.loads((ROOT / "scout-operations/historical-coverage.json").read_text())
        exceptions = json.loads((ROOT / "scout-operations/historical-reconciliation-exceptions.json").read_text())
        from build_crosslane_research_memory import build as graph_builder
        held = {n["doi"] for n in graph_builder()["nodes"]
                if n["preprint_or_version_hold"]}
        expected = {e["identity"].removeprefix("doi:").lower()
                    for e in exceptions["exceptions"]} - held
        if historical["remaining"] <= self.index["max_preview_per_group"]:
            self.assertEqual(pending, expected)
        self.assertNotIn(self.doi, pending)

    def test_limits_and_dedup_of_blocked_identities(self):
        with self.assertRaisesRegex(ValueError, "bounded"):
            eligible(self.index, limit=6)
        blocked = [x["doi"] for x in eligible(self.index, limit=5)]
        self.assertTrue(all(x["doi"] not in blocked
                            for x in eligible(self.index, blocked=blocked, limit=5)))


if __name__ == "__main__":
    unittest.main()
