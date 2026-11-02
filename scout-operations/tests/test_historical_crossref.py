"""Regression tests for historical Crossref as a non-duplicating seed cohort."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from reconcile_historical_crossref import canonical, verified_seed
from select_workstream import decide

SHA="e"*64
def datacite_done():
    m={"candidate_rows":188}
    c={"total_distinct_dois":188,"fully_investigated":188,"remaining":0,
       "research_complete":True,"source_manifest_sha256":SHA}
    return m,c
def crossref_open(doi="10.1234/existing"):
    manifest={"candidate_rows":1}
    coverage={"total_distinct_dois":1,"fully_investigated":0,"remaining":1,
              "awaiting_research":1,"research_complete":False,
              "source_manifest_sha256":SHA}
    triage={"entries":[{"identity":"doi:"+doi,"status":"awaiting_research",
             "seed_expansion_status":"awaiting_exploration",
             "present_in_published_scout_feed_at_intake":True}]}
    return manifest,coverage,triage

class HistoricalCrossrefTests(unittest.TestCase):
    def test_doi_canonicalization(self):
        self.assertEqual(canonical("https://doi.org/10.1234/ABC"),"doi:10.1234/abc")
        self.assertEqual(canonical("10.1234/ABC"),"doi:10.1234/abc")
        self.assertFalse(canonical("not a doi"))

    def test_api_hit_is_not_seed_research_completion(self):
        self.assertFalse(verified_seed({"seed_expansion_status":"awaiting_exploration"}))
        self.assertFalse(verified_seed({"seed_expansion_status":"complete"}))
        self.assertTrue(verified_seed({"seed_expansion_status":"complete",
             "seed_checked_sources":["https://api.crossref.org/works/10.1234/test"],
             "seed_research_notes":"References, availability and code outputs checked."}))

    def test_crossref_preempts_completed_datacite(self):
        hm,hc=datacite_done()
        cm,cc,ct=crossref_open()
        result=decide({},{"checked":0},hm,hc,SHA,
          crossref_manifest=cm,crossref_coverage=cc,crossref_triage=ct,
          crossref_manifest_sha=SHA)
        self.assertEqual(result["mode"],"historical_crossref_triage")
        self.assertEqual(result["phase"],"initial_research")

    def test_already_in_reach_does_not_suppress_expansion_seed(self):
        hm,hc=datacite_done()
        cm,cc,ct=crossref_open()
        cc.update({"awaiting_research":0})
        ct["entries"][0]["status"]="already_in_reach"
        result=decide({},{"checked":0},hm,hc,SHA,
           crossref_manifest=cm,crossref_coverage=cc,crossref_triage=ct,
           crossref_manifest_sha=SHA)
        self.assertEqual(result["mode"],"historical_crossref_triage")
        self.assertEqual(result["phase"],"seed_expansion_research")
        self.assertEqual(result["historical_crossref_api"]["seed_expansions_pending"],1)

    def test_monthly_preempts_crossref(self):
        hm,hc=datacite_done()
        cm,cc,ct=crossref_open()
        result=decide({"candidate_rows":1},
          {"received":1,"checked":0,"missing_from_ledger":0},hm,hc,SHA,
          crossref_manifest=cm,crossref_coverage=cc,crossref_triage=ct,
          crossref_manifest_sha=SHA)
        self.assertEqual(result["mode"],"monthly_api_triage")

if __name__=="__main__":unittest.main()
