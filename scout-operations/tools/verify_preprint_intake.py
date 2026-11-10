#!/usr/bin/env python3
"""One publication-status gate for ALL new Scout review feed entries.

Every new inbox draft and any direct new batches are checked BEFORE promotion.
Keep unverifiable publications on hold. No preprint DOI can be promoted, even
when a version of record exists at a different DOI. No private Hub writes.
"""
import csv
import datetime as dt
import hashlib
import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scout-operations/tools"))
from preprint_watchlist import crossref, datacite, norm_doi, SCHEMA
from reach_version_identity import (version_links, fetch_reach_index,
                                    version_decision, public_staged_dois)

REPORT = ROOT / "scout-operations/preprint-intake-gate.json"
WATCH = ROOT / "scout-operations/preprint-watchlist.json"
DOI = re.compile(r"^10\.\d{4,9}/\S+$", re.I)
HOLD_TERMS = ("preprint", "pre-print", "accepted manuscript", "working paper",
              "manuscript submitted", "not peer reviewed", "not peer-reviewed")
PREPRINT_HOSTS = ("arxiv.org/", "biorxiv.org/", "medrxiv.org/",
                  "egusphere.copernicus.org/", "eartharxiv.org/",
                  "preprints.org/", "essopenarchive.org/")

def watchlist(root=ROOT):
    data = json.loads((root / "scout-operations/preprint-watchlist.json").read_text(encoding="utf-8"))
    if data.get("schema") != SCHEMA or not isinstance(data.get("entries"), list):
        raise ValueError("Invalid preprint watchlist; block new publication")
    return data

def preprint_type(cr, dc):
    if cr and str(cr.get("type", "")).lower() == "posted-content":
        return True
    if dc:
        types = dc.get("types") or {}
        general = str(types.get("resourceTypeGeneral") or "").lower()
        specific = str(types.get("resourceType") or "").lower()
        if general == "preprint" or any(x in specific for x in HOLD_TERMS):
            return True
    return False

def publication_decision(doi, output_type, cr=None, dc=None, cr_error=False, dc_error=False,
                         watched=False, rationale="", output_url=""):
    """Publication dates do not prove journal status. Registry errors hold articles."""
    if (watched or
        re.search(r"(?im)^(?:API publication status|Publication status):\s*(?:Preprint|Unpublished|Accepted manuscript)\s*$", rationale or "") or
        any(host in str(output_url or "").lower() for host in PREPRINT_HOSTS)):
        return "preprint_hold", "Known preprint identity; original DOI remains held"
    if preprint_type(cr, dc):
        return "preprint_hold", "Source registry explicitly classifies this DOI as preprint or posted content"
    if not doi:
        # No DOI: existing verified public reports/other outputs stay human-reviewable.
        return "eligible", "No DOI to cross-check; independent human review still required"
    if str(output_type) != "1":
        if cr_error and dc_error:
            return "metadata_hold", "Both DOI registries unavailable; cannot exclude a posted preprint"
        return "eligible", "Non-publication DOI is not identified as preprint in available metadata"
    if cr and str(cr.get("type", "")).lower() in {
        "journal-article", "proceedings-article", "book-chapter", "report"
    }:
        for key in ("published-online", "published-print", "published", "issued"):
            parts = (cr.get(key) or {}).get("date-parts") or []
            if parts and parts[0] and parts[0][0]:
                return "eligible", "Crossref identifies an officially issued scholarly publication"
    if dc:
        types = dc.get("types") or {}
        if str(types.get("resourceTypeGeneral") or "").lower() == "journalarticle":
            # DataCite created date is an office Pub Date convention, NOT proof
            # of an officially published journal version.
            issued = any(
                str(d.get("dateType") or "").lower() in ("issued", "available", "published")
                for d in (dc.get("dates") or []))
            if issued:
                return "eligible", "DataCite identifies a journal article with issued/available metadata"
    return "metadata_hold", "No authoritative official-publication evidence; date or title alone is insufficient"

def read_batches(root=ROOT):
    manifest_path = root / "scout-discoveries/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    old = {b["path"] for b in manifest.get("batches", [])}
    inbox = root / "scout-discoveries/inbox"
    batches = root / "scout-discoveries/batches"
    paths = sorted(
        p for p in inbox.glob("*.csv")
        if not (batches / p.name).exists() or
        (batches / p.name).read_bytes() != p.read_bytes())
    paths += sorted(
        p for p in batches.glob("*.csv")
        if str(p.relative_to(root)).replace("\\", "/") not in old)
    return paths

