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


    def test_legacy_backfill_separates_method_and_purpose(self):
        """Pre-API SPARK research may suggest a metadata correction, not a new output."""
        with tempfile.TemporaryDirectory() as d:
            base = Path(d) / "scout-discoveries"
            batches = base / "batches"
            batches.mkdir(parents=True)
            draft = base.parent / "research.json"
            draft.write_text(json.dumps({"candidates": [candidate()]}))
            row_path = batches / "2026-10-27-legacy-001.csv"
            prepare(draft, row_path)
            with row_path.open(newline="", encoding="utf-8") as stream:
                reader = csv.DictReader(stream)
                fields = reader.fieldnames
                row = next(reader)
            row["Scout Discovery Rationale"] = row["Scout Discovery Rationale"].replace(
                "Scout discovery route: API-seeded expansion\n", "")
            with row_path.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
                writer.writeheader()
                writer.writerow(row)
            digest = hashlib.sha256(row_path.read_bytes()).hexdigest()
            batch = {
                "id": row_path.stem, "path": "scout-discoveries/batches/" + row_path.name,
                "sha256": digest, "record_count": 1,
                "source_run_ids": ["REACH-SCOUT-TEST-001"]
            }
            manifest = {"schema": "reach-scout-discovery-feed-v1",
                        "batch_count": 1, "candidate_rows": 1, "batches": [batch]}
            rec = {
                "record_key": row_path.stem + "#1",
                "source_batch_id": row_path.stem,
                "source_batch_path": batch["path"],
                "source_batch_sha256": digest,
                "source_data_row": 1,
                "source_run_id": "REACH-SCOUT-TEST-001",
                "output_identity": row["DOI"],
                "output_title": row["Title"],
                "discovery_method": "Independent discovery",
                "discovery_method_confidence": "High",
                "finding_purpose": "metadata_correction",
                "cohort": "pre_historical_datacite_spark_award_research",
            }
            previous = rebuild_discovery_rollup.ROOT
            rebuild_discovery_rollup.ROOT = base
            try:
                summary = rebuild_discovery_rollup.enrich_from_legacy(
                    manifest, {"schema": "reach-scout-legacy-provenance-backfill-v1",
                               "entries": [rec]})
                self.assertEqual(summary["discovery_method_counts"]["Independent discovery"], 1)
                self.assertEqual(summary["finding_purpose_counts"]["metadata_correction"], 1)
                self.assertEqual(summary["beyond_direct_api_new_output_review_proposals"], 0)
                self.assertEqual(summary["legacy_method_backfilled"], 1)
                bad = dict(rec, source_batch_sha256="0" * 64)
                with self.assertRaisesRegex(ValueError, "identity/digest mismatch"):
                    rebuild_discovery_rollup.enrich_from_legacy(
                        manifest, {"schema": "reach-scout-legacy-provenance-backfill-v1",
                                   "entries": [bad]})
                bad_key = dict(rec, record_key=row_path.stem + "#2")
                with self.assertRaisesRegex(ValueError, "not in manifest"):
                    rebuild_discovery_rollup.enrich_from_legacy(
                        manifest, {"schema": "reach-scout-legacy-provenance-backfill-v1",
                                   "entries": [bad_key]})
            finally:
                rebuild_discovery_rollup.ROOT = previous

    def test_explicit_newer_route_cannot_be_overridden_by_legacy(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d) / "scout-discoveries"
            batch_dir = base / "batches"
            batch_dir.mkdir(parents=True)
            draft = base.parent / "research.json"
            draft.write_text(json.dumps({"candidates": [candidate()]}))
            row_path = batch_dir / "2026-10-30-modern-001.csv"
            prepare(draft, row_path)
            batch = {"id": row_path.stem,
                     "path": "scout-discoveries/batches/" + row_path.name,
                     "sha256": hashlib.sha256(row_path.read_bytes()).hexdigest(),
                     "record_count": 1, "source_run_ids": ["REACH-SCOUT-TEST-001"]}
            manifest = {"schema": "reach-scout-discovery-feed-v1",
                        "batch_count": 1, "candidate_rows": 1, "batches": [batch]}
            row = candidate()["fields"]
            record = {"record_key": row_path.stem + "#1",
                      "source_batch_id": row_path.stem, "source_batch_path": batch["path"],
                      "source_batch_sha256": batch["sha256"], "source_data_row": 1,
                      "source_run_id": row["Source Run ID"], "output_identity": row["DOI"],
                      "output_title": row["Title"], "discovery_method": "Independent discovery",
                      "discovery_method_confidence": "High",
                      "finding_purpose": "new_output_review", "cohort": "legacy"}
            previous = rebuild_discovery_rollup.ROOT
            rebuild_discovery_rollup.ROOT = base
            try:
                with self.assertRaisesRegex(ValueError, "Refusing ledger override"):
                    rebuild_discovery_rollup.enrich_from_legacy(
                        manifest, {"schema": "reach-scout-legacy-provenance-backfill-v1",
                                   "entries": [record]})
            finally:
                rebuild_discovery_rollup.ROOT = previous



    def test_metadata_correction_records_its_independent_discovery_method(self):
        correction = candidate()
        correction["provenance"].update({
            "classification": "REACH METADATA UPDATE",
            "route": "Metadata correction",
            "origin_method": "Independent discovery",
            "discovery_method": "Started from SPARK award and followed publisher funding.",
        })
        rationale = compose_rationale(correction["provenance"])
        self.assertIn("Scout discovery route: Metadata correction", rationale)
        self.assertIn("Scout origin method: Independent discovery", rationale)
        self.assertIn("Scout finding purpose: metadata_correction", rationale)
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp) / "scout-discoveries"
            batches = base / "batches"
            batches.mkdir(parents=True)
            fixture = base.parent / "correction.json"
            fixture.write_text(json.dumps({"candidates": [correction]}))
            output = batches / "2026-10-30-test-correction.csv"
            prepare(fixture, output)
            digest = hashlib.sha256(output.read_bytes()).hexdigest()
            manifest = {
                "schema": "reach-scout-discovery-feed-v1",
                "batch_count": 1, "candidate_rows": 1,
                "batches": [{
                    "id": output.stem,
                    "path": "scout-discoveries/batches/" + output.name,
                    "sha256": digest,
                    "record_count": 1,
                    "source_run_ids": ["REACH-SCOUT-TEST-001"]
                }]
            }
            previous = rebuild_discovery_rollup.ROOT
            rebuild_discovery_rollup.ROOT = base
            try:
                actual = rebuild_discovery_rollup.enrich_from_legacy(manifest, None)
                self.assertEqual(actual["discovery_method_counts"]["Independent discovery"], 1)
                self.assertEqual(actual["finding_purpose_counts"]["metadata_correction"], 1)
                self.assertEqual(actual["beyond_direct_api_new_output_review_proposals"], 0)
            finally:
                rebuild_discovery_rollup.ROOT = previous
        correction["provenance"].pop("origin_method")
        with self.assertRaisesRegex(ValueError, "origin_method"):
            compose_rationale(correction["provenance"])



if __name__ == "__main__":
    unittest.main()
