"""Regression tests for Scout monthly original fast path and separate expansion."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from build_monthly_decision_queue import build, classify


def original(doi, funded=None, status="needs_more_research", extra=None):
    row = {"source_batch_id": "2026-11-01-monthly-api-2026-10-primary-only-part001",
           "identity": "doi:" + doi, "cohort": "2026-10", "status": status,
           "checked_sources": ["https://example.org/study"], "substantive_research": {
               "funding_assessment": ({"same_project_verified": funded} if funded is not None else {}),
               "identity_and_related_outputs": extra or {},
           }}
    return row


def make(root, cases, leads=None):
    ops = root / "scout-operations"
    ops.mkdir(parents=True)
    (ops / "monthly-triage.json").write_text(json.dumps({
        "schema": "reach-scout-monthly-triage-v1", "entries": cases}))
    (ops / "monthly-expansion-leads.json").write_text(json.dumps({
        "schema": "reach-scout-monthly-expansion-leads-v1", "entries": leads or []}))


class DecisionQueueTests(unittest.TestCase):
    def test_verified_original_is_fast_path_even_with_pending_expansion(self):
        orig = original("10.1234/original", True)
        lead = {"identity": "doi:10.1234/related",
                "original_seed_doi": "10.1234/original",
                "origin_method": "API-seeded expansion",
                "status": "awaiting_independent_verification",
                "project_funding_verified": False,
                "full_reach_and_scout_dedup_verified": False,
                "path_evidence_url": "https://example.org/reference"}
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            make(root, [orig], [lead])
            queue = build(root)
            self.assertEqual(queue["originals"][0]["decision_track"], "original_fast_path_final_checks")
            self.assertTrue(queue["originals"][0]["decision_review_due"])
            self.assertFalse(queue["originals"][0]["explicit_draft_gate_passed"])
            self.assertTrue(queue["originals"][0]["original_review_independent_of_expansion"])
            self.assertEqual(queue["expansion_lead_count"], 1)

    def test_only_explicit_four_part_evidence_gate_can_enable_draft(self):
        row = original("10.1234/original", True)
        row["original_output_gate"] = {
            "same_project_wpo_funding_verified": True,
            "all_reach_and_scout_identities_checked": True,
            "distinct_output_or_canonical_version_verified": True,
            "required_metadata_verified": True,
            "checked_sources": ["https://example.org/publisher", "https://example.org/reach"]}
        self.assertEqual(classify(row)[:2], ("prepare_validated_candidate_draft", True))
        row["original_output_gate"]["required_metadata_verified"] = False
        self.assertFalse(classify(row)[1])
        row["original_output_gate"].pop("all_reach_and_scout_identities_checked")
        with self.assertRaisesRegex(ValueError, "Incomplete explicit"):
            classify(row)

    def test_funding_conflict_cannot_become_draft(self):
        track, ready, blockers = classify(original("10.1234/conflict", False))
        self.assertEqual(track, "funding_or_scope_decision_due")
        self.assertFalse(ready)
        self.assertTrue(blockers)

    def test_zenodo_family_reuses_historical_review_without_duplicate(self):
        row = original("10.5281/zenodo.123", True,
                       extra={"historical_review_unit": "zenodo-mom6",
                              "duplicate_cross_cohort_seed": True})
        track, ready, blockers = classify(row)
        self.assertEqual(track, "reconcile_existing_review_unit")
        self.assertFalse(ready)
        self.assertIn("historical", blockers[0])

    def test_existing_reach_expansion_not_counted_as_new(self):
        orig = original("10.1234/original", True)
        lead = {"identity": "doi:10.1234/old", "original_seed_doi": "10.1234/original",
                "origin_method": "API-seeded expansion", "status": "already_in_reach",
                "reach_id": "reach-000001", "path_evidence_url": "https://example.org/ref"}
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            make(root, [orig], [lead])
            queue = build(root)
            self.assertEqual(queue["expansion_leads_awaiting_independent_verification"], 0)
            self.assertEqual(queue["expansion_leads"][0]["action"], "Do not restage existing REACH output")

    def test_reject_missing_seed_and_duplicate_original(self):
        orig = original("10.1234/original", True)
        bad = {"identity": "doi:10.1234/related", "original_seed_doi": "10.1234/not-present",
               "origin_method": "API-seeded expansion", "status": "awaiting_independent_verification",
               "path_evidence_url": "https://example.org/ref"}
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            make(root, [orig], [bad])
            with self.assertRaisesRegex(ValueError, "Unknown original monthly DOI seed"):
                build(root)
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            make(root, [orig, dict(orig)])
            with self.assertRaisesRegex(ValueError, "Duplicate monthly original"):
                build(root)


if __name__ == "__main__":
    unittest.main()
