#!/usr/bin/env python3
"""Validate redacted, HMAC-signed Discovery Hub review feedback.

The private Google Apps Script remains the authority for reviewer decisions.
A public Scout report is advisory, never proof of Smartsheet write or REACH
publication. Without an authenticated signed event, do not change counts.
"""
import hashlib
import hmac
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from decision_pipeline import build_index, norm_doi

ROOT=Path(__file__).resolve().parents[2]
INBOX=ROOT/"scout-operations/reviewer-feedback-inbox"
OUTPUT=ROOT/"scout-operations/research-feedback.json"
SCHEMA="reach-scout-signed-review-feedback-v1"
CODES={
    "APPROVED_FOR_STAGING","ON_HOLD","REJECTED","ALREADY_IN_REACH",
    "UPDATE_NEEDED","UPDATED_IN_SMARTSHEET_REVIEWER_REPORTED","NO_UPDATE_NEEDED"
}
EVENT_KEYS={"candidate_id","doi","decision","reviewed_at",
            "finding_fingerprint","decision_fingerprint","signature"}
CANDIDATE_ID=re.compile(r"scoutnew-v1-[0-9a-f]{32}")
HEX=re.compile(r"[0-9a-f]{32,128}")
SIGNATURE=re.compile(r"[0-9a-f]{64}")

def event_message(e):
    return "\n".join(["reach-scout-feedback-v1",e["candidate_id"],e["doi"],
                      e["decision"],e["reviewed_at"],e["finding_fingerprint"],
                      e["decision_fingerprint"]]).encode("utf-8")

def verify_event(e,key):
    if set(e)!=EVENT_KEYS:raise ValueError("Feedback contains unexpected or potentially identifying fields")
    if not CANDIDATE_ID.fullmatch(e["candidate_id"]):raise ValueError("Bad candidate identifier")
    d=norm_doi(e["doi"])
    if not d or d!=e["doi"]:raise ValueError("Non-canonical DOI")
    if e["decision"] not in CODES:raise ValueError("Unsupported review outcome")
    if not HEX.fullmatch(e["finding_fingerprint"]) or not HEX.fullmatch(e["decision_fingerprint"]):
        raise ValueError("Missing verified private decision and source fingerprints")
    if not SIGNATURE.fullmatch(e["signature"]):raise ValueError("Malformed reviewer signature")
    at=e["reviewed_at"]
    try:timestamp=datetime.fromisoformat(at.replace("Z","+00:00"))
    except (ValueError,TypeError):raise ValueError("Bad ISO reviewer decision timestamp")
    if timestamp.tzinfo is None or timestamp.astimezone(timezone.utc).year<2020:
        raise ValueError("Missing trusted reviewer timezone")
    expected=hmac.new(key.encode("utf-8"),event_message(e),hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected,e["signature"]):
        raise ValueError("Reviewer feedback signature mismatch; no signals accepted")
    return hashlib.sha256(event_message(e)).hexdigest()[:24]

def extract_valid_events(bundles,index,key):
    known={}
    for rec in index["records"]:
        if rec["source"] in {"SCOUT_PUBLISHED","SCOUT_INBOX"}:
            known.setdefault(rec["identity"],set()).update(rec["dois"])
    confirmed=[];manual=[]
    seen={}
    for rel,data,source_sha in bundles:
        if data.get("schema")!=SCHEMA or data.get("source")!="DiscoveryHubPrivateExport":
            raise ValueError("Unrecognized private feedback export schema or source")
        if set(data)!={"schema","source","events"}:
            raise ValueError("Unnecessary private metadata in export")
        for e in data.get("events",[]):
            identity=verify_event(e,key)
            previous=seen.get(identity)
            if previous and previous!=e:
                raise ValueError("Two different signed events share one identity")
            seen[identity]=e
            result={"event_id":identity,"candidate_id":e["candidate_id"],
                    "doi":e["doi"],"decision_code":e["decision"],
                    "reviewed_at":e["reviewed_at"],
                    "finding_fingerprint":e["finding_fingerprint"],
                    "decision_fingerprint":e["decision_fingerprint"],
                    "bundle_path":rel,"bundle_sha256":source_sha,
                    "source":"SIGNED_PRIVATE_DISCOVERY_HUB_EXPORT",
                    "reviewer_identity": "REDACTED",
                    "private_hub_action_verified":True,
                    "smartsheet_write_verified":False,
                    "public_reach_addition_verified":False,
                    "automatic_research_status_change":False}
            if e["candidate_id"] in known and e["doi"] in known[e["candidate_id"]]:
                confirmed.append(result)
            else:
                result["manual_reconciliation_reason"]="Public candidate/DOI association is no longer in the active verified Scout feed"
                manual.append(result)
    return confirmed,manual

def run(root=ROOT,key=None,index=None):
    secret=os.environ.get("SCOUT_FEEDBACK_HMAC_KEY","") if key is None else key
    files=sorted((root/"scout-operations/reviewer-feedback-inbox").glob("*.json"))
    bundles=[]
    for path in files:
        b=path.read_bytes()
        bundles.append((path.relative_to(root).as_posix(),json.loads(b),
                        hashlib.sha256(b).hexdigest()))
    if bundles and not secret:
        raise ValueError("SCOUT_FEEDBACK_HMAC_KEY absent: signed private feedback cannot be imported")
    shared=index if index is not None else build_index(root)
    events,unlinked=extract_valid_events(bundles,shared,secret) if bundles else ([],[])
    dest=root/"scout-operations/research-feedback.json"
    prior=json.loads(dest.read_text(encoding="utf-8")) if dest.exists() else {"signals":[]}
    if prior.get("schema")!="reach-scout-research-feedback-v1":
        raise ValueError("Unknown research-feedback schema")
    # Append-only public operational signals; never replace a preexisting
    # human decision or lower an approved candidate's effective history.
    previous={x["event_id"]:x for x in prior["signals"] if "event_id" in x}
    for current in events:
        k=current["event_id"]
        if k in previous and previous[k]!=current:
            raise ValueError("Previously accepted reviewer signal was altered")
        previous[k]=current
    if len(previous)<len([x for x in prior["signals"] if "event_id" in x]):
        raise ValueError("Prior reviewer signal lost")
    signal_rows=sorted(previous.values(),key=lambda x:(x["reviewed_at"],x["event_id"]))
    return {"schema":"reach-scout-research-feedback-v1",
            "repository":"PART-WPO/reach-scout-discoveries",
            "note":"Public minimized, authenticated reviewer disposition signals ONLY; do not treat Approved for Staging as Smartsheet insertion or public REACH publication. Never infer a private decision from missing feedback.",
            "signals":signal_rows,
            "signed_bundle_files_checked":len(bundles),
            "verified_signed_events_count":len(events),
            "events_held_for_manual_identity_reconciliation":unlinked,
            "private_hub_connection_status":("SIGNED_EXPORT_VALIDATED" if bundles else "NOT_CONNECTED_OR_NOT_EXPORTED"),
            "source_identity_fingerprint":shared["source_fingerprint"]}

def main():
    result=run()
    serialized=json.dumps(result,indent=2,ensure_ascii=False)+"\n"
    if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8")!=serialized:
        OUTPUT.write_text(serialized,encoding="utf-8")
    print(json.dumps({"signed_bundles":result["signed_bundle_files_checked"],
                      "verified_review_events":result["verified_signed_events_count"],
                      "manual_identity_holds":len(result["events_held_for_manual_identity_reconciliation"]),
                      "private_connection":result["private_hub_connection_status"]},indent=2))

if __name__=="__main__":main()
