#!/usr/bin/env python3
"""One read-only public identity/disposition decision for all Scout entry paths.

REACH, Scout queue, and preprint version identities are distinct concepts.
No private Hub history, author names, SPARK personnel data, or review actions
are inferred or written to GitHub by this module.
"""
import argparse
import json
from collections import Counter
from pathlib import Path

from decision_pipeline import (ROOT, check_index_fresh, lookup, norm_doi,
                               read_json, sha_file)

WATCHLIST_SCHEMA = "reach-scout-preprint-watchlist-v1"
IDENTITY_SCHEMA = "reach-scout-identity-index-v1"


def version_relationships(watchlist, doi):
    """Explicit DOI relations only; no inferred title/author version merges."""
    if watchlist.get("schema") != WATCHLIST_SCHEMA:
        raise ValueError("Preprint watchlist schema not verified")
    parents, siblings = [], []
    seen = set()
    for entry in watchlist.get("entries", []):
        pre = norm_doi(entry.get("preprint_doi"))
        if not pre or pre in seen:
            raise ValueError("Invalid or duplicate preprint DOI in verified watchlist")
        seen.add(pre)
        published = {norm_doi(x) for x in entry.get("verified_published_dois", [])}
        published.discard("")
        if pre in published:
            raise ValueError("Preprint cannot be its own published version")
        if doi == pre:
            parents.append(pre)
            siblings.extend(sorted(published))
        elif doi in published:
            parents.append(pre)
    # Multiple earlier preprint iterations may legitimately point to one final DOI.
    # Keep every known predecessor; do not collapse or discard their history.
    return {"is_original_preprint": doi in seen,
            "preprint_dois": sorted(set(parents)),
            "official_published_doi_leads": sorted(set(siblings))}


def decide(index, watchlist, *, doi="", title="", url=""):
    """Public-source routing only: never close related-output expansion lanes."""
    if index.get("schema") != IDENTITY_SCHEMA:
        raise ValueError("Unverified public identity index schema")
    identity = lookup(index, doi=doi, title=title, url=url)
    normalized = norm_doi(doi) or norm_doi(url)
    family = version_relationships(watchlist, normalized)
    status = identity["status"]
    if status == "CONFIRMED_PUBLIC_REACH_IDENTITY":
        disposition, action = "EXISTING_IN_REACH", "SKIP_ORIGINAL_RETAIN_EXPANSION"
    elif family["is_original_preprint"]:
        # An original preprint is not eligible even if it was accidentally
        # submitted to a public Scout queue; keep all version leads.
        disposition, action = "PREPRINT_WATCHLIST_HOLD", "MONTHLY_PREPRINT_MONITOR_ONLY"
    elif status == "IN_PUBLIC_SCOUT_QUEUE":
        disposition, action = "EXISTING_PUBLIC_SCOUT_CANDIDATE", "DO_NOT_REPROPOSE"
    elif status in ("POSSIBLE_PUBLIC_REACH_MATCH", "POSSIBLE_SCOUT_QUEUE_MATCH"):
        disposition, action = "IDENTITY_REVIEW_REQUIRED", "BOUNDED_IDENTITY_AND_VERSION_REVIEW"
    elif family["preprint_dois"]:
        disposition, action = "PUBLISHED_VERSION_LEAD", "VERIFY_FINAL_DOI_INDEPENDENTLY"
    else:
        disposition, action = "NO_PUBLIC_IDENTITY_MATCH", "PROCEED_TO_ELIGIBILITY_AND_FUNDING_RESEARCH"
    # Even a published-version lead has to establish its own award/project
    # evidence; a preprint family relation alone is never proof of funding.
    return {
        "schema": "reach-scout-public-identity-disposition-v1",
        "doi": normalized,
        "disposition": disposition,
        "next_action": action,
        "identity": identity,
        "explicit_version_family": family,
        "expansion_seed_preserved": True,
        "auto_staging": False,
        "private_review": "NOT_VERIFIED",
        "source_fingerprint": index["source_fingerprint"],
    }



