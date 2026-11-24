"""Cross-snapshot evidence may survive relocation, and must survive conflict checks."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCREENING = ROOT / "scout-operations/historical-crossref-screening"
spec = importlib.util.spec_from_file_location("routing", SCREENING / "build_actionable_routing.py")
routing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(routing)


class CrossSnapshotIdentityTests(unittest.TestCase):
    def setUp(self):
        self.proof = json.loads((SCREENING / "publisher-identity-evidence.json").read_text())["publisher_article"]
        self.doi = self.proof["doi"]
        self.titles = {routing.norm_title(self.proof["title"])}
        self.record = {"reach_uid": self.proof["reach_uid"], "title": self.proof["title"],
                       "links": [self.proof["publisher_url"]], "dois": []}

    def test_relocation_preserves_independently_verified_publisher_join(self):
        for record_id, shard in (("reach-000639", "part-078.csv"), ("reach-000672", "part-080.csv")):
            self.assertTrue(routing.publisher_match(
                self.proof, self.doi, self.titles, dict(self.record, record_id=record_id, detail_path=shard)))

    def test_title_uid_or_wrong_doi_never_suffices(self):
        for changes in ({"links": ["https://ieeexplore.ieee.org/document/9088231"]},
                        {"dois": ["10.1109/other"]},
                        {"title": "Different article"}, {"reach_uid": "different-uid"}):
            with self.subTest(changes=changes):
                self.assertFalse(routing.publisher_match(
                    self.proof, self.doi, self.titles, dict(self.record, **changes)))

    def test_publisher_join_does_not_override_multiple_identity_conflict(self):
        hit = {"reach_uid": "a", "title_hit": True, "publisher_url_hit": True}
        other = {"reach_uid": "b", "title_hit": True}
        decision = routing.bulk_decide([hit, other], {}, title_available=True)
        self.assertEqual(decision["status"], "NEEDS_IDENTITY_REVIEW")

    def test_current_publication_and_preprint_resolve_separately(self):
        doc = routing.build()
        records = {r["doi"]: r for r in doc["entries"]}
        self.assertEqual(records[self.doi]["bulk_identity_gate"]["basis"],
                         "VERIFIED_PUBLISHER_DOI_TO_REACH_URL_AND_TITLE")
        self.assertEqual(records["10.5194/egusphere-2025-1142"]["outcome"], "LIKELY_IN_REACH")
        self.assertEqual(records["10.5194/gmd-18-7969-2025"]["outcome"], "CONFIRMED_IN_REACH")
