"""Offline critical-metadata first tests for monthly fast intake."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scout-operations" / "tools"))
from quick_monthly_intake import pre_stage_metadata_recovery, monthly_review_guidance


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

    def test_monthly_guidance_explains_funding_and_remaining_checks(self):
        row = self.row()
        row["Brief Abstract"] = "Original source data included a complete abstract."
        row["NOAA Award Number(s)"] = "NA22OAR4590187"
        entry = {
            "cohort": "2026-10",
            "first_pass_screening": {
                "normalized_reach_exact_lookup_completed": True
            },
            "substantive_research": {
                "funding_assessment": {
                    "same_project_verified": True,
                    "spark_primary_project": "A Weather-Ready Nation Para Todos"
                },
                "identity_and_related_outputs": {
                    "full_alt_link_version_dedup_verified": False,
                    "reach_detail_followup": {
                        "related_existing_reach_ids": ["reach-000765", "reach-000766"]
                    }
                },
                "source_specific_metadata": {
                    "reach_pub_date_basis": "Crossref published-print YYYY-MM normalized"
                }
            }
        }
        notes = monthly_review_guidance(
            entry, row, "fast_track", "primary_award_matched",
            [], "not_needed")
        self.assertEqual(len(notes), 3)
        self.assertTrue(notes[0].startswith("Finding:"))
        self.assertIn("corroborates an output-level WPO award", notes[0])
        self.assertIn("A Weather-Ready Nation Para Todos", notes[0])
        self.assertIn("Check publisher/repository alternative URLs", notes[1])
        self.assertIn("2 already-cataloged related", notes[1])
        self.assertIn("Crossref published-print", notes[1])
        self.assertTrue(notes[2].startswith("Reviewer question:"))
        self.assertNotIn("already approved", " ".join(notes).lower())

    def test_monthly_guidance_does_not_claim_unverified_funding(self):
        row = self.row()
        entry = {
            "cohort": "2026-10",
            "first_pass_screening": {
                "normalized_reach_exact_lookup_completed": True
            },
            "substantive_research": {
                "funding_assessment": {"same_project_verified": False}
            }
        }
        notes = monthly_review_guidance(
            entry, row, "metadata_review", "multiple_project_matches",
            ["Brief Abstract"], "exhausted")
        self.assertIn("human attribution question", notes[0])
        self.assertIn("remains unavailable", notes[0])
        self.assertIn("Confirm which of the listed SPARK", notes[1])
        self.assertIn("Resolve missing Brief Abstract", notes[1])
        self.assertNotIn("verified project", notes[0].lower())

    def test_monthly_prepare_rejects_generic_status_only_guidance(self):
        from prepare_batch import prepare
        import tempfile
        import json
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / "monthly.json"
            target = Path(d) / "2026-11-02-test-monthly-001.csv"
            payload = {
                "candidates": [{
                    "fields": {
                        **self.row(),
                        "Brief Abstract": "Public source provided a valid article abstract.",
                        "Scout Confidence": "Medium",
                        "NOAA Award Number(s)": "NA22OAR4590187",
                        "Source Run ID": "REACH-SCOUT-MONTHLY-FAST-202610"
                    },
                    "provenance": {
                        "classification": "NEW CANDIDATE",
                        "route": "Direct API",
                        "origin_method": "Direct API",
                        "path_evidence": "https://api.crossref.org/works/10.1234/example.study",
                        "intake_origin": "Monthly API",
                        "monthly_intake": "2026-10",
                        "reach_snapshot": "a" * 40,
                        "sources_checked": ["https://api.crossref.org/works/10.1234/example.study"],
                        "funding_basis": "Original primary grant matched to a source SPARK project.",
                        "related_outputs_checked": "Initial source input assessed separately from follow-up expansion.",
                        "notes": ["Needs Investigation"]
                    }
                }]
            }
            source.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "evidence-specific Finding"):
                prepare(source, target)
            self.assertFalse(target.exists())

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
