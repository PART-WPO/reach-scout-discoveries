import importlib.util,json,tempfile,unittest
from datetime import datetime,timezone
from pathlib import Path
p=Path(__file__).resolve().parents[1]/"tools/build_mission_activity_log.py"
spec=importlib.util.spec_from_file_location("activity",p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class ActivityTests(unittest.TestCase):
 def test_idempotent_baseline_and_delta(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)
   for f in [m.SCORE,m.REG,m.LOG]:(root/f).parent.mkdir(parents=True,exist_ok=True)
   reg={"research_note_events":2,"distinct_research_identities":1}
   raw=json.dumps(reg).encode();(root/m.REG).write_bytes(raw)
   import hashlib
   score={"source_sha256":{m.REG:hashlib.sha256(raw).hexdigest()},
    "verified_original_research":{"crossref_completed":48,"datacite_completed":186},
    "separate_related_output_expansion":{"crossref_verified_completed":0},
    "public_candidate_pipeline":{"public_feed_rows":84},
    "preprint_workload":{"archived_versions":20}}
   (root/m.SCORE).write_text(json.dumps(score))
   first=m.build(root,datetime(2026,11,6,tzinfo=timezone.utc))
   self.assertEqual(first["observation_count"],1)
   self.assertIsNone(first["events"][0]["delta_since_previous_observation"])
   self.assertEqual(m.build(root)["observation_count"],1)
   score["verified_original_research"]["crossref_completed"]=49
   (root/m.SCORE).write_text(json.dumps(score))
   second=m.build(root)
   self.assertEqual(second["observation_count"],2)
   self.assertEqual(second["events"][-1]["delta_since_previous_observation"]["crossref_verified_completed"],1)
 def test_rejects_stale_registry(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)
   for f in [m.SCORE,m.REG]:(root/f).parent.mkdir(parents=True,exist_ok=True)
   (root/m.REG).write_text("{}");(root/m.SCORE).write_text('{"source_sha256":{"'+m.REG+'":"stale"}}')
   with self.assertRaises(ValueError):m.build(root)
if __name__=="__main__":unittest.main()
