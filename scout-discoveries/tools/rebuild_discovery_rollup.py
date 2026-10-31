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
        "attribution_metrics": {
            "direct_api_staged": counts["Direct API"],
            "api_seeded_expansion_staged": counts["API-seeded expansion"],
            "independent_discovery_staged": counts["Independent discovery"],
            "metadata_correction_staged": counts["Metadata correction"],
            "unclassified_staged": counts["Unclassified explicit"] + counts["Unclassified legacy (route missing)"],
            "beyond_direct_api_staged_review_candidates": counts["API-seeded expansion"] + counts["Independent discovery"],
            "human_confirmed_attribution_recoveries": "NOT_VERIFIED",
            "private_hub_imports": "NOT_VERIFIED",
            "verified_public_reach_additions": "NOT_VERIFIED",
            "interpretation": "Staged proposals only. Research route does not prove human eligibility or a published outcome.",
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
        "note": ("Route-missing legacy rows remain UNCLASSIFIED, never inferred as independent. "
                 "All counts are rebuilt from published CSVs after successful manifest validation. "
                 "Prior public REACH baseline is retained but not independently refreshed."),
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
