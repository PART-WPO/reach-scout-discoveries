"""Every source-backed research note gets a nonterminal operational disposition."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from build_research_outcome_registry import (
    build,stable_decision,HUMAN,PREPRINT,HOLD,ACCESS,OTHER
)

class OutcomeRegistryTests(unittest.TestCase):
    def test_live_monthly_and_historical_research_files_are_reconciled(self):
        r=build()
        self.assertGreaterEqual(r["evidence_files_scanned"],26)
        self.assertGreaterEqual(r["distinct_research_identities"],7)
        self.assertEqual(r["research_note_events"],len(r["events"]))
        self.assertEqual(r["distinct_research_identities"],len(r["cases"]))
        self.assertEqual(sum(r["operational_disposition_counts"].values()),len(r["events"]))
        self.assertTrue(all(not e["formal_original_closed"] and
            not e["separate_expansion_closed"] and not e["new_public_proposal"]
            for e in r["events"]))
        self.assertEqual(r["original_status_changes"],0)
        self.assertEqual(r["expansion_status_changes"],0)
        self.assertEqual(r["private_hub_imports"],"NOT_VERIFIED")
        monthly=[x for x in r["events"] if x["source_path"].startswith("scout-operations/monthly-research/")]
        self.assertGreaterEqual(len(monthly),4)
        self.assertTrue(any(e["identity"]=="doi:10.1002/qj.70325" for e in monthly))
        self.assertTrue(any(e["identity"]=="doi:10.1175/aies-d-23-0106.1" for e in r["events"]))
        self.assertTrue(any(e["identity"].startswith("url:https://github.com/") for e in r["events"]))
    def test_supported_bounded_human_decision_requires_evidence_and_does_not_stage(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            a=root/"scout-operations/historical-crossref-phase2"
            b=root/"scout-operations/monthly-research"
            a.mkdir(parents=True);b.mkdir(parents=True)
            (a/"2026-11-05-1000ET-approval.json").write_text(json.dumps({
              "cases":[{"doi":"10.1000/valid","decision":"BOUNDED_RESEARCH_COMPLETE_NEEDS_HUMAN_PROJECT_ASSESSMENT",
                  "next_action":"Ask reviewer whether source publication is the funded project deliverable",
                  "sources":[{"url":"https://publisher.example.org/valid"},
                             {"url":"https://spark.example.org/valid"}]}]}))
            (b/"2026-11-06-1000ET-access.json").write_text(json.dumps({
               "original":{"doi":"10.1000/unavailable","decision":"TECHNICAL_HOLD_METADATA_ACCESS"},
               "sources":[{"url":"https://api.datacite.org/dois/10.1000/unavailable"}]}))
            r=build(root)
            match=next(x for x in r["events"] if x["doi"]=="10.1000/valid")
            self.assertEqual(match["operational_disposition"],HUMAN)
            self.assertTrue(match["bounded_human_question_to_verify"])
            self.assertFalse(match["new_public_proposal"])
            self.assertEqual(next(x for x in r["events"] if x["doi"]=="10.1000/unavailable")["operational_disposition"],ACCESS)
    def test_explicit_multi_child_expansion_has_independent_bounded_hold_events(self):
        registry=build()
        suffix="2026-11-09-1129ET-seus-rainfall-zenodo-related-ci-award-hold.json"
        matches=[e for e in registry["events"] if e["source_path"].endswith(suffix)]
        self.assertEqual({e["doi"] for e in matches},{
            "10.5281/zenodo.4433147","10.5281/zenodo.5057616"})
        self.assertTrue(all(e["role_in_note"]=="related_output" for e in matches))
        self.assertTrue(all(e["operational_disposition"]==HOLD for e in matches))
        self.assertTrue(all(e["related_parent_doi"]=="10.1029/2021gl096709"
                            for e in matches))
        self.assertTrue(all(e["relationship_verified_from_two_official_sources"]
                            and len(e["related_link_source_urls"])==2
                            for e in matches))
        self.assertTrue(all(not e["formal_original_closed"] and
                            not e["separate_expansion_closed"] and
                            not e["bounded_human_question_to_verify"] and
                            not e["new_public_proposal"] for e in matches))

    def test_unverified_parent_child_link_is_research_only_not_relationship_proof(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            a=root/"scout-operations/historical-crossref-phase2"
            b=root/"scout-operations/monthly-research"
            a.mkdir(parents=True);b.mkdir(parents=True)
            (a/"2026-11-09-unverified-related.json").write_text(json.dumps({
              "research_subject":{"parent_publication_doi":"10.1000/parent",
                                  "child_dois":["10.1000/child"]},
              "operational_disposition":"PROJECT_EVIDENCE_HOLD",
              "source_evidence":[{"url":"https://publisher.example.org/article",
                "type":"official_publisher_article",
                "finding":"Links 10.1000/child to the article"}]}))
            registry=build(root)
            self.assertEqual(len(registry["events"]),1)
            e=registry["events"][0]
            self.assertEqual(e["role_in_note"],"related_output")
            self.assertEqual(e["operational_disposition"],HOLD)
            self.assertFalse(e["relationship_verified_from_two_official_sources"])
            self.assertFalse(e["related_link_source_urls"])
            self.assertFalse(e["bounded_human_question_to_verify"])
            self.assertFalse(e["new_public_proposal"])

    def test_no_inference_from_missing_or_preprint_status(self):
        self.assertEqual(stable_decision("PREPRINT_HOLD"),PREPRINT)
        self.assertEqual(stable_decision("SOFT_DEFER_UNTIL_MATERIAL_WPO_PROJECT_EVIDENCE"),HOLD)
        self.assertEqual(stable_decision("TECHNICAL_HOLD_NO_PROPOSAL"),ACCESS)
        self.assertEqual(stable_decision(""),OTHER)
        self.assertEqual(stable_decision("READY_FOR_VALIDATED_DRAFT_PREFLIGHT"),OTHER)

if __name__=="__main__":unittest.main()
