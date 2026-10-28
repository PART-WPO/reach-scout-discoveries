import importlib.util
import pathlib
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"tools"))
import harvest as h
import publish_harvest as p

class HarvestUnitTests(unittest.TestCase):
    def test_october_window_inclusive(self):
        self.assertEqual(h.month_window("2026-10"),("2026-10-01","2026-10-31"))
        self.assertEqual(h.month_window("2026-02"),("2026-02-01","2026-02-28"))
        self.assertEqual(h.month_window("2024-02"),("2024-02-01","2024-02-29"))

    def test_malformed_public_award_placeholder(self):
        self.assertEqual(h.clean_award('"'),"")
        self.assertEqual(h.clean_award("  'NA16OAR4590234'  "),"NA16OAR4590234")
        self.assertEqual(h.clean_award("OWAQ16-JTTI-I-1"),"OWAQ16-JTTI-I-1")
        self.assertEqual(h.clean_award("WPO20-SSP-E-1(SSP"),"WPO20-SSP-E-1")
        self.assertEqual(h.clean_award("OWAQOBS001(IAA"),"OWAQOBS001")

    def test_exact_award_not_substring(self):
        self.assertTrue(h.exact_awards(["NA16OAR4590234"],"NA16OAR4590234"))
        self.assertTrue(h.exact_awards(["NA16OAR4590234; NA16OAR4590235"],"NA16OAR4590234"))
        self.assertFalse(h.exact_awards(["NA16OAR45902345"],"NA16OAR4590234"))
        self.assertTrue(h.exact_awards(["OWAQ16-JTTI-I-1"],"OWAQ16-JTTI-I-1"))

    def test_datacite_published_not_registration(self):
        issued={"dates":[{"dateType":"Issued","date":"2026-10-12"}],"registered":"2026-11-02"}
        self.assertEqual(h.datacite_date(issued,"2026-10"),("2026-10-12","published_issued"))
        old={"dates":[{"dateType":"Issued","date":"2023-02-01"}],"registered":"2026-10-15"}
        self.assertEqual(h.datacite_date(old,"2026-10")[1],"published_outside_window")
        registered={"dates":[],"published":"2026","registered":"2026-10-15"}
        self.assertEqual(h.datacite_date(registered,"2026-10"),("","registration_only_publication_unverified"))

    def test_crossref_multiple_pub_dates(self):
        a={"published-online":{"date-parts":[[2026,9,29]]},
           "published-print":{"date-parts":[[2026,10,3]]}}
        self.assertEqual(h.crossref_date(a,"2026-10"),("2026-10-03","published_exact"))
        partial={"published":{"date-parts":[[2026,10]]}}
        self.assertEqual(h.crossref_date(partial,"2026-10"),("","published_month_only"))

    def test_monthly_datacite_undated_candidate_never_infers_day(self):
        a={"doi":"10.5281/example","fundingReferences":[{"awardNumber":"NA16OAR4590234"}],
          "dates":[],"published":"2026","registered":"2026-10-12",
          "titles":[{"title":"Example dataset"}],"types":{"resourceTypeGeneral":"Dataset"}}
        v=h.to_candidate(a,"datacite","NA16OAR4590234","monthly","2026-10")
        self.assertEqual(v["date"],"")
        self.assertEqual(v["outtype"],"3")
        row=p.output_row(p.merge_record([v]),"monthly","2026-10","REACH-MONTHLY-API-2026-10")
        self.assertEqual(row["Publication Date"],"")
        self.assertEqual(row["IR?"],"")
        self.assertEqual(row["Existing REACH Match"],"Unchecked")
        self.assertEqual(len(row),24)
        self.assertEqual(row["Funding Evidence URL"],"https://api.datacite.org/dois/10.5281/example")
        self.assertIn("Scout verification: Not started",row["Scout Discovery Rationale"])

    def test_historical_is_separate_research_inbox(self):
        a={"doi":"10.5281/other","fundingReferences":[{"awardNumber":"WPO22-JTTI-I-1"}],
           "titles":[{"title":"Example"}],"types":{"resourceTypeGeneral":"Software"}}
        v=h.to_candidate(a,"datacite","WPO22-JTTI-I-1","historical","")
        row=p.output_row(p.merge_record([v]),"historical","","REACH-HISTORICAL-DATACITE-2026-10-28")
        self.assertIn("Historical DataCite API Backfill",row["Scout Discovery Rationale"])
        self.assertNotIn("Intake origin: Monthly API",row["Scout Discovery Rationale"])
        self.assertEqual(row["Output Type"],"2")

    def test_combine_award_matches(self):
        v={"doi":"10.1234/z","src":"datacite","award":"NA16OAR4590234",
           "programs":["JTTI"],"projects":["Project A"],"title":"Example",
           "date":"","date_basis":"historical_undated","authors":[],"abstract":"",
           "outtype":"3","evidence":"https://api.datacite.org/dois/10.1234/z"}
        z=p.merge_record([v,dict(v,award="NA16OAR4590235",programs=["Testbeds"])])
        self.assertEqual(z["awards"],["NA16OAR4590234","NA16OAR4590235"])
        self.assertEqual(z["programs"],["JTTI","Testbeds"])

if __name__=="__main__":
    unittest.main()
