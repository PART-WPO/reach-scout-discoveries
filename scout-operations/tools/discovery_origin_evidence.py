"""Conservative, source-hash-verified first-path attribution for historical Crossref originals.

A source DOI from the exact captured historical Crossref batch is Direct API
only when an immutable, exact-output funding-screen note independently ties
that DOI, award and raw input batch together. Never use a related seed, title
similarity, or the generic fact a DOI appears in Crossref as proof of method.
No public batch is rewritten; the rollup may overlay a verified correction.
"""
import csv
import hashlib
import json
from pathlib import Path

NOTES = Path("scout-operations/historical-crossref-phase2")
QUEUE = Path("scout-operations/crossref-candidate-queue.json")
API_PREFIX = "api-discoveries/historical-crossref/batches/"
PUBLIC_PREFIX = "https://github.com/PART-WPO/reach-scout-discoveries/blob/main/"


def historical_crossref_source(root, doi):
    doi = str(doi or "").strip().lower()
    if not doi.startswith("10.") or "/" not in doi:
        return None
    note_name = "auto-verified-oar459-" + hashlib.sha256(doi.encode()).hexdigest()[:18] + ".json"
    note_path = NOTES / note_name
    full = root / note_path
    qpath = root / QUEUE
    if not (full.is_file() and qpath.is_file()):
        return None
    note_bytes = full.read_bytes()
    note = json.loads(note_bytes)
    if (note.get("schema") != "scout-source-backed-research-evidence-v1"
        or note.get("original_doi", "").lower() != doi
        or note.get("lane") != "historical_crossref_original"
        or note.get("funding") != "OFFICIAL_CROSSREF_EXACT_DOI_WPO459_CONFIRMED"
        or note.get("publication_status") != "OFFICIALLY_PUBLISHED_JOURNAL_ARTICLE"):
        return None
    queue = json.loads(qpath.read_text(encoding="utf-8"))
    if queue.get("schema") != "reach-scout-crossref-candidate-queue-v2":
        raise ValueError("Unexpected source queue schema for discovery method")
    items = [x for x in queue.get("items", []) if x.get("doi", "").lower() == doi]
    if len(items) != 1:
        return None
    item = items[0]
    award = str(note.get("structured_award") or "").upper()
    if not award or award not in item.get("wpo_459_award_numbers", []):
        return None
    source_paths = set(note.get("award_evidence_source_batches", [])) & set(
        item.get("award_evidence_source_batches", [])
    )
    cited = {x.get("url") for x in note.get("source_evidence", [])
             if x.get("type") == "sha_verified_historical_crossref_batch"}
    for path in sorted(source_paths):
        if not (path.startswith(API_PREFIX) and path.endswith(".csv")
                and path in queue.get("source_sha256", {})
                and PUBLIC_PREFIX + path in cited):
            continue
        raw = (root / path).read_bytes()
        if hashlib.sha256(raw).hexdigest() != queue["source_sha256"][path]:
            raise ValueError("Historical Crossref source batch SHA mismatch: " + path)
        with (root / path).open(newline="", encoding="utf-8-sig") as f:
            rows = csv.DictReader(f)
            if any(
                str(row.get("DOI") or "").strip().lower() == doi and
                award in str(row.get("NOAA Award Number(s)") or "").upper()
                for row in rows
            ):
                return {
                    "method": "Direct API",
                    "original_doi": doi,
                    "source_batch_path": path,
                    "source_batch_sha256": queue["source_sha256"][path],
                    "source_note_path": note_path.as_posix(),
                    "source_note_sha256": hashlib.sha256(note_bytes).hexdigest(),
                    "path_evidence_url": PUBLIC_PREFIX + path,
                    "basis": "Exact original DOI and publisher-deposited WPO459 award in SHA-verified historical Crossref capture and exact-output screen",
                }
    return None


