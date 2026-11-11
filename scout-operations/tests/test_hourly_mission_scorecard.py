"""Scorecard counts only verifiable per-run records, with producers separated."""
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from summarize_hourly_missions import summarize

NOW = datetime(2026, 11, 10, 15, 0, tzinfo=timezone.utc).isoformat()


def record(producer, run, doi):
    return {
        "schema": "reach-scout-hourly-mission-outcome-v1",
        "producer": producer,
        "not_chatgpt_hourly_mission": producer != "chatgpt_hourly_mission",
        "mission_id": run, "started_at_utc": NOW, "completed_at_utc": NOW,
        "policy_commit_sha": "a"*40, "memory_source_fingerprint": "f"*64,
        "memory_builder_policy_sha256": "b"*64,
        "lane": "historical_crossref_original" if producer.startswith("github") else "independent_original",
        "selected_original_dois": [doi], "selected_expansion_seed_dois": [],
        "fast_exited_public_reach": [], "fast_exited_public_scout": [],
        "new_original_full_decisions": [doi], "new_expansion_decisions": [],
        "research_only_holds": [], "technical_or_funding_holds": [],
        "published_public_batch_urls": ["https://github.com/PART-WPO/reach-scout-discoveries/blob/main/batches/example.csv"],
        "guarded_handoff_run_urls": [], "handoff_status": "PUBLISHED_PUBLIC_SCOUT",
        "handoff_blocker": None, "prior_note_sha256_reused": [],
        "prior_metadata_fingerprints_reused": [],
        "cache_hits_observed": None, "external_requests_observed": None,
        "avoided_requests_measured": None,
        "private_hub_import": "NOT_VERIFIED", "human_decision": "NOT_VERIFIED",
        "public_reach_addition": "NOT_VERIFIED"
    }


class ScorecardTests(unittest.TestCase):
    def test_producers_separate_and_reused_doi_not_double_counted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dirs = {
                "chatgpt_hourly_mission": "scout-operations/reports/hourly-missions",
                "github_guarded_crossref_backstop": "scout-operations/reports/guarded-backstop-missions"
            }
            for producer, folder in dirs.items():
                path = root / folder / ("test-" + producer + ".json")
                path.parent.mkdir(parents=True)
                path.write_text(json.dumps(record(producer, producer, "10.1175/duplicate")))
            result = summarize(root)["by_producer"]
            self.assertEqual(result["chatgpt_hourly_mission"]["verified_report_count"], 1)
            self.assertEqual(result["github_guarded_crossref_backstop"]["verified_report_count"], 1)
            self.assertIsNone(result["chatgpt_hourly_mission"]["observed_metadata_requests_sum_only_instrumented_missions"])
            self.assertEqual(result["chatgpt_hourly_mission"]["distinct_completed_original_dois"], ["10.1175/duplicate"])

    def test_bounded_seed_negative_not_formal_expansion_or_technical_hold(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "scout-operations/reports/hourly-missions"
            folder.mkdir(parents=True)
            for i, kind in enumerate(("negative", "technical", "repeat")):
                r = record("chatgpt_hourly_mission", f"seed-{i}", "10.1175/original")
                r["lane"] = "related_expansion"
                r["selected_original_dois"] = []
                r["new_original_full_decisions"] = []
                r["selected_expansion_seed_dois"] = ["10.1007/seed"]
                r["new_expansion_decisions"] = []
                r["research_only_holds"] = ["10.1007/seed"] if kind != "technical" else []
                r["technical_or_funding_holds"] = ["10.1007/seed"] if kind == "technical" else []
                r["published_public_batch_urls"] = []
                r["handoff_status"] = "NOT_ATTEMPTED"
                (folder / f"{i}.json").write_text(json.dumps(r))
            x = summarize(root)["by_producer"]["chatgpt_hourly_mission"]
            self.assertEqual(x["bounded_seed_no_new_output_missions"], 2)
            self.assertEqual(x["distinct_bounded_seed_no_new_output_count"], 1)
            self.assertEqual(x["expansion_seeds_revisited_across_missions"], 1)
            self.assertEqual(x["formal_expansion_decision_missions"], 0)


if __name__ == "__main__":
    unittest.main()
