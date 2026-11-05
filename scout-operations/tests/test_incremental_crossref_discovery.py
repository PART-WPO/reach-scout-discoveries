"""API update discovery is a research lead, never a direct review proposal."""
import sys
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"api-discoveries/tools"))
from incremental_crossref import (
    window,prev_month,crossref_index_updates,project_search_plan,
    query_project_titles,generate,valid_noaa_primary,
)

class IncrementalTests(unittest.TestCase):
    def fixture(self):
        return [{"award":"NA22OAR4590199",
                 "programs":["ESRM"],
                 "projects":["Advancing Probabilistic Extreme Heat Communication for Local Weather Forecast Offices"]}]
    def index(self):
        return {"source_fingerprint":"sha-fixture","records":[],
                "keys":{"doi":{},"title":{},"url":{}}}
    def work(self,doi,awards=None,title="Probabilistic extreme heat forecasts in local weather offices",typ="journal-article"):
        return {"DOI":doi,"title":[title],"URL":"https://doi.org/"+doi,
                "type":typ,"funder":[{"award":awards or ["NA22OAR4590199"]}]}
    def test_month_rollover_and_february(self):
        self.assertEqual(prev_month(date(2026,1,3)),"2025-12")
        self.assertEqual(window("2028-02"),("2028-02-01","2028-02-29"))
        with self.assertRaises(ValueError): window("2026-13")
    def test_nonstandard_primary_labels_are_recorded_not_queried(self):
        self.assertFalse(valid_noaa_primary("BOP"))
        self.assertFalse(valid_noaa_primary("UNK"))
        self.assertFalse(valid_noaa_primary("NA19NES4320002"))
        self.assertTrue(valid_noaa_primary("NA25OARX459C0342-T1-01"))
        awards=[{"award":"BOP","programs":["ESRM"],"projects":["General budget research program"]}]+self.fixture()
        calls=[]
        def fake(url,params):
            calls.append(params)
            return {"message":{"items":[]}}
        with patch("incremental_crossref.fetch",side_effect=fake):
            data=generate("2026-10",pilot=True,awards=awards,
                          index=self.index(),preprints=set())
        self.assertEqual(data["non_normalized_primary_identifiers_skipped"],1)
        self.assertEqual(data["spark_primary_awards_queried"],1)
        self.assertNotIn("BOP",str(calls))
        self.assertEqual(data["new_public_scout_candidates"],0)

    def test_index_filter_is_not_publication_date(self):
        recorded=[]
        def fake(url,params):
            recorded.append(params)
            return {"message":{"items":[self.work("10.1000/old"),
                                        self.work("10.1000/unrelated",awards=["NA22OAR4597777"])]}}
        with patch("incremental_crossref.fetch",side_effect=fake):
            x=crossref_index_updates("NA22OAR4590199","2026-10-01","2026-10-31")
        self.assertEqual(len(x),1)
        self.assertIn("from-index-date:2026-10-01",recorded[0]["filter"])
        self.assertIn("until-index-date:2026-10-31",recorded[0]["filter"])
        self.assertNotIn("pub-date",recorded[0]["filter"])
        self.assertIn("award.number:NA22OAR4590199",recorded[0]["filter"])
    def test_partial_cursor_ceiling_fails_not_false_empty(self):
        with patch("incremental_crossref.fetch",return_value={
            "message":{"items":[self.work("10.1000/a")],"next-cursor":"step2"}}):
            with self.assertRaisesRegex(RuntimeError,"maximum pages"):
                crossref_index_updates("NA22OAR4590199","2026-10-01","2026-10-31",
                                       max_pages=1,page_size=1)
    def test_project_title_leads_must_have_two_distinctive_terms(self):
        plan=project_search_plan(self.fixture())
        self.assertEqual(len(plan),1)
        with patch("incremental_crossref.fetch",return_value={"message":{
            "items":[self.work("10.1000/good",title="Extreme heat communication for weather offices"),
                     self.work("10.1000/bad",title="A study of unrelated white blood cells")]}}):
            result=query_project_titles(plan[0])
        self.assertEqual(len(result),1)
        self.assertEqual(result[0][0]["DOI"],"10.1000/good")
    def test_generate_leads_are_not_hub_additions_or_pubdate_claims(self):
        work=self.work("10.1000/older")
        work["indexed"]={"date-time":"2026-10-15T10:00:00Z"}
        work["published-print"]={"date-parts":[[2021,2]]}
        def fake(url,params):
            if "filter" in params:return {"message":{"items":[work]}}
            return {"message":{"items":[self.work("10.1000/project",
                    title="Extreme Heat Communication for Local Weather Offices",awards=["NOT-WPO"])]}}
        with patch("incremental_crossref.fetch",side_effect=fake):
            report=generate("2026-10",pilot=True,awards=self.fixture(),
                            index=self.index(),preprints={"10.1000/project"})
        self.assertTrue(report["complete_selected_awards"])
        self.assertEqual(report["spark_primary_awards_queried"],1)
        self.assertEqual(report["new_public_scout_candidates"],0)
        self.assertEqual(report["new_private_discovery_hub_imports"],0)
        self.assertEqual(report["new_reach_additions"],0)
        index_lead=next(e for e in report["leads"] if e["source_kind"]=="CROSSREF_INDEX_UPDATE")
        self.assertEqual(index_lead["funding_status"],"STRUCTURED_AWARD_LEAD_NOT_PROJECT_VERIFIED")
        self.assertNotIn("pub_date",index_lead)
        project_lead=next(e for e in report["leads"] if e["source_kind"]=="PROJECT_TITLE_SEARCH")
        self.assertTrue(project_lead["preprint_original_hold"])
        self.assertEqual(project_lead["required_next_action"],"TRACK_PREPRINT_OFFICIAL_JOURNAL_VERSION")
        self.assertEqual(project_lead["funding_status"],"PROJECT_TITLE_QUERY_ONLY_NOT_WPO_VERIFIED")

if __name__=="__main__":unittest.main()
