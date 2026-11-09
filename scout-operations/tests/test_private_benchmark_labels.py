"""Blinded 100-case benchmark labels never become a public GitHub file."""
import csv
import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from score_private_benchmark import create_private_gold_template, score


def benchmark():
    return {"cases": [
        {"case_id": f"case-{i}", "doi": f"10.1234/test-{i}",
         "stratum": "known_reach_identity" if i < 30 else "index_negative_original",
         "shared_engine_preflight": "EXISTING_IN_REACH" if i < 30
                                   else "NO_PUBLIC_IDENTITY_MATCH"}
        for i in range(100)
    ]}


class PrivateGoldTests(unittest.TestCase):
    def test_blind_private_100_case_template_and_scoring(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "private_gold.csv"
            self.assertEqual(create_private_gold_template(benchmark(), output), 100)
            with output.open(encoding="utf8", newline="") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 100)
            self.assertEqual(rows[0]["gold_label"], "")
            self.assertEqual(set(rows[0]), {
                "case_id", "doi", "stratum", "gold_label", "evidence_url",
                "reviewer_minutes"})
            self.assertNotIn("shared_engine_preflight", output.read_text())
            if os.name == "posix":
                self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o600)
            for i, r in enumerate(rows):
                r["gold_label"] = ("EXISTING_IN_REACH" if i < 30
                                   else "NOT_WPO_ASSOCIATED")
            metrics = score(benchmark(), rows)
            self.assertEqual(metrics["duplicate_precision"], 1)
            self.assertEqual(metrics["duplicate_recall"], 1)
            with self.assertRaises(FileExistsError):
                create_private_gold_template(benchmark(), output)

    def test_refuse_template_inside_public_checkout(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaisesRegex(ValueError, "outside public GitHub"):
                create_private_gold_template(benchmark(), Path(root)/"gold.csv",
                                             root=Path(root))

    def test_incomplete_labels_do_not_get_accuracy_claim(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"labels.csv"
            create_private_gold_template(benchmark(), path)
            with path.open(encoding="utf8",newline="") as f:
                rows=list(csv.DictReader(f))
            with self.assertRaisesRegex(ValueError, "Human gold label"):
                score(benchmark(), rows)


if __name__=="__main__":
    unittest.main()
