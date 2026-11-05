#!/usr/bin/env python3
"""Conservative, evidence-only bulk REACH identity decision for public DOI leads.

This is a SCREENING gate. It must never rewrite original research ledgers,
close DOI-seeded expansion lanes, stage candidates, infer private Hub review,
or claim that index-negative research is globally new.
"""
from collections import Counter

IR_VERIFIED = "VERIFIED_OFFICIAL_IR_DOI_TO_EXISTING_REACH_URL"
IR_HOLDS = {
    "IR_INDEX_UNAVAILABLE_HOLD",
    "AMBIGUOUS_IR_DOI_HOLD",
    "MULTIPLE_REACH_RECORDS_HOLD",
    "REACH_DOI_CONFLICT_VERSION_REVIEW",
    "IR_URL_MATCH_REQUIRES_REVIEW",
}


def decide(matches, ir_evidence, *, title_available, previous_screening_status="POSSIBLE_MATCH"):
    """Return a screening disposition from VERIFIED public REACH+NOAA IR inputs.

    matches: one per distinct REACH UID, containing doi_hit, title_hit,
    official_ir_url_hit and evidence paths. The caller must verify cache,
    original source, official IR crosswalk and complete feed snapshots first.

    Exact DOI *plus title agreement* or an exact official IR DOI->URL->REACH
    link *plus title agreement* must point to precisely one REACH record.
    Missing/contradictory titles, multiple identities and version conflicts
    remain for bounded review rather than being silently auto-confirmed.
    """
    ir_status = (ir_evidence or {}).get("status", "IR_INDEX_UNAVAILABLE_HOLD")
    if not title_available:
        return {
            "status": "SCREENING_INCOMPLETE",
            "route": "RECOVER_SOURCE_TITLE_THEN_RESCREEN",
            "basis": "SOURCE_TITLE_MISSING",
            "verified_reach_uid": None,
            "verified_record_id": None,
            "verified_detail_path": None,
            "requires_human_identity_review": True,
        }

    strong_doi = [m for m in matches if m.get("doi_hit")]
    strong_ir = [m for m in matches if m.get("official_ir_url_hit")]
    all_ids = {m["reach_uid"] for m in matches}
    has_exact = bool(strong_doi)
    has_ir = ir_status == IR_VERIFIED and bool(strong_ir)
    strong = bool(has_exact or has_ir)
    one_match = len(all_ids) == 1
    same_title = one_match and bool(matches[0].get("title_hit"))
    # Never convert a version conflict, ambiguous IR link or multiple REACH
    # identities into a confirmed duplicate, even when DOI/title also match.
    conflict = ir_status in IR_HOLDS
    if strong and one_match and same_title and not conflict:
        m = matches[0]
        method = ("EXACT_REACH_DOI_AND_TITLE" if has_exact
                  else "VERIFIED_NOAA_IR_DOI_TO_REACH_URL_AND_TITLE")
        return {
            "status": "VERIFIED_EXISTING_REACH",
            "route": "SKIP_ORIGINAL_NEW_OUTPUT_RESEARCH_KEEP_EXPANSION_SEED",
            "basis": method,
            "verified_reach_uid": m["reach_uid"],
            "verified_record_id": m["record_id"],
            "verified_detail_path": m["detail_path"],
            "requires_human_identity_review": False,
        }

    if conflict:
        reason = "OFFICIAL_IR_IDENTITY_AMBIGUOUS_OR_CONFLICTING"
        route = "VERIFY_OFFICIAL_IR_AND_VERSION_CONFLICT_ONCE"
    elif len(all_ids) > 1:
        reason = "MULTIPLE_REACH_IDENTITIES"
        route = "VERIFY_MULTIPLE_REACH_IDENTITIES_ONCE"
    elif strong:
        reason = "STRONG_IDENTITY_BUT_TITLE_OR_VERSION_DISAGREES"
        route = "VERIFY_TITLE_VERSION_ONCE"
    elif matches:
        reason = "NORMALIZED_TITLE_ONLY"
        route = "VERIFY_TITLE_VERSION_ONCE"
    else:
        reason = "NO_PUBLIC_REACH_IDENTITY_MATCH"
        route = "ADVANCE_TO_FUNDING_AND_METADATA_RESEARCH"

    if matches or conflict:
        return {
            "status": "NEEDS_IDENTITY_REVIEW",
            "route": route,
            "basis": reason,
            "verified_reach_uid": None,
            "verified_record_id": None,
            "verified_detail_path": None,
            "requires_human_identity_review": True,
        }
    return {
        "status": "NO_PUBLIC_REACH_MATCH",
        "route": route,
        "basis": reason,
        "verified_reach_uid": None,
        "verified_record_id": None,
        "verified_detail_path": None,
        "requires_human_identity_review": False,
    }


def summarize(entries):
    """Validate all unique source DOIs and return a non-terminal screening score."""
    seen = set()
    totals = Counter()
    basis = Counter()
    for entry in entries:
        doi = entry["doi"]
        if doi in seen:
            raise ValueError("Duplicate DOI in bulk-screening ledger: " + doi)
        seen.add(doi)
        gate = entry["bulk_identity_gate"]
        totals[gate["status"]] += 1
        basis[gate["basis"]] += 1
        if gate["status"] == "VERIFIED_EXISTING_REACH":
            if not all(gate.get(k) for k in ("verified_reach_uid", "verified_record_id", "verified_detail_path")):
                raise ValueError("Verified match missing linked REACH identity: " + doi)
            if len(entry["matches"]) != 1 or gate["verified_reach_uid"] != entry["matches"][0]["reach_uid"]:
                raise ValueError("Verified match not uniquely supported: " + doi)
            if not entry["matches"][0].get("title_hit"):
                raise ValueError("Verified match lacks normalized title agreement: " + doi)
            if gate["requires_human_identity_review"]:
                raise ValueError("Verified identity unexpectedly marked for identity review: " + doi)
        elif gate.get("verified_reach_uid") is not None:
            raise ValueError("Unverified match contains confirmed identity: " + doi)
    return {"counts": dict(sorted(totals.items())),
            "evidence_basis_counts": dict(sorted(basis.items())),
            "source_dois": len(seen)}
