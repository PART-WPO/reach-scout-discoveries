#!/usr/bin/env python3
"""Read-only replay of five verified Scout case paths using the actual engine.

No metadata / research / decision / reviewer CSV is changed, and no private
Discovery Hub, SPARK, Smartsheet or public REACH integration is invoked.
"""
import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"scout-operations/tools"))
sys.path.insert(0,str(ROOT/"scout-discoveries/tools"))
from build_research_outcome_registry import build as build_registry
from recover_queued_doi_metadata import run as run_recovery
from build_human_project_referrals import build as build_referrals,existing_verified_self_draft
from decision_pipeline import build_index,check_index_fresh,evaluate
from ir_reach_identity import verified_snapshot,identity_check
from prepare_batch import is_tracked_preprint,validate_canonical
from lookup_independent_dois import metadata as lookup_official

CASE_DOIS={
    "apar_human_question":"10.1109/radarconf2248738.2022.9764246",
    "gfdl_project_hold":"10.1007/s00382-022-06655-w",
    "ecmwf_metadata_recovery":"10.21957/befj-es73",
    "tornado_preprint":"10.1002/essoar.10504829.1",
    "gulf_stream_reach_duplicate":"10.1002/essoar.10507067.1",
}
OUTPUT=ROOT/"scout-operations/reports/workflow-replay/2026-11-06-five-real-cases.json"

def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def load(p):return json.loads((ROOT/p).read_text(encoding="utf-8"))
def require(test,message):
    if not test:raise ValueError("REPLAY VALIDATION FAILED: "+message)
def bundle(name,doi,expected,actual,source_paths,reason,other=None):
    return {"case":name,"doi":doi,"expected":expected,"observed":actual,
            "verified":expected==actual,"source_sha256":{p:sha(p) for p in source_paths},
            "why":reason,**(other or {})}

