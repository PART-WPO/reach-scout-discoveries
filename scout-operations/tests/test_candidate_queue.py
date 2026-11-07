import importlib.util, unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location("candidate_queue",Path(__file__).resolve().parents[1]/"tools/build_candidate_queue.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class QueueTests(unittest.TestCase):
 def test_award_format(self):
  self.assertEqual(m.funding_signal(["NA26OARX459C0001"]),"POSSIBLE_WPO_459")
  self.assertEqual(m.funding_signal(["NA22OAR4590527"]),"POSSIBLE_WPO_459")
  self.assertEqual(m.funding_signal(["NA20OAR4320278"]),"CI_432_NEEDS_PROJECT_PROOF")
  self.assertEqual(m.funding_signal(["NA26OARX459C0001","NA20OAR4320278"]),"MIXED_432_459")
  self.assertEqual(m.funding_signal(["NA26OARX459C0001-not-a-match"]),"INCONCLUSIVE")
 def test_fast_exit_and_ambiguous(self):
  def entry(d,status,uid=None):
   return {"doi":d,"title":"test","bulk_identity_gate":{"status":status,"verified_reach_uid":uid}}
  r={"total":3,"bulk_identity_screening":{"source_dois":3},"entries":[entry("10.1/a","VERIFIED_EXISTING_REACH","reach-1"),entry("10.1/b","NEEDS_IDENTITY_REVIEW"),entry("10.1/c","NO_PUBLIC_REACH_MATCH")]}
  q=m.build(r,{"cases":[]})
  self.assertEqual(q["lane_counts"],{"BOUNDED_IDENTITY_REVIEW":1,"EXISTING_REACH_FAST_EXIT":1,"NOVEL_IDENTITY_RESEARCH":1})
  self.assertEqual(q["original_dispositions_changed"],0)
  self.assertEqual(q["new_review_proposals"],0)
 def test_structured_awards_affect_priority(self):
  r={"total":2,"bulk_identity_screening":{"source_dois":2},"entries":[{"doi":"10.1/a","bulk_identity_gate":{"status":"NO_PUBLIC_REACH_MATCH"}},{"doi":"10.1/b","bulk_identity_gate":{"status":"NO_PUBLIC_REACH_MATCH"}}]}
  awards={"10.1/a":{"awards":{"NA26OARX459C0001"},"source_batches":{"batch1.csv"}},"10.1/b":{"awards":{"NA20OAR4320278"},"source_batches":{"batch2.csv"}}}
  q=m.build(r,{"cases":[]},awards)
  self.assertEqual(q["items"][0]["funding_signal"],"POSSIBLE_WPO_459")
  self.assertEqual(q["items"][0]["priority"],80)
  self.assertEqual(q["items"][1]["funding_signal"],"CI_432_NEEDS_PROJECT_PROOF")
  self.assertEqual(q["items"][1]["priority"],25)
 def test_hold_does_not_research_again(self):
  r={"total":1,"bulk_identity_screening":{"source_dois":1},"entries":[{"doi":"10.1/c","bulk_identity_gate":{"status":"NO_PUBLIC_REACH_MATCH"}}]}
  q=m.build(r,{"cases":[{"identity":"doi:10.1/c","latest_operational_disposition":"PROJECT_EVIDENCE_HOLD"}]})
  self.assertEqual(q["items"][0]["lane"],"WAIT_FOR_NEW_EVIDENCE")
if __name__=="__main__":unittest.main()
