#!/usr/bin/env python3
"""Reconcile Scout discovery-origin metrics from verified manifest CSV bytes.

No inference from research reports, Hub state, or DOI registries. Never writes
the discovery feed manifest. Run only after build_manifest.py succeeds.
"""
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from build_manifest import ROOT

MANIFEST = ROOT / "manifest.json"
ROLLUP = ROOT.parent / "scout-operations" / "discovery-origin-rollup.json"
ROUTES = ("Direct API", "API-seeded expansion", "Independent discovery",
          "Metadata correction", "Unclassified explicit",
          "Unclassified legacy (route missing)")
ROUTE_LINE = re.compile(r"(?im)^\s*Scout discovery route:\s*([^\r\n]+)")


# Research method and reviewer action are independent dimensions. Metadata correction
# is a finding purpose, not an assumption about the original search pathway.
LEGACY_LEDGER = ROOT.parent / "scout-operations" / "legacy-provenance-backfill.json"
METHODS = ("Direct API", "API-seeded expansion", "Independent discovery", "Unclassified")
PURPOSES = ("new_output_review", "metadata_correction", "possible_duplicate_review",
            "existing_duplicate_review", "needs_investigation", "unclassified_purpose")
CLASS_LINE = re.compile(r"(?im)^\s*Scout classification:\s*([^\r\n]+)")
ORIGIN_METHOD_LINE = re.compile(r"(?im)^\s*Scout origin method:\s*([^\r\n]+)")
FINDING_PURPOSE_LINE = re.compile(r"(?im)^\s*Scout finding purpose:\s*([^\r\n]+)")


def _original_purpose(rationale):
    match = CLASS_LINE.search(rationale)
    label = (match.group(1).strip() if match else rationale.splitlines()[0].strip() if rationale else "").upper()
    if "REACH METADATA UPDATE" in label:
        return "metadata_correction"
    if "POSSIBLE DUPLICATE" in label:
        return "possible_duplicate_review"
    if "KNOWN DUPLICATE" in label:
        return "existing_duplicate_review"
    if "NEEDS INVESTIGATION" in label or "NEEDS EVIDENCE" in label:
        return "needs_investigation"
    if "NEW CANDIDATE" in label or label.startswith("A / NEW"):
        return "new_output_review"
    return "unclassified_purpose"


