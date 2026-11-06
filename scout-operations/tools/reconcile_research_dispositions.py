#!/usr/bin/env python3
"""Reconcile heterogeneous Scout research notes into explicit, traceable work units.

A research disposition is not a formal historical terminal status, human Hub
import, new Scout candidate, approved funding, or expansion completion.
Every eligible research note receives a SHA-backed identity or an explicit
unlinked evidence exception. Previously approved/rejected items are untouched.
"""
import hashlib
import json
import re
from collections import defaultdict, Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUTPUT="scout-operations/research-case-dispositions.json"
LANES=("scout-operations/historical-crossref-phase2",
       "scout-operations/monthly-research")
DOI_RE=re.compile(r"^10\.\d{4,9}/\S+$",re.I)
CODE_RE=re.compile(r"^https://github\.com/[^/\s]+/[^/\s]+/?$",re.I)
DECISIONS=("PREPRINT_WATCHLIST","REACH_IDENTITY_VERIFICATION",
           "PROJECT_SCOPE_EVIDENCE_HOLD","METADATA_ACCESS_RETRY",
           "BOUNDED_HUMAN_PROJECT_QUESTION","CONTINUE_TARGETED_RESEARCH",
           "REVIEW_SOURCE_IDENTITY")
LAST_ACTIONS={
 "PREPRINT_WATCHLIST":"Monthly official journal-version watchlist; never stage original preprint DOI.",
 "REACH_IDENTITY_VERIFICATION":"Check current SHA-verified REACH, published Scout, inbox, canonical NOAA IR URL and versions.",
 "PROJECT_SCOPE_EVIDENCE_HOLD":"Reopen only with exact SPARK primary award and same-project evidence; no automatic rejection.",
 "METADATA_ACCESS_RETRY":"Use the official exact-DOI metadata checkpoint; do not declare an absent abstract/date.",
 "BOUNDED_HUMAN_PROJECT_QUESTION":"Prepare focused reviewer question, but verify current public identity before any private import.",
 "CONTINUE_TARGETED_RESEARCH":"Collect one truly distinct, project-specific source within bounded research budget.",
 "REVIEW_SOURCE_IDENTITY":"Research note lacks one safe original identity; manually reconcile source without loss."
}

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def doi(x):
    s=str(x or "").strip().lower()
    if s.startswith("doi:"):s=s[4:]
    if s.startswith("https://doi.org/"):s=s[16:]
    return s if DOI_RE.fullmatch(s) else None
def code(x):
    s=str(x or "").strip()
    return s.rstrip("/").lower() if CODE_RE.fullmatch(s) else None
def read(root,rel):return json.loads((root/rel).read_text(encoding="utf-8"))
def safe_path(root,path):
    r=(root/path).resolve()
    if not r.is_relative_to(root.resolve()) or not r.is_file():raise ValueError("Missing or unsafe research source "+str(path))
    return r

def cases_for_note(obj):
    # Multi-output source cases must retain their individual identities.
    if isinstance(obj.get("cases"),list) and obj["cases"]:
        return [x for x in obj["cases"] if isinstance(x,dict)]
    return [obj]

def identify(obj,parent):
    for k in ("doi","original_doi","parent_original_doi","source_parent_original_doi"):
        v=doi(obj.get(k))
        if v:return ("doi:"+v,v)
    inner=obj.get("original")
    if isinstance(inner,dict) and doi(inner.get("doi")):
        v=doi(inner["doi"]);return ("doi:"+v,v)
    identity=obj.get("identity")
    if isinstance(identity,dict):
        v=doi(identity.get("doi"))
        if v:return ("doi:"+v,v)
        v=code(identity.get("canonical_url"))
        if v:return ("code:"+v,None)
    if isinstance(identity,str) and doi(identity):
        v=doi(identity);return ("doi:"+v,v)
    # Never attach child DOI data to unrelated parent merely from a prose title.
    if obj is not parent:
        v=doi(parent.get("original_doi"))
        if v:return ("doi:"+v,v)
    return (None,None)

def explicit_text(x):
    # Only structured decision fields; NEVER draw a completion decision from
    # free-text mentions of publication, funding or review.
    vals=[]
    for k in ("decision","original_publication_status","publication_status",
              "source_award_status","same_project_wpo_funding","funding",
              "public_identity","identity","workflow_blocker"):
        v=x.get(k)
        if isinstance(v,str):vals.append(v.upper())
        elif isinstance(v,dict):
            vals.extend(str(v.get(z,"")).upper() for z in
                        ("status","decision","reason","same_project_wpo_attribution",
                         "same_project_award_verified"))
    return " | ".join(vals)

