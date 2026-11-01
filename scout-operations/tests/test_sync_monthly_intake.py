"""Offline regression checks for recurring monthly Scout ledger intake."""
import csv
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import sync_monthly_intake as sync

FIELDS = ["DOI", "Output URL", "NOAA Award Number(s)", "Source Run ID"]


def fixture(root, batch_id, month, dois):
    path = root / "api-discoveries/batches" / (batch_id + ".csv")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=FIELDS)
        writer.writeheader()
        for doi in dois:
            writer.writerow({
                "DOI": doi, "Output URL": "https://doi.org/" + doi,
                "NOAA Award Number(s)": "NA23OAR4590379",
                "Source Run ID": "REACH-MONTHLY-API-" + month,
            })
    raw = path.read_bytes()
    return {"id": batch_id, "path": str(path.relative_to(root)),
            "sha256": hashlib.sha256(raw).hexdigest(), "record_count": len(dois)}


def write_state(root, batches, superseded=None):
    (root / "scout-operations").mkdir(exist_ok=True)
    payload = {
        "schema": "reach-monthly-api-discovery-feed-v1",
        "generated_at": "2026-12-01T05:01:00Z",
        "candidate_rows": sum(batch["record_count"] for batch in batches),
        "batches": batches,
        "superseded_batches": superseded or [],
    }
    (root / "api-discoveries/manifest.json").write_text(json.dumps(payload))
    (root / "scout-operations/monthly-triage.json").write_text(
        json.dumps({"schema": "reach-scout-monthly-triage-v1",
                    "repository": "PART-WPO/reach-scout-discoveries",
                    "entries": []}) + "\n"
    )


class MonthlyIntakeTests(unittest.TestCase):
    def test_new_monthly_dois_start_unresearched_and_reruns_are_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            batch = fixture(root, "2026-12-01-monthly-api-2026-11-part001",
                            "2026-11", ["10.1234/one", "10.1234/two"])
            write_state(root, [batch])
            first = sync.reconcile(root)
            self.assertEqual(len(first["entries"]), 2)
            self.assertTrue(all(e["status"] == "awaiting_research" for e in first["entries"]))
            self.assertTrue(all(e["checked_sources"] == [] for e in first["entries"]))
            ledger_path = root / "scout-operations/monthly-triage.json"
            before = ledger_path.read_bytes()
            sync.reconcile(root)
            self.assertEqual(ledger_path.read_bytes(), before)
            first["entries"][0]["status"] = "needs_more_research"
            first["entries"][0]["research_notes"] = "Verified initial screening; full research pending"
            ledger_path.write_text(json.dumps(first))
            updated = sync.reconcile(root)
            self.assertEqual(updated["entries"][0]["status"], "needs_more_research")
            self.assertIn("Verified initial screening", updated["entries"][0]["research_notes"])

    def test_following_month_appends_without_erasing_prior_work(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            october = fixture(root, "2026-11-01-monthly-api-2026-10-part001",
                              "2026-10", ["10.1234/october"])
            write_state(root, [october])
            sync.reconcile(root)
            november = fixture(root, "2026-12-01-monthly-api-2026-11-part001",
                               "2026-11", ["10.1234/november"])
            (root / "api-discoveries/manifest.json").write_text(json.dumps({
                "schema": "reach-monthly-api-discovery-feed-v1",
                "generated_at": "2026-12-01T05:01:00Z",
                "candidate_rows": 2, "batches": [october, november],
            }))
            result = sync.reconcile(root)
            self.assertEqual(len(result["entries"]), 2)
            self.assertEqual({x["cohort"] for x in result["entries"]}, {"2026-10","2026-11"})

    def test_corrected_batch_archives_original_without_reusing_old_decision(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            prior = fixture(root, "2026-12-01-monthly-api-2026-11-part001",
                            "2026-11", ["10.1234/related", "10.1234/genuine"])
            write_state(root, [prior])
            old = sync.reconcile(root)
            old["entries"][0]["research_notes"] = "Case-specific human-reviewed research checkpoint"
            (root / "scout-operations/monthly-triage.json").write_text(json.dumps(old))
            corrected = fixture(root, "2026-12-01-monthly-api-2026-11-primary-only-part001",
                                "2026-11", ["10.1234/genuine"])
            manifest = {"schema": "reach-monthly-api-discovery-feed-v1",
                        "generated_at": "2026-12-01T06:00:00Z",
                        "candidate_rows": 1, "batches": [corrected],
                        "superseded_batches": [{
                            "original_id": prior["id"],
                            "replacement_id": corrected["id"],
                            "replacement_published": True,
                        }]}
            (root / "api-discoveries/manifest.json").write_text(json.dumps(manifest))
            result = sync.reconcile(root)
            self.assertEqual(len(result["entries"]), 1)
            self.assertEqual(result["entries"][0]["status"], "awaiting_research")
            self.assertEqual(len(result["archived_entries"]), 2)
            self.assertIn("human-reviewed", result["archived_entries"][0]["research_notes"])
            self.assertEqual(result["archived_entries"][0]["superseded_by_batch_id"], corrected["id"])

    def test_fail_closed_when_source_hash_mismatches_or_case_disappears(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            batch = fixture(root, "2026-12-01-monthly-api-2026-11-part001",
                            "2026-11", ["10.1234/one"])
            write_state(root, [batch])
            path = root / batch["path"]
            path.write_bytes(path.read_bytes() + b"changed")
            with self.assertRaisesRegex(ValueError, "SHA mismatch"):
                sync.reconcile(root)
            self.assertEqual(json.loads(
                (root / "scout-operations/monthly-triage.json").read_text())["entries"], [])

    def test_fail_closed_when_original_disappears_without_supersession(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            batch = fixture(root, "2026-12-01-monthly-api-2026-11-part001",
                            "2026-11", ["10.1234/one"])
            write_state(root, [batch])
            sync.reconcile(root)
            (root / "api-discoveries/manifest.json").write_text(json.dumps({
                "schema": "reach-monthly-api-discovery-feed-v1",
                "generated_at": "2026-12-01T06:00:00Z",
                "candidate_rows": 0, "batches": [],
            }))
            with self.assertRaisesRegex(ValueError, "without explicit supersession"):
                sync.reconcile(root)


if __name__ == "__main__":
    unittest.main()