def verified_historical_scope_origin(root, doi):
    """Evidence-backed original discovery method for historical-scope referrals.

    The *first captured exact DOI* in the November 2 historical Crossref
    original intake is Direct API even if a later source check uses publisher,
    project or repository data. A separate project-title pilot explicitly
    recorded as NOT a direct API result can establish Independent research.
    Keep any other origin Unclassified; never rewrite an immutable CSV.
    """
    doi = str(doi or "").strip().lower()
    earlier = historical_crossref_source(root, doi)
    if earlier:
        return earlier
    registry_path = root / "scout-operations/research-outcome-registry.json"
    queue_path = root / QUEUE
    if not registry_path.is_file():
        return None
    registry_raw = registry_path.read_bytes()
    registry = json.loads(registry_raw)
    if registry.get("schema") != "reach-scout-all-lane-research-outcomes-v1":
        raise ValueError("Unknown source-verified research registry")
    verified = []
    for event in registry.get("events", []):
        if (str(event.get("doi") or "").lower() != doi
            or not str(event.get("source_path") or "").startswith(
                "scout-operations/historical-crossref-phase2/")):
            continue
        path = event["source_path"]
        actual = hashlib.sha256((root / path).read_bytes()).hexdigest()
        if (actual != event.get("source_sha256")
            or actual != registry.get("source_sha256", {}).get(path)):
            raise ValueError("Original research note SHA mismatch for origin: " + path)
        note = json.loads((root / path).read_text(encoding="utf-8"))
        verified.append((event, note))
    if not verified:
        return None
    if queue_path.is_file():
        queue = json.loads(queue_path.read_text(encoding="utf-8"))
        if queue.get("schema") != "reach-scout-crossref-candidate-queue-v2":
            raise ValueError("Unrecognized historical Crossref queue")
        entries = [item for item in queue.get("items", [])
                   if str(item.get("doi") or "").lower() == doi]
        if len(entries) > 1:
            raise ValueError("Repeated historical Crossref DOI identity")
        if entries:
            item = entries[0]
            for path in sorted(item.get("award_evidence_source_batches", [])):
                if not (path.startswith(API_PREFIX) and path.endswith(".csv")
                        and path in queue.get("source_sha256", {})):
                    continue
                raw = (root / path).read_bytes()
                if hashlib.sha256(raw).hexdigest() != queue["source_sha256"][path]:
                    raise ValueError("Captured original API batch SHA mismatch")
                with (root / path).open(newline="", encoding="utf-8-sig") as stream:
                    matches = [row for row in csv.DictReader(stream)
                               if str(row.get("DOI") or "").lower().strip() == doi
                               and any(award in str(row.get("NOAA Award Number(s)") or "").upper()
                                       for award in item.get("wpo_459_award_numbers", []))]
                if len(matches) != 1:
                    continue
                # Require a separate SHA-verified source note, not simply that
                # a paper is *now* resolvable through Crossref.
                event, _note = verified[0]
                return {
                    "method": "Direct API", "original_doi": doi,
                    "source_batch_path": path, "source_batch_sha256": queue["source_sha256"][path],
                    "source_note_path": event["source_path"],
                    "source_note_sha256": event["source_sha256"],
                    "path_evidence_url": PUBLIC_PREFIX + path,
                    "basis": "Exact original DOI in historical Crossref primary-award batch and distinct SHA-verified research note",
                }

    # Only an explicitly documented project-title discovery method, not a
    # generic Crossref metadata URL or an arbitrary Independent default.
    for event, note in verified:
        for case in note.get("cases", []) if isinstance(note.get("cases"), list) else []:
            if (str(case.get("doi") or "").lower() == doi
                and case.get("source_origin") == "PROJECT_TITLE_SEARCH_NOT_DIRECT_API"
                and str(case.get("initial_source") or "").startswith("https://")
                and note.get("research_lane") == "supplemental_project_title_pilot"):
                return {
                    "method": "Independent discovery", "original_doi": doi,
                    "source_note_path": event["source_path"],
                    "source_note_sha256": event["source_sha256"],
                    "path_evidence_url": case["initial_source"],
                    "basis": "SHA-verified independent SPARK project-title pilot explicitly not sourced from direct API intake",
                }
    return None
