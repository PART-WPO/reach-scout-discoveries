#!/usr/bin/env python3
"""Recover an exact historical DataCite identity without inventing fresh evidence.

This is a bounded fallback after DOI registry access fails. It reuses immutable,
SHA-verified public API source rows and recorded native repository links.
Archived metadata is *not* treated as a new live publication/funding check or
an approved candidate. The public REACH/Scout duplicate gate still applies.
"""
import hashlib
import json
import re
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from decision_pipeline import checked_csv, norm_doi

ROOT = Path(__file__).resolve().parents[2]
HISTORICAL_MANIFEST = "api-discoveries/historical/manifest.json"
HISTORICAL_TRIAGE = "scout-operations/historical-triage.json"
TRUSTED_NATIVE_HOSTS = frozenset({
    "databank.illinois.edu", "zenodo.org", "figshare.com",
    "dataverse.harvard.edu", "dataverse.tdl.org",
})


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def _native_link(url):
    raw = str(url or "").strip()
    parsed = urlparse(raw)
    return (raw if parsed.scheme == "https" and
            parsed.hostname in TRUSTED_NATIVE_HOSTS and
            not parsed.username and not parsed.password and
            (parsed.port is None or parsed.port == 443) else None)


def _check_native_record(url, exact_doi, *, opener=None):
    """Live corroboration only for recognized official HTTPS repositories.

    No redirect following or arbitrary URLs from untrusted source records.
    A positive result checks the exact DOI text, not funding or metadata date.
    """
    selected = _native_link(url)
    if selected is None:
        return {"url": url, "result": "UNAPPROVED_NATIVE_HOST"}
    try:
        req = urllib.request.Request(selected, headers={
            "Accept": "text/html", "User-Agent": "NOAA-WPO-Scout-Archive-Recovery/1.0"})
        response = (opener or urllib.request.build_opener(_NoRedirect)).open(req, timeout=9)
        with response as stream:
            body = stream.read(131073)
        if len(body) > 131072:
            return {"url": selected, "result": "HTML_SIZE_LIMIT"}
        sample = body.decode("utf-8", errors="replace").lower()
        found = exact_doi.lower() in sample or exact_doi.lower().replace("/", "%2f") in sample
        return {"url": selected, "result": (
            "LIVE_EXACT_DOI_PRESENT" if found else "EXACT_DOI_NOT_IN_PAGE")}
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
        return {"url": selected, "result": "ACCESS_UNAVAILABLE",
                "error_type": type(exc).__name__}


def recover(root, exact_doi, failed_metadata, *, check_native=True, opener=None):
    """Return a research-only archived-source recovery, or original failure.

    Failure to read/check an existing archive is a hard error: never silently
    substitute unverifiable public data. The archive itself is a previously
    observed DataCite source, not evidence the external API is accessible now.
    """
    canonical = norm_doi(exact_doi)
    if not canonical:
        raise ValueError("Exact DOI is required for archived recovery")
    if failed_metadata.get("status") != "unavailable_or_not_found":
        return failed_metadata
    archive = root / HISTORICAL_MANIFEST
    if not archive.exists():
        return failed_metadata
    manifest_bytes = archive.read_bytes()
    manifest = json.loads(manifest_bytes)
    if manifest.get("schema") != "reach-historical-api-feed-v1":
        raise ValueError("Unexpected historical DataCite manifest schema")
    original = None
    source_batch = None
    count = 0
    for batch in manifest["batches"]:
        rows = checked_csv(root, batch["path"], batch["sha256"], batch["record_count"])
        count += len(rows)
        for row in rows:
            if norm_doi(row.get("DOI")) == canonical:
                if original is not None:
                    raise ValueError("Duplicate DOI across historical DataCite batches")
                original, source_batch = row, batch["id"]
    if count != manifest["candidate_rows"]:
        raise ValueError("Historical DataCite manifest row count is incomplete")
    if original is None:
        return failed_metadata
    ledger = json.loads((root / HISTORICAL_TRIAGE).read_text(encoding="utf-8"))
    matching = [e for e in ledger["entries"]
                if norm_doi(e.get("identity")) == canonical]
    if len(matching) != 1:
        raise ValueError("Historical metadata has no unique research ledger identity")
    recorded = matching[0]
    source_urls = [x for x in recorded.get("checked_sources", [])
                   if isinstance(x, str) and _native_link(x)]
    evidence_url = (source_urls[0] if source_urls else
                    original.get("Scout Source URL") or original.get("Output URL") or
                    "https://doi.org/" + canonical)
    native = (_check_native_record(source_urls[0], canonical, opener=opener)
              if check_native and source_urls else None)
    return {
        "status": "archived_source_recovered",
        "provider": "historical_datacite_snapshot",
        "doi": canonical,
        "title": str(original.get("Title") or ""),
        "creators": [a.strip() for a in
                     re.split(r";", str(original.get("Authors / PI") or "")) if a.strip()],
        "abstract": str(original.get("Brief Abstract") or "")[:3500],
        "resource_type": str(original.get("Output Type") or ""),
        "publication_status": "NOT_RECHECKED",
        "pub_date": "",
        "archived_pub_date_hint": str(original.get("Pub Date") or ""),
        "pub_date_basis": "Archived source only; live publication/date not rechecked",
        "evidence": evidence_url,
        "source_batch_id": source_batch,
        "archive_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "source_record_sha256": hashlib.sha256(json.dumps(
            original, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest(),
        "recorded_award_hints": str(original.get("NOAA Award Number(s)") or ""),
        "native_repository_check": native,
        "attempts": failed_metadata.get("attempts", []),
        "research_only": True,
        "original_terminal_status": recorded.get("status"),
        "next_action": "CHECK_PUBLIC_TERMINAL_GATE_FIRST_THEN_DISTINCT_SOURCE_IF_ELIGIBLE",
    }
