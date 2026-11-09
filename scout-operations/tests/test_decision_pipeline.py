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
from decision_pipeline import (VERSION, build_index, check_index_fresh, current_checkpoints,
                               evaluate, lookup, norm_doi, norm_title)


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
        self.assertEqual(lookup(self.index, doi="10.1234/secondary", title="Article without primary DOI")["status"],
                         "CONFIRMED_PUBLIC_REACH_IDENTITY")

    def test_exact_reach_and_title_only_not_same_disposition(self):
        self.assertEqual(lookup(self.index, doi="10.1234/existing", title="Already Published Report")["status"],
                         "CONFIRMED_PUBLIC_REACH_IDENTITY")
        result = lookup(self.index, doi="10.1234/novel", title="Already Published Report")
        self.assertEqual(result["status"], "POSSIBLE_PUBLIC_REACH_MATCH")

    def test_existing_scout_batch_and_inbox(self):
        self.assertEqual(lookup(self.index, doi="10.1234/scout", title="In Scout")["status"],
                         "IN_PUBLIC_SCOUT_QUEUE")
        self.assertEqual(lookup(self.index, url="https://example.org/waiting", title="Waiting Review")["status"],
                         "IN_PUBLIC_SCOUT_QUEUE")

    def test_exact_doi_missing_title_is_not_confirmed(self):
        result = lookup(self.index, doi="10.1234/existing")
        self.assertEqual(result["status"], "POSSIBLE_PUBLIC_REACH_MATCH")
        self.assertEqual(result["reason"], "SOURCE_TITLE_REQUIRED")

    def test_exact_doi_wrong_title_is_not_confirmed(self):
        result = lookup(self.index, doi="10.1234/existing", title="Unrelated New Dataset")
        self.assertEqual(result["status"], "POSSIBLE_PUBLIC_REACH_MATCH")
        self.assertEqual(result["reason"], "IDENTIFIER_TITLE_OR_VERSION_REVIEW")
        self.assertEqual(evaluate(self.case(doi="10.1234/existing",
                         title="Unrelated New Dataset"), self.index)["decision"],
                         "IDENTITY_REVIEW_REQUIRED")

    def test_multiple_reach_uids_for_doi_are_not_confirmed(self):
        # Separate REACH records must never be silently collapsed.
        self.index["records"].append({
            "source": "REACH", "identity": "uid-three",
            "title": "Already Published Report", "location": "part-003.csv",
            "dois": ["10.1234/existing"], "urls": []
        })
        pos = len(self.index["records"]) - 1
        self.index["keys"]["doi"]["10.1234/existing"].append(pos)
        self.index["keys"]["title"]["already published report"].append(pos)
        result = lookup(self.index, doi="10.1234/existing",
                        title="Already Published Report")
        self.assertEqual(result["status"], "POSSIBLE_PUBLIC_REACH_MATCH")
        self.assertEqual(result["reason"], "MULTIPLE_REACH_IDENTITIES")

    def test_scout_queue_same_identifier_different_titles_requires_review(self):
        result = lookup(self.index, doi="10.1234/scout",
                        title="A Dataset Distinct from the Scout Publication")
        self.assertEqual(result["status"], "POSSIBLE_SCOUT_QUEUE_MATCH")
        self.assertEqual(result["reason"], "IDENTIFIER_TITLE_OR_VERSION_REVIEW")

    def test_normalized_same_title_different_identifier_is_not_duplicate(self):
        result = lookup(self.index, doi="10.1234/new-dataset",
                        title="Already Published Report")
        self.assertEqual(result["status"], "POSSIBLE_PUBLIC_REACH_MATCH")
        self.assertNotEqual(result["status"], "CONFIRMED_PUBLIC_REACH_IDENTITY")

    def test_current_checkpoint_ignores_old_immutable_revisions(self):
        case = self.case(doi="10.1234/new")
        fingerprint = hashlib.sha256(json.dumps({
            "case": case, "index": self.index["source_fingerprint"],
            "version": VERSION}, sort_keys=True).encode()).hexdigest()
        hash_id = hashlib.sha256(case["doi"].encode()).hexdigest()[:16]
        folder = "scout-operations/case-checkpoints/doi-" + hash_id
        self.write_json(folder + "/rev-" + fingerprint[:20] + ".json", {
            "case_input": case, "input_fingerprint": fingerprint,
            "index_fingerprint": self.index["source_fingerprint"],
            "evaluation": {"doi": case["doi"], "decision": "READY_FOR_VALIDATED_DRAFT_PREFLIGHT"}})
        self.write_json(folder + "/rev-obsolete.json", {
            "case_input": case, "input_fingerprint": "outdated",
            "index_fingerprint": self.index["source_fingerprint"]})
        rows = current_checkpoints(self.index, [case], self.root)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["input_fingerprint"], fingerprint)
        with self.assertRaisesRegex(ValueError, "checkpoint missing"):
            current_checkpoints(self.index, [self.case(doi="10.1234/another")], self.root)

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
