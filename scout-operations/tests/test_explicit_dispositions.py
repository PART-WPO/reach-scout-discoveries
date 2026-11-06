import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from reconcile_research_dispositions import build,disposition,identify

class ExplicitDispositions(unittest.TestCase):
    def test_all_current_sources_accounted_and_unchanged(self):
        r=build()
        self.assertGreaterEqual(r["source_files_scanned"],25)
        self.assertEqual(r["identities_with_case_dispositions"],len(r["records"]))
        self.assertEqual(sum(r["operational_counts"].values()),len(r["records"]))
        self.assertEqual(r["automatic_status_changes"],0)
        self.assertEqual(len({(x["lane"],x["identity"]) for x in r["records"]}),len(r["records"]))
        self.assertTrue(all(not x["scout_proposal_staged"] and not x["expansion_closed"]
              and x["human_review_import"]=="NOT_VERIFIED" for x in r["records"]))
        for file in r["source_file_sha256"]:
            b=(Path(__file__).resolve().parents[2]/file["path"]).read_bytes()
            self.assertEqual(hashlib.sha256(b).hexdigest(),file["sha256"])
    def test_real_monthly_ecmwf_research_remains_metadata_hold(self):
        r=build()
        row=next(x for x in r["records"] if x["doi"]=="10.21957/e8rz-wh72"
                 and x["lane"]=="monthly_research")
        self.assertIn(row["operational_disposition"],{
            "METADATA_ACCESS_RETRY","PROJECT_SCOPE_EVIDENCE_HOLD"})
        self.assertGreaterEqual(len(row["source_evidence"]),1)
    def test_preprint_parent_does_not_become_published_from_child_article(self):
        obj={"original_doi":"10.1002/essoar.10504829.1",
             "original_publication_status":"PREPRINT_HOLD",
             "published_related_doi":"10.1029/2021GL096709"}
        self.assertEqual(disposition(obj,obj),"PREPRINT_WATCHLIST")
    def test_human_decision_is_not_inferred_from_bounded_search(self):
        r=build()
        self.assertFalse(any(x["research_completed_in_original_ledger"] for x in r["records"]))
        self.assertFalse(any(x["human_approval"]!="NOT_VERIFIED" for x in r["records"]))
    def test_nested_doi_not_confused_with_different_parent(self):
        nested={"doi":"10.1109/past49659.2022.9975045"}
        parent={"original_doi":"10.1000/parent","cases":[nested]}
        self.assertEqual(identify(nested,parent)[0],"doi:10.1109/past49659.2022.9975045")
    def test_url_only_repository_does_not_invent_doi(self):
        obj={"identity":{"type":"URL_ONLY_CODE",
                         "canonical_url":"https://github.com/coreypotvin/wofs_fcst_skill",
                         "doi":None}}
        identity,d=identify(obj,obj)
        self.assertTrue(identity.startswith("code:"))
        self.assertIsNone(d)
    def test_unsafe_relative_source_fails_closed(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            for d in ("scout-operations/monthly-research",
                      "scout-operations/historical-crossref-phase2"):
                (root/d).mkdir(parents=True)
            f=root/"scout-operations/monthly-research/2026-11-06-case.json"
            f.write_text(json.dumps({"doi":"10.1000/test","decision":"BOUNDED_RESEARCH_COMPLETE_NEEDS_HUMAN_PROJECT_ASSESSMENT"}))
            j=build(root)
            self.assertEqual(j["operational_counts"]["BOUNDED_HUMAN_PROJECT_QUESTION"],1)
            self.assertEqual(j["records"][0]["source_evidence"][0]["sha256"],
                             hashlib.sha256(f.read_bytes()).hexdigest())

if __name__=="__main__":unittest.main()
