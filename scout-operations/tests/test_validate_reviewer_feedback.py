import hashlib
import hmac
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from validate_reviewer_feedback import (
    event_message,verify_event,extract_valid_events,run
)

KEY="a-long-random-looking-private-key-for-test-only-123456"
ID="scoutnew-v1-"+"a"*32
DOI="10.1000/reviewer"

def signed_event(decision="ON_HOLD",**overrides):
    e={"candidate_id":ID,"doi":DOI,"decision":decision,
       "reviewed_at":"2026-11-05T19:00:00.000Z",
       "finding_fingerprint":"a"*32,
       "decision_fingerprint":"a"*32}
    e.update(overrides)
    e["signature"]=hmac.new(KEY.encode(),event_message(e),hashlib.sha256).hexdigest()
    return e

class FeedbackTests(unittest.TestCase):
    def fake_index(self,doi=DOI):
        return {"source_fingerprint":"dummy_verified_public_index",
                "records":[{"source":"SCOUT_PUBLISHED","identity":ID,"dois":[doi]}]}
    def test_authenticated_real_candidate_enters_redacted_feedback(self):
        e=signed_event("ALREADY_IN_REACH")
        bundle={"schema":"reach-scout-signed-review-feedback-v1",
                "source":"DiscoveryHubPrivateExport","events":[e]}
        valid,pending=extract_valid_events([("private-bundle.json",bundle,"f"*64)],
                                            self.fake_index(),KEY)
        self.assertEqual(len(valid),1)
        self.assertEqual(pending,[])
        self.assertTrue(valid[0]["private_hub_action_verified"])
        self.assertFalse(valid[0]["smartsheet_write_verified"])
        self.assertFalse(valid[0]["public_reach_addition_verified"])
        self.assertNotIn("Reviewer Email",json.dumps(valid))
    def test_wrong_signing_key_and_extra_personal_data_fail_closed(self):
        e=signed_event()
        with self.assertRaisesRegex(ValueError,"signature mismatch"):
            verify_event(e,"wrong key")
        e["reviewer_email"]="private@noaa.gov"
        with self.assertRaisesRegex(ValueError,"unexpected"):
            verify_event(e,KEY)
    def test_unlinked_public_identity_is_not_used_as_live_review_signal(self):
        e=signed_event()
        bundle={"schema":"reach-scout-signed-review-feedback-v1",
                "source":"DiscoveryHubPrivateExport","events":[e]}
        confirmed,hold=extract_valid_events([("bundle.json",bundle,"a"*64)],
                     self.fake_index("10.1000/other"),KEY)
        self.assertEqual(confirmed,[])
        self.assertEqual(len(hold),1)
    def test_empty_config_absence_does_not_fake_hub_decisions(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"scout-operations/reviewer-feedback-inbox").mkdir(parents=True)
            out=root/"scout-operations/research-feedback.json"
            out.write_text(json.dumps({"schema":"reach-scout-research-feedback-v1",
                     "repository":"PART-WPO/reach-scout-discoveries","signals":[]}))
            r=run(root,key="",index=self.fake_index())
            self.assertEqual(r["signals"],[])
            self.assertEqual(r["private_hub_connection_status"],"NOT_CONNECTED_OR_NOT_EXPORTED")
    def test_private_export_without_key_is_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            folder=root/"scout-operations/reviewer-feedback-inbox"
            folder.mkdir(parents=True)
            (folder/"signed.json").write_text(json.dumps({
                "schema":"reach-scout-signed-review-feedback-v1",
                "source":"DiscoveryHubPrivateExport","events":[signed_event()]}))
            with self.assertRaisesRegex(ValueError,"HMAC_KEY absent"):
                run(root,key="",index=self.fake_index())

if __name__=="__main__":unittest.main()
