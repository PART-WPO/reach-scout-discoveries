"""Regression tests for independent DOI and historical NOAA IR→REACH duplicate gate."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from ir_reach_identity import identity_check,research_route

class IRReachIdentityTests(unittest.TestCase):
    def setUp(self):
        self.url="https://repository.library.noaa.gov/view/noaa/9001"
        self.public={"records":[{"source":"REACH","identity":"reach-test-uid",
                       "title":"Different punctuation","dois":[],"urls":[self.url],
                       "location":"agent-data/details/part-001.csv"}],
                     "keys":{"doi":{},"title":{},"url":{self.url:[0]}}}
        self.doi="10.1234/independent-item"
        self.ir={"dois":{self.doi:[self.url]}}

    def test_independent_doi_joins_verified_ir_url(self):
        result=identity_check(self.public,self.ir,self.doi,"Different title")
        self.assertEqual(result["status"],"CONFIRMED_PUBLIC_REACH_IDENTITY")
        self.assertEqual(result["noaa_ir_reach_check"]["match_uid"],"reach-test-uid")
        self.assertEqual(result["noaa_ir_reach_check"]["match_detail_shard"],
                         "agent-data/details/part-001.csv")
        self.assertEqual(research_route(result),"existing_reach_original_preserve_doi_seed_expansion")

    def test_missing_index_holds(self):
        result=identity_check(self.public,None,self.doi)
        self.assertEqual(result["noaa_ir_reach_check"]["status"],"IR_INDEX_UNAVAILABLE_HOLD")
        self.assertEqual(research_route(result),"bounded_identity_or_version_review_no_staging")

    def test_ambiguous_ir_identity_holds(self):
        ir={"dois":{self.doi:[self.url,"https://repository.library.noaa.gov/view/noaa/9002"]}}
        result=identity_check(self.public,ir,self.doi)
        self.assertNotEqual(result["status"],"CONFIRMED_PUBLIC_REACH_IDENTITY")
        self.assertEqual(result["noaa_ir_reach_check"]["status"],"AMBIGUOUS_IR_DOI_HOLD")

    def test_different_reach_doi_requires_version_review(self):
        self.public["records"][0]["dois"]=["10.1234/other-version"]
        result=identity_check(self.public,self.ir,self.doi)
        self.assertEqual(result["status"],"POSSIBLE_PUBLIC_REACH_MATCH")
        self.assertEqual(result["noaa_ir_reach_check"]["status"],"REACH_DOI_CONFLICT_VERSION_REVIEW")

    def test_verified_ir_url_absent_from_reach_is_not_global_newness(self):
        self.public["keys"]["url"]={}
        result=identity_check(self.public,self.ir,self.doi)
        self.assertEqual(result["status"],"NO_PUBLIC_IDENTITY_MATCH")
        self.assertEqual(result["noaa_ir_reach_check"]["status"],"VERIFIED_IR_URL_NOT_IN_PUBLIC_REACH")
        self.assertEqual(research_route(result),"advance_to_funding_metadata_and_private_decision_checks")

if __name__=="__main__":
    unittest.main()
