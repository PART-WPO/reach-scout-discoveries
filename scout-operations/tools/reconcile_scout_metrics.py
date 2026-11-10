#!/usr/bin/env python3
"""Rebuild and verify all public Scout discovery/throughput/impact measurements.

Use after the final SHA-verified manifest publication and after bounded GitHub
expansion notes. This job NEVER creates a candidate or mutates private systems.
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_STEPS = [
    "scout-discoveries/tools/rebuild_discovery_rollup.py",
    "scout-operations/tools/build_operational_scorecard.py",
    "scout-operations/tools/build_throughput_scorecard.py",
    "scout-operations/tools/build_impact_report.py",
    "scout-operations/tools/summarize_hourly_missions.py",
]
OUTPUTS = [
    "scout-operations/discovery-origin-rollup.json",
    "scout-operations/scout-operational-scorecard.json",
    "scout-operations/scout-throughput-scorecard.json",
    "scout-operations/scout-v2-impact-report.json",
    "scout-operations/reports/hourly-mission-scorecard/latest.json",
]


def load(root, path):
    return json.loads((root / path).read_text(encoding="utf-8"))


def sha(root, path):
    return hashlib.sha256((root / path).read_bytes()).hexdigest()


def verify(root=ROOT):
    manifest_path = "scout-discoveries/manifest.json"
    feed = load(root, manifest_path)
    origin = load(root, OUTPUTS[0])
    operational = load(root, OUTPUTS[1])
    throughput = load(root, OUTPUTS[2])
    impact = load(root, OUTPUTS[3])
    mission = load(root, OUTPUTS[4])

    if feed.get("schema") != "reach-scout-discovery-feed-v1":
        raise ValueError("Unexpected active public Scout manifest")
    if len(feed.get("batches", [])) != feed["batch_count"] or sum(
        x.get("record_count", 0) for x in feed["batches"]) != feed["candidate_rows"]:
        raise ValueError("Public Scout manifest totals are internally inconsistent")
    if origin.get("source_manifest_sha256") != sha(root, manifest_path):
        raise ValueError("STALE_DISCOVERY_ORIGIN_ROLLUP")
    if origin.get("source_manifest_generated_at") != feed.get("generated_at"):
        raise ValueError("Attribution rollup is not for current public manifest")
    if (origin.get("staged_review_rows") != feed["candidate_rows"]
        or origin.get("batch_count") != feed["batch_count"]):
        raise ValueError("Attribution totals disagree with active manifest")
    if sum(origin["effective_discovery_method_counts"].values()) != feed["candidate_rows"]:
        raise ValueError("Discovery-method counts do not reconcile")
    if sum(origin["effective_finding_purpose_counts"].values()) != feed["candidate_rows"]:
        raise ValueError("Reviewer finding-purpose counts do not reconcile")
    if (operational["review_pipeline"]["public_scout_staged_proposals"] != feed["candidate_rows"]
        or operational["review_pipeline"]["public_scout_batches"] != feed["batch_count"]):
        raise ValueError("STALE_OPERATIONAL_SCORECARD_PUBLIC_FEED")
    if (throughput["public_candidate_pipeline"]["public_feed_rows"] != feed["candidate_rows"]
        or throughput["public_candidate_pipeline"]["public_feed_batches"] != feed["batch_count"]
        or throughput["source_sha256"][manifest_path] != sha(root, manifest_path)):
        raise ValueError("STALE_THROUGHPUT_SCORECARD_PUBLIC_FEED")
    if impact["pipeline"]["public_scout_staged_proposal_rows"] != feed["candidate_rows"]:
        raise ValueError("STALE_IMPACT_REPORT_PUBLIC_FEED")
    if mission["schema"] != "reach-scout-separated-completed-mission-scorecard-v1":
        raise ValueError("Unexpected mission metrics schema")
    expansion = mission["github_bounded_expansion_research"]
    if expansion["new_distinct_source_backed_doi_leads"] != len(expansion["distinct_source_backed_doi_leads"]):
        raise ValueError("Non-distinct discovery leads")
    if expansion["distinct_verified_reach_seeds_investigated"] != len(expansion["distinct_seed_dois"]):
        raise ValueError("Non-distinct expansion seeds")
    for path, expected in expansion["source_report_sha256"].items():
        if not path.startswith("scout-operations/reports/bounded-expansion-research/"):
            raise ValueError("Untrusted expansion research path")
        if sha(root, path) != expected:
            raise ValueError("Expansion research report SHA mismatch: " + path)
    for path in OUTPUTS:
        if not (root / path).is_file():
            raise ValueError("Missing refreshed public report " + path)
    return {
        "schema": "reach-scout-discovery-metrics-reconciliation-v1",
        "public_manifest_sha256": sha(root, manifest_path),
        "public_batch_count": feed["batch_count"],
        "public_review_rows": feed["candidate_rows"],
        "effective_discovery_method_counts": origin["effective_discovery_method_counts"],
        "verified_crossref_origin_corrections":
            origin["historical_crossref_method_reconciliation"]["verified_explicit_independent_to_direct_corrections"],
        "github_completed_guarded_missions":
            mission["by_producer"]["github_guarded_crossref_backstop"]["completed_original_decision_missions"],
        "chatgpt_hourly_report_coverage":
            mission["by_producer"]["chatgpt_hourly_mission"]["verified_report_count"],
        "source_driven_distinct_research_leads": expansion["new_distinct_source_backed_doi_leads"],
        "completed_expansion_decisions": expansion["completed_distinct_expansion_decisions"],
        "private_hub_imports": "NOT_VERIFIED",
    }


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--check", action="store_true", help="Read only: verify previously generated outputs")
    args = a.parse_args()
    if not args.check:
        for rel in SCRIPT_STEPS:
            subprocess.run([sys.executable, str(ROOT / rel)], check=True, cwd=ROOT)
    print(json.dumps(verify(ROOT), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
