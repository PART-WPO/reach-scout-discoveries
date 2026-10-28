#!/usr/bin/env python3
"""Validate append-only public Scout Discovery batches and build a manifest.

This reads only scout-discoveries/batches/*.csv. A failed validation prevents
manifest publication. No Smartsheet, Library, or REACH catalog interaction.
"""
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BATCHES = ROOT / "batches"
MANIFEST = ROOT / "manifest.json"
REPO = "PART-WPO/reach-scout-discoveries"
SCHEMA = "reach-scout-discovery-feed-v1"
INPUT = [
    "Candidate ID", "Title", "DOI", "Output URL", "Output Type",
    "NOAA Award Number(s)", "WPO Program", "Proposed Project Title",
    "Suggested Parent Project", "Authors / PI", "Principal Investigators",
    "Principal Investigator Email(s)", "Publication Date", "Brief Abstract",
    "IR?", "IR Status", "IR Pub Date", "IR Repository URL",
    "Evidence URL", "Funding Evidence URL", "Scout Discovery Rationale",
    "Existing REACH Match", "Scout Confidence", "Source Run ID",
]
NAME = re.compile(r"\d{4}-\d\d-\d\d-[A-Za-z0-9][A-Za-z0-9_.-]{0,70}\.csv\Z")
MAX_SIZE = 1_900_000


