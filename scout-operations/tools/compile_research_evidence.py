#!/usr/bin/env python3
"""Compile checked Crossref research notes into conservative, reproducible decision inputs.

Research notes are evidence, not terminal dispositions, private Hub decisions,
verified funding, or automatically publishable candidates. Source files stay
immutable. All generated cases remain gated by the shared decision pipeline.
"""
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

from decision_pipeline import norm_doi, norm_title

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "scout-operations/historical-crossref-phase2"
TARGET = ROOT / "scout-operations/research-decision-cases.json"
PROVENANCE = ROOT / "scout-operations/research-evidence-coverage.json"
DOI_RE = re.compile(r"10\.\d{4,9}/[^\s]+", re.I)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def evidence_urls(obj):
    """Only consume explicit source/checked URL fields; not arbitrary prose URLs."""
    urls = set()
    def visit(item):
        if isinstance(item, str):
            if item.startswith("https://") and " " not in item:
                urls.add(item)
        elif isinstance(item, list):
            for v in item:
                visit(v)
        elif isinstance(item, dict):
            for k, v in item.items():
                if k == "source" and isinstance(v, str) and v.startswith("https://"):
                    visit(v)
                if k in ("url", "checked_sources", "verified_sources", "evidence",
                         "sources", "new_evidence", "additional_primary_source",
                         "distinct_source", "link", "source_url", "checked_url",
                         "path_evidence_url"):
                    visit(v)
    visit(obj)
    return sorted(urls)


def declared_original_preprint(doc):
    # Never interpret a *related journal article* as the original's status.
    values = [
        doc.get("original_publication_status"),
        doc.get("original_status"),
        doc.get("publication_status"),
        doc.get("original_lane", {}).get("publication_status")
        if isinstance(doc.get("original_lane"), dict) else None,
    ]
    return any(str(v or "").upper().startswith(("PREPRINT", "HOLD_PREPRINT"))
               for v in values)


def confirmed_original_published(doc):
    # Require an explicit output-level status, not simply a related final lead.
    return str(doc.get("original_publication_status") or "").upper() == "PUBLISHED"


