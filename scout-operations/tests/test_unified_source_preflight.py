"""Unifying public identity decisions may not fabricate output eligibility."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from unified_source_preflight import derive_record, preflight

class UnifiedPreflightTests(unittest.TestCase):
    def test_all_original_and_related_discovery_modes_covered(self):
        report=preflight()
        cases=report["cases"]
        lanes={x["discovery_lane"] for x in cases}
        self.assertEqual(lanes,{"historical_crossref","historical_datacite",
                                "monthly_api","monthly_related_outputs","independent"})
        self.assertEqual(report["original_and_related_cases_preflighted"],len(cases))
        self.assertEqual(len([x for x in cases if x["discovery_lane"]=="historical_crossref"]),614)
        self.assertEqual(len([x for x in cases if x["discovery_lane"]=="historical_datacite"]),188)
        self.assertEqual(len([x for x in cases if x["discovery_lane"]=="monthly_api"]),13)
        self.assertEqual(len([x for x in cases if x["discovery_lane"]=="monthly_related_outputs"]),6)
        self.assertEqual(len([x for x in cases if x["discovery_lane"]=="independent"]),6)
        self.assertTrue(all(not x["automatically_staged"] and not x["review_state_modified"]
                        and not x["original_disposition_changed"] and not x["seed_expansion_closed"]
                        for x in cases))
        self.assertEqual(report["changes_to_human_dispositions"],0)
        self.assertEqual(report["new_public_review_proposals"],0)
    def test_source_award_numbers_not_trusted_as_verified_primary_award(self):
        r=derive_record("monthly_api",{"DOI":"10.1000/month","Title":"Some study",
            "NOAA Award Number(s)":"NA22OAR4590010"},{"status":"staged_for_hub_import"},set())
        self.assertIsNone(r["primary_award_match"])
        self.assertEqual(r["publication_status"],"NOT_CHECKED")
        self.assertEqual(r["project_attribution"],"NOT_CHECKED")
        self.assertEqual(r["private_review_status"],"NOT_VERIFIED")
    def test_preprint_is_held_even_with_date_and_project_hint(self):
        r=derive_record("historical_datacite",{"DOI":"10.1000/preprint",
            "Publication Date":"2026-05-05","Title":"An unreviewed version"},
            {"award_numbers":["NA23OAR4590000"]},{"10.1000/preprint"})
        self.assertEqual(r["publication_status"],"PREPRINT")
        self.assertIsNone(r["primary_award_match"])
    def test_existing_staged_lead_status_not_changed(self):
        r=derive_record("monthly_related_outputs",{"identity":"doi:10.1000/related",
            "title":"Related article","status":"staged_for_human_review"},
            {"status":"staged_for_human_review"},set())
        self.assertEqual(r["_recorded_status"],"staged_for_human_review")
        self.assertIsNone(r["primary_award_match"])

if __name__=="__main__":unittest.main()