def verified_disposition(index, watchlist, ir_index, *, doi="", title="", url=""):
    """One read-only screen for monthly, historical and independent research.

    The direct shared gate and the separately trusted NOAA IR DOI->URL mapping
    are reconciled. No reviewer state or funding attribution is inferred.
    """
    from ir_reach_identity import identity_check
    result = decide(index, watchlist, doi=doi, title=title, url=url)
    check = identity_check(index, ir_index, doi, title, url)
    ir = check["noaa_ir_reach_check"]
    result["official_noaa_ir"] = {
        "status": ir["status"],
        "match_uid": ir["match_uid"],
        "official_url": ir["official_url"],
    }
    if result["disposition"] == "EXISTING_IN_REACH":
        return result
    if result["explicit_version_family"]["is_original_preprint"]:
        return result
    if ir["status"] == "VERIFIED_OFFICIAL_IR_DOI_TO_EXISTING_REACH_URL":
        if check["status"] != "CONFIRMED_PUBLIC_REACH_IDENTITY":
            raise ValueError("Official IR verification contradicts public identity")
        result["disposition"] = "EXISTING_IN_REACH"
        result["next_action"] = "SKIP_ORIGINAL_RETAIN_EXPANSION"
        result["identity_confirmation_basis"] = "VERIFIED_IR_DOI_URL_AND_TITLE"
    elif ir["status"] in {
        "IR_INDEX_UNAVAILABLE_HOLD", "AMBIGUOUS_IR_DOI_HOLD",
        "MULTIPLE_REACH_RECORDS_HOLD", "REACH_DOI_CONFLICT_VERSION_REVIEW",
        "IR_URL_MATCH_REQUIRES_REVIEW"
    } and result["disposition"] in {"NO_PUBLIC_IDENTITY_MATCH", "PUBLISHED_VERSION_LEAD"}:
        # May still research other evidence, but no no-match assertion may
        # be promoted into a new-output recommendation until identity resolved.
        result["disposition"] = "IDENTITY_REVIEW_REQUIRED"
        result["next_action"] = "VERIFY_OFFICIAL_IR_IDENTITY_FIRST"
    return result


def public_reach_author_seeds(cache, award):
    """Fail closed: only public REACH *publication* records may seed author search.

    The current comparison-cache v1 contains no author fields, so this
    intentionally returns no author seeds until a separately verified REACH
    publication metadata enrichment is available. SPARK is never an input.
    The returned names are transient research leads, never identity proof.
    """
    if cache.get("schema") != "reach-scout-comparison-cache-v1" or cache.get("source_repo") != "PART-WPO/reach-dashboard":
        raise ValueError("Author seeds require verified public REACH source")
    award = str(award or "").upper().strip()
    if not award:
        return []
    candidates = set()
    for rec in cache.get("records", []):
        # Explicit publication type and source evidence are mandatory.
        if str(rec.get("output_type", "")).casefold() != "publication":
            continue
        import re
        award_tokens = {x.upper() for x in re.findall(r"NA[0-9A-Z-]+", rec.get("awards", ""), flags=re.I)}
        if award not in award_tokens:
            continue
        if rec.get("authors_source") != "REACH_PUBLIC_VERIFIED":
            continue
        for author in rec.get("authors", []):
            if isinstance(author, str) and author.strip():
                candidates.add(author.strip())
    return sorted(candidates)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--doi", default="")
    p.add_argument("--title", default="")
    p.add_argument("--url", default="")
    p.add_argument("--benchmark", action="store_true",
                   help="Read-only 100-case coverage replay, NOT accuracy scoring")
    args = p.parse_args()
    root = args.root.resolve()
    index = read_json(root / "scout-operations/identity-cache/public-identity-index.json")
    check_index_fresh(root, index)
    watch_path = root / "scout-operations/preprint-watchlist.json"
    watchlist = read_json(watch_path)
    if args.benchmark:
        sample = read_json(root / "scout-operations/scout-v2-benchmark-100.json")
        if sample.get("sample_size") != 100 or len(sample.get("cases", [])) != 100:
            raise ValueError("Frozen benchmark must contain 100 cases")
        outcomes = Counter(decide(index, watchlist, doi=x["doi"])["disposition"]
                           for x in sample["cases"])
        print(json.dumps({
            "cases_replayed": 100, "dispositions": dict(sorted(outcomes.items())),
            "watchlist_sha256": sha_file(watch_path),
            "identity_fingerprint": index["source_fingerprint"],
            "independent_gold_labels": "NOT_COLLECTED",
            "accuracy_or_recall": "NOT_ESTIMABLE",
            "private_review": "NOT_VERIFIED",
            "auto_staging": False
        }, indent=2))
    else:
        print(json.dumps(decide(index, watchlist, doi=args.doi,
                                title=args.title, url=args.url), indent=2))


if __name__ == "__main__":
    main()
