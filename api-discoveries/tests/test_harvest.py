import importlib.util
import pathlib
import sys
import unittest
import json
import tempfile
from pathlib import Path
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

    def test_only_primary_spark_award_column_is_searchable(self):
        # A real production failure: SPARK's flattened awards feed includes
        # related-only identifiers; NA19NES4320002 must not seed any API query.
        rows=[
            {"Award Number":"NA23OAR4590379","Match Basis":"primary_noaa_award",
             "Project Title":"Non-Gaussian Ensemble Data Assimilation"},
            {"Award Number":"NA19NES4320002","Match Basis":"related_noaa_award",
             "Project Title":"Non-Gaussian Ensemble Data Assimilation"},
            {"Award Number":"OWAQ16-JTTI-I-1","Match Basis":"primary_unparsed_identifier"},
            {"Award Number":"OWAQ15-R2O-I-1","Match Basis":"related_unparsed_identifier"},
        ]
        primary=h.primary_award_rows(rows)
        self.assertEqual([r["Award Number"] for r in primary],
                         ["NA23OAR4590379","OWAQ16-JTTI-I-1"])
        # The same identifier in a different project must still be included
        # when its OWN row is genuinely primary.
        rows.append({"Award Number":"NA19NES4320002","Match Basis":"primary_noaa_award"})
        self.assertEqual(h.primary_award_rows(rows)[-1]["Award Number"],"NA19NES4320002")

    def test_unknown_spark_match_basis_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"Unrecognized SPARK award Match Basis"):
            h.primary_award_rows([{"Award Number":"NA19NES4320002","Match Basis":""}])
        with self.assertRaisesRegex(ValueError,"Match Basis"):
            h.parse_awards("Award Number,Project Title\\nNA23OAR4590379,Project A\\n")

    def test_exact_award_not_substring(self):
        self.assertTrue(h.exact_awards(["NA16OAR4590234"],"NA16OAR4590234"))
        self.assertTrue(h.exact_awards(["NA16OAR4590234; NA16OAR4590235"],"NA16OAR4590234"))
        self.assertFalse(h.exact_awards(["NA16OAR45902345"],"NA16OAR4590234"))
        self.assertTrue(h.exact_awards(["OWAQ16-JTTI-I-1"],"OWAQ16-JTTI-I-1"))
        # FY25 OARX full task award is distinct from its base FAIN and sibling tasks.
        full="NA25OARX459C0342-T1-01"
        base="NA25OARX459C0342"
        self.assertEqual(h.clean_award(full), full)
        self.assertTrue(h.exact_awards([full], full))
        self.assertFalse(h.exact_awards([full], base))
        self.assertFalse(h.exact_awards([base], full))
        self.assertFalse(h.exact_awards([full.replace("-T1-01", "-T1-02")], full))
        self.assertFalse(h.exact_awards(["X"+full], full))
        self.assertTrue(h.exact_awards([full+"; NA22NWS4320003"],"NA22NWS4320003"))

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

    def test_pending_immutable_corrective_batch_is_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            batches=root/"api-discoveries/batches"
            batches.mkdir(parents=True)
            (batches/"2026-11-01-monthly-api-2026-10-part001.csv").write_text("original")
            data={"superseded_batches":{
                "2026-11-01-monthly-api-2026-10-part001":{
                    "replacement_id":"2026-11-01-monthly-api-2026-10-primary-only-part001"
                }
            }}
            (root/"api-discoveries/supersessions.json").write_text(json.dumps(data))
            import datetime as dt
            release=dt.date(2026,11,1)
            self.assertEqual(p.pending_monthly_correction("2026-10",release,root),"primary-only")
            (batches/"2026-11-01-monthly-api-2026-10-primary-only-part001.csv").write_text("corrected")
            self.assertEqual(p.pending_monthly_correction("2026-10",release,root),"")

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
