"""Offline tests for canonical Scout CSV preparation and attribution reconciliation."""
import csv
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
from prepare_batch import compose_rationale, prepare, validate_canonical
import rebuild_discovery_rollup
import promote_inbox


def candidate():
    return {
        "fields": {
            "Title": "Fixture dataset for DOI discovery testing",
            "DOI": "10.1234/example.dataset",
            "Output URL": "https://doi.org/10.1234/example.dataset",
            "Output Type": "3",
            "NOAA Award Number(s)": "NA23OAR4590137",
            "Publication Date": "2025-10-17",
            "Evidence URL": "https://doi.org/10.1234/example.dataset",
            "Funding Evidence URL": "https://example.org/publisher",
            "Existing REACH Match": "Not found in the verified public REACH index",
            "Scout Confidence": "Medium",
            "Source Run ID": "REACH-SCOUT-TEST-001",
        },
        "provenance": {
            "intake_origin": "Historical DataCite API Backfill",
            "classification": "NEW CANDIDATE",
            "route": "API-seeded expansion",
            "path_evidence": "https://example.org/publisher",
            "seed_doi": "10.25923/t7t6-m677",
            "reach_snapshot": "a" * 40,
            "sources_checked": [
                "https://example.org/publisher",
                "https://api.datacite.org/dois/10.1234/example.dataset",
            ],
            "funding_basis": "Publisher acknowledgments and source metadata identify the WPO award.",
            "related_outputs_checked": "Checked original grant record and neighboring articles; original dataset is distinct.",
            "notes": ["Reviewer question: Confirm dataset public file scope and uniqueness."],
        }
    }


class ScoutBatchTests(unittest.TestCase):
    def test_required_canonical_labels(self):
        text = compose_rationale(candidate()["provenance"])
        for item in ("Scout seed DOI: 10.25923/t7t6-m677",
                     "Scout classification: NEW CANDIDATE",
                     "Intake origin: Historical DataCite API Backfill",
                     "Scout verification: Completed",
                     "REACH snapshot: " + "a" * 40,
                     "Sources checked: https://",
                     "Funding basis: ", "Related outputs checked: "):
            self.assertIn(item, text)

    def test_missing_seed_is_rejected_before_output(self):
        row = candidate()
        row["provenance"].pop("seed_doi")
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            src = base / "draft.json"
            dest = base / "2026-10-30-test-001.csv"
            src.write_text(json.dumps({"candidates": [row]}))
            with self.assertRaises((ValueError, KeyError)):
                prepare(src, dest)
            self.assertFalse(dest.exists())

    def test_build_and_validation_uses_real_manifest_rules(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            src = base / "draft.json"
            dest = base / "2026-10-30-test-001.csv"
            src.write_text(json.dumps({"candidates": [candidate()]}))
            meta = prepare(src, dest)
            self.assertEqual(meta["record_count"], 1)
            self.assertEqual(validate_canonical(dest)["source_run_ids"], ["REACH-SCOUT-TEST-001"])
            with self.assertRaisesRegex(ValueError, "overwrite"):
                prepare(src, dest)
            broken = dest.read_text().replace("Scout seed DOI:", "Original API seed DOI:")
            dest.write_text(broken)
            with self.assertRaisesRegex(ValueError, "seed DOI"):
                validate_canonical(dest)

    def test_rollup_counts_only_sha_verified_manifested_rows(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d) / "scout-discoveries"
            batches = base / "batches"
            batches.mkdir(parents=True)
            src = batches / "2026-10-30-test-001.csv"
            record = candidate()
            source = base.parent / "fixture.json"
            source.write_text(json.dumps({"candidates": [record]}))
            prepare(source, src)
            sha = hashlib.sha256(src.read_bytes()).hexdigest()
            manifest = {
                "schema": "reach-scout-discovery-feed-v1",
                "batch_count": 1,
                "candidate_rows": 1,
                "batches": [{
                    "id": src.stem,
                    "path": "scout-discoveries/batches/" + src.name,
                    "sha256": sha,
                    "record_count": 1,
                    "source_run_ids": ["REACH-SCOUT-TEST-001"],
                }]
            }
            prior = rebuild_discovery_rollup.ROOT
            rebuild_discovery_rollup.ROOT = base
            try:
                counts, checked, n = rebuild_discovery_rollup.summarize(manifest)
                self.assertEqual(n, 1)
                self.assertEqual(counts["API-seeded expansion"], 1)
                self.assertEqual(sum(counts.values()), 1)
                self.assertEqual(len(checked), 1)
                src.write_bytes(src.read_bytes() + b"\n")
                with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                    rebuild_discovery_rollup.summarize(manifest)
            finally:
                rebuild_discovery_rollup.ROOT = prior


    def test_inbox_promotes_only_valid_drafts(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            inbox = base / "inbox"
            batches = base / "batches"
            inbox.mkdir()
            src = base / "draft.json"
            src.write_text(json.dumps({"candidates": [candidate()]}))
            draft = inbox / "2026-10-30-test-001.csv"
            prepare(src, draft)
            old_inbox, old_batches = promote_inbox.INBOX, promote_inbox.BATCHES
            promote_inbox.INBOX, promote_inbox.BATCHES = inbox, batches
            try:
                promote_inbox.promote()
                self.assertEqual((batches / draft.name).read_bytes(), draft.read_bytes())
                promote_inbox.promote()  # already published drafts are not published twice
                self.assertEqual(list(batches.glob("*.csv")), [batches / draft.name])
            finally:
                promote_inbox.INBOX, promote_inbox.BATCHES = old_inbox, old_batches

    def test_invalid_inbox_draft_cannot_poison_published_batches(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            inbox = base / "inbox"
            batches = base / "batches"
            inbox.mkdir()
            src = base / "draft.json"
            src.write_text(json.dumps({"candidates": [candidate()]}))
            valid = inbox / "2026-10-30-test-001.csv"
            prepare(src, valid)
            invalid = inbox / "2026-10-30-test-002.csv"
            invalid.write_text(valid.read_text().replace("Scout seed DOI:", "Original API seed DOI:"))
            old_inbox, old_batches = promote_inbox.INBOX, promote_inbox.BATCHES
            promote_inbox.INBOX, promote_inbox.BATCHES = inbox, batches
            try:
                with self.assertRaisesRegex(ValueError, "seed DOI"):
                    promote_inbox.promote()
                self.assertFalse(batches.exists(), "No candidate should be promoted if any new draft fails")
            finally:
                promote_inbox.INBOX, promote_inbox.BATCHES = old_inbox, old_batches


if __name__ == "__main__":
    unittest.main()