def inspect_batch(p):
    if not NAME.fullmatch(p.name):
        raise ValueError(f"Invalid batch name: {p.name}")
    data = p.read_bytes()
    if not data or len(data) > MAX_SIZE:
        raise ValueError(f"Invalid byte size for {p.name}")
    text = data.decode("utf-8-sig")
    reader = csv.DictReader(text.splitlines(keepends=True))
    if reader.fieldnames != INPUT:
        raise ValueError(f"Unexpected 24-column schema for {p.name}: {reader.fieldnames!r}")
    count, runs = 0, set()
    for line, row in enumerate(reader, 2):
        count += 1
        if None in row or not (row.get("Title") or "").strip():
            raise ValueError(f"Missing title / malformed row: {p.name}:{line}")
        if not (row.get("Evidence URL") or "").strip():
            raise ValueError(f"Missing evidence URL: {p.name}:{line}")
        if (row.get("Principal Investigator Email(s)") or "").strip():
            raise ValueError(f"Do not publicly publish PI emails in {p.name}:{line}")
        if (row.get("Candidate ID") or "").strip():
            raise ValueError(f"Candidate ID must be blank so Hub computes stable identity: {p.name}:{line}")
        for k in ("Evidence URL", "Funding Evidence URL", "Output URL", "IR Repository URL"):
            u = (row.get(k) or "").strip()
            if u and not u.startswith(("https://", "http://")):
                raise ValueError(f"Unsupported external URL in {p.name}:{line} / {k}")
        rationale = row.get("Scout Discovery Rationale") or ""
        run = (row.get("Source Run ID") or "").strip()
        monthly = re.search(r"(?im)^\s*Intake origin:\s*Monthly API\s*$", rationale) or run.startswith("REACH-MONTHLY-API-")
        historical = re.search(r"(?im)^\s*Intake origin:\s*Historical DataCite API Backfill\s*$", rationale) or run.startswith("REACH-HISTORICAL-DATACITE-")
        if monthly or historical:
            if run.startswith(("REACH-MONTHLY-API-", "REACH-HISTORICAL-DATACITE-")):
                raise ValueError(f"Raw monthly API records cannot enter Scout-reviewed batches: {p.name}:{line}")
            if not re.search(r"(?im)^\s*Scout verification:\s*Completed\s*$", rationale):
                raise ValueError(f"Monthly-origin review proposal lacks Scout verification: {p.name}:{line}")
            if monthly and not re.search(r"(?im)^\s*Monthly intake:\s*\d{4}-\d{2}\s*$", rationale):
                raise ValueError(f"Missing monthly cohort in verified proposal: {p.name}:{line}")
            classification = re.search(r"(?im)^\s*Scout classification:\s*(.+?)\s*$", rationale)
            if not classification or not re.search(
                r"\b(?:NEW CANDIDATE|POSSIBLE DUPLICATE|KNOWN DUPLICATE|NEEDS INVESTIGATION|NEEDS EVIDENCE|HOLD|REACH METADATA UPDATE)\b",
                classification.group(1), re.I
            ):
                raise ValueError(f"Missing supported Scout assessment: {p.name}:{line}")
            proof = {
                "REACH snapshot": r"(?im)^\s*REACH snapshot:\s*[0-9a-f]{40,64}\s*$",
                "Sources checked": r"(?im)^\s*Sources checked:\s*[^\r\n]*https://[^\s]+",
                "Funding basis": r"(?im)^\s*Funding basis:\s*[^\r\n]{12,}",
                "Related outputs checked": r"(?im)^\s*Related outputs checked:\s*[^\r\n]{12,}",
            }
            for label, pattern in proof.items():
                if not re.search(pattern, rationale):
                    raise ValueError(f"Monthly Scout review lacks {label}: {p.name}:{line}")
            existing_match = (row.get("Existing REACH Match") or "").strip()
            if not existing_match or existing_match.lower() in ("unchecked", "pending", "unknown", "not assessed", "not checked"):
                raise ValueError(f"Monthly-origin proposal has no completed REACH comparison: {p.name}:{line}")
        if re.search(r"(?im)^\s*Research escalation:\s*Human Metadata Needed\s*$", rationale):
            if not re.search(r"(?im)^\s*Metadata recovery:\s*Exhausted\s*$", rationale):
                raise ValueError(f"Unfinished metadata recovery cannot enter review: {p.name}:{line}")
            if not re.search(r"(?im)^\s*Metadata missing:\s*[^\r\n]{3,}", rationale):
                raise ValueError(f"Missing fields must be listed for human review: {p.name}:{line}")
            if not re.search(r"(?im)^\s*Metadata checks:\s*[^\r\n]{12,}", rationale):
                raise ValueError(f"Recovery sources must be documented: {p.name}:{line}")
            if not re.search(r"(?im)^\s*Scout verification:\s*Completed\s*$", rationale):
                raise ValueError(f"Human metadata referral needs finished Scout research: {p.name}:{line}")
            if not (row.get("DOI") or "").strip() and not (row.get("Output URL") or "").strip():
                raise ValueError(f"Human metadata referral requires a persistent identifier: {p.name}:{line}")
            if not (row.get("Existing REACH Match") or "").strip() or (row.get("Existing REACH Match") or "").strip().lower() in {"unchecked","pending","unknown"}:
                raise ValueError(f"Human metadata referral requires completed REACH comparison: {p.name}:{line}")
        runs.add(run)
    if not 1 <= count <= 3000:
        raise ValueError(f"Invalid record count in {p.name}: {count}")
    return {
        "id": p.stem,
        "path": "scout-discoveries/batches/" + p.name,
        "sha256": hashlib.sha256(data).hexdigest(),
        "record_count": count,
        "source_run_ids": sorted(r for r in runs if r),
    }


def main():
    BATCHES.mkdir(parents=True, exist_ok=True)
    entries = [inspect_batch(p) for p in sorted(BATCHES.glob("*.csv"))]
    if len(entries) > 1500:
        raise ValueError("Manifest batch limit exceeded")
    existing = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    prior = {x["id"]: x["sha256"] for x in existing.get("batches", [])}
    for b in entries:
        if b["id"] in prior and prior[b["id"]] != b["sha256"]:
            raise ValueError(f"Immutable previously published batch changed: {b['id']}")
    same_entries = entries == existing.get("batches", [])
    stamp = (existing.get("generated_at") if same_entries else None) or datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    result = {"schema": SCHEMA, "repository": REPO, "generated_at": stamp,
              "batch_count": len(entries), "candidate_rows": sum(b["record_count"] for b in entries),
              "batches": entries,
              "policy": "PUBLIC SCOUT RESEARCH STAGING ONLY. No human review, approval, insertion or REACH publication is implied."}
    MANIFEST.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Validated Scout feed:", len(entries), "batches /", result["candidate_rows"], "candidate rows")


if __name__ == "__main__":
    main()
