#!/usr/bin/env python3
"""INFERRED: Keep candidate labels aligned with the written source-review proposal.

This module is offline. It neither collects evidence nor adjudicates human truth.
The rows and reasons in gold-source-reviewed.csv define the proposal membership.
"""
import argparse
import collections
import csv
import json
from pathlib import Path

SUPPORTED = "SOURCE_SUPPORTED_CANDIDATE_NOT_FROZEN"
UNREVIEWED = "CANDIDATE_NOT_FROZEN"
TIER = "supporting output of a named paper"


def pair_key(row):
    fields = ("artifact_record_id", "paper_record_id", "paper_doi")
    key = tuple(str(row.get(field, "")).strip().lower() for field in fields)
    if not all(key):
        raise ValueError("Incomplete artifact/paper/DOI identity")
    return key


def index_rows(rows, label):
    indexed = {}
    for row in rows:
        key = pair_key(row)
        if key in indexed:
            raise ValueError(f"Duplicate {label} pair: {key}")
        indexed[key] = row
    return indexed


def read_csv(path):
    with Path(path).open(newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows):
    with Path(path).open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def apply_source_review(candidates, proposal):
    """Return labeled copies; a relation type alone never selects a pair."""
    candidate_index = index_rows(candidates, "candidate")
    proposed = index_rows(proposal, "proposal")
    missing = proposed.keys() - candidate_index.keys()
    if missing:
        raise ValueError(f"Proposed pairs absent from candidates: {sorted(missing)}")
    for key, row in proposed.items():
        if row.get("agent_source_review") != "RELATIONSHIP_SUPPORTED":
            raise ValueError(f"Missing source-review assessment: {key}")
        if not str(row.get("review_reason", "")).strip():
            raise ValueError(f"Missing written source-review reason: {key}")
        if row.get("claim_tier") != TIER:
            raise ValueError(f"Unexpected proposal claim tier: {key}")
        # Match the evidence identity as well as the pair identity. An old
        # review cannot silently endorse a changed source or relationship.
        for field in ("source", "relation", "evidence_class"):
            if row.get(field) != candidate_index[key].get(field):
                raise ValueError(f"Source-review evidence changed ({field}): {key}")
    result = []
    for candidate in candidates:
        row = dict(candidate)
        review = proposed.get(pair_key(row))
        row["gold_state"] = SUPPORTED if review else UNREVIEWED
        row["claim_tier"] = TIER if review else "unverified"
        row["source_review_reason"] = review["review_reason"] if review else ""
        # In particular, do not change human_adjudication or imply funding.
        result.append(row)
    return result


def validate_rows(candidates, proposal):
    expected = apply_source_review(candidates, proposal)
    expected_keys = {pair_key(row) for row in proposal}
    actual_keys = {pair_key(row) for row in candidates if row.get("gold_state") == SUPPORTED}
    if actual_keys != expected_keys:
        raise ValueError(
            "Supported pair sets differ: "
            f"unexpected={sorted(actual_keys - expected_keys)}; "
            f"missing={sorted(expected_keys - actual_keys)}"
        )
    for actual, target in zip(candidates, expected):
        for field in ("gold_state", "claim_tier", "source_review_reason"):
            if actual.get(field, "") != target[field]:
                raise ValueError(f"Candidate {field} disagrees with proposal: {pair_key(actual)}")
    for row in proposal:
        if row.get("gold_state") != SUPPORTED:
            raise ValueError(f"Proposal row has inconsistent gold_state: {pair_key(row)}")
    if any(row.get("human_adjudication") != "NOT_DETERMINED" for row in candidates + proposal):
        raise ValueError("This public proposal must not invent human adjudication")
    return {
        "candidate_pairs": len(candidates),
        "source_supported_proposal_pairs": len(expected_keys),
        "source_reviewed_relation_basis": dict(collections.Counter(row["evidence_class"] for row in proposal)),
        "human_adjudicated_pairs": 0,
        "supported_pair_sets_equal": True,
    }


def validate_files(directory):
    directory = Path(directory)
    candidates = read_csv(directory / "artifact-first-gold-candidates.csv")
    proposal = read_csv(directory / "gold-source-reviewed.csv")
    result = validate_rows(candidates, proposal)
    summary_path = directory / "gold-rebuild-summary.json"
    if summary_path.exists():
        summary = json.loads(summary_path.read_text())
        for field, expected in (
            ("candidate_pairs", result["candidate_pairs"]),
            ("source_reviewed_relationship_pairs", result["source_supported_proposal_pairs"]),
            ("source_reviewed_relation_basis", result["source_reviewed_relation_basis"]),
            ("human_adjudicated_pairs", 0),
            ("frozen_benchmark_activated", False),
        ):
            if summary.get(field) != expected:
                raise ValueError(f"Gold summary disagrees with proposal: {field}")
    return result


def synchronize_files(directory):
    """Refresh labels only; preserve the proposal's members and written reasons."""
    directory = Path(directory)
    proposal_path = directory / "gold-source-reviewed.csv"
    candidate_path = directory / "artifact-first-gold-candidates.csv"
    proposal = read_csv(proposal_path)
    candidates = read_csv(candidate_path)
    labeled = apply_source_review(candidates, proposal)
    normalized = [{**row, "gold_state": SUPPORTED} for row in proposal]
    validate_rows(labeled, normalized)
    write_csv(candidate_path, labeled)
    write_csv(proposal_path, normalized)
    return validate_files(directory)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Synchronize labels from the existing proposal")
    args = parser.parse_args()
    directory = Path(__file__).resolve().parent
    result = synchronize_files(directory) if args.write else validate_files(directory)
    print(json.dumps({"claim_label": "VERIFIED_SOURCE", "result": "PASS", **result}, indent=2))
