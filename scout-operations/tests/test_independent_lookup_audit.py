"""Exercise real vs cached provider attempts and stale snapshot safety."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from audit_independent_lookup import audit, SOURCES


class IndependentAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_only_uncached_attempts_are_counted(self):
        rel, schema, field = SOURCES["independent-doi"]
        p = self.root / rel
        p.parent.mkdir(parents=True)
        p.write_text(json.dumps({
            "schema": schema, "public_identity_source_fingerprint": "f"*64,
            field: [
                {"doi": "10.1234/cached", "metadata_memory_hit": True,
                 "metadata_memory_reason": "VERIFIED_CACHED_OFFICIAL_METADATA",
                 "metadata": {"status": "ok", "attempts": [
                     {"provider": "datacite"}, {"provider": "crossref"}]}},
                {"doi": "10.1234/live", "metadata_memory_hit": False,
                 "metadata_memory_reason": "SOURCE_TTL_EXPIRED",
                 "metadata": {"status": "ok", "attempts": [
                     {"provider": "datacite"}, {"provider": "crossref"}]}},
            ]
        }))
        report = audit(self.root, "independent-doi")
        self.assertEqual(report["verified_persistent_metadata_cache_hits"], 1)
        self.assertEqual(report["provider_http_requests_observed"], 2)
        self.assertIsNone(report["avoided_requests_measured"])
        self.assertEqual(len(report["prior_metadata_content_sha256_reused"]), 1)

    def test_missing_actual_attempts_is_not_zero_requests(self):
        rel, schema, field = SOURCES["independent-metadata"]
        p = self.root / rel
        p.parent.mkdir(parents=True)
        p.write_text(json.dumps({
            "schema": schema, field: [
                {"doi": "10.1234/miss", "metadata_memory_hit": False,
                 "metadata_memory_reason": "SOURCE_TTL_EXPIRED",
                 "metadata": {"status": "unavailable_or_not_found"}}]
        }))
        self.assertIsNone(audit(self.root, "independent-metadata")[
            "provider_http_requests_observed"])


if __name__ == "__main__":
    unittest.main()
