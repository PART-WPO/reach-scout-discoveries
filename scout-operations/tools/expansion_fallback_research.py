#!/usr/bin/env python3
"""One bounded, source-backed expansion investigation when monthly originals are clear.

This is a research fallback, not a finished expansion decision or a public
review handoff. Existing REACH publications are SEEDS, never new originals.
"""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
from lookup_independent_dois import metadata as lookup_metadata

ROOT = Path(__file__).resolve().parents[2]
GRAPH = "scout-operations/research-memory/crosslane-relationship-graph.json"
INDEX = "scout-operations/research-memory/mission-index.json"
WORKSTREAM = "scout-operations/active-workstream.json"
LEDGER = "scout-operations/research-memory/expansion-fallback-ledger.json"
REPORTS = "scout-operations/reports/bounded-expansion-research"
SCHEMA = "reach-scout-expansion-fallback-v1"
RESEARCH_SCHEMA = "reach-scout-bounded-expansion-research-v1"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def load(root, relative):
    return json.loads((root / relative).read_text(encoding="utf-8"))


def norm(value):
    x = str(value or "").strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if x.startswith(prefix):
            x = x[len(prefix):]
    return x


def source_snapshot(root):
    graph = load(root, GRAPH)
    index = load(root, INDEX)
    if graph.get("schema") != "reach-scout-crosslane-research-memory-v1" or \
       index.get("schema") != "reach-scout-compact-crosslane-mission-index-v1":
        raise ValueError("Unexpected source-verified cross-lane graph or index schema")
    if (graph.get("source_fingerprint") != index.get("source_fingerprint")
        or graph.get("builder_policy_sha256") != index.get("builder_policy_sha256")):
        raise ValueError("STALE_CROSSLANE_INDEX")
    # The existing graph builder stored SHA-verified public source records.
    # An identity or source-note mutation must not silently turn an old seed
    # into a new attribution claim.
    source = graph.get("source_evidence_sha256") or {}
    for category in ("research_notes_sha256", "related_lead_file_sha256"):
        for rel, expected in source.get(category, {}).items():
            if (not rel.startswith("scout-operations/") or ".." in Path(rel).parts
                or not (root / rel).is_file()
                or digest((root / rel).read_bytes()) != expected):
                raise ValueError("STALE_EXPANSION_SOURCE: " + rel)
    return graph, index


def eligible_monthly_state(root):
    state = load(root, WORKSTREAM)
    monthly = state.get("monthly_api") or {}
    # Never steal time from outstanding monthly original decisions.
    return not any(int(monthly.get(k) or 0) for k in (
        "original_decisions_due", "originals_for_final_checks",
        "pending_metadata_blockers_including_originals"))


def read_ledger(root):
    p = root / LEDGER
    if not p.exists():
        return {"schema": SCHEMA, "cases": {}}
    data = json.loads(p.read_text(encoding="utf-8"))
    if data.get("schema") != SCHEMA or not isinstance(data.get("cases"), dict):
        raise ValueError("Unknown expansion fallback ledger schema")
    return data


def pick_seed(graph, ledger, now):
    nodes = {n["doi"]: n for n in graph.get("nodes", [])}
    candidates = []
    for task in graph.get("work_items", []):
        if task.get("track") != "EXPANSION" or task.get("next_action") != "EXPAND_VERIFIED_WPO_REACH_SEED":
            continue
        doi = norm(task.get("doi"))
        node = nodes.get(doi) or {}
        if not node.get("public_reach_verified_existing") or node.get("preprint_or_version_hold"):
            continue
        info = node.get("expansion_research") or {}
        if info.get("separate_expansion_closed_by_memory"):
            continue
        fingerprint = info.get("input_fingerprint")
        if not isinstance(fingerprint, str) or len(fingerprint) != 64:
            raise ValueError("Missing verified expansion seed fingerprint: " + doi)
        previous = ledger["cases"].get(doi)
        if previous and previous.get("source_fingerprint") == fingerprint:
            until = previous.get("recheck_after")
            if until and now < datetime.fromisoformat(until.replace("Z", "+00:00")):
                continue
        candidates.append((doi, node, fingerprint))
    candidates.sort(key=lambda x: (-len(x[1]["expansion_research"].get("explicit_related_dois") or []),
                                   x[1]["expansion_research"].get("recorded_related_note_count",0),
                                   x[0]))
    return candidates[0] if candidates else None


