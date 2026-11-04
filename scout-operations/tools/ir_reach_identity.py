#!/usr/bin/env python3
"""Evidence-only NOAA IR DOI to existing REACH URL identity fallback.

Works for independent discovery and historical original/expansion research.
Loads the locally SHA-verified public NOAA IR index once per mission. Never
enriches existing REACH outputs, changes user decisions, or creates candidates.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scout-discoveries/tools"))
from noaa_ir_lookup import trusted_index
from decision_pipeline import build_index, check_index_fresh, lookup, norm_doi, norm_url


def verified_snapshot(root=ROOT):
    """Build one verified public REACH+Scout index and one trusted IR DOI index."""
    public = build_index(root)
    check_index_fresh(root, public)
    return public, trusted_index(root)


def identity_check(public, ir_index, doi, title="", url=""):
    """Check original DOI/title/URL, then exact official DOI->IR URL->REACH.

    A unique official IR mapping is not automatically a REACH match. Require
    exactly one REACH record with that identical URL. A conflicting DOI or
    multiple REACH identities require human version/identity review.
    """
    key = norm_doi(doi)
    direct = lookup(public, doi=key, title=title, url=url)
    result = dict(direct)
    result["noaa_ir_reach_check"] = {
        "status": "NOT_NEEDED_DIRECT_REACH" if direct["status"] == "CONFIRMED_PUBLIC_REACH_IDENTITY" else "NOT_VERIFIED",
        "official_url": None,
        "match_uid": None,
        "match_detail_shard": None,
    }
    if direct["status"] == "CONFIRMED_PUBLIC_REACH_IDENTITY":
        return result
    if ir_index is None:
        result["noaa_ir_reach_check"]["status"] = "IR_INDEX_UNAVAILABLE_HOLD"
        return result
    urls = ir_index["dois"].get(key, []) if key else []
    if not urls:
        result["noaa_ir_reach_check"]["status"] = "DOI_NOT_IN_VERIFIED_IR_INDEX_UNKNOWN"
        return result
    if len(set(urls)) != 1:
        result["noaa_ir_reach_check"]["status"] = "AMBIGUOUS_IR_DOI_HOLD"
        return result
    ir_url = urls[0]
    result["noaa_ir_reach_check"]["official_url"] = ir_url
    positions = public["keys"]["url"].get(norm_url(ir_url), [])
    reach_positions = sorted(set(pos for pos in positions if public["records"][pos]["source"] == "REACH"))
    if len(reach_positions) > 1:
        result["noaa_ir_reach_check"]["status"] = "MULTIPLE_REACH_RECORDS_HOLD"
        return result
    if not reach_positions:
        result["noaa_ir_reach_check"]["status"] = "VERIFIED_IR_URL_NOT_IN_PUBLIC_REACH"
        return result
    rec = public["records"][reach_positions[0]]
    result["noaa_ir_reach_check"].update({
        "match_uid": rec["identity"],
        "match_detail_shard": rec["location"],
    })
    # The same IR URL associated with another explicit DOI can represent a
    # distinct version. Do not silently resolve it as the same publication.
    if rec["dois"] and key not in rec["dois"]:
        result["noaa_ir_reach_check"]["status"] = "REACH_DOI_CONFLICT_VERSION_REVIEW"
        result["status"] = "POSSIBLE_PUBLIC_REACH_MATCH"
        return result
    secondary = lookup(public, doi=key, title=title, url=ir_url)
    exact = [m for m in secondary["matches"]
             if m["source"] == "REACH"
             and m["identity"] == rec["identity"]
             and "exact_url" in m["match_bases"]]
    if len(exact) != 1:
        result["noaa_ir_reach_check"]["status"] = "IR_URL_MATCH_REQUIRES_REVIEW"
        return result
    result["status"] = "CONFIRMED_PUBLIC_REACH_IDENTITY"
    result["matches"] = secondary["matches"]
    result["noaa_ir_reach_check"]["status"] = "VERIFIED_OFFICIAL_IR_DOI_TO_EXISTING_REACH_URL"
    return result


def research_route(check):
    """Never treat public negative identities as approval or global absence."""
    status = check["status"]
    ir = check["noaa_ir_reach_check"]["status"]
    if status == "CONFIRMED_PUBLIC_REACH_IDENTITY":
        return "existing_reach_original_preserve_doi_seed_expansion"
    if status == "IN_PUBLIC_SCOUT_QUEUE":
        return "existing_scout_candidate_no_duplicate_preserve_seed"
    if ir in {"IR_INDEX_UNAVAILABLE_HOLD", "AMBIGUOUS_IR_DOI_HOLD",
              "MULTIPLE_REACH_RECORDS_HOLD", "REACH_DOI_CONFLICT_VERSION_REVIEW",
              "IR_URL_MATCH_REQUIRES_REVIEW"} or check["matches"]:
        return "bounded_identity_or_version_review_no_staging"
    return "advance_to_funding_metadata_and_private_decision_checks"
