"""Evidence-to-action pilot: deterministic, safe, source-pinned, bounded."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from evaluate_research_to_action import (
    build, evidence_assessment, compile_decision, independent_critique, SCHEMA,
)


class EvidenceActionPilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = build()
        cls.by_identity = {x["identity"]: x for x in cls.report["cases"]}

    def test_preserves_every_current_public_research_identity_and_event(self):
        r = self.report
        self.assertEqual(r["schema"], SCHEMA)
        self.assertGreaterEqual(r["unique_research_identities"], 34)
        self.assertGreaterEqual(r["source_research_note_events"], 52)
        self.assertEqual(len(r["cases"]), r["unique_research_identities"])
        self.assertEqual(len(self.by_identity), len(r["cases"]))
        self.assertEqual(sum(r["recommended_disposition_counts"].values()),
                         r["unique_research_identities"])
        self.assertEqual(sum(x["evaluation"]["note_event_count"] for x in r["cases"]),
                         r["source_research_note_events"])
        self.assertTrue(r["source_case_dispositions_unchanged"])

    def test_no_approval_or_hidden_private_hub_inference(self):
        r = self.report
        self.assertEqual(r["research_ready_review_proposals_automatically_created"], 0)
        self.assertEqual(r["published_reach_additions"], 0)
        self.assertEqual(r["formal_original_or_expansion_closures"], 0)
        self.assertEqual(r["private_hub_imports"], "NOT_VERIFIED")
        self.assertFalse(r["source_author_pi_collaborator_names_copied"])
        for x in r["cases"]:
            self.assertTrue(x["read_only"])
            self.assertTrue(x["existing_reviewer_status_unchanged"])
            self.assertTrue(x["independent_critique"]["adversarial_gate_checks_passed"])
            d = x["compiled_decision"]
            for field in ("formal_original_completed", "separate_expansion_completed",
                          "public_proposal_created", "private_hub_write", "human_reviewer_approval"):
                self.assertFalse(d[field])
            self.assertTrue(d["next_action"] and d["reopen_or_finish_trigger"] and d["owner"])
            self.assertEqual(x["evaluation"]["gates"]["related_output_scope"] in (
                "RELATED_OUTPUT_INDEPENDENT_VERIFICATION_REQUIRED",
                "SEED_ORIGINAL_EXPANSION_REMAINS_SEPARATE"), True)

    def test_known_preprints_cannot_be_staged(self):
        key = "doi:10.1002/essoar.10504829.1"
        self.assertIn(key, self.by_identity)
        c = self.by_identity[key]
        self.assertEqual(c["compiled_decision"]["recommended_disposition"],
                         "PREPRINT_MONTHLY_WATCH")
        self.assertFalse(c["compiled_decision"]["public_proposal_created"])
        self.assertTrue(c["evaluation"]["preprint"])
        self.assertIn("monthly", c["compiled_decision"]["next_action"].lower())

    def test_related_dataset_with_ci_funding_clue_never_ready_by_inference(self):
        key = "doi:10.5281/zenodo.4433147"
        self.assertIn(key, self.by_identity)
        c = self.by_identity[key]
        self.assertFalse(c["evaluation"]["primary_project_supported_by_prior_evidence"])
        self.assertNotEqual(c["compiled_decision"]["recommended_disposition"],
                            "REVIEW_PREFLIGHT_CANDIDATE_NO_AUTO_STAGING")
        self.assertEqual(c["evaluation"]["gates"]["related_output_scope"],
                         "RELATED_OUTPUT_INDEPENDENT_VERIFICATION_REQUIRED")
        self.assertFalse(c["compiled_decision"]["separate_expansion_completed"])

    def test_human_project_question_is_bounded_and_has_sources(self):
        referrals = [x for x in self.report["cases"]
                     if x["compiled_decision"]["recommended_disposition"] ==
                        "BOUNDED_HUMAN_PROJECT_QUESTION"]
        self.assertLessEqual(len(referrals), 2)
        self.assertGreaterEqual(len(referrals), 1)
        for c in referrals:
            self.assertGreaterEqual(c["evaluation"]["source_url_count"], 2)
            self.assertTrue(c["evaluation"]["bounded_human_referral_evidence"])
            self.assertIn("primary WPO SPARK project", c["compiled_decision"]["next_action"])
            self.assertFalse(c["compiled_decision"]["human_reviewer_approval"])

    def test_precise_technical_access_recovery_not_negative_evidence(self):
        key = "doi:10.1175/waf-d-22-0056.1"
        c = self.by_identity[key]
        self.assertTrue(c["evaluation"]["technical_hold"])
        self.assertEqual(c["compiled_decision"]["recommended_disposition"],
                         "DOI_METADATA_RECOVERY_ONLY")
        self.assertEqual(c["compiled_decision"]["owner"], "EXACT_DOI_METADATA_RECOVERY")
        self.assertNotIn("NOT_RELATED", c["compiled_decision"]["recommended_disposition"])

    def test_non_doi_code_case_stays_held_if_award_conflicts(self):
        key = "url:https://github.com/coreypotvin/wofs_fcst_skill"
        self.assertIn(key, self.by_identity)
        c = self.by_identity[key]
        self.assertEqual(c["output_kind"], "PUBLIC_CODE_OR_URL")
        self.assertFalse(c["compiled_decision"]["public_proposal_created"])
        self.assertNotEqual(c["compiled_decision"]["recommended_disposition"],
                            "REVIEW_PREFLIGHT_CANDIDATE_NO_AUTO_STAGING")

    def test_source_provenance_fingerprints_and_deterministic_replay(self):
        a = self.report
        b = build()
        self.assertEqual(a, b)
        self.assertEqual(a["source_fingerprint"], b["source_fingerprint"])
        for c in a["cases"]:
            self.assertEqual(c["evaluation"]["note_event_count"],
                             len(c["evaluation"]["source_note_sha256"]))
            for p in c["evaluation"]["source_note_sha256"]:
                self.assertEqual(len(p["sha256"]), 64)

    def test_adversarial_critique_blocks_unsafe_review_promotion(self):
        example = self.by_identity["doi:10.1002/qj.5049"]["evaluation"]
        forced = compile_decision(example)
        forced["recommended_disposition"] = "REVIEW_PREFLIGHT_CANDIDATE_NO_AUTO_STAGING"
        critique = independent_critique(example, forced)
        self.assertFalse(critique["adversarial_gate_checks_passed"])
        self.assertIn("REVIEW_PREFLIGHT_WITH_FAILED_MANDATORY_GATE",
                      critique["blocking_safety_issues"])

    def test_single_targeted_research_gate_not_generic_loop(self):
        example = {
            "doi": "10.1000/synthetic", "preprint": False,
            "verified_public_reach": False, "publicly_staged": False,
            "public_no_action": False, "contradictory_project_evidence": False,
            "bounded_human_referral_evidence": False, "source_url_count": 0,
            "technical_hold": False, "prior_research_budget_exhausted": False,
            "prior_dispositions": [], "ambiguous_identity": True,
            "primary_project_supported_by_prior_evidence": False,
            "prior_secondary_identity_checked": False,
            "gates": {"publication":"OFFICIAL_RELEASE_NOT_VERIFIED",
                      "required_metadata":"INCOMPLETE_OR_NOT_VERIFIED"},
        }
        d = compile_decision(example)
        self.assertEqual(d["recommended_disposition"],
                         "TARGETED_IDENTITY_VERSION_CHECK")
        self.assertIn("canonical version", d["next_action"])


if __name__ == "__main__":
    unittest.main()
