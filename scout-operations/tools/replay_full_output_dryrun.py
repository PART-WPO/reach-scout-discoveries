#!/usr/bin/env python3
"""One-output real preflight replay, public evidence only.

Runs the ACTUAL Scout shared REACH/Scout/NOAA-IR identity checks, referral
decision and canonical 24-column CSV validator against an already researched
candidate. Does not call external APIs, create permanent inbox/batches, modify
source registries or claim a private Hub import/decision.
"""
import argparse
import csv
import hashlib
import html
import json
import re
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"scout-operations/tools"))
sys.path.insert(0,str(ROOT/"scout-discoveries/tools"))
from build_human_project_referrals import (proposal, referral_state, eligible_record,
    score_for_human_review)
from ir_reach_identity import verified_snapshot, identity_check
from reviewer_feedback_guard import known_feedback_by_doi
from prepare_batch import prepare, validate_canonical, is_tracked_preprint

QUEUE="scout-operations/crossref-candidate-queue.json"
REFERRALS="scout-operations/human-project-referrals.json"
OUTPUT="scout-operations/reports/one-mission-dry-run"
TEST_DOI="10.1029/2026jd046327"

def sha(b):
    return hashlib.sha256(b).hexdigest()

def load(root, relative):
    return json.loads((root/relative).read_text(encoding="utf-8"))

def source_checks(root, queue):
    """Fail closed rather than treating a stale historical selection as new."""
    checks={}
    for rel,expected in queue["source_sha256"].items():
        path=(root/rel).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file():
            raise ValueError("Unsafe/missing queue source: "+rel)
        ok=sha(path.read_bytes())==expected
        checks[rel]=ok
        if not ok:
            raise ValueError("Stale queue source SHA: "+rel)
    return checks

def plain_abstract(value):
    # The cached Crossref abstract can contain JATS/XML markup; do not
    # paste raw markup into an editable review sheet.
    cleaned=re.sub(r"<[^>]+>"," ",str(value or ""))
    return re.sub(r"\s+"," ",html.unescape(cleaned)).strip()

