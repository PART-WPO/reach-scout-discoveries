#!/usr/bin/env python3
"""One bounded, source-backed expansion investigation when monthly originals are clear.

This is a research fallback, not a finished expansion decision or a public
review handoff. Existing REACH publications are SEEDS, never new originals.
"""
import argparse
import hashlib
import json
import re
import sys
from urllib.parse import urlsplit
from datetime import datetime, timedelta, timezone
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
from lookup_independent_dois import metadata as lookup_metadata
from source_driven_expansion import discover as discover_sources
from ir_reach_identity import verified_snapshot, identity_check
from noaa_ir_lookup import trusted_index
from wpo_awards import official_459_awards
from recover_related_output_source import recover as recover_related_source
from related_output_identity import screen as complete_related_identity

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


def pick_seed(graph, ledger, now, preferred=None):
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
    if preferred:
        filtered = [c for c in candidates if c[0] == norm(preferred)]
        if not filtered:
            raise ValueError("Manual seed is not eligible or remains on cooldown")
        return filtered[0]
    return candidates[0] if candidates else None


def cited_github_repo(lead):
    """Only an exact repository URL in official publisher context is a source lead.

    The recovery helper subsequently verifies the README's exact DOI; a random
    upstream dependency or user-supplied third-party GitHub link is not proof.
    """
    evidence_url = str(lead.get("source_url") or "")
    host = urlsplit(evidence_url).hostname
    if host not in {"agupubs.onlinelibrary.wiley.com", "onlinelibrary.wiley.com",
                    "www.nature.com", "link.springer.com", "journals.ametsoc.org"}:
        return None
    context = str(lead.get("context_excerpt") or "")
    found = re.search(r"https://github\\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\\.git)?", context, re.I)
    return found.group(0) if found else None


