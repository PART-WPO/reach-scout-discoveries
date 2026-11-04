"""Deterministic regression tests for the read-only Scout decision pipeline."""
import csv
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from decision_pipeline import (build_index, check_index_fresh, evaluate, lookup,
                               norm_doi, norm_title)


class DecisionPipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.write_json("scout-operations/reach-comparison-cache/comparison-index.json", {
            "schema": "reach-scout-comparison-cache-v1",
            "source_repo": "PART-WPO/reach-dashboard",
            "source_records": 2,
            "source_manifest_sha256": "a" * 64,
            "verified_shards": [{"path": "mock", "sha256": "b" * 64}] * 150,
            "records": [
                {"reach_uid": "uid-one", "title": "Already Published Report",
                 "dois": ["10.1234/existing"], "links": ["https://noaa.gov/paper/one"],
                 "detail_path": "agent-data/details/part-001.csv"},
                {"reach_uid": "uid-two", "title": "Article without primary DOI",
                 "dois": [], "links": ["https://doi.org/10.1234/secondary"],
                 "detail_path": "agent-data/details/part-002.csv"},
            ],
        })
        rows = [{"Candidate ID": "c-one", "Title": "In Scout", "DOI": "10.1234/scout",
                 "Output URL": "https://example.org/scout"}]
        p = "scout-discoveries/batches/mock.csv"
        self.write_csv(p, rows)
        self.write_json("scout-discoveries/manifest.json", {
            "schema": "reach-scout-discovery-feed-v1",
            "batch_count": 1, "candidate_rows": 1,
            "batches": [{"id": "mock-batch", "path": p, "record_count": 1,
                         "sha256": self.digest(p)}],
        })
        self.write_csv("scout-discoveries/inbox/new.csv",
                       [{"Candidate ID": "", "Title": "Waiting Review",
                         "DOI": "10.1234/waiting",
                         "Output URL": "https://example.org/waiting"}])
        self.index = build_index(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def write_json(self, rel, value):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(value), encoding="utf-8")

    def write_csv(self, rel, rows):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    def digest(self, rel):
        return hashlib.sha256((self.root / rel).read_bytes()).hexdigest()

    def case(self, **overrides):
        obj = {"doi": "10.1234/new", "title": "A New Published Work",
               "cohort": "historical_crossref", "publication_status": "PUBLISHED",
               "primary_award_match": True, "project_attribution": "VERIFIED",
               "checked_sources": ["https://example.org/publisher", "https://example.org/spark"],
               "secondary_identity_checked": True, "required_metadata_verified": True,
               "research_rounds": 1}
        obj.update(overrides)
        return obj

    def test_normalization_and_secondary_doi(self):
        self.assertEqual(norm_doi("https://doi.org/10.1234/Secondary."), "10.1234/secondary")
        self.assertEqual(norm_title("A <scp>New</scp> &amp; Fine Article"), "a new fine article")
        self.assertEqual(lookup(self.index, doi="10.1234/secondary")["status"],
                         "CONFIRMED_PUBLIC_REACH_IDENTITY")

    def test_exact_reach_and_title_only_not_same_disposition(self):
        self.assertEqual(lookup(self.index, doi="10.1234/existing")["status"],
                         "CONFIRMED_PUBLIC_REACH_IDENTITY")
        result = lookup(self.index, doi="10.1234/novel", title="Already Published Report")
        self.assertEqual(result["status"], "POSSIBLE_PUBLIC_REACH_MATCH")

    def test_existing_scout_batch_and_inbox(self):
        self.assertEqual(lookup(self.index, doi="10.1234/scout")["status"],
                         "IN_PUBLIC_SCOUT_QUEUE")
        self.assertEqual(lookup(self.index, url="https://example.org/waiting")["status"],
                         "IN_PUBLIC_SCOUT_QUEUE")

    def test_source_fingerprint_fails_closed_when_inbox_changes(self):
        check_index_fresh(self.root, self.index)
        with (self.root / "scout-discoveries/inbox/new.csv").open("a") as out:
            out.write("changed")
        with self.assertRaisesRegex(ValueError, "inbox changed"):
            check_index_fresh(self.root, self.index)

    def test_manifest_batch_sha_checked(self):
        p = "scout-discoveries/batches/mock.csv"
        with (self.root / p).open("a") as out:
            out.write("tamper")
        with self.assertRaisesRegex(ValueError, "SHA mismatch"):
            build_index(self.root)

    def test_monthly_fast_path_is_human_review_not_approval(self):
        case = self.case(cohort="monthly_api", project_attribution="UNRESOLVED",
                         structured_funding_evidence_verified=True,
                         checked_sources=["https://example.org/publisher"])
        result = evaluate(case, self.index)
        self.assertEqual(result["decision"], "READY_FOR_VALIDATED_DRAFT_PREFLIGHT")
        self.assertEqual(result["review_action"], "HUMAN_REVIEW_PROPOSAL")
        self.assertTrue(result["unverified_private_hub_import"])
        self.assertFalse(result["automatically_staged"])

    def test_monthly_requires_verified_structured_funding_field(self):
        case = self.case(cohort="monthly_api", project_attribution="UNRESOLVED")
        self.assertEqual(evaluate(case, self.index)["decision"],
                         "STRUCTURED_FUNDING_EVIDENCE_REQUIRED")

    def test_historical_requires_positive_same_project_evidence(self):
        case = self.case(project_attribution="UNRESOLVED", research_rounds=2)
        result = evaluate(case, self.index)
        self.assertEqual(result["decision"], "ATTRIBUTION_HOLD_AFTER_BOUNDED_RESEARCH")
        case["project_attribution"] = "VERIFIED"
        self.assertEqual(evaluate(case, self.index)["decision"], "READY_FOR_VALIDATED_DRAFT_PREFLIGHT")

    def test_contradiction_and_preprints_block_staging(self):
        result = evaluate(self.case(project_attribution="CONTRADICTED"), self.index)
        self.assertEqual(result["decision"], "NO_DEMONSTRATED_SAME_WPO_PROJECT")
        result = evaluate(self.case(publication_status="PREPRINT"), self.index)
        self.assertEqual(result["decision"], "PREPRINT_HOLD")

    def test_missing_identity_check_and_metadata_do_not_pass(self):
        self.assertEqual(evaluate(self.case(secondary_identity_checked=False), self.index)["decision"],
                         "CANONICAL_IDENTITY_CHECK_REQUIRED")
        self.assertEqual(evaluate(self.case(required_metadata_verified=False), self.index)["decision"],
                         "METADATA_RECOVERY_REQUIRED")

    def test_private_human_review_and_existing_duplicate_take_precedence(self):
        result = evaluate(self.case(private_review_status="EXISTING_HUMAN_DECISION"), self.index)
        self.assertEqual(result["decision"], "RESPECT_EXISTING_HUMAN_DECISION")
        result = evaluate(self.case(doi="10.1234/existing", title="Already Published Report"), self.index)
        self.assertEqual(result["decision"], "EXISTING_IN_REACH")


if __name__ == "__main__":
    unittest.main()
