#!/usr/bin/env python3
"""Use ONE SHA-verified public identity/eligibility engine across Scout sources.

Read-only cohort-wide preflight. Recorded human/reviewer dispositions are NOT
recomputed or modified. Source funding identifiers, DOI dates, and author
overlap are search hints, not verified same-project funding proof.
"""
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from decision_pipeline import build_index, check_index_fresh, checked_csv, evaluate, norm_doi, norm_title
from reviewer_feedback_guard import known_feedback_by_doi, reviewer_hold_for_proposal

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT/"scout-operations/unified-source-preflight.json"
MANIFESTS = {
    "monthly_api":"api-discoveries/manifest.json",
    "historical_datacite":"api-discoveries/historical/manifest.json",
}
CROSSREF_ROUTING="scout-operations/historical-crossref-screening/actionable-routing.json"

def load(root, path):
    p=root/path
    data=p.read_bytes()
    return json.loads(data),hashlib.sha256(data).hexdigest()

def source_rows(root, manifest_rel):
    manifest, manifest_sha=load(root,manifest_rel)
    rows=[]
    for batch in manifest["batches"]:
        rows.extend((batch["id"],r) for r in checked_csv(root,batch["path"],
            batch["sha256"],batch["record_count"]))
    if len(rows)!=manifest["candidate_rows"]:
        raise ValueError("API source manifest row count mismatch: "+manifest_rel)
    return rows,manifest_sha

def link_map(records):
    links={}
    for e in records:
        d=norm_doi(e.get("identity") or e.get("doi"))
        if d and d in links:
            raise ValueError("Duplicate original status in same cohort: "+d)
        if d: links[d]=e
    return links

def urls_from(entry):
    urls=[]
    for item in (entry.get("checked_sources") or []):
        if isinstance(item,str): candidate=item
        elif isinstance(item,dict): candidate=item.get("url","")
        else: candidate=""
        if candidate.startswith("https://") and candidate not in urls: urls.append(candidate)
    return urls

def derive_record(lane, raw, recorded, preprint_dois, *,source_batch=""):
    doi=norm_doi(raw.get("DOI") or raw.get("identity") or raw.get("doi"))
    if not doi:
        raise ValueError("Missing valid source DOI for "+lane)
    # A created/deposited/date value does not prove official publication.
    preprint=doi in preprint_dois
    publication="PREPRINT" if preprint else "NOT_CHECKED"
    if recorded.get("publication_status") in ("PUBLISHED","PREPRINT"):
        publication=recorded["publication_status"]
    award=None
    attribution="NOT_CHECKED"
    structured=None
    if recorded.get("primary_award_match") is True:
        award=True
    if recorded.get("project_attribution") in {"VERIFIED","CONTRADICTED","UNRESOLVED"}:
        attribution=recorded["project_attribution"]
    if recorded.get("structured_funding_evidence_verified") is True:
        structured=True
    checked=urls_from(recorded)
    metadata=recorded.get("required_metadata_verified") is True
    secondary=recorded.get("secondary_identity_checked") is True
    rounds=recorded.get("research_rounds",0)
    rounds=rounds if rounds in (0,1,2) else 0
    title=raw.get("Title") or raw.get("title") or (recorded.get("title") or "")
    original_status=recorded.get("status","NOT_VERIFIED")
    output_url=raw.get("Output URL") or raw.get("original_source_url") or ""
    # The project verification and private-review status are never inferred
    # from historical forwarded/staged statuses.
    return {
        "doi":doi,"title":title,"url":output_url,"cohort":(
            "independent" if lane in ("monthly_related_outputs","independent") else lane),
        "publication_status":publication,
        "primary_award_match":award,"project_attribution":attribution,
        "structured_funding_evidence_verified":structured,
        "checked_sources":checked,"research_rounds":rounds,
        "secondary_identity_checked":secondary,
        "required_metadata_verified":metadata,
        "private_review_status":"NOT_VERIFIED",
        "_lane":lane,"_recorded_status":original_status,
        "_source_batch":source_batch,
        "_source_awards_unverified":raw.get("NOAA Award Number(s)") or recorded.get("award_numbers") or [],
        "_original_source_identity":str(raw.get("identity") or raw.get("DOI") or raw.get("doi") or ""),
    }

