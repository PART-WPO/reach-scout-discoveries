#!/usr/bin/env python3
"""Emit evidence-backed, privacy-minimized GitHub backstop mission metrics.

This records actual completed GitHub guarded handoffs and deliberately never
represents them as ChatGPT's distinct hourly research mission executions.
"""
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HANDOFF = Path("scout-operations/reports/hourly-decision-handoff.json")
INDEX = Path("scout-operations/research-memory/mission-index.json")
DEST = Path("scout-operations/reports/guarded-backstop-missions")


def canonical_dois(values):
    cleaned = []
    for value in values:
        doi = str(value or "").strip().lower()
        doi = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:)", "", doi)
        if doi.startswith("10.") and doi not in cleaned:
            cleaned.append(doi)
    return cleaned


def utc_time(value):
    dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("Mission timestamps must include an offset")
    return dt.astimezone(timezone.utc)


def build(root, run_id, attempt, commit_sha, *, finished_at=None):
    if not re.fullmatch(r"[0-9]+", str(run_id)):
        raise ValueError("GitHub run ID must be an integer string")
    if not re.fullmatch(r"[1-9][0-9]*", str(attempt)):
        raise ValueError("GitHub attempt must be a positive integer")
    if not re.fullmatch(r"[0-9a-f]{40}", commit_sha):
        raise ValueError("Source commit SHA must be a full 40-character SHA")
    report_raw = (root / HANDOFF).read_bytes()
    report = json.loads(report_raw)
    if report.get("schema") != "reach-scout-hourly-decision-handoff-v1":
        raise ValueError("Unknown guarded handoff report schema")
    index_path = root / INDEX
    index = json.loads(index_path.read_text()) if index_path.exists() else {}
    outcomes = report.get("outcomes")
    if not isinstance(outcomes, list):
        raise ValueError("No verifiable guarded handoff outcomes array")
    published = [x for x in outcomes if x.get("status") == "PUBLISHED_PUBLIC_SCOUT"]
    if len(published) != report.get("public_review_batches_validated_this_run"):
        raise ValueError("Published handoff count disagrees with outcomes")
    blocked = [x for x in outcomes if x.get("status") == "BLOCKED"]
    if published:
        handoff_status = "PUBLISHED_PUBLIC_SCOUT"
    elif blocked or any(x.get("status") in ("STAGED_VALIDATED_INBOX", "PENDING_OR_HELD_PUBLICATION_GATE") for x in outcomes):
        handoff_status = "BLOCKED"
    else:
        handoff_status = "NOT_ATTEMPTED"
    blocker = "; ".join(sorted({x.get("decision", x.get("status", "UNKNOWN")) for x in outcomes if x not in published}))
    if handoff_status == "BLOCKED" and not blocker:
        blocker = "PUBLICATION_GATE_NOT_CONFIRMED"
    t0 = utc_time(report["ran_at"])
    t1 = finished_at or datetime.now(timezone.utc)
    if t1 < t0:
        raise ValueError("Completion cannot precede actual processing time")
    measured = report.get("measurement") or {}
    request_count = measured.get("provider_http_requests_observed")
    if request_count is not None and (type(request_count) is not int or request_count < 0):
        raise ValueError("Invalid actual-provider-request counter")
    reuse = measured.get("in_process_metadata_reuses")
    if reuse is not None and (type(reuse) is not int or reuse < 0):
        raise ValueError("Invalid in-process reuse count")
    note_hashes = measured.get("prior_research_note_sha256_reused") or []
    for digest in note_hashes:
        if not re.fullmatch(r"[a-f0-9]{64}", digest):
            raise ValueError("Unverified prior note fingerprint")
    paths = [str(x.get("published_batch", "")) for x in published]
    if any(not x.startswith("scout-discoveries/batches/") for x in paths):
        raise ValueError("Published batch is not a public Scout batch")
    for rel in paths:
        if not (root / rel).is_file():
            raise ValueError("Published batch file is missing: " + rel)
    doc = {
        "schema": "reach-scout-hourly-mission-outcome-v1",
        "producer": "github_guarded_crossref_backstop",
        "not_chatgpt_hourly_mission": True,
        "mission_id": f"github-{run_id}-{attempt}",
        "started_at_utc": t0.isoformat(),
        "completed_at_utc": t1.isoformat(),
        "policy_commit_sha": commit_sha,
        "memory_source_fingerprint": index.get("source_fingerprint") or "NOT_VERIFIED",
        "memory_builder_policy_sha256": index.get("builder_policy_sha256") or "NOT_VERIFIED",
        "lane": "historical_crossref_original",
        "selected_original_dois": canonical_dois(x.get("doi") for x in outcomes),
        "selected_expansion_seed_dois": [],
        "fast_exited_public_reach": canonical_dois(x.get("doi") for x in outcomes if x.get("fast_exit_kind") == "reach"),
        "fast_exited_public_scout": canonical_dois(x.get("doi") for x in outcomes if x.get("fast_exit_kind") == "scout"),
        "new_original_full_decisions": canonical_dois(x.get("doi") for x in published),
        "new_expansion_decisions": [],
        "research_only_holds": [],
        "technical_or_funding_holds": canonical_dois(x.get("doi") for x in blocked),
        "published_public_batch_urls": [
            "https://github.com/PART-WPO/reach-scout-discoveries/blob/main/" + p for p in paths
        ],
        "guarded_handoff_run_urls": [
            f"https://github.com/PART-WPO/reach-scout-discoveries/actions/runs/{run_id}"
        ],
        "handoff_status": handoff_status,
        "handoff_blocker": blocker if handoff_status == "BLOCKED" else None,
        "prior_note_sha256_reused": sorted(set(note_hashes)),
        "prior_metadata_fingerprints_reused": [],
        "cache_hits_observed": reuse,
        "external_requests_observed": request_count,
        "avoided_requests_measured": None,
        "measurement_scope": "actual DOI metadata provider requests observed in guarded Python process only; cache_hits_observed denotes in-process memo reuse, not persistent-cache hits",
        "previously_screened_skipped_not_mission_fast_exits": canonical_dois(
            x.get("doi") for x in report.get("skipped_cooldown_or_already_staged", [])
        ),
        "source_handoff_report_sha256": hashlib.sha256(report_raw).hexdigest(),
        "source_selection_sha256": report.get("source_selection_sha256"),
        "private_hub_import": "NOT_VERIFIED",
        "human_decision": "NOT_VERIFIED",
        "public_reach_addition": "NOT_VERIFIED"
    }
    # Validating the assembled record is part of its creation.
    from validate_hourly_mission import validate
    errs = validate(doc)
    if errs:
        raise ValueError("Invalid completed mission report: " + "; ".join(errs))
    return doc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--github-run-id", required=True)
    ap.add_argument("--github-attempt", required=True)
    ap.add_argument("--source-commit", required=True)
    args = ap.parse_args()
    doc = build(args.root, args.github_run_id, args.github_attempt, args.source_commit)
    rel = DEST / (doc["mission_id"] + ".json")
    dest = args.root / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        raise ValueError("Immutable completed mission ID already exists: " + str(rel))
    dest.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"mission_report": str(rel), "status": doc["handoff_status"],
                      "public_handoffs": len(doc["new_original_full_decisions"]),
                      "private_hub_import": "NOT_VERIFIED"}))


if __name__ == "__main__":
    main()
