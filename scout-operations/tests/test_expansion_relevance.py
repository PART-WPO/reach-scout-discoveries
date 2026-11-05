"""Scout 2.0 project relevance is a reversible research priority, never an approval."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from build_expansion_relevance import (
    ACTIVE, SOFT_DEFER, SCOPE_CHECK, audited_soft_holds,
    classify_seed, classify_related_lead, validated_reconsiderations,
    BIOMEDICAL_AUDIT, BIOMEDICAL_SOURCES, RECONSIDERATIONS,
)


class ScopeGateTests(unittest.TestCase):
    def test_verified_reach_catalog_output_prioritized(self):
        case = {"doi": "10.1000/wpo", "outcome":"CONFIRMED_IN_REACH",
                "bulk_identity_gate":{
                    "status":"VERIFIED_EXISTING_REACH",
                    "verified_reach_uid":"reachuid-v1-test",
                    "verified_record_id":"reach-001", "verified_detail_path":"agent-data/details/part-001.csv"}}
        result = classify_seed(case,{})
        self.assertEqual(result["priority"],ACTIVE)
        self.assertEqual(result["evidence_reach_uid"],"reachuid-v1-test")

    def test_unverified_identification_never_treated_as_relevance_proof(self):
        with self.assertRaisesRegex(ValueError, "Unverified REACH identity"):
            classify_seed({"doi":"10.1000/wpo", "outcome":"LIKELY_IN_REACH",
                "bulk_identity_gate":{"status":"VERIFIED_EXISTING_REACH",
                    "verified_reach_uid":"fake-uid", "verified_record_id":"reach-001",
                    "verified_detail_path":"details/file.csv"}},{})

    def test_title_only_and_index_negative_must_first_verify_project(self):
        for status in ("NEEDS_IDENTITY_REVIEW","NO_PUBLIC_REACH_MATCH"):
            with self.subTest(status=status):
                result=classify_seed({"doi":"10.1000/unknown","bulk_identity_gate":{"status":status}}, {})
                self.assertEqual(result["priority"],SCOPE_CHECK)

    def test_uncertain_biomedical_attribution_soft_defers_not_excludes(self):
        holds={"10.1000/unknown":{"note":"Original award unverified",
            "audit_files":[{"path":"evidence.json","sha256":"a"*64}],
            "reopen_trigger":"New primary award bridge","evidence_urls":["https://example.org/1","https://example.org/2"]}}
        result=classify_seed({"doi":"10.1000/unknown","bulk_identity_gate":{"status":"NO_PUBLIC_REACH_MATCH"}},holds)
        self.assertEqual(result["priority"], SOFT_DEFER)
        self.assertIn("New primary",result["reopen_trigger"])

    def test_project_evidence_can_reopen_to_scope_check_not_autoapprove(self):
        holds={"10.1000/unknown":{"note":"Previously held","audit_files":[],"evidence_urls":[],"reopen_trigger":"new evidence"}}
        renewed={"10.1000/unknown":{"reason":"New source evidence requires a new project check",
                  "evidence_urls":["https://example.org/a","https://example.org/b"],
                  "supporting_files":[]}}
        result=classify_seed({"doi":"10.1000/unknown","bulk_identity_gate":{"status":"NO_PUBLIC_REACH_MATCH"}},holds,renewed)
        self.assertEqual(result["priority"],SCOPE_CHECK)
        self.assertIsNone(result["evidence_reach_uid"])

    def test_existing_reviewers_and_original_leads_not_reopened_or_removed(self):
        prior=[
            ({"identity":"doi:10.1000/yes","status":"staged_for_human_review"}, "PRESERVE_CURRENT_HUMAN_HANDOFF"),
            ({"identity":"doi:10.1000/old","status":"already_in_reach"}, "EXISTING_REACH_LEAD_RECORDED"),
            ({"identity":"doi:10.1000/no","status":"FOLLOWUP_CLOSED_NO_DEMONSTRATED_WPO_PROJECT_BRIDGE"}, SOFT_DEFER),
            ({"identity":"doi:10.1000/maybe","status":"awaiting_independent_verification"}, SCOPE_CHECK),
        ]
        for entry,expected in prior:
            with self.subTest(expected=expected):
                before=json.dumps(entry,sort_keys=True)
                result=classify_related_lead(entry)
                self.assertEqual(result["priority"],expected)
                self.assertFalse(result["review_feed_modified"])
                self.assertFalse(result["human_decision_changed"])
                self.assertEqual(json.dumps(entry,sort_keys=True),before)

    def test_independent_structured_audits_need_real_sources_and_unknown_award(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            a=root/BIOMEDICAL_AUDIT
            b=root/BIOMEDICAL_SOURCES
            a.parent.mkdir(parents=True)
            a.write_text(json.dumps({"schema":"reach-scout-append-only-research-evidence-v1",
                "lane":"historical_original_source_provenance_audit",
                "source_manifest":"api-discoveries/historical-crossref/manifest.json",
                "cases":[{"doi":"10.1000/hold","original_award_column":"UNK",
                    "disposition":"BOUNDED_HOLD_SOURCE_AWARD_UNVERIFIED"}]}))
            b.write_text(json.dumps({"schema":"reach-scout-append-only-research-evidence-v1",
                "lane":"historical_original_funding_attribution",
                "cases":[{"doi":"10.1000/hold",
                    "decision":"BOUNDED_HOLD_PROJECT_ATTRIBUTION_NOT_ESTABLISHED",
                    "uncertainty":"Not proven unrelated; exact source award unverified",
                    "sources":[{"url":"https://publisher.example.org/article"},
                        {"url":"https://institution.example.org/research"}]}]}))
            holds,hashes=audited_soft_holds(root)
            self.assertIn("10.1000/hold",holds)
            self.assertEqual(len(holds["10.1000/hold"]["evidence_urls"]),2)
            self.assertEqual(len(hashes),2)
            # A vague single-source or explicitly matched award must not defer.
            d=json.loads(b.read_text())
            d["cases"][0]["sources"]=d["cases"][0]["sources"][:1]
            b.write_text(json.dumps(d))
            self.assertFalse(audited_soft_holds(root)[0])
            d=json.loads(a.read_text())
            d["cases"][0]["original_award_column"]="NA21OAR4590000"
            a.write_text(json.dumps(d))
            self.assertFalse(audited_soft_holds(root)[0])

    def test_reconsideration_requires_sha_backed_new_project_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            evidence=root/"scout-operations/historical-crossref-phase2/new-proof.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text('{"evidence":"New source"}')
            path=root/RECONSIDERATIONS
            record={"doi":"10.1000/hold","decision":"REOPEN_PROJECT_SCOPE_CHECK",
                "specific_new_evidence":"An official project deliverable and a primary WPO award linkage require another targeted scope check.",
                "evidence_urls":["https://example.org/1","https://example.org/2"],
                "supporting_files":[{"path":evidence.relative_to(root).as_posix(),
                                    "sha256":hashlib.sha256(evidence.read_bytes()).hexdigest()}]}
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(json.dumps({"schema":"reach-scout-expansion-scope-reconsiderations-v1","entries":[record]}))
            result,_=validated_reconsiderations(root,{"10.1000/hold"})
            self.assertIn("10.1000/hold",result)
            record["supporting_files"][0]["sha256"]="0"*64
            path.write_text(json.dumps({"schema":"reach-scout-expansion-scope-reconsiderations-v1","entries":[record]}))
            with self.assertRaisesRegex(ValueError,"SHA mismatch"):
                validated_reconsiderations(root,{"10.1000/hold"})


if __name__ == "__main__":
    unittest.main()
