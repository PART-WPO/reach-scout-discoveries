import json
import sys
import tempfile
import unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from recover_queued_doi_metadata import queue,run,need_attempt

class QueuedDOIMetadataTests(unittest.TestCase):
    def test_live_failure_sources_covered_and_source_evidence_verified(self):
        q=queue()
        d={x["doi"]:x for x in q["queue"]}
        for target in ("10.21957/befj-es73","10.21957/e8rz-wh72",
                       "10.5281/zenodo.4433147","10.5281/zenodo.5057616"):
            self.assertIn(target,d)
            self.assertTrue(d[target]["source_notes"])
            self.assertFalse(d[target]["candidate_staged"])
        self.assertEqual(q["doi_queue_size"],len(d))
    def test_bounded_api_retry_and_no_auto_review(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            docpath="scout-operations/monthly-research/2026-11-06-demo.json"
            p=root/docpath;p.parent.mkdir(parents=True)
            doc={"cases":[{"doi":"10.1000/unknown","datacite_exact_metadata":"ACCESS_FAILED_NOT_MISSING"}]}
            p.write_text(json.dumps(doc))
            import hashlib
            b=p.read_bytes()
            reg={"schema":"reach-scout-all-lane-research-outcomes-v1",
                 "evidence_files_scanned":1,
                 "source_sha256":{docpath:hashlib.sha256(b).hexdigest()}}
            q=root/"scout-operations/research-outcome-registry.json"
            q.write_text(json.dumps(reg))
            used=[]
            def fake(d):
                used.append(d)
                return {"status":"ok","evidence":"https://api.datacite.org/dois/"+d,
                        "title":"Official recovered metadata","pub_date":"2026-11-01"}
            fn=lambda d,title:{"status":"NO_PUBLIC_IDENTITY_MATCH"}
            now=datetime(2026,11,6,tzinfo=timezone.utc)
            first=run(root,lookup=fake,identity=fn,now=now)
            self.assertEqual(first["lookups_attempted"],1)
            self.assertEqual(first["metadata_recovered"],1)
            self.assertFalse(first["records"][0]["public_candidate_staged"])
            (root/"scout-operations/reports/queued-doi-metadata").mkdir(parents=True)
            (root/"scout-operations/reports/queued-doi-metadata/latest.json").write_text(json.dumps(first))
            second=run(root,lookup=fake,identity=fn,now=now+timedelta(hours=1))
            self.assertEqual(second["lookups_attempted"],0)
            self.assertEqual(len(used),1)
            self.assertEqual(second["records"][0]["recovery_status"],"CACHED_PREVIOUS_SUCCESS")
            p.write_text(json.dumps({"cases":[{"doi":"10.1000/unknown","datacite_exact_metadata":"TAMPERED"}]}))
            with self.assertRaisesRegex(ValueError,"changed since"):queue(root)
    def test_failure_is_retryable_not_missing_metadata(self):
        now=datetime(2026,11,6,tzinfo=timezone.utc)
        old={"looked_up_at":now.isoformat(),"metadata":{"status":"unavailable_or_not_found"}}
        self.assertFalse(need_attempt(old,now+timedelta(hours=6)))
        self.assertTrue(need_attempt(old,now+timedelta(hours=25)))

if __name__=="__main__":unittest.main()
