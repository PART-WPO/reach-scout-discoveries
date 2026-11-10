"""Offline regression tests for missing-run recovery, status and weekday gating."""
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from guarded_handoff_watchdog import evaluate

NOW = datetime(2026, 11, 10, 13, 12, tzinfo=timezone.utc)

def run(when, status="completed", conclusion="success", event="schedule", ident=1):
    return {"id": ident, "name": "Scout hourly guarded DOI decision handoff",
            "head_branch": "main", "event": event, "status": status,
            "conclusion": conclusion, "created_at": when, "updated_at": when}

class WatchdogTests(unittest.TestCase):
    def test_missing_scheduled_runs_trigger_recovery(self):
        x = evaluate({"workflow_runs": [run("2026-11-10T04:14:31Z")]}, NOW)
        self.assertEqual(x["action"], "RECOVERY_REQUIRED")
        self.assertEqual(x["latest_success_run_id"], 1)
        self.assertEqual(x["new_public_candidate_count"], "NOT_INFERRED")

    def test_recent_success_no_recovery(self):
        x = evaluate({"workflow_runs": [run("2026-11-10T12:40:00Z")]}, NOW)
        self.assertEqual(x["action"], "HEALTHY")

    def test_in_progress_no_concurrent_recovery(self):
        x = evaluate({"workflow_runs": [
            run("2026-11-10T04:14:31Z"),
            run("2026-11-10T12:59:00Z", status="in_progress", conclusion=None, ident=2)
        ]}, NOW)
        self.assertEqual(x["action"], "RUN_IN_PROGRESS")

    def test_recent_manual_recovery_is_idempotent(self):
        x = evaluate({"workflow_runs": [
            run("2026-11-10T04:14:31Z"),
            run("2026-11-10T12:55:00Z", status="completed", conclusion="failure",
                event="workflow_dispatch", ident=3)
        ]}, NOW)
        self.assertEqual(x["action"], "RECOVERY_COOLDOWN")

    def test_unrelated_or_failed_ci_is_not_completion(self):
        x = evaluate({"workflow_runs": [
            run("2026-11-10T12:40:00Z", status="completed", conclusion="failure"),
            {**run("2026-11-10T12:50:00Z", ident=4), "head_branch": "other"}
        ]}, NOW)
        self.assertEqual(x["action"], "RECOVERY_REQUIRED")

    def test_weekend_is_existing_schedule_pause(self):
        sat = datetime(2026, 11, 14, 17, 12, tzinfo=timezone.utc)
        self.assertEqual(evaluate({"workflow_runs":[]},sat)["action"],"EXPECTED_WEEKEND_PAUSE")

    def test_bad_input_fails_closed(self):
        with self.assertRaises(ValueError):
            evaluate({}, NOW)
