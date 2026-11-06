import sys
import unittest
import tempfile
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from build_human_project_referrals import (
    build,referral_state,publication_meta_valid,proposal,main
)

class HumanProjectReferrals(unittest.TestCase):
    def published(self):
        return {"status":"ok","provider":"crossref",
                "resource_type":"proceedings-article",
                "publication_status":"other_or_unverified",
                "pub_date":"2022-03-21",
                "title":"Airborne Phased Array Radar (APAR) Program Status & Critical Requirements Analyses",
                "creators":["Mark Yaklich","Mark Leifer"],
                "evidence":"https://api.crossref.org/works/10.1109/radarconf2248738.2022.9764246"}
    def identity(self,doi,title):
        return {"status":"NO_PUBLIC_IDENTITY_MATCH",
                "matches":[],
                "noaa_ir_reach_check":{"status":"DOI_NOT_IN_VERIFIED_IR_INDEX_UNKNOWN"}}
    def test_no_direct_new_output_approval_from_bounded_project_question(self):
        data=build(metadata=lambda d:self.published(),public_identity=self.identity,
                   stage=False)
        cases={x["doi"]:x for x in data["referrals"]}
        self.assertIn("10.1109/radarconf2248738.2022.9764246",cases)
        self.assertEqual(cases["10.1109/radarconf2248738.2022.9764246"]["disposition"],
                         "READY_FOR_VALIDATED_HUMAN_PROJECT_REFERRAL")
        self.assertTrue(cases["10.1109/radarconf2248738.2022.9764246"]["review_question"].startswith("Reviewer question:"))
        self.assertFalse(cases["10.1109/radarconf2248738.2022.9764246"]["eligible_for_new_reach_addition"] is True)
        self.assertEqual(data["human_referral_drafts_prevalidated"],0)
        self.assertEqual(data["private_hub_imports"],"NOT_VERIFIED")
        self.assertEqual(data["new_approved_reach_outputs"],0)
        # General umbrella award without independently matched project must
        # not be sent to the reviewer merely for appearing in public research.
        self.assertEqual(cases["10.1007/s00382-022-06655-w"]["disposition"],
                         "HOLD_UNVERIFIED_PROJECT_CONTEXT")
    def test_command_line_main_writes_valid_referral_report_without_name_error(self):
        report={"unique_bounded_project_questions":0,
                "human_referral_drafts_prevalidated":0,"referrals":[]}
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/"referrals.json"
            with patch("build_human_project_referrals.build",return_value=report), \
                 patch("build_human_project_referrals.OUTPUT",target), \
                 patch("sys.argv",["build_human_project_referrals.py"]):
                main()
            self.assertEqual(__import__("json").loads(target.read_text()),report)

    def test_exact_official_publication_date_and_newness_required(self):
        meta=self.published()
        self.assertTrue(publication_meta_valid(meta))
        for typ in ("posted-content","preprint"):
            self.assertFalse(publication_meta_valid({**meta,"resource_type":typ}))
        event={"bounded_human_question_to_verify":True}
        project={"award_context_only":"NA18OAR4590431"}
        self.assertEqual(referral_state(event,meta,self.identity("",""),project=project),
                         "READY_FOR_VALIDATED_HUMAN_PROJECT_REFERRAL")
        self.assertEqual(referral_state(event,meta,{"status":"CONFIRMED_PUBLIC_REACH_IDENTITY"},
                            project=project),"HOLD_ALREADY_IN_PUBLIC_REACH_OR_SCOUT")
        self.assertEqual(referral_state(event,meta,{"status":"NO_PUBLIC_IDENTITY_MATCH"},
                            project=project,watched=True),"HOLD_PREPRINT_MONTHLY_WATCH")
        self.assertEqual(referral_state(event,meta,{"status":"NO_PUBLIC_IDENTITY_MATCH"},
                            prior={"status":"approved"},project=project),"HOLD_EXISTING_HUMAN_DECISION")
    def test_referral_draft_does_not_claim_an_unverified_primary_award(self):
        event={"event_id":"e"*24,"checked_evidence_urls":[
            "https://ieeexplore.ieee.org/document/9764246/",
            "https://conference.example.org/program"]}
        project={"award_context_only":"NA18OAR4590431"}
        row=proposal("10.1109/radarconf2248738.2022.9764246",self.published(),event,project)
        self.assertEqual(row["provenance"]["classification"],"NEEDS INVESTIGATION")
        self.assertEqual(row["fields"]["NOAA Award Number(s)"],"")
        self.assertEqual(row["fields"]["Funding Evidence URL"],"")
        self.assertIn("NOT an eligible new REACH output", " ".join(row["provenance"]["notes"]))
        self.assertIn("NA18OAR4590431"," ".join(row["provenance"]["notes"]))

if __name__=="__main__":unittest.main()