def enrich_from_legacy(manifest, ledger):
    """Strictly overlay verified research provenance, never modify staged files.

    A legacy annotation is valid only for a row from the same immutable manifest
    batch digest and exact identity/run. Failed checks stop metrics publication.
    """
    if ledger and ledger.get("schema") != "reach-scout-legacy-provenance-backfill-v1":
        raise ValueError("Unknown legacy provenance ledger schema")
    entries = (ledger or {}).get("entries", [])
    by_key = {}
    for e in entries:
        key = e["record_key"]
        if key in by_key:
            raise ValueError(f"Duplicate provenance ledger record_key: {key}")
        if e["discovery_method"] not in METHODS or e["finding_purpose"] not in PURPOSES:
            raise ValueError(f"Invalid method/purpose in {key}")
        if e["discovery_method_confidence"] not in ("High", "Medium", "Low"):
            raise ValueError(f"Unrecognized confidence in {key}")
        if e["discovery_method_confidence"] != "High" and e["discovery_method"] != "Unclassified":
            # Provisional routes may be recorded as suggestions but must not enter
            # independently verified attribution metrics.
            raise ValueError(f"Unverified proposed route must be Unclassified: {key}")
        by_key[key] = e

    methods = {m: 0 for m in METHODS}
    purposes = {p: 0 for p in PURPOSES}
    raw_classified = 0
    backfilled = 0
    unresolved_legacy = 0
    seen_keys = set()
    legacy_cohorts = {}
    verified_new_output_non_direct = 0
    for batch in manifest["batches"]:
        path = ROOT.parent / batch["path"]
        with path.open("r", newline="", encoding="utf-8-sig") as stream:
            rows = list(csv.DictReader(stream))
        for index, row in enumerate(rows, start=1):
            key = batch["id"] + "#" + str(index)
            rationale = row.get("Scout Discovery Rationale") or ""
            raw_route = ROUTE_LINE.search(rationale)
            if raw_route:
                if key in by_key:
                    raise ValueError(f"Refusing ledger override of explicit source route: {key}")
                route = raw_route.group(1).strip()
                method = route if route in METHODS else "Unclassified"
                purpose = _original_purpose(rationale)
                if route == "Metadata correction":
                    purpose = "metadata_correction"
                stated_method = ORIGIN_METHOD_LINE.search(rationale)
                if stated_method:
                    value = stated_method.group(1).strip()
                    if value not in METHODS:
                        raise ValueError(f"Invalid explicit original discovery method: {key}")
                    if route in METHODS and value != route:
                        raise ValueError(f"Disagreement between discovery route and original method: {key}")
                    method = value
                stated_purpose = FINDING_PURPOSE_LINE.search(rationale)
                if stated_purpose:
                    value = stated_purpose.group(1).strip()
                    if value not in PURPOSES or value != purpose:
                        raise ValueError(f"Invalid/conflicting explicit finding purpose: {key}")
                    purpose = value
                raw_classified += 1
            else:
                entry = by_key.get(key)
                if entry is not None and (ORIGIN_METHOD_LINE.search(rationale) or
                                          FINDING_PURPOSE_LINE.search(rationale)):
                    raise ValueError(f"Refusing backfill of already explicit method or purpose: {key}")
                if entry is None:
                    method = "Unclassified"
                    purpose = _original_purpose(rationale)
                    unresolved_legacy += 1
                else:
                    if (entry["source_batch_id"] != batch["id"] or
                        entry["source_batch_path"] != batch["path"] or
                        entry["source_batch_sha256"] != batch["sha256"] or
                        entry["source_data_row"] != index or
                        entry["source_run_id"] != row["Source Run ID"] or
                        entry["output_title"] != row["Title"] or
                        entry["output_identity"].strip().lower() !=
                            (row.get("DOI") or row.get("Output URL") or "").strip().lower()):
                        raise ValueError(f"Provenance source identity/digest mismatch: {key}")
                    method = entry["discovery_method"]
                    purpose = entry["finding_purpose"]
                    cohort = entry["cohort"]
                    legacy_cohorts[cohort] = legacy_cohorts.get(cohort, 0) + 1
                    seen_keys.add(key)
                    if method == "Unclassified":
                        unresolved_legacy += 1
                    else:
                        backfilled += 1
            methods[method] += 1
            purposes[purpose] += 1
            if method in ("API-seeded expansion", "Independent discovery") and purpose == "new_output_review":
                verified_new_output_non_direct += 1

    if seen_keys != set(by_key):
        raise ValueError(f"Provenance entries not in manifest: {sorted(set(by_key) - seen_keys)}")
    if sum(methods.values()) != manifest["candidate_rows"] or sum(purposes.values()) != manifest["candidate_rows"]:
        raise ValueError("Discovery method and finding purpose metrics must reconcile with manifest")
    return {
        "source": "SHA-256-verified published CSVs plus exact-row legacy provenance ledger",
        "discovery_method_counts": methods,
        "finding_purpose_counts": purposes,
        "legacy_record_count": len(by_key),
        "legacy_method_backfilled": backfilled,
        "legacy_still_unclassified": unresolved_legacy,
        "legacy_cohort_counts": legacy_cohorts,
        "modern_explicit_route_rows": raw_classified,
        "beyond_direct_api_new_output_review_proposals": verified_new_output_non_direct,
        "private_hub_imports": "NOT_VERIFIED",
        "human_confirmed_recoveries": "NOT_VERIFIED",
        "public_reach_additions": "NOT_VERIFIED",
        "interpretation": "Method describes original discovery; purpose describes requested reviewer action. Counts are staged proposals, not approvals. Metadata corrections and duplicates are NOT new public outputs.",
    }


