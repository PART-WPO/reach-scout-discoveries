#!/usr/bin/env python3
"""Bounded, source-fingerprint-aware rotation for independent hourly Scout work.

The selector is read-only. Completed public originals are never proposed as
new original research; a completed REACH seed may still be used for *distinct*
related-output expansion. Blocked DOI identities rotate rather than ending an
hourly mission. The Crossref-459 guarded backstop retains its own originals.
"""
import argparse
import hashlib
import json
from pathlib import Path

from decision_pipeline import norm_doi

ROOT = Path(__file__).resolve().parents[2]
INDEX = "scout-operations/research-memory/mission-index.json"
GRAPH = "scout-operations/research-memory/crosslane-relationship-graph.json"
BUILDER = "scout-operations/tools/build_crosslane_research_memory.py"
GROUPS = (
    "monthly_original",
    "additional_related_output",
    "monthly_related",
    "historical_datacite_original",
    "verified_reach_expansion",
)
MAX_ATTEMPTS = 5
KNOWN_TERMINAL = frozenset({
    "already_in_reach", "no_action", "forwarded_to_hub",
    "metadata_update_forwarded", "staged_for_hub_import",
    "staged_for_human_review", "research_complete_human_intake",
    "human_metadata_needed",
})


def _sha(root, path):
    return hashlib.sha256((root / path).read_bytes()).hexdigest()


def load_index(root=ROOT):
    index = json.loads((root / INDEX).read_text(encoding="utf-8"))
    graph = json.loads((root / GRAPH).read_text(encoding="utf-8"))
    if index.get("schema") != "reach-scout-compact-crosslane-mission-index-v1":
        raise ValueError("Unexpected Scout mission index schema")
    if graph.get("schema") != "reach-scout-crosslane-research-memory-v1":
        raise ValueError("Unexpected Scout graph schema")
    if (graph.get("source_fingerprint") != index.get("source_fingerprint") or
            index.get("builder_policy_sha256") != _sha(root, BUILDER)):
        raise ValueError("STALE_SCOUT_RESEARCH_MEMORY: rebuild before DOI selection")
    shas = graph.get("source_evidence_sha256", {}).get(
        "verified_public_original_exit_source_sha256", {})
    if not shas:
        raise ValueError("MISSING_VERIFIED_TERMINAL_GATE: rebuild research memory")
    for label, path in (
        ("historical_research_coverage_sha256", "scout-operations/historical-coverage.json"),
        ("historical_reconciliation_exceptions_sha256",
         "scout-operations/historical-reconciliation-exceptions.json"),
        ("historical_original_ledger_sha256", "scout-operations/historical-triage.json"),
        ("active_public_scout_manifest_sha256", "scout-discoveries/manifest.json"),
    ):
        if shas.get(label) != _sha(root, path):
            raise ValueError("STALE_TERMINAL_GATE: " + path)
    return index


def eligible(index, *, blocked=(), limit=MAX_ATTEMPTS):
    if limit < 1 or limit > MAX_ATTEMPTS:
        raise ValueError("Hourly rotation is bounded to 1–5 distinct DOIs")
    ignored = {norm_doi(d) for d in blocked}
    if None in ignored or "" in ignored:
        raise ValueError("Invalid blocked DOI identity")
    picked = []
    seen = set(ignored)
    groups = index["recommended_preview"]
    for lane in GROUPS:
        for item in groups.get(lane, []):
            d = norm_doi(item.get("doi"))
            if not d or d in seen:
                continue
            if item.get("hourly_original_research_allowed") is False:
                continue
            # An unchanged source-backed project hold is not a fresh research
            # target. Reopen after a new evidence note changes its disposition,
            # rather than repeatedly using an hourly slot on the same hold.
            if item.get("next_action") == (
                    "REUSE_RECORDED_PROJECT_HOLD_REOPEN_ON_DISTINCT_EVIDENCE"):
                continue
            if lane.endswith("_original"):
                statuses = {
                    str(v).strip().lower()
                    for recorded in item.get("public_recorded_statuses_by_lane", {}).values()
                    for v in recorded
                }
                # A listed exception to an unsupported historical terminal is
                # eligible only because the *source-verified builder* explicitly
                # retained it for revalidation. Do not suppress blindly here.
                if (statuses & KNOWN_TERMINAL and
                        lane != "historical_datacite_original"):
                    continue
            seen.add(d)
            picked.append({"doi": d, "group": lane, "track": item.get("track"),
                           "next_action": item["next_action"],
                           "input_fingerprint": item.get("input_fingerprint")})
            if len(picked) == limit:
                return picked
    return picked


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--blocked-doi", action="append", default=[])
    parser.add_argument("--limit", type=int, default=MAX_ATTEMPTS)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    index = load_index(args.root)
    queue = eligible(index, blocked=args.blocked_doi, limit=args.limit)
    print(json.dumps({
        "schema": "reach-scout-independent-hourly-mission-rotation-v1",
        "max_distinct_dois_per_mission": MAX_ATTEMPTS,
        "candidates": queue,
        "candidate_count": len(queue),
        "public_original_decisions_or_approvals_inferred": False,
    }, indent=2))


if __name__ == "__main__":
    main()
