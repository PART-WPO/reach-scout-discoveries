#!/usr/bin/env python3
"""Conservative, source-SHA-pinned extraction from existing public Scout notes.

No external network calls; no source text is rewritten; only explicitly
structured fields are interpreted. Publication or award clues are NOT
proof of a fresh REACH/Scout duplicate screen, exact project funding,
complete 24-column metadata, or authorized human decision.
"""
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
REG = "scout-operations/research-outcome-registry.json"
VERSION = "reach-scout-public-evidence-extraction-v1"

PUBLISHED = frozenset({
    "PUBLISHED", "PUBLICLY_RELEASED", "PUBLISHED_JOURNAL_ARTICLE",
    "PUBLISHED_JOURNAL_ARTICLE_INSTITUTIONAL_BIBLIOGRAPHY",
    "OFFICIAL_JOURNAL_PUBLICATION_VERIFIED",
    "NOAA_IR_CATALOG_IDENTIFIED_JOURNAL_ARTICLE",
    "PUBLISHED_JOURNAL_ARTICLE_PER_NOAA_IR_NOT_PREPRINT",
    "PUBLISHER_JOURNAL_ARTICLE_NOT_ORIGINAL_PREPRINT",
    "OFFICIAL_PUBLISHED_JOURNAL_ARTICLE",
})
PREPRINT = frozenset({"PREPRINT", "PREPRINT_HOLD", "ORIGINAL_PREPRINT",
                      "ORIGINAL_PREPRINT_HOLD", "PREPRINT_WATCHLIST_HOLD"})
PUBLISHED_KEYS = ("publication_status", "official_publication_identity",
                  "preprint_eligibility", "preprint_status", "publisher_version")
AWARD_KEYS = ("primary_spark_award_verified", "spark_primary_award_verified",
              "primary_spark_exact_match", "exact_primary_spark_award_verified")
SAME_PROJECT_KEYS = ("project_attribution", "output_to_primary_project_proof",
                     "project_deliverable_proof", "same_project_wpo_funding",
                     "same_project_award_verified", "wpo_funding")
FUNDING_CONTRADICTION = frozenset({
    "CONTRADICTORY_TO_PILOT_PROJECT_AWARD",
    "NOT_CORROBORATED_AND_PARENT_PUBLICATION_HAS_CONTRADICTORY_AWARD",
    "VERIFIED_DIFFERENT_PROJECT",
    "DISPROVED",
    "CONTRADICTED",
})
URL_KEYS = ("source_evidence", "sources", "verified_sources", "evidence",
            "new_source_findings", "independent_sources_checked",
            "official_source", "official_publisher_url", "official_noaa_ir_url",
            "publisher_url", "noaa_ir_url", "initial_source",
            "distinct_source_followup", "independent_program_source")
MATCH_YES = frozenset({"VERIFIED_EXACT_PRIMARY_MATCH",
                       "VERIFIED_IN_PRIMARY_AWARD_COLUMN", "VERIFIED_PRIMARY_SPARK_AWARD",
                       "VERIFIED_SAME_PROJECT", "CONFIRMED_SAME_PROJECT"})

def sha(data):
    return hashlib.sha256(data).hexdigest()

def norm_doi(value):
    x = str(value or "").strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if x.startswith(prefix):
            x = x[len(prefix):]
    return x

def norm_url(value):
    return str(value or "").strip().lower().rstrip("/")

def verified_note(root, event):
    rel = event["source_path"]
    full = (root / rel).resolve()
    if not full.is_relative_to(root.resolve()) or not full.is_file():
        raise ValueError("Unsafe or missing public note: " + rel)
    raw = full.read_bytes()
    if sha(raw) != event["source_sha256"]:
        raise ValueError("Public note SHA mismatch: " + rel)
    doc = json.loads(raw)
    if not isinstance(doc, dict):
        raise ValueError("Non-object public note: " + rel)
    return doc

def note_scope(doc, event):
    """Never attribute a parent statement to its discovered child DOI."""
    identity = event["identity"]
    if "cases" in doc:
        if not isinstance(doc["cases"], list):
            raise ValueError("Note cases must be an array")
        matched = [x for x in doc["cases"]
                   if isinstance(x, dict) and x.get("doi")
                   and identity == "doi:" + norm_doi(x["doi"])]
        if len(matched) != 1:
            raise ValueError("Ambiguous source-note identity: " + identity)
        return matched[0], "/cases/" + str(doc["cases"].index(matched[0])), True
    subject = doc.get("research_subject")
    if isinstance(subject, dict) and subject.get("child_dois"):
        if identity not in ["doi:" + norm_doi(x) for x in subject["child_dois"]]:
            raise ValueError("Unmatched related DOI: " + identity)
        # Funding/project assertions in this parent/child note are only
        # general cautions, not child metadata or award verification.
        return {}, "/research_subject/child_dois", True
    if identity.startswith("url:"):
        stated = (doc.get("identity") or {}).get("canonical_url")
        if not stated or norm_url(stated) != norm_url(identity[4:]):
            raise ValueError("Unmatched code identity: " + identity)
    else:
        values = [doc.get(x) for x in ("doi", "original_doi",
                   "source_parent_original_doi", "parent_original_doi") if doc.get(x)]
        if values and "doi:" + norm_doi(values[0]) != identity:
            raise ValueError("Note DOI differs from registry event: " + identity)
    return doc, "", False

