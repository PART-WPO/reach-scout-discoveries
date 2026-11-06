"""Offline issue #35 invariants: source freshness, chronology, privacy, safety."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"tools"))
from reconcile_derived_reporting import (
    INDEX, ROLLUP, UNIFIED, SCORECARD, IMPACT, FEEDBACK, MANIFEST, STEPS,
    TRIAGE, snapshot_protected, verify,
)

class DerivedReportingTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.source="f"*64
        batches=[{"record_count":54}]+[{"record_count":1} for _ in range(30)]
        self.write(MANIFEST,{"schema":"reach-scout-discovery-feed-v1",
                             "batch_count":31,"candidate_rows":84,"batches":batches})
        self.write(INDEX,{"sources":{"scout_manifest_sha256":self.sha(MANIFEST),"scout_batches":31},
                          "source_fingerprint":self.source,
                          "records":[{"source":"SCOUT_PUBLISHED"} for _ in range(84)]})
        self.write(ROLLUP,{"identity_index_fingerprint":self.source,"automatically_staged":0,
                           "original_terminal_statuses_modified":0,"expansion_seed_closures":0})
        self.write(UNIFIED,{"identity_index_fingerprint":self.source,
                            "identity_index_source_sha256":self.read(INDEX)["sources"],
                            "changes_to_human_dispositions":0,
                            "new_public_review_proposals":0,"new_reach_additions":0})
        self.write(SCORECARD,{"source_sha256":{
            "shared_identity_index":self.sha(INDEX),
            "scout_published_manifest":self.sha(MANIFEST)},
            "review_pipeline":{"public_scout_batches":31,"public_scout_staged_proposals":84,
                               "private_discovery_hub_imports":"NOT_VERIFIED"}})
        self.write(IMPACT,{"source_sha256":{"scorecard":self.sha(SCORECARD),
                                            "unified":self.sha(UNIFIED)},
                           "pipeline":{"public_scout_staged_proposal_rows":84,
                                       "private_hub_imports":"NOT_VERIFIED",
                                       "verified_new_public_reach_additions_from_scout":"NOT_VERIFIED"}})
        self.write(FEEDBACK,{"signals":[],"events_held_for_manual_identity_reconciliation":[],
                             "private_hub_connection_status":"NOT_CONNECTED_OR_NOT_EXPORTED",
                             "source_identity_fingerprint":self.source})
    def write(self,p,obj):
        dest=self.root/p
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(json.dumps(obj),encoding="utf-8")
    def read(self,p):
        return json.loads((self.root/p).read_text(encoding="utf-8"))
    def sha(self,p):
        return hashlib.sha256((self.root/p).read_bytes()).hexdigest()
    def mutate(self,p,fn):
        x=self.read(p)
        fn(x)
        self.write(p,x)
        # Derived artifacts are intentionally not automatically resynchronized.
    def test_complete_sha_aligned_31_batch_84_row_report(self):
        r=verify(self.root)
        self.assertEqual((r["scout_batches"],r["published_scout_candidates"]),(31,84))
        self.assertEqual(r["protected_reviewer_events"],0)
    def test_stale_30_batch_index_is_rejected(self):
        self.mutate(INDEX,lambda x:x["sources"].update(scout_batches=30))
        with self.assertRaisesRegex(ValueError,"identity cache is stale"):
            verify(self.root)
    def test_research_rollup_divergence_is_rejected(self):
        self.mutate(ROLLUP,lambda x:x.update(identity_index_fingerprint="old"))
        with self.assertRaisesRegex(ValueError,"different identity index"):
            verify(self.root)
    def test_scorecard_stale_counts_are_rejected(self):
        self.mutate(SCORECARD,lambda x:x["review_pipeline"].update(public_scout_batches=30))
        with self.assertRaisesRegex(ValueError,"stale Scout counts"):
            verify(self.root)
    def test_public_feedback_cannot_expose_review_outcome(self):
        self.mutate(FEEDBACK,lambda x:x["signals"].append({"decision_code":"REJECTED"}))
        with self.assertRaisesRegex(ValueError,"Privacy hold"):
            verify(self.root)
    def test_private_hub_approval_cannot_be_inferred(self):
        self.mutate(IMPACT,lambda x:x["pipeline"].update(private_hub_imports="VERIFIED"))
        with self.assertRaisesRegex(ValueError,"infer private Hub import"):
            verify(self.root)
    def test_unexpected_staging_fails_closed(self):
        self.mutate(ROLLUP,lambda x:x.update(automatically_staged=1))
        with self.assertRaisesRegex(ValueError,"publication boundary"):
            verify(self.root)
    def test_protected_historical_identity_duplicates_rejected(self):
        for p in TRIAGE:
            self.write(p,{"entries":[{"identity":"doi:10.1000/test","status":"awaiting_research"},
                                      {"identity":"doi:10.1000/test","status":"already_in_reach"}]})
        with self.assertRaisesRegex(ValueError,"Duplicate historical identity"):
            snapshot_protected(self.root)
    def test_rebuild_order_is_safe(self):
        self.assertLess(STEPS.index("decision_pipeline.py build-index"),
                        STEPS.index("decision_pipeline.py evaluate --cases scout-operations/research-decision-cases.json"))
        self.assertLess(STEPS.index("summarize_research_decisions.py"),
                        STEPS.index("build_operational_scorecard.py"))
        self.assertLess(STEPS.index("unified_source_preflight.py"),
                        STEPS.index("build_operational_scorecard.py"))
        self.assertLess(STEPS.index("validate_reviewer_feedback.py"),
                        STEPS.index("build_impact_report.py"))
        self.assertLess(STEPS.index("build_operational_scorecard.py"),
                        STEPS.index("build_impact_report.py"))

if __name__=="__main__":
    unittest.main()
