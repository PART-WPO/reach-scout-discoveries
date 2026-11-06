#!/usr/bin/env python3
"""Issue #35: rebuild Scout's public-source-derived reports in dependency order.

No private Hub/Smartsheet access, human decisions, public batch publication,
or changes to protected original/seed-expansion dispositions.
Run on a clean, SHA-pinned checkout; caller retries from fresh main on conflicts.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESEARCH = "scout-operations/"
MANIFEST = "scout-discoveries/manifest.json"
INDEX = RESEARCH + "identity-cache/public-identity-index.json"
ROLLUP = RESEARCH + "research-decision-rollup.json"
UNIFIED = RESEARCH + "unified-source-preflight.json"
SCORECARD = RESEARCH + "scout-operational-scorecard.json"
IMPACT = RESEARCH + "scout-v2-impact-report.json"
FEEDBACK = RESEARCH + "research-feedback.json"

# The ordering is deliberate: no downstream fingerprint-dependent tests before
# the new persisted index, the checkpoint decisions, and all derived reports.
STEPS = (
    "reconcile_historical.py",
    "reconcile_historical_crossref.py",
    "decision_pipeline.py build-index",
    "compile_research_evidence.py",
    "decision_pipeline.py evaluate --cases scout-operations/research-decision-cases.json",
    "summarize_research_decisions.py",
    "build_expansion_relevance.py",
    "select_workstream.py",
    "unified_source_preflight.py",
    "validate_reviewer_feedback.py",
    "build_operational_scorecard.py",
    "build_impact_report.py",
    "build_scout_v2_benchmark.py",
)

PROTECTED = ("status", "seed_expansion_status", "human_decision", "scout_batch_path")
TRIAGE = (
    RESEARCH + "historical-triage.json",
    RESEARCH + "historical-crossref-triage.json",
)

# The stage list is intentionally restricted to known derived outputs.
DERIVED_FILES = (
    RESEARCH + "historical-coverage.json",
    RESEARCH + "historical-crossref-coverage.json",
    RESEARCH + "historical-reconciliation-exceptions.json",
    RESEARCH + "historical-crossref-reconciliation-exceptions.json",
    INDEX, RESEARCH + "research-decision-cases.json",
    RESEARCH + "research-evidence-coverage.json",
    ROLLUP, RESEARCH + "expansion-relevance-priority.json",
    RESEARCH + "active-workstream.json", UNIFIED, FEEDBACK,
    SCORECARD, IMPACT, RESEARCH + "scout-v2-benchmark-100.json",
)

def read(root, relative):
    return json.loads((root / relative).read_text(encoding="utf-8"))

def digest(root, relative):
    return hashlib.sha256((root / relative).read_bytes()).hexdigest()

def snapshot_protected(root):
    result = {}
    for relative in TRIAGE:
        data = read(root, relative)
        entries = data["entries"]
        identity = [str(x["identity"]) for x in entries]
        if len(identity) != len(set(identity)):
            raise ValueError("Duplicate historical identity in protected source: " + relative)
        result[relative] = {
            key: {k: row.get(k) for k in PROTECTED}
            for key, row in ((str(x["identity"]), x) for x in entries)
        }
    return result

def verify(root=ROOT):
    feed = read(root, MANIFEST)
    index = read(root, INDEX)
    rollup = read(root, ROLLUP)
    unified = read(root, UNIFIED)
    score = read(root, SCORECARD)
    impact = read(root, IMPACT)
    feedback = read(root, FEEDBACK)
    if feed["schema"] != "reach-scout-discovery-feed-v1":
        raise ValueError("Unexpected public Scout manifest schema")
    if feed["batch_count"] != len(feed["batches"]):
        raise ValueError("Published Scout manifest batch count mismatch")
    if feed["candidate_rows"] != sum(b["record_count"] for b in feed["batches"]):
        raise ValueError("Published Scout candidate rows mismatch")
    sources = index["sources"]
    if sources["scout_manifest_sha256"] != digest(root, MANIFEST) or sources["scout_batches"] != feed["batch_count"]:
        raise ValueError("Persisted Scout identity cache is stale")
    fingerprint = index["source_fingerprint"]
    if rollup["identity_index_fingerprint"] != fingerprint or unified["identity_index_fingerprint"] != fingerprint:
        raise ValueError("Rollup/preflight uses a different identity index fingerprint")
    if unified["identity_index_source_sha256"] != sources:
        raise ValueError("Preflight source index is not byte-identical to shared sources")
    if score["source_sha256"]["shared_identity_index"] != digest(root, INDEX):
        raise ValueError("Scorecard identity-index checksum mismatch")
    if score["source_sha256"]["scout_published_manifest"] != digest(root, MANIFEST):
        raise ValueError("Scorecard public Scout feed checksum mismatch")
    if impact["source_sha256"]["scorecard"] != digest(root, SCORECARD) or impact["source_sha256"]["unified"] != digest(root, UNIFIED):
        raise ValueError("Impact report references stale derived sources")
    published = sum(x["source"] == "SCOUT_PUBLISHED" for x in index["records"])
    if published != feed["candidate_rows"]:
        raise ValueError("Shared identity index lacks some published Scout candidates")
    if score["review_pipeline"]["public_scout_batches"] != feed["batch_count"] or score["review_pipeline"]["public_scout_staged_proposals"] != feed["candidate_rows"]:
        raise ValueError("Operational scorecard has stale Scout counts")
    if impact["pipeline"]["public_scout_staged_proposal_rows"] != feed["candidate_rows"]:
        raise ValueError("Impact report has stale published Scout counts")
    if any((
        rollup.get("automatically_staged", 0),
        rollup.get("original_terminal_statuses_modified", 0),
        rollup.get("expansion_seed_closures", 0),
        unified.get("changes_to_human_dispositions", 0),
        unified.get("new_public_review_proposals", 0),
        unified.get("new_reach_additions", 0),
    )):
        raise ValueError("Derived reporting crossed an original/reviewer/publication boundary")
    if score["review_pipeline"]["private_discovery_hub_imports"] != "NOT_VERIFIED" or impact["pipeline"]["private_hub_imports"] != "NOT_VERIFIED":
        raise ValueError("Do not infer private Hub import from public source data")
    if impact["pipeline"]["verified_new_public_reach_additions_from_scout"] != "NOT_VERIFIED":
        raise ValueError("Do not infer public REACH additions from public Scout staging")
    if feedback["signals"] or feedback["events_held_for_manual_identity_reconciliation"]:
        raise ValueError("Privacy hold: private reviewer outcomes may not be exported to public GitHub")
    if feedback["private_hub_connection_status"] != "NOT_CONNECTED_OR_NOT_EXPORTED":
        raise ValueError("Unexpected public reviewer feedback connection")
    if feedback["source_identity_fingerprint"] != fingerprint:
        raise ValueError("Empty public reviewer-feedback metadata uses a stale source fingerprint")
    return {
        "scout_batches": feed["batch_count"],
        "published_scout_candidates": feed["candidate_rows"],
        "fingerprint": fingerprint,
        "protected_reviewer_events": len(feedback["signals"]),
        "private_hub_imports": "NOT_VERIFIED",
        "public_reach_additions": "NOT_VERIFIED",
    }

def rebuild(root=ROOT):
    before = snapshot_protected(root)
    public_feedback = read(root, FEEDBACK)
    if public_feedback["signals"] or public_feedback["events_held_for_manual_identity_reconciliation"]:
        raise ValueError("Privacy hold: existing public private-review disclosures require separate handling")
    for step in STEPS:
        name, *arguments = step.split()
        subprocess.run([sys.executable, str(root / RESEARCH / "tools" / name), *arguments],
                       cwd=root, check=True)
    if snapshot_protected(root) != before:
        raise ValueError("Protected original/human/seed-expansion state was changed")
    if read(root, FEEDBACK)["signals"] != public_feedback["signals"]:
        raise ValueError("Review outcome list unexpectedly changed")
    report = verify(root)
    print("SCOUT_DERIVED_REFRESH_VERIFIED:", json.dumps(report, sort_keys=True))
    return report

if __name__ == "__main__":
    rebuild()
