#!/usr/bin/env python3
"""Read-only triage of earlier public-REACH-anchored Crossref author pilot leads.

Each lead is independently evaluated for author identity, research topic,
structured award evidence and its public identity. Crossref author names are
processed ONLY in memory. Never read SPARK or promote to Discovery Hub.
All outcomes are provisional research priorities, not eligibility decisions.
"""
import argparse
from collections import Counter
import json
import re
import urllib.parse

from decision_pipeline import ROOT, norm_doi, norm_title, read_json, sha_file
from identity_disposition import verified_disposition
from ir_reach_identity import verified_snapshot
from reach_author_pilot import (
    CACHE_PATH, WATCHLIST_PATH, accepted_public_journal_source,
    author_identity_key, get_crossref_json, publication_dois
)

AWARD = "NA22OAR4590515"
PILOT_SCHEMA = "reach-scout-public-reach-author-pilot-v1"
OUTPUT_SCHEMA = "reach-scout-author-safeguards-replay-v1"

# A deliberately narrow profile for this *award*, built from its existing
# public REACH atmospheric composition, air-pollution and emissions work.
# Other awards MUST get their own public-evidence-grounded profiles.
TARGET_TERMS = (
    r"air[\s-]+quality", r"air[\s-]+pollut", r"airborne[\s-]+pollut",
    r"atmospher", r"nitrogen[\s-]+oxid", r"\bNOX\b", r"\bNO2\b",
    r"\bPM\s*2[.]?5\b", r"particulate[\s-]+matter",
    r"aerosol", r"ozone", r"wildfire[\s-]+smoke",
    r"greenhouse[\s-]+gas", r"\bemissions?\b",
    r"chemical[\s-]+transport", r"\bCMAQ\b", r"\bTROPOMI\b",
    r"ambient[\s-]+air", r"air[\s-]+pollution"
)
CONTEXT_TERMS = (
    r"climate", r"environment", r"sustainab", r"meteorolog",
    r"geospatial", r"remote[\s-]+sens", r"urban", r"weather", r"\bheat\b"
)
CROSS_DOMAIN_TERMS = (
    r"clinical", r"oncolog", r"cancer", r"retinal", r"medicine",
    r"psychia", r"semaglutide", r"pharmac", r"health[\s-]+equity",
    r"music", r"rhythm", r"poem", r"bank", r"tax", r"marketing",
    r"retail", r"adolescen", r"television", r"bioethic",
    r"finance", r"financial", r"university[\s-]+lectur"
)
NOAA_AWARD = re.compile(r"(?<![A-Z0-9-])(NA[0-9]{2}[A-Z0-9]+(?:-[A-Z0-9]+)*)(?![A-Z0-9-])", re.I)


def topical_evidence(title):
    """No generic 'risk' or name-overlap shortcut to topical relevance."""
    matches = sorted(set(
        m.group(0).casefold()
        for pattern in TARGET_TERMS
        for m in re.finditer(pattern, title, flags=re.I)
    ))
    if matches:
        return "DIRECT_ATMOSPHERIC_AIR_QUALITY_TOPIC", matches[:6]
    possible = any(re.search(x, title, flags=re.I) for x in CONTEXT_TERMS)
    unrelated = any(re.search(x, title, flags=re.I) for x in CROSS_DOMAIN_TERMS)
    if unrelated and not possible:
        return "OUTSIDE_AWARD_TOPIC", []
    if possible:
        return "BROAD_CONTEXT_NEEDS_REVIEW", []
    return "NO_AWARD_TOPIC_SIGNAL", []


def orcid(author):
    text = str(author.get("ORCID") or "").strip()
    m = re.fullmatch(r"(?:https?://orcid[.]org/)?([0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9X]{4})", text, flags=re.I)
    return m.group(1).upper() if m else ""


def institutions(author):
    """Distinctive exact public affiliations and ROR IDs; never names in output."""
    out = set()
    for a in author.get("affiliation", []) or []:
        if not isinstance(a, dict):
            continue
        for val in (a.get("name"), a.get("id")):
            if isinstance(val, str):
                norm = norm_title(val)
                if len(norm) >= 14:
                    out.add(norm)
        for item in a.get("identifiers", []) or []:
            if isinstance(item, dict):
                candidate = str(item.get("id") or "")
                if "ror.org/" in candidate:
                    out.add(candidate.casefold().strip("/"))
    return out


