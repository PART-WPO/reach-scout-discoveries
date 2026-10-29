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

    def test_historical_38_future_dated_followups_take_priority_over_older_awards(self):
        mm,mc=m(0,0,0)
        hh,hc=h(188,150,38)
        hc["awaiting_research"]=0
        hc["needs_more_research"]=38
        ht={"entries":[
            {"identity":"doi:10.1234/test"+str(i),"status":"needs_more_research",
             "next_research_at":"2026-11-05T00:00:00Z"} for i in range(38)
        ]}
        r=decide(mm,mc,hh,hc,SHA,historical_triage=ht)
        self.assertEqual(r["mode"],"historical_api_triage")
        self.assertEqual(r["phase"],"additional_evidence_research")
        self.assertEqual(r["historical_api"]["unresolved_followups"],38)

    def test_monthly_followups_preempt_historical_further_evidence(self):
        mm,mc=m(12,12,2)
        hh,hc=h(188,150,38)
        mt={"entries":[{"status":"needs_more_research"} for _ in range(10)]}
        r=decide(mm,mc,hh,hc,SHA,monthly_triage=mt)
        self.assertEqual(r["mode"],"monthly_api_triage")
        self.assertEqual(r["phase"],"additional_evidence_research")
        self.assertEqual(r["monthly_api"]["unresolved_followups"],10)

    def test_new_monthly_cases_preempt_old_monthly_followups(self):
        mm,mc=m(12,12,2)
        hh,hc=h(188,150,38)
        mt={"entries":[{"status":"needs_more_research"} for _ in range(7)]
                      +[{"status":"awaiting_research"} for _ in range(3)]}
        r=decide(mm,mc,hh,hc,SHA,monthly_triage=mt)
        self.assertEqual(r["mode"],"monthly_api_triage")
        self.assertEqual(r["phase"],"initial_research")

    def test_linked_historical_metadata_blockers_are_not_cleared(self):
        mm,mc=m(0,0,0)
        hh,hc=h(188,188,0)
        blockers={"entries":[{"cohort":"Historical DataCite API Backfill 2026-10-28 — API-seeded expansion",
                              "status":"blocked","next_retry_at":"2026-11-05T00:00:00Z"}]}
        r=decide(mm,mc,hh,hc,SHA,metadata_blockers=blockers)
        self.assertEqual(r["mode"],"historical_api_triage")
        self.assertEqual(r["phase"],"additional_evidence_research")

    def test_attribution_rechecks_preempt_normal_after_api_resolution(self):
        mm,mc=m(0,0,0)
        hh,hc=h(188,188,0)
        followups={"entries":[{"stage":"closed_no_project_bridge"},
                              {"stage":"queued_targeted_attribution_review"}]}
        r=decide(mm,mc,hh,hc,SHA,attribution_followups=followups)
        self.assertEqual(r["mode"],"historical_api_triage")
        self.assertEqual(r["phase"],"attribution_followups")
        self.assertEqual(r["attribution_followups_pending"],1)

    def test_monthly_blocker_alone_preempts_historical(self):
        mm,mc=m(12,12,12)
        hh,hc=h(188,150,38)
        blockers={"entries":[{"cohort":"Monthly API 2026-10 — API-seeded expansion",
                              "status":"blocked"}]}
        r=decide(mm,mc,hh,hc,SHA,metadata_blockers=blockers)
        self.assertEqual(r["mode"],"monthly_api_triage")
        self.assertEqual(r["phase"],"additional_evidence_research")


    def test_completed_human_handoff_does_not_block_older_award_discovery(self):
        mm,mc=m(0,0,0)
        hh,hc=h(188,188,0)
        ht={"entries":[{"status":"human_metadata_needed","human_handoff_status":"pending_hub_intake"}]}
        blockers={"entries":[{"cohort":"Historical DataCite API Backfill 2026-10-28",
                              "status":"pending_hub_handoff","research_completed":True}]}
        r=decide(mm,mc,hh,hc,SHA,historical_triage=ht,metadata_blockers=blockers)
        self.assertEqual(r["mode"],"normal_historical_discovery")

    def test_unfinished_metadata_research_still_preempts_awards(self):
        mm,mc=m(0,0,0)
        hh,hc=h(188,188,0)
        blockers={"entries":[{"cohort":"Historical DataCite API Backfill 2026-10-28",
                              "status":"blocked","research_completed":False}]}
        r=decide(mm,mc,hh,hc,SHA,metadata_blockers=blockers)
        self.assertEqual(r["mode"],"historical_api_triage")
        self.assertEqual(r["phase"],"additional_evidence_research")

if __name__=="__main__":unittest.main()
