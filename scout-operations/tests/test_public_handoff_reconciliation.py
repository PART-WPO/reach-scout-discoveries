"""Two real DOI regressions: retired REACH preprint and already-staged Scout article."""
import csv
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from reconcile_public_handoff import (public_reach_preprint_resolutions,
                                     active_public_scout, reconcile, run)
from reach_version_identity import version_links, version_decision
from build_candidate_queue import build as build_queue
from hourly_decision_handoff import candidate_order

PRE = "10.5194/gmd-2022-311"
FINAL = "10.5194/gmd-16-3809-2023"
UID = "reachuid-v1-04d227bc0979ce0e23a055c1a3eba317"
IR = "https://repository.library.noaa.gov/view/noaa/58453"
MWR = "10.1175/mwr-d-25-0146.1"
TITLE = "Estimates of Entrainment Zone Depth across the United States from Dual-Polarization WSR-88D Radar Observations"
BATCH = "scout-discoveries/batches/2026-11-10-human-project-8eb678e5c990af2471.csv"

def write(root, path, doc):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")

def fixture(root):
    write(root, "scout-operations/preprint-retirement-archive.json", {
        "schema":"reach-scout-preprint-retirement-archive-v1",
        "entries":[{"preprint_doi":PRE,"published_doi":FINAL,
                    "reach_ids":[UID], "verification_source":IR,
                    "reason":"OFFICIAL_PUBLISHED_VERSION_CONFIRMED_IN_PUBLIC_REACH"}]})
    cache = {"schema":"reach-scout-identity-index-v1",
             "sources":{}, "records":[{"source":"REACH", "identity":UID,
                                        "urls":[IR], "dois":[], "title":"Spring wheat paper"}]}
    cp = root/"scout-operations/reach-comparison-cache/comparison-index.json"
    cp.parent.mkdir(parents=True, exist_ok=True)
    cp.write_text('{"records":[]}\n')
    cache["sources"]["reach_cache_sha256"] = hashlib.sha256(cp.read_bytes()).hexdigest()
    write(root,"scout-operations/identity-cache/public-identity-index.json",cache)
    file = root / BATCH
    file.parent.mkdir(parents=True, exist_ok=True)
    with file.open("w",newline="",encoding="utf-8") as stream:
        w=csv.DictWriter(stream,fieldnames=["DOI","Title","Output Type"])
        w.writeheader()
        w.writerow({"DOI":MWR,"Title":TITLE,"Output Type":"1"})
    write(root,"scout-discoveries/manifest.json",{
        "schema":"reach-scout-discovery-feed-v1",
        "batches":[{"path":BATCH, "record_count":1,
                    "sha256":hashlib.sha256(file.read_bytes()).hexdigest()}]})
    write(root,"scout-operations/historical-crossref-screening/actionable-routing.json",{
        "entries":[{"doi":MWR,"title":TITLE},
                   {"doi":PRE,"title":"Developing spring wheat in the Noah-MP LSM"}]})
    write(root,"scout-operations/decision-handoff-ledger.json",{
        "schema":"reach-scout-hourly-decision-handoff-v1",
        "last_mission":{"at":"2026-11-10T16:43:08Z"},
        "cases":{
            PRE: {"state":"BLOCKED","reason":"OFFICIAL_PUBLICATION_UNVERIFIED",
                  "attempt_count":1,"checked_at":"2026-11-10T16:43:08Z",
                  "retry_after":"2026-11-11T16:43:08Z","private_hub_import":"NOT_VERIFIED"},
            MWR: {"state":"BLOCKED","reason":"NOT_NEW_IN_REACH_OR_SCOUT",
                  "attempt_count":2,"checked_at":"2026-11-10T02:55:34Z",
                  "retry_after":"2026-12-10T02:55:34Z","private_hub_import":"NOT_VERIFIED"},
            "10.1234/unresolved":{"state":"BLOCKED","reason":"OFFICIAL_METADATA_UNAVAILABLE",
                  "retry_after":"2026-11-12T00:00:00Z"},
        }})

