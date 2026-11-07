import importlib.util, unittest
from pathlib import Path
p=Path(__file__).resolve().parents[1]/"tools/reconcile_preprint_retirements.py"
spec=importlib.util.spec_from_file_location("retire",p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class RetireTests(unittest.TestCase):
 def test_family_and_tombstones(self):
  w={"entries":[{"preprint_doi":"10.1234/one.1"},{"preprint_doi":"10.1234/one.2"},{"preprint_doi":"10.1234/other"}]}
  lead={"published_doi":"10.5678/final","preprint_doi":"10.1234/one.1","preprint_dois":["10.1234/one.1","10.1234/one.2"],"status":"already_in_reach","confirmed_reach_duplicate":{"reach_ids":["reach-1"],"basis":"Exact DOI plus title","source":"official IR"}}
  archive={"schema":"reach-scout-preprint-retirement-archive-v1","entries":[]}
  self.assertEqual(m.reconcile(w,{"entries":[lead]},archive),2)
  self.assertEqual(len(w["entries"]),1)
  self.assertEqual(len(archive["entries"]),2)
  self.assertEqual(m.reconcile(w,{"entries":[lead]},archive),0)
 def test_ambiguous_not_retired(self):
  w={"entries":[{"preprint_doi":"10.1234/one.1"}]}
  lead={"published_doi":"10.5678/final","preprint_doi":"10.1234/one.1","status":"already_in_reach"}
  archive={"schema":"reach-scout-preprint-retirement-archive-v1","entries":[]}
  self.assertEqual(m.reconcile(w,{"entries":[lead]},archive),0)
 def test_conflicting_family_rejected(self):
  w={"entries":[]};archive={"schema":"reach-scout-preprint-retirement-archive-v1","entries":[{"preprint_doi":"10.1234/a","published_doi":"10.5678/a"}]}
  lead={"published_doi":"10.5678/b","preprint_doi":"10.1234/a","status":"already_in_reach","confirmed_reach_duplicate":{"reach_ids":["r"],"basis":"exact","source":"IR"}}
  with self.assertRaises(ValueError):m.reconcile(w,{"entries":[lead]},archive)
if __name__=="__main__":unittest.main()
