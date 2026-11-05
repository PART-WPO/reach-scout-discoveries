#!/usr/bin/env python3
"""Scout 2.0: evidence-only relevance gate for *research expansion*, not approvals.

Do not confuse a permanently preserved DOI lead with a mandate to explore all
of its references. Never change original dispositions, historical seed status,
human review, public Scout staging or the public REACH. A negative scope check
is a reversible priority hold, never proof an output is unrelated.
"""
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROUTING = "scout-operations/historical-crossref-screening/actionable-routing.json"
TARGET = "scout-operations/expansion-relevance-priority.json"
BIOMEDICAL_AUDIT = "scout-operations/historical-crossref-phase2/2026-11-05-1125ET-biomedical-immutable-source-attribution-audit.json"
BIOMEDICAL_SOURCES = "scout-operations/historical-crossref-phase2/2026-11-05-1026ET-biomedical-award-attribution-holds.json"
MONTHLY = "scout-operations/monthly-expansion-leads.json"
INDEPENDENT = "scout-operations/independent-discovery-leads.json"

ACTIVE = "PRIORITIZE_VERIFIED_WPO_SEED"
SCOPE_CHECK = "VERIFY_WPO_PROJECT_SCOPE_FIRST"
SOFT_DEFER = "DEFER_UNTIL_NEW_PROJECT_EVIDENCE"


def load(root, relative):
    p = root / relative
    return json.loads(p.read_text(encoding="utf-8")), hashlib.sha256(p.read_bytes()).hexdigest()


def norm_doi(value):
    x = str(value or "").strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "https://dx.doi.org/", "doi:"):
        if x.startswith(prefix):
            x = x[len(prefix):]
    if not x.startswith("10.") or "/" not in x or any(k.isspace() for k in x):
        raise ValueError("Invalid DOI identity: " + str(value))
    return x


def audited_soft_holds(root):
    """Recognize two already documented *uncertain* WPO-source anomalies.

    Require two independent audited files, specific structured dispositions,
    >=2 actual public DOI-specific sources. They are not 'proven unrelated'.
    Other or incomplete cases do not inherit these deferrals.
    """
    audit, audit_sha = load(root, BIOMEDICAL_AUDIT)
    sources, sources_sha = load(root, BIOMEDICAL_SOURCES)
    if audit.get("schema") != "reach-scout-append-only-research-evidence-v1" or audit.get("lane") != "historical_original_source_provenance_audit":
        raise ValueError("Unexpected primary-award provenance audit schema")
    if sources.get("schema") != "reach-scout-append-only-research-evidence-v1" or sources.get("lane") != "historical_original_funding_attribution":
        raise ValueError("Unexpected second-source funding audit schema")
    if audit.get("source_manifest") != "api-discoveries/historical-crossref/manifest.json":
        raise ValueError("Audit source manifest not historical Crossref")
    a = {norm_doi(c["doi"]): c for c in audit["cases"]}
    b = {norm_doi(c["doi"]): c for c in sources["cases"]}
    if set(a) != set(b) or not a:
        raise ValueError("Source/independent biomedical audit DOI mismatch")
    result = {}
    for d in sorted(a):
        first, second = a[d], b[d]
        if (first.get("original_award_column") != "UNK"
            or first.get("disposition") != "BOUNDED_HOLD_SOURCE_AWARD_UNVERIFIED"
            or second.get("decision") not in {
                "BOUNDED_HOLD_UNRELATED_PROJECT_EVIDENCE",
                "BOUNDED_HOLD_PROJECT_ATTRIBUTION_NOT_ESTABLISHED"}):
            # Unknown or inconsistent evidence MUST NOT be used for a negative.
            continue
        urls = sorted(set(x.get("url", "") for x in second.get("sources", [])
                          if isinstance(x, dict) and str(x.get("url", "")).startswith("https://")))
        if len(urls) < 2 or not second.get("uncertainty"):
            continue
        result[d] = {
            "note": "Crossref source award identity unverified and independent sources do not establish the proposed WPO project; not a final ineligibility finding.",
            "evidence_urls": urls,
            "audit_files": [
                {"path": BIOMEDICAL_AUDIT, "sha256": audit_sha},
                {"path": BIOMEDICAL_SOURCES, "sha256": sources_sha},
            ],
            "reopen_trigger": "New exact primary SPARK Award Number(s), independently corroborated same-project deliverable, or verified human direction",
        }
    return result, {BIOMEDICAL_AUDIT: audit_sha, BIOMEDICAL_SOURCES: sources_sha}


