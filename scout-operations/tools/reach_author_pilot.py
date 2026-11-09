#!/usr/bin/env python3
"""Optional, bounded public REACH publication -> Crossref author research pilot.

No SPARK input. Authors are transient in memory, never in JSON reports/logs.
DOI leads are *not* award evidence and never reach the Discovery Hub from here.
Run only when requested; the hourly Scout scheduler does not invoke this.
"""
import argparse
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from decision_pipeline import ROOT, norm_doi, norm_title, read_json, sha_file
from identity_disposition import verified_disposition
from ir_reach_identity import verified_snapshot

CACHE_PATH = "scout-operations/reach-comparison-cache/comparison-index.json"
WATCHLIST_PATH = "scout-operations/preprint-watchlist.json"


def award_matches(record, award):
    # Do not truncate FY25+ award task suffixes or use related award numbers.
    tokens = [a.strip().upper() for a in re.split(r"[,;]", str(record.get("awards", "")))]
    return award.strip().upper() in tokens and bool(award.strip())


def publication_dois(cache, ir_index, award):
    """Return public REACH-linked DOI seeds; no SPARK/PI/personnel columns."""
    if cache.get("schema") != "reach-scout-comparison-cache-v1" or cache.get("source_repo") != "PART-WPO/reach-dashboard":
        raise ValueError("Unverified public REACH publication cache")
    reverse = {}
    if ir_index:
        for raw_doi, urls in ir_index.get("dois", {}).items():
            for url in urls:
                reverse.setdefault(str(url).lower().rstrip("/"), set()).add(norm_doi(raw_doi))
    seeds = []
    for rec in cache.get("records", []):
        if not award_matches(rec, award):
            continue
        # Crossref must verify journal-article status/title in a second step;
        # a REACH record alone does not prove this is a publication.
        dois = {norm_doi(x) for x in rec.get("dois", [])}
        for url in rec.get("links", []):
            dois.add(norm_doi(url))
            dois.update(reverse.get(str(url).lower().rstrip("/"), set()))
        for doi in sorted(d for d in dois if d):
            seeds.append({"doi": doi, "reach_uid": rec["reach_uid"],
                          "reach_title": rec.get("title", "")})
    return seeds


def get_crossref_json(url):
    request = urllib.request.Request(
        url, headers={"Accept": "application/json",
                      "User-Agent": "REACH-Scout-Public-Author-Pilot/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=22) as response:
            return json.load(response).get("message") or {}
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError):
        return None


def author_name(x):
    return " ".join(filter(None, [str(x.get("given") or "").strip(),
                                   str(x.get("family") or "").strip()])).strip()


def accepted_public_journal_source(seed, data):
    """Crossref must corroborate both the REACH title and final publication."""
    if not isinstance(data, dict):
        return False
    if norm_doi(data.get("DOI")) != seed["doi"]:
        return False
    if data.get("type") != "journal-article":
        return False
    if not any(data.get(k) for k in ("published-print", "published-online", "published")):
        return False
    titles = data.get("title") or []
    return bool(titles and norm_title(titles[0]) and
                norm_title(titles[0]) == norm_title(seed["reach_title"]))


def research_award(index, watchlist, ir_index, cache, award, *, doi_lookup,
                   author_search, max_publications=5, max_authors=4,
                   max_results_per_author=5):
    """Bounded author expansion with DOI-only outputs; never persist names."""
    if not re.fullmatch(r"NA[0-9]{2}[A-Z0-9]+(?:-[A-Z0-9]+)*", award.upper().strip()):
        raise ValueError("Exact NOAA award number required")
    seed_items = publication_dois(cache, ir_index, award)
    authors = {}
    verified_publications = 0
    for seed in seed_items[:max_publications]:
        data = doi_lookup(seed["doi"])
        if not accepted_public_journal_source(seed, data):
            continue
        verified_publications += 1
        for raw in data.get("author", []):
            name = author_name(raw)
            # A full given+family is required to avoid surname-only searches.
            if not raw.get("given") or not raw.get("family") or not name:
                continue
            authors.setdefault(name.casefold(), (name, seed))
            if len(authors) >= max_authors:
                break
        if len(authors) >= max_authors:
            break
    leads = {}
    for _key, (name, seed) in authors.items():
        for work in (author_search(name, max_results_per_author) or [])[:max_results_per_author]:
            doi = norm_doi(work.get("DOI"))
            title = (work.get("title") or [""])[0]
            # Not even a prospective candidate without DOI/title/author-match.
            if not doi or not title or work.get("type") != "journal-article":
                continue
            if name.casefold() not in {
                author_name(a).casefold() for a in work.get("author", [])
            }:
                continue
            disposition = verified_disposition(index, watchlist, ir_index,
                                               doi=doi, title=title,
                                               url="https://doi.org/" + doi)
            if disposition["disposition"] not in {"NO_PUBLIC_IDENTITY_MATCH",
                                                   "PUBLISHED_VERSION_LEAD"}:
                continue
            # No author fields, SPARK metadata, or personnel identifiers in
            # returned/persisted evidence. Shared authorship is a lead only.
            leads.setdefault(doi, {
                "doi": doi, "title": title,
                "seed_reach_uid": seed["reach_uid"],
                "seed_reach_doi": seed["doi"],
                "discovery_basis": "PUBLIC_REACH_ARTICLE_CROSSREF_AUTHOR",
                "project_funding_verified": False,
                "relevance_verified": False,
                "discovery_hub_eligible": False,
                "action": "INDEPENDENT_AWARD_PROJECT_EVIDENCE_REQUIRED"
            })
    return {
        "schema": "reach-scout-public-reach-author-pilot-v1",
        "source": "SHA_VERIFIED_PUBLIC_REACH_AND_CROSSREF",
        "award": award.upper().strip(),
        "potential_seed_dois": len(seed_items),
        "verified_publications": verified_publications,
        "transient_authors_used": len(authors),
        "independent_doi_leads": sorted(leads.values(), key=lambda x: x["doi"]),
        "pii_publication": "NO_AUTHOR_NAMES_PERSISTED_OR_PRINTED",
        "spark_author_data_accessed": False,
        "human_review_or_reach_modified": False
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--award", required=True, help="Exact primary WPO award, not project name")
    p.add_argument("--output", type=Path, help="Optional DOI-only research-lead JSON")
    args = p.parse_args()
    public, ir = verified_snapshot(ROOT)
    cache = read_json(ROOT / CACHE_PATH)
    if sha_file(ROOT / CACHE_PATH) != public["sources"]["reach_cache_sha256"]:
        raise ValueError("Stale verified public REACH cache")
    watch = read_json(ROOT / WATCHLIST_PATH)

    def by_doi(doi):
        return get_crossref_json("https://api.crossref.org/works/" +
                                 urllib.parse.quote(doi, safe="/"))
    def by_author(name, count):
        qs = urllib.parse.urlencode({"query.author": name, "rows": count,
                                     "filter": "type:journal-article"})
        return (get_crossref_json("https://api.crossref.org/works?" + qs)
                or {}).get("items", [])

    report = research_award(public, watch, ir, cache, args.award,
                            doi_lookup=by_doi, author_search=by_author)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf8")
    # Aggregate counts only in logs; author names must never be printed.
    print(json.dumps({k: v for k, v in report.items()
                      if k != "independent_doi_leads"} | {
                      "independent_doi_lead_count": len(report["independent_doi_leads"])
                      }, indent=2))


if __name__ == "__main__":
    main()
