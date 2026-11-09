"""Existing-note extraction must preserve source scope, attribution, and privacy."""
import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from extract_structured_research_evidence import (
    ROOT, REG, extract, note_scope, verified_note, report
)
from evidence_to_action_pilot import build as build_pilot

class ExtractorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry=json.loads((ROOT / REG).read_text())
        cls.extracted=extract(cls.registry)
        cls.report=build_pilot()

    def test_existing_notes_cover_every_public_registry_identity(self):
        self.assertEqual(len(self.extracted),self.registry["distinct_research_identities"])
        self.assertGreaterEqual(len(self.extracted), 35)
        self.assertEqual(set(self.extracted), set(x["identity"] for x in self.registry["cases"]))
        self.assertEqual(self.report["new_external_research_requests"],0)

    def test_pilot_replaces_only_prior_unstructured_cases(self):
        x=self.report
        self.assertEqual(x["previously_unstructured_identities"],x["evidence_extracted_from_verified_notes"])
        self.assertEqual(x["structured_case_inputs"] + x["previously_unstructured_identities"],
                         x["distinct_cases_evaluated"])
        self.assertEqual(x["unstructured_identity_cases"],0)
        self.assertTrue(all(not c["automatic_hub_write"] and not c["formal_original_closed"] and
                            not c["separate_expansion_closed"] for c in x["cases"]))

    def test_parent_fields_never_inherited_by_child_doi(self):
        parent={"research_subject":{"parent_publication_doi":"10.1234/parent",
                "child_dois":["10.5281/zenodo.1111","10.5281/zenodo.2222"]},
                "primary_spark_award_verified":True,
                "publication_status":"OFFICIAL_JOURNAL_PUBLICATION_VERIFIED",
                "source_evidence":[{"url":"https://zenodo.org/records/1111"}]}
        scoped,_,child=note_scope(parent,{"identity":"doi:10.5281/zenodo.1111"})
        self.assertTrue(child)
        self.assertEqual(scoped,{})
        self.assertNotIn("primary_spark_award_verified", scoped)

    def test_multi_case_scoping_does_not_share_sibling_project_metadata(self):
        note={"cases":[{"doi":"10.1234/A","same_project_wpo_funding":"VERIFIED_SAME_PROJECT"},
                       {"doi":"10.1234/B","same_project_wpo_funding":"NOT_VERIFIED"}],
              "same_project_wpo_funding":"VERIFIED_SAME_PROJECT"}
        scoped,_,child=note_scope(note,{"identity":"doi:10.1234/b"})
        self.assertTrue(child)
        self.assertEqual(scoped["same_project_wpo_funding"],"NOT_VERIFIED")

    def test_award_in_noaa_ir_not_equivalent_to_spark_primary_project(self):
        case=self.extracted["doi:10.1088/2515-7620/aeaad2"]
        self.assertIsNone(case["primary_award_match"])
        self.assertNotEqual(case["project_attribution"],"VERIFIED_SAME_PROJECT")
        self.assertFalse(case["secondary_identity_checked"])

    def test_umbrella_related_dataset_funding_not_inferred(self):
        for doi in ("10.5281/zenodo.4433147","10.5281/zenodo.5057616"):
            case=self.extracted["doi:"+doi]
            self.assertIsNone(case["primary_award_match"])
            self.assertFalse(case["required_metadata_verified"])
            self.assertEqual(case["publication_status"],"NOT_CHECKED")

    def test_existing_non_wpo_contradiction_does_not_stage(self):
        original="doi:10.1175/aies-d-23-0106.1"
        self.assertEqual(self.extracted[original]["project_attribution"],"CONTRADICTED")
        disp={x["identity"]:x["suggested_disposition"] for x in self.report["cases"]}[original]
        self.assertEqual(disp,"CONTRADICTORY_PROJECT_EVIDENCE_HOLD")

    def test_pinned_source_sha_tamper_fails_closed(self):
        with TemporaryDirectory() as td:
            root=Path(td)
            rel="scout-operations/monthly-research/example.json"
            path=root/rel
            path.parent.mkdir(parents=True)
            path.write_text('{"doi":"10.1234/a"}')
            with self.assertRaisesRegex(ValueError,"SHA mismatch"):
                verified_note(root,{"source_path":rel,"source_sha256":"0"*64})
            with self.assertRaisesRegex(ValueError,"Unsafe or missing"):
                verified_note(root,{"source_path":"../other.json","source_sha256":"0"*64})

    def test_latest_verified_note_supersedes_older_reopen_only_directive(self):
        with TemporaryDirectory() as td:
            root=Path(td)
            docs=[
                {"doi":"10.1234/a","decision":"SOFT_DEFER_UNTIL_MATERIAL_WPO_EVIDENCE",
                 "next_action":"Only reopen if new evidence arrives"},
                {"doi":"10.1234/a","publication_status":"OFFICIAL_JOURNAL_PUBLICATION_VERIFIED",
                 "decision":"INVESTIGATE_NEW_PUBLICATION_EVIDENCE",
                 "next_action":"Verify updated identity and primary project scope"},
            ]
            events=[]
            for i,doc in enumerate(docs):
                rel=f"scout-operations/monthly-research/note{i}.json"
                p=root/rel
                p.parent.mkdir(parents=True,exist_ok=True)
                raw=json.dumps(doc).encode()
                p.write_bytes(raw)
                events.append({"event_id":str(i),"identity":"doi:10.1234/a",
                    "source_path":rel,"source_sha256":hashlib.sha256(raw).hexdigest(),
                    "role_in_note":"original"})
            registry={"events":events,
                      "distinct_research_identities":1,
                      "cases":[{"identity":"doi:10.1234/a","event_ids":["0","1"],
                                "latest_event_id":"1",
                                "latest_operational_disposition":"EVIDENCE_RECORDED_CONTINUE_OR_VERIFY"}]}
            value=extract(registry,root)["doi:10.1234/a"]
            self.assertFalse(value["evidence_reopen_only"])
            self.assertEqual(value["publication_status"],"PUBLISHED")

    def test_no_personnel_or_private_reviewer_data_materialized(self):
        import json
        text=json.dumps(report())
        for key in ('"authors":','"pi_name":','"collaborators":',
                    '"reviewer_approved":true','"private_hub_imported":true'):
            self.assertNotIn(key,text)
        self.assertTrue(all(x["private_hub_state"]=="NOT_VERIFIED" for x in self.report["cases"]))

    def test_changed_recommendations_are_not_false_positive_stages(self):
        self.assertEqual(self.report["new_human_review_stages"],0)
        self.assertEqual(self.report["new_public_reach_additions"],0)
        self.assertNotIn("READY_FOR_EXISTING_VALIDATED_DRAFT_PREFLIGHT", [
            x["suggested_disposition"] for x in self.report["cases"]
            if x["evidence_origin"]=="VERIFIED_PUBLIC_NOTES_EXTRACTED"])
        self.assertEqual(self.report["cases_with_changed_recommendation"],
                         sum(x["decision_changed"] for x in self.report["cases"]))

if __name__=="__main__":
    unittest.main()
