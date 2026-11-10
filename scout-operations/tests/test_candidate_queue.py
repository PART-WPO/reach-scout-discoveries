import importlib.util, unittest, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
spec=importlib.util.spec_from_file_location("candidate_queue",Path(__file__).resolve().parents[1]/"tools/build_candidate_queue.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class QueueTests(unittest.TestCase):
 def test_award_format(self):
  self.assertEqual(m.funding_signal(["NA26OARX459C0001"]),"CONFIRMED_WPO_459")
  self.assertEqual(m.funding_signal(["NA22OAR4590527"]),"CONFIRMED_WPO_459")
  self.assertEqual(m.funding_signal(["NA20OAR4320278"]),"CI_432_NEEDS_PROJECT_PROOF")
  self.assertEqual(m.funding_signal(["NA26OARX459C0001","NA20OAR4320278"]),"CONFIRMED_WPO_459")
  self.assertEqual(m.funding_signal(["NA26OARX459C0001-not-a-match"]),"INCONCLUSIVE")
  self.assertEqual(m.funding_signal(["NA22OAR0110123"]),"NON_WPO_OAR_AWARD")
  self.assertEqual(m.funding_signal(["NA22OAR4690123"]),"NON_WPO_OAR_AWARD")
  self.assertEqual(m.funding_signal(["NA22OAR0110123","NA21OAR4590367"]),"CONFIRMED_WPO_459")
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
  self.assertEqual(q["items"][0]["funding_signal"],"CONFIRMED_WPO_459")
  self.assertEqual(q["items"][0]["priority"],90)
  self.assertEqual(q["items"][1]["funding_signal"],"CI_432_NEEDS_PROJECT_PROOF")
  self.assertEqual(q["items"][1]["priority"],25)
 def test_preprint_overrides_wpo_award_and_published_version_is_separate(self):
  r={"total":2,"bulk_identity_screening":{"source_dois":2},"entries":[{"doi":"10.1/a","bulk_identity_gate":{"status":"NO_PUBLIC_REACH_MATCH"}},{"doi":"10.1/b","bulk_identity_gate":{"status":"NEEDS_IDENTITY_REVIEW"}}]}
  awards={"10.1/a":{"awards":{"NA26OARX459C0001"}}}
  watch={"10.1/a":{"status":"tracking_preprint","verified_published_dois":[]},"10.1/b":{"status":"published_version_found","verified_published_dois":["10.2/official"]}}
  q=m.build(r,{"cases":[]},awards,watch)
  lanes={x["doi"]:x for x in q["items"]}
  self.assertEqual(lanes["10.1/a"]["lane"],"PREPRINT_WATCHLIST_HOLD")
  self.assertEqual(lanes["10.1/a"]["priority"],5)
  self.assertEqual(lanes["10.1/b"]["lane"],"PREPRINT_PUBLISHED_VERSION_LEAD")
  self.assertEqual(lanes["10.1/b"]["verified_published_dois"],["10.2/official"])
 def test_hail_case_already_in_public_scout_exits_even_with_previous_hold(self):
  doi="10.1175/aies-d-26-0004.1"
  entry={"doi":doi,"title":"the impact of target dataset choice on machine learning prediction of severe hail wind and tornadoes",
         "bulk_identity_gate":{"status":"NO_PUBLIC_REACH_MATCH"},
         "scout_overlap":True,
         "scout_public_queue_matches":[
            {"source":"SCOUT_PUBLISHED","location":"scout-discoveries/batches/monthly.csv:4",
             "basis":["exact_doi","normalized_title"]},
            {"source":"SCOUT_INBOX","location":"scout-discoveries/inbox/reviewer.csv:2",
             "basis":["exact_doi","normalized_title"]}]}
  route={"total":1,"bulk_identity_screening":{"source_dois":1},"entries":[entry]}
  registry={"cases":[{"identity":"doi:"+doi,"latest_operational_disposition":"PROJECT_EVIDENCE_HOLD"}]}
  awards={doi:{"awards":{"NA22OAR4590530"}}}
  item=m.build(route,registry,awards)["items"][0]
  self.assertEqual(item["lane"],"ALREADY_IN_SCOUT_REVIEW_FAST_EXIT")
  self.assertEqual(item["priority"],0)
  self.assertTrue(item["already_in_public_scout_queue"])
  self.assertEqual(len(item["matched_public_review_locations"]),2)
  self.assertFalse(item["one_mission_disposition_required"])
  self.assertIn("keep independent expansion",item["next_action"])

 def test_scout_overlap_hint_alone_never_counts_as_duplicate(self):
  route={"total":1,"bulk_identity_screening":{"source_dois":1},
   "entries":[{"doi":"10.1234/new","scout_overlap":True,
      "scout_public_queue_matches":[{"source":"SCOUT_INBOX",
       "location":"scout-discoveries/inbox/ambiguous.csv:2","basis":["normalized_title"]}],
      "bulk_identity_gate":{"status":"NO_PUBLIC_REACH_MATCH"}}]}
  item=m.build(route,{"cases":[]},{"10.1234/new":{"awards":{"NA26OARX459C0001"}}})["items"][0]
  self.assertEqual(item["lane"],"NOVEL_IDENTITY_RESEARCH")
  self.assertEqual(item["priority"],90)
  self.assertTrue(item["one_mission_disposition_required"])
  self.assertFalse(item["already_in_public_scout_queue"])
  self.assertIn("New Candidate",item["next_action"])

 def test_project_hold_for_459_is_human_handoff_due_not_research_loop(self):
  r={"total":1,"bulk_identity_screening":{"source_dois":1},
    "entries":[{"doi":"10.1234/another","bulk_identity_gate":{"status":"NO_PUBLIC_REACH_MATCH"}}]}
  prior={"cases":[{"identity":"doi:10.1234/another","latest_operational_disposition":"PROJECT_EVIDENCE_HOLD"}]}
  item=m.build(r,prior,{"10.1234/another":{"awards":{"NA22OAR4590530"}}})["items"][0]
  self.assertEqual(item["lane"],"HUMAN_REVIEW_FAST_SCREEN_DUE")
  self.assertTrue(item["one_mission_disposition_required"])

 def test_432_or_other_awards_require_more_specific_scrutiny(self):
  r={"total":2,"bulk_identity_screening":{"source_dois":2},
     "entries":[{"doi":"10.1234/ci","bulk_identity_gate":{"status":"NO_PUBLIC_REACH_MATCH"}},
                {"doi":"10.1234/other","bulk_identity_gate":{"status":"NO_PUBLIC_REACH_MATCH"}}]}
  q=m.build(r,{"cases":[]},{"10.1234/ci":{"awards":{"NA22OAR4320515"}},
                            "10.1234/other":{"awards":{"NA22OAR4190100"}}})
  got={x["doi"]:x for x in q["items"]}
  self.assertEqual(got["10.1234/ci"]["funding_signal"],"CI_432_NEEDS_PROJECT_PROOF")
  self.assertEqual(got["10.1234/ci"]["priority"],25)
  self.assertEqual(got["10.1234/other"]["funding_signal"],"NON_WPO_OAR_AWARD")
  self.assertNotIn("Strong WPO",got["10.1234/other"]["next_action"])

 def test_mission_preview_only_includes_cases_requiring_a_real_decision(self):
  r={"total":2,"bulk_identity_screening":{"source_dois":2},
     "entries":[{"doi":"10.1234/existing","bulk_identity_gate":{"status":"NO_PUBLIC_REACH_MATCH"},
                 "scout_public_queue_matches":[{"source":"SCOUT_PUBLISHED","basis":["exact_doi","normalized_title"],
                 "location":"scout-discoveries/batches/a.csv:2"}]},
                {"doi":"10.1234/new","bulk_identity_gate":{"status":"NO_PUBLIC_REACH_MATCH"}}]}
  q=m.build(r,{"cases":[]},{"10.1234/new":{"awards":{"NA22OAR4590530"}}})
  self.assertEqual(q["one_mission_actionable_original_count"],1)
  self.assertEqual(len(q["next_one_mission_original_preview"]),1)
  self.assertEqual(q["next_one_mission_original_preview"][0]["doi"],"10.1234/new")
  self.assertEqual(q["items"][-1]["lane"],"ALREADY_IN_SCOUT_REVIEW_FAST_EXIT")

 def test_special_editorial_notices_route_to_low_priority_human_check(self):
  notices=[
   ("10.1234/corr","Corrigendum", "CORRIGENDUM"),
   ("10.1234/erratum","Erratum: Original paper", "ERRATUM"),
   ("10.1234/correction","Publisher Correction: Original paper","CORRECTION_NOTICE"),
   ("10.1234/retract","Retraction of: Original paper","RETRACTION"),
   ("10.1234/concern","Expression of Concern: Original paper","EXPRESSION_OF_CONCERN"),
  ]
  normal=[
   ("10.1234/bias","Bias correction for improved weather forecasts"),
   ("10.1234/data","Correction of radar bias in a novel forecast system"),
   ("10.1234/original","Physical modeling of severe storms")
  ]
  all_entries=[{"doi":doi,"title":title,
                "bulk_identity_gate":{"status":"NO_PUBLIC_REACH_MATCH"}}
               for doi,title,*_ in notices+normal]
  r={"total":len(all_entries),
     "bulk_identity_screening":{"source_dois":len(all_entries)},
     "entries":all_entries}
  grants={x["doi"]:{"awards":{"NA24OARX459C0001"}} for x in all_entries}
  q=m.build(r,{"cases":[]},grants)
  by={x["doi"]:x for x in q["items"]}
  self.assertEqual(q["special_publication_type_review_count"],len(notices))
  self.assertEqual(len(q["special_publication_review_preview"]),len(notices))
  self.assertEqual(q["one_mission_actionable_original_count"],len(normal))
  for doi,title,kind in notices:
   self.assertEqual(by[doi]["lane"],"SPECIAL_PUBLICATION_TYPE_REVIEW")
   self.assertEqual(by[doi]["priority"],12)
   self.assertEqual(by[doi]["special_publication_type"],kind)
   self.assertFalse(by[doi]["one_mission_disposition_required"])
   self.assertNotIn(doi,[x["doi"] for x in q["next_one_mission_original_preview"]])
  for doi,title in normal:
   self.assertEqual(by[doi]["lane"],"NOVEL_IDENTITY_RESEARCH")
   self.assertEqual(by[doi]["priority"],90)
   self.assertIsNone(by[doi]["special_publication_type"])

 def test_special_notice_does_not_override_existing_reach_scout_or_preprint(self):
  entries=[
   {"doi":"10.1234/old","title":"Corrigendum",
    "bulk_identity_gate":{"status":"VERIFIED_EXISTING_REACH","verified_reach_uid":"reach-old"}},
   {"doi":"10.1234/scout","title":"Corrigendum",
    "bulk_identity_gate":{"status":"NO_PUBLIC_REACH_MATCH"},
    "scout_public_queue_matches":[{"source":"SCOUT_PUBLISHED",
       "location":"scout-discoveries/batches/old.csv:2",
       "basis":["exact_doi","normalized_title"]}]},
   {"doi":"10.1234/preprint","title":"Erratum",
    "bulk_identity_gate":{"status":"NO_PUBLIC_REACH_MATCH"}}]
  r={"total":3,"bulk_identity_screening":{"source_dois":3},"entries":entries}
  grants={x["doi"]:{"awards":{"NA24OARX459C0001"}} for x in entries}
  pre={"10.1234/preprint":{"status":"tracking_preprint"}}
  q=m.build(r,{"cases":[]},grants,pre)
  by={x["doi"]:x["lane"] for x in q["items"]}
  self.assertEqual(by["10.1234/old"],"EXISTING_REACH_FAST_EXIT")
  self.assertEqual(by["10.1234/scout"],"ALREADY_IN_SCOUT_REVIEW_FAST_EXIT")
  self.assertEqual(by["10.1234/preprint"],"PREPRINT_WATCHLIST_HOLD")
  self.assertEqual(q["special_publication_type_review_count"],0)

 def test_hold_does_not_research_again(self):
  r={"total":1,"bulk_identity_screening":{"source_dois":1},"entries":[{"doi":"10.1/c","bulk_identity_gate":{"status":"NO_PUBLIC_REACH_MATCH"}}]}
  q=m.build(r,{"cases":[{"identity":"doi:10.1/c","latest_operational_disposition":"PROJECT_EVIDENCE_HOLD"}]})
  self.assertEqual(q["items"][0]["lane"],"WAIT_FOR_NEW_EVIDENCE")
if __name__=="__main__":unittest.main()
