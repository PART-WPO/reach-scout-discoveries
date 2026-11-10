#!/usr/bin/env python3
"""Reconcile terminal *public identity* evidence without inventing Hub decisions.

This repairs stale hourly retry entries from SHA-verifiable public sources.
Publication identities and reviewer workflow have separate terminal states:
a public Scout batch is NOT private Hub intake, and an original preprint's
identity resolution does NOT imply its related-output seed expansion is done.
"""
import argparse
import csv
import hashlib
import io
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
LEDGER = "scout-operations/decision-handoff-ledger.json"
RETIRE = "scout-operations/preprint-retirement-archive.json"
IDENTITY = "scout-operations/identity-cache/public-identity-index.json"
COMPARISON = "scout-operations/reach-comparison-cache/comparison-index.json"
MANIFEST = "scout-discoveries/manifest.json"
ROUTING = "scout-operations/historical-crossref-screening/actionable-routing.json"
REPORT = "scout-operations/reports/public-blocker-reconciliation.json"
LEDGER_SCHEMA = "reach-scout-hourly-decision-handoff-v1"
SCHEMA = "reach-scout-public-handoff-reconciliation-v1"
UID = re.compile(r"reachuid-v1-[0-9a-f]{32}\Z")
DOI = re.compile(r"10\.\d{4,9}/\S+\Z", re.I)


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def norm_doi(v):
    v = str(v or "").strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if v.startswith(prefix):
            v = v[len(prefix):]
    return v.rstrip(".,);")


def norm_title(v):
    return re.sub(r"[^a-z0-9]+", " ", str(v or "").lower()).strip()


def noaa_ir(v):
    p = urlsplit(str(v or "").strip())
    if (p.scheme not in ("http", "https") or
            (p.hostname or "").lower() != "repository.library.noaa.gov" or
            p.username or p.password or p.port):
        return ""
    path = p.path.rstrip("/").lower()
    return "https://repository.library.noaa.gov" + path if re.fullmatch(r"/view/noaa/\d+", path) else ""


def public_reach_preprint_resolutions(root):
    """Use retirement proof AND a public REACH record with the exact UID/IR URL.

    If the cached public catalog source is stale or absent, do not infer an
    existing REACH identity just from a historical title or award match.
    """
    files = [root / rel for rel in (RETIRE, IDENTITY, COMPARISON)]
    if not all(p.is_file() for p in files):
        return {}
    archive, index = (json.loads(p.read_text(encoding="utf-8")) for p in files[:2])
    if (archive.get("schema") != "reach-scout-preprint-retirement-archive-v1" or
            index.get("schema") != "reach-scout-identity-index-v1" or
            index.get("sources", {}).get("reach_cache_sha256") != digest(files[2])):
        raise ValueError("Public REACH identity cache/retirement archive out of sync")
    public = {}
    for rec in index.get("records", []):
        if rec.get("source") == "REACH":
            public.setdefault(rec.get("identity"), []).append(rec)
    found = {}
    for entry in archive.get("entries", []):
        pre, final = norm_doi(entry.get("preprint_doi")), norm_doi(entry.get("published_doi"))
        ir_url = noaa_ir(entry.get("verification_source"))
        if (entry.get("reason") != "OFFICIAL_PUBLISHED_VERSION_CONFIRMED_IN_PUBLIC_REACH"
                or not DOI.fullmatch(pre) or not DOI.fullmatch(final) or not ir_url):
            continue
        match = []
        for uid in entry.get("reach_ids", []):
            if not UID.fullmatch(str(uid)):
                continue
            for rec in public.get(uid, []):
                if ir_url in {noaa_ir(url) for url in rec.get("urls", [])}:
                    match.append(uid)
        if len(set(match)) == 1:
            if pre in found and found[pre]["published_doi"] != final:
                raise ValueError("Conflicting official publication versions for archived preprint")
            found[pre] = {
                "published_doi": final, "reach_uid":match[0],
                "official_ir_url":ir_url, "basis":"ARCHIVED_FINAL_DOI_AND_VERIFIED_PUBLIC_REACH_UID_IR_URL"
            }
    return found


def active_public_scout(root):
    """Return exact-DOI published units after verifying manifest CSV SHA and title."""
    path = root / MANIFEST
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "reach-scout-discovery-feed-v1":
        raise ValueError("Unexpected public Scout manifest")
    result = {}
    for batch in data.get("batches", []):
        rel = batch.get("path", "")
        if (not re.fullmatch(r"scout-discoveries/batches/[A-Za-z0-9_.-]+\.csv", rel)
                or not (root / rel).is_file()):
            raise ValueError("Invalid public Scout batch locator")
        raw = (root / rel).read_bytes()
        if hashlib.sha256(raw).hexdigest() != batch.get("sha256"):
            raise ValueError("Public Scout batch SHA mismatch")
        rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
        if len(rows) != batch.get("record_count"):
            raise ValueError("Public Scout batch row count mismatch")
        for row in rows:
            doi = norm_doi(row.get("DOI"))
            if DOI.fullmatch(doi):
                result.setdefault(doi, []).append({
                    "path": rel, "title": norm_title(row.get("Title")),
                    "output_type": str(row.get("Output Type", "")),
                })
    return result


