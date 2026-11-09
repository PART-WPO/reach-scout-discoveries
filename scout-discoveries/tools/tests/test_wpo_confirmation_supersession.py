"""Regression: one immutable 4:24 Scout review unit receives a validated 459 correction."""
import hashlib
import sys
import unittest
from pathlib import Path

TOOLS=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(TOOLS))
from build_manifest import inspect_batch
from supersessions import get_rules, verify_wpo_award_confirmation, approved_batches, rows_for

SCOUT_ROOT=Path(__file__).resolve().parents[2]
OLD="2026-11-09-human-project-9509397cf11df96346"
NEW="2026-11-09-aies-d-23-0094-wpo459-reclassification-001"
DOI="10.1175/aies-d-23-0094.1"


class ExistingCandidate459CorrectionTests(unittest.TestCase):
    def setUp(self):
        self.old=inspect_batch(SCOUT_ROOT/"batches"/(OLD+".csv"))
        self.new=inspect_batch(SCOUT_ROOT/"batches"/(NEW+".csv"))
        self.rule=get_rules(SCOUT_ROOT)[OLD]

    def test_source_bound_wpo_459_reclassification_keeps_single_review_unit(self):
        self.assertEqual(self.old["sha256"],self.rule["original_sha256"])
        verify_wpo_award_confirmation(SCOUT_ROOT,self.old,self.new,self.rule)
        original=rows_for(SCOUT_ROOT,self.old)[0]
        corrected=rows_for(SCOUT_ROOT,self.new)[0]
        self.assertEqual(original["DOI"],corrected["DOI"])
        self.assertEqual(corrected["NOAA Award Number(s)"],"NA19OAR4590128")
        self.assertEqual(corrected["Funding Evidence URL"],
                         "https://api.crossref.org/works/"+DOI)
        self.assertEqual(corrected["Source Run ID"],original["Source Run ID"])
        self.assertEqual(corrected["Suggested Parent Project"],"")
        self.assertIn("Scout classification: NEW CANDIDATE",
                      corrected["Scout Discovery Rationale"])
        self.assertIn("Private Hub import and any prior unsynchronized review remain NOT VERIFIED.",
                      corrected["Scout Discovery Rationale"])
        all_entries=[inspect_batch(p) for p in sorted((SCOUT_ROOT/"batches").glob("*.csv"))]
        active=approved_batches(SCOUT_ROOT,all_entries)
        matching=[entry for entry in active if any(
            row.get("DOI","").lower()==DOI for row in rows_for(SCOUT_ROOT,entry))]
        self.assertEqual([x["id"] for x in matching],[NEW])

    def test_other_award_cannot_be_substituted(self):
        for suspect in ("NA20OAR4320278","NA22OAR0110123","NA22OAR4690123",
                        "NA19OAR4590999"):
            bad={**self.rule,"confirmed_wpo_award":suspect}
            with self.assertRaises(ValueError):
                verify_wpo_award_confirmation(SCOUT_ROOT,self.old,self.new,bad)

    def test_missing_corroborated_source_is_rejected(self):
        bad={**self.rule,"evidence_path":"scout-operations/private-review-history.json"}
        with self.assertRaises(ValueError):
            verify_wpo_award_confirmation(SCOUT_ROOT,self.old,self.new,bad)


if __name__=="__main__":
    unittest.main()
