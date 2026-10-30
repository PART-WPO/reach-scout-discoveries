#!/usr/bin/env python3
"""Offline regression tests: WPO prefers Crossref print, online fallback, month -> day 01."""
import importlib.util
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
m=module(ROOT/"scout-operations/tools/audit_doi_metadata.py","doi_checkpoint")
h=module(ROOT/"api-discoveries/tools/harvest.py","monthly_harvest")

class CrossrefMetadataTests(unittest.TestCase):
    def test_date_parts_precision_remains_true(self):
        self.assertEqual(m.crossref_date_parts({"date-parts":[[2024,8,15]]})["full_date"],"2024-08-15")
        self.assertEqual(m.crossref_date_parts({"date-parts":[[2024,8]]})["value"],"2024-08")
        self.assertEqual(m.crossref_date_parts({"date-parts":[[2024,8]]})["full_date"],"")
        self.assertEqual(m.crossref_date_parts({"date-parts":[[2024]]})["value"],"2024")
        self.assertEqual(m.crossref_date_parts({"date-parts":[[2024]]})["full_date"],"")

    def test_print_preferred_over_online_even_if_later(self):
        a={"type":"journal-article",
           "published-online":{"date-parts":[[2024,4,10]]},
           "published-print":{"date-parts":[[2024,6,25]]},
           "created":{"date-parts":[[2023,12,12]]}}
        x=m.crossref_date_info(a)
        self.assertEqual(x["pub_date"],"2024-06-25")
        self.assertEqual(x["pub_date_basis"],"published-print")
        self.assertFalse(x["pub_date_imputed_first_of_month"])
        self.assertEqual(x["publication_dates"]["published-online"]["full_date"],"2024-04-10")

    def test_month_only_print_over_online_full(self):
        a={"type":"journal-article",
           "published-print":{"date-parts":[[2020,12]]},
           "published-online":{"date-parts":[[2020,5,6]]},
           "created":{"date-parts":[[2020,5,6]]}}
        x=m.crossref_date_info(a)
        self.assertEqual(x["pub_date"],"2020-12-01")
        self.assertEqual(x["pub_date_basis"],"published-print")
        self.assertEqual(x["pub_date_precision"],"month")
        self.assertTrue(x["pub_date_imputed_first_of_month"])
        self.assertEqual(x["source_full_date"],"")

    def test_online_only_dynamic_fallback(self):
        x=m.crossref_date_info({"type":"journal-article",
              "published-online":{"date-parts":[[2025,3]]}})
        self.assertEqual(x["pub_date"],"2025-03-01")
        self.assertEqual(x["pub_date_basis"],"published-online")

    def test_online_full_when_no_print(self):
        x=m.crossref_date_info({"type":"journal-article",
              "published-online":{"date-parts":[[2025,3,17]]}})
        self.assertEqual(x["pub_date"],"2025-03-17")
        self.assertEqual(x["pub_date_precision"],"day")

    def test_print_year_only_falls_back_online_month(self):
        x=m.crossref_date_info({"type":"journal-article",
              "published-print":{"date-parts":[[2025]]},
              "published-online":{"date-parts":[[2025,3]]}})
        self.assertEqual(x["pub_date"],"2025-03-01")
        self.assertEqual(x["pub_date_basis"],"published-online")

    def test_preprint_prefers_posted(self):
        x=m.crossref_date_info({"type":"posted-content",
              "posted":{"date-parts":[[2025,2]]},
              "published-online":{"date-parts":[[2025,7,15]]}})
        self.assertEqual(x["pub_date"],"2025-02-01")
        self.assertEqual(x["pub_date_basis"],"posted")

    def test_created_not_used_for_publication_date(self):
        x=m.crossref_date_info({"type":"journal-article",
              "created":{"date-parts":[[2025,1,5]]},
              "published-online":{"date-parts":[[2025]]}})
        self.assertEqual(x["pub_date"],"")
        self.assertEqual(x["crossref_created"]["full_date"],"2025-01-05")

    def test_invalid_dates(self):
        self.assertFalse(m.crossref_date_parts({"date-parts":[[2025,2,30]]})["full_date"])
        self.assertFalse(m.crossref_date_parts({"date-parts":[[2025,13,2]]})["full_date"])

    def test_ieee_lookup_prefers_december_print(self):
        doc={"message":{"DOI":"10.1109/TGRS.2020.2984458","type":"journal-article",
              "title":["Ceilometer-Based Rain-Rate Estimation"],
              "created":{"date-parts":[[2020,5,6]]},
              "published-print":{"date-parts":[[2020,12]]}}}
        with patch.object(m,"get",return_value=doc):
            r=m.fetch("10.1109/tgrs.2020.2984458")
        self.assertEqual(r["pub_date"],"2020-12-01")
        self.assertEqual(r["source_publication_date"],"")
        self.assertEqual(r["source_publication_precision"],"month")
        self.assertTrue(r["pub_date_imputed_first_of_month"])
        self.assertIn("published-print",r["pub_date_basis"])
        self.assertEqual(r["crossref_created"]["full_date"],"2020-05-06")
        self.assertEqual(r["checkpoint_schema"],"crossref-publication-v4-print-online-month-first")

    def test_lookup_keeps_online_and_print_alternatives(self):
        doc={"message":{"DOI":"10.1175/JAS-D-17-0385.1","type":"journal-article",
              "created":{"date-parts":[[2018,6,13]]},
              "published-online":{"date-parts":[[2018,8,15]]},
              "published-print":{"date-parts":[[2018,9,1]]}}}
        with patch.object(m,"get",return_value=doc):
            r=m.fetch("10.1175/jas-d-17-0385.1")
        self.assertEqual(r["pub_date"],"2018-09-01")
        self.assertEqual(r["source_publication_date"],"2018-09-01")
        self.assertEqual(r["publication_dates"]["published-online"]["full_date"],"2018-08-15")
        self.assertEqual(r["crossref_created"]["full_date"],"2018-06-13")

    def test_monthly_harvest_preferred_print_first(self):
        date,basis=h.preferred_crossref_pub_date({"type":"journal-article",
           "published-print":{"date-parts":[[2020,12]]},
           "published-online":{"date-parts":[[2020,5,6]]}})
        self.assertEqual(date,"2020-12-01")
        self.assertIn("published_print_month_first",basis)
        self.assertEqual(h.crossref_date({"published-print":{"date-parts":[[2020,12]]}},"2020-12")[1],"published_month_only")

    def test_monthly_harvest_online_when_print_missing(self):
        date,basis=h.preferred_crossref_pub_date({"published-online":{"date-parts":[[2025,3]]}})
        self.assertEqual(date,"2025-03-01")
        self.assertIn("published_online_month_first",basis)

    def test_monthly_gate_preserved_even_if_office_suggested_month_differs(self):
        a={"DOI":"10.9999/example","type":"journal-article",
           "published-online":{"date-parts":[[2020,5,6]]},
           "published-print":{"date-parts":[[2020,12]]},
           "title":["Test"]}
        candidate=h.to_candidate(a,"crossref","NA23OAR4590137","monthly","2020-05")
        self.assertIsNotNone(candidate)
        self.assertEqual(candidate["date"],"2020-12-01")
        self.assertIn("published_print_month_first",candidate["date_basis"])
        self.assertIn("intake_window_basis=",candidate["date_basis"])

    def test_no_date_if_only_year_and_created(self):
        x=m.crossref_date_info({"created":{"date-parts":[[2020,5,6]]},
                               "published-print":{"date-parts":[[2020]]}})
        self.assertEqual(x["pub_date"],"")
        self.assertEqual(x["best_partial_date"],"2020")

    def test_markup_and_doi(self):
        self.assertEqual(m.strip_markup("<jats:p>Thunderstorms &amp; floods</jats:p>"),
                         "Thunderstorms & floods")
        self.assertEqual(m.doi("DOI:10.1175/BAMS-D-23-0036.1"),"10.1175/bams-d-23-0036.1")

if __name__=="__main__":
    unittest.main()
