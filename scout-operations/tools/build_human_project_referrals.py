#!/usr/bin/env python3
"""Source-bound HUMAN WPO project referrals, not new-output eligibility.

A bounded research pass with official publication and verified *public* absence
may become a validated NEEDS INVESTIGATION draft. This never approves WPO
funding, selects a Smartsheet parent, or proves a private Hub import.
"""
import argparse
import hashlib
import json
from datetime import date
from pathlib import Path

from build_research_outcome_registry import build as source_registry
from decision_pipeline import norm_doi
from reviewer_feedback_guard import known_feedback_by_doi

ROOT=Path(__file__).resolve().parents[2]
OUTPUT=ROOT/"scout-operations/human-project-referrals.json"
SCHEMA="reach-scout-bounded-project-human-referral-v1"
PURPOSE="NEEDS INVESTIGATION"
PROMOTE_LIMIT=3

def eligible_record(event, doc):
    """Provide an exact project-award search context, not a verified award."""
    cases=doc.get("cases")
    entry=next((x for x in cases if norm_doi(x.get("doi"))==norm_doi(event["doi"])),
               {}) if isinstance(cases,list) else doc
    award=str(entry.get("spark_primary_award_context") or entry.get("proposed_primary_award")
              or doc.get("proposed_primary_award") or "").strip()
    # General NOAA umbrella awards alone are not adequate project-specific
    # clues for automatic generation of another reviewer card.
    project=str(entry.get("spark_project_title") or entry.get("proposed_spark_project")
                or doc.get("proposed_spark_project") or "").strip()
    if not award or award in {"NOT_VERIFIED","UNK"}:
        return None
    if "PROJECT_TITLE" not in str(event.get("research_lane","")).upper() and not project:
        return None
    return {"award_context_only":award,"project_context_only":project,
            "source_case":entry}

def publication_meta_valid(meta):
    if meta.get("status")!="ok" or meta.get("publication_status")=="preprint":
        return False
    if not str(meta.get("pub_date") or ""):return False
    return str(meta.get("resource_type") or "").lower() in {
        "journal-article","proceedings-article","book-chapter","report"
    }

def referral_state(event,meta,identity,prior=None,watched=False,project=None):
    if watched:return "HOLD_PREPRINT_MONTHLY_WATCH"
    if prior:return "HOLD_EXISTING_HUMAN_DECISION"
    if not project:return "HOLD_UNVERIFIED_PROJECT_CONTEXT"
    if not publication_meta_valid(meta):return "HOLD_OFFICIAL_PUBLICATION_OR_METADATA"
    s=identity.get("status")
    if s in {"CONFIRMED_PUBLIC_REACH_IDENTITY","IN_PUBLIC_SCOUT_QUEUE"}:
        return "HOLD_ALREADY_IN_PUBLIC_REACH_OR_SCOUT"
    if s!="NO_PUBLIC_IDENTITY_MATCH":
        return "HOLD_IDENTITY_OR_VERSION_AMBIGUOUS"
    ir=(identity.get("noaa_ir_reach_check") or {}).get("status","NOT_VERIFIED")
    if ir in {"IR_INDEX_UNAVAILABLE_HOLD","AMBIGUOUS_IR_DOI_HOLD",
               "MULTIPLE_REACH_RECORDS_HOLD","REACH_DOI_CONFLICT_VERSION_REVIEW",
               "IR_URL_MATCH_REQUIRES_REVIEW"}:
        return "HOLD_IR_OR_REACH_SOURCE_INCOMPLETE"
    if not event.get("bounded_human_question_to_verify"):
        return "HOLD_RESEARCH_PROOF_INCOMPLETE"
    return "READY_FOR_VALIDATED_HUMAN_PROJECT_REFERRAL"