def build(root=ROOT):
    source = root / "scout-operations/historical-crossref-phase2"
    files = sorted(source.glob("20*.json"))
    grouped = defaultdict(list)
    unlinked = []
    for path in files:
        parent = read(path)
        if isinstance(parent.get("cases"), list):
            # Multi-DOI audit notes are independent original cases. Never
            # attach one case's funding or source evidence to another DOI.
            docs = [entry for entry in parent["cases"] if isinstance(entry, dict)]
            if len(docs) != len(parent["cases"]):
                raise ValueError("Malformed nested evidence case: "+str(path))
            records = [(entry.get("doi"),entry) for entry in docs]
        else:
            raw = parent.get("original_doi")
            if not raw and parent.get("lane") == "historical_crossref_original":
                raw = parent.get("doi")
            records = [(raw,parent)]
        linked=0
        for raw, doc in records:
            doi = norm_doi(raw)
            if not doi:
                continue
            if str(raw).lower().removeprefix("doi:").strip() != doi:
                raise ValueError("Ambiguous original DOI in "+str(path))
            grouped[doi].append((path,doc))
            linked += 1
        if not linked:
            unlinked.append(path.relative_to(root).as_posix())

    # Use SHA-verified source manifest parsing rather than copying titles from
    # non-authoritative research narratives. Cases MUST be source-originals.
    from reconcile_historical_crossref import cases as crossref_source_cases
    _, source_cases = crossref_source_cases()
    decision_cases = []
    coverage = []
    supplemental_holds = []
    for doi, documents in sorted(grouped.items()):
        key = "doi:" + doi
        if key not in source_cases:
            allowed = {"supplemental_project_title_pilot", "independent_research",
                       "doi_seeded_expansion", "monthly_related_lead"}
            lanes = set()
            for path, doc in documents:
                parent = read(path)
                lane = str(doc.get("research_lane") or parent.get("research_lane") or "")
                # Legacy append-only related evidence used track, not research_lane.
                # Require a manifest-backed historical seed and retain a separate hold.
                if not lane and parent.get("track") == "historical_crossref_api_seeded_related_discovery":
                    origin = str(parent.get("origin") or "")
                    match = DOI_RE.search(origin)
                    parent_doi = norm_doi(match.group(0).rstrip(".,;")) if match else ""
                    if not parent_doi or "doi:" + parent_doi not in source_cases:
                        raise ValueError("Related DOI missing verified source seed: "+doi+" in "+str(path))
                    lane = "doi_seeded_expansion"
                if lane not in allowed:
                    raise ValueError("Unknown DOI without supplemental provenance: "+doi+" in "+str(path))
                if lane == "supplemental_project_title_pilot":
                    if doc.get("source_origin") != "PROJECT_TITLE_SEARCH_NOT_DIRECT_API":
                        raise ValueError("Pilot DOI missing explicit source origin: "+doi)
                    provenance_doc = parent
                    if not parent.get("source_pointer") and parent.get("parent_evidence"):
                        parent_path = (root / str(parent["parent_evidence"])).resolve()
                        if not parent_path.is_relative_to(root.resolve()) or not parent_path.is_file():
                            raise ValueError("Invalid parent evidence path for pilot DOI: "+doi)
                        provenance_doc = read(parent_path)
                        if not any(norm_doi(c.get("doi")) == doi for c in provenance_doc.get("cases", [])):
                            raise ValueError("Parent evidence does not contain pilot DOI: "+doi)
                    pointer = provenance_doc.get("source_pointer")
                    expected = provenance_doc.get("source_pointer_sha256")
                    if not pointer or not expected:
                        raise ValueError("Pilot DOI missing SHA-backed source pointer: "+doi)
                    pointer_path = (root / str(pointer)).resolve()
                    if not pointer_path.is_relative_to(root.resolve()) or not pointer_path.is_file():
                        raise ValueError("Invalid pilot source pointer: "+doi)
                    if sha(pointer_path) != expected:
                        raise ValueError("Pilot source pointer SHA mismatch: "+doi)
                    if not any(norm_doi(lead.get("doi")) == doi for lead in read(pointer_path).get("leads", [])):
                        raise ValueError("Pilot DOI absent from SHA-backed source pointer: "+doi)
                lanes.add(lane)
            supplemental_holds.append({
                "doi": doi, "research_lanes": sorted(lanes),
                "decision": "HOLD_SEPARATE_COHORT_REQUIRES_OWN_VALIDATION",
                "source_evidence": [
                    {"path": path.relative_to(root).as_posix(), "sha256": sha(path)}
                    for path, _ in documents
                ],
                "private_review_status": "NOT_VERIFIED",
                "original_and_expansion_status_unchanged": True,
            })
            continue
        titles = source_cases[key].get("titles", set())
        raw_title = sorted(titles, key=lambda x: (len(norm_title(x)), x), reverse=True)[0] if titles else ""
        urls = set()
        distinct_source_rounds = 0
        preprint = False
        published = False
        award = False
        attribution = "NOT_CHECKED"
        provenance = []
        for path, doc in documents:
            new_urls = set(evidence_urls(doc)) - urls
            if new_urls:
                distinct_source_rounds += 1
            urls.update(new_urls)
            preprint = preprint or declared_original_preprint(doc)
            published = published or confirmed_original_published(doc)
            funding = doc.get("funding", {})
            if isinstance(funding, dict):
                if funding.get("primary_spark_award_match") == "VERIFIED":
                    award = True
                if funding.get("same_project_wpo_attribution") == "VERIFIED":
                    attribution = "VERIFIED"
                elif attribution != "VERIFIED" and funding.get("same_project_wpo_attribution"):
                    attribution = "UNRESOLVED"
            provenance.append({"path":path.relative_to(root).as_posix(), "sha256":sha(path)})
        # Multiple evidence notes repeating the same sources do not consume
        # distinct-source follow-up budget. One new-source note = one round.
        rounds = min(2, distinct_source_rounds)
        if preprint:
            publication = "PREPRINT"
        elif published:
            publication = "PUBLISHED"
        else:
            publication = "NOT_CHECKED"
        case = {
            "doi":doi, "title":raw_title, "cohort":"historical_crossref",
            "publication_status":publication,
            "primary_award_match":True if award else None,
            "project_attribution":attribution,
            "checked_sources":sorted(urls),
            "research_rounds":rounds,
            "secondary_identity_checked":False,
            "required_metadata_verified":False,
            "private_review_status":"NOT_VERIFIED",
            "source_evidence":provenance,
            "research_budget_exhausted":rounds >= 2,
        }
        decision_cases.append(case)
        coverage.append({"doi":doi,"research_notes":len(documents),
                         "research_rounds":rounds,"publication_status":publication,
                         "source_evidence":provenance,
                         "budget_exhausted":rounds >= 2,
                         "requires_formal_decision":True,
                         "original_and_expansion_status_unchanged":True})
    report = {"schema":"reach-scout-research-evidence-coverage-v1",
              "cohort":"historical_crossref",
              "files_scanned":len(files),
              "doi_case_count":len(decision_cases),
              "source_unlinked_files":unlinked,
              "supplemental_cohort_holds":supplemental_holds,
              "supplemental_cohort_hold_count":len(supplemental_holds),
              "bounded_cases":sum(x["budget_exhausted"] for x in coverage),
              "note":"Research evidence catalog, not completion or review staging. Original triage and expansion seeds unchanged.",
              "cases":coverage}
    return {"schema":"reach-scout-decision-cases-v1",
            "description":"Conservative automatic evaluation of historical Crossref source DOIs from append-only research evidence. Never auto-stage.",
            "cases":decision_cases}, report


def main():
    cases, report = build()
    for path, value in ((TARGET, cases), (PROVENANCE, report)):
        rendered = json.dumps(value, indent=2, ensure_ascii=False)+"\n"
        if not path.exists() or path.read_text(encoding="utf-8")!=rendered:
            path.write_text(rendered, encoding="utf-8")
    print(json.dumps({"cases":len(cases["cases"]),"research_files":report["files_scanned"],
                      "bounded_cases":report["bounded_cases"]}, indent=2))


if __name__ == "__main__":
    main()
