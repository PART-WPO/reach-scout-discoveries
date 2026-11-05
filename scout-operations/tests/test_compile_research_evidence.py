"""Multi-case Scout overnight evidence must retain each original DOI independently."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from compile_research_evidence import build


class ResearchEvidenceIngestTests(unittest.TestCase):
    def test_multi_case_does_not_transfer_funding_and_uses_distinct_source_rounds(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            out=root/"scout-operations/historical-crossref-phase2"
            out.mkdir(parents=True)
            (out/"2026-11-05-0100ET-two-case.json").write_text(json.dumps({
                "cases":[
                    {"doi":"10.1000/alpha", "sources":[{"url":"https://example.org/alpha"}],
                     "funding":{"primary_spark_award_match":"VERIFIED",
                                "same_project_wpo_attribution":"CORROBORATED_BUT_NOT_CONCLUSIVE"}},
                    {"doi":"10.1000/beta", "sources":[{"url":"https://example.org/beta"}],
                     "decision":"BOUNDED_HOLD_PROJECT_ATTRIBUTION_NOT_ESTABLISHED"}
                ]}))
            (out/"2026-11-05-0200ET-first-followup.json").write_text(json.dumps({
                "original_doi":"10.1000/alpha",
                "sources":[{"url":"https://example.org/alpha"}],
                "decision":"RESEARCH_EVIDENCE_ONLY_HOLD"
            }))
            (out/"2026-11-05-0300ET-second-followup.json").write_text(json.dumps({
                "original_doi":"10.1000/alpha",
                "sources":[{"url":"https://example.org/independent"}],
                "decision":"RESEARCH_EVIDENCE_ONLY_HOLD"
            }))
            cases={"doi:10.1000/alpha":{"titles":{"Alpha Publication"}},
                   "doi:10.1000/beta":{"titles":{"Beta Publication"}}}
            with patch("reconcile_historical_crossref.cases",
                       return_value=({},cases)):
                data, report=build(root)
            self.assertEqual(report["doi_case_count"],2)
            self.assertEqual(report["source_unlinked_files"],[])
            by={r["doi"]:r for r in data["cases"]}
            self.assertEqual(by["10.1000/alpha"]["research_rounds"],2)
            self.assertEqual(by["10.1000/beta"]["research_rounds"],1)
            self.assertEqual(by["10.1000/alpha"]["project_attribution"],"UNRESOLVED")
            self.assertIsNone(by["10.1000/beta"]["primary_award_match"])
            self.assertFalse(by["10.1000/alpha"]["required_metadata_verified"])
            self.assertEqual(by["10.1000/beta"]["private_review_status"],"NOT_VERIFIED")
            self.assertEqual(len(by["10.1000/alpha"]["source_evidence"]),3)
            self.assertEqual(len(by["10.1000/beta"]["source_evidence"]),1)


if __name__=="__main__":
    unittest.main()