def classify_seed(entry, holds):
    d = norm_doi(entry["doi"])
    gate = entry.get("bulk_identity_gate") or {}
    if gate.get("status") == "VERIFIED_EXISTING_REACH":
        if entry.get("outcome") != "CONFIRMED_IN_REACH" or not all(gate.get(x) for x in
            ("verified_reach_uid", "verified_record_id", "verified_detail_path")):
            raise ValueError("Unverified REACH identity cannot justify WPO relevance: " + d)
        return {
            "priority": ACTIVE,
            "reason": "Verified unique identity in the existing WPO REACH catalog",
            "evidence_reach_uid": gate["verified_reach_uid"],
            "required_next_action": "Explore relevant project-specific datasets, code and publications if not already documented; check each distinct related output independently",
            "audit": [],
        }
    if d in holds:
        return {
            "priority": SOFT_DEFER,
            "reason": holds[d]["note"],
            "evidence_reach_uid": None,
            "required_next_action": "Do not traverse generic references or datasets until new positive WPO project evidence appears; keep DOI lead for reconsideration",
            "audit": holds[d]["audit_files"],
            "reopen_trigger": holds[d]["reopen_trigger"],
            "evidence_urls": holds[d]["evidence_urls"],
        }
    return {
        "priority": SCOPE_CHECK,
        "reason": ("Ambiguous REACH identity requires bounded version/project check"
                   if gate.get("status") == "NEEDS_IDENTITY_REVIEW"
                   else "Public REACH index-negative original needs a WPO project relevance check before related-output exploration"),
        "evidence_reach_uid": None,
        "required_next_action": "First verify primary SPARK Award Number(s) and project-specific evidence, or confirm existing WPO identity; do not automatically expand from topical similarity or blanket awards",
        "audit": [],
    }


def classify_related_lead(entry):
    """Preview ONLY: never reopen/remove staged reviewer submissions or alter lead."""
    d = norm_doi(entry["identity"])
    status = str(entry.get("status") or "")
    if status == "already_in_reach":
        priority, action = "EXISTING_REACH_LEAD_RECORDED", "No duplicate new-output review; keep its original seed association"
    elif status in ("staged_for_human_review", "pending_human_intake",
                    "RESEARCH_COMPLETE_HUMAN_INTAKE", "RESEARCH_COMPLETE_HUMAN_INTAKE_PENDING_PRIVATE_UI"):
        priority, action = "PRESERVE_CURRENT_HUMAN_HANDOFF", "Existing public/private staging status unchanged; do not restage"
    elif status == "FOLLOWUP_CLOSED_NO_DEMONSTRATED_WPO_PROJECT_BRIDGE":
        priority, action = SOFT_DEFER, "Reopen only on new DOI-specific WPO project evidence or explicit human request"
    elif entry.get("project_funding_verified") is True and (
            entry.get("funding_assessment") or {}).get("contradictory_project_evidence_found") is not True:
        priority, action = "PROJECT_LINKED_LEAD_PRIORITY", "Complete normal identity/metadata and reviewer preflight independently"
    else:
        priority, action = SCOPE_CHECK, "Verify same-project WPO connection before additional related-output exploration"
    return {"doi":d, "current_recorded_status":status, "priority":priority,
            "required_next_action":action, "human_decision_changed":False,
            "review_feed_modified":False}


