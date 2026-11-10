#!/usr/bin/env python3
"""Audit genuine prior-metadata reuse in an executed independent lookup report.

No new network calls: this is a post-run measurement of the provider attempt
logs already captured at the actual resolver boundary. It cannot measure
GitHub/Zenodo scope enrichment or other HTTP activity.
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCES = {
    "independent-doi": (
        "scout-operations/reports/independent-doi-lookup/latest.json",
        "reach-scout-independent-doi-lookup-v1", "records"
    ),
    "independent-metadata": (
        "scout-operations/reports/independent-metadata-lookup/latest.json",
        "reach-scout-independent-metadata-lookup-v1", "doi_records"
    ),
}


def sha(value):
    return hashlib.sha256(value).hexdigest()


def audit(root, mode):
    source, schema, field = SOURCES[mode]
    raw = (root / source).read_bytes()
    doc = json.loads(raw)
    if doc.get("schema") != schema or not isinstance(doc.get(field), list):
        raise ValueError("Unsupported independent lookup source")
    rows = doc[field]
    if len(rows) != len({str(x.get("doi", "")).lower() for x in rows}):
        raise ValueError("DOI identities are not unique in source")
    hits = [x for x in rows if x.get("metadata_memory_hit") is True]
    misses = [x for x in rows if x.get("metadata_memory_hit") is False]
    if len(hits) + len(misses) != len(rows):
        raise ValueError("Missing prior-metadata reuse instrumentation")
    if any(x.get("metadata_memory_reason") != "VERIFIED_CACHED_OFFICIAL_METADATA" for x in hits):
        raise ValueError("Unverified metadata cache hit")
    attempts = [x.get("metadata", {}).get("attempts") for x in misses]
    observed = sum(len(x) for x in attempts) if all(isinstance(x, list) for x in attempts) else None
    fingerprints = sorted(set(sha(json.dumps(
        x["metadata"], sort_keys=True, ensure_ascii=False,
        separators=(",", ":")).encode("utf-8")) for x in hits))
    used_historical_hints = sum(x.get("previous_public_research") is not None for x in rows)
    return {
        "schema": "reach-scout-measured-independent-metadata-reuse-v1",
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_report": source,
        "source_report_sha256": sha(raw),
        "source_public_identity_fingerprint": doc.get("public_identity_source_fingerprint"),
        "scope": "DOI DataCite/Crossref resolver attempts only; excludes unrelated HTTP calls and historical requests from cached responses",
        "distinct_dois_observed": len(rows),
        "verified_persistent_metadata_cache_hits": len(hits),
        "doi_resolver_cache_misses": len(misses),
        "provider_http_requests_observed": observed,
        "prior_metadata_content_sha256_reused": fingerprints,
        "historical_author_hint_consulted_count": used_historical_hints,
        "avoided_requests_measured": None,
        "private_hub_import": "NOT_VERIFIED",
        "human_decision": "NOT_VERIFIED",
        "public_reach_addition": "NOT_VERIFIED"
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--mode", choices=sorted(SOURCES), required=True)
    args = p.parse_args()
    result = audit(args.root, args.mode)
    target = args.root / f"scout-operations/reports/research-memory-reuse/{args.mode}-latest.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"source": result["source_report"], "cache_hits": result["verified_persistent_metadata_cache_hits"],
                      "provider_requests_observed": result["provider_http_requests_observed"],
                      "avoided_requests_measured": None}))


if __name__ == "__main__":
    main()