def proposal(doi,meta,event,project):
    urls=event["checked_evidence_urls"]
    primary=next((x for x in urls if "ieeexplore.ieee.org" in x or
                  "journals.ametsoc.org" in x or "onlinelibrary.wiley.com" in x),urls[0])
    title=str(meta.get("title") or "").strip()
    if not title:return None
    authors="; ".join(str(x) for x in meta.get("creators",[])[:20] if x)
    core_id=hashlib.sha256((doi+"|"+event["event_id"]).encode()).hexdigest()[:18]
    fields={"Title":title,"DOI":doi,"Output URL":"https://doi.org/"+doi,
        "Output Type":"1","NOAA Award Number(s)":"",
        "Proposed Project Title":"","Suggested Parent Project":"",
        "Authors / PI":authors,"Publication Date":meta.get("pub_date") or "",
        "Brief Abstract":meta.get("abstract") or "",
        "Evidence URL":primary,"Funding Evidence URL":"",
        "Existing REACH Match":"No public DOI/title/URL match in SHA-verified REACH/Scout + official NOAA IR crosswalk. Private history not verified.",
        "Scout Confidence":"Low",
        "Source Run ID":"REACH-SCOUT-HUMAN-SCOPE-"+core_id}
    context="Research was bounded; publisher/program evidence supports publication identity but the specific WPO primary project association has NOT been demonstrated."
    question=("Is this independently published output a deliverable of SPARK primary award "+
             project["award_context_only"]+" (rather than merely topically related), and if so which project parent should it use?")
    prov={"classification":PURPOSE,
        "route":"Independent discovery",
        "origin_method":"Independent discovery",
        "discovery_method":"SPARK project-title lead, official publisher and program follow-up",
        "path_evidence":meta.get("evidence") or primary,
        "publication_status":"published",
        "notes":[
            "Finding: Official publication metadata identifies "+title+"; WPO project eligibility remains unresolved.",
            "What to check before adding this output: Verify primary SPARK project award and explicit output-to-project bridge; check publisher funding; confirm no duplicate REACH or version family before approving.",
            "Reviewer question: "+question,
            "Research handoff: bounded project-attribution question, NOT an eligible new REACH output or approved association.",
            "Potential primary SPARK award SEARCH CONTEXT ONLY: "+project["award_context_only"],
            "Research source evidence: "+" ; ".join(urls[:5]),
            "Private Hub import and any prior unsynchronized review remain NOT VERIFIED.",
            context]}
    return {"fields":fields,"provenance":prov}

def existing_verified_self_draft(root,doi,event,check,previous):
    """Only recognize an exact prior self-created inbox DOI, never another case."""
    if not previous or check.get("status")!="IN_PUBLIC_SCOUT_QUEUE":
        return None
    old=next((r for r in previous.get("referrals",[]) if
              r.get("doi")==doi and r.get("source_event_id")==event["event_id"]
              and r.get("source_sha256")==event["source_sha256"]
              and r.get("scout_inbox_status") in {
                "VALIDATED_INBOX_DRAFT_NOT_PRIVATE_HUB",
                "EXISTING_VERIFIED_INBOX_DRAFT"}),None)
    if not old:return None
    import csv
    for rel in previous.get("draft_paths",[]):
        path=(root/rel).resolve()
        allowed=root/"scout-discoveries/inbox"
        if path.parent!=allowed.resolve() or not path.is_file():
            continue
        # Never count an already published batch as a new human handoff.
        if (root/"scout-discoveries/batches"/path.name).exists():
            continue
        with path.open(encoding="utf-8-sig",newline="") as f:
            rows=list(csv.DictReader(f))
        if (len(rows)!=1 or str(rows[0].get("DOI","")).lower()!=doi or
            "Scout classification: NEEDS INVESTIGATION" not in
                str(rows[0].get("Scout Discovery Rationale",""))):
            continue
        matches=check.get("matches",[])
        if (matches and all(m.get("source")=="SCOUT_INBOX" and
            str(m.get("location","")).startswith(rel+":") for m in matches)):
            return path
    return None



