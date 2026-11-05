"""Fast monthly DOI intake regression checks. No private Hub is contacted."""
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from quick_monthly_intake import AWARD, clean, match_reach, check_funding, detect_version, gather_feed, shared_identity_route

class MonthlyQuickIntakeTests(unittest.TestCase):
    def test_html_title_markup_is_removed_not_invented(self):
        self.assertEqual(clean("The <scp>Wind</scp> &amp; Waves"), "The Wind & Waves")
        self.assertIn("Skynet", clean("We &lt;3 Skynet"))

    def test_doi_secondary_field_and_exact_title_checks(self):
        index=[{"Record ID":"reach-1","Title":"Other article", "Link to Output":"https://example.org/other"}]
        details=[{"Record ID":"reach-1","Title":"Other article",
                  "Publications":"https://doi.org/10.1234/paper.1",
                  "Journal Article Link":""}]
        self.assertEqual(match_reach("10.1234/paper.1", "New article",
                                      "https://doi.org/10.1234/paper.1",index,details)[0]["reach_id"],
                         "reach-1")
        self.assertEqual(match_reach("10.1234/absent","Not here",
                                    "https://doi.org/10.1234/absent",index,details), [])

    def test_shared_identity_gate_accepts_only_unique_doi_or_url_with_matching_title(self):
        base={"source":"REACH","title":"Complete WPO article","match_bases":["exact_doi","normalized_title"]}
        shared={"status":"CONFIRMED_PUBLIC_REACH_IDENTITY","matches":[base]}
        found=[{"reach_id":"reach-1","match_basis":"exact_doi"}]
        self.assertEqual(shared_identity_route(found,shared,"Complete WPO article"),"already_in_reach")
        conflict={"status":"CONFIRMED_PUBLIC_REACH_IDENTITY",
                  "matches":[dict(base,title="Different article")]}
        self.assertEqual(shared_identity_route(found,conflict,"Complete WPO article"),"reach_identity_review")
        duplicates={"status":"CONFIRMED_PUBLIC_REACH_IDENTITY",
                    "matches":[base,dict(base,title="Complete WPO article")]}
        self.assertEqual(shared_identity_route(found,duplicates,"Complete WPO article"),"reach_identity_review")
    def test_title_only_and_scout_queue_matches_are_not_new_proposals(self):
        shared={"status":"POSSIBLE_PUBLIC_REACH_MATCH",
                "matches":[{"source":"REACH","title":"Shared title","match_bases":["normalized_title"]}]}
        self.assertEqual(shared_identity_route([],shared,"Shared title"),"reach_identity_review")
        queued={"status":"IN_PUBLIC_SCOUT_QUEUE",
                "matches":[{"source":"SCOUT_PUBLISHED","title":"Other","match_bases":["exact_doi"]}]}
        self.assertEqual(shared_identity_route([],queued,"A title"),"already_in_scout_or_inbox")
        self.assertEqual(shared_identity_route([],None,"A title"),"no_public_identity_match")

    def test_primary_award_is_needed_and_related_awards_are_ignored(self):
        row={"NOAA Award Number(s)":"NA22OAR4590179"}
        spark=[{"Record ID":"spark-1","Award Number(s)":"NA22OAR4590179",
                "Related Award Number(s)":"NA23OAR4599999"}]
        c,status,issues=check_funding(row,{},spark)
        self.assertEqual(status,"primary_award_matched")
        _,status,_=check_funding({"NOAA Award Number(s)":"NA23OAR4599999"},{},spark)
        self.assertEqual(status,"unmatched_primary_award")

    def test_fy25_oarx_task_award_preserved_and_not_confused_with_siblings(self):
        full = "NA25OARX459C0342-T1-01"
        sibling = "NA25OARX459C0342-T1-02"
        base = "NA25OARX459C0342"
        self.assertEqual(AWARD.findall("Grant no. " + full + "; NA22NWS4320003"),
                         [full, "NA22NWS4320003"])
        spark = [
            {"Record ID": "spark-fy25-a", "Award Number(s)": full},
            {"Record ID": "spark-fy25-b", "Award Number(s)": sibling},
        ]
        candidates, status, _ = check_funding(
            {"NOAA Award Number(s)": full}, {}, spark)
        self.assertEqual(status, "primary_award_matched")
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["Record ID"], "spark-fy25-a")
        # A base FAIN alone cannot uniquely name a WPO task.
        _, status, _ = check_funding(
            {"NOAA Award Number(s)": base}, {}, spark)
        self.assertEqual(status, "unmatched_primary_award")

    def test_explicit_contradiction_is_held_but_missing_grant_proof_is_not(self):
        spark=[{"Record ID":"spark-1","Award Number(s)":"NA22OAR4590179"}]
        row={"NOAA Award Number(s)":"NA22OAR4590179"}
        negative={"substantive_research":{"funding_assessment":{
            "same_project_verified":False,"reason":"Article objectives differ from project"}}}
        _,status,_=check_funding(row,negative,spark)
        self.assertEqual(status,"funding_anomaly")
        uncertain={"substantive_research":{"funding_assessment":{
            "same_project_verified":False,"basis":"Article's grant acknowledgment not yet found"}}}
        _,status,_=check_funding(row,uncertain,spark)
        self.assertEqual(status,"primary_award_matched")

    def test_prior_cross_cohort_version_review_is_preserved(self):
        case={"substantive_research":{"identity_and_related_outputs":{
            "historical_review_unit":"zenodo-mom6","concept_doi":"10.1234/first",
            "version_doi":"10.1234/second"}}}
        self.assertEqual(detect_version(case,"10.1234/second"),
                         "existing_historical_review_family")

    def test_source_sha_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"manifest.json").write_text(json.dumps({
                "batches":[{"path":"batches/test.csv","sha256":"0"*64,"record_count":1}]}))
            p=root/"batches/test.csv"
            p.parent.mkdir()
            p.write_text("DOI,Title\n10.1234/x,Test\n")
            with self.assertRaisesRegex(ValueError, "Source SHA mismatch"):
                gather_feed(root,"","manifest.json",None)

if __name__=="__main__":
    unittest.main()
