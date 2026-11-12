"""Cache SHA/freshness regression: no source failures may imply novelty."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
from cache_attestation import CACHE, ATTESTATION, git_blob_sha, verify_snapshot


class CacheAttestationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / CACHE).parent.mkdir(parents=True)
        self.manifest = b'{"source":{"rows":1},"index":{"files":[]}}'
        self.cache = {
            "schema": "reach-scout-comparison-cache-v1",
            "source_repo": "PART-WPO/reach-dashboard",
            "source_manifest_sha256": hashlib.sha256(self.manifest).hexdigest(),
            "source_csv_sha256_declared": "source-csv-sha256",
            "source_records": 1,
            "verified_shards": [{"path": "agent-data/index/part-001.csv",
                                 "sha256": "fake-shard-sha256"}],
            "records": [{"record_id": "reach-000079"}],
        }
        self.write_cache()

    def write_cache(self):
        raw = (json.dumps(self.cache, sort_keys=True) + "\n").encode()
        (self.root / CACHE).write_bytes(raw)
        return raw

    def write_proof(self):
        raw = (self.root / CACHE).read_bytes()
        proof = {
            "schema": "reach-scout-comparison-attestation-v1",
            "status": "VERIFIED_SNAPSHOT",
            "source_repo": "PART-WPO/reach-dashboard",
            "source_manifest_sha256": self.cache["source_manifest_sha256"],
            "source_manifest_git_blob_sha": git_blob_sha(self.manifest),
            "source_csv_sha256_declared": self.cache["source_csv_sha256_declared"],
            "cache_sha256": hashlib.sha256(raw).hexdigest(),
            "cache_git_blob_sha": git_blob_sha(raw),
            "source_records": 1,
            "verified_shard_count": 1,
        }
        (self.root / ATTESTATION).write_text(json.dumps(proof))

    def test_no_proof_reports_not_verified_not_mismatch(self):
        result = verify_snapshot(root=self.root)
        self.assertEqual(result["status"], "NOT_VERIFIED")
        self.assertEqual(result["reason"], "ATTESTATION_MISSING")

    def test_attested_snapshot_can_be_reused_without_source_download(self):
        self.write_proof()
        result = verify_snapshot(root=self.root)
        self.assertEqual(result["status"], "VERIFIED_SNAPSHOT")
        self.assertEqual(result["source_freshness"], "NOT_CHECKED")
        self.assertEqual(result["verified_shard_count"], 1)

    def test_live_manifest_same_fingerprint_is_current(self):
        self.write_proof()
        result = verify_snapshot(root=self.root, manifest_bytes=self.manifest)
        self.assertEqual(result["status"], "VERIFIED_SNAPSHOT")
        self.assertEqual(result["source_freshness"], "CURRENT")

    def test_source_manifest_changed_is_stale_not_sha_mismatch(self):
        self.write_proof()
        result = verify_snapshot(root=self.root, manifest_bytes=b'{"new":true}')
        self.assertEqual(result["status"], "SOURCE_CHANGED")
        self.assertEqual(result["reason"], "LIVE_SOURCE_MANIFEST_CHANGED")

    def test_actual_cache_change_is_sha_mismatch(self):
        self.write_proof()
        self.cache["records"][0]["record_id"] = "reach-changed"
        self.write_cache()
        result = verify_snapshot(root=self.root)
        self.assertEqual(result["status"], "SHA_MISMATCH")
        self.assertEqual(result["reason"], "CACHE_CONTENT_HASH_MISMATCH")

    def test_invalid_counts_cannot_be_reused(self):
        self.write_proof()
        p = self.root / ATTESTATION
        proof = json.loads(p.read_text())
        proof["verified_shard_count"] = 2
        p.write_text(json.dumps(proof))
        result = verify_snapshot(root=self.root)
        self.assertEqual(result["status"], "NOT_VERIFIED")


if __name__ == "__main__":
    unittest.main()
