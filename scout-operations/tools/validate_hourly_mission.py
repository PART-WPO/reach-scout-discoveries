#!/usr/bin/env python3
"""Validate public, privacy-minimized Scout hourly mission records (stdlib only)."""
import argparse
import json
import re
from datetime import datetime
from pathlib import Path

REQUIRED_LISTS = (
    "selected_original_dois", "selected_expansion_seed_dois",
    "fast_exited_public_reach", "fast_exited_public_scout",
    "new_original_full_decisions", "new_expansion_decisions",
    "research_only_holds", "technical_or_funding_holds",
    "published_public_batch_urls", "guarded_handoff_run_urls",
    "prior_note_sha256_reused", "prior_metadata_fingerprints_reused",
)
ALLOWED_HANDOFF = {"PUBLISHED_PUBLIC_SCOUT", "VERIFIED_ALREADY_PUBLIC", "BLOCKED", "NOT_ATTEMPTED", "NOT_VERIFIED"}
ALLOWED_LANES = {"monthly_original", "historical_crossref_original", "historical_datacite_original", "independent_original", "related_expansion", "mixed"}

def validate(record):
    errors = []
    if record.get("schema") != "reach-scout-hourly-mission-outcome-v1":
        errors.append("schema mismatch")
    if not isinstance(record.get("mission_id"), str) or not record["mission_id"].strip():
        errors.append("missing mission_id")
    for key in ("started_at_utc", "completed_at_utc"):
        try:
            dt = datetime.fromisoformat(record[key].replace("Z", "+00:00"))
            if dt.tzinfo is None:
                raise ValueError("timezone missing")
        except (KeyError, TypeError, ValueError):
            errors.append(f"invalid {key}")
    if not any(e.startswith("invalid ") for e in errors):
        start = datetime.fromisoformat(record["started_at_utc"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(record["completed_at_utc"].replace("Z", "+00:00"))
        if end < start:
            errors.append("completion precedes start")
    if record.get("lane") not in ALLOWED_LANES:
        errors.append("invalid lane")
    if record.get("handoff_status") not in ALLOWED_HANDOFF:
        errors.append("invalid handoff_status")
    for key in REQUIRED_LISTS:
        if not isinstance(record.get(key), list):
            errors.append(f"{key} must be a list")
    for key in ("cache_hits_observed", "external_requests_observed", "avoided_requests_measured"):
        val = record.get(key, "MISSING")
        if val == "MISSING" or (val is not None and (type(val) is not int or val < 0)):
            errors.append(f"{key} must be null or nonnegative integer")
    for key in ("policy_commit_sha", "memory_source_fingerprint", "memory_builder_policy_sha256"):
        if key not in record or not isinstance(record[key], str):
            errors.append(f"missing {key}")
    for key in ("private_hub_import", "human_decision", "public_reach_addition"):
        if record.get(key) != "NOT_VERIFIED":
            errors.append(f"{key} requires separate authenticated evidence; public mission schema permits NOT_VERIFIED only")
    if record.get("handoff_status") == "PUBLISHED_PUBLIC_SCOUT" and not record.get("published_public_batch_urls"):
        errors.append("published handoff requires a public batch URL")
    if record.get("handoff_status") == "BLOCKED" and not record.get("handoff_blocker"):
        errors.append("blocked handoff requires blocker")
    return errors

def main():
    p = argparse.ArgumentParser()
    p.add_argument("paths", nargs="+", type=Path)
    args = p.parse_args()
    failed = False
    for path in args.paths:
        try:
            errors = validate(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, ValueError) as exc:
            errors = [str(exc)]
        print(f"{path}: " + ("OK" if not errors else "; ".join(errors)))
        failed |= bool(errors)
    raise SystemExit(1 if failed else 0)

if __name__ == "__main__":
    main()