def matches_author(a, b):
    return bool(author_identity_key(a) and author_identity_key(a) == author_identity_key(b))


def author_evidence(seed, work):
    """Only an explicit ORCID match is strong; affiliations/coauthors support."""
    seed_authors = seed.get("author", []) or []
    work_authors = work.get("author", []) or []
    named_pairs = [(a, b) for a in seed_authors for b in work_authors if matches_author(a, b)]
    if not named_pairs:
        return "AUTHOR_NAME_NOT_CORROBORATED"
    statuses = []
    for a, b in named_pairs:
        a_id, b_id = orcid(a), orcid(b)
        if a_id and b_id:
            statuses.append("SAME_REPORTED_ORCID" if a_id == b_id else "ORCID_CONFLICT")
            continue
        coa = {author_identity_key(x) for x in seed_authors if x is not a}
        cob = {author_identity_key(x) for x in work_authors if x is not b}
        common_coauthors = len((coa & cob) - {(), author_identity_key(a)})
        if institutions(a) & institutions(b):
            statuses.append("SHARED_PUBLIC_AFFILIATION")
        elif common_coauthors >= 2:
            statuses.append("TWO_SHARED_COAUTHORS")
        else:
            statuses.append("AUTHOR_IDENTITY_UNRESOLVED")
    for priority in ("SAME_REPORTED_ORCID", "SHARED_PUBLIC_AFFILIATION",
                     "TWO_SHARED_COAUTHORS", "AUTHOR_IDENTITY_UNRESOLVED",
                     "ORCID_CONFLICT"):
        if priority in statuses:
            # If multiple matching-name persons share a byline, even an
            # ORCID conflict on another pair is retained for manual review.
            return priority
    return "AUTHOR_IDENTITY_UNRESOLVED"


def awards_recorded(work):
    found = set()
    for funder in work.get("funder", []) or []:
        if not isinstance(funder, dict):
            continue
        for award in funder.get("award", []) if isinstance(funder.get("award"), list) else [funder.get("award")]:
            for m in NOAA_AWARD.finditer(str(award or "")):
                found.add(m.group(1).upper())
    return found


def funding_evidence(work, award):
    codes = awards_recorded(work)
    if award.upper() in codes:
        return "EXACT_TARGET_AWARD_REGISTERED", sorted(codes)
    if codes:
        return "DIFFERENT_NOAA_AWARD_REGISTERED", sorted(codes)
    if work.get("funder"):
        return "FUNDER_PRESENT_NO_TARGET_AWARD_PROOF", []
    return "NO_STRUCTURED_AWARD_EVIDENCE", []


def choose_tier(topic, author_status, funding, identity):
    """Never reject or stage a candidate from author-only metadata."""
    if identity not in ("NO_PUBLIC_IDENTITY_MATCH", "PUBLISHED_VERSION_LEAD"):
        return "PUBLIC_IDENTITY_OR_VERSION_REVIEW"
    if funding == "EXACT_TARGET_AWARD_REGISTERED":
        return "TARGET_AWARD_PROJECT_VALIDATION"  # Never self-approve.
    if topic == "DIRECT_ATMOSPHERIC_AIR_QUALITY_TOPIC":
        return "TARGETED_FUNDING_INVESTIGATION"
    if topic == "BROAD_CONTEXT_NEEDS_REVIEW":
        return "LOWER_PRIORITY_TOPIC_INVESTIGATION"
    if author_status == "SAME_REPORTED_ORCID":
        # Topic mismatch must not create a permanent false negative.
        return "LOWER_PRIORITY_ORCID_FOLLOWUP"
    return "DEFER_OFF_TOPIC_RETAIN_LEAD"