def existing_verified_published_self_referral(root,doi,event,check,previous):
    """Verify one previously owned, now published *public* Scout review unit.

    Publishing a public review feed row is NOT a private Hub import, approval,
    Smartsheet insertion, or REACH addition. Only SHA-verified exact matching
    immutable batch contents may upgrade the public-feed lifecycle stage.
    """
    if not previous or check.get("status")!="IN_PUBLIC_SCOUT_QUEUE":
        return None
    old=next((r for r in previous.get("referrals",[]) if
              r.get("doi")==doi and r.get("source_event_id")==event["event_id"]
              and r.get("source_sha256")==event["source_sha256"]
              and r.get("scout_inbox_status") in {
                  "VALIDATED_INBOX_DRAFT_NOT_PRIVATE_HUB",
                  "EXISTING_VERIFIED_INBOX_DRAFT",
                  "PUBLISHED_PUBLIC_SCOUT_FEED_NOT_PRIVATE_HUB"}),None)
    if not old:return None
    names={Path(rel).name for rel in (
        previous.get("draft_paths",[])+previous.get("published_batch_paths",[]))
        if str(rel).startswith(("scout-discoveries/inbox/",
                                "scout-discoveries/batches/"))}
    if not names:return None
    manifest_path=root/"scout-discoveries/manifest.json"
    if not manifest_path.is_file():raise ValueError("Missing authoritative published feed manifest")
    manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema")!="reach-scout-discovery-feed-v1":
        raise ValueError("Unrecognized public discovery manifest schema")
    if manifest.get("batch_count")!=len(manifest.get("batches",[])):
        raise ValueError("Published feed batch manifest incomplete")
    import csv
    found=[]
    for b in manifest["batches"]:
        rel=str(b.get("path") or "")
        if (not rel.startswith("scout-discoveries/batches/")
            or Path(rel).name not in names):continue
        path=(root/rel).resolve()
        if (not path.is_relative_to((root/"scout-discoveries/batches").resolve())
            or not path.is_file()):raise ValueError("Invalid published referral batch file: "+rel)
        if hashlib.sha256(path.read_bytes()).hexdigest()!=b["sha256"]:
            raise ValueError("Published human referral batch SHA mismatch: "+rel)
        with path.open(encoding="utf-8-sig",newline="") as f:
            rows=list(csv.DictReader(f))
        if len(rows)!=b["record_count"]:
            raise ValueError("Published referral batch source row count mismatch")
        target=[x for x in rows if str(x.get("DOI","")).lower()==doi]
        if not target:continue
        if len(target)!=1 or len(rows)!=1:
            raise ValueError("Published human referral must be a single unambiguous DOI record")
        row=target[0]
        expected="REACH-SCOUT-HUMAN-SCOPE-"+hashlib.sha256(
            (doi+"|"+event["event_id"]).encode()).hexdigest()[:18]
        if (row.get("Source Run ID")!=expected or row.get("NOAA Award Number(s)")
            or "Scout classification: NEEDS INVESTIGATION" not in
               str(row.get("Scout Discovery Rationale",""))):
            raise ValueError("Published referral identity, funding or category contradiction")
        matches=check.get("matches",[])
        if (not any(m.get("source")=="SCOUT_PUBLISHED"
                    and m.get("location")==rel+":2" for m in matches)
            or any(m.get("source")=="REACH" for m in matches)):
            raise ValueError("Published referral DOI conflicts with current REACH/Scout identity")
        found.append(path)
    if len(found)>1:raise ValueError("Multiple published self-referrals for the same DOI")
    return found[0] if found else None



