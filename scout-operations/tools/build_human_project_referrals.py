#!/usr/bin/env python3
"""Source-bound Scout referrals for new outputs or funding-scope investigation.

An official publisher-deposited 459 grant on the exact DOI establishes WPO
funding and can yield a NEW CANDIDATE for review. All other unverified
project leads remain NEEDS INVESTIGATION. Neither route approves a Smartsheet
parent, proves private Hub import, or adds anything to public REACH.
"""
import argparse
import hashlib
import json
import re
from datetime import date
from pathlib import Path

from build_research_outcome_registry import build as source_registry
from decision_pipeline import norm_doi
from reviewer_feedback_guard import known_feedback_by_doi
from wpo_awards import WPO_459, official_459_awards

ROOT=Path(__file__).resolve().parents[2]
OUTPUT=ROOT/"scout-operations/human-project-referrals.json"
SCHEMA="reach-scout-bounded-project-human-referral-v1"
PURPOSE="NEEDS INVESTIGATION"
PROMOTE_LIMIT=3
WPO_AWARD_CUE=WPO_459
EXPLICIT_CONTRADICTION=(
    "CONTRADICTORY_TO_PILOT_PROJECT_AWARD",
    "NOT_CORROBORATED_AND_PARENT_PUBLICATION_HAS_CONTRADICTORY_AWARD",
    "VERIFIED_DIFFERENT_PROJECT",
    "CONTRADICTED",
    "DISPROVED",
)


def matching_note_case(event, doc):
    """Match exact output; never inherit parent funding into a child DOI."""
    subject=doc.get("research_subject")
    if isinstance(subject,dict) and subject.get("child_dois"):
        return None
    cases=doc.get("cases")
    if isinstance(cases,list):
        selected=[x for x in cases if isinstance(x,dict)
                  and norm_doi(x.get("doi"))==norm_doi(event.get("doi"))]
        return selected[0] if len(selected)==1 else None
    own=(doc.get("doi") or doc.get("original_doi") or
         doc.get("source_parent_original_doi"))
    if own and norm_doi(own)!=norm_doi(event.get("doi")):
        return None
    return doc

def note_contradicts_target(entry,doc):
    """Only structured *explicit* contradiction fields can screen out."""
    for obj in (entry,doc):
        if not isinstance(obj,dict):
            continue
        for key in ("funding","project_attribution","same_project_wpo_funding",
                    "award_evidence_status","funding_signal"):
            if str(obj.get(key) or "").strip().upper() in EXPLICIT_CONTRADICTION:
                return True
    return False

def eligible_record(event, doc):
    """Plausible WPO context for *human investigation*, not eligible funding."""
    entry=matching_note_case(event,doc)
    if entry is None or note_contradicts_target(entry,doc):
        return None
    award=str(entry.get("spark_primary_award_context")
              or entry.get("proposed_primary_award")
              or entry.get("primary_award_candidate")
              or entry.get("structured_award")
              or entry.get("structured_award_context")
              or entry.get("award_number_in_official_noaa_ir")
              or entry.get("wpo_primary_award")
              or doc.get("proposed_primary_award") or "").strip()
    project=str(entry.get("spark_project_title") or entry.get("proposed_spark_project")
                or doc.get("proposed_spark_project") or "").strip()
    if not award or award in {"NOT_VERIFIED","UNK","UNKNOWN","NONE"}:
        return None
    direct_wpo_cue=bool(WPO_AWARD_CUE.fullmatch(award))
    # Generic NOAA or Cooperative Institute context alone never creates an
    # automatic reviewer card, but a documented, specific SPARK project-title
    # lead remains a plausible human question.
    project_title_lead=("PROJECT_TITLE" in
        str(event.get("research_lane","")).upper() and bool(project))
    if not direct_wpo_cue and not project_title_lead:
        return None
    return {"award_context_only":award,"project_context_only":project,
            "source_case":entry,
            "wpo_award_cue_not_proof":direct_wpo_cue,
            "reason_for_review":("WPO-pattern award cited but exact funded project deliverable unverified"
                                if direct_wpo_cue else
                                "Specific SPARK project-title research lead needs human association")}

