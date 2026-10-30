#!/usr/bin/env python3
"""Network-free regression checks for Crossref publication metadata checkpoint."""
import importlib.util
import unittest
from pathlib import Path
P=Path(__file__).resolve().parents[1]/"tools"/"audit_doi_metadata.py"
spec=importlib.util.spec_from_file_location("doi_checkpoint",P)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class CrossrefMetadataTests(unittest.TestCase):
    def test_full_day(self):
        self.assertEqual(m.crossref_date_parts({"date-parts":[[2024,8,15]]}),
                         {"value":"2024-08-15","precision":"day","full_date":"2024-08-15"})

    def test_no_fabricated_day_for_partial_date(self):
        r=m.crossref_date_parts({"date-parts":[[2024,8]]})
        self.assertEqual(r["value"],"2024-08")
        self.assertEqual(r["precision"],"month")
        self.assertEqual(r["full_date"],"")
        r=m.crossref_date_parts({"date-parts":[[2024]]})
        self.assertEqual(r["value"],"2024")
        self.assertEqual(r["full_date"],"")

    def test_prefer_online_publication_for_journal(self):
        data={"type":"journal-article",
              "published-online":{"date-parts":[[2024,4,10]]},
              "published-print":{"date-parts":[[2024,6,1]]},
              "created":{"date-parts":[[2023,12,12]]}}
        x=m.crossref_date_info(data)
        self.assertEqual(x["pub_date"],"2024-04-10")
        self.assertEqual(x["pub_date_basis"],"published-online")
        self.assertEqual(x["publication_dates"]["published-print"]["full_date"],"2024-06-01")

    def test_posted_date_for_preprint(self):
        x=m.crossref_date_info({"type":"posted-content",
              "posted":{"date-parts":[[2025,2,5]]},
              "published-online":{"date-parts":[[2025,7,15]]}})
        self.assertEqual(x["pub_date"],"2025-02-05")
        self.assertEqual(x["pub_date_basis"],"posted")

    def test_use_exact_print_date_if_online_is_partial(self):
        x=m.crossref_date_info({"type":"journal-article",
             "published-online":{"date-parts":[[2025,3]]},
             "published-print":{"date-parts":[[2025,4,2]]}})
        self.assertEqual(x["pub_date"],"2025-04-02")
        self.assertEqual(x["pub_date_basis"],"published-print")
        self.assertEqual(x["publication_dates"]["published-online"]["value"],"2025-03")

    def test_no_registration_substitution(self):
        x=m.crossref_date_info({"type":"journal-article",
              "created":{"date-parts":[[2025,1,5]]},
              "published-online":{"date-parts":[[2025]]}})
        self.assertEqual(x["pub_date"],"")
        self.assertEqual(x["best_partial_date"],"2025")
        self.assertEqual(x["crossref_created"]["full_date"],"2025-01-05")

    def test_invalid_dates(self):
        self.assertFalse(m.crossref_date_parts({"date-parts":[[2025,2,30]]})["full_date"])
        self.assertFalse(m.crossref_date_parts({"date-parts":[[2025,13,2]]})["full_date"])

    def test_markup_abstract(self):
        self.assertEqual(m.strip_markup("<jats:p>Thunderstorms &amp; floods</jats:p>"),
                         "Thunderstorms & floods")

    def test_doi_identity(self):
        self.assertEqual(m.doi("DOI:10.1175/BAMS-D-23-0036.1"),"10.1175/bams-d-23-0036.1")

if __name__=="__main__":
    unittest.main()