def summarize(manifest):
    if manifest.get("schema") != "reach-scout-discovery-feed-v1":
        raise ValueError("Unrecognized manifest schema")
    counts = {route: 0 for route in ROUTES}
    checked = []
    identities = set()
    row_count = 0
    for batch in manifest["batches"]:
        key = batch["id"]
        if key in identities:
            raise ValueError(f"Repeated manifest batch ID: {key}")
        identities.add(key)
        rel = batch["path"]
        if not rel.startswith("scout-discoveries/batches/") or not rel.endswith(".csv"):
            raise ValueError(f"Unexpected batch path: {rel}")
        path = ROOT.parent / rel
        data = path.read_bytes()
        actual = hashlib.sha256(data).hexdigest()
        if actual != batch["sha256"]:
            raise ValueError(f"SHA-256 mismatch for {key}: {actual} != {batch['sha256']}")
        with path.open("r", newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
        if len(rows) != batch["record_count"]:
            raise ValueError(f"Record count mismatch for {key}")
        found_runs = sorted(set((row.get("Source Run ID") or "").strip()
                                for row in rows if (row.get("Source Run ID") or "").strip()))
        if found_runs != batch["source_run_ids"]:
            raise ValueError(f"Source Run IDs differ for {key}")
        row_count += len(rows)
        for row in rows:
            if None in row:
                raise ValueError(f"Malformed CSV row in {key}")
            rationale = row.get("Scout Discovery Rationale") or ""
            matched = ROUTE_LINE.search(rationale)
            if not matched:
                bucket = "Unclassified legacy (route missing)"
            elif matched.group(1).strip().lower() == "unclassified":
                bucket = "Unclassified explicit"
            else:
                expected = [route for route in ROUTES[:4]
                            if route.lower() == matched.group(1).strip().lower()]
                if not expected:
                    raise ValueError(f"Unrecognized route in {key}: {matched.group(1)!r}")
                bucket = expected[0]
            counts[bucket] += 1
        checked.append({"id": key, "sha256": actual, "records": len(rows)})
    if row_count != manifest["candidate_rows"] or len(checked) != manifest["batch_count"]:
        raise ValueError("Manifest aggregate counts disagree with fully verified CSVs")
    if sum(counts.values()) != row_count:
        raise ValueError("Route classification doesn't reconcile")
    return counts, checked, row_count

def main():
    payload = MANIFEST.read_bytes()
    manifest = json.loads(payload)
    counts, checked, count = summarize(manifest)
    legacy_bytes = LEGACY_LEDGER.read_bytes() if LEGACY_LEDGER.exists() else None
    ledger = json.loads(legacy_bytes) if legacy_bytes else None
    effective = enrich_from_legacy(manifest, ledger)
    old = json.loads(ROLLUP.read_text(encoding="utf-8")) if ROLLUP.exists() else {}
    generated_at = manifest["generated_at"]
    previous_baseline = old.get("public_reach", {})
    latest = manifest["batches"][-1] if manifest["batches"] else None
    report = {
        "schema": "reach-scout-discovery-origin-rollup-v1",
        "snapshot_date": generated_at[:10],
        "source": "Automated SHA-256-verified scout-discoveries/manifest.json and every published batch",
        "source_manifest_sha256": hashlib.sha256(payload).hexdigest(),
        "source_manifest_generated_at": generated_at,
        "batch_count": len(checked),
        "staged_review_rows": count,
        "manifest_rows_verified": True,
        "route_counts": counts,
        "raw_route_counts": counts,
        "effective_discovery_method_counts": effective["discovery_method_counts"],
        "effective_finding_purpose_counts": effective["finding_purpose_counts"],
        "legacy_provenance": {
            "ledger_path": "scout-operations/legacy-provenance-backfill.json" if legacy_bytes else None,
            "ledger_sha256": hashlib.sha256(legacy_bytes).hexdigest() if legacy_bytes else None,
            "annotated_legacy_records": effective["legacy_record_count"],
            "verified_methods_recovered": effective["legacy_method_backfilled"],
            "remaining_unclassified_legacy": effective["legacy_still_unclassified"],
            "cohorts": effective["legacy_cohort_counts"],
            "validation": "EXACT_MANIFEST_BATCH_SHA_AND_ROW_IDENTITY_VERIFIED",
        },
        "attribution_metrics": {
            "direct_api_staged": counts["Direct API"],
            "api_seeded_expansion_staged": counts["API-seeded expansion"],
            "independent_discovery_staged": counts["Independent discovery"],
            "metadata_correction_staged": counts["Metadata correction"],
            "unclassified_staged": counts["Unclassified explicit"] + counts["Unclassified legacy (route missing)"],
            "beyond_direct_api_staged_review_candidates": effective["beyond_direct_api_new_output_review_proposals"],
            "previous_raw_routed_beyond_direct_api_staged": counts["API-seeded expansion"] + counts["Independent discovery"],
            "effective_independent_discovery_method_staged": effective["discovery_method_counts"]["Independent discovery"],
            "effective_api_seeded_expansion_method_staged": effective["discovery_method_counts"]["API-seeded expansion"],
            "effective_direct_api_method_staged": effective["discovery_method_counts"]["Direct API"],
            "effective_unclassified_method_staged": effective["discovery_method_counts"]["Unclassified"],
            "effective_metadata_correction_purpose_staged": effective["finding_purpose_counts"]["metadata_correction"],
            "human_confirmed_attribution_recoveries": "NOT_VERIFIED",
            "private_hub_imports": "NOT_VERIFIED",
            "verified_public_reach_additions": "NOT_VERIFIED",
            "interpretation": "Staged proposals only; effective counts use separate original discovery method and finding purpose. Beyond-direct metric counts only method-confirmed new-output review proposals, not duplicates or corrections. Human eligibility, private Hub import and public REACH additions are not verified.",
        },
        "public_reach": previous_baseline,
        "human_review_status": f"NOT_VERIFIED; {count} staged proposals are not approvals or public REACH additions.",
        "latest_verified_run": ({
            "batch_id": latest["id"],
            "source_run_ids": latest["source_run_ids"],
            "record_count": latest["record_count"],
            "manifest_verified": True,
            "human_hub_import": "NOT_VERIFIED",
        } if latest else None),
        "note": ("route_counts and raw_route_counts preserve literal source-CSV route buckets for historical compatibility; "
                 "effective_discovery_method_counts and effective_finding_purpose_counts use verified source-identity-matched legacy annotations. "
                 "A metadata correction is a finding purpose, not a discovery method. "
                 "Never infer an undocumented route or human approval; prior public REACH baseline is not refreshed."),
    }
    for key in ("overnight_2026_10_28_2029ET_to_2026_10_29_0734ET", "audit_backfills"):
        if key in old:
            report[key] = old[key]
    ROLLUP.parent.mkdir(parents=True, exist_ok=True)
    output = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    ROLLUP.write_text(output, encoding="utf-8")
    print(f"VERIFIED ATTRIBUTION ROLLUP: {count} candidates / {len(checked)} batches: {counts}")

if __name__ == "__main__":
    main()