def true_only(value):
    return value is True or (isinstance(value, str) and value.strip().lower() == "true")

def textflag(value):
    return str(value or "").strip().upper()

def source_urls(node):
    """Only URLs in explicit evidence/source fields, never author/citation prose."""
    found = set()
    def rec(value):
        if isinstance(value, str):
            if (value.startswith("https://") and not any(x.isspace() for x in value)
                    and "@" not in urlsplit(value).netloc):
                found.add(value)
        elif isinstance(value, list):
            for v in value:
                rec(v)
        elif isinstance(value, dict):
            for k, v in value.items():
                if k in ("url", "source", "source_url", "publisher_url",
                         "official_ir_url", "evidence_url"):
                    rec(v)
    for key in URL_KEYS:
        if key in node:
            rec(node[key])
    return sorted(found)

def count_int(obj, key):
    v = obj.get(key)
    try:
        n = int(v) if isinstance(v, (str, int)) and str(v).strip().isdigit() else 0
        return min(n, 10)
    except (TypeError, ValueError):
        return 0

def counts(node):
    initial = max(count_int(node, k) for k in
                  ("initial_checks", "research_checks", "initial_research_count"))
    follow = max(count_int(node, k) for k in
                 ("distinct_source_followups", "distinct_source_followup_count",
                  "distinct_followup_count"))
    passes = node.get("research_passes")
    if isinstance(passes, dict):
        initial = max(initial, count_int(passes, "initial_count"))
        follow = max(follow, count_int(passes, "distinct_followup_count"))
    research = node.get("research")
    if isinstance(research, dict):
        initial = max(initial, int(bool(research.get("initial"))))
        follow = max(follow, int(bool(research.get("distinct_source_followup"))))
    stage = textflag(node.get("research_stage"))
    if stage == "BOUNDED_INITIAL_PLUS_DISTINCT_INSTITUTIONAL_FOLLOWUP":
        initial, follow = max(initial, 1), max(follow, 1)
    return initial, follow

