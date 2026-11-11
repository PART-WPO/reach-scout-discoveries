#!/usr/bin/env python3
"""Read-only, same-mission check for a related artifact's PRIMARY URL in REACH.

The SHA-pinned comparison cache only narrows the search. Its links may be
secondary links in papers, so fetch each matching index shard from the LIVE
original REACH repository and compare the canonical "Link to Output" field.
A negative result is never proof of global absence. No private or public writes.
"""
import argparse
import csv
import hashlib
import io
import json
import re
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen

from decision_pipeline import norm_url

ROOT = Path(__file__).resolve().parents[2]
CACHE = "scout-operations/reach-comparison-cache/comparison-index.json"
SOURCE_BASE = "https://raw.githubusercontent.com/PART-WPO/reach-dashboard/main/"
INDEX_PATH = re.compile(r"^agent-data/index/part-[0-9]{3}\.csv$")
REQUIRED = {"Record ID", "REACH UID", "Output Type", "Link to Output", "Award Number(s)", "Title"}


def artifact_url(value):
    """Normalize exact artifact identity, not an unrelated path or fork."""
    normalized = norm_url(value)
    if not normalized:
        return ""
    parsed = urlsplit(normalized)
    host = parsed.hostname or ""
    path = parsed.path
    if host in {"github.com", "www.github.com"}:
        # Github repo root URLs are equivalent with .git, but /tree or /blob
        # paths and different owners/repos must NEVER be collapsed to the root.
        if re.fullmatch(r"/[^/]+/[^/]+\.git", path):
            path = path[:-4]
        return urlunsplit(("https", "github.com", path, "", ""))
    return normalized


def official_index_bytes(relative, *, timeout=12):
    if not INDEX_PATH.fullmatch(relative):
        raise ValueError("Unexpected REACH index shard path")
    request = Request(SOURCE_BASE + relative, headers={"User-Agent": "reach-scout-url-verifier/1.0"})
    with urlopen(request, timeout=timeout) as response:
        return response.read(3_000_001)


def verify(url, *, root=ROOT, load_shard=official_index_bytes):
    target = artifact_url(url)
    if not target:
        raise ValueError("A full HTTPS artifact URL is required")
    cache = json.loads((Path(root) / CACHE).read_text(encoding="utf-8"))
    if (cache.get("schema") != "reach-scout-comparison-cache-v1"
            or cache.get("source_repo") != "PART-WPO/reach-dashboard"
            or cache.get("source_records") != len(cache.get("records", []))):
        raise ValueError("Incomplete or unrecognized REACH source cache")
    expected_shas = {s["path"]: s["sha256"] for s in cache.get("verified_shards", [])
                     if INDEX_PATH.fullmatch(s.get("path", ""))}
    candidates = [rec for rec in cache["records"] if target in {
        artifact_url(link) for link in rec.get("links", [])
    }]
    if not candidates:
        return {"status": "NO_CACHE_LINK_MATCH_FULL_REACH_GATE_STILL_REQUIRED",
                "query_url": target, "matches": [], "scanned_shards": []}

    checked, errors, matches, secondary = [], [], [], []
    for path in sorted({rec.get("index_path", "") for rec in candidates}):
        if not INDEX_PATH.fullmatch(path) or path not in expected_shas:
            errors.append({"shard": path, "reason": "UNVERIFIED_INDEX_PATH"})
            continue
        try:
            raw = load_shard(path)
            if isinstance(raw, str):
                raw = raw.encode("utf-8")
            digest = hashlib.sha256(raw).hexdigest()
            if len(raw) > 3_000_000:
                raise ValueError("Shard exceeds bounded size")
            rows = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
            if not REQUIRED.issubset(set(rows.fieldnames or [])):
                raise ValueError("Official REACH index columns missing")
            current = {rec["record_id"]: rec for rec in candidates if rec.get("index_path") == path}
            for row in rows:
                rec = current.get(row["Record ID"])
                if not rec:
                    continue
                if row["REACH UID"] != rec.get("reach_uid"):
                    errors.append({"shard": path, "record_id": row["Record ID"],
                                   "reason": "REACH_UID_CHANGED"})
                    continue
                evidence = {"record_id": row["Record ID"], "reach_uid": row["REACH UID"],
                            "title": row["Title"], "output_type": row["Output Type"],
                            "award_numbers": row["Award Number(s)"],
                            "primary_url": row["Link to Output"],
                            "index_source": SOURCE_BASE + path,
                            "index_sha256": digest,
                            "index_sha_matches_cache": digest == expected_shas[path]}
                if artifact_url(row["Link to Output"]) == target:
                    matches.append(evidence)
                else:
                    secondary.append(evidence)
            checked.append({"shard": path, "sha_matches_cache": digest == expected_shas[path]})
        except Exception as exc:
            errors.append({"shard": path, "reason": type(exc).__name__ + ": " + str(exc)[:180]})

    # A live, exact primary URL is sufficient positive public evidence even
    # when a cached shard has since changed. Never clear a negative against
    # a stale or unavailable source; a full REACH identity gate is still due.
    if matches and not errors:
        status = "EXISTING_REACH_PRIMARY_OUTPUT_URL"
    elif matches:
        status = "POSSIBLE_REACH_IDENTITY_SOURCE_ERROR"
    elif errors:
        status = "REACH_URL_CHECK_BLOCKED"
    else:
        status = "SUPPORTING_LINK_ONLY_FULL_REACH_GATE_REQUIRED"
    return {"status": status, "query_url": target, "matches": matches,
            "supporting_link_records": secondary, "scanned_shards": checked,
            "errors": errors, "source_cache_manifest_sha256": cache.get("source_manifest_sha256")}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="Full distinct artifact URL")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    result = verify(args.url, root=args.root)
    print(json.dumps(result, indent=2))
    # Any source failure must be treated as an unresolved gate, never a new item.
    if result["status"] in ("REACH_URL_CHECK_BLOCKED", "POSSIBLE_REACH_IDENTITY_SOURCE_ERROR"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
