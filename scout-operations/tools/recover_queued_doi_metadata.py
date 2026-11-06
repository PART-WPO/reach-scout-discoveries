#!/usr/bin/env python3
"""Bounded exact-DOI recovery for access failures in Scout's research notes.

Reuse the existing DataCite→Crossref code in GitHub Actions. Never interpret a
failed request as missing DOI metadata; never stage the DOI or alter a reviewer.
"""
import argparse
import hashlib
import json
from datetime import datetime,timedelta,timezone
from pathlib import Path
from collections import defaultdict

from decision_pipeline import norm_doi
ROOT=Path(__file__).resolve().parents[2]
REG="scout-operations/research-outcome-registry.json"
OUT="scout-operations/reports/queued-doi-metadata/latest.json"
SCHEMA="reach-scout-doi-fallback-queue-v1"
BAD=("ACCESS_FAIL","ACCESS_FAILURE","ACCESS_FAILED","SOURCE_UNAVAILABLE",
     "NETWORK_OR_TOOL_FAILURE","TIMEOUT","RATE_LIMIT","HTTP_429","DNS")

def sha(blob):return hashlib.sha256(blob).hexdigest()
def read(root,p):
    b=(root/p).read_bytes()
    return json.loads(b),sha(b)

def failed(v):
    if isinstance(v,dict):
        return any(failed(v.get(k)) for k in ("status","metadata_result","error","error_category"))
    return any(x in str(v or "").upper() for x in BAD)

def extract_failures(doc):
    """Return DOI-specific source evidence only; never extract DOI from prose."""
    found=[]
    for item in doc.get("cases",[]) if isinstance(doc.get("cases"),list) else []:
        d=norm_doi(item.get("doi"))
        if d and any(failed(item.get(k)) for k in ("datacite_exact_metadata","metadata_result",
                   "metadata_attempt_status","metadata_status","metadata")):
            found.append((d,"NESTED_EXACT_DOI_ACCESS_FAILURE"))
    for item in doc.get("related_outputs",[]) if isinstance(doc.get("related_outputs"),list) else []:
        d=norm_doi(item.get("doi"))
        if d and any(failed(item.get(k)) for k in ("metadata_result","datacite_exact_metadata","metadata_status")):
            found.append((d,"RELATED_OUTPUT_DOI_ACCESS_FAILURE"))
    for item in doc.get("findings",[]) if isinstance(doc.get("findings"),list) else []:
        d=norm_doi(item.get("doi"))
        if d and failed((doc.get("source_validation") or {}).get("datacite_exact_doi_api")):
            found.append((d,"SHARED_EXPLICIT_EXACT_DATACITE_ACCESS_FAILURE"))
    d=norm_doi(doc.get("doi") or doc.get("original_doi"))
    if d and any(failed(doc.get(k)) for k in ("metadata_result","datacite_exact_metadata","metadata_status")):
        found.append((d,"ORIGINAL_EXACT_DOI_ACCESS_FAILURE"))
    return sorted(set(found))

def queue(root=ROOT):
    registry,reg_sha=read(root,REG)
    if registry.get("schema")!="reach-scout-all-lane-research-outcomes-v1":
        raise ValueError("Wrong source outcome registry schema")
    if len(registry["source_sha256"])!=registry["evidence_files_scanned"]:
        raise ValueError("Incomplete source coverage")
    grouped=defaultdict(lambda:{"source_notes":[],"reasons":[]})
    for p,expected in registry["source_sha256"].items():
        source,actual=read(root,p)
        if actual!=expected:raise ValueError("Research note changed since source-verified registry: "+p)
        for doi,reason in extract_failures(source):
            item=grouped[doi]
            item["source_notes"].append({"path":p,"sha256":expected})
            item["reasons"].append(reason)
    candidates=[]
    for d,value in sorted(grouped.items()):
        candidates.append({"doi":d,
            "source_notes":sorted({x["path"]:x for x in value["source_notes"]}.values(),key=lambda x:x["path"]),
            "reasons":sorted(set(value["reasons"])),
            "source_identity_verified_for_review":False,
            "wpo_project_funding_verified":False,
            "publication_version_verified":False,
            "candidate_staged":False})
    return {"schema":SCHEMA,"source_registry_sha256":reg_sha,
        "source_note_files_verified":len(registry["source_sha256"]),
        "doi_queue_size":len(candidates),"queue":candidates,
        "policy":"A tool access failure requires exact DOI metadata retry in GitHub Actions. An absent DOI in a tool is not missing repository metadata. No candidate, WPO funding proof, or human decision is created."}

