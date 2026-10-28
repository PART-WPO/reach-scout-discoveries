import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from select_workstream import decide

SHA="c"*64
def m(rows,received,checked,missing=0):
    return ({"candidate_rows":rows},{"received":received,"checked":checked,"missing_from_ledger":missing})
def h(rows,completed,remaining,matched=True):
    return ({"candidate_rows":rows},{"total_distinct_dois":rows,"fully_investigated":completed,
        "remaining":remaining,"research_complete":remaining==0,
        "source_manifest_sha256":SHA if matched else "a"*64})
class RouterTests(unittest.TestCase):
    def test_historical_api_test_preempts_open_ended_historical(self):
        mm,mc=m(0,0,0)
        hh,hc=h(188,0,188)
        r=decide(mm,mc,hh,hc,SHA)
        self.assertEqual(r["mode"],"historical_api_triage")
        self.assertEqual(r["historical_api"]["remaining_or_untracked"],188)

    def test_monthly_arrival_preempts_unfinished_historical_api(self):
        mm,mc=m(12,12,0)
        hh,hc=h(188,10,178)
        self.assertEqual(decide(mm,mc,hh,hc,SHA)["mode"],"monthly_api_triage")

    def test_return_to_historical_api_after_monthly_done(self):
        mm,mc=m(12,12,12)
        hh,hc=h(188,10,178)
        self.assertEqual(decide(mm,mc,hh,hc,SHA)["mode"],"historical_api_triage")

    def test_return_to_original_discovery_when_both_cleared(self):
        mm,mc=m(12,12,12)
        hh,hc=h(188,188,0)
        self.assertEqual(decide(mm,mc,hh,hc,SHA)["mode"],"normal_historical_discovery")

    def test_new_monthly_after_historical_done_retriggers(self):
        mm,mc=m(13,12,12)
        hh,hc=h(188,188,0)
        self.assertEqual(decide(mm,mc,hh,hc,SHA)["mode"],"monthly_api_triage")

    def test_stale_historical_coverage_not_equivalent_to_done(self):
        mm,mc=m(0,0,0)
        hh,hc=h(188,188,0,matched=False)
        self.assertEqual(decide(mm,mc,hh,hc,SHA)["mode"],"historical_api_triage")

    def test_monthly_missing_coverage_not_equivalent_to_done(self):
        mm,mc=m(1,0,0,1)
        hh,hc=h(188,188,0)
        self.assertEqual(decide(mm,mc,hh,hc,SHA)["mode"],"monthly_api_triage")
if __name__=="__main__":unittest.main()
