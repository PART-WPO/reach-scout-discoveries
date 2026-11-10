"""Offline regression tests for GitHub-owned verified original handoff and cooldown."""
import csv
import hashlib
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import hourly_decision_handoff as mission

NOW = datetime(2026, 11, 10, 2, 0, tzinfo=timezone.utc)
D1 = "10.1175/mwr-d-25-0146.1"
D2 = "10.1175/mwr-d-26-0134.1"
A1 = "NA24OARX459C0006"
A2 = "NA24OARX459C0001"


def item(doi, award, title):
    return {"doi": doi, "title": title, "priority": 90,
            "funding_signal": "CONFIRMED_WPO_459",
            "wpo_459_award_numbers": [award],
            "lane": "NOVEL_IDENTITY_RESEARCH",
            "already_in_public_scout_queue": False,
            "award_evidence_source_batches": [
                "api-discoveries/historical-crossref/batches/archive.csv"]}


def official(doi, title, award):
    return {"status": "ok", "provider": "crossref",
            "evidence": "https://api.crossref.org/works/" + doi,
            "title": title, "pub_date": "2026-09-01",
            "publication_status": "official_journal_article",
            "resource_type": "journal-article",
            "creators": ["An Official Author"],
            "funding_references": [{"name": "NOAA", "award": [award]}]}


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.rows = [
            item(D1, A1, "Estimates of Entrainment Zone Depth across the United States"),
            item(D2, A2, "Convection Allowing Ensemble Based Land Atmosphere Coupling"),
            item("10.1175/mwr-d-19-0165.1", "NA16OAR4590216", "Corrigendum"),
        ]
        for rel, data in {
            "scout-operations/research-outcome-registry.json": b'{"schema":"mock"}',
            "scout-operations/preprint-watchlist.json": json.dumps({
                "schema":"reach-scout-preprint-watchlist-v1", "entries":[]}).encode(),
            "api-discoveries/historical-crossref/batches/archive.csv": b"DOI,NOAA Award Number(s)\n",
            "scout-operations/historical-crossref-screening/actionable-routing.json": b'{}',
        }.items():
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
        src = {p: mission.checksum((self.root / p).read_bytes()) for p in (
            "scout-operations/research-outcome-registry.json",
            "scout-operations/preprint-watchlist.json",
            "api-discoveries/historical-crossref/batches/archive.csv",
            "scout-operations/historical-crossref-screening/actionable-routing.json")}
        q = {"schema":"reach-scout-crossref-candidate-queue-v2",
             "items":self.rows, "source_sha256":src}
        p = self.root / mission.QUEUE
        p.write_text(json.dumps(q))

    def test_public_selection_inputs_must_be_current(self):
        p=self.root/mission.QUEUE
        queue=json.loads(p.read_text())
        queue["dynamic_selection_sha256"]={
            "scout-operations/research-outcome-registry.json":
            mission.checksum((self.root/"scout-operations/research-outcome-registry.json").read_bytes())}
        p.write_text(json.dumps(queue))
        mission.verified_queue(self.root)
        (self.root/"scout-operations/research-outcome-registry.json").write_text("different")
        with self.assertRaisesRegex(ValueError,"STALE_QUEUE"):
            mission.verified_queue(self.root)

    def test_source_fingerprint_must_be_fresh(self):
        self.assertEqual(len(mission.verified_queue(self.root)["items"]), 3)
        (self.root / "scout-operations/research-outcome-registry.json").write_text("modified")
        with self.assertRaisesRegex(ValueError, "STALE_QUEUE_SOURCE"):
            mission.verified_queue(self.root)

    def test_corrigendum_is_routed_out_of_autonomous_originals(self):
        queue = mission.verified_queue(self.root)
        choices, skipped = mission.candidate_order(queue, mission.read_ledger(self.root), NOW)
        self.assertEqual([x["doi"] for x in choices], [D1, D2])
        self.assertEqual(skipped[-1]["doi"], "10.1175/mwr-d-19-0165.1")
        self.assertEqual(skipped[-1]["reason"], "SPECIAL_PUBLICATION_TYPE_REVIEW")

    def test_scientific_bias_correction_is_not_editorial_notice(self):
        from special_publication_types import special_publication_type
        self.assertEqual(special_publication_type("Bias Correction of NWP Forecasts"), "")
        self.assertEqual(special_publication_type("Correction of radar bias in forecasts"), "")
        self.assertEqual(special_publication_type("Correction to: Original Article"), "CORRECTION_NOTICE")
        self.assertEqual(special_publication_type("Corrigendum"), "CORRIGENDUM")
        normal = item("10.1234/science",A1,"Bias Correction of NWP Forecasts")
        choices, skipped = mission.candidate_order({"items":[normal]},
                             mission.read_ledger(self.root), NOW)
        self.assertEqual(len(choices),1)
        self.assertEqual(skipped,[])

    def test_official_crossref_unavailable_rotates_and_persists_cooldown(self):
        lookup = {D1: {"status":"unavailable_or_not_found"},
                  D2: official(D2, self.rows[1]["title"], A2)}
        identity = {"status":"NO_PUBLIC_IDENTITY_MATCH",
                    "noaa_ir_reach_check":{"status":"DOI_NOT_IN_VERIFIED_IR_INDEX_UNKNOWN"}}
        fake_report = {"referrals":[{
            "doi":D2,"disposition":"READY_FOR_VALIDATED_HUMAN_PROJECT_REFERRAL",
            "scout_inbox_status":"VALIDATED_INBOX_DRAFT_NOT_PRIVATE_HUB"}],
            "human_referral_drafts_prevalidated":1, "draft_paths":[]}
        fake_reg = {"research_note_events":1, "events":[], "cases":[]}
        with patch.object(mission, "identity_check", return_value=identity), \
             patch.object(mission, "build_registry", return_value=fake_reg), \
             patch.object(mission, "build_referrals", return_value=fake_report):
            result=mission.run(root=self.root, now=NOW, metadata_fn=lambda d:lookup[d],
                               public={}, ir_index={"dois":{}}, stage=True)
        self.assertEqual(result["attempted_originals"], 2)
        self.assertEqual([x["status"] for x in result["outcomes"]],
                         ["BLOCKED","STAGED_VALIDATED_INBOX"])
        self.assertEqual(result["outcomes"][0]["decision"],"OFFICIAL_METADATA_UNAVAILABLE")
        ledger=mission.read_ledger(self.root)
        self.assertGreater(datetime.fromisoformat(ledger["cases"][D1]["retry_after"]),NOW)
        self.assertEqual(ledger["cases"][D2]["state"],"STAGED_VALIDATED_INBOX")
        notes=list((self.root / mission.NOTES).glob("auto-*.json"))
        self.assertEqual(len(notes),1)
        note=json.loads(notes[0].read_text())
        self.assertEqual(note["structured_award"],A2)
        self.assertIn("official",note["source_evidence"][0]["type"])
        self.assertEqual(note["private_hub_action"],"NONE")
        choices,_ = mission.candidate_order({"items": self.rows}, ledger,
                                            NOW + timedelta(minutes=10))
        self.assertFalse(any(x["doi"] in {D1,D2} for x in choices))

    def test_auto_verified_note_enters_real_research_registry(self):
        from build_research_outcome_registry import build
        note_dir = self.root / mission.NOTES
        note_dir.mkdir(parents=True, exist_ok=True)
        (self.root / "scout-operations/monthly-research").mkdir(parents=True)
        md = official(D1, self.rows[0]["title"], A1)
        identity={"status":"NO_PUBLIC_IDENTITY_MATCH",
                  "noaa_ir_reach_check":{"status":"DOI_NOT_IN_VERIFIED_IR_INDEX_UNKNOWN"}}
        rel, doc = mission.screened_note(D1, self.rows[0], md, A1, identity, NOW)
        (self.root / rel).write_text(json.dumps(doc))
        report=build(self.root)
        records=[e for e in report["events"] if e.get("doi")==D1]
        self.assertEqual(len(records),1)
        self.assertEqual(records[0]["source_path"],rel)
        self.assertGreaterEqual(records[0]["source_count"],2)
        self.assertEqual(records[0]["research_lane"],"historical_crossref_original")

    def test_technical_handoff_rejection_rotates_to_second_source_verified_doi(self):
        metadata = {D1:official(D1,self.rows[0]["title"],A1),
                    D2:official(D2,self.rows[1]["title"],A2)}
        ident={"status":"NO_PUBLIC_IDENTITY_MATCH",
               "noaa_ir_reach_check":{"status":"DOI_NOT_IN_VERIFIED_IR_INDEX_UNKNOWN"}}
        counter=[0]
        def fake_referrals(**kwargs):
            counter[0]+=1
            if counter[0]==1:
                return {"referrals":[{"doi":D1,"disposition":"HOLD_METADATA_VALIDATION",
                                      "scout_inbox_status":"NOT_STAGED"}],
                        "human_referral_drafts_prevalidated":0,"draft_paths":[]}
            return {"referrals":[{"doi":D2,
                     "disposition":"READY_FOR_VALIDATED_HUMAN_PROJECT_REFERRAL",
                     "scout_inbox_status":"VALIDATED_INBOX_DRAFT_NOT_PRIVATE_HUB"}],
                    "human_referral_drafts_prevalidated":1,"draft_paths":[]}
        with patch.object(mission,"identity_check",return_value=ident), \
             patch.object(mission,"build_registry",return_value={"events":[],"cases":[]}), \
             patch.object(mission,"build_referrals",side_effect=fake_referrals):
            report=mission.run(root=self.root,now=NOW,metadata_fn=lambda doi:metadata[doi],
                        public={},ir_index={"dois":{}},stage=True,limit=2)
        self.assertEqual(report["attempted_originals"],2)
        self.assertEqual(report["public_review_handoffs_staged"],1)
        self.assertEqual([x["status"] for x in report["outcomes"]],
                         ["BLOCKED","STAGED_VALIDATED_INBOX"])
        self.assertEqual(counter[0],2)

    def test_unverified_award_cannot_stage(self):
        md=official(D1,self.rows[0]["title"],"NA19NES4320002")
        result=mission.run(root=self.root,now=NOW,metadata_fn=lambda doi:md,
                           public={},ir_index={"dois":{}},limit=1,stage=False)
        self.assertEqual(result["outcomes"][0]["decision"],"PUBLISHER_459_NOT_VERIFIED")
        self.assertEqual(result["public_review_handoffs_staged"],0)
        self.assertFalse((self.root / mission.NOTES).exists())

    def test_public_manifest_required_to_claim_completion(self):
        doi=D2
        ledger={"schema":mission.SCHEMA,"cases":{doi:{
            "state":"STAGED_VALIDATED_INBOX","source_note":"some.json"}},
            "last_mission":None}
        p=self.root / mission.LEDGER
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(ledger))
        result={"schema":mission.SCHEMA,"outcomes":[{
            "doi":doi,"status":"STAGED_VALIDATED_INBOX","award":A2}],
            "attempted_originals":1,"public_review_handoffs_staged":1}
        q=self.root / mission.REPORT
        q.parent.mkdir(parents=True,exist_ok=True)
        q.write_text(json.dumps(result))
        batch=self.root / "scout-discoveries/batches/test.csv"
        batch.parent.mkdir(parents=True,exist_ok=True)
        with batch.open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=["DOI","NOAA Award Number(s)","Scout Discovery Rationale"])
            w.writeheader()
            w.writerow({"DOI":doi,"NOAA Award Number(s)":A2,
                        "Scout Discovery Rationale":"Scout classification: NEW CANDIDATE"})
        manifest={"batches":[{"path":batch.relative_to(self.root).as_posix(),
                             "sha256":mission.checksum(batch.read_bytes())}]}
        (self.root / "scout-discoveries/manifest.json").write_text(json.dumps(manifest))
        published=mission.confirm_published(self.root)
        self.assertEqual(published["public_review_batches_validated_this_run"],1)
        self.assertEqual(mission.read_ledger(self.root)["cases"][doi]["state"],
                         "PUBLISHED_PUBLIC_SCOUT")


if __name__ == "__main__":
    unittest.main()
