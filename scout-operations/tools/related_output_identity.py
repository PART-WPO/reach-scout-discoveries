#!/usr/bin/env python3
"""Fail-closed, read-only same-mission related DOI public identity screen.

The SHA-checked REACH+Scout snapshot includes BOTH published batches and the
public Scout inbox. A negative needs an independently live, checksum-verified
full canonical REACH index; a cache-only miss is never enough.
"""
from pathlib import Path
from ir_reach_identity import verified_snapshot, identity_check
from reach_version_identity import fetch_reach_index
from decision_pipeline import norm_doi, norm_title
from verify_reach_artifact_url import artifact_url as canonical_artifact_url

IR_SAFE_NEGATIVES = {
    "DOI_NOT_IN_VERIFIED_IR_INDEX_UNKNOWN",
    "VERIFIED_IR_URL_NOT_IN_PUBLIC_REACH",
}


def screen(root, doi, title="", artifact_url="", *,
           snapshot_fn=verified_snapshot, check_fn=identity_check,
           live_fn=fetch_reach_index):
    key = norm_doi(doi)
    if not key:
        raise ValueError("Exact DOI required for public identity check")
    result = {
        "doi": key, "status": "PUBLIC_IDENTITY_GATE_INCOMPLETE",
        "noaa_ir_reach_check": {"status": "NOT_VERIFIED"},
        "checked_public_scout_manifest_and_inbox": False,
        "checked_live_complete_reach": False,
        "public_identity_source_fingerprint": None,
        "live_reach_manifest_sha256": None,
        "matches": [], "reason": "",
    }
    try:
        public, ir = snapshot_fn(Path(root))
        current = check_fn(public, ir, key, title, "https://doi.org/" + key)
        result["checked_public_scout_manifest_and_inbox"] = True
        result["public_identity_source_fingerprint"] = public.get("source_fingerprint")
        result["noaa_ir_reach_check"] = current.get("noaa_ir_reach_check") or {"status": "NOT_VERIFIED"}
        result["matches"] = current.get("matches", [])
        public_status = current.get("status", "NOT_VERIFIED")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        result["reason"] = "PUBLIC_SCOUT_REACH_SNAPSHOT_FAILURE:" + type(exc).__name__
        return result

    # A verified public Scout proposal is already one review unit. No need
    # to re-stage or spend a full REACH negative scan merely to skip it.
    if public_status == "IN_PUBLIC_SCOUT_QUEUE":
        result["status"] = "IN_PUBLIC_SCOUT_QUEUE"
        result["reason"] = "SHA_VERIFIED_SCOUT_PUBLISHED_OR_INBOX_MATCH"
        return result

    try:
        live = live_fn()
        if not isinstance(live, dict) or not isinstance(live.get("by_id"), dict) or not isinstance(live.get("by_doi"), dict) or not live.get("manifest_sha256"):
            raise ValueError("Unverified live REACH canonical index")
        result["checked_live_complete_reach"] = True
        result["live_reach_manifest_sha256"] = live["manifest_sha256"]
        primary_doi = live["by_doi"].get(key, [])
        target = canonical_artifact_url(artifact_url)
        primary_artifacts = [
            item for item in live["by_id"].values()
            if target and canonical_artifact_url(item.get("link")) == target
        ]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        result["reason"] = "LIVE_REACH_INDEX_FAILURE:" + type(exc).__name__
        return result

    # Exact primary URL or DOI can reveal an existing REACH output even if
    # the older cache contains only an article's supporting link.
    positives = {x.get("record_id"): x for x in primary_doi + primary_artifacts
                 if isinstance(x, dict) and x.get("record_id")}
    if positives:
        result["matches"] = [
            {"source": "LIVE_REACH_PRIMARY", "record_id": x["record_id"],
             "reach_uid": x.get("reach_uid"), "title": x.get("title"),
             "output_type": x.get("output_type"), "primary_url": x.get("link")}
            for x in positives.values()
        ]
        if len(positives) == 1 and (
            primary_artifacts or not title or
            norm_title(next(iter(positives.values())).get("title", "")) == norm_title(title)
        ):
            result["status"] = "CONFIRMED_PUBLIC_REACH_IDENTITY"
            result["reason"] = "LIVE_CANONICAL_PRIMARY_IDENTIFIER"
        else:
            result["status"] = "BOUNDED_PUBLIC_IDENTITY_REVIEW"
            result["reason"] = "MULTIPLE_OR_CONFLICTING_PRIMARY_IDENTITIES"
        return result

    if public_status == "CONFIRMED_PUBLIC_REACH_IDENTITY":
        # The cache has a positive whose live primary identity vanished:
        # fail closed rather than silently reversing an existing verdict.
        result["status"] = "PUBLIC_IDENTITY_GATE_INCOMPLETE"
        result["reason"] = "REACH_CACHE_AND_LIVE_PRIMARY_CONFLICT"
    elif public_status != "NO_PUBLIC_IDENTITY_MATCH":
        result["status"] = "BOUNDED_PUBLIC_IDENTITY_REVIEW"
        result["reason"] = "CACHE_OR_SCOUT_SIMILARITY_REQUIRES_REVIEW"
    elif result["noaa_ir_reach_check"].get("status") not in IR_SAFE_NEGATIVES:
        result["status"] = "PUBLIC_IDENTITY_GATE_INCOMPLETE"
        result["reason"] = "IR_IDENTITY_NOT_RESOLVED"
    else:
        result["status"] = "NO_PUBLIC_IDENTITY_MATCH"
        result["reason"] = "SHA_VERIFIED_SCOUT_AND_LIVE_FULL_REACH_NEGATIVE"
    return result
