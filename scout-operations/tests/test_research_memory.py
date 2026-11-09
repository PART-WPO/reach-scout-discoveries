"""Source-sha-pinned DOI metadata reuse without any new author-name index."""
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from research_memory import (
    INDEX, PARSER, REPORTS, SCHEMA, build_index, canonical,
    key, metadata_result, read_index, write_index,
)


class SourceAwareMemoryTests(unittest.TestCase):
    doi = "10.1234/public-example"
    now = datetime(2026, 11, 9, 14, 30, tzinfo=timezone.utc)

    def fixture(self, *, status="ok", provider="crossref", preprint=False):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        script = root / PARSER
        script.parent.mkdir(parents=True)
        script.write_text("# public official resolver policy v1\n")
        md = {
            "status": status, "provider": provider,
            "title": "Atmospheric Air Quality",
            "publication_status": "preprint" if preprint else "official_journal_article",
            "evidence": "https://api.crossref.org/works/" + self.doi,
            # Already present in the existing public lookup report, but
            # never copied to the new hashed research memory index.
            "creators": ["Public A Researcher"],
            "pub_date": "2026-10-02",
        }
        rec = {
            "doi": self.doi,
            "metadata": md,
            "metadata_observed_at": self.now.isoformat(),
            "identity_gate": {"status": "NO_PUBLIC_IDENTITY_MATCH"}
        }
        file = root / REPORTS[0][0]
        file.parent.mkdir(parents=True)
        file.write_text(json.dumps({"schema": REPORTS[0][1],
                                    "records": [rec]}))
        return root, file, rec

    def test_build_index_uses_only_pointers_never_names_or_reviewer_state(self):
        root, path, rec = self.fixture()
        doc = write_index(root)
        self.assertEqual(doc["schema"], SCHEMA)
        self.assertEqual(doc["total_distinct_doi_keys"], 1)
        self.assertEqual(read_index(root), doc)
        self.assertNotIn(self.doi, (root / INDEX).read_text())
        self.assertNotIn("Public A Researcher", (root / INDEX).read_text())
        self.assertNotIn("creators", (root / INDEX).read_text())
        self.assertEqual(len(next(iter(doc["entries"]))), 64)
        self.assertFalse(doc["automatic_staging"])
        self.assertEqual(doc["private_reviewer_state"], "NOT_VERIFIED")

    def test_seven_day_reuse_and_no_hidden_ttl_reset(self):
        root, path, rec = self.fixture()
        mem = write_index(root)
        out, captured, reason = metadata_result(root, mem, self.doi,
                                                now=self.now + timedelta(days=2))
        self.assertEqual(out, rec["metadata"])
        self.assertEqual(reason, "VERIFIED_CACHED_OFFICIAL_METADATA")
        self.assertEqual(captured, self.now.isoformat())
        out, captured, reason = metadata_result(root, mem, self.doi,
                                                now=self.now + timedelta(days=8))
        self.assertIsNone(out)
        self.assertEqual(reason, "SOURCE_TTL_EXPIRED")

    def test_source_tamper_and_parser_change_invalidate_cache(self):
        root, path, rec = self.fixture()
        mem = write_index(root)
        report = json.loads(path.read_text())
        report["records"][0]["metadata"]["title"] = "Tampered"
        path.write_text(json.dumps(report))
        out, _, reason = metadata_result(root, mem, self.doi,
                                         now=self.now + timedelta(hours=1))
        self.assertIsNone(out)
        self.assertEqual(reason, "SOURCE_REPORT_CHANGED")
        (root / PARSER).write_text("# resolver policy v2\n")
        out, _, reason = metadata_result(root, mem, self.doi,
                                         now=self.now + timedelta(hours=1))
        self.assertIsNone(out)
        self.assertEqual(reason, "PARSER_POLICY_CHANGED")

    def test_preprint_never_uses_cached_published_date(self):
        root, path, rec = self.fixture(preprint=True)
        mem = write_index(root)
        response, _, reason = metadata_result(root, mem, self.doi,
                                              now=self.now + timedelta(minutes=1))
        self.assertIsNone(response)
        self.assertEqual(reason, "PREPRINT_REQUIRES_FRESH_SOURCE")

    def test_unavailable_sources_retry_in_six_hours(self):
        root, path, rec = self.fixture(status="unavailable_or_not_found",
                                      provider=None)
        mem = write_index(root)
        response, _, reason = metadata_result(root, mem, self.doi,
                                              now=self.now + timedelta(hours=1))
        self.assertEqual(response["status"], "unavailable_or_not_found")
        self.assertEqual(reason, "VERIFIED_CACHED_OFFICIAL_METADATA")
        response, _, reason = metadata_result(root, mem, self.doi,
                                              now=self.now + timedelta(hours=7))
        self.assertIsNone(response)
        self.assertEqual(reason, "SOURCE_TTL_EXPIRED")

    def test_old_legacy_report_is_not_assumed_recent(self):
        root, path, rec = self.fixture()
        doc = json.loads(path.read_text())
        del doc["records"][0]["metadata_observed_at"]
        path.write_text(json.dumps(doc))
        mem = write_index(root)
        self.assertEqual(mem["total_distinct_doi_keys"], 0)
        response, _, reason = metadata_result(root, mem, self.doi,
                                              now=self.now)
        self.assertIsNone(response)
        self.assertEqual(reason, "NO_PREVIOUS_DOI_EVIDENCE")

    def test_forged_doikey_and_unapproved_paths_fail_closed(self):
        root, path, rec = self.fixture()
        mem = write_index(root)
        mem["entries"][key(self.doi)]["doi_key"] = key("10.1234/other")
        with self.assertRaisesRegex(ValueError, "identity conflict"):
            metadata_result(root, mem, self.doi, now=self.now)
        mem["entries"][key(self.doi)]["doi_key"] = key(self.doi)
        mem["entries"][key(self.doi)]["source_report"] = "private-discovery-hub.csv"
        with self.assertRaisesRegex(ValueError, "unapproved source"):
            metadata_result(root, mem, self.doi, now=self.now)

    def test_latest_independent_report_can_be_reused_from_other_mode(self):
        root, path, rec = self.fixture()
        second = root / REPORTS[1][0]
        second.parent.mkdir(parents=True)
        second.write_text(json.dumps({
            "schema": REPORTS[1][1],
            "doi_records": [{
                **rec,
                "metadata_observed_at": (self.now + timedelta(hours=1)).isoformat(),
                "metadata": {**rec["metadata"], "title": "Updated Air Quality"}
            }]
        }))
        memory = write_index(root)
        retrieved, observed, reason = metadata_result(root, memory, self.doi,
                                          now=self.now + timedelta(hours=2))
        self.assertEqual(retrieved["title"], "Updated Air Quality")
        self.assertIn("15:30", observed)
        self.assertEqual(reason, "VERIFIED_CACHED_OFFICIAL_METADATA")


if __name__ == "__main__":
    unittest.main()