def score_for_human_review(meta,identity,project,source_urls):
    """Uncalibrated prioritization points, not probability or grant proof."""
    if not publication_meta_valid(meta) or identity.get("status")!="NO_PUBLIC_IDENTITY_MATCH":
        return {"score":0,"band":"Not ready","meaning":"Fast-screen eligibility unmet"}
    points=25  # officially dated distinct output identity
    if project.get("wpo_award_cue_not_proof"):
        points+=20
    if project.get("project_context_only"):
        points+=10
    if len({u for u in source_urls if str(u).startswith("https://")})>=2:
        points+=10
    if (identity.get("noaa_ir_reach_check") or {}).get("status") not in (
        "IR_INDEX_UNAVAILABLE_HOLD","AMBIGUOUS_IR_DOI_HOLD",
        "MULTIPLE_REACH_RECORDS_HOLD","REACH_DOI_CONFLICT_VERSION_REVIEW",
        "IR_URL_MATCH_REQUIRES_REVIEW"):
        points+=10
    points+=10  # fresh public identity screen has no matching output
    points=min(points,70)  # unconfirmed WPO project can never be "high"
    funded=project.get("award_context_only","").upper() in official_459_awards(meta)
    return {"score":points,"band":("Medium" if points>=50 else "Low"),
            "meaning":("Heuristic reviewer-readiness score; official 459 establishes WPO funding, not automatic output acceptance" if funded else
                       "Heuristic new-output screening priority; NOT calibrated probability or WPO funding proof")}

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
    return "READY_FOR_VALIDATED_HUMAN_PROJECT_REFERRAL"

def proposal(doi,meta,event,project,identity=None):
    urls=event["checked_evidence_urls"]
    primary=next((x for x in urls if "ieeexplore.ieee.org" in x or
                  "journals.ametsoc.org" in x or "onlinelibrary.wiley.com" in x),urls[0])
    title=str(meta.get("title") or "").strip()
    if not title:return None
    authors="; ".join(str(x) for x in meta.get("creators",[])[:20] if x)
    core_id=hashlib.sha256((doi+"|"+event["event_id"]).encode()).hexdigest()[:18]
    confidence=score_for_human_review(meta,identity or {"status":"NO_PUBLIC_IDENTITY_MATCH"},
                                      project,urls)
    official=official_459_awards(meta)
    context_award=str(project.get("award_context_only") or "").strip().upper()
    verified_awards=[a for a in official if a==context_award]
    wpo_verified=bool(verified_awards)
    classification="NEW CANDIDATE" if wpo_verified else PURPOSE
    fields={"Title":title,"DOI":doi,"Output URL":"https://doi.org/"+doi,
        "Output Type":"1","NOAA Award Number(s)":"; ".join(verified_awards),
        "Proposed Project Title":"","Suggested Parent Project":"",
        "Authors / PI":authors,"Publication Date":meta.get("pub_date") or "",
        "Brief Abstract":meta.get("abstract") or "",
        "Evidence URL":primary,
        "Funding Evidence URL":((meta.get("evidence") or "") if wpo_verified else ""),
        "Existing REACH Match":"No match in SHA-verified public REACH/Scout DOI, title or URL checks and official NOAA IR crosswalk. Private reviewer history not verified.",
        "Scout Confidence":confidence["band"],
        "Source Run ID":"REACH-SCOUT-HUMAN-SCOPE-"+core_id}
    if wpo_verified:
        question=("Select and verify the correct SPARK parent for the explicitly funded WPO award "+
                  context_award+"; confirm the output belongs with that parent before addition.")
        notes=[
            "Finding: Exact officially published DOI explicitly lists NOAA OAR459 award "+context_award+
                " in publisher-deposited Crossref funding metadata; WPO funding connection CONFIRMED.",
            "What to check before adding this output: Confirm title/DOI/version and select the correct SPARK primary project parent for "+
                context_award+"; reviewer retains final approval.",
            "Reviewer question: "+question,
            "Scout screening score: "+str(confidence["score"])+"/100 ("+confidence["band"]+"). "+confidence["meaning"],
            "Funding rule: 459 following OAR or OARX is WPO. Other award program codes such as 432, 011 or 469 do not negate an independently verified 459 award.",
            "Research handoff: NEW CANDIDATE, not Needs Investigation solely over WPO funding; no automatic private Hub/REACH insertion.",
            "Verified WPO Award Number(s): "+"; ".join(verified_awards),
            "Publisher-deposited funding evidence: "+str(meta.get("evidence") or primary),
            "Research source evidence: "+" ; ".join(urls[:5]),
            "Private Hub import and any prior unsynchronized review remain NOT VERIFIED."
        ]
    else:
        question=("Is this independently published output a deliverable of SPARK primary award "+
                 context_award+" (rather than merely topically related), and if so which project parent should it use?")
        notes=[
            "Finding: Official publication metadata identifies "+title+"; a 459 WPO funding connection on this exact DOI has NOT been verified.",
            "What to check before adding this output: Verify exact output-level WPO funding or a specific SPARK project relationship; check for duplicates before approval.",
            "Reviewer question: "+question,
            "Scout screening score: "+str(confidence["score"])+"/100 ("+confidence["band"]+"). "+confidence["meaning"],
            "Research handoff: Needs Investigation; cannot assume parent/child funding inheritance or project eligibility.",
            "Potential award SEARCH CONTEXT ONLY: "+context_award,
            "Research source evidence: "+" ; ".join(urls[:5]),
            "Private Hub import and any prior unsynchronized review remain NOT VERIFIED."
        ]
    prov={"classification":classification,
        "route":"Independent discovery",
        "origin_method":"Independent discovery",
        "discovery_method":"Publisher-deposited Crossref OAR459 award and SPARK parent selection" if wpo_verified
                           else "SPARK project-title lead, official publisher and program follow-up",
        "path_evidence":meta.get("evidence") or primary,
        "publication_status":"published",
        "notes":notes}
    return {"fields":fields,"provenance":prov}


