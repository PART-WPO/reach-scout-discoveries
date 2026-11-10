#!/usr/bin/env python3
"""Public-only, fail-closed identity gate for published versions of REACH preprints.

No human review state is read or written. A final journal DOI is a new DOI,
not necessarily a new intellectual work. Only explicit preprint-to-final DOI
relations from verified Scout public registries are considered.
"""
import csv
import hashlib
import io
import json
import re
import urllib.request
from pathlib import Path

from preprint_watchlist import norm_doi

REACH_BASE = "https://raw.githubusercontent.com/PART-WPO/reach-dashboard/main/"
INDEX_PATH = re.compile(r"agent-data/index/part-\d{3}\.csv\Z")
RID = re.compile(r"reach-\d{6}\Z")
UID = re.compile(r"reachuid-v1-[0-9a-f]{32}\Z")
CLASSIFICATION = re.compile(r"(?im)^\s*Scout classification:\s*([^\r\n]+)")
ROUTE = re.compile(r"(?im)^\s*Scout discovery route:\s*([^\r\n]+)")
UPDATE_FIELDS = re.compile(r"(?im)^\s*REACH update fields:\s*(\S[^\r\n]{9,})")


def version_links(root):
    """Map published DOI to verified prior preprint DOIs and archived REACH IDs."""
    links = {}
    sources = (
        ("scout-operations/preprint-watchlist.json",
         "reach-scout-preprint-watchlist-v1", "watch"),
        ("scout-operations/preprint-publication-leads.json",
         "reach-scout-preprint-publication-leads-v1", "leads"),
        ("scout-operations/preprint-retirement-archive.json",
         "reach-scout-preprint-retirement-archive-v1", "retired"),
    )
    for relative, schema, source in sources:
        path = root / relative
        if not path.exists():
            if source == "watch":
                raise ValueError("Required preprint watchlist missing")
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("schema") != schema or not isinstance(data.get("entries"), list):
            raise ValueError("Invalid public version-identity source: " + relative)
        for item in data["entries"]:
            if source == "watch":
                pre = norm_doi(item.get("preprint_doi"))
                finals = item.get("verified_published_dois") or []
            else:
                pre = norm_doi(item.get("preprint_doi"))
                finals = [item.get("published_doi")]
            for final in finals:
                final = norm_doi(final)
                if not re.fullmatch(r"10\.\d{4,9}/\S+", final, re.I) or not pre:
                    continue
                entry = links.setdefault(final, {"preprints": set(), "reach_ids": set()})
                entry["preprints"].add(pre)
                if source == "retired":
                    entry["reach_ids"].update(
                        r for r in item.get("reach_ids", []) if RID.fullmatch(str(r)))
                if source == "leads":
                    for match in (item.get("public_reach_index_screen") or {}).get("matches", []):
                        rid = match.get("record_id", "")
                        if RID.fullmatch(rid):
                            entry["reach_ids"].add(rid)
    return links


def _download(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "REACH-Scout-version-identity-gate/1.0",
        "Accept": "application/octet-stream"})
    with urllib.request.urlopen(req, timeout=18) as response:
        return response.read(1_000_001)