class PublicHandoffReconciliationTests(unittest.TestCase):
    def test_public_evidence_separates_resolved_from_hub_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            fixture(root)
            retired=public_reach_preprint_resolutions(root)
            self.assertEqual(retired[PRE]["reach_uid"],UID)
            self.assertEqual(retired[PRE]["published_doi"],FINAL)
            published=active_public_scout(root)
            self.assertEqual(published[MWR][0]["path"],BATCH)
            report=run(root)
            self.assertEqual({x["doi"] for x in report["changed_cases"]},{PRE,MWR})
            ledger=json.loads((root/"scout-operations/decision-handoff-ledger.json").read_text())
            pre, mwr=ledger["cases"][PRE],ledger["cases"][MWR]
            self.assertEqual(pre["state"],"RESOLVED_EXISTING_REACH")
            self.assertEqual(pre["original_publication_eligibility"],"PREPRINT_DOI_NOT_ELIGIBLE")
            self.assertEqual(pre["reach_uid"],UID)
            self.assertEqual(mwr["state"],"PUBLISHED_PUBLIC_SCOUT")
            self.assertEqual(mwr["published_batch"],BATCH)
            self.assertNotIn("retry_after",pre)
            self.assertNotIn("retry_after",mwr)
            self.assertEqual(mwr["downstream_hub_verification"],"NOT_VERIFIED")
            self.assertEqual(mwr["private_hub_import"],"NOT_VERIFIED")
            self.assertFalse(mwr["seed_expansion_closed"])
            self.assertEqual(ledger["cases"]["10.1234/unresolved"]["state"],"BLOCKED")
            self.assertEqual(len(report["active_research_retry_cases"]),1)
            self.assertIn(MWR,report["public_scout_pending_private_verification"])
            self.assertEqual(run(root,check=True)["changed_cases"],[])

    def test_stale_archive_does_not_clear_a_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            fixture(root)
            cache=root/"scout-operations/reach-comparison-cache/comparison-index.json"
            cache.write_text('{"changed":true}')
            with self.assertRaisesRegex(ValueError,"out of sync"):
                public_reach_preprint_resolutions(root)

    def test_wrong_iris_and_nonpublication_scout_unit_do_not_resolve(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            fixture(root)
            doc=json.loads((root/"scout-operations/identity-cache/public-identity-index.json").read_text())
            doc["records"][0]["urls"]=["https://repository.library.noaa.gov/view/noaa/98765"]
            write(root,"scout-operations/identity-cache/public-identity-index.json",doc)
            self.assertNotIn(PRE,public_reach_preprint_resolutions(root))
            record=root/BATCH
            record.write_text("DOI,Title,Output Type\n"+MWR+","+TITLE+",2\n")
            manifest=json.loads((root/"scout-discoveries/manifest.json").read_text())
            manifest["batches"][0]["sha256"]=hashlib.sha256(record.read_bytes()).hexdigest()
            write(root,"scout-discoveries/manifest.json",manifest)
            r=run(root)
            self.assertEqual(r["changed_cases"],[])

    def test_corrupt_manifest_never_grants_public_scout_fast_exit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            fixture(root)
            (root/BATCH).write_text("tampered")
            with self.assertRaisesRegex(ValueError,"SHA mismatch"):
                active_public_scout(root)

    def test_uid_and_ir_match_in_existing_version_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            fixture(root)
            links=version_links(root)
            article={"record_id":"reach-000251","reach_uid":UID,
                     "output_type":"1","link":IR,"title":"Spring wheat"}
            index={"by_doi":{},"by_id":{"reach-000251":article},
                   "by_uid":{UID:article},"by_url":{IR:[article]}}
            row={"DOI":FINAL,"Output Type":"1",
                 "Scout Discovery Rationale":"Scout classification: NEW CANDIDATE",
                 "Existing REACH Match":"None"}
            decision=version_decision(row,links,index)
            self.assertEqual(decision[0],"identity_hold")
            self.assertIn("reach-000251",decision[1])
            self.assertIn(UID,decision[1])
            self.assertIn(IR,links[FINAL]["official_ir_urls"])

    def test_repository_snapshot_has_actual_evidence_for_both_cases(self):
        # Run on the current SHA-verified source snapshot, never the private Hub.
        root=Path(__file__).resolve().parents[2]
        verified=public_reach_preprint_resolutions(root)
        self.assertEqual(verified[PRE]["reach_uid"],UID)
        self.assertEqual(verified[PRE]["published_doi"],FINAL)
        public=active_public_scout(root)
        self.assertTrue(any(x["path"]==BATCH and x["output_type"]=="1"
                            for x in public[MWR]))
        ledger=json.loads((root/"scout-operations/decision-handoff-ledger.json").read_text())
        self.assertEqual(ledger["cases"][PRE]["state"],"RESOLVED_EXISTING_REACH")
        self.assertEqual(ledger["cases"][MWR]["state"],"PUBLISHED_PUBLIC_SCOUT")
        self.assertNotIn("retry_after",ledger["cases"][PRE])
        self.assertNotIn("retry_after",ledger["cases"][MWR])

    def test_original_queue_fast_exit_preserves_expansion(self):
        routing={"total":2,"bulk_identity_screening":{"source_dois":2},"entries":[
            {"doi":PRE,"title":"Spring wheat","bulk_identity_gate":{"status":"NO_PUBLIC_REACH_MATCH"}},
            {"doi":MWR,"title":TITLE,"bulk_identity_gate":{"status":"NO_PUBLIC_REACH_MATCH"},
             "scout_public_queue_matches":[{"source":"SCOUT_PUBLISHED","location":BATCH,
                                            "basis":["exact_doi","normalized_title"]}]}]}
        ledger={"cases":{PRE:{"state":"BLOCKED",
                              "reason":"OFFICIAL_PUBLICATION_UNVERIFIED",
                              "retry_after":"2026-11-11T16:43:08Z"},
                         MWR:{"state":"BLOCKED","reason":"NOT_NEW_IN_REACH_OR_SCOUT",
                              "retry_after":"2026-12-10T02:55:34Z"}}}
        retirement={PRE:{"published_doi":FINAL,"reach_uid":UID}}
        q=build_queue(routing,{"cases":[]},
                      retired_preprints=retirement,handoff_ledger=ledger)
        by={x["doi"]:x for x in q["items"]}
        self.assertEqual(by[PRE]["lane"],"RETIRED_PREPRINT_EXISTING_REACH_FAST_EXIT")
        self.assertEqual(by[MWR]["lane"],"ALREADY_IN_SCOUT_REVIEW_FAST_EXIT")
        self.assertFalse(by[PRE]["one_mission_disposition_required"])
        self.assertFalse(by[MWR]["one_mission_disposition_required"])
        self.assertIn("expansion",by[PRE]["next_action"].lower())
        due, skipped=candidate_order(q,ledger,datetime(2026,11,10,tzinfo=timezone.utc))
        self.assertEqual(due,[])

if __name__=="__main__":
    unittest.main()
