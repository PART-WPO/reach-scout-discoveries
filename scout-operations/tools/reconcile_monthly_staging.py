#!/usr/bin/env python3
"""Reconcile validated, manifest-published monthly proposals back to original DOI cases.

'staged_for_hub_import' is a completed Scout research and validated public-feed
state, NOT evidence of private Discovery Hub ingestion, reviewer decision or REACH
addition. Never infer these states from inbox drafts or raw API records.
"""
import csv
import hashlib
import io
import json
import re
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scout-discoveries" / "tools"))
from supersessions import get_rules

ROOT = Path(__file__).resolve().parents[2]
DOI = re.compile(r"10\.\d{4,9}/[^\s]+", re.I)
REACH_SNAPSHOT = re.compile(r"(?im)^REACH snapshot:\s*([0-9a-f]{64})\s*$")
COHORT = re.compile(r"(?im)^Monthly intake:\s*(20\d{2}-\d{2})\s*$")
VERIFIED = re.compile(r"(?im)^Scout verification:\s*Completed\s*$")
ORIGIN = re.compile(r"(?im)^Intake origin:\s*Monthly API\s*$")
ROUTE = re.compile(r"(?im)^Scout discovery route:\s*Direct API\s*$")
PURPOSE = re.compile(r"(?im)^Scout classification:\s*(NEW CANDIDATE|NEEDS INVESTIGATION)\s*$")


def reconcile(root=ROOT):
    m = json.loads((root / "scout-discoveries/manifest.json").read_text(encoding="utf-8"))
    path = root / "scout-operations/monthly-triage.json"
    ledger = json.loads(path.read_text(encoding="utf-8"))
    bykey = {(e["cohort"], e["identity"]): e for e in ledger["entries"]}
    supersessions = get_rules(root / "scout-discoveries")
    matches = {}
    for b in m["batches"]:
        if not b["id"].startswith(("2026-", "2027-", "2028-", "2029-")) or not any(x in b["id"] for x in ("-monthly-fast-", "-monthly-enriched-")):
            continue
        p = root / b["path"]
        raw = p.read_bytes()
        if hashlib.sha256(raw).hexdigest() != b["sha256"]:
            raise ValueError("Published Scout manifest source changed")
        rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
        if len(rows) != b["record_count"]:
            raise ValueError("Published Scout row count mismatch")
        for row in rows:
            rationale = row.get("Scout Discovery Rationale", "")
            if not (VERIFIED.search(rationale) and ORIGIN.search(rationale) and ROUTE.search(rationale)):
                raise ValueError("Monthly fast-review batch lacks verified direct API route")
            cohort = COHORT.search(rationale)
            snap = REACH_SNAPSHOT.search(rationale)
            classification = PURPOSE.search(rationale)
            doi = row.get("DOI", "").strip().lower()
            if not DOI.fullmatch(doi) or not cohort or not snap or not classification:
                raise ValueError("Published monthly fast-review missing verified identity/provenance")
            key = (cohort.group(1), "doi:" + doi)
            if key in matches:
                raise ValueError("Duplicate staged original DOI identity: " + doi)
            if key not in bykey:
                raise ValueError("Published monthly original missing ledger: " + doi)
            matches[key] = {"scout_batch_path": b["path"],
                            "reach_snapshot": snap.group(1),
                            "evidence_url": row["Evidence URL"],
                            "classification": classification.group(1)}
    changed = 0
    for key, match in matches.items():
        entry = bykey[key]
        if entry["status"] == "staged_for_hub_import":
            if entry.get("scout_batch_path") != match["scout_batch_path"]:
                previous = Path(entry.get("scout_batch_path") or "").stem
                current = Path(match["scout_batch_path"]).stem
                rule = supersessions.get(previous)
                if (not rule or rule.get("replacement_kind") not in
                        {"metadata_refresh", "review_reclassification"}
                        or rule.get("replacement_id") != current):
                    raise ValueError("Already staged original changed without an approved same-DOI supersession")
                # The GitHub manifest validates each exact-sha immutable batch
                # replacement. Preserve ALL private Hub and human decisions.
                entry["scout_batch_path"] = match["scout_batch_path"]
                if rule.get("replacement_kind") == "review_reclassification":
                    if (entry.get("metadata_recovery") or {}).get("status") != "resolved":
                        raise ValueError("Cannot promote monthly case before verified metadata recovery")
                    if match["classification"] != "NEW CANDIDATE":
                        raise ValueError("Unexpected Scout review-ready classification")
                    entry["classification"] = match["classification"]
                entry["research_notes"] = (entry.get("research_notes", "") +
                    "\nVerified public Scout review batch change (" +
                    rule["replacement_kind"] + "): " + previous +
                    " superseded by " + current +
                    " for SAME original DOI. Existing human decisions unchanged; Hub sync is separately verified.")
                changed += 1
            continue
        if entry["status"] in {"already_in_reach", "forwarded_to_hub", "metadata_update_forwarded",
                               "no_action", "human_metadata_needed"}:
            raise ValueError("Published candidate conflicts with existing original disposition")
        entry["status"] = "staged_for_hub_import"
        entry.update(match)
        entry["private_hub_import_verified"] = False
        entry["human_approval_verified"] = False
        entry["public_reach_addition_verified"] = False
        entry["review_feed_state"] = "MANIFEST_PUBLISHED"
        entry["research_notes"] = (entry.get("research_notes", "") +
            "\nValidated Scout review feed contains this exact original DOI in " +
            match["scout_batch_path"] +
            ". Research stage completed for human review. Private Hub import NOT VERIFIED; "
            "no human approval or public REACH update inferred. DOI-seeded related output research continues separately.")
        changed += 1
    if changed:
        path.write_text(json.dumps(ledger, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Reconciled monthly manifest-staged original DOI cases:", changed,
          "; cumulative:", len(matches), "; private Hub import NOT VERIFIED")
    return changed


if __name__ == "__main__":
    reconcile()
