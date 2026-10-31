#!/usr/bin/env python3
"""Build/preflight 24-column Scout candidates BEFORE GitHub publication.

Input JSON contains {"candidates": [{"fields": {24-column values...},
"provenance": {...}}]}. No external service calls. Never writes a manifest.
"""
import argparse
import csv
import json
import re
from pathlib import Path

from build_manifest import INPUT, inspect_batch

ALLOWED_CLASSIFICATIONS = {
    "NEW CANDIDATE", "POSSIBLE DUPLICATE", "KNOWN DUPLICATE",
    "NEEDS INVESTIGATION", "REACH METADATA UPDATE",
}
ALLOWED_ROUTES = {
    "Direct API", "API-seeded expansion", "Independent discovery",
    "Metadata correction", "Unclassified",
}
PURPOSE_BY_CLASSIFICATION = {
    "NEW CANDIDATE": "new_output_review",
    "POSSIBLE DUPLICATE": "possible_duplicate_review",
    "KNOWN DUPLICATE": "existing_duplicate_review",
    "NEEDS INVESTIGATION": "needs_investigation",
    "REACH METADATA UPDATE": "metadata_correction",
}
ORIGIN_METHODS = {"Direct API", "API-seeded expansion", "Independent discovery", "Unclassified"}

DOI = re.compile(r"^10\.\d{4,9}/\S+$", re.I)
SHA = re.compile(r"^[0-9a-f]{40,64}$", re.I)
URL = re.compile(r"^https://\S+$", re.I)
RESERVED = {
    "Scout classification", "Scout discovery route", "Scout discovery path evidence",
    "Scout seed DOI", "Scout discovery method", "Intake origin",
    "Monthly intake", "Scout verification", "REACH snapshot", "Sources checked",
    "Funding basis", "Related outputs checked", "Scout origin method", "Scout finding purpose",
}


def safe_line(value, label):
    if not isinstance(value, str) or not value.strip() or "\n" in value or "\r" in value:
        raise ValueError(f"{label} must be one nonblank line")
    return value.strip()


def compose_rationale(prov):
    classification = safe_line(prov["classification"], "classification")
    route = safe_line(prov["route"], "route")
    if classification not in ALLOWED_CLASSIFICATIONS or route not in ALLOWED_ROUTES:
        raise ValueError("Invalid canonical classification or discovery route")
    original_method = prov.get("origin_method")
    if route == "Metadata correction":
        # The old 24-column Hub parser still uses the route value as a
        # correction-type signal, so record the original method separately.
        original_method = safe_line(original_method, "origin_method")
    else:
        original_method = safe_line(original_method or route, "origin_method")
        if original_method != route:
            raise ValueError("Origin method and discovery route conflict")
    if original_method not in ORIGIN_METHODS:
        raise ValueError("Original discovery method must be a canonical method")
    purpose = PURPOSE_BY_CLASSIFICATION[classification]
    lines = []
    origin = prov.get("intake_origin")
    if origin:
        origin = safe_line(origin, "intake_origin")
        if origin not in {"Monthly API", "Historical DataCite API Backfill"}:
            raise ValueError("Use exact intake origin; put additional context in notes")
        lines.append(f"Intake origin: {origin}")
        if origin == "Monthly API":
            month = safe_line(prov.get("monthly_intake"), "monthly_intake")
            if not re.fullmatch(r"\d{4}-\d{2}", month):
                raise ValueError("Monthly intake must be YYYY-MM")
            lines.append(f"Monthly intake: {month}")
    lines.extend((
        "Scout verification: Completed",
        f"Scout classification: {classification}",
        f"Scout discovery route: {route}",
        f"Scout origin method: {original_method}",
        f"Scout finding purpose: {purpose}",
    ))
    if original_method in {"Direct API", "API-seeded expansion", "Independent discovery"}:
        path = safe_line(prov.get("path_evidence"), "path_evidence")
        if not URL.fullmatch(path):
            raise ValueError("Path evidence must be a real HTTPS source URL")
        lines.append(f"Scout discovery path evidence: {path}")
    if original_method == "API-seeded expansion":
        seed = safe_line(prov.get("seed_doi"), "seed_doi")
        if not DOI.fullmatch(seed):
            raise ValueError("API-seeded expansion requires a valid exact seed DOI")
        lines.append(f"Scout seed DOI: {seed}")
    if original_method == "Independent discovery":
        method = safe_line(prov.get("discovery_method"), "discovery_method")
        if len(method) < 12:
            raise ValueError("Independent discovery requires substantive method")
        lines.append(f"Scout discovery method: {method}")
    if origin:
        snap = safe_line(prov.get("reach_snapshot"), "reach_snapshot")
        checked = prov.get("sources_checked", [])
        if not SHA.fullmatch(snap):
            raise ValueError("REACH snapshot must be 40-64 hex characters")
        if not isinstance(checked, list) or not checked:
            raise ValueError("sources_checked must list public HTTPS URLs")
        for url in checked:
            if not URL.fullmatch(safe_line(url, "checked source")):
                raise ValueError("Invalid checked-source URL")
        funding = safe_line(prov.get("funding_basis"), "funding_basis")
        related = safe_line(prov.get("related_outputs_checked"), "related_outputs_checked")
        if len(funding) < 12 or len(related) < 12:
            raise ValueError("API origin requires evidence-backed funding/related-output checks")
        lines.extend((
            f"REACH snapshot: {snap}",
            f"Sources checked: {' ; '.join(checked)}",
            f"Funding basis: {funding}",
            f"Related outputs checked: {related}",
        ))
    notes = prov.get("notes", [])
    if not isinstance(notes, list):
        raise ValueError("notes must be an array of public-safe rationale lines")
    for note in notes:
        note = safe_line(note, "note")
        key = note.split(":", 1)[0]
        if key in RESERVED:
            raise ValueError(f"Do not rewrite canonical field in notes: {key}")
        lines.append(note)
    return "\n".join(lines)


