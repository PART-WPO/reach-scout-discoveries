import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from build_reconciliation_repair_worklist import make

class RepairWorklistTests(unittest.TestCase):
    def test_current_source_exceptions_all_preserved_without_terminal_mutation(self):
        report=make()
        self.assertEqual(report["unverified_terminal_cases"],len(report["cases"]))
        self.assertEqual(len({e["identity"] for e in report["cases"]}),len(report["cases"]))
        self.assertTrue(all(e["ready_to_auto_close"] is False
                            and e["original_terminal_status_changed"] is False
                            and e["human_decision_changed"] is False
                            and e["private_hub_outcome"]=="NOT_VERIFIED"
                            for e in report["cases"]))
        self.assertEqual(sum(report["repair_priority_counts"].values()),len(report["cases"]))
    def test_retired_datacite_doi_never_reinstated_as_active(self):
        report=make()
        row=next(x for x in report["cases"] if x["identity"]=="doi:10.17603/ds2-xjyf-nc93")
        self.assertEqual(row["priority"],"RETIRED_PUBLIC_PROPOSAL_VERIFY_PRIVATE_REVIEW_HISTORY")
        self.assertTrue(row["public_batch_exclusion_history"])
        self.assertIn("Do NOT reinstate",row["repair_instruction"])
    def test_reconciliation_does_not_claim_validated_terminal_evidence(self):
        report=make()
        self.assertTrue(all(e["evidence_verified_and_terminal_reconciled"] is False
                             for e in report["cases"]))
        self.assertEqual(len([e for e in report["cases"] if e["cohort"]=="historical_datacite"]),2)
        self.assertEqual(len([e for e in report["cases"] if e["cohort"]=="historical_crossref"]),10)

if __name__=="__main__":
    unittest.main()
