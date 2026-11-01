#!/usr/bin/env python3
"""Synchronize active monthly API DOI cases into Scout's persistent research queue.

This queues research; it NEVER performs or claims research. The immutable
API manifest is the only source of case identities. Existing Scout research
is preserved, and superseded batch cases are archived, never silently lost.
"""
import csv
import hashlib
import io
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "api-discoveries/manifest.json"
LEDGER = ROOT / "scout-operations/monthly-triage.json"
DOI = re.compile(r"10\.\d{4,9}/\S+", re.I)
BATCH_PATH = re.compile(r"api-discoveries/batches/[A-Za-z0-9_.-]+\.csv")
RUN_MONTH = re.compile(r"^REACH-MONTHLY-API-(20\d{2}-(?:0[1-9]|1[0-2]))$")


def normalize_identity(row):
    doi = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "",
                 (row.get("DOI") or "").strip(), flags=re.I).lower()
    if doi:
        if not DOI.fullmatch(doi):
            raise ValueError("Invalid source DOI")
        return "doi:" + doi
    url = (row.get("Output URL") or "").strip().lower().split("#", 1)[0].rstrip("/")
    if not url.startswith("https://"):
        raise ValueError("Missing DOI or HTTPS output URL")
    return "url:" + url


def load_cases(root, manifest):
    if manifest.get("schema") != "reach-monthly-api-discovery-feed-v1":
        raise ValueError("Unexpected monthly API manifest schema")
    result = {}
    for batch in manifest["batches"]:
        if not BATCH_PATH.fullmatch(batch["path"]):
            raise ValueError("Unsafe monthly API batch path")
        raw = (root / batch["path"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != batch["sha256"]:
            raise ValueError("Monthly API source SHA mismatch")
        rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline="")))
        if len(rows) != batch["record_count"]:
            raise ValueError("Monthly API record count mismatch")
        for row in rows:
            identity = normalize_identity(row)
            run = (row.get("Source Run ID") or "").strip()
            matched = RUN_MONTH.fullmatch(run)
            if not matched:
                raise ValueError("Unrecognized monthly API source run")
            award_numbers = [a.strip() for a in (row.get("NOAA Award Number(s)") or "").split(",") if a.strip()]
            if not award_numbers:
                raise ValueError("Monthly case without award number")
            key = (batch["id"], identity)
            if key in result:
                raise ValueError("Duplicate batch and DOI in monthly input")
            result[key] = {
                "source_batch_id": batch["id"],
                "identity": identity,
                "cohort": matched.group(1),
                "status": "awaiting_research",
                "first_seen_at": manifest["generated_at"],
                "updated_at": manifest["generated_at"],
                "source_run_id": run,
                "award_numbers": award_numbers,
                "research_notes": "Automatically queued from validated monthly API harvest. Scout investigation has not started; no REACH or Discovery Hub decision.",
                "checked_sources": [],
                "source_batch_sha256": batch["sha256"],
            }
    if len(result) != manifest["candidate_rows"]:
        raise ValueError("Monthly manifest aggregate count mismatch")
    return result


def reconcile(root=ROOT):
    manifest = json.loads((root / "api-discoveries/manifest.json").read_text(encoding="utf-8"))
    path = root / "scout-operations/monthly-triage.json"
    ledger = json.loads(path.read_text(encoding="utf-8"))
    if ledger.get("schema") != "reach-scout-monthly-triage-v1" or not isinstance(ledger.get("entries"), list):
        raise ValueError("Unrecognized monthly Scout research ledger")
    expected = load_cases(root, manifest)
    superseded = {x["original_id"]: x["replacement_id"]
                  for x in manifest.get("superseded_batches", []) if x.get("replacement_published") is True}
    seen = set()
    active = []
    archive = list(ledger.get("archived_entries", []))
    archived_keys = {(x["source_batch_id"], x["identity"]) for x in archive}
    for item in ledger["entries"]:
        key = (item["source_batch_id"], item["identity"])
        if key in seen or key in archived_keys:
            raise ValueError("Repeated or archived DOI key")
        seen.add(key)
        if key in expected:
            if item.get("cohort") != expected[key]["cohort"]:
                raise ValueError("Changed monthly cohort for existing case")
            active.append(item)
        elif item["source_batch_id"] in superseded:
            archived = dict(item)
            archived["archived_reason"] = "Superseded immutable monthly API batch; preserve research history."
            archived["superseded_by_batch_id"] = superseded[item["source_batch_id"]]
            archived["archived_at_manifest"] = manifest["generated_at"]
            archive.append(archived)
        else:
            raise ValueError("Ledger case absent from active manifest without explicit supersession")
    for key, item in expected.items():
        if key not in seen:
            active.append(item)
    ledger["entries"] = active
    if archive:
        ledger["archived_entries"] = archive
    rendered = json.dumps(ledger, indent=2, ensure_ascii=False) + "\n"
    if path.read_text(encoding="utf-8") != rendered:
        path.write_text(rendered, encoding="utf-8")
    print("Monthly intake synchronized:", len(active), "active cases;",
          len(archive), "archived;", sum(e["status"] == "awaiting_research" for e in active), "awaiting Scout research")
    return ledger


if __name__ == "__main__":
    reconcile()
