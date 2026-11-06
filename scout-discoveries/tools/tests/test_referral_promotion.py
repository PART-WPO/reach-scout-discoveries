"""Sourced human referral promotion never consumes unrelated stale inbox drafts."""
import csv
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

TOOLS=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(TOOLS))
from build_manifest import new_batch_has_verified_publication_proof
import promote_inbox

class ReferralPromotionTests(unittest.TestCase):
    def test_immutable_inbox_gate_survives_batch_copy_exact_sha_only(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/"scout-discoveries"
            inbox=root/"inbox";inbox.mkdir(parents=True)
            batch=root/"batches";batch.mkdir()
            raw=b"Candidate ID,Title,DOI\n,Test,10.1000/test\n"
            name="2026-11-06-human-project-test.csv"
            a=inbox/name;b=batch/name
            a.write_bytes(raw);b.write_bytes(raw)
            sha=hashlib.sha256(raw).hexdigest()
            entry={"path":"scout-discoveries/batches/"+name,"sha256":sha}
            gate={"scout-discoveries/inbox/"+name:
                    {"path":"scout-discoveries/inbox/"+name,
                     "sha256":sha,"verdict":"eligible"}}
            self.assertTrue(new_batch_has_verified_publication_proof(entry,gate,root))
            gate["scout-discoveries/inbox/"+name]["verdict"]="hold"
            self.assertFalse(new_batch_has_verified_publication_proof(entry,gate,root))
            gate["scout-discoveries/inbox/"+name]["verdict"]="eligible"
            a.write_bytes(b"tampered")
            self.assertFalse(new_batch_has_verified_publication_proof(entry,gate,root))
            self.assertFalse(new_batch_has_verified_publication_proof(
                {"path":entry["path"],"sha256":"0"*64},gate,root))
    def test_only_new_verified_human_draft_is_selected_not_old_test(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); inbox=root/"scout-discoveries/inbox";inbox.mkdir(parents=True)
            batches=root/"scout-discoveries/batches";batches.mkdir()
            name="2026-11-06-human-project-test.csv"
            known=inbox/name
            stale=inbox/"2026-11-04-crossref-flash-drought-positive-control.csv"
            for path,doi in ((known,"10.1000/verified"),(stale,"10.1000/oldtest")):
                with path.open("w",newline="") as out:
                    w=csv.DictWriter(out,fieldnames=["DOI","Title"])
                    w.writeheader();w.writerow({"DOI":doi,"Title":"A test article"})
            report=root/"scout-operations/human-project-referrals.json"
            report.parent.mkdir(parents=True)
            report.write_text(json.dumps({
                "schema":"reach-scout-bounded-project-human-referral-v1",
                "private_hub_imports":"NOT_VERIFIED",
                "new_approved_reach_outputs":0,
                "human_referral_drafts_prevalidated":1,
                "draft_paths":["scout-discoveries/inbox/"+name],
                "referrals":[{"doi":"10.1000/verified",
                    "disposition":"READY_FOR_VALIDATED_HUMAN_PROJECT_REFERRAL",
                    "scout_inbox_status":"VALIDATED_INBOX_DRAFT_NOT_PRIVATE_HUB"}]}))
            with patch.object(promote_inbox,"REPO",root),\
                 patch.object(promote_inbox,"INBOX",inbox),\
                 patch.object(promote_inbox,"BATCHES",batches):
                self.assertEqual(promote_inbox.changed_inbox("", "",True),[known])
                self.assertNotIn(stale,promote_inbox.changed_inbox("","",True))
                report.write_text(report.read_text().replace("10.1000/verified","10.1000/wrong"))
                with self.assertRaisesRegex(ValueError,"Unrecognized DOI"):
                    promote_inbox.changed_inbox("","",True)

if __name__=="__main__":unittest.main()