def need_attempt(previous,now):
    if not previous:return True
    if previous.get("metadata",{}).get("status")=="ok":return False
    last=previous.get("looked_up_at")
    if not last:return True
    when=datetime.fromisoformat(last.replace("Z","+00:00"))
    return now>=when+timedelta(hours=24)

def run(root=ROOT,lookup=None,identity=None,now=None,max_new=10):
    q=queue(root)
    now=now or datetime.now(timezone.utc)
    if lookup is None:
        # Existing exact DOI resolver handles DataCite first, Crossref
        # fallback, preprint status, print-first publication dates.
        from lookup_independent_dois import metadata
        lookup=metadata
    if identity is None:
        from ir_reach_identity import verified_snapshot,identity_check
        public,official_ir=verified_snapshot(root)
        identity=lambda d,title:identity_check(public,official_ir,d,title,"https://doi.org/"+d)
        fingerprint=public["source_fingerprint"]
    else:fingerprint="TEST_ONLY_TRUSTED_PUBLIC_IDENTITY_FIXTURE"
    prior={}
    path=root/OUT
    if path.exists():
        old=json.loads(path.read_text(encoding="utf-8"))
        if old.get("schema")!=SCHEMA:raise ValueError("Unexpected prior recovery report schema")
        prior={item["doi"]:item for item in old.get("records",[])}
    count=0;results=[]
    for item in q["queue"]:
        d=item["doi"]
        previous=prior.get(d)
        if previous and previous.get("metadata",{}).get("status")=="ok":
            response=previous["metadata"];looked=previous["looked_up_at"]
            state="CACHED_PREVIOUS_SUCCESS"
        elif previous and not need_attempt(previous,now):
            response=previous["metadata"];looked=previous.get("looked_up_at")
            state="RETRY_AFTER_24_HOURS"
        elif count>=max_new:
            response=(previous or {}).get("metadata",{"status":"PENDING_GITHUB_LOOKUP"})
            looked=(previous or {}).get("looked_up_at")
            state="QUEUED_NOT_RUN_CAPACITY_BOUND"
        else:
            response=lookup(d)
            if not isinstance(response,dict) or "status" not in response:
                raise ValueError("Invalid provider response for "+d)
            if response["status"]=="ok":
                if not str(response.get("evidence","")).startswith("https://"):
                    raise ValueError("Successful DOI metadata lacks official API evidence: "+d)
            count+=1
            looked=now.isoformat()
            state="DOI_METADATA_VERIFIED" if response["status"]=="ok" else "API_UNAVAILABLE_RETRY_DUE_LATER"
        identity_result=identity(d,response.get("title",""))
        results.append({**item,"metadata":response,"looked_up_at":looked,
            "recovery_status":state,"public_identity":identity_result,
            "public_identity_index_fingerprint":fingerprint,
            "source_verification":"EXACT_DOI_API_METADATA_ONLY_NOT_WPO_PROJECT_PROOF",
            "scout_original_disposition_changed":False,
            "related_expansion_completed":False,
            "private_hub_import":"NOT_VERIFIED",
            "public_candidate_staged":False})
    return {**q,"records":results,"lookups_attempted":count,
        "metadata_recovered":sum(x["metadata"].get("status")=="ok" for x in results),
        "api_retry_or_pending":sum(x["metadata"].get("status")!="ok" for x in results),
        "verified_identity_snapshot":fingerprint,
        "last_check_at":now.isoformat(),
        "human_approvals":"NOT_VERIFIED","new_public_scout_proposals":0,
        "new_reach_additions":0}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--check-only",action="store_true")
    parser.add_argument("--max-new",type=int,default=10)
    a=parser.parse_args()
    result=queue() if a.check_only else run(max_new=a.max_new)
    if a.check_only:
        print(json.dumps({"queue":result["doi_queue_size"],"source_files":result["source_note_files_verified"]}))
        return
    dest=ROOT/OUT;dest.parent.mkdir(parents=True,exist_ok=True)
    body=json.dumps(result,indent=2,ensure_ascii=False)+"\n"
    if not dest.exists() or dest.read_text(encoding="utf-8")!=body:
        dest.write_text(body,encoding="utf-8")
    print(json.dumps({"queued":result["doi_queue_size"],"attempted":result["lookups_attempted"],
        "recovered":result["metadata_recovered"],"pending":result["api_retry_or_pending"]},indent=2))

if __name__=="__main__":main()
