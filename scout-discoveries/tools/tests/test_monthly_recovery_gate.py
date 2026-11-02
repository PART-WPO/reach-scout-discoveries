"""Offline critical-metadata first tests for monthly fast intake."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scout-operations" / "tools"))
from quick_monthly_intake import pre_stage_metadata_recovery


class MonthlyCriticalMetadataGateTests(unittest.TestCase):
    def row(self):
        return {
            "Title": "Example publicly archived study",
            "DOI": "10.1234/example.study",
            "Output URL": "https://doi.org/10.1234/example.study",
            "Output Type": "1",
            "Authors / PI": "A. Investigator",
            "Publication Date": "2026-10-01",
            "Brief Abstract": "",
            "Evidence URL": "https://api.crossref.org/works/10.1234/example.study",
            "Funding Evidence URL": "https://example.org/verified-funding",
        }

    def check(self):
        return {"method": "exact_doi_primary_source",
                "url": "https://example.org/verified-publication",
                "result": "Publisher confirms abstract and DOI identity."}

    def test_new_missing_abstract_requires_research_before_staging(self):
        _, remaining, state, checks = pre_stage_metadata_recovery({}, self.row())
        self.assertEqual(state, "required")
        self.assertEqual(remaining, ["Brief Abstract"])
        self.assertEqual(checks, [])

    def test_verified_recovery_uses_source_and_clears_blocker(self):
        abstract = "This publication analyzes documented severe weather safety practices " + "and independently verified workplace preparedness findings. " * 3
        ledger = {"metadata_recovery": {
            "status": "resolved", "checks": [self.check()],
            "resolved_fields": {"Brief Abstract": {
                "value": abstract, "evidence_url": "https://example.org/verified-publication"}}}}
        row, remaining, state, checks = pre_stage_metadata_recovery(ledger, self.row())
        self.assertEqual(state, "resolved")
        self.assertEqual(remaining, [])
        self.assertEqual(row["Brief Abstract"], abstract.strip())
        self.assertEqual(len(checks), 1)

    def test_exhausted_checks_allow_explicit_human_review_not_automatic_approval(self):
        ledger = {"metadata_recovery": {"status": "exhausted", "checks": [self.check()]}}
        _, remaining, state, _ = pre_stage_metadata_recovery(ledger, self.row())
        self.assertEqual(state, "exhausted")
        self.assertIn("Brief Abstract", remaining)

    def test_recovery_rejects_unverified_public_source(self):
        ledger = {"metadata_recovery": {
            "status": "resolved", "checks": [self.check()],
            "resolved_fields": {"Brief Abstract": {
                "value": "A " * 50, "evidence_url": "https://different.example.com/not-checked"}}}}
        with self.assertRaisesRegex(ValueError, "checked source"):
            pre_stage_metadata_recovery(ledger, self.row())

    def test_invalid_recovered_date_rejected(self):
        row = self.row()
        row["Brief Abstract"] = "This original abstract is complete and evidence-backed."
        row["Publication Date"] = ""
        ledger = {"metadata_recovery": {
            "status": "resolved", "checks": [self.check()],
            "resolved_fields": {"Publication Date": {
                "value": "2026-13-40", "evidence_url": "https://example.org/verified-publication"}}}}
        with self.assertRaisesRegex(ValueError, "YYYY-MM-DD"):
            pre_stage_metadata_recovery(ledger, row)

    def test_valid_recovered_date_with_source_is_accepted(self):
        row = self.row()
        row["Brief Abstract"] = "The original abstract is verified and complete."
        row["Publication Date"] = ""
        ledger = {"metadata_recovery": {
            "status": "resolved", "checks": [self.check()],
            "resolved_fields": {"Publication Date": {
                "value": "2026-10-01",
                "evidence_url": "https://example.org/verified-publication"}}}}
        enriched, missing, state, _ = pre_stage_metadata_recovery(ledger, row)
        self.assertEqual(state, "resolved")
        self.assertEqual(enriched["Publication Date"], "2026-10-01")
        self.assertEqual(missing, [])

    def test_complete_api_record_keeps_fast_path(self):
        row = self.row()
        row["Brief Abstract"] = "Complete source provided an authoritative abstract."
        result, remaining, state, checks = pre_stage_metadata_recovery({}, row)
        self.assertEqual(state, "not_needed")
        self.assertEqual(remaining, [])
        self.assertEqual(checks, [])
        self.assertEqual(result["Brief Abstract"], row["Brief Abstract"])


if __name__ == "__main__":
    unittest.main()