def verify(root=ROOT, fetch_crossref=crossref, fetch_datacite=datacite,
           now=None, fetch_reach=fetch_reach_index):
    now = now or dt.datetime.now(dt.timezone.utc).isoformat()
    watch = watchlist(root)
    known = {norm_doi(x["preprint_doi"]) for x in watch["entries"]}
    # The public version index includes retired preprints, so a journal DOI
    # cannot return as NEW after earlier DOI versions leave the watchlist.
    linked = version_links(root)
    staged_dois = public_staged_dois(root)
    reach_index = None
    reach_index_error = None
    reach_index_checked = False
    checks = []
    cache = {}
    for path in read_batches(root):
        raw = path.read_bytes()
        rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline="")))
        if not rows:
            raise ValueError("Empty prospective Scout review batch: " + str(path))
        decisions = []
        for row in rows:
            doi = norm_doi(row.get("DOI") or row.get("Output URL"))
            if doi and not DOI.fullmatch(doi):
                doi = ""
            if doi not in cache and doi:
                cr = dc = None
                cr_error = dc_error = False
                try:
                    cr = fetch_crossref(doi)
                except Exception:
                    cr_error = True
                try:
                    dc = fetch_datacite(doi)
                except Exception:
                    dc_error = True
                cache[doi] = (cr, dc, cr_error, dc_error)
            cr, dc, cr_error, dc_error = cache.get(doi, (None, None, False, False))
            status, reason = publication_decision(
                doi, row.get("Output Type", ""), cr, dc, cr_error, dc_error,
                doi in known, row.get("Scout Discovery Rationale", ""),
                row.get("Output URL", ""))
            if status == "eligible" and doi:
                rationale = row.get("Scout Discovery Rationale", "")
                classification = re.search(
                    r"(?im)^\s*Scout classification:\s*([^\r\n]+)", rationale)
                class_text = classification.group(1).upper() if classification else ""
                if doi in staged_dois and "NEW CANDIDATE" in class_text:
                    status = "identity_hold"
                    reason = ("DOI already exists in public Scout candidate batches; "
                              "a prior Hub decision is private and must not be inferred. "
                              "Do not send a second NEW CANDIDATE.")
                elif doi in linked and str(row.get("Output Type", "")) == "1":
                    if not reach_index_checked:
                        reach_index_checked = True
                        try:
                            reach_index = fetch_reach()
                        except Exception as error:
                            reach_index_error = type(error).__name__
                    if reach_index is None:
                        status = "identity_hold"
                        reason = ("Public REACH index unavailable or incomplete (" +
                                  str(reach_index_error) + "); cannot clear "
                                  "known preprint-to-published version DOI")
                    else:
                        verdict = version_decision(row, linked, reach_index)
                        if verdict is not None:
                            status, reason = verdict
            if status == "preprint_hold" and doi and doi not in known:
                watch["entries"].append({
                    "preprint_doi": doi, "title": row.get("Title", ""),
                    "award_numbers": row.get("NOAA Award Number(s)", ""),
                    "status": "tracking_preprint", "source": str(path.relative_to(root)),
                    "evidence_url": ("https://api.crossref.org/works/" + doi if cr
                                     else "https://api.datacite.org/dois/" + doi),
                    "seed_expansion_allowed": True
                })
                known.add(doi)
            decisions.append({
                "doi": doi, "status": status, "reason": reason,
                "evidence": ["https://api.crossref.org/works/" + doi,
                             "https://api.datacite.org/dois/" + doi] if doi else []
            })
        verdict = "eligible" if all(d["status"] == "eligible" for d in decisions) else "hold"
        checks.append({"path": str(path.relative_to(root)).replace("\\", "/"),
                       "sha256": hashlib.sha256(raw).hexdigest(),
                       "verdict": verdict, "rows": decisions})
    watch["entries"].sort(key=lambda x: x["preprint_doi"])
    watch_path = root / "scout-operations/preprint-watchlist.json"
    watch_path.write_text(json.dumps(watch, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result = {"schema": "reach-scout-preprint-intake-gate-v1", "checked_at": now,
              "policy": "All new publication proposals require registry check. A preprint DOI cannot be staged through ANY origin. Uncertain metadata remains on hold. Existing human decisions unchanged.",
              "checks": checks, "eligible_batches": sum(x["verdict"] == "eligible" for x in checks),
              "held_batches": sum(x["verdict"] == "hold" for x in checks)}
    path = root / "scout-operations/preprint-intake-gate.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Universal Scout preprint gate:", len(checks), "new batches;",
          result["held_batches"], "held; preprints known:", len(known))
    return result

def audit_active_feed(root=ROOT):
    """Check the complete ACTIVE reviewer manifest, without changing old source files."""
    watch = watchlist(root)
    blocked = {norm_doi(x["preprint_doi"]) for x in watch["entries"]}
    manifest = json.loads((root / "scout-discoveries/manifest.json").read_text(encoding="utf-8"))
    problems = []
    count = 0
    for entry in manifest.get("batches", []):
        relative = str(entry["path"])
        if not relative.startswith("scout-discoveries/batches/") or ".." in Path(relative).parts:
            raise ValueError("Invalid active Scout manifest source path")
        raw = (root / relative).read_bytes()
        if hashlib.sha256(raw).hexdigest() != entry["sha256"]:
            raise ValueError("Active Scout manifest batch checksum mismatch")
        rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline="")))
        if len(rows) != entry["record_count"]:
            raise ValueError("Active Scout manifest batch row count mismatch")
        for row in rows:
            count += 1
            doi = norm_doi(row.get("DOI") or row.get("Output URL"))
            rationale = row.get("Scout Discovery Rationale", "")
            url = str(row.get("Output URL") or "").lower()
            if (doi in blocked or
                re.search(r"(?im)^(?:API publication status|Publication status):\s*(?:Preprint|Unpublished|Accepted manuscript)\s*$", rationale) or
                any(host in url for host in PREPRINT_HOSTS)):
                problems.append({"doi": doi, "batch": relative})
    if problems:
        raise ValueError("Active Scout feed includes held preprints: " +
                         json.dumps(problems[:12]))
    print("ACTIVE SCOUT REVIEW FEED AUDIT PASSED:", count,
          "records; zero known preprint DOI violations")
    return count


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-active", action="store_true")
    args = parser.parse_args()
    audit_active_feed() if args.audit_active else verify()
