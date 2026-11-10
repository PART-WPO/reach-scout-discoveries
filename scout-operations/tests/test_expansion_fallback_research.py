"""Offline bounded expansion work: rotate and record real external lookups, never claim staging."""
import hashlib
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import expansion_fallback_research as m

NOW = datetime(2026, 11, 10, 14, tzinfo=timezone.utc)
D1="10.1029/2021gl096709"
D2="10.1002/2017ms001154"
CHILD="10.5281/zenodo.1234"

class FallbackTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        evidence="scout-operations/independent-discovery-leads.json"
        p=self.root/evidence
        p.parent.mkdir(parents=True)
        p.write_text('{"source":"public"}')
        self.evidence=evidence
        self.graph={
            "schema":"reach-scout-crosslane-research-memory-v1",
            "source_fingerprint":"f"*64,"builder_policy_sha256":"b"*64,
            "source_evidence_sha256":{"research_notes_sha256":{},
                "related_lead_file_sha256":{evidence:hashlib.sha256(p.read_bytes()).hexdigest()}},
            "nodes":[
                self.node(D1,"1"*64,[CHILD]),
                self.node(D2,"2"*64,[]),
            ],
            "work_items":[
                {"doi":D1,"track":"EXPANSION","next_action":"EXPAND_VERIFIED_WPO_REACH_SEED"},
                {"doi":D2,"track":"EXPANSION","next_action":"EXPAND_VERIFIED_WPO_REACH_SEED"}],
            "links":[{"source_doi":D1,"related_doi":CHILD,
                      "source_files":[{"source_file":evidence,
                       "source_sha256":hashlib.sha256(p.read_bytes()).hexdigest()}]}]
        }
        self.write_graph()
        q=self.root/m.WORKSTREAM
        q.parent.mkdir(parents=True,exist_ok=True)
        q.write_text(json.dumps({"monthly_api":{"original_decisions_due":0,
           "originals_for_final_checks":0,"pending_metadata_blockers_including_originals":0}}))
        self.calls=[]
        def metadata(doi):
            self.calls.append(doi)
            return {"status":"ok","provider":"crossref","title":"Verified exact DOI title",
                "evidence":"https://api.crossref.org/works/"+doi,
                "publication_status":"official_journal_article","funding_references":[]}
        self.metadata=metadata

    def node(self,doi,fingerprint,children):
        return {"doi":doi,"public_reach_verified_existing":True,"preprint_or_version_hold":False,
                "expansion_research":{"input_fingerprint":fingerprint,
                  "explicit_related_dois":children,"recorded_related_note_count":0,
                  "separate_expansion_closed_by_memory":False}}

    def write_graph(self):
        p=self.root/m.GRAPH
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(self.graph))
        idx=self.root/m.INDEX
        idx.write_text(json.dumps({"schema":"reach-scout-compact-crosslane-mission-index-v1",
            "source_fingerprint":self.graph["source_fingerprint"],
            "builder_policy_sha256":self.graph["builder_policy_sha256"]}))

    def test_select_and_research_linked_seed_then_rotate(self):
        first=m.run(self.root,NOW,"1212",self.metadata)
        self.assertEqual(first["seed"],D1)
        self.assertEqual(first["source_lookup_count"],2)
        self.assertEqual(self.calls,[D1,CHILD])
        note=json.loads((self.root/first["research_report"]).read_text())
        self.assertEqual(note["new_public_candidate_count"],0)
        self.assertEqual(note["separate_expansion_decisions_completed"],0)
        self.assertEqual(note["private_hub_import"],"NOT_VERIFIED")
        self.assertEqual(note["explicit_related_dois_preserved"],[CHILD])
        second=m.run(self.root,NOW+timedelta(hours=1),"1213",self.metadata)
        self.assertEqual(second["seed"],D2)
        self.assertEqual(second["related_leads_checked"],0)
        exhausted=m.run(self.root,NOW+timedelta(hours=2),"1214",self.metadata)
        self.assertEqual(exhausted["status"],"NO_ELIGIBLE_UNWORKED_EXPANSION_SEED")
        self.assertEqual(len(self.calls),3)

    def test_monthly_priority_never_consumes_seed(self):
        p=self.root/m.WORKSTREAM
        p.write_text(json.dumps({"monthly_api":{"original_decisions_due":1}}))
        result=m.run(self.root,NOW,"1234",self.metadata)
        self.assertEqual(result["status"],"MONTHLY_ORIGINALS_HAVE_PRIORITY")
        self.assertEqual(self.calls,[])

    def test_prior_hold_no_loop_until_new_source_fingerprint(self):
        first=m.run(self.root,NOW,"1212",self.metadata)
        ledger=m.read_ledger(self.root)
        self.assertEqual(ledger["cases"][D1]["status"],"OFFICIAL_SOURCE_CHECK_RECORDED")
        self.assertGreater(datetime.fromisoformat(ledger["cases"][D1]["recheck_after"]),NOW)
        self.graph["nodes"][0]["expansion_research"]["input_fingerprint"]="9"*64
        self.write_graph()
        self.assertEqual(m.pick_seed(self.graph,ledger,NOW+timedelta(minutes=1))[0],D1)

    def test_source_sha_mismatch_fails_closed(self):
        (self.root/self.evidence).write_text("tampered")
        with self.assertRaisesRegex(ValueError,"STALE_EXPANSION_SOURCE"):
            m.source_snapshot(self.root)

    def test_official_access_error_not_counted_as_new_output(self):
        def failing(_doi):
            raise ConnectionError("network blocked")
        row=m.run(self.root,NOW,"1212",failing)
        self.assertEqual(row["status"],"TECHNICAL_ACCESS_HOLD")
        note=json.loads((self.root/row["research_report"]).read_text())
        self.assertEqual(note["source_lookups"][0]["source_status"],"OFFICIAL_METADATA_ACCESS_ERROR")
        self.assertEqual(note["new_related_output_eligibility_confirmed"],0)


    def test_source_driven_dataset_stays_research_only_pending_exact_award(self):
        dataset = "10.6075/j0sn07g9"
        def source(seed):
            return {
                "schema": "reach-scout-source-driven-expansion-v1",
                "seed_doi": seed, "status": "SOURCE_BACKED_LEADS_FOUND",
                "source_checks": [{"kind": "publisher_article_html", "status": "SOURCE_READ"}],
                "discovered_doi_leads": [{
                    "doi": dataset, "source_url": "https://onlinelibrary.wiley.com/doi/10.1002/hyp.13998",
                    "source_sha256": "a"*64, "evidence_kind": "crossref_structured_data_code_citation",
                    "eligibility": "RESEARCH_LEAD_ONLY"}],
            }
        def meta(doi):
            return {"status": "ok", "provider": "datacite", "title": "Data from: soil moisture network",
                    "resource_type": "Dataset", "publication_status": "other_or_unverified",
                    "evidence": "https://api.datacite.org/dois/" + doi, "funding_references": []}
        def identity(_doi,_title):
            return {"status": "NO_PUBLIC_IDENTITY_MATCH",
                    "noaa_ir_reach_check": {"status": "DOI_NOT_IN_VERIFIED_IR_INDEX_UNKNOWN"}}
        result = m.run(self.root, NOW, "2020", meta, source_fn=source, identity_fn=identity, seed_override=D2)
        self.assertEqual(result["seed"], D2)
        self.assertEqual(result["source_driven_leads_found"], 1)
        note = json.loads((self.root/result["research_report"]).read_text())
        child = note["new_source_driven_leads_screened"][0]
        self.assertEqual(child["doi"], dataset)
        self.assertEqual(child["next_gate"], "VERIFY_EXACT_OUTPUT_WPO_PROJECT_FUNDING")
        self.assertEqual(child["eligibility"], "RESEARCH_LEAD_ONLY_NOT_STAGED")
        self.assertEqual(note["new_related_output_eligibility_confirmed"], 0)
        self.assertEqual(note["separate_expansion_decisions_completed"], 0)
        self.assertEqual(note["new_public_candidate_count"], 0)
        self.assertEqual(note["private_hub_import"], "NOT_VERIFIED")

    def test_source_driven_existing_public_identity_never_restaged(self):
        dataset = "10.6075/j0sn07g9"
        def source(seed):
            return {"schema":"reach-scout-source-driven-expansion-v1", "seed_doi":seed,
                    "discovered_doi_leads":[{"doi":dataset}]}
        def identity(_doi, _title):
            return {"status":"CONFIRMED_PUBLIC_REACH_IDENTITY",
                    "noaa_ir_reach_check":{"status":"NOT_NEEDED_DIRECT_REACH"}}
        result = m.run(self.root, NOW, "2021", self.metadata,
                       source_fn=source, identity_fn=identity, seed_override=D2)
        note = json.loads((self.root/result["research_report"]).read_text())
        self.assertEqual(note["new_source_driven_leads_screened"][0]["next_gate"],
                         "EXISTING_PUBLIC_IDENTITY_NO_RESTAGING")
        self.assertEqual(note["new_public_candidate_count"], 0)

    def test_manual_seed_respects_ledger_cooldown(self):
        result = m.run(self.root, NOW, "2000", self.metadata, seed_override=D2)
        self.assertEqual(result["seed"], D2)
        with self.assertRaisesRegex(ValueError, "not eligible or remains on cooldown"):
            m.run(self.root, NOW+timedelta(minutes=2), "2001", self.metadata, seed_override=D2)

if __name__=="__main__":
    unittest.main()
