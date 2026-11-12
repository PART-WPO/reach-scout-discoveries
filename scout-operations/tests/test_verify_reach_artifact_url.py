"""Regression: the exact objective_thresholds code URL is already in REACH."""
import csv
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
from verify_reach_artifact_url import CACHE, artifact_url, verify  # noqa: E402
from cache_attestation import ATTESTATION, git_blob_sha  # noqa: E402

URL = "https://github.com/chrisrac/objective_thresholds"
INDEX = "agent-data/index/part-001.csv"
FIELDNAMES = ["Record ID", "REACH UID", "Output Type", "Award Number(s)",
              "Title", "Link to Output", "Funded By", "Sheet Name",
              "Principal Investigators", "Journal Pub Date", "Detail File"]


class ArtifactUrlVerification(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / CACHE).parent.mkdir(parents=True)
        self.records = [
            {"reach_uid": "reachuid-paper", "record_id": "reach-000066",
             "index_path": INDEX, "links": [
                 "https://repository.library.noaa.gov/view/noaa/58730", URL]},
            {"reach_uid": "reachuid-v1-2db795d7c2e4513ff44d2c5a7fd97532",
             "record_id": "reach-000079", "index_path": INDEX, "links": [URL]},
        ]
        self.rows = [
            {"Record ID": "reach-000066", "REACH UID": "reachuid-paper",
             "Output Type": "1", "Award Number(s)": "NA19OAR4590411",
             "Title": "Development of an Objective Low Flow Identification Method Using Breakpoint Analysis",
             "Link to Output": "https://repository.library.noaa.gov/view/noaa/58730"},
            {"Record ID": "reach-000079",
             "REACH UID": "reachuid-v1-2db795d7c2e4513ff44d2c5a7fd97532",
             "Output Type": "2", "Award Number(s)": "NA19OAR4590411",
             "Title": "Objective low flow (flood) threshold identification using breakpoint analysis",
             "Link to Output": URL},
        ]
        self.save_fixture()

    def save_fixture(self):
        f = io.StringIO()
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(self.rows)
        self.csvbytes = f.getvalue().encode("utf-8")
        cache = {
            "schema": "reach-scout-comparison-cache-v1",
            "source_repo": "PART-WPO/reach-dashboard",
            "source_records": len(self.records),
            "source_manifest_sha256": "test-source-manifest",
            "verified_shards": [{"path": INDEX,
                                 "sha256": hashlib.sha256(self.csvbytes).hexdigest()}],
            "records": self.records,
        }
        (self.root / CACHE).write_text(json.dumps(cache))

    def check(self, url=URL, loader=None):
        return verify(url, root=self.root, load_shard=loader or (lambda path: self.csvbytes))

    def test_exact_primary_code_url_fast_exit_despite_different_article_title(self):
        result = self.check()
        self.assertEqual(result["status"], "EXISTING_REACH_PRIMARY_OUTPUT_URL")
        self.assertEqual([x["record_id"] for x in result["matches"]], ["reach-000079"])
        self.assertEqual(result["matches"][0]["award_numbers"], "NA19OAR4590411")
        self.assertEqual(result["matches"][0]["output_type"], "2")
        self.assertEqual([x["record_id"] for x in result["supporting_link_records"]],
                         ["reach-000066"])
        self.assertTrue(result["matches"][0]["index_sha_matches_cache"])

    def test_github_root_normalization_but_never_forks_or_subpaths(self):
        self.assertEqual(artifact_url("http://www.github.com/CHRISRAC/OBJECTIVE_THRESHOLDS.git/?tab=readme"),
                         artifact_url(URL))
        self.assertNotEqual(artifact_url(URL + "/tree/main"), artifact_url(URL))
        self.assertNotEqual(artifact_url("https://github.com/someoneelse/objective_thresholds"),
                            artifact_url(URL))
        self.assertEqual(self.check("https://github.com/chrisrac/objective_thresholds.git")["status"],
                         "EXISTING_REACH_PRIMARY_OUTPUT_URL")

    def test_supporting_link_alone_is_not_confirmed_artifact_duplicate(self):
        self.rows.pop()
        self.save_fixture()
        result = self.check()
        self.assertEqual(result["status"], "SUPPORTING_LINK_ONLY_FULL_REACH_GATE_REQUIRED")
        self.assertEqual(result["matches"], [])

    def test_unavailable_primary_index_fails_closed(self):
        def fail(path):
            raise ConnectionError("source unavailable")
        result = self.check(loader=fail)
        self.assertEqual(result["status"], "REACH_URL_CHECK_BLOCKED")
        self.assertEqual(result["matches"], [])
        self.assertEqual(len(result["errors"]), 1)

    def test_no_cache_link_is_not_global_negative(self):
        result = self.check("https://github.com/other/repo")
        self.assertEqual(result["status"], "NO_CACHE_LINK_MATCH_FULL_REACH_GATE_STILL_REQUIRED")

    def test_current_official_positive_survives_old_shard_fingerprint(self):
        self.rows[1]["Title"] = "Updated current REACH title"
        # Keep cached SHA: source has changed but exact live primary URL is proof.
        f = io.StringIO()
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        w.writeheader()
        w.writerows(self.rows)
        result = self.check(loader=lambda path: f.getvalue().encode("utf-8"))
        self.assertEqual(result["status"], "EXISTING_REACH_PRIMARY_OUTPUT_URL")
        self.assertFalse(result["matches"][0]["index_sha_matches_cache"])


    def write_attestation(self, manifest=b"fixture-manifest"):
        cache_file = self.root / CACHE
        raw = cache_file.read_bytes()
        proof = {
            "schema": "reach-scout-comparison-attestation-v1",
            "status": "VERIFIED_SNAPSHOT",
            "source_repo": "PART-WPO/reach-dashboard",
            "source_manifest_sha256": hashlib.sha256(manifest).hexdigest(),
            "source_manifest_git_blob_sha": git_blob_sha(manifest),
            "source_csv_sha256_declared": "fixture-csv-sha256",
            "cache_sha256": hashlib.sha256(raw).hexdigest(),
            "cache_git_blob_sha": git_blob_sha(raw),
            "source_records": len(self.records),
            "verified_shard_count": 1,
        }
        cache = json.loads(raw)
        cache["source_manifest_sha256"] = proof["source_manifest_sha256"]
        cache["source_csv_sha256_declared"] = proof["source_csv_sha256_declared"]
        raw = (json.dumps(cache) + "\n").encode()
        cache_file.write_bytes(raw)
        proof["cache_sha256"] = hashlib.sha256(raw).hexdigest()
        proof["cache_git_blob_sha"] = git_blob_sha(raw)
        (self.root / ATTESTATION).write_text(json.dumps(proof))
        return manifest

    def test_existing_primary_url_fast_exit_when_full_cache_unverified(self):
        result = self.check()
        self.assertEqual(result["status"], "EXISTING_REACH_PRIMARY_OUTPUT_URL")
        self.assertEqual(result["cache_verification"]["status"], "NOT_VERIFIED")
        self.assertEqual(result["cache_verification"]["reason"], "ATTESTATION_MISSING")

    def test_existing_primary_url_fast_exit_even_after_actual_cache_sha_mismatch(self):
        self.write_attestation()
        cache_file = self.root / CACHE
        cache = json.loads(cache_file.read_text())
        cache["records"][0]["links"].append("https://example.org/updated")
        cache_file.write_text(json.dumps(cache))
        result = self.check()
        self.assertEqual(result["status"], "EXISTING_REACH_PRIMARY_OUTPUT_URL")
        self.assertEqual(result["cache_verification"]["status"], "SHA_MISMATCH")

    def test_verified_cache_live_manifest_check_is_separate_from_artifact(self):
        manifest = self.write_attestation()
        good = verify(URL, root=self.root, load_shard=lambda _: self.csvbytes,
                      manifest_bytes=manifest)
        self.assertEqual(good["cache_verification"]["status"], "VERIFIED_SNAPSHOT")
        self.assertEqual(good["cache_verification"]["source_freshness"], "CURRENT")
        stale = verify(URL, root=self.root, load_shard=lambda _: self.csvbytes,
                       manifest_bytes=b"new official snapshot")
        self.assertEqual(stale["status"], "EXISTING_REACH_PRIMARY_OUTPUT_URL")
        self.assertEqual(stale["cache_verification"]["status"], "SOURCE_CHANGED")


if __name__ == "__main__":
    unittest.main()