def build(root=ROOT):
    routing, routing_sha = load(root, ROUTING)
    manifest, manifest_sha = load(root, "api-discoveries/historical-crossref/manifest.json")
    reach, reach_sha = load(root, "scout-operations/reach-comparison-cache/comparison-index.json")
    ir, ir_sha = load(root, "scout-operations/noaa-ir/manifest.json")
    monthly, monthly_sha = load(root, MONTHLY)
    independent, independent_sha = load(root, INDEPENDENT)
    if (manifest_sha != routing.get("source_manifest_sha256")
        or reach_sha != routing.get("reach_cache_sha256")
        or ir_sha != routing.get("noaa_ir_manifest_sha256")
        or len(routing.get("entries", [])) != routing.get("total")
        or len({norm_doi(e["doi"]) for e in routing["entries"]}) != routing["total"]
        or routing.get("total") != manifest.get("candidate_rows")):
        raise ValueError("Stale, incomplete or inconsistent Crossref/REACH/NOAA IR source evidence")
    if sum(routing.get("counts", {}).values()) != routing["total"]:
        raise ValueError("Historical routing classifications incomplete")
    holds, audit_shas = audited_soft_holds(root)
    source_dois = {norm_doi(e["doi"]) for e in routing["entries"]}
    if not set(holds).issubset(source_dois):
        raise ValueError("Audited scope evidence is not part of Crossref source cohort")
    rows = []
    for e in routing["entries"]:
        decision = classify_seed(e, holds)
        rows.append({
            "doi": norm_doi(e["doi"]), "original_screening_outcome": e["outcome"],
            "priority": decision["priority"], "reason": decision["reason"],
            "next_action": decision["required_next_action"],
            "verified_reach_uid": decision["evidence_reach_uid"],
            "audit_sources": decision["audit"],
            "reopen_trigger": decision.get("reopen_trigger"),
            "evidence_urls": decision.get("evidence_urls", []),
            "source_seed_expansion_status": "UNMODIFIED",
            "source_original_status": "UNMODIFIED",
            "private_reviewer_decision": "NOT_VERIFIED",
        })
    counts = dict(sorted(Counter(r["priority"] for r in rows).items()))
    monthly_rows = [classify_related_lead(e) for e in monthly["entries"]]
    independent_rows = [classify_related_lead(e) for e in independent["entries"]]
    for cohort, case_rows in (("monthly", monthly_rows), ("independent", independent_rows)):
        if len({r["doi"] for r in case_rows}) != len(case_rows):
            raise ValueError("Duplicate "+cohort+" expansion/research lead identity")
    return {
        "schema": "reach-scout-expansion-relevance-priority-v1",
        "source_routing_sha256": routing_sha,
        "source_crossref_manifest_sha256": manifest_sha,
        "source_reach_cache_sha256": reach_sha,
        "source_ir_manifest_sha256": ir_sha,
        "other_source_sha256": {"monthly_expansion_leads": monthly_sha,
                                "independent_discovery_leads": independent_sha,
                                "audited_scope_files": audit_shas},
        "historical_crossref": {
            "total_preserved_seeds": routing["total"],
            "counts": counts,
            "note": "Research prioritization only. All historical seed DOI records and their original terminal/reviewer statuses remain unchanged. Deferred means reversible scope hold, NOT permanent ineligibility or completed expansion.",
            "entries": rows,
        },
        "other_discovery_sources": {
            "monthly_expansion": {
                "count": len(monthly_rows),
                "priority_counts": dict(sorted(Counter(x["priority"] for x in monthly_rows).items())),
                "entries": monthly_rows,
            },
            "independent_research": {
                "count": len(independent_rows),
                "priority_counts": dict(sorted(Counter(x["priority"] for x in independent_rows).items())),
                "entries": independent_rows,
            },
            "note": "Read-only relevance view of existing discovered leads, not new outputs or changes to previously staged human referrals.",
        },
        "publication_or_review_changes": 0,
        "seed_expansion_closures": 0,
        "decision_rule": "WPO catalog confirmation prioritizes project-specific exploration; uncertain primary-award/project bridges require scope verification; well-documented source-attribution anomalies may be deferred until new evidence. Never infer final ineligibility from absent evidence.",
    }


def main():
    report = build()
    p = ROOT / TARGET
    rendered = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if not p.exists() or p.read_text(encoding="utf-8") != rendered:
        p.write_text(rendered, encoding="utf-8")
    print(json.dumps({
        "preserved": report["historical_crossref"]["total_preserved_seeds"],
        "historical_priorities": report["historical_crossref"]["counts"],
        "monthly": report["other_discovery_sources"]["monthly_expansion"]["priority_counts"],
        "independent": report["other_discovery_sources"]["independent_research"]["priority_counts"],
    }, indent=2))


if __name__ == "__main__":
    main()