def valid_prior_referral_row(row, metadata, expected_source_run_id):
    """Honor immutable old Needs Investigation batches and new verified-459 units."""
    if row.get("Source Run ID")!=expected_source_run_id:
        return False
    rationale=str(row.get("Scout Discovery Rationale",""))
    award=str(row.get("NOAA Award Number(s)") or "").strip().upper()
    if "Scout classification: NEEDS INVESTIGATION" in rationale:
        return not award
    if "Scout classification: NEW CANDIDATE" in rationale:
        return bool(award and award in official_459_awards(metadata))
    return False

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
            not valid_prior_referral_row(rows[0],old.get("official_metadata") or {},
                "REACH-SCOUT-HUMAN-SCOPE-"+hashlib.sha256(
                    (doi+"|"+event["event_id"]).encode()).hexdigest()[:18])):
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
        if not valid_prior_referral_row(row,old.get("official_metadata") or {},expected):
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
        if not event.get("doi") or not event["source_path"].startswith(
                "scout-operations/historical-crossref-phase2/"):
            continue
        path=root/event["source_path"]
        raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=event["source_sha256"]:
            raise ValueError("Source research note SHA mismatch: "+event["source_path"])
        doc=json.loads(raw)
        # Research notes select the DOI/award context. Exact publisher-deposited
        # 459 funding is checked separately from the official DOI metadata.
        project=eligible_record(event,doc)
        if (event.get("bounded_human_question_to_verify") or
             (project and event.get("checked_evidence_urls"))):
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
        candidate=proposal(doi,meta,source,project,effective_check) if state=="READY_FOR_VALIDATED_HUMAN_PROJECT_REFERRAL" else None
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
            "review_question":(next((n for n in candidate["provenance"]["notes"] if n.startswith("Reviewer question:")), "") if candidate else
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
        "unique_bounded_project_questions":sum(
            any(e.get("bounded_human_question_to_verify") for e in events)
            for events in potential.values()),
        "potential_wpo_cases_quick_screened":len(potential),
        "human_referral_drafts_prevalidated":len(submitted),
        "draft_paths":submitted,
        "published_batch_paths":already_published,
        "verified_public_scout_referral_batches":len(already_published),
        "human_reviewer_decisions":"NOT_VERIFIED",
        "private_hub_imports":"NOT_VERIFIED",
        "new_approved_reach_outputs":0,
        "policy":"A publisher-deposited Crossref funding record explicitly associating a valid OAR459/OARX459 award with this DOI confirms WPO funding. Route such officially published, publicly novel outputs to NEW CANDIDATE with the verified WPO award populated; other OAR codes (432, 011, 469) alone do not confirm WPO. Unverified/contradictory project leads remain NEEDS INVESTIGATION. Reviewer selects the correct SPARK parent; no auto approval, Hub import, or REACH addition.",
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
                      "potential_wpo_cases_quick_screened":r.get("potential_wpo_cases_quick_screened", 0),
                      "validated_inbox_drafts":r["human_referral_drafts_prevalidated"],
                      "statuses":{x["doi"]:x["disposition"] for x in r["referrals"]}},indent=2))

if __name__=="__main__":main()