def build(root=ROOT,metadata=None,public_identity=None,stage=False):
    import sys
    sys.path.insert(0,str(root/"scout-discoveries/tools"))
    from prepare_batch import prepare,validate_canonical,is_tracked_preprint
    from ir_reach_identity import verified_snapshot,identity_check
    if metadata is None:
        from lookup_independent_dois import metadata as metadata_fn
        metadata=metadata_fn
    if public_identity is None:
        public,official_ir=verified_snapshot(root)
        public_identity=lambda doi,title:identity_check(public,official_ir,doi,title,"https://doi.org/"+doi)
        fingerprint=public["source_fingerprint"]
    else:fingerprint="TEST_PUBLIC_IDENTITY_FIXTURE"
    registry=source_registry(root)
    previous=known_feedback_by_doi(root)
    prior_path=root/OUTPUT.relative_to(ROOT)
    prior_report=json.loads(prior_path.read_text(encoding="utf-8")) if prior_path.is_file() else None
    if prior_report and prior_report.get("schema")!=SCHEMA:
        raise ValueError("Unexpected previous human referral contract; do not overwrite")
    potential={}
    for event in registry["events"]:
        if (event["bounded_human_question_to_verify"] and event["doi"] and
            event["operational_disposition"]=="BOUNDED_PROJECT_QUESTION_FOR_HUMAN"):
            potential.setdefault(event["doi"],[]).append(event)
    responses=[]
    submitted=[]
    already_published=[]
    for doi,events in sorted(potential.items()):
        source=sorted(events,key=lambda e:e["source_path"])[-1]
        doc=json.loads((root/source["source_path"]).read_text(encoding="utf-8"))
        project=eligible_record(source,doc)
        # Only DOI-verified, independently sourced publication research with a
        # concrete project-title/primary-award search context may consume API.
        cached=next((r for r in (prior_report or {}).get("referrals",[])
            if r.get("doi")==doi and r.get("source_event_id")==source["event_id"]
            and r.get("source_sha256")==source["source_sha256"]
            and r.get("official_metadata",{}).get("status")=="ok"),None)
        meta=(cached["official_metadata"] if project and cached else
              metadata(doi) if project else
              {"status":"NOT_ATTEMPTED_UNVERIFIED_PROJECT_CONTEXT"})
        check=public_identity(doi,meta.get("title","")) if project else {"status":"NOT_CHECKED"}
        own_draft=existing_verified_self_draft(root,doi,source,check,prior_report)
        own_published=existing_verified_published_self_referral(
            root,doi,source,check,prior_report)
        effective_check=({**check,"status":"NO_PUBLIC_IDENTITY_MATCH"} if own_draft else check)
        state=referral_state(source,meta,effective_check,previous.get(doi),
              is_tracked_preprint(doi),project)
        candidate=proposal(doi,meta,source,project) if state=="READY_FOR_VALIDATED_HUMAN_PROJECT_REFERRAL" else None
        status="NOT_STAGED"
        if own_published:
            # A public proposal is an existing unit of review work, never
            # a new inbox draft or proof that the private Hub imported it.
            status="PUBLISHED_PUBLIC_SCOUT_FEED_NOT_PRIVATE_HUB"
            already_published.append(own_published.relative_to(root).as_posix())
        elif candidate and stage and len(submitted)>=PROMOTE_LIMIT:
            status="READY_DEFERRED_REVIEWER_CAP"
        elif candidate and stage:
            name=date.today().isoformat()+"-human-project-"+hashlib.sha256(doi.encode()).hexdigest()[:18]+".csv"
            path=own_draft or root/"scout-discoveries/inbox"/name
            if path.exists():
                validate_canonical(path)
                status="EXISTING_VERIFIED_INBOX_DRAFT"
                if not (root/"scout-discoveries/batches"/path.name).exists():
                    submitted.append(path.relative_to(root).as_posix())
            else:
                inp=root/"scout-operations"/(".human-referral-"+hashlib.sha256(doi.encode()).hexdigest()[:14]+".json")
                inp.write_text(json.dumps({"candidates":[candidate]},ensure_ascii=False))
                try:prepare(inp,path)
                finally:inp.unlink(missing_ok=True)
                status="VALIDATED_INBOX_DRAFT_NOT_PRIVATE_HUB"
                submitted.append(path.relative_to(root).as_posix())
        elif candidate:status="READY_NOT_PUBLISHED_PREVIEW"
        responses.append({"doi":doi,"source_event_id":source["event_id"],
            "source_file":source["source_path"],"source_sha256":source["source_sha256"],
            "official_metadata":meta,"public_identity":check,
            "project_search_context_only":{k:v for k,v in (project or {}).items() if k!="source_case"},
            "disposition":state,
            "review_question":(candidate["provenance"]["notes"][2] if candidate else
                               cached.get("review_question",source["next_action"]) if cached else
                               source["next_action"]),
            "scout_inbox_status":status,
            "published_scout_batch_path":(own_published.relative_to(root).as_posix()
                                         if own_published else None),
            "eligible_for_new_reach_addition":"NOT_VERIFIED",
            "private_hub_import":"NOT_VERIFIED",
            "human_approval":"NOT_VERIFIED"})
    return {"schema":SCHEMA,
        "source_outcome_event_count":registry["research_note_events"],
        "source_outcome_sha256":hashlib.sha256(json.dumps(registry,sort_keys=True).encode()).hexdigest(),
        "unique_bounded_project_questions":len(potential),
        "human_referral_drafts_prevalidated":len(submitted),
        "draft_paths":submitted,
        "published_batch_paths":already_published,
        "verified_public_scout_referral_batches":len(already_published),
        "human_reviewer_decisions":"NOT_VERIFIED",
        "private_hub_imports":"NOT_VERIFIED",
        "new_approved_reach_outputs":0,
        "policy":"Bounded investigation can refer an independently published DOI for a human WPO-project funding question. No project award or REACH eligibility is asserted. Preprint, duplicate, no-source or prior-human-review cases stay held.",
        "referrals":responses}

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--stage",action="store_true")
    args=a.parse_args()
    r=build(stage=args.stage)
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    text=json.dumps(r,indent=2,ensure_ascii=False)+"\n"
    if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8")!=text:
        OUTPUT.write_text(text,encoding="utf-8")
    print(json.dumps({"review_questions":r["unique_bounded_project_questions"],
                      "validated_inbox_drafts":r["human_referral_drafts_prevalidated"],
                      "statuses":{x["doi"]:x["disposition"] for x in r["referrals"]}},indent=2))

if __name__=="__main__":main()
