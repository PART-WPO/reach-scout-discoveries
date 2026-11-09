#!/usr/bin/env python3
"""Evidence-only, source-SHA-pinned DOI research memory.

Reuses *existing* public independent DOI metadata reports by reference,
without copying authors/PI/collaborator lists into the new memory index.
Every reused response must pass DOI, provider, timestamp, checksum, parser
version and publication/preprint freshness gates. Private Hub state is unknown.
"""
import argparse
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from decision_pipeline import norm_doi

ROOT = Path(__file__).resolve().parents[2]
INDEX = "scout-operations/research-memory/doi-cache-index.json"
SCHEMA = "reach-scout-public-doi-research-memory-v1"
REPORTS = (
    ("scout-operations/reports/independent-doi-lookup/latest.json",
     "reach-scout-independent-doi-lookup-v1", "records"),
    ("scout-operations/reports/independent-metadata-lookup/latest.json",
     "reach-scout-independent-metadata-lookup-v1", "doi_records"),
)
PARSER = "scout-operations/tools/lookup_independent_dois.py"
SUCCESS_TTL = timedelta(days=7)
FAILURE_TTL = timedelta(hours=6)
PREPRINT_TTL = timedelta(0)
MAX_AGE = timedelta(days=365)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(data):
    return json.dumps(data, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")


def key(doi):
    d = norm_doi(doi)
    if not d:
        raise ValueError("An exact DOI is required for persistent memory")
    return digest(("doi:" + d).encode("utf-8"))


def iso_date(value):
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return dt.astimezone(timezone.utc) if dt.tzinfo is not None else None


def read_index(root=ROOT):
    path = root / INDEX
    if not path.exists():
        return None
    doc = json.loads(path.read_text(encoding="utf-8"))
    if doc.get("schema") != SCHEMA or not isinstance(doc.get("entries"), dict):
        raise ValueError("Invalid Scout metadata memory schema")
    return doc


def metadata_result(root, memory, doi, *, now=None):
    """Return (response, capture_timestamp, reason). Never infer fresh evidence.

    A valid cached response is a prior *observed* official provider result,
    not a guarantee that the remote publisher or grant metadata is unchanged.
    """
    now = now or datetime.now(timezone.utc)
    if memory is None:
        return None, None, "MEMORY_NOT_INITIALIZED"
    parser_path = root / PARSER
    if not parser_path.is_file() or memory.get("resolver_sha256") != digest(parser_path.read_bytes()):
        return None, None, "PARSER_POLICY_CHANGED"
    entry = memory["entries"].get(key(doi))
    if entry is None:
        return None, None, "NO_PREVIOUS_DOI_EVIDENCE"
    if entry.get("doi_key") != key(doi):
        raise ValueError("DOI memory key identity conflict")
    when = iso_date(entry.get("observed_at"))
    if when is None or when > now + timedelta(minutes=2):
        return None, None, "INVALID_OR_FUTURE_OBSERVATION_TIME"
    age = now - when
    if age < timedelta(0) or age > MAX_AGE:
        return None, None, "OUT_OF_BOUNDS_OBSERVATION_TIME"
    if entry.get("publication_status") == "preprint":
        return None, None, "PREPRINT_REQUIRES_FRESH_SOURCE"
    ttl = SUCCESS_TTL if entry.get("status") == "ok" else FAILURE_TTL
    if age > ttl:
        return None, None, "SOURCE_TTL_EXPIRED"
    source_rel = entry.get("source_report")
    if source_rel not in {v[0] for v in REPORTS}:
        raise ValueError("DOI memory references an unapproved source path")
    report_path = root / source_rel
    if not report_path.is_file():
        return None, None, "SOURCE_REPORT_MISSING"
    raw = report_path.read_bytes()
    if digest(raw) != entry.get("source_report_sha256"):
        return None, None, "SOURCE_REPORT_CHANGED"
    report = json.loads(raw)
    expected_schema, field = next((v[1], v[2]) for v in REPORTS if v[0] == source_rel)
    if report.get("schema") != expected_schema:
        raise ValueError("DOI memory source report schema changed")
    matched = [r for r in report.get(field, []) if norm_doi(r.get("doi")) == norm_doi(doi)]
    if len(matched) != 1:
        return None, None, "SOURCE_CASE_NOT_UNIQUE"
    source = matched[0]
    md = source.get("metadata")
    if not isinstance(md, dict) or digest(canonical(md)) != entry.get("metadata_sha256"):
        return None, None, "DOI_METADATA_CONTENT_CHANGED"
    if md.get("status") != entry.get("status"):
        return None, None, "METADATA_STATUS_CHANGED"
    if md.get("status") == "ok":
        url = str(md.get("evidence") or "")
        provider = md.get("provider")
        if provider not in ("datacite", "crossref"):
            return None, None, "UNAPPROVED_METADATA_PROVIDER"
        if not url.startswith("https://api.datacite.org/dois/") and not url.startswith("https://api.crossref.org/works/"):
            return None, None, "OFFICIAL_PROVIDER_EVIDENCE_NOT_VERIFIED"
    return md, when.isoformat(), "VERIFIED_CACHED_OFFICIAL_METADATA"


def build_index(root=ROOT, *, now=None):
    """Construct a deterministic pointer-only snapshot from public reports."""
    parser = root / PARSER
    if not parser.is_file():
        raise ValueError("DOI resolver missing")
    registry = {}
    stats = {}
    for rel, expected_schema, field in REPORTS:
        path = root / rel
        if not path.is_file():
            continue
        raw = path.read_bytes()
        report = json.loads(raw)
        if report.get("schema") != expected_schema:
            raise ValueError("Unsupported public DOI metadata report: " + rel)
        source_sha = digest(raw)
        eligible = 0
        for record in report.get(field, []):
            d = norm_doi(record.get("doi"))
            md = record.get("metadata")
            captured = record.get("metadata_observed_at")
            if not d or not isinstance(md, dict) or md.get("status") not in (
                    "ok", "unavailable_or_not_found") or iso_date(captured) is None:
                continue
            if md["status"] == "ok" and not str(md.get("evidence") or "").startswith("https://api."):
                continue
            eligible += 1
            k = key(d)
            row = {
                "doi_key": k,
                "observed_at": iso_date(captured).isoformat(),
                "source_report": rel,
                "source_report_sha256": source_sha,
                "metadata_sha256": digest(canonical(md)),
                "status": md["status"],
                "provider": md.get("provider"),
                "publication_status": md.get("publication_status"),
            }
            if k in registry and registry[k]["observed_at"] > row["observed_at"]:
                continue
            registry[k] = row
        stats[rel] = {"rows_with_valid_observation": eligible,
                      "source_report_sha256": source_sha}
    return {
        "schema": SCHEMA,
        "scope": "PUBLIC_OFFICIAL_DOI_METADATA_POINTERS_ONLY",
        "resolver_sha256": digest(parser.read_bytes()),
        "public_source_reports": stats,
        "total_distinct_doi_keys": len(registry),
        "entries": dict(sorted(registry.items())),
        "author_names_in_memory_index": False,
        "private_reviewer_state": "NOT_VERIFIED",
        "automatic_staging": False,
        "policy": "Positive TTL seven days; errors six hours; preprints always live. Identity and NOAA IR are always re-screened against the current SHA-pinned public snapshot. Absent metadata cannot prove no output. No SPARK personnel source.",
    }


def write_index(root=ROOT):
    data = build_index(root)
    path = root / INDEX
    path.parent.mkdir(parents=True, exist_ok=True)
    blob = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if not path.exists() or path.read_text(encoding="utf-8") != blob:
        path.write_text(blob, encoding="utf-8")
    return data


def cli():
    p = argparse.ArgumentParser()
    p.add_argument("--rebuild", action="store_true")
    p.add_argument("--check", action="store_true")
    args = p.parse_args()
    if not args.rebuild and not args.check:
        p.error("choose --rebuild or --check")
    built = build_index(ROOT)
    if args.check:
        stored = read_index(ROOT)
        if stored is None or stored != built:
            raise ValueError("DOI memory index is stale or missing; rebuild after public report refresh")
    else:
        write_index(ROOT)
    print(json.dumps({"doi_keys": built["total_distinct_doi_keys"],
                      "source_reports": list(built["public_source_reports"]),
                      "no_author_names": True, "private_hub_modified": False}))


if __name__ == "__main__":
    cli()
