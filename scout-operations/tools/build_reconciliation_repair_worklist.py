#!/usr/bin/env python3
"""Produce source-backed work orders for unresolved historical terminal claims.

Do not invent missing source fields, alter original research status, reconstruct
human decisions, treat retired feed proposals as active, or accept a presumed
private Hub import. This is a decision-support report, not research itself.
"""
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "scout-operations/reconciliation-repair-worklist.json"
DATACITE = "scout-operations/historical-reconciliation-exceptions.json"
CROSSREF = "scout-operations/historical-crossref-reconciliation-exceptions.json"
SUPERSESSIONS = "scout-discoveries/supersessions.json"
ROUTING = "scout-operations/historical-crossref-screening/actionable-routing.json"
FEED = "scout-discoveries/manifest.json"

def read(rel, root=ROOT):
    p = root / rel
    blob = p.read_bytes()
    return json.loads(blob), hashlib.sha256(blob).hexdigest()

def make(root=ROOT):
    datacite, dc_sha = read(DATACITE,root)
    crossref, cr_sha = read(CROSSREF,root)
    supersessions, su_sha = read(SUPERSESSIONS,root)
    routing, ro_sha = read(ROUTING,root)
    feed, feed_sha = read(FEED,root)
    if datacite["schema"] != "reach-scout-reconciliation-exceptions-v1" or crossref["schema"] != "reach-scout-reconciliation-exceptions-v1":
        raise ValueError("Unexpected historical exceptions schema")
    if datacite["declared_unverified_terminal_count"] != len(datacite["exceptions"]) or crossref["declared_unverified_terminal_count"] != len(crossref["exceptions"]):
        raise ValueError("Exception count mismatch")
    source, source_sha = read("api-discoveries/historical-crossref/manifest.json",root)
    if crossref["source_manifest_sha256"] != source_sha or routing["source_manifest_sha256"] != source_sha:
        raise ValueError("Crossref exception cohort/routing not source-verified")
    datacite_source, dc_source_sha = read("api-discoveries/historical/manifest.json",root)
    if datacite["source_manifest_sha256"] != dc_source_sha:
        raise ValueError("DataCite exception cohort changed")
    excluded = {}
    for batch_id, obj in supersessions.get("superseded_batches",{}).items():
        for doi in obj.get("excluded_dois", []):
            excluded.setdefault(doi.lower(),[]).append({"original_batch":batch_id,
                "replacement_batch":obj.get("replacement_id"),
                "reason":obj.get("reason")})
    active_batches = {b["path"] for b in feed.get("batches",[])}
    routes = {e["doi"]:e for e in routing["entries"]}
    rows=[]
    for cohort, report in (("historical_datacite",datacite),("historical_crossref",crossref)):
        for e in report["exceptions"]:
            identity=e["identity"]
            if not identity.startswith("doi:"):
                raise ValueError("Unsafe original identity: "+identity)
            doi=identity[4:]
            reasons=e["missing_evidence_requirements"]
            status=e["declared_status"]
            if not reasons:
                raise ValueError("An exception with no missing requirement cannot be actioned safely")
            if cohort=="historical_datacite" and status=="metadata_update_forwarded":
                if "active_scout_feed_batch" not in reasons:
                    raise ValueError("Unexpected DataCite retired-proposal explanation")
                if doi in excluded:
                    priority="RETIRED_PUBLIC_PROPOSAL_VERIFY_PRIVATE_REVIEW_HISTORY"
                    action=("The public batch was superseded and the proposal excluded. "
                            "Do NOT reinstate it or count an active handoff. A human checks "
                            "whether an old private Hub card exists and retires it if appropriate; "
                            "reopen funding only with independently verified primary SPARK WPO award evidence.")
                else:
                    priority="MISSING_ACTIVE_PUBLIC_FEED_VERIFY_HISTORICAL_DECISION"
                    action=("Find the exact source batch and immutable reviewer history; "
                            "determine whether the proposal was superseded or never staged. "
                            "Do not create a duplicate or invent a private Hub import.")
            elif cohort=="historical_crossref":
                r=routes.get(doi)
                if r is None:
                    raise ValueError("Crossref missing from checked source routing: "+doi)
                priority=("REACH_IDENTITY_EVIDENCE_REPAIR" if r["outcome"]=="CONFIRMED_IN_REACH"
                          else "FUNDING_OR_SCOPE_AND_SNAPSHOT_REPAIR")
                action=("Recheck exact primary project award, DOI-specific public research evidence, "
                        "the current verified REACH comparison SHA and any related-output disposition. "
                        "Record new sourced evidence; do not fill audit fields with placeholders, "
                        "auto-approve an existing no-action decision or mark expansion complete.")
            else:
                raise ValueError("Unrecognized historical exception: "+identity)
            rows.append({"identity":identity,"cohort":cohort,"original_declared_status":status,
                "priority":priority,"missing_requirements":reasons,"repair_instruction":action,
                "public_batch_exclusion_history":excluded.get(doi,[]),
                "related_source_routing":routes[doi]["outcome"] if cohort=="historical_crossref" else None,
                "private_hub_outcome":"NOT_VERIFIED",
                "human_decision_changed":False,"original_terminal_status_changed":False,
                "evidence_verified_and_terminal_reconciled":False,
                "ready_to_auto_close":False})
    counts=Counter(x["priority"] for x in rows)
    return {"schema":"reach-scout-reconciliation-repair-worklist-v1",
        "sources_sha256":{"historical_datacite_exceptions":dc_sha,
                          "historical_crossref_exceptions":cr_sha,
                          "historical_datacite_manifest":dc_source_sha,
                          "historical_crossref_manifest":source_sha,
                          "scout_supersessions":su_sha,
                          "scout_active_manifest":feed_sha,
                          "crossref_routing":ro_sha},
        "unverified_terminal_cases":len(rows),
        "repair_priority_counts":dict(sorted(counts.items())),
        "cases":rows,
        "safety":"No declared status, historical source, human decision or seed-expansion disposition changed. Only independently verified new evidence and the original completion validator may resolve a claim."}

def main():
    data=make()
    rendered=json.dumps(data,indent=2,ensure_ascii=False)+"\n"
    if not OUT.exists() or OUT.read_text(encoding="utf-8")!=rendered:
        OUT.write_text(rendered,encoding="utf-8")
    print(json.dumps({"unverified_terminal_cases":data["unverified_terminal_cases"],
                      "priority_counts":data["repair_priority_counts"]},indent=2))

if __name__=="__main__":
    main()