def bounded_research(root, graph, ledger, now, metadata_fn=lookup_metadata):
    selected = pick_seed(graph, ledger, now)
    if not selected:
        return None
    seed, node, fingerprint = selected
    explicit = sorted(set(norm(d) for d in (
        node["expansion_research"].get("explicit_related_dois") or []) if norm(d) != seed))
    # Every remembered DOI relationship must have a public SHA-backed edge.
    for child in explicit:
        links = [e for e in graph.get("links", []) if e.get("source_doi") == seed
                 and e.get("related_doi") == child]
        if not links or not links[0].get("source_files"):
            raise ValueError("UNVERIFIED_RELATED_LINK: " + seed + " -> " + child)
        for evidence in links[0]["source_files"]:
            rel = evidence["source_file"]
            if (not rel.startswith("scout-operations/") or ".." in Path(rel).parts
                or not (root / rel).is_file()
                or digest((root / rel).read_bytes()) != evidence["source_sha256"]):
                raise ValueError("STALE_RELATED_LINK_EVIDENCE: " + rel)
    target_dois = [seed] + explicit[:2]
    checked = []
    for doi in target_dois:
        try:
            metadata = metadata_fn(doi)
            if not isinstance(metadata, dict):
                metadata = {"status": "MALFORMED_METADATA_RESPONSE"}
        except Exception as err:
            # Explicit technical hold; NEVER claim missing publication or no WPO link.
            metadata = {"status": "OFFICIAL_METADATA_ACCESS_ERROR", "error_type": type(err).__name__}
        good = metadata.get("status") == "ok"
        checked.append({
            "doi": doi, "role": "VERIFIED_REACH_EXPANSION_SEED" if doi == seed else "EXPLICIT_RELATED_DOI_LEAD",
            "source_status": metadata.get("status", "UNKNOWN"),
            "official_provider": metadata.get("provider") if good else None,
            "official_title": metadata.get("title") if good else None,
            "official_metadata_url": metadata.get("evidence") if good else None,
            "publication_status": metadata.get("publication_status") if good else "NOT_VERIFIED",
            "official_award_numbers_observed": sorted({
                str(award).strip().upper()
                for x in (metadata.get("funding_references") or []) if isinstance(x, dict)
                for award in (x.get("award") or []) if isinstance(award, str)
            }) if good else [],
            "separate_output_uniqueness": "NOT_VERIFIED",
            "same_WPO_project_parent": "NOT_VERIFIED",
        })
    succeeded = sum(x["source_status"] == "ok" for x in checked)
    status = "OFFICIAL_SOURCE_CHECK_RECORDED" if succeeded else "TECHNICAL_ACCESS_HOLD"
    prior = ledger["cases"].get(seed, {})
    retry_days = 21 if succeeded else 2
    # Permanently skip the same source fingerprint for a bounded interval;
    # a newly evidenced graph fingerprint reopens immediately.
    ledger["cases"][seed] = {
        "status": status, "source_fingerprint": fingerprint,
        "checked_at": now.isoformat(),
        "recheck_after": (now + timedelta(days=retry_days)).isoformat(),
        "attempt_count": int(prior.get("attempt_count") or 0) + 1,
        "official_lookups_completed": succeeded,
        "private_hub_import": "NOT_VERIFIED",
    }
    return {
        "schema": RESEARCH_SCHEMA, "observed_at_utc": now.isoformat(),
        "seed_doi": seed, "source_graph_sha256": graph["source_fingerprint"],
        "seed_expansion_fingerprint": fingerprint,
        "seed_reach_identity_verified_in_graph": True,
        "explicit_related_dois_preserved": explicit,
        "source_lookups": checked, "status": status,
        "new_public_candidate_count": 0,
        "new_related_output_eligibility_confirmed": 0,
        "separate_expansion_decisions_completed": 0,
        "reason_not_a_completed_expansion": "Source metadata and DOI edges are research leads; distinct output identity, preprint, public REACH/Scout duplicate and exact WPO project funding require independent checks.",
        "next_action": ("Investigate official metadata and full current REACH/Scout identity "
                        "for distinct linked DOI(s); verify their OWN publisher award and primary SPARK parent "
                        "before any Needs Investigation or New Candidate."),
        "private_hub_import": "NOT_VERIFIED",
        "human_approval": "NOT_VERIFIED",
    }


def run(root, now, run_id, metadata_fn=lookup_metadata):
    if not eligible_monthly_state(root):
        return {"status": "MONTHLY_ORIGINALS_HAVE_PRIORITY", "source_lookup_count": 0}
    graph, index = source_snapshot(root)
    ledger = read_ledger(root)
    report = bounded_research(root, graph, ledger, now, metadata_fn)
    if report is None:
        return {"status": "NO_ELIGIBLE_UNWORKED_EXPANSION_SEED", "source_lookup_count": 0}
    # One immutable research record per observed GitHub execution. The report
    # is not a ChatGPT completed-mission record under PR #77's separate schema.
    if not run_id.isdigit():
        raise ValueError("GitHub run ID must be numeric")
    suffix = digest(report["seed_doi"].encode())[:12]
    rel = REPORTS + "/github-" + run_id + "-" + suffix + ".json"
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise ValueError("Do not overwrite a prior bounded expansion note")
    path.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    ledger["cases"][report["seed_doi"]]["research_report"] = rel
    dest = root / LEDGER
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(ledger,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return {"status": report["status"], "seed": report["seed_doi"],
            "related_leads_checked": len(report["source_lookups"])-1,
            "source_lookup_count": len(report["source_lookups"]),
            "source_verified_lookups": sum(x["source_status"]=="ok" for x in report["source_lookups"]),
            "research_report": rel, "new_public_candidates": 0, "completed_expansions": 0}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--run-id", required=True)
    args = ap.parse_args()
    result = run(args.root, datetime.now(timezone.utc), args.run_id)
    print(json.dumps(result,sort_keys=True))


if __name__ == "__main__":
    main()