def evaluate_leads(pilot, cache, index, watchlist, ir_index, *, get_metadata):
    if pilot.get("schema") != PILOT_SCHEMA or pilot.get("award") != AWARD:
        raise ValueError("Unexpected original award or DOI-lead schema")
    leads = pilot.get("independent_doi_leads")
    if not isinstance(leads, list) or len(leads) != 32:
        raise ValueError("Pilot reproduction requires 32 previously observed DOI leads")
    if len({norm_doi(x.get("doi")) for x in leads}) != 32:
        raise ValueError("Duplicate or invalid original DOI lead")
    seed_map = {x["doi"]: x for x in publication_dois(cache, ir_index, AWARD)}
    needed = sorted({norm_doi(x.get("seed_reach_doi")) for x in leads})
    source_meta = {}
    for doi in needed:
        seed = seed_map.get(doi)
        if seed is None:
            raise ValueError("Lead has no exact-award public REACH seed: " + doi)
        work = get_metadata(doi)
        if not accepted_public_journal_source(seed, work):
            raise ValueError("Lead source not verified official public REACH journal article: " + doi)
        source_meta[doi] = work
    results = []
    for item in sorted(leads, key=lambda x: x["doi"]):
        doi = norm_doi(item.get("doi"))
        seed_doi = norm_doi(item.get("seed_reach_doi"))
        work = get_metadata(doi)
        if not isinstance(work, dict) or norm_doi(work.get("DOI")) != doi:
            results.append({"doi": doi, "title": item.get("title", ""),
                            "seed_reach_doi": seed_doi,
                            "metadata": "UNAVAILABLE_OR_DOI_CONFLICT",
                            "tier": "METADATA_RETRY_REQUIRED",
                            "hub_eligible": False})
            continue
        title = (work.get("title") or [""])[0]
        if not title or norm_title(title) != norm_title(item.get("title")):
            results.append({"doi": doi, "title": item.get("title", ""),
                            "seed_reach_doi": seed_doi,
                            "metadata": "TITLE_MISMATCH_REVIEW",
                            "tier": "METADATA_RETRY_REQUIRED",
                            "hub_eligible": False})
            continue
        topic, terms = topical_evidence(title)
        author_status = author_evidence(source_meta[seed_doi], work)
        funding, awards = funding_evidence(work, AWARD)
        identity = verified_disposition(index, watchlist, ir_index,
                                        doi=doi, title=title, url="https://doi.org/" + doi)
        tier = choose_tier(topic, author_status, funding, identity["disposition"])
        results.append({"doi": doi, "title": title,
                        "seed_reach_doi": seed_doi,
                        "metadata": "CROSSREF_EXACT_DOI_TITLE_VERIFIED",
                        "topic": topic, "topic_evidence_terms": terms,
                        "author_identity_evidence": author_status,
                        "award_evidence": funding, "recorded_noaa_awards": awards,
                        "public_identity": identity["disposition"],
                        "tier": tier,
                        "funding_project_verified": False,
                        "hub_eligible": False})
    return {
        "schema": OUTPUT_SCHEMA,
        "award": AWARD,
        "baseline_unverified_doi_leads": 32,
        "public_reach_source_dois_checked": len(source_meta),
        "rows_reviewed": len(results),
        "tiers": dict(Counter(row["tier"] for row in results)),
        "topic_evidence": dict(Counter(row.get("topic", "METADATA_UNVERIFIED") for row in results)),
        "author_identity_evidence": dict(Counter(row.get("author_identity_evidence", "METADATA_UNVERIFIED") for row in results)),
        "award_evidence": dict(Counter(row.get("award_evidence", "METADATA_UNVERIFIED") for row in results)),
        "no_promotion_to_discovery_hub": True,
        "spark_personnel_accessed": False,
        "author_names_saved": False,
        "absent_award_is_not_negative_proof": True,
        "classification_is_not_eligibility": True,
        "results": results,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pilot-json", required=True, help="Temporary DOI-only prior pilot artifact")
    p.add_argument("--out-json", required=True, help="Temporary DOI-only results (not Git-tracked)")
    args = p.parse_args()
    index, ir_index = verified_snapshot(ROOT)
    cache_file = ROOT / CACHE_PATH
    if sha_file(cache_file) != index["sources"]["reach_cache_sha256"]:
        raise ValueError("Stale SHA-verified public REACH cache")
    cache = read_json(cache_file)
    watchlist = read_json(ROOT / WATCHLIST_PATH)
    pilot = read_json(__import__("pathlib").Path(args.pilot_json))
    lookup_cache = {}
    def lookup(doi):
        if doi not in lookup_cache:
            url = "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="/")
            lookup_cache[doi] = get_crossref_json(url)
        return lookup_cache[doi]
    output = evaluate_leads(pilot, cache, index, watchlist, ir_index, get_metadata=lookup)
    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(json.dumps({k: v for k, v in output.items() if k != "results"}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
