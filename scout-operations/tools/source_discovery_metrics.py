#!/usr/bin/env python3
"""Evidence-based counters for independently executed GitHub expansion research.

Count investigated seeds and newly evidenced DOI identities, NOT completed outputs.
Read-only against immutable public research notes; never access private Hub data.
"""
import hashlib
import json
import re
from pathlib import Path

REPORT_DIR = Path("scout-operations/reports/bounded-expansion-research")
SCHEMA = "reach-scout-bounded-expansion-research-v1"
SOURCE_SCHEMA = "reach-scout-source-driven-expansion-v1"
SHA = re.compile(r"^[a-f0-9]{64}$")


def norm(value):
    s = str(value or "").strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if s.startswith(prefix):
            s = s[len(prefix):]
    if not s.startswith("10.") or "/" not in s:
        raise ValueError("Invalid source-discovery DOI")
    return s


def summary(root):
    roots = root / REPORT_DIR
    files = sorted(roots.glob("*.json")) if roots.exists() else []
    seeds, leads, metadata_verified, source_reports, checked = set(), set(), set(), 0, {}
    decisions = handoffs = 0
    for path in files:
        raw = path.read_bytes()
        obj = json.loads(raw)
        if obj.get("schema") != SCHEMA or obj.get("seed_reach_identity_verified_in_graph") is not True:
            raise ValueError("Non-verified expansion research report: " + str(path))
        seed = norm(obj.get("seed_doi"))
        if not SHA.fullmatch(str(obj.get("source_graph_sha256") or "")):
            raise ValueError("Unpinned cross-lane source for " + seed)
        if not SHA.fullmatch(str(obj.get("seed_expansion_fingerprint") or "")):
            raise ValueError("Unpinned seed fingerprint for " + seed)
        if obj.get("private_hub_import") != "NOT_VERIFIED" or obj.get("human_approval") != "NOT_VERIFIED":
            raise ValueError("Expansion research cannot assert human review")
        seed_sources = obj.get("source_lookups", [])
        if not seed_sources or seed_sources[0].get("role") != "VERIFIED_REACH_EXPANSION_SEED" or norm(seed_sources[0].get("doi")) != seed:
            raise ValueError("Missing verified REACH seed lookup")
        ds = obj.get("source_driven_discovery")
        screened = obj.get("new_source_driven_leads_screened") or []
        if ds is not None:
            if ds.get("schema") != SOURCE_SCHEMA or norm(ds.get("seed_doi")) != seed:
                raise ValueError("Invalid official-source discovery evidence")
            source_reports += 1
            source_hashes = {
                c["source_sha256"] for c in ds.get("source_checks", [])
                if c.get("status") == "SOURCE_READ" and SHA.fullmatch(str(c.get("source_sha256", "")))
            }
            raw_leads = {norm(l.get("doi")) for l in ds.get("discovered_doi_leads", [])}
            for lead in screened:
                key = norm(lead.get("doi"))
                if key == seed or key not in raw_leads or lead.get("source_sha256") not in source_hashes:
                    raise ValueError("Unpinned/reused source-driven DOI lead: " + key)
                if lead.get("eligibility") != "RESEARCH_LEAD_ONLY_NOT_STAGED":
                    raise ValueError("Research lead was incorrectly staged")
                leads.add(key)
                if lead.get("official_metadata_status") == "ok":
                    metadata_verified.add(key)
            if obj.get("new_distinct_doi_leads_found") != len(screened):
                raise ValueError("Lead count contradicts screened research evidence")
        elif screened or obj.get("new_distinct_doi_leads_found", 0):
            raise ValueError("Unattributed research lead without source checks")
        decisions += obj.get("separate_expansion_decisions_completed", 0)
        handoffs += obj.get("new_public_candidate_count", 0)
        for count in (obj.get("new_related_output_eligibility_confirmed", 0),
                      obj.get("separate_expansion_decisions_completed", 0),
                      obj.get("new_public_candidate_count", 0)):
            if type(count) is not int or count < 0:
                raise ValueError("Invalid expansion completion/handoff count")
        seeds.add(seed)
        checked[path.relative_to(root).as_posix()] = hashlib.sha256(raw).hexdigest()
    return {
        "verified_research_report_count": len(files),
        "distinct_verified_reach_seeds_investigated": len(seeds),
        "distinct_seed_dois": sorted(seeds),
        "source_driven_research_report_count": source_reports,
        "new_distinct_source_backed_doi_leads": len(leads),
        "distinct_source_backed_doi_leads": sorted(leads),
        "new_leads_with_official_metadata_retrieved": len(metadata_verified),
        "completed_distinct_expansion_decisions": decisions,
        "new_public_candidates_from_these_expansions": handoffs,
        "source_report_sha256": checked,
        "private_hub_imports": "NOT_VERIFIED",
        "human_approvals": "NOT_VERIFIED",
        "interpretation": "Distinct seeds, DOI leads and official metadata retrieval are research progress, not completed expansions or public candidate/REACH additions.",
    }
