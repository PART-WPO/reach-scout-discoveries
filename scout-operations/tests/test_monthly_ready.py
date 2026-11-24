"""Scheduled catch-up only runs after the authoritative month is complete."""
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[2]
CHECK = ROOT / "api-discoveries/tools/monthly_ready.py"
SCHEMA = json.loads((ROOT / "api-discoveries/manifest.json").read_text())["schema"]
STATUS = "completed_API_research_input_only_not_Scout_reviewed_not_REACH_published"


class MonthlyReadinessTests(unittest.TestCase):
    def setUp(self):
        folder = self.enterContext(TemporaryDirectory())
        self.root = Path(folder)
        self.api = self.root / "api-discoveries"
        (self.api / "runs").mkdir(parents=True)
        self.reports = self.root / "monthly-harvest-reports"
        self.reports.mkdir()
        self.manifest = self.api / "manifest.json"
        self.manifest.write_text(json.dumps({"schema": SCHEMA, "batches": []}))

    def check(self, root=None, month="2026-11"):
        return subprocess.run(
            [sys.executable, str(CHECK), "--root", str(root or self.root), "--month", month],
            capture_output=True, text=True,
        )

    def test_waits_for_completion_even_if_last_month_exists(self):
        completed = self.check(ROOT, "2026-10")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(self.check().returncode, 1)

    def test_missing_summary_for_published_batch_is_an_error(self):
        self.manifest.write_text(json.dumps({"schema": SCHEMA,
            "batches": [{"source_run_ids": ["REACH-MONTHLY-API-2026-11"]}]}))
        result = self.check()
        self.assertEqual(result.returncode, 2)
        self.assertIn("no completion summary", result.stderr)

    def test_zero_row_success_requires_matching_workbook(self):
        (self.api / "runs/monthly-2026-11.json").write_text(json.dumps({
            "status": STATUS, "cohort": "2026-11", "run": "REACH-MONTHLY-API-2026-11",
            "source_apis": ["datacite", "crossref"], "batch_count": 0, "distinct_dois": 0,
            "unique_awards_checked_per_api": 1,
        }))
        result = self.check()
        self.assertEqual(result.returncode, 2)
        self.assertIn("missing its comparison workbook", result.stderr)
        (self.reports / "November_2026.xlsx").write_bytes(b"fixture")
        self.assertEqual(self.check().returncode, 0)
