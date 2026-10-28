#!/usr/bin/env python3
"""Build public, append-only monthly API intake manifest for Discovery Hub."""
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
SCHEMA = "reach-monthly-api-discovery-feed-v1"
HEADERS = [
    "Candidate ID", "Title", "DOI", "Output URL", "Output Type",
    "NOAA Award Number(s)", "WPO Program", "Proposed Project Title",
    "Suggested Parent Project", "Authors / PI", "Principal Investigators",
    "Principal Investigator Email(s)", "Publication Date", "Brief Abstract",
    "IR?", "IR Status", "IR Pub Date", "IR Repository URL",
    "Evidence URL", "Funding Evidence URL", "Scout Discovery Rationale",
    "Existing REACH Match", "Scout Confidence", "Source Run ID",
]
FILENAME = re.compile(r"\d{4}-\d\d-\d\d-[A-Za-z0-9][A-Za-z0-9_.-]{0,70}\.csv\Z")
MAX_SIZE = 1_900_000

def inspect_batch(path):
    if not FILENAME.fullmatch(path.name):
        raise ValueError("Invalid monthly batch filename: " + path.name)
    data = path.read_bytes()
    if not data or len(data) > MAX_SIZE:
        raise ValueError("Invalid monthly batch size: " + path.name)
    reader = csv.DictReader(data.decode("utf-8-sig").splitlines(keepends=True))
    if reader.fieldnames != HEADERS:
        raise ValueError("Monthly feed must use the exact 24-column Discovery Hub schema: " + path.name)
    runs = set()
    count = 0
    for line, row in enumerate(reader, 2):
        count += 1
        if None in row or not (row.get("Title") or "").strip():
            raise ValueError(f"Malformed title/column count: {path.name}:{line}")
        if (row.get("Candidate ID") or "").strip() or (row.get("Principal Investigator Email(s)") or "").strip():
            raise ValueError(f"No internal IDs or PI emails may enter public staging: {path.name}:{line}")
        run = (row.get("Source Run ID") or "").strip()
        if not run.startswith("REACH-MONTHLY-API-"):
            raise ValueError(f"Not a monthly API Source Run ID: {path.name}:{line}")
        rationale = row.get("Scout Discovery Rationale") or ""
        if "Intake origin: Monthly API" not in rationale:
            raise ValueError(f"Missing monthly intake marker: {path.name}:{line}")
        if not (row.get("Evidence URL") or "").startswith("https://"):
            raise ValueError(f"Missing public HTTPS evidence URL: {path.name}:{line}")
        for field in ("Output URL", "Funding Evidence URL", "IR Repository URL"):
            value = (row.get(field) or "").strip()
            if value and not value.startswith("https://"):
                raise ValueError(f"Invalid public URL in {field}: {path.name}:{line}")
        runs.add(run)
    if not 1 <= count <= 3000:
        raise ValueError("Monthly batches must have 1-3000 rows: " + path.name)
    return {
        "id": path.stem,
        "path": "api-discoveries/batches/" + path.name,
        "sha256": hashlib.sha256(data).hexdigest(),
        "record_count": count,
        "source_run_ids": sorted(runs),
        "source": "Monthly API",
    }

def main():
    BATCHES.mkdir(parents=True, exist_ok=True)
    entries = [inspect_batch(p) for p in sorted(BATCHES.glob("*.csv"))]
    if len(entries) > 1500:
        raise ValueError("Exceeded monthly batch manifest limit")
    existing = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    old_hashes = {row["id"]: row["sha256"] for row in existing.get("batches", [])}
    for entry in entries:
        if entry["id"] in old_hashes and old_hashes[entry["id"]] != entry["sha256"]:
            raise ValueError("Previously published monthly batch modified: " + entry["id"])
    same = entries == existing.get("batches", [])
    stamp = (existing.get("generated_at") if same else None) or datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    result = {
        "schema": SCHEMA, "repository": REPO, "generated_at": stamp,
        "batch_count": len(entries), "candidate_rows": sum(x["record_count"] for x in entries),
        "batches": entries,
        "policy": "PUBLIC MONTHLY API RESEARCH INBOX FOR SCOUT ONLY. NOT HUMAN-REVIEW READY OR A REACH PUBLICATION.",
    }
    MANIFEST.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Validated monthly API feed: {len(entries)} batches / {result['candidate_rows']} candidate rows")

if __name__ == "__main__":
    main()
