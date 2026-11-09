"""Safety and decision semantics of the read-only evidence-to-action pilot."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from evidence_to_action_pilot import assess, build, verified_file

def case(disposition="PROJECT_EVIDENCE_HOLD"):
    return {"identity":"doi:10.1234/test", "latest_operational_disposition":disposition,
            "latest_evidence_path":"public-note.json",
            "observed_dispositions":[disposition]}

def detail(**kwargs):
    d={"publication_status":"NOT_CHECKED","primary_award_match":None,
       "project_attribution":"NOT_CHECKED","secondary_identity_checked":False,
       "required_metadata_verified":False,"research_rounds":1,
       "research_budget_exhausted":False,
       "checked_sources":["https://example.org/one","https://example.net/two"]}
    d.update(kwargs)
    return d

class PilotTests(unittest.TestCase):
    def out(self, c=None, d=None):
        return assess(c or case(), d if d is not None else detail(), [])

    def test_all_registry_cases_are_evaluated_and_source_notes_verified(self):
        report=build()
        self.assertGreaterEqual(report["distinct_cases_evaluated"], 34)
        self.assertEqual(report["distinct_cases_evaluated"], len(report["cases"]))
        self.assertGreaterEqual(report["research_events_source_sha_verified"], 50)
        self.assertGreaterEqual(report["unstructured_identity_cases"], 0)
        self.assertEqual(report["new_human_review_stages"], 0)
        self.assertTrue(report["read_only"])
        self.assertTrue(all(not x["automatic_hub_write"] and not x["formal_original_closed"]
                            and not x["separate_expansion_closed"] for x in report["cases"]))

    def test_preprint_never_forwarded_even_when_all_other_gates_present(self):
        d=detail(publication_status="PREPRINT", primary_award_match=True,
                 project_attribution="VERIFIED_SAME_PROJECT",
                 secondary_identity_checked=True, required_metadata_verified=True)
        self.assertEqual(self.out(d=d)["suggested_disposition"],"PREPRINT_MONTHLY_WATCH")

    def test_author_or_award_only_is_never_sufficient(self):
        d=detail(publication_status="PUBLISHED", primary_award_match=True,
                 project_attribution="UNRESOLVED",secondary_identity_checked=True,
                 required_metadata_verified=True)
        self.assertNotEqual(self.out(d=d)["suggested_disposition"],"READY_FOR_EXISTING_VALIDATED_DRAFT_PREFLIGHT")

    def test_all_required_gates_and_sources_for_human_proposal(self):
        d=detail(publication_status="PUBLISHED", primary_award_match=True,
                 project_attribution="VERIFIED_SAME_PROJECT",
                 secondary_identity_checked=True, required_metadata_verified=True)
        o=self.out(d=d)
        self.assertEqual(o["suggested_disposition"],"READY_FOR_EXISTING_VALIDATED_DRAFT_PREFLIGHT")
        self.assertFalse(o["automatic_hub_write"])

    def test_monthly_direct_primary_award_threshold_and_historical_threshold(self):
        monthly=detail(cohort="monthly_direct_api",publication_status="PUBLISHED",
                       primary_award_match=True,project_attribution="UNRESOLVED",
                       secondary_identity_checked=True,required_metadata_verified=True)
        self.assertEqual(self.out(d=monthly)["suggested_disposition"],
                         "READY_FOR_EXISTING_VALIDATED_DRAFT_PREFLIGHT")
        historical=dict(monthly,cohort="historical_crossref")
        self.assertNotEqual(self.out(d=historical)["suggested_disposition"],
                            "READY_FOR_EXISTING_VALIDATED_DRAFT_PREFLIGHT")

    def test_no_same_project_and_budget_exhaustion(self):
        d=detail(publication_status="PUBLISHED",primary_award_match=False,
                 project_attribution="VERIFIED_DIFFERENT_PROJECT",research_budget_exhausted=True)
        self.assertEqual(self.out(d=d)["suggested_disposition"],"NO_MATCHING_WPO_PROJECT_EVIDENCE")
        self.assertEqual(self.out(d=detail(research_budget_exhausted=True))["suggested_disposition"],
                         "BOUNDED_EVIDENCE_HOLD")

    def test_unstructured_case_requires_extraction_not_new_research(self):
        self.assertEqual(self.out(d={})["suggested_disposition"],"STRUCTURED_EVIDENCE_NEEDED")

    def test_human_question_needs_source_evidence(self):
        self.assertEqual(self.out(c=case("BOUNDED_PROJECT_QUESTION_FOR_HUMAN"),
                                  d=detail())["suggested_disposition"],
                         "ONE_BOUNDED_HUMAN_QUESTION")

    def test_existing_identity_does_not_close_expansion(self):
        o=self.out(c=case("EXISTING_IN_REACH"))
        self.assertEqual(o["suggested_disposition"],"EXISTING_REACH_KEEP_EXPANSION")
        self.assertFalse(o["separate_expansion_closed"])

    def test_source_sha_mismatch_fails_closed(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as t:
            p=Path(t)/"note.json";p.write_text('{"hello":1}')
            with self.assertRaisesRegex(ValueError,"SHA mismatch"):
                verified_file(Path(t),"note.json","0"*64)
            with self.assertRaisesRegex(ValueError,"unsafe"):
                verified_file(Path(t),"../other-file","0"*64)

if __name__=="__main__":
    unittest.main()