def bounded_research(root, graph, ledger, now, metadata_fn=lookup_metadata, *,
                     source_fn=None, identity_fn=None, recovery_fn=None,
                     identity_screen_fn=None, seed_override=None):
    selected = pick_seed(graph, ledger, now, preferred=seed_override)
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
    first_metadata = {}
    for doi in target_dois:
        try:
            metadata = metadata_fn(doi)
            if not isinstance(metadata, dict):
                metadata = {"status": "MALFORMED_METADATA_RESPONSE"}
        except Exception as err:
            # Explicit technical hold; NEVER claim missing publication or no WPO link.
            metadata = {"status": "OFFICIAL_METADATA_ACCESS_ERROR", "error_type": type(err).__name__}
        first_metadata[doi] = metadata
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
    # Source-driven DOI discovery is independent from preexisting graph edges.
    # Every new lead remains NONTERMINAL, even when publisher context is explicit.
    # Tests may inject source_fn and identity_fn without network or private data.
    source_discovery = {
        "schema": "reach-scout-source-driven-expansion-v1", "seed_doi": seed,
        "source_checks": [], "discovered_doi_leads": [],
        "status": "NOT_INSTRUMENTED", "new_public_candidates": 0,
        "private_hub_import": "NOT_VERIFIED",
    }
    screened_leads = []
    if source_fn is not None:
        try:
            if source_fn is discover_sources:
                # The public IR index verifies the seed DOI -> exact NOAA IR
                # landing page against every shard SHA before any PDF is read.
                ir_index = trusted_index(root)
                ir_matches = (ir_index or {}).get("dois", {}).get(seed, [])
                ir_url = ir_matches[0] if len(ir_matches) == 1 else None
                source_discovery = source_fn(seed, ir_url=ir_url)
            else:
                source_discovery = source_fn(seed)
            if source_discovery.get("seed_doi") != seed or source_discovery.get("schema") != "reach-scout-source-driven-expansion-v1":
                raise ValueError("Source discovery seed/schema mismatch")
            if len(source_discovery.get("discovered_doi_leads", [])) > 3:
                raise ValueError("Source discovery exceeded bounded lead limit")
        except (ValueError, OSError, TimeoutError) as err:
            source_discovery = {**source_discovery, "status": "SOURCE_DISCOVERY_TECHNICAL_HOLD",
                                "error_type": type(err).__name__, "discovered_doi_leads": []}
        public_cache = None
        public_leads = list(source_discovery.get("discovered_doi_leads", []))
        # The original graph's SHA-verified explicit related DOIs also need
        # source recovery and a complete identity decision, even when no new
        # publisher URL can be reached in this run.
        seen = {norm(x.get("doi")) for x in public_leads}
        for child in explicit[:2]:
            if child not in seen:
                public_leads.append({"doi": child,
                    "evidence_kind": "sha_verified_graph_related_doi",
                    "source_url": None, "context_excerpt": ""})
                seen.add(child)
        for lead in public_leads:
            child = norm(lead.get("doi"))
            if child == seed or not child.startswith("10.") or "/" not in child:
                continue
            meta = first_metadata.get(child)
            if meta is None:
                try:
                    meta = metadata_fn(child)
                except (OSError, ValueError, TimeoutError):
                    meta = {"status": "OFFICIAL_METADATA_ACCESS_ERROR"}
            if not isinstance(meta, dict):
                meta = {"status": "MALFORMED_METADATA_RESPONSE"}
            ok = meta.get("status") == "ok"
            github_repo = cited_github_repo(lead)
            recovery = None
            if not ok and recovery_fn is not None:
                try:
                    recovery = recovery_fn(
                        child, github_repo_url=github_repo,
                        github_source_url=lead.get("source_url") if github_repo else None)
                except (OSError, ValueError, TimeoutError) as err:
                    recovery = {"status": "SOURCE_ACCESS_FAILURE",
                                "reason": "NATIVE_RECOVERY_FAILURE:" + type(err).__name__}
            recovered = isinstance(recovery, dict) and recovery.get(
                "official_exact_doi_verified") is True
            official_title = meta.get("title") if ok else (
                (recovery or {}).get("title") or "")
            if identity_fn is not None:
                # Existing unit-test injection, still runs even when metadata
                # is unavailable. Production uses the complete live gate.
                try:
                    identity = identity_fn(child, official_title)
                except (ValueError, OSError, TypeError):
                    identity = {"status": "PUBLIC_IDENTITY_GATE_INCOMPLETE"}
            elif identity_screen_fn is not None:
                try:
                    identity = identity_screen_fn(
                        root, child, official_title, artifact_url=github_repo or "")
                except (ValueError, OSError, TypeError):
                    identity = {"status": "PUBLIC_IDENTITY_GATE_INCOMPLETE"}
            else:
                # Keep legacy offline/injected paths read-only; production uses
                # the full live canonical REACH gate above.
                try:
                    if public_cache is None:
                        public_cache = verified_snapshot(root)
                    identity = identity_check(public_cache[0], public_cache[1],
                                              child, official_title, "https://doi.org/" + child)
                except (ValueError, OSError, TypeError):
                    identity = {"status": "PUBLIC_IDENTITY_GATE_INCOMPLETE"}
            public_status = identity.get("status", "PUBLIC_IDENTITY_GATE_INCOMPLETE")
            ir_status = (identity.get("noaa_ir_reach_check") or {}).get(
                "status", "NOT_VERIFIED")
            awards = official_459_awards(meta) if ok else []
            if public_status in {"CONFIRMED_PUBLIC_REACH_IDENTITY", "IN_PUBLIC_SCOUT_QUEUE"}:
                next_gate = "EXISTING_PUBLIC_IDENTITY_NO_RESTAGING"
            elif meta.get("publication_status") == "preprint":
                next_gate = "PREPRINT_WATCHLIST_HOLD"
            elif public_status == "PUBLIC_IDENTITY_GATE_INCOMPLETE":
                next_gate = "PUBLIC_IDENTITY_GATE_INCOMPLETE"
            elif public_status != "NO_PUBLIC_IDENTITY_MATCH":
                next_gate = "BOUNDED_PUBLIC_IDENTITY_REVIEW"
            elif not ok and not recovered:
                next_gate = "OFFICIAL_METADATA_UNVERIFIED"
            elif not awards:
                # An exact source-backed output is a plausible review unit.
                # Its parent's 459 award is NOT transferred to the output.
                # No private Hub connection/ingestion is inferred.
                next_gate = ("REVIEW_READY_NEEDS_INVESTIGATION_NOT_DELIVERED"
                             if identity_screen_fn is not None else
                             "VERIFY_EXACT_OUTPUT_WPO_PROJECT_FUNDING")
            else:
                next_gate = "VERIFY_SEPARATE_OUTPUT_IDENTITY_AND_PROJECT_PARENT"
            screened_leads.append({
                "doi": child, "source_url": lead.get("source_url"),
                "source_sha256": lead.get("source_sha256"),
                "source_context_type": lead.get("evidence_kind"),
                "official_metadata_status": meta.get("status"),
                "official_metadata_url": meta.get("evidence") if ok else None,
                "official_title": official_title,
                "official_resource_type": meta.get("resource_type") if ok else (
                    (recovery or {}).get("resource_type")),
                "publication_status": meta.get("publication_status") if ok else "NOT_VERIFIED",
                "exact_doi_publisher_deposited_wpo_awards": awards,
                "public_identity_status": public_status,
                "public_identity_detail": identity,
                "official_ir_reach_status": ir_status,
                "native_source_recovery": recovery,
                "new_public_candidate_count": 0,
                "private_hub_import": "NOT_VERIFIED",
                "next_gate": next_gate,
                "eligibility": "RESEARCH_LEAD_ONLY_NOT_STAGED",
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
        "source_driven_discovery": source_discovery,
        "new_source_driven_leads_screened": screened_leads,
        "new_distinct_doi_leads_found": len({norm(x.get("doi")) for x in source_discovery.get("discovered_doi_leads", []) if norm(x.get("doi")) != seed}),
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


def run(root, now, run_id, metadata_fn=lookup_metadata, *, source_fn=None, identity_fn=None,
        recovery_fn=None, identity_screen_fn=None, seed_override=None):
    if not eligible_monthly_state(root):
        return {"status": "MONTHLY_ORIGINALS_HAVE_PRIORITY", "source_lookup_count": 0}
    graph, index = source_snapshot(root)
    ledger = read_ledger(root)
    report = bounded_research(root, graph, ledger, now, metadata_fn,
                              source_fn=source_fn, identity_fn=identity_fn,
                              recovery_fn=(recovery_fn if recovery_fn is not None else
                                           recover_related_source if source_fn is discover_sources else None),
                              identity_screen_fn=(identity_screen_fn if identity_screen_fn is not None else
                                                  complete_related_identity if source_fn is discover_sources else None),
                              seed_override=seed_override)
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
            "source_driven_leads_found": report.get("new_distinct_doi_leads_found", 0),
            "source_lookup_count": len(report["source_lookups"]),
            "source_verified_lookups": sum(x["source_status"]=="ok" for x in report["source_lookups"]),
            "research_report": rel, "new_public_candidates": 0, "completed_expansions": 0}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--seed-doi", default=None, help="Optional verified REACH seed for controlled positive-control replay")
    args = ap.parse_args()
    result = run(args.root, datetime.now(timezone.utc), args.run_id, source_fn=discover_sources, seed_override=args.seed_doi)
    print(json.dumps(result,sort_keys=True))


if __name__ == "__main__":
    main()