def disposition(doc,parent):
    t=explicit_text(doc)+" | "+explicit_text(parent)
    if "PREPRINT_HOLD" in t or "HOLD_PREPRINT" in t or "PREPRINT_ONLY" in t:
        return "PREPRINT_WATCHLIST"
    if "ACCESS_FAIL" in t or "TECHNICAL_HOLD" in t or "ACCESS_FAILURE" in t:
        return "METADATA_ACCESS_RETRY"
    if "BOUNDED_RESEARCH_COMPLETE_NEEDS_HUMAN" in t:
        return "BOUNDED_HUMAN_PROJECT_QUESTION"
    if ("NO_PUBLIC_IDENTITY_MATCH" in t and
        "NOT_REVALIDATED" in t) or "REACH_IDENTITY" in t:
        return "REACH_IDENTITY_VERIFICATION"
    if any(z in t for z in ("SCOPE","FUNDING","AWARD","ATTRIBUTION","DEFER","HOLD","CONTRADICT")):
        return "PROJECT_SCOPE_EVIDENCE_HOLD"
    return "CONTINUE_TARGETED_RESEARCH"

def build(root=ROOT):
    grouped=defaultdict(list);unlinked=[];files=[]
    for folder in LANES:
        for p in sorted((root/folder).glob("20*.json")):
            rel=p.relative_to(root).as_posix()
            source=read(root,rel)
            if not isinstance(source,dict):raise ValueError("Research source must be a JSON object: "+rel)
            files.append({"path":rel,"sha256":digest(p)})
            units=cases_for_note(source)
            if isinstance(source.get("cases"),list) and any(not isinstance(x,dict) for x in source["cases"]):
                raise ValueError("Non-object nested research case: "+rel)
            linked=False
            for unit in units:
                key,d=identify(unit,source)
                if not key:continue
                linked=True
                group=("monthly_research" if folder.endswith("monthly-research")
                       else "historical_crossref_and_supplemental")
                grouped[(group,key)].append({"source_path":rel,"source_sha256":digest(p),
                    "doi":d,"case":unit,"parent":source})
            if not linked:unlinked.append({"path":rel,"sha256":digest(p),
                "reason":"NO_SAFE_EXPLICIT_DOI_OR_CANONICAL_CODE_IDENTITY"})
    rows=[]
    for (group,key),notes in sorted(grouped.items()):
        outcomes=[disposition(n["case"],n["parent"]) for n in notes]
        # Priority chooses next safe action, not strongest-sounding terminal claim.
        if "PREPRINT_WATCHLIST" in outcomes:state="PREPRINT_WATCHLIST"
        elif "METADATA_ACCESS_RETRY" in outcomes:state="METADATA_ACCESS_RETRY"
        elif "BOUNDED_HUMAN_PROJECT_QUESTION" in outcomes:state="BOUNDED_HUMAN_PROJECT_QUESTION"
        elif "REACH_IDENTITY_VERIFICATION" in outcomes:state="REACH_IDENTITY_VERIFICATION"
        elif "PROJECT_SCOPE_EVIDENCE_HOLD" in outcomes:state="PROJECT_SCOPE_EVIDENCE_HOLD"
        else:state="CONTINUE_TARGETED_RESEARCH"
        evidence=sorted({(n["source_path"],n["source_sha256"]) for n in notes})
        rows.append({"identity":key,"doi":notes[0]["doi"],"lane":group,
           "research_note_count":len(notes),
           "source_evidence":[{"path":p,"sha256":h} for p,h in evidence],
           "evidence_dispositions":sorted(set(outcomes)),
           "operational_disposition":state,
           "next_action":LAST_ACTIONS[state],
           "research_completed_in_original_ledger":False,
           "expansion_closed":False,"human_review_import":"NOT_VERIFIED",
           "human_approval":"NOT_VERIFIED","scout_proposal_staged":False,
           "needs_current_reach_identity_before_handoff":True})
    counts=Counter(x["operational_disposition"] for x in rows)
    return {"schema":"reach-scout-explicit-research-dispositions-v1",
      "source_files_scanned":len(files),
      "source_file_sha256":files,"identities_with_case_dispositions":len(rows),
      "operational_counts":dict(sorted(counts.items())),
      "unlinked_source_evidence":unlinked,
      "unlinked_source_count":len(unlinked),
      "records":rows,
      "private_review_import":"NOT_VERIFIED",
      "automatic_status_changes":0,
      "note":"Every research source accounted for; disposition drives next operation, not actual completed original or expansion. Human questions are gated by current identity and privacy-safe reviewer review."}

def main():
    report=build()
    path=ROOT/OUTPUT
    data=json.dumps(report,indent=2,ensure_ascii=False)+"\n"
    if not path.exists() or path.read_text(encoding="utf-8")!=data:
        path.write_text(data,encoding="utf-8")
    print(json.dumps({k:report[k] for k in ("source_files_scanned","identities_with_case_dispositions","operational_counts","unlinked_source_count")},indent=2))

if __name__=="__main__":main()