def fetch_reach_index(fetch_bytes=_download):
    """Read all REACH index shards with SHA checks to avoid partial-catalog false negatives."""
    raw_manifest = fetch_bytes(REACH_BASE + "agent-data/manifest.json")
    if len(raw_manifest) > 1_000_000:
        raise ValueError("REACH manifest too large")
    manifest = json.loads(raw_manifest.decode("utf-8"))
    shards = manifest.get("index", {}).get("files", [])
    if not shards or not isinstance(shards, list):
        raise ValueError("Missing REACH index shards")
    result = {"by_doi": {}, "by_id": {}, "manifest_sha256": hashlib.sha256(raw_manifest).hexdigest()}
    total = 0
    for shard in shards:
        path = shard.get("path", "")
        if not INDEX_PATH.fullmatch(path):
            raise ValueError("Unexpected REACH index shard path")
        raw = fetch_bytes(REACH_BASE + path)
        if (len(raw) != shard.get("bytes")
                or hashlib.sha256(raw).hexdigest() != shard.get("sha256")):
            raise ValueError("REACH index shard SHA/byte mismatch: " + path)
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
        if not {"Record ID", "REACH UID", "Link to Output", "Output Type"}.issubset(reader.fieldnames or []):
            raise ValueError("REACH index shard missing identity fields")
        rows = list(reader)
        if len(rows) != shard.get("rows"):
            raise ValueError("REACH index shard row count mismatch")
        total += len(rows)
        for row in rows:
            rid, uid = row["Record ID"], row["REACH UID"]
            if not RID.fullmatch(rid) or not UID.fullmatch(uid) or rid in result["by_id"]:
                raise ValueError("Invalid or duplicate REACH identity")
            item = {"record_id": rid, "reach_uid": uid,
                    "output_type": row["Output Type"], "title": row.get("Title", ""),
                    "award": row.get("Award Number(s)", ""), "link": row["Link to Output"]}
            result["by_id"][rid] = item
            doi = norm_doi(row["Link to Output"])
            if re.fullmatch(r"10\.\d{4,9}/\S+", doi, re.I):
                result["by_doi"].setdefault(doi, []).append(item)
    if total != manifest.get("source", {}).get("rows"):
        raise ValueError("REACH index incomplete")
    result["records"] = total
    return result


def version_decision(row, linked, reach_index):
    """Check one verified preprint-to-journal link; return None if unrelated."""
    if str(row.get("Output Type", "")) != "1":
        return None
    doi = norm_doi(row.get("DOI") or row.get("Output URL"))
    relation = linked.get(doi)
    if relation is None:
        return None
    candidates = {}
    for earlier in relation["preprints"] | {doi}:
        for item in reach_index["by_doi"].get(earlier, []):
            if item["output_type"] == "1":
                candidates[item["record_id"]] = item
    for rid in relation["reach_ids"]:
        item = reach_index["by_id"].get(rid)
        if item and item["output_type"] == "1":
            candidates[rid] = item
    if not candidates:
        return ("eligible", "Verified article version relationship; no matching prior or final publication DOI found in complete SHA-verified public REACH index")
    if len(candidates) != 1:
        return ("identity_hold", "Multiple possible REACH records for published-version relationship; require human identity reconciliation")
    item = next(iter(candidates.values()))
    rationale = row.get("Scout Discovery Rationale", "")
    classified = CLASSIFICATION.search(rationale)
    route = ROUTE.search(rationale)
    existing = row.get("Existing REACH Match", "")
    correct_update = (
        classified and classified.group(1).strip() == "REACH METADATA UPDATE"
        and route and route.group(1).strip() == "Metadata correction"
        and item["record_id"] in existing
        and item["reach_uid"] in (existing + "\n" + rationale)
        and UPDATE_FIELDS.search(rationale)
    )
    if correct_update:
        return ("eligible", "Published version represented by REACH "
                + item["record_id"] + " / " + item["reach_uid"]
                + "; existing-record metadata update for human review only")
    return ("identity_hold", "Published version already represented by REACH "
            + item["record_id"] + " / " + item["reach_uid"]
            + "; NEW CANDIDATE is invalid; require REACH METADATA UPDATE "
            "with Metadata correction route, exact ID/UID and named update fields")


def public_staged_dois(root):
    """Previously manifested public Scout DOIs, without private Hub decisions."""
    manifest_path = root / "scout-discoveries/manifest.json"
    if not manifest_path.exists():
        return {}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    result = {}
    for batch in manifest.get("batches", []):
        rel = batch.get("path", "")
        if (not rel.startswith("scout-discoveries/batches/")
                or ".." in Path(rel).parts or not rel.endswith(".csv")):
            raise ValueError("Unsafe manifested Scout batch path")
        raw = (root / rel).read_bytes()
        if hashlib.sha256(raw).hexdigest() != batch.get("sha256"):
            raise ValueError("Published Scout batch hash mismatch")
        rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
        if len(rows) != batch.get("record_count"):
            raise ValueError("Published Scout batch row count mismatch")
        for row in rows:
            doi = norm_doi(row.get("DOI") or row.get("Output URL"))
            if re.fullmatch(r"10\.\d{4,9}/\S+", doi, re.I):
                result.setdefault(doi, set()).add(rel)
    return result