def build(*,live_metadata=False):
    index,official_ir=verified_snapshot(ROOT)
    check_index_fresh(ROOT,index)
    registry=build_registry(ROOT)
    recorded=load("scout-operations/research-outcome-registry.json")
    require(registry==recorded,"Source research registry is stale; do not replay old case labels")
    require(registry["evidence_files_scanned"]==len(registry["source_sha256"]),
            "Missing source-backed evidence files")
    for p,h in registry["source_sha256"].items():
        require(sha(p)==h,"Research file SHA changed without registry refresh: "+p)
    by_doi={}
    for event in registry["events"]:
        if event["doi"]:by_doi.setdefault(event["doi"],[]).append(event)

    stored_recovery=load("scout-operations/reports/queued-doi-metadata/latest.json")
    stored_referrals=load("scout-operations/human-project-referrals.json")
    require(stored_recovery["source_registry_sha256"]==
            sha("scout-operations/research-outcome-registry.json"),
            "Metadata recovery is stale relative to actual outcome registry")
    require(stored_referrals["source_outcome_event_count"]==registry["research_note_events"],
            "Referral evidence is stale relative to actual outcome registry")
    require(stored_referrals["source_outcome_sha256"]==
            hashlib.sha256(json.dumps(registry,sort_keys=True).encode()).hexdigest(),
            "Human project referrals no longer match SHA-verified registry")

    # This exercises the REAL recovery function. No API requests should be
    # issued for previously verified, cached successful source records.
    api_calls=[]
    def must_not_fetch(doi):
        api_calls.append(doi)
        raise ValueError("Cached successful DOI was unexpectedly re-requested: "+doi)
    shared_identity=lambda d,title:identity_check(index,official_ir,d,title,"https://doi.org/"+d)
    recovered=run_recovery(ROOT,lookup=must_not_fetch,identity=shared_identity,max_new=0)
    require(not api_calls,"Metadata recovery repeated verified DOI requests")
    require(recovered["doi_queue_size"]==len(recovered["records"]),
            "Metadata queue case count wrong")
    metadata={e["doi"]:e for e in recovered["records"]}

    apar=CASE_DOIS["apar_human_question"]
    gfdl=CASE_DOIS["gfdl_project_hold"]
    ecmwf=CASE_DOIS["ecmwf_metadata_recovery"]
    tornado=CASE_DOIS["tornado_preprint"]
    gulf=CASE_DOIS["gulf_stream_reach_duplicate"]
    ref_map={x["doi"]:x for x in stored_referrals["referrals"]}
    require(apar in by_doi and gfdl in by_doi and ecmwf in by_doi,
            "Missing original case notes in current registry")
    require(apar in ref_map and gfdl in ref_map,
            "Missing human project question record")
    require(apar in {x["doi"] for x in stored_referrals["referrals"]},
            "APAR referral missing from human handoff")
    source_ref=next(e for e in by_doi[apar]
                    if e["event_id"]==ref_map[apar]["source_event_id"])
    original=load(source_ref["source_path"])
    apar_meta=ref_map[apar]["official_metadata"]
    require(apar_meta["status"]=="ok","Official APAR publication metadata unverified")
    require(apar_meta["evidence"].startswith("https://api.crossref.org/works/"),
            "APAR lacks exact Crossref metadata provenance")
    public_apar=shared_identity(apar,apar_meta["title"])
    require(public_apar["status"]=="IN_PUBLIC_SCOUT_QUEUE",
            "APAR is no longer identifiable in verified Scout public feed")
    # The public feed workflow has independently promoted its earlier inbox
    # draft to a published batch; this is NOT a private Hub import.
    manifest=load("scout-discoveries/manifest.json")
    matched=[]
    for batch in manifest["batches"]:
        candidate=ROOT/batch["path"]
        with candidate.open(encoding="utf-8-sig",newline="") as f:
            rows_in_batch=list(csv.DictReader(f))
        if any(str(row.get("DOI","")).lower()==apar for row in rows_in_batch):
            require(sha(batch["path"])==batch["sha256"],
                    "Published APAR batch SHA does not match authoritative manifest")
            matched.append((batch,rows_in_batch))
    require(len(matched)==1,"APAR must exist exactly once in published public Scout feed")
    apar_batch,rows=matched[0]
    batch_path=ROOT/apar_batch["path"]
    require(len(rows)==1 and rows[0]["DOI"].lower()==apar,
            "Published APAR funding question is not exactly one unique DOI")
    require(any(m["source"]=="SCOUT_PUBLISHED" and
                m["location"]==apar_batch["path"]+":2" for m in public_apar["matches"]),
            "Current REACH/Scout index did not reconcile published APAR identity")
    validate_canonical(batch_path)
    own_draft=existing_verified_self_draft(
        ROOT,apar,source_ref,public_apar,stored_referrals)
    require(own_draft is None,
            "An already published APAR batch was incorrectly treated as an unpublished inbox draft")
    require(not rows[0]["NOAA Award Number(s)"],
            "APAR draft incorrectly claims an unverified WPO award")
    require("Scout classification: NEEDS INVESTIGATION" in rows[0]["Scout Discovery Rationale"],
            "APAR draft incorrectly claims eligible new-output approval")
    require("Reviewer question:" in rows[0]["Scout Discovery Rationale"],
            "APAR draft lacks a precise human funding question")
    require("NA18OAR4590431" in rows[0]["Scout Discovery Rationale"],
            "APAR draft lost primary award search context")
    require(ref_map[gfdl]["disposition"]=="HOLD_UNVERIFIED_PROJECT_CONTEXT" and
            ref_map[gfdl]["scout_inbox_status"]=="NOT_STAGED",
            "GFDL funding hold incorrectly becomes review proposal")

    # Re-run the REAL human-referral decision function in read-only mode.
    # Prior correct draft is recognized as its own existing reviewed work unit.
    def known_official(d):
        if d==apar:return apar_meta
        raise ValueError("Non-contextual DOI unexpectedly triggered publisher query: "+d)
    referral_preview=build_referrals(
        root=ROOT,metadata=known_official,public_identity=shared_identity,stage=False)
    rechecked={x["doi"]:x for x in referral_preview["referrals"]}
    require(rechecked[apar]["disposition"]=="HOLD_ALREADY_IN_PUBLIC_REACH_OR_SCOUT",
            "An already published APAR question would be proposed a second time")
    require(rechecked[gfdl]["disposition"]=="HOLD_UNVERIFIED_PROJECT_CONTEXT",
            "GFDL was incorrectly promoted from missing award context")
    require(not referral_preview["draft_paths"],"Read-only replay wrote unexpected reviewer draft")

    require(ecmwf in metadata and metadata[ecmwf]["metadata"]["status"]=="ok",
            "ECMWF exact DOI recovery missing")
    require(metadata[ecmwf]["metadata"]["provider"]=="datacite",
            "ECMWF recovered provider not DataCite")
    require(metadata[ecmwf]["public_identity"]["status"]=="NO_PUBLIC_IDENTITY_MATCH",
            "ECMWF public REACH result changed; manual identity check required")
    require(not metadata[ecmwf]["wpo_project_funding_verified"],
            "Recovered DOI metadata incorrectly establishes WPO funding")

    historical=load("scout-operations/research-decision-cases.json")["cases"]
    by_case={e["doi"]:e for e in historical}
    require(tornado in by_case and gulf in by_case,
            "Original historical cases missing from immutable decision inputs")
    pre=evaluate(by_case[tornado],index)
    dup=evaluate(by_case[gulf],index)
    require(pre["decision"]=="PREPRINT_HOLD" and is_tracked_preprint(tornado),
            "Original tornado DOI was not held on monthly preprint watchlist")
    require(dup["decision"]=="EXISTING_IN_REACH",
            "Existing Gulf Stream version was not recognized as REACH identity")
    require(pre["automatically_staged"] is False and dup["automatically_staged"] is False,
            "Old preprint or REACH duplicate staged a new candidate")

    live={}
    if live_metadata:
        # Fresh exact DOI requests use the existing DataCite->Crossref
        # resolver and check official DOI identity before accepting a result.
        for d in (apar,ecmwf):
            result=lookup_official(d)
            require(result["status"]=="ok","Live exact DOI API unavailable: "+d)
            require(result["evidence"].startswith("https://api."),
                    "Live DOI metadata lacks official API provenance: "+d)
            require(result["title"],"Live DOI metadata omitted title: "+d)
            live[d]={"provider":result["provider"],"status":result["status"],
                     "evidence":result["evidence"],"title":result["title"],
                     "pub_date":result.get("pub_date"),
                     "funding_proven_from_metadata":False}
    reports=[
        bundle("published_with_uncertain_project",apar,"EXISTING_SINGLE_PUBLIC_NEEDS_INVESTIGATION_BATCH",
               "EXISTING_SINGLE_PUBLIC_NEEDS_INVESTIGATION_BATCH" if
                  rechecked[apar]["disposition"]=="HOLD_ALREADY_IN_PUBLIC_REACH_OR_SCOUT"
                  else "RISK_OF_DUPLICATE_REFERRAL",
               ["scout-operations/human-project-referrals.json",
                "scout-discoveries/manifest.json",apar_batch["path"],source_ref["source_path"]],
               "One SHA-verified published Scout review record; new attempts are held as an existing public queue item. A prior inbox report is stale after promotion, and the funding award field remains blank.",
               {"public_identity":public_apar["status"],"private_hub":"NOT_VERIFIED",
                "recorded_referral_lifecycle":"STALE_INBOX_STATUS_AFTER_PUBLIC_FEED_PROMOTION",
                "published_feed_batch":apar_batch["path"]}),
        bundle("publication_with_missing_award_bridge",gfdl,"HOLD_UNVERIFIED_PROJECT_CONTEXT",
               rechecked[gfdl]["disposition"],
               ["scout-operations/human-project-referrals.json",
                ref_map[gfdl]["source_file"]],
               "Project-level WPO evidence is insufficient; no reviewer overload or invented funding proof."),
        bundle("dataset_with_recovered_registry_metadata",ecmwf,"METADATA_VERIFIED_PROJECT_UNRESOLVED",
               "METADATA_VERIFIED_PROJECT_UNRESOLVED" if metadata[ecmwf]["metadata"]["status"]=="ok"
                  and not metadata[ecmwf]["wpo_project_funding_verified"]
                  else "INCORRECT_PROGRESSION",
               ["scout-operations/reports/queued-doi-metadata/latest.json",
                metadata[ecmwf]["source_notes"][0]["path"]],
               "DataCite metadata is recovered and reused; related dataset remains unverified as WPO-funded.",
               {"recovered_from":metadata[ecmwf]["metadata"]["provider"],
                "new_api_calls_for_cached_metadata":len(api_calls)}),
        bundle("preprint_guard",tornado,"PREPRINT_HOLD",pre["decision"],
               ["scout-operations/research-decision-cases.json",
                "scout-operations/preprint-watchlist.json"],
               "Tracked ESSOAr posted DOI is not staged; wait for official published-version research."),
        bundle("already_cataloged_published_version",gulf,"EXISTING_IN_REACH",dup["decision"],
               ["scout-operations/research-decision-cases.json",
                "scout-operations/reach-comparison-cache/comparison-index.json"],
               "Crossref original has a verified REACH identity; no duplicate Scout proposal.")
    ]
    require(all(x["verified"] for x in reports),"A real workflow branch failed its expected result")
    return {"schema":"reach-scout-five-case-source-fresh-workflow-replay-v1",
      "replay_mode":"READ_ONLY_CURRENT_SOURCE_FULL_ENGINE_WITH_OPTIONAL_LIVE_DOI",
      "live_official_metadata_probes":live,
      "case_count":len(reports),"passed":sum(x["verified"] for x in reports),
      "failed":sum(not x["verified"] for x in reports),
      "registry_source_sha256":sha("scout-operations/research-outcome-registry.json"),
      "source_evidence_files":registry["evidence_files_scanned"],
      "source_note_events":registry["research_note_events"],
      "doi_recovery_cached_success":recovered["metadata_recovered"],
      "new_public_candidates_created":0,"private_hub_imports":"NOT_VERIFIED",
      "human_approvals":"NOT_VERIFIED","formal_historical_statuses_mutated":0,
      "expansion_seed_closures":0,"reviewer_csv_writes":0,"cases":reports,
      "notes":"Replay executes live Scout source, metadata-cache, DOI identity, preprint, historical decision, and private-safe reviewer functions; checks existing published inbox artifact without writing it. Actual current private Hub sync is not simulated or claimed."}

def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("--live-metadata",action="store_true")
    cli.add_argument("--out",default=str(OUTPUT))
    args=cli.parse_args()
    result=build(live_metadata=args.live_metadata)
    target=Path(args.out)
    target.parent.mkdir(parents=True,exist_ok=True)
    rendered=json.dumps(result,indent=2,ensure_ascii=False)+"\n"
    if not target.exists() or target.read_text(encoding="utf-8")!=rendered:
        target.write_text(rendered,encoding="utf-8")
    print(json.dumps({"passed":result["passed"],"total":result["case_count"],
         "cases":{x["case"]:x["observed"] for x in result["cases"]},
         "live_api_probes":result["live_official_metadata_probes"]},indent=2))

if __name__=="__main__":main()