def authoritative_effective_decision(engine_result, bulk, bulk_uid, doi):
    """Never let a permissive generic DOI hit override version-safe Crossref routing."""
    common=engine_result["decision"]
    if bulk is None:
        return common
    if bulk=="CONFIRMED_IN_REACH":
        if not bulk_uid:
            raise ValueError("Missing verified REACH UID for confirmed DOI: "+doi)
        return "EXISTING_IN_REACH_VERIFIED_BULK"
    if bulk=="LIKELY_IN_REACH":
        return "IDENTITY_REVIEW_REQUIRED_FROM_BULK"
    if bulk=="SCREENING_INCOMPLETE":
        return "SCREENING_INCOMPLETE"
    if bulk=="NOT_FOUND_IN_REACH_INDEX":
        if common=="EXISTING_IN_REACH":
            raise ValueError("Public REACH identity disagreement with negative Crossref routing: "+doi)
        return common
    raise ValueError("Unknown Crossref bulk identity route for "+doi)


def preflight(root=ROOT):
    index=build_index(root)
    check_index_fresh(root,index)
    watch,watch_sha=load(root,"scout-operations/preprint-watchlist.json")
    reviewer_feedback,feedback_sha=load(root,"scout-operations/research-feedback.json")
    feedback=known_feedback_by_doi(root)
    preprints={norm_doi(e.get("preprint_doi")) for e in watch["entries"]}
    monthly_triage, mt_sha=load(root,"scout-operations/monthly-triage.json")
    historical_triage, ht_sha=load(root,"scout-operations/historical-triage.json")
    research, research_sha=load(root,"scout-operations/research-decision-cases.json")
    related,related_sha=load(root,"scout-operations/monthly-expansion-leads.json")
    independent, independent_sha=load(root,"scout-operations/independent-discovery-leads.json")
    routing,routing_sha=load(root,CROSSREF_ROUTING)
    cross_source,cross_sha=load(root,"api-discoveries/historical-crossref/manifest.json")
    if routing["source_manifest_sha256"]!=cross_sha:
        raise ValueError("Crossref bulk routing snapshot no longer matches source")
    if routing["reach_cache_sha256"]!=index["sources"]["reach_cache_sha256"]:
        raise ValueError("Crossref bulk identity uses stale REACH comparison cache")
    recorded_monthly=link_map(monthly_triage["entries"])
    recorded_historical=link_map(historical_triage["entries"])
    recorded_crossref=link_map(research["cases"])
    records=[]
    sha_sources={"preprint_watchlist":watch_sha,"reviewer_feedback":feedback_sha,"monthly_triage":mt_sha,
        "historical_datacite_triage":ht_sha,"crossref_research_cases":research_sha,
        "monthly_related_leads":related_sha,"independent_leads":independent_sha,
        "crossref_routing":routing_sha,"historical_crossref_manifest":cross_sha}
    for lane,manifest_rel in MANIFESTS.items():
        pairs,source_sha=source_rows(root,manifest_rel)
        sha_sources[lane+"_manifest"]=source_sha
        originals=recorded_monthly if lane=="monthly_api" else recorded_historical
        seen=set()
        for batch_id,raw in pairs:
            d=norm_doi(raw.get("DOI"))
            if d in seen:raise ValueError("Duplicate source DOI in "+lane+": "+d)
            seen.add(d)
            if d not in originals:raise ValueError("Source DOI missing historical decision ledger: "+d)
            records.append(derive_record(lane,raw,originals[d],preprints,source_batch=batch_id))
        if set(originals)!=seen:
            raise ValueError("Original cohort ledger and immutable API source disagree: "+lane)
    for e in routing["entries"]:
        d=norm_doi(e["doi"])
        original=recorded_crossref.get(d,{})
        base=derive_record("historical_crossref",{"DOI":d,"Title":e["title"]},original,preprints,
                           source_batch="verified_historical_crossref_routing")
        base["_crossref_bulk_outcome"]=e["outcome"]
        base["_bulk_verified_reach_uid"]=(e.get("bulk_identity_gate") or {}).get("verified_reach_uid")
        records.append(base)
    for lane,items in (("monthly_related_outputs",related["entries"]),("independent",independent["entries"])):
        for e in items:
            base=derive_record(lane,e,e,preprints,source_batch="source_ledger")
            if lane=="monthly_related_outputs":
                base["url"]=e.get("original_source_url") or ""
            records.append(base)

    counts=Counter()
    rows=[]
    by_doi=defaultdict(set)
    for case in records:
        lane=case.pop("_lane")
        recorded_status=case.pop("_recorded_status")
        source_batch=case.pop("_source_batch")
        raw_awards=case.pop("_source_awards_unverified")
        raw_identity=case.pop("_original_source_identity")
        bulk=case.pop("_crossref_bulk_outcome",None)
        bulk_uid=case.pop("_bulk_verified_reach_uid",None)
        evaluated=evaluate(case,index)
        # Verified canonical NOAA IR -> public REACH URL is an independent
        # source-backed original identity gate; do not rely on the generic
        # lookup engine to infer that URL from DOI alone.
        decision=authoritative_effective_decision(
            evaluated,bulk,bulk_uid,case["doi"])
        counts[(lane,decision)]+=1
        by_doi[case["doi"]].add(lane)
        existing_review=reviewer_hold_for_proposal(case["doi"],feedback)
        rows.append({"doi":case["doi"],"discovery_lane":lane,
            "source_batch":source_batch,"raw_source_identity":raw_identity,
            "recorded_status_unchanged":recorded_status,
            "shared_gate_decision":evaluated["decision"],
            "effective_identity_or_preflight":decision,
            "trusted_bulk_public_reach_uid":bulk_uid,
            "source_awards_are_unverified_hints":raw_awards,
            "publication_status":case["publication_status"],
            "identity_match_status":evaluated["identity_check"]["status"],
            "private_review_status":("SIGNED_PRIVATE_REVIEW_EVENT_PRESENT"
                                     if existing_review else "NOT_VERIFIED"),
            "authenticated_prior_review_event_id":existing_review["review_event_id"] if existing_review else None,
            "authenticated_prior_review_code":existing_review["last_private_review_code"] if existing_review else None,
            "review_state_modified":False,"automatically_staged":False,
            "original_disposition_changed":False,"seed_expansion_closed":False,
            "evidence_input_sha256":hashlib.sha256(json.dumps(case,sort_keys=True).encode()).hexdigest()})
    lane_counts={}
    for (lane,decision),total in sorted(counts.items()):
        lane_counts.setdefault(lane,{})[decision]=total
    return {"schema":"reach-scout-unified-source-preflight-v1",
        "identity_index_fingerprint":index["source_fingerprint"],
        "identity_index_source_sha256":index["sources"],
        "source_manifest_sha256":sha_sources,
        "original_and_related_cases_preflighted":len(rows),
        "lane_decision_counts":lane_counts,
        "cross_cohort_duplicate_doi_identities":sum(len(v)>1 for v in by_doi.values()),
        "crossref_bulk_confirms_after_version_guard":sum(
            r["effective_identity_or_preflight"]=="EXISTING_IN_REACH_VERIFIED_BULK"
            for r in rows if r["discovery_lane"]=="historical_crossref"),
        "authenticated_private_review_event_dois":len(feedback),
        "changes_to_human_dispositions":0,"new_public_review_proposals":0,"new_reach_additions":0,
        "note":"Single shared SHA-verified public identity and decision engine across source modes, with an independent trusted official NOAA IR REACH URL gate. Input-only source award and date hints never establish funding or official publication, and already published reviewer rows remain unchanged.",
        "cases":rows}

def main():
    report=preflight()
    output=json.dumps(report,ensure_ascii=False,indent=2)+"\n"
    if not DEST.exists() or DEST.read_text(encoding="utf-8")!=output:
        DEST.write_text(output,encoding="utf-8")
    print(json.dumps({"cases":report["original_and_related_cases_preflighted"],
                      "lanes":report["lane_decision_counts"],
                      "cross_cohort_overlap":report["cross_cohort_duplicate_doi_identities"]},indent=2))

if __name__=="__main__":main()
