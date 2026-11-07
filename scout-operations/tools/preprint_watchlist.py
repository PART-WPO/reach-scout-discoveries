#!/usr/bin/env python3
"""First-of-month, public-only preprint tracking. NEVER stages a Scout candidate."""
import csv
import datetime as dt
import hashlib
import io
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WATCH = ROOT / "scout-operations/preprint-watchlist.json"
LEADS = ROOT / "scout-operations/preprint-publication-leads.json"
SCHEMA = "reach-scout-preprint-watchlist-v1"
DOI = re.compile(r"^10\.\d{4,9}/\S+$", re.I)
PREPRINT_LINE = re.compile(r"(?im)^API publication status:\s*Preprint\s*$")

def norm_doi(value):
    value = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", str(value or "").strip(), flags=re.I)
    return value.lower().rstrip(".,);")

def api_json(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "REACH-Scout-preprint-watchlist/1.0 (public scholarly metadata)",
        "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.load(resp)

def crossref(doi):
    try:
        return api_json("https://api.crossref.org/works/" +
                        urllib.parse.quote(doi, safe="/"))["message"]
    except urllib.error.HTTPError as ex:
        if ex.code == 404:
            return None
        raise

def datacite(doi):
    try:
        return api_json("https://api.datacite.org/dois/" +
                        urllib.parse.quote(doi, safe="/"))["data"]["attributes"]
    except urllib.error.HTTPError as ex:
        if ex.code == 404:
            return None
        raise

def linked_final_dois(crossref_record=None, datacite_record=None):
    """An explicit preprint-to-VOR DOI relation, not a title guess."""
    found = set()
    if crossref_record:
        for key, values in (crossref_record.get("relation") or {}).items():
            if re.sub(r"[^a-z]", "", key.lower()) != "ispreprintof":
                continue
            for obj in values or []:
                if isinstance(obj, dict) and str(obj.get("id-type", "doi")).lower() == "doi":
                    doi = norm_doi(obj.get("id"))
                    if DOI.fullmatch(doi):
                        found.add(doi)
    if datacite_record:
        for obj in datacite_record.get("relatedIdentifiers") or []:
            if str(obj.get("relationType", "")).lower() != "ispreprintof":
                continue
            if str(obj.get("relatedIdentifierType", "")).lower() != "doi":
                continue
            doi = norm_doi(obj.get("relatedIdentifier"))
            if DOI.fullmatch(doi):
                found.add(doi)
    return found

def verified_final(article):
    """Official journal version: Crossref article type PLUS publication date."""
    if not article or article.get("type") != "journal-article":
        return False
    for key in ("published-online", "published-print", "published", "issued"):
        dates = (article.get(key) or {}).get("date-parts") or []
        if dates and dates[0] and len(dates[0]) >= 1:
            try:
                y = int(dates[0][0])
                if 1800 <= y <= 2200:
                    return True
            except (ValueError, TypeError):
                pass
    return False

def source_preprints(root):
    """Only tagged API preprints from SHA-verified immutable research batches."""
    for folder in ("api-discoveries", "api-discoveries/historical",
                   "api-discoveries/historical-crossref"):
        manifest_path = root / folder / "manifest.json"
        if not manifest_path.exists():
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for batch in manifest.get("batches", []):
            rel = str(batch.get("path", ""))
            allowed = (rel.startswith("api-discoveries/batches/") or
                       rel.startswith("api-discoveries/historical/batches/") or
                       rel.startswith("api-discoveries/historical-crossref/batches/"))
            if not allowed or ".." in Path(rel).parts or not rel.endswith(".csv"):
                raise ValueError("Unsafe API source path")
            path = root / rel
            raw = path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != batch["sha256"]:
                raise ValueError("Preprint seed batch SHA mismatch: " + rel)
            rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
            if len(rows) != batch["record_count"]:
                raise ValueError("Preprint seed batch count mismatch: " + rel)
            for row in rows:
                if PREPRINT_LINE.search(row.get("Scout Discovery Rationale", "")):
                    doi = norm_doi(row.get("DOI"))
                    if DOI.fullmatch(doi):
                        yield {"preprint_doi": doi, "title": row.get("Title", ""),
                               "award_numbers": row.get("NOAA Award Number(s)", ""),
                               "source": rel, "status": "tracking_preprint",
                               "seed_expansion_allowed": True,
                               "evidence_url": row.get("Evidence URL") or "https://doi.org/" + doi}

    # Independent Scout DOIs, their unified metadata checkpoints, and manually
    # evidenced preprint research leads feed this SAME watchlist. They are not
    # eligible to become review candidates merely because a DOI has a date.
    for relative in (
        "scout-operations/reports/independent-doi-lookup/latest.json",
        "scout-operations/reports/independent-metadata-lookup/latest.json",
        "scout-operations/reports/doi-metadata-checkpoint/latest.json",
    ):
        path = root / relative
        if not path.exists():
            continue
        doc = json.loads(path.read_text(encoding="utf-8"))
        for record in doc.get("doi_records", doc.get("records", [])):
            meta = record.get("metadata") or {}
            resource = str(meta.get("resource_type") or meta.get("type") or "").lower()
            specific = str(meta.get("resource_type_detail") or "").lower()
            if not (meta.get("publication_status") == "preprint" or
                    resource in ("posted-content", "preprint") or
                    "preprint" in specific):
                continue
            doi = norm_doi(record.get("doi"))
            if not DOI.fullmatch(doi):
                continue
            yield {"preprint_doi": doi, "title": meta.get("title", ""),
                   "source": relative, "status": "tracking_preprint",
                   "seed_expansion_allowed": True,
                   "evidence_url": meta.get("evidence") or "https://doi.org/" + doi}

    for path in sorted((root / "scout-operations/research-leads").glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        for lead in doc.get("leads", []):
            if str(lead.get("publication_status") or lead.get("resource_type") or "").lower() not in (
                    "preprint", "posted-content", "accepted manuscript"):
                continue
            doi = norm_doi(lead.get("identity") or lead.get("doi") or lead.get("output_url"))
            if not DOI.fullmatch(doi):
                continue
            yield {"preprint_doi": doi, "title": lead.get("title", ""),
                   "source": str(path.relative_to(root)), "status": "tracking_preprint",
                   "seed_expansion_allowed": True,
                   "evidence_url": lead.get("evidence_url") or "https://doi.org/" + doi}


def refresh(root=ROOT, today=None, fetch_crossref=crossref, fetch_datacite=datacite,
            check_existing=True):
    today = today or dt.datetime.now(dt.timezone.utc).date().isoformat()
    watch_path = root / "scout-operations/preprint-watchlist.json"
    leads_path = root / "scout-operations/preprint-publication-leads.json"
    data = json.loads(watch_path.read_text(encoding="utf-8"))
    if data.get("schema") != SCHEMA or not isinstance(data.get("entries"), list):
        raise ValueError("Invalid preprint watchlist format")
    known = {}
    for entry in data["entries"]:
        doi = norm_doi(entry.get("preprint_doi"))
        if not DOI.fullmatch(doi) or doi in known:
            raise ValueError("Invalid or duplicate tracked preprint DOI")
        known[doi] = entry
    from reconcile_preprint_retirements import ARCHIVE, norm as retirement_norm, reconcile, save
    archive_path = root / ARCHIVE
    archive = json.loads(archive_path.read_text(encoding="utf-8")) if archive_path.exists() else {"schema":"reach-scout-preprint-retirement-archive-v1","policy":"Public evidence only; no re-seeding retired identities","entries":[]}
    retired_dois = {retirement_norm(x["preprint_doi"]) for x in archive["entries"]}
    known = {d:e for d,e in known.items() if d not in retired_dois}
    for seed in source_preprints(root):
        if seed["preprint_doi"] in retired_dois:
            continue
        existing = known.get(seed["preprint_doi"])
        if existing is None:
            known[seed["preprint_doi"]] = seed
        else:
            for key in ("title", "award_numbers"):
                if not existing.get(key) and seed.get(key):
                    existing[key] = seed[key]
    previous_leads = {}
    if leads_path.exists():
        previous_doc = json.loads(leads_path.read_text(encoding="utf-8"))
        if previous_doc.get("schema") != "reach-scout-preprint-publication-leads-v1":
            raise ValueError("Unexpected existing publication-lead schema")
        for prior in previous_doc.get("entries", []):
            key = norm_doi(prior.get("published_doi"))
            if not DOI.fullmatch(key) or key in previous_leads:
                raise ValueError("Invalid or duplicate existing publication lead DOI")
            previous_leads[key] = prior
    output_leads = {}
    source_versions_by_final = {}
    for doi, entry in sorted(known.items()):
        if check_existing and entry.get("last_checked_on") != today:
            cr = dc = None
            errors = []
            try:
                cr = fetch_crossref(doi)
            except Exception as ex:
                errors.append("Crossref metadata unavailable: " + type(ex).__name__)
            try:
                dc = fetch_datacite(doi)
            except Exception as ex:
                errors.append("DataCite metadata unavailable: " + type(ex).__name__)
            verified = []
            for candidate in sorted(linked_final_dois(cr, dc) - {doi}):
                try:
                    published = fetch_crossref(candidate)
                    if verified_final(published):
                        verified.append(candidate)
                except Exception as ex:
                    errors.append("Final article check unavailable: " + type(ex).__name__)
            entry["last_checked_on"] = today
            entry["checked_sources"] = ["https://api.crossref.org/works/" + doi,
                                        "https://api.datacite.org/dois/" + doi]
            if errors:
                entry["last_check_notes"] = "; ".join(errors)
            else:
                entry.pop("last_check_notes", None)
            old = set(entry.get("verified_published_dois") or [])
            entry["verified_published_dois"] = sorted(old | set(verified))
            entry["status"] = ("published_version_found" if entry["verified_published_dois"]
                               else "tracking_preprint")
        for published_doi in entry.get("verified_published_dois") or []:
            source_versions_by_final.setdefault(published_doi, set()).add(doi)
            output_leads[published_doi] = {
                "published_doi": published_doi, "preprint_doi": doi,
                "status": "awaiting_full_reach_scout_dedup_and_funding_review",
                "publication_evidence_url": "https://api.crossref.org/works/" + published_doi,
                "discovery_path": "Preprint Watchlist - verified isPreprintOf",
                "source_seed_expansion_allowed": True, "private_hub_import": "NOT_VERIFIED"}
    for published_doi, fresh in output_leads.items():
        prior = previous_leads.get(published_doi) or {}
        # Preserve verified dedup, reviewer notes, research status and prior human
        # evidence. New monthly metadata cannot reset an existing decision.
        merged = {**fresh, **prior}
        sources = source_versions_by_final[published_doi]
        sources.update(norm_doi(x) for x in prior.get("preprint_dois", []) if DOI.fullmatch(norm_doi(x)))
        merged["preprint_dois"] = sorted(sources)
        old_primary = norm_doi(prior.get("preprint_doi"))
        merged["preprint_doi"] = old_primary if old_primary in sources else sorted(sources)[0]
        merged["published_doi"] = published_doi
        merged["publication_evidence_url"] = fresh["publication_evidence_url"]
        merged["source_seed_expansion_allowed"] = True
        output_leads[published_doi] = merged
    data["entries"] = [known[k] for k in sorted(known)]
    data["metrics"] = {
        "preprints_tracked": len(known),
        "preprints_still_waiting_for_official_publication": sum(
            not x.get("verified_published_dois") for x in known.values()),
        "preprints_with_verified_published_versions": sum(
            bool(x.get("verified_published_dois")) for x in known.values()),
        "verified_official_article_doi_research_leads": len(output_leads),
        "automatically_forwarded_to_discovery_hub": 0,
    }
    result = {"schema": "reach-scout-preprint-publication-leads-v1",
              "policy": "Publication-version research leads ONLY; do not auto-stage, approve or insert to REACH.",
              "entries": [output_leads[k] for k in sorted(output_leads)]}
    reconcile(data, result, archive)
    save(root, ARCHIVE, archive)
    watch_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    leads_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Preprints tracked", len(known), "official article DOI research leads", len(output_leads))
    return data, result

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--register-only", action="store_true",
                        help="Import newly verified preprint research leads without rechecking the existing watchlist")
    args = parser.parse_args()
    refresh(check_existing=not args.register_only)