def extract(registry, root=ROOT):
    """Extract only facts explicitly recorded for each registry identity."""
    events_by_id = {e["event_id"]: e for e in registry["events"]}
    if len(events_by_id) != len(registry["events"]):
        raise ValueError("Duplicate source event ids")
    docs = {}
    for event in registry["events"]:
        rel = event["source_path"]
        if rel not in docs:
            docs[rel] = verified_note(root, event)
        else:
            verified_note(root, event)  # source SHA still checked for each event
    extracted = {}
    for case in registry["cases"]:
        identity = case["identity"]
        urlset, provenance, statuses, raw_fields = set(), [], set(), {}
        max_initial = max_follow = 0
        award_exact = same_project = contradiction = reopen_only = False
        cohort = "historical_or_independent"
        for eid in case["event_ids"]:
            event = events_by_id[eid]
            doc = docs[event["source_path"]]
            scoped, pointer, is_child = note_scope(doc, event)
            # Shared source URLs may corroborate that a relationship was
            # investigated; they do not verify the child identity or funding.
            urlset.update(source_urls(scoped))
            if is_child:
                urlset.update(source_urls(doc))
            note_decision = textflag(scoped.get("decision") or scoped.get("operational_disposition")
                                      or doc.get("operational_disposition"))
            note_action = str(scoped.get("next_action") or doc.get("next_action") or "")
            if note_decision.startswith("SOFT_DEFER_UNTIL_MATERIAL_") or note_action.lower().startswith("only reopen if"):
                reopen_only = True
            if (event["source_path"].startswith("scout-operations/monthly-research/")
                and event.get("role_in_note") in ("original", "original_followup_and_expansion_leads")
                and textflag(doc.get("origin")) == "DIRECT API"):
                cohort = "monthly_direct_api"
            if is_child:
                # Parent has no verified child project/metadata facts.
                src_node = scoped
            else:
                src_node = scoped
            for key in PUBLISHED_KEYS:
                if key not in src_node:
                    continue
                val = textflag(src_node[key])
                st = None
                if val in PREPRINT:
                    st = "PREPRINT"
                elif val in PUBLISHED or (key == "publisher_version" and val == "VERSION OF RECORD"):
                    st = "PUBLISHED"
                if st:
                    statuses.add(st)
                    raw_fields.setdefault("publication_status", []).append(
                        {"path": event["source_path"], "sha256": event["source_sha256"],
                         "pointer": pointer + "/" + key, "value": st})
            for key in AWARD_KEYS:
                if key in src_node and (true_only(src_node[key]) or textflag(src_node[key]) in MATCH_YES):
                    award_exact = True
                    raw_fields.setdefault("primary_award_match", []).append(
                        {"path": event["source_path"], "sha256": event["source_sha256"],
                         "pointer": pointer + "/" + key, "value": "VERIFIED_PRIMARY_MATCH_CLAIM"})
            for key in SAME_PROJECT_KEYS:
                if key in src_node and textflag(src_node[key]) in ("VERIFIED_SAME_PROJECT", "CONFIRMED_SAME_PROJECT"):
                    same_project = True
                    raw_fields.setdefault("project_attribution", []).append(
                        {"path": event["source_path"], "sha256": event["source_sha256"],
                         "pointer": pointer + "/" + key, "value": "VERIFIED_SAME_PROJECT_CLAIM"})
            for key in ("funding", "same_project_wpo_funding", "project_attribution", "award_evidence_status"):
                if key in src_node and textflag(src_node[key]) in FUNDING_CONTRADICTION:
                    contradiction = True
                    raw_fields.setdefault("contradiction", []).append(
                        {"path": event["source_path"], "sha256": event["source_sha256"],
                         "pointer": pointer + "/" + key, "value": "EXPLICIT_CONTRADICTION"})
            a, b = counts(src_node)
            if not is_child:
                max_initial = max(max_initial, a)
                max_follow = max(max_follow, b)
            provenance.append({"path": event["source_path"], "sha256": event["source_sha256"],
                               "event_id": eid, "case_pointer": pointer,
                               "role_in_note": event.get("role_in_note")})
        status = ("CONFLICTING_VERSION_EVIDENCE" if len(statuses) > 1
                  else next(iter(statuses)) if statuses else "NOT_CHECKED")
        # Positive same-project claims require an exact primary award too;
        # explicit contradictory evidence stops any positive recommendation.
        attrib = ("CONTRADICTED" if contradiction else
                  "VERIFIED_SAME_PROJECT" if same_project and award_exact else "NOT_CHECKED")
        case_data = {
            "publication_status": status,
            "primary_award_match": True if award_exact else None,
            "project_attribution": attrib,
            "cohort": cohort,
            # A note's "not found" identity or old source pointer NEVER
            # supplies a fresh SHA-checked REACH+Scout+NOAA IR decision.
            "secondary_identity_checked": False,
            "required_metadata_verified": False,
            "checked_sources": sorted(urlset),
            "research_rounds": max_initial + min(max_follow, 1),
            "research_budget_exhausted": max_initial > 0 and max_follow > 0,
            "evidence_reopen_only": reopen_only,
            "technical_metadata_retry": case.get("latest_operational_disposition") == "TECHNICAL_METADATA_RECOVERY",
            "evidence_conflicts": sorted(statuses) if len(statuses) > 1 else [],
            "source_evidence": provenance,
            "field_provenance": raw_fields,
            "structured_from_existing_notes_only": True,
        }
        extracted[identity] = case_data
    if len(extracted) != registry["distinct_research_identities"]:
        raise ValueError("Identity/extraction count mismatch")
    return extracted

def report(root=ROOT):
    raw = (root / REG).read_bytes()
    registry = json.loads(raw)
    data = extract(registry, root)
    return {
        "schema": VERSION, "read_only": True, "no_external_requests": True,
        "registry_sha256": sha(raw),
        "identities_with_pinned_notes": len(data),
        "identities_with_explicit_publication_evidence":
            sum(v["publication_status"] in ("PUBLISHED", "PREPRINT") for v in data.values()),
        "identities_with_primary_award_claim":
            sum(v["primary_award_match"] is True for v in data.values()),
        "identities_with_verified_current_duplicate_screen":
            sum(v["secondary_identity_checked"] for v in data.values()),
        "automatic_proposals": 0, "private_hub_write": False,
        "cases": data,
    }

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--output", default="scout-operations/reports/extracted-public-evidence-pilot.json")
    p.add_argument("--check", action="store_true")
    args = p.parse_args()
    out = (ROOT / args.output).resolve()
    if not out.is_relative_to(ROOT.resolve()):
        raise SystemExit("Unsafe output path")
    raw = (json.dumps(report(), indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode()
    if args.check:
        if not out.is_file() or out.read_bytes() != raw:
            raise SystemExit("Extracted public evidence artifact missing or stale")
        print("Source SHA-verified evidence extraction check PASS")
    else:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(raw)
        print("Extracted structured facts from SHA-verified notes; no external research or live edits")
