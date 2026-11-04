#!/usr/bin/env python3
"""Validate small Crossref screening batches and generate reproducible coverage."""
import csv
import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = pathlib.Path(__file__).resolve().parent
SOURCE = ROOT / "api-discoveries/historical-crossref/manifest.json"
STATUSES = {"CONFIRMED_IN_REACH", "NOT_FOUND_IN_REACH", "POSSIBLE_MATCH"}
DOI_RE = re.compile(r"10\.\d{4,9}/\S+", re.I)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def doi(value):
    value = str(value or "").strip().lower()
    value = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", value)
    value = re.sub(r"^doi:", "", value).strip()
    return value

def main():
    source = json.loads(SOURCE.read_text())
    source_sha = sha(SOURCE)
    source_dois = set()
    for batch in source["batches"]:
        p = ROOT / batch["path"]
        if sha(p) != batch["sha256"]:
            raise ValueError(f"source checksum mismatch: {p}")
        with p.open(newline="", encoding="utf-8-sig") as stream:
            for row in csv.DictReader(stream):
                values = [v for k, v in row.items() if k and ("doi" in k.lower() or "identity" in k.lower())]
                found = [doi(v) for v in values if v and DOI_RE.search(str(v))]
                if not found:
                    found = [doi(m.group()) for m in DOI_RE.finditer(" ".join(str(v) for v in row.values() if v))]
                source_dois.update(found)
    if len(source_dois) != source["candidate_rows"]:
        raise ValueError(f"expected {source['candidate_rows']} source DOIs; parsed {len(source_dois)}")
    records = {}
    batches = []
    for path in sorted(HERE.glob("batch-*.json")):
        payload = json.loads(path.read_text())
        if payload.get("schema") != "reach-scout-crossref-screening-batch-v1":
            raise ValueError(f"invalid schema: {path}")
        if payload.get("source_manifest_sha256") != source_sha:
            raise ValueError(f"source manifest checksum differs: {path}")
        if not payload.get("reach_snapshot"):
            raise ValueError(f"missing REACH snapshot identity: {path}")
        entries = payload.get("records", [])
        if not entries or len(entries) > 100:
            raise ValueError(f"batch must contain 1..100 records: {path}")
        for item in entries:
            identity = doi(item.get("doi"))
            status = item.get("screening_status")
            if identity not in source_dois or status not in STATUSES:
                raise ValueError(f"invalid DOI or screening status: {path}: {identity}")
            if identity in records:
                raise ValueError(f"duplicate DOI across batches: {identity}")
            if status == "CONFIRMED_IN_REACH" and not item.get("reach_uid"):
                raise ValueError(f"confirmed match missing REACH UID: {identity}")
            if not item.get("evidence_urls") or not item.get("next_action"):
                raise ValueError(f"missing evidence or next action: {identity}")
            records[identity] = item
        batches.append({"path": str(path.relative_to(ROOT)), "sha256": sha(path), "record_count": len(entries)})
    counts = {status: sum(r["screening_status"] == status for r in records.values()) for status in sorted(STATUSES)}
    counts["screened"] = len(records)
    counts["unscreened"] = len(source_dois) - len(records)
    counts["total"] = len(source_dois)
    counts["scout_overlap_flagged"] = sum(bool(r.get("scout_overlap")) for r in records.values())
    manifest = {"schema": "reach-scout-crossref-screening-manifest-v1", "source_manifest": str(SOURCE.relative_to(ROOT)), "source_manifest_sha256": source_sha, "batches": batches, "counts": counts}
    coverage = {"schema": "reach-scout-crossref-screening-coverage-v1", "source_manifest_sha256": source_sha, **counts, "note": "Validated checkpoint coverage only; does not replace original disposition or expansion-seed metrics."}
    for filename, obj in (("manifest.json", manifest), ("coverage.json", coverage)):
        (HERE / filename).write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")
    print(json.dumps(counts, sort_keys=True))

if __name__ == "__main__":
    main()