def run(root=ROOT,doi=TEST_DOI,outdir=None):
    doi=doi.lower()
    queue=load(root,QUEUE)
    checks=source_checks(root,queue)
    preview=queue.get("next_one_mission_original_preview",[])
    selected=next((p for p in preview if p.get("doi")==doi),None)
    if not selected:
        raise ValueError("Requested DOI is no longer in source-fresh one-mission selection preview")
    if selected["lane"] not in ("NOVEL_IDENTITY_RESEARCH","HUMAN_REVIEW_FAST_SCREEN_DUE"):
        raise ValueError("Requested DOI no longer eligible for direct new-original review")

    referrals=load(root,REFERRALS)
    matched=[r for r in referrals.get("referrals",[]) if r.get("doi")==doi]
    if len(matched)!=1:
        raise ValueError("No unique prior Scout research-referral for next selected original")
    prior=matched[0]
    note_rel=prior["source_file"]
    note_bytes=(root/note_rel).read_bytes()
    if sha(note_bytes)!=prior["source_sha256"]:
        raise ValueError("Research-referral evidence source SHA mismatch")
    note=json.loads(note_bytes)
    event={
        "doi":doi,
        "event_id":prior["source_event_id"],
        "research_lane":"historical_crossref_original",
        "checked_evidence_urls":[
            "https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2026JD046327",
            "https://repository.library.noaa.gov/view/noaa/77328",
        ],
    }
    project=eligible_record(event,note)
    if not project:
        raise ValueError("No grounded WPO award search context; do not create candidate")

    metadata=prior.get("official_metadata",{})
    if str(metadata.get("publication_status","")).lower()=="preprint":
        raise ValueError("Preprint cannot be passed to Discovery Hub")
    prior_human=known_feedback_by_doi(root).get(doi)
    public,official_ir=verified_snapshot(root)
    identity=identity_check(public,official_ir,doi,metadata.get("title",""),
                            "https://doi.org/"+doi)
    watched=is_tracked_preprint(doi)
    decision=referral_state(event,metadata,identity,prior_human,watched,project)
    score=score_for_human_review(metadata,identity,project,event["checked_evidence_urls"])

    result={
        "schema":"reach-scout-one-output-verified-dryrun-v1",
        "read_only":True,
        "external_research_requests":0,
        "selected_from_current_one_mission_preview":True,
        "selected_doi":doi,
        "title":metadata.get("title"),
        "queue_lane":selected["lane"],
        "queue_priority":selected["priority"],
        "queue_sources_sha_verified":len(checks),
        "source_note":note_rel,
        "source_note_sha256":prior["source_sha256"],
        "official_metadata_provider":metadata.get("provider"),
        "official_record_type":metadata.get("resource_type"),
        "crossref_preferred_pub_date":metadata.get("pub_date"),
        "publisher_version_of_record_online":"2026-09-03",
        "date_discrepancy_for_reviewer":"Publisher version of record September 3, 2026; Crossref published-print preferred date September 16, 2026",
        "potential_wpo_award_unverified":project["award_context_only"],
        "wpo_funding_scope":"Publisher confirms WPO partially supported NEMO development; does NOT establish the whole article as an exact SPARK project deliverable.",
        "source_identity_status":identity.get("status"),
        "noaa_ir_identity_status":identity.get("noaa_ir_reach_check",{}).get("status"),
        "noaa_ir_url":identity.get("noaa_ir_reach_check",{}).get("official_url"),
        "known_signed_human_decision":bool(prior_human),
        "is_watchlisted_preprint":bool(watched),
        "decision":decision,
        "screening_score_0_to_100_uncalibrated":score["score"],
        "screening_confidence":score["band"],
        "previous_referral_status":prior["scout_inbox_status"],
        "reviewer_question":"Does the award's partial support for NEMO development make this article a deliverable of the specific WPO-funded project, and if so which SPARK parent should be selected?",
        "public_review_candidate_validated":False,
        "private_hub_import":"NOT_VERIFIED",
        "human_approval":"NOT_VERIFIED",
        "new_public_scout_batch_published":False,
        "new_reach_output_published":False,
    }

    out=(Path(outdir) if outdir else root/OUTPUT).resolve()
    out.mkdir(parents=True,exist_ok=True)
    if decision=="READY_FOR_VALIDATED_HUMAN_PROJECT_REFERRAL":
        candidate=proposal(doi,metadata,event,project,identity)
        if not candidate:
            raise ValueError("Scout referral builder did not produce a candidate")
        candidate["fields"]["Brief Abstract"]=plain_abstract(metadata.get("abstract"))
        # Keep unproven funding out of the authoritative award/parent fields.
        candidate["provenance"]["discovery_method"]=(
            "Historic Crossref primary-award lead, direct publisher acknowledgment "
            "and verified NOAA IR record")
        conf=score["score"]
        candidate["provenance"]["notes"]=[
            "Finding: Officially published Oklahoma compound heat and ozone study with exact DOI; NOAA WPO grant supports NEMO development used in the article.",
            "What to check before adding this output: Confirm SPARK primary project for award "+
                project["award_context_only"]+"; assess whether NEMO's partial support makes the article a funded project deliverable; verify canonical REACH version and parent before approval.",
            "Reviewer question: "+result["reviewer_question"],
            "Scout screening score: "+str(conf)+"/100 ("+score["band"]+
                "); heuristic review priority, NOT probability of WPO project eligibility.",
            "Funding distinction: Publisher says article primarily funded by UNSA and NASA; WPO partially supported NEMO development. No automatic full-article funding attribution.",
            "Date source review: Publisher version of record online 2026-09-03; Crossref published-print selected 2026-09-16. Keep source distinction for reviewer.",
            "Unverified funding context only: "+project["award_context_only"],
            "Official publisher evidence: https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2026JD046327",
            "Official NOAA IR record: https://repository.library.noaa.gov/view/noaa/77328",
            "Existing REACH public screening negative; private Hub reviewer history not verified without signed record.",
        ]
        basename="2026-11-09-mission-dryrun-compound-heat-ozone.csv"
        candidate_input=out/"candidate-input.json"
        candidate_input.write_text(json.dumps({"candidates":[candidate]},
                                              ensure_ascii=False),encoding="utf-8")
        csv_path=out/basename
        validate=prepare(candidate_input,csv_path)
        revalidated=validate_canonical(csv_path)
        if validate["record_count"]!=1 or revalidated["record_count"]!=1:
            raise ValueError("Canonical public candidate preflight did not validate exactly one output")
        with csv_path.open(encoding="utf-8-sig",newline="") as fd:
            rows=list(csv.DictReader(fd))
        row=rows[0]
        if (row["DOI"].lower()!=doi or row["NOAA Award Number(s)"] or
            row["Suggested Parent Project"] or row["Principal Investigator Email(s)"]):
            raise ValueError("The proposal incorrectly asserted project/award or personal data")
        if "Scout classification: NEEDS INVESTIGATION" not in row["Scout Discovery Rationale"]:
            raise ValueError("Incorrect public candidate route")
        if row["Scout Confidence"]!=score["band"]:
            raise ValueError("Incorrect confidence band")
        result.update({
            "public_review_candidate_validated":True,
            "review_feed_classification":"NEEDS INVESTIGATION",
            "preflight_24_columns":len(rows[0]),
            "preflight_candidate_count":validate["record_count"],
            "ir_flag_for_new_output":row["IR?"],
            "ir_url_in_prepared_record":row["IR Repository URL"],
            "actual_review_confidence_band":row["Scout Confidence"],
            "unverified_award_field_left_blank":True,
            "unverified_parent_field_left_blank":True,
            "proposed_public_review_csv":basename,
            "simulation_outcome":"PREPARED_AND_VALIDATED_NOT_PUBLISHED",
        })
    else:
        result["simulation_outcome"]="FAST_EXIT_OR_BLOCKED_"+decision
    report=out/"full-output-screening-report.json"
    report.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return result

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--doi",default=TEST_DOI)
    parser.add_argument("--outdir",default=OUTPUT)
    a=parser.parse_args()
    result=run(doi=a.doi,outdir=ROOT/a.outdir)
    print(json.dumps(result,indent=2,ensure_ascii=False))
if __name__=="__main__":
    main()