def validate_canonical(path):
    entry = inspect_batch(path)  # Exact 24-column, safety, provenance and DOI rules
    with path.open("r", newline="", encoding="utf-8-sig") as stream:
        for num, row in enumerate(csv.DictReader(stream), 2):
            rationale = row["Scout Discovery Rationale"] or ""
            found = re.findall(r"(?im)^\s*Scout classification:\s*([^\r\n]+)", rationale)
            if len(found) != 1 or found[0].strip() not in ALLOWED_CLASSIFICATIONS:
                raise ValueError(f"Non-canonical Scout classification: {path.name}:{num}")
            ver = re.findall(r"(?im)^\s*Scout verification:\s*([^\r\n]+)", rationale)
            if len(ver) != 1 or ver[0].strip() != "Completed":
                raise ValueError(f"Non-canonical Scout verification: {path.name}:{num}")
            route = re.findall(r"(?im)^\s*Scout discovery route:\s*([^\r\n]+)", rationale)
            if len(route) != 1 or route[0].strip() not in ALLOWED_ROUTES:
                raise ValueError(f"Non-canonical discovery route: {path.name}:{num}")
            method = re.findall(r"(?im)^\s*Scout origin method:\s*([^\r\n]+)", rationale)
            purposes = re.findall(r"(?im)^\s*Scout finding purpose:\s*([^\r\n]+)", rationale)
            if len(method) != 1 or method[0].strip() not in ORIGIN_METHODS:
                raise ValueError(f"Missing canonical origin method: {path.name}:{num}")
            if len(purposes) != 1 or purposes[0].strip() != PURPOSE_BY_CLASSIFICATION[found[0].strip()]:
                raise ValueError(f"Missing canonical finding purpose: {path.name}:{num}")
            if route[0].strip() != "Metadata correction" and method[0].strip() != route[0].strip():
                raise ValueError(f"Conflicting origin method/route: {path.name}:{num}")
            if route[0].strip() == "API-seeded expansion":
                if len(re.findall(r"(?im)^\s*Scout seed DOI:\s*10\.\d{4,9}/[^\s]+\s*$", rationale)) != 1:
                    raise ValueError(f"Missing exact Scout seed DOI: {path.name}:{num}")
    return entry


def prepare(source, output):
    payload = json.loads(source.read_text(encoding="utf-8"))
    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("candidates must be a nonempty list")
    if output.exists():
        raise ValueError("Refusing to overwrite an existing batch")
    rows = []
    for item in candidates:
        fields = item["fields"]
        if not isinstance(fields, dict):
            raise ValueError("Each candidate needs a fields object")
        if any(k not in INPUT for k in fields):
            raise ValueError("Unknown field outside 24-column contract")
        if fields.get("Scout Discovery Rationale"):
            raise ValueError("Provide structured provenance, not freeform rationale")
        if fields.get("Candidate ID") or fields.get("Principal Investigator Email(s)"):
            raise ValueError("Never publish Candidate ID or PI email")
        record = {key: fields.get(key, "") for key in INPUT}
        record["Scout Discovery Rationale"] = compose_rationale(item["provenance"])
        rows.append(record)
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with output.open("x", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=INPUT, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        return validate_canonical(output)
    except BaseException:
        output.unlink(missing_ok=True)
        raise


def main():
    parser = argparse.ArgumentParser(description="Scout local-only CSV generation and preflight")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input-json", type=Path, help="Structured candidate JSON")
    group.add_argument("--check", type=Path, help="Preflight a draft CSV, without publication")
    parser.add_argument("--output", type=Path, help="Unique destination CSV for --input-json")
    args = parser.parse_args()
    if args.input_json and not args.output:
        parser.error("--input-json requires --output")
    if args.check and args.output:
        parser.error("--check must not have --output")
    entry = prepare(args.input_json, args.output) if args.input_json else validate_canonical(args.check)
    print(f"PRE-PUBLICATION VALIDATION PASSED: {entry['record_count']} candidates; {entry['id']}")


if __name__ == "__main__":
    main()
