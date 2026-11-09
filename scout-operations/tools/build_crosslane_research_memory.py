#!/usr/bin/env python3
"""SHA-pinned, nonterminal Scout cross-lane research relationship memory.

Historical Crossref and DataCite origins, monthly originals, related-output
discovery, and independent leads retain separate original/expansion state.
Reuses existing publicly recorded evidence, but never treats prior notes as a
verified funding decision, finished expansion, private review, or publication.
"""
import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from decision_pipeline import norm_doi
from unified_source_preflight import preflight
from build_research_outcome_registry import build as research_registry

ROOT = Path(__file__).resolve().parents[2]
DEST = "scout-operations/research-memory/crosslane-relationship-graph.json"
SCHEMA = "reach-scout-crosslane-research-memory-v1"
RELATED = "scout-operations/monthly-expansion-leads.json"
INDEPENDENT = "scout-operations/independent-discovery-leads.json"
LEAD_DIR = "scout-operations/research-leads"
CHECKPOINT = "scout-operations/reports/doi-metadata-checkpoint/latest.json"
VALID_LANES = ("historical_crossref", "historical_datacite", "monthly_api",
               "monthly_related_outputs", "independent")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(data):
    return json.dumps(data, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def file_doc(root, rel):
    path = root / rel
    raw = path.read_bytes()
    return json.loads(raw), sha(raw)


def doi(value):
    d = norm_doi(value)
    return d or None


def exact_identifier(value):
    raw = str(value or "").strip()
    if raw.startswith("doi:"):
        raw = raw[4:]
    return doi(raw)


def require_sha(root, rel, expected):
    if not (root / rel).is_file() or sha((root / rel).read_bytes()) != expected:
        raise ValueError("Research graph source changed or missing: " + rel)


def source_links(root):
    """Only explicit DOI fields, never authors, abstracts or prose heuristics."""
    references = {}
    evidence_shas = {}
    for rel, label in ((RELATED, "monthly_related_outputs"),
                       (INDEPENDENT, "independent")):
        doc, checksum = file_doc(root, rel)
        expected = ("reach-scout-monthly-expansion-leads-v1" if label == "monthly_related_outputs"
                    else "reach-scout-independent-discovery-leads-v1")
        if doc.get("schema") != expected:
            raise ValueError("Unexpected related-output source schema: " + rel)
        evidence_shas[rel] = checksum
        for entry in doc.get("entries", []):
            child = exact_identifier(entry.get("identity"))
            if not child:
                raise ValueError("Related-output lead missing exact DOI identity")
            seed = doi(entry.get("original_seed_doi"))
            if seed and seed == child:
                raise ValueError("A related-output cannot link to itself")
            if seed:
                key = (seed, child)
                references.setdefault(key, set()).add((rel, label))

    base = root / LEAD_DIR
    if base.is_dir():
        for path in sorted(base.glob("*.json")):
            rel = path.relative_to(root).as_posix()
            source, checksum = file_doc(root, rel)
            # Research leads may be about a single original or have several
            # independently identified leads. Never extrapolate links from
            # narrative or person fields.
            leads = source.get("leads", [])
            if not isinstance(leads, list):
                continue
            evidence_shas[rel] = checksum
            for item in leads:
                if not isinstance(item, dict):
                    continue
                child = exact_identifier(item.get("identity") or item.get("output_url"))
                seed = doi(item.get("original_seed_doi"))
                if child and seed:
                    if child == seed:
                        raise ValueError("Self-related DOI in evidence lead: " + rel)
                    references.setdefault((seed, child), set()).add(
                        (rel, "independent_doi_evidence_lead"))
    return references, evidence_shas


def metadata_pointers(root):
    """Historical API metadata may be remembered, not assumed currently fresh."""
    path = root / CHECKPOINT
    if not path.is_file():
        return {}, None
    doc, checksum = file_doc(root, CHECKPOINT)
    records = doc.get("records")
    if not isinstance(records, list):
        raise ValueError("Invalid historical direct DOI checkpoint records")
    out = {}
    for item in records:
        d = doi(item.get("doi"))
        if not d:
            continue
        # Only a sha of the existing public metadata record is copied. Never
        # copy creators, abstracts or private data to new graph.
        fingerprint = sha(canonical(item.get("metadata", {})))
        if d in out and out[d] != fingerprint:
            raise ValueError("Conflicting DOI metadata checkpoints: " + d)
        out[d] = fingerprint
    return out, checksum


def build(root=ROOT):
    # Both functions revalidate their own underlying public source manifests
    # and source-file hashes. Do not rely on a stale generated preflight file.
    checked = preflight(root)
    journal = research_registry(root)
    if checked.get("schema") != "reach-scout-unified-source-preflight-v1":
        raise ValueError("Unrecognized unified preflight schema")
    if journal.get("schema") != "reach-scout-all-lane-research-outcomes-v1":
        raise ValueError("Unrecognized source-backed research journal")
    if sum(sum(v.values()) for v in checked["lane_decision_counts"].values()) != len(checked["cases"]):
        raise ValueError("Cross-lane preflight count drift")
    if len(checked["cases"]) != checked["original_and_related_cases_preflighted"]:
        raise ValueError("Partial cross-lane preflight source")
    for rel, checksum in journal["source_sha256"].items():
        require_sha(root, rel, checksum)

    edges, edge_sources = source_links(root)
    historic_metadata, historic_sha = metadata_pointers(root)
    node_rows = defaultdict(list)
    note_rows = defaultdict(list)
    cohort_pairs = set()
    for row in checked["cases"]:
        lane = row["discovery_lane"]
        d = doi(row["doi"])
        if lane not in VALID_LANES or not d:
            raise ValueError("Unrecognized discovery lane or DOI")
        pair = (lane, d)
        if pair in cohort_pairs:
            raise ValueError("Duplicate lane DOI in verified preflight: " + str(pair))
        cohort_pairs.add(pair)
        node_rows[d].append(row)

    # Only explicitly identified case notes may be replayed. No original or
    # separate expansion is ever deemed completed on this basis alone.
    for event in journal["events"]:
        d = doi(event.get("doi"))
        if d:
            note_rows[d].append(event)

    all_dois = set(node_rows) | set(note_rows)
    for parent, child in edges:
        all_dois.update((parent, child))

    children = defaultdict(list)
    parents = defaultdict(list)
    links = []
    for (parent, child), references in sorted(edges.items()):
        sources = [{"source_file": rel, "source_sha256": edge_sources[rel],
                    "relationship_origin": label}
                   for rel, label in sorted(references)]
        children[parent].append(child)
        parents[child].append(parent)
        links.append({"source_doi": parent, "related_doi": child,
                      "edge_type": "EXPLICIT_PUBLIC_DOI_RESEARCH_LEAD",
                      "source_files": sources,
                      "proven_distinct_eligible_output": False,
                      "funded_by_same_wpo_project": "NOT_VERIFIED",
                      "separate_expansion_complete": False,
                      "private_hub_import": "NOT_VERIFIED",
                      "reviewer_approval": "NOT_VERIFIED"})

    nodes = []
    work = []
    for d in sorted(all_dois):
        cases = sorted(node_rows[d], key=lambda c: c["discovery_lane"])
        events = sorted(note_rows[d], key=lambda v: (v["source_path"], v["event_id"]))
        lanes = sorted({x["discovery_lane"] for x in cases})
        verified_reach = any(
            x["discovery_lane"] == "historical_crossref"
            and x.get("effective_identity_or_preflight") == "EXISTING_IN_REACH_VERIFIED_BULK"
            and x.get("trusted_bulk_public_reach_uid")
            for x in cases
        )
        preprint = any(
            x.get("publication_status") == "PREPRINT" or
            str(x.get("public_identity_disposition", "")).startswith("PREPRINT")
            for x in cases
        )
        signatures = [
            {"lane": row["discovery_lane"], "preflight_sha256": row["evidence_input_sha256"],
             "public_identity": row["public_identity_disposition"],
             "effective_identity": row["effective_identity_or_preflight"]}
            for row in cases
        ]
        note_ids = sorted({e["event_id"] for e in events})
        prior_dispositions = sorted({e["operational_disposition"] for e in events})
        original_fingerprint = sha(canonical({"case_signatures": signatures,
                                               "prior_note_ids": note_ids}))
        expansion_fingerprint = sha(canonical({
            "original_fingerprint": original_fingerprint,
            "related_doi_ids": sorted(children[d]),
            "reference_source_shas": sorted({edge_sources[rel]
                for (src, _), refs in edges.items() if src == d
                for rel, _label in refs}),
        }))
        primary_role = "HISTORICAL_CROSSREF" if "historical_crossref" in lanes else (
            "HISTORICAL_DATACITE" if "historical_datacite" in lanes else (
                "MONTHLY" if "monthly_api" in lanes else "EXPLICIT_RELATED_RESEARCH"))
        record = {
            "doi": d, "lanes": lanes, "primary_role": primary_role,
            "public_reach_verified_existing": bool(verified_reach),
            "preprint_or_version_hold": bool(preprint),
            "original_research": {
                "input_fingerprint": original_fingerprint,
                "recorded_note_count": len(events),
                "recorded_note_event_ids": note_ids,
                "source_evidence_file_sha256": [
                    {"path": e["source_path"], "sha256": e["source_sha256"]}
                    for e in events
                ],
                "nonterminal_dispositions": prior_dispositions,
                "reuse_prior_notes_before_new_queries": bool(events),
                "identity_screened_current_snapshot": bool(cases),
                "formal_original_closed_by_memory": False,
            },
            "expansion_research": {
                "input_fingerprint": expansion_fingerprint,
                "explicit_related_doi_count": len(children[d]),
                "explicit_related_dois": sorted(children[d]),
                "explicit_parent_dois": sorted(parents[d]),
                "continue_new_distinct_output_exploration": bool(cases or children[d]),
                "separate_expansion_closed_by_memory": False,
            },
            "historical_exact_doi_metadata_pointer_sha256": historic_metadata.get(d),
            "historical_metadata_is_currently_verified": False,
            "no_authors_or_spark_personnel_in_graph": True,
            "funding_and_same_project_inference": "NOT_VERIFIED_BY_MEMORY",
            "private_hub_status": "NOT_VERIFIED",
            "reviewer_approved": False,
        }
        nodes.append(record)

        if cases and "monthly_related_outputs" not in lanes and "independent" not in lanes:
            if verified_reach:
                original = "REUSE_VERIFIED_REACH_IDENTITY_NO_DUPLICATE_ORIGINAL"
            elif preprint:
                original = "PREPRINT_WATCHLIST_NOT_ELIGIBLE_AS_ORIGINAL"
            elif events:
                original = "REUSE_SOURCE_VERIFIED_PRIOR_RESEARCH_NOT_CLOSURE"
            else:
                original = "ORIGINAL_SOURCE_SPECIFIC_RESEARCH_NEEDED"
            work.append({"doi": d, "track": "ORIGINAL", "lane": primary_role,
                         "next_action": original, "note_events_reused": len(events),
                         "input_fingerprint": original_fingerprint,
                         "can_skip_retrieving_unchanged_prior_note": bool(events),
                         "not_a_human_decision": True, "complete": False})
        if cases or children[d]:
            if verified_reach:
                expand_action = "EXPAND_VERIFIED_WPO_REACH_SEED"
            elif children[d]:
                expand_action = "CONTINUE_DISTINCT_RELATED_OUTPUT_VERIFICATION"
            elif preprint:
                expand_action = "PRESERVE_SEED_RELATED_RESEARCH_WITH_PREPRINT_HOLD"
            else:
                expand_action = "VERIFY_PROJECT_SCOPE_THEN_EXPAND"
            work.append({"doi": d, "track": "EXPANSION", "lane": primary_role,
                         "next_action": expand_action,
                         "existing_distinct_related_doi_links": len(children[d]),
                         "input_fingerprint": expansion_fingerprint,
                         "note_events_reused": len(events),
                         "can_skip_retrieving_unchanged_prior_note": bool(events),
                         "not_a_human_decision": True, "complete": False})
        if parents[d]:
            work.append({"doi": d, "track": "RELATED_OUTPUT", "lane": primary_role,
                         "next_action": "RECHECK_DISTINCT_OUTPUT_IDENTITY_AND_AWARD_PROOF",
                         "parent_seed_count": len(parents[d]),
                         "not_a_human_decision": True, "complete": False})

    if len(cohort_pairs) != checked["original_and_related_cases_preflighted"]:
        raise ValueError("Cohort coverage inconsistent")
    counts = Counter(x["track"] for x in work)
    lane_counts = Counter(lane for n in nodes for lane in n["lanes"])
    work_counts = Counter(x["next_action"] for x in work)
    # Merely closing original identity NEVER clears the candidate from the
    # research-memory expansion worklist.
    existing_reach_seeds = sum(x["public_reach_verified_existing"] for x in nodes)
    active_reach_expansion = sum(
        x["next_action"] == "EXPAND_VERIFIED_WPO_REACH_SEED" for x in work)
    if existing_reach_seeds != active_reach_expansion:
        raise ValueError("A verified REACH original was incorrectly lost as expansion seed")

    sources = {
        "verified_preflight_input_manifest_shas": checked["source_manifest_sha256"],
        "verified_preflight_identity_fingerprint": checked["identity_index_fingerprint"],
        "research_notes_sha256": dict(sorted(journal["source_sha256"].items())),
        "related_lead_file_sha256": dict(sorted(edge_sources.items())),
        "historical_metadata_checkpoint_sha256": historic_sha,
    }
    source_fingerprint = sha(canonical(sources))
    return {
        "schema": SCHEMA,
        "source_fingerprint": source_fingerprint,
        "source_evidence_sha256": sources,
        "preflighted_lane_doi_records": len(cohort_pairs),
        "distinct_public_doi_nodes": len(nodes),
        "explicit_related_output_links": len(links),
        "historical_note_events_reused_as_context": sum(len(v) for v in note_rows.values()),
        "source_documented_doi_nodes": sum(bool(v) for v in note_rows.values()),
        "verified_reach_originals_preserved_as_expansion_seeds": active_reach_expansion,
        "historical_metadata_pointers_not_treated_as_current": len(
            set(historic_metadata) & all_dois),
        "lane_doi_counts": dict(sorted(lane_counts.items())),
        "work_track_counts": dict(sorted(counts.items())),
        "work_action_counts": dict(sorted(work_counts.items())),
        "originals_closed_by_memory": 0,
        "expansions_closed_by_memory": 0,
        "human_reviewer_decisions_changed": 0,
        "hub_records_automatically_staged": 0,
        "new_reach_publications": 0,
        "preprint_hold_respected": True,
        "public_author_names_or_spark_personnel_indexed": False,
        "read_only": True,
        "policy": ("Reusable SHA-pinned historical research notes and explicit DOI "
                   "links are context only. Identity and preprint decisions always "
                   "come from live SHA-verified public preflight; original and "
                   "expansion research remain separate, funding and private "
                   "reviewer decisions are never inferred."),
        "nodes": nodes,
        "links": links,
        "work_items": work,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--check", action="store_true")
    p.add_argument("--summary", action="store_true")
    a = p.parse_args()
    output = build(ROOT)
    dest = ROOT / DEST
    raw = json.dumps(output, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    if a.check:
        if not dest.exists() or dest.read_text(encoding="utf-8") != raw:
            raise ValueError("Persistent cross-lane research memory is stale; rebuild")
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists() or dest.read_text(encoding="utf-8") != raw:
            dest.write_text(raw, encoding="utf-8")
    summary = {k: v for k, v in output.items()
               if k in ("source_fingerprint", "preflighted_lane_doi_records",
                        "distinct_public_doi_nodes", "explicit_related_output_links",
                        "historical_note_events_reused_as_context",
                        "verified_reach_originals_preserved_as_expansion_seeds",
                        "historical_metadata_pointers_not_treated_as_current",
                        "work_track_counts", "work_action_counts")}
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