def public_source_resolutions(root):
    retirement = public_reach_preprint_resolutions(root)
    staged = active_public_scout(root)
    titles = {}
    path = root / ROUTING
    if path.is_file():
        routing = json.loads(path.read_text(encoding="utf-8"))
        for row in routing.get("entries", []):
            doi = norm_doi(row.get("doi"))
            titles[doi] = norm_title(row.get("title"))
    return retirement, staged, titles


def reconcile(ledger, retirement, staged, titles):
    """Apply only source-backed public identity repairs; preserve reviewer unknowns."""
    if ledger.get("schema") != LEDGER_SCHEMA or not isinstance(ledger.get("cases"), dict):
        raise ValueError("Unrecognized hourly decision ledger")
    changes = []
    for doi, row in ledger["cases"].items():
        pre = retirement.get(norm_doi(doi))
        public_units = staged.get(norm_doi(doi), [])
        expected = titles.get(norm_doi(doi), "")
        verified_units = [u for u in public_units if u["output_type"] == "1"
                          and expected and u["title"] == expected]
        current_state = row.get("state")
        replacement = None
        if pre and (current_state == "BLOCKED" or current_state == "RESOLVED_EXISTING_REACH"):
            # Original is preprint/posted content; it can NEVER be passed on as
            # a new published article, even though its final DOI is in REACH.
            replacement = {
                "state": "RESOLVED_EXISTING_REACH",
                "reason": "PREPRINT_FINAL_VERSION_ALREADY_IN_REACH",
                "published_doi": pre["published_doi"],
                "reach_uid": pre["reach_uid"],
                "official_evidence_url": pre["official_ir_url"],
                "evidence_basis": pre["basis"],
                "research_retry_required": False,
                "original_publication_eligibility": "PREPRINT_DOI_NOT_ELIGIBLE",
                "original_formally_closed": False,
                "seed_expansion_closed": False,
            }
        elif (len(verified_units) == 1 and
              (current_state == "BLOCKED" or current_state == "PUBLISHED_PUBLIC_SCOUT") and
              row.get("reason") in {"NOT_NEW_IN_REACH_OR_SCOUT",
                                    "PUBLIC_SCOUT_REVIEW_UNIT_VERIFIED",
                                    "SOURCE_VERIFIED_AND_MANIFEST_VALIDATED"}):
            replacement = {
                "state": "PUBLISHED_PUBLIC_SCOUT",
                "reason": "PUBLIC_SCOUT_REVIEW_UNIT_VERIFIED",
                "published_batch": verified_units[0]["path"],
                "research_retry_required": False,
                "downstream_hub_verification": "NOT_VERIFIED",
                "seed_expansion_closed": False,
            }
        if replacement:
            before = dict(row)
            row.pop("retry_after", None)
            row.update(replacement)
            # Preserve the historical attempt count and previous check time.
            row["private_hub_import"] = "NOT_VERIFIED"
            if row != before:
                changes.append({"doi":doi,"previous_state":before.get("state"),
                                "new_state":row["state"],"reason":row["reason"],
                                "prior_retry_after":before.get("retry_after")})
    return changes


def run(root=ROOT, now=None, check=False):
    path = root / LEDGER
    ledger = json.loads(path.read_text(encoding="utf-8"))
    retired, staged, titles = public_source_resolutions(root)
    changes = reconcile(ledger, retired, staged, titles)
    report = {
        "schema": SCHEMA,
        "policy": "Public evidence only; no Hub import, reviewer action, REACH write or seed-expansion closure inferred.",
        "changed_cases": changes,
        "active_research_retry_cases": [
            d for d, case in ledger["cases"].items()
            if case.get("state") == "BLOCKED" and case.get("retry_after")],
        "public_scout_pending_private_verification": [
            d for d, case in ledger["cases"].items()
            if case.get("state") == "PUBLISHED_PUBLIC_SCOUT"],
        "resolved_existing_reach_preprint_identities": [
            d for d, case in ledger["cases"].items()
            if case.get("state") == "RESOLVED_EXISTING_REACH"],
        "downstream_hub_imports": "NOT_VERIFIED",
        "human_decisions": "NOT_VERIFIED",
    }
    rendered = json.dumps(ledger, indent=2, ensure_ascii=False) + "\n"
    if check:
        if path.read_text(encoding="utf-8") != rendered:
            raise ValueError("Handoff ledger contains stale publicly resolved blockers")
    else:
        path.write_text(rendered, encoding="utf-8")
        target = root / REPORT
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8")
    print(json.dumps({"source_resolved":len(retired),"new_changes":len(changes),
                      "active_retries":len(report["active_research_retry_cases"]),
                      "private_hub_imports":"NOT_VERIFIED"}))
    return report


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args=parser.parse_args()
    run(check=args.check)
