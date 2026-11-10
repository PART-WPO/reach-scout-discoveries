"""Offline tests: record only actual completed public backstop outcomes."""
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from write_hourly_mission_metrics import build
from validate_hourly_mission import validate

NOW = datetime(2026, 11, 10, 14, 0, tzinfo=timezone.utc)
SHA = "a" * 40
DOI = "10.1175/waf-d-25-0244.1"


class MissionMeasurementTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.rel = "scout-discoveries/batches/demo.csv"
        batch = self.root / self.rel
        batch.parent.mkdir(parents=True)
        batch.write_text("DOI,Title\\n" + DOI + ",Verified article\\n")
        index = self.root / "scout-operations/research-memory/mission-index.json"
        index.parent.mkdir(parents=True)
        index.write_text(json.dumps({"source_fingerprint": "f" * 64,
                                     "builder_policy_sha256": "b" * 64}))

    def write_handoff(self, outcomes, published_count, measurement=None):
        path = self.root / "scout-operations/reports/hourly-decision-handoff.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "schema": "reach-scout-hourly-decision-handoff-v1",
            "ran_at": (NOW - timedelta(seconds=30)).isoformat(),
            "attempted_originals": len(outcomes),
            "public_review_batches_validated_this_run": published_count,
            "source_selection_sha256": "c" * 64,
            "outcomes": outcomes, "skipped_cooldown_or_already_staged": [
                {"doi": "10.1175/mwr-d-20-0098.1", "reason": "PUBLISHED_PUBLIC_SCOUT"}],
            "measurement": measurement or {}
        }))

    def test_actual_published_public_handoff_distinct_from_hourly_chatgpt(self):
        self.write_handoff([{
            "doi": DOI, "status": "PUBLISHED_PUBLIC_SCOUT",
            "published_batch": self.rel, "decision": "SOURCE_VERIFIED_FOR_GUARDED_REVIEW",
            "prior_research_note_sha256_reused": "1" * 64
        }], 1, {"provider_http_requests_observed": 2,
               "in_process_metadata_reuses": 1,
               "prior_research_note_sha256_reused": ["1" * 64]})
        data = build(self.root, "123", "1", SHA, finished_at=NOW)
        self.assertEqual(validate(data), [])
        self.assertEqual(data["producer"], "github_guarded_crossref_backstop")
        self.assertTrue(data["not_chatgpt_hourly_mission"])
        self.assertEqual(data["new_original_full_decisions"], [DOI])
        self.assertEqual(len(data["published_public_batch_urls"]), 1)
        self.assertEqual(data["external_requests_observed"], 2)
        self.assertEqual(data["cache_hits_observed"], 1)
        self.assertIsNone(data["avoided_requests_measured"])
        self.assertEqual(data["fast_exited_public_scout"], [])
        self.assertEqual(len(data["previously_screened_skipped_not_mission_fast_exits"]), 1)

    def test_blocked_with_unknown_provider_requests_remains_unknown(self):
        self.write_handoff([{"doi": DOI, "status": "BLOCKED",
                            "decision": "OFFICIAL_METADATA_UNAVAILABLE"}], 0, {
                                "provider_http_requests_observed": None,
                                "in_process_metadata_reuses": 0})
        data = build(self.root, "124", "2", SHA, finished_at=NOW)
        self.assertEqual(validate(data), [])
        self.assertEqual(data["handoff_status"], "BLOCKED")
        self.assertIsNone(data["external_requests_observed"])
        self.assertEqual(data["new_original_full_decisions"], [])
        self.assertEqual(data["technical_or_funding_holds"], [DOI])

    def test_publication_claim_requires_reconciled_handoff_count(self):
        self.write_handoff([{"doi": DOI, "status": "PUBLISHED_PUBLIC_SCOUT",
                            "published_batch": self.rel}], 0)
        with self.assertRaisesRegex(ValueError, "count disagrees"):
            build(self.root, "125", "1", SHA, finished_at=NOW)

    def test_invalid_private_claim_is_rejected(self):
        self.write_handoff([], 0)
        data = build(self.root, "126", "1", SHA, finished_at=NOW)
        data["human_decision"] = "APPROVED"
        self.assertTrue(any("human_decision" in x for x in validate(data)))


if __name__ == "__main__":
    unittest.main()
