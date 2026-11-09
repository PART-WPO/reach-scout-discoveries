"""Unifying public identity decisions may not fabricate output eligibility."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from unified_source_preflight import derive_record, preflight, authoritative_effective_decision, load, ROOT, CROSSREF_ROUTING

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
    def test_strict_bulk_crossref_identity_override(self):
        engine={"decision":"EXISTING_IN_REACH"}
        self.assertEqual(authoritative_effective_decision(engine,"LIKELY_IN_REACH",None,
            "10.1000/conflict"),"IDENTITY_REVIEW_REQUIRED_FROM_BULK")
        self.assertEqual(authoritative_effective_decision(engine,"CONFIRMED_IN_REACH",
            "reachuid-v1-123","10.1000/same"),"EXISTING_IN_REACH_VERIFIED_BULK")
        with self.assertRaisesRegex(ValueError,"disagreement"):
            authoritative_effective_decision(engine,"NOT_FOUND_IN_REACH_INDEX",
                                             None,"10.1000/negative")
    def test_only_strict_bulk_verified_crossref_records_count_confirmed(self):
        report=preflight()
        cr=[r for r in report["cases"] if r["discovery_lane"]=="historical_crossref"]
        confirmed=[r for r in cr if r["effective_identity_or_preflight"]=="EXISTING_IN_REACH_VERIFIED_BULK"]
        routing,_=load(ROOT,CROSSREF_ROUTING)
        self.assertEqual(len(confirmed),routing["counts"]["CONFIRMED_IN_REACH"])
        self.assertEqual(report["crossref_bulk_confirms_after_version_guard"],len(confirmed))
        self.assertEqual(sum(x["effective_identity_or_preflight"]=="IDENTITY_REVIEW_REQUIRED_FROM_BULK"
                        for x in cr),routing["counts"]["LIKELY_IN_REACH"])

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
