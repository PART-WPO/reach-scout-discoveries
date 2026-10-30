#!/usr/bin/env python3
"""Local, network-free tests for DataCite date evidence classification."""
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/"api-discoveries/tools/reconcile_datacite_dates.py"
spec=importlib.util.spec_from_file_location("dates",SRC)
dates=importlib.util.module_from_spec(spec)
spec.loader.exec_module(dates)

class DatesTests(unittest.TestCase):
    def test_historical_manifest_rows_are_checksum_verified(self):
        src,sha=dates.checked_source("historical","")
        self.assertEqual(len(src),188)
        self.assertEqual(len(sha),64)
        self.assertEqual(src["10.17603/ds2-58ft-kp27"]["Title"],
                         "HTI Interview Protocol with Professional Users")

    def test_monthly_empty_baseline_not_fabricated(self):
        src,sha=dates.checked_source("monthly","2026-10")
        self.assertIsInstance(src,dict)
        self.assertTrue(all(v.get("DOI") for v in src.values()))
        self.assertEqual(len(sha),64)

    def test_precision_is_not_invented(self):
        self.assertEqual(dates.iso_date("2025"),"")
        self.assertEqual(dates.iso_date("2025-04"),"")
        self.assertEqual(dates.iso_date("2025-04-10T21:52:56.000Z"),"2025-04-10")
        self.assertEqual(dates.iso_date("2025-02-30"),"")

    def test_created_and_registered_do_not_become_reach_pub_date(self):
        a={"created":"2025-04-10T21:52:56.000Z",
           "registered":"2025-04-11T10:00:00.000Z",
           "updated":"2025-06-02T16:03:08.000Z","published":"2025",
           "publicationYear":2025,"dates":[],"url":""}
        r=dates.date_recommendation(a,"10.17603/ds2-58ft-kp27",try_native=False)
        self.assertEqual(r["status"],"doi_record_timestamp_only")
        self.assertEqual(r["verified_date"],"")
        self.assertEqual(r["provisional_date"],"2025-04-11")
        self.assertEqual(r["publication_year"],"2025")

    def test_issued_exact_requires_repository_check(self):
        a={"dates":[{"date":"2025-04-10","dateType":"Issued"}],
           "published":"2025-04-10","created":"2025-01-01","url":""}
        r=dates.date_recommendation(a,"10.17603/example",try_native=False)
        self.assertEqual(r["status"],"structured_date_needs_native")
        self.assertEqual(r["verified_date"],"")
        self.assertEqual(r["provisional_date"],"2025-04-10")

    def test_conflicting_issued_available_requires_human(self):
        a={"dates":[{"date":"2025-02-02","dateType":"Issued"},
                    {"date":"2025-04-03","dateType":"Available"}],
           "published":"2025-02-02"}
        r=dates.date_recommendation(a,"10.17603/example",try_native=False)
        self.assertEqual(r["status"],"conflicting_typed_dates")
        self.assertEqual(r["verified_date"],"")

    def test_native_exact_doi_publication_metadata(self):
        html='''<html><head><meta name="citation_doi" content="10.17603/ds2-58ft-kp27">
        <meta name="citation_publication_date" content="2025-04-10"></head></html>'''
        match,found=dates.native_date(html,"10.17603/ds2-58ft-kp27")
        self.assertTrue(match)
        self.assertEqual(found,["2025-04-10"])

    def test_native_wrong_doi_not_confident(self):
        html='''<meta name="citation_doi" content="10.17603/some-other-work">
        <meta name="citation_publication_date" content="2025-04-10">'''
        match,found=dates.native_date(html,"10.17603/ds2-58ft-kp27")
        self.assertFalse(match)
        self.assertEqual(found,[])

    def test_native_jsonld_creation_is_not_publication(self):
        html='''<script type="application/ld+json">{
           "@type":"Dataset","identifier":"https://doi.org/10.17603/example",
           "dateCreated":"2025-04-10"
           }</script>'''
        match,found=dates.native_date(html,"10.17603/example")
        self.assertFalse(match)
        self.assertEqual(found,[])

    def test_native_jsonld_publication_can_count(self):
        html='''<script type="application/ld+json">{
           "@type":"Dataset","identifier":"https://doi.org/10.17603/example",
           "datePublished":"2025-04-10"
           }</script>'''
        match,found=dates.native_date(html,"10.17603/example")
        self.assertTrue(match)
        self.assertEqual(found,["2025-04-10"])

    def test_year_only_is_not_exact(self):
        a={"published":"2025","publicationYear":"2025","dates":[]}
        r=dates.date_recommendation(a,"10.17603/example",try_native=False)
        self.assertEqual(r["status"],"year_only_or_unknown")
        self.assertFalse(r["verified_date"])
        self.assertEqual(r["publication_year"],"2025")

if __name__=="__main__":
    unittest.main()
