#!/usr/bin/env python3
"""Turn public Scout research evidence into an operational, non-terminal queue.

All source notes stay immutable. A bounded hold is a completed *research pass*,
not a completed historical original, a completed expansion, a new candidate,
a private Hub card or a human decision. Unrecognized notes remain visible.
"""
import hashlib
import json
import re
from collections import Counter,defaultdict
from pathlib import Path

from decision_pipeline import norm_doi,norm_url

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"scout-operations/research-outcome-registry.json"
DIRS=("scout-operations/historical-crossref-phase2","scout-operations/monthly-research")
VERSION="reach-scout-all-lane-research-outcomes-v1"
HOLD="PROJECT_EVIDENCE_HOLD"
ACCESS="TECHNICAL_METADATA_RECOVERY"
HUMAN="BOUNDED_PROJECT_QUESTION_FOR_HUMAN"
PREPRINT="PREPRINT_MONTHLY_WATCH"
OTHER="EVIDENCE_RECORDED_CONTINUE_OR_VERIFY"

def sha(b):return hashlib.sha256(b).hexdigest()

def stable_decision(raw):
    code=str(raw or "").strip().upper()
    if not code:return OTHER
    if "PREPRINT" in code and ("HOLD" in code or "WATCH" in code):return PREPRINT
    if "ACCESS" in code or "TECHNICAL" in code or "METADATA_RETRY" in code:
        return ACCESS
    if "HUMAN" in code or "REVIEWER" in code or "HUMAN_PROJECT" in code:
        return HUMAN
    if any(x in code for x in ("DEFER","HOLD","PROJECT_SCOPE","ATTRIBUTION","FUNDING","CONTRADICT")):
        return HOLD
    return OTHER

def extract_sources(node):
    found=set()
    def rec(obj):
        if isinstance(obj,str):
            if obj.startswith("https://") and not re.search(r"\s",obj):
                found.add(obj)
        elif isinstance(obj,list):
            for x in obj:rec(x)
        elif isinstance(obj,dict):
            for k,v in obj.items():
                if k in {"url","source","evidence_url","publisher_url","official_ir_url",
                         "canonical_url","source_url","initial_source","distinct_source_followup",
                         "source_evidence","sources","evidence_urls","initial_research_sources",
                         "distinct_followup_sources","new_source_findings","research","followup_findings"}:
                    rec(v)
    rec(node)
    return sorted(found)

def node_ids(doc):
    """Only explicit structured output identifiers; never DOI regex on prose."""
    cases=doc.get("cases")
    if isinstance(cases,list):
        for case in cases:
            if isinstance(case,dict) and case.get("doi"):
                yield case["doi"],case,"case"
        return
    original=doc.get("original")
    if isinstance(original,dict) and original.get("doi"):
        yield original["doi"],original,"original"
        return
    for k in ("original_doi","doi","source_parent_original_doi","parent_original_doi"):
        if doc.get(k):
            yield doc[k],doc,"original" if k in ("original_doi","doi") else "seed"
            return
    identity=doc.get("identity")
    if isinstance(identity,dict) and identity.get("canonical_url"):
        yield identity["canonical_url"],doc,"code"

def source_decision(parent,node):
    # Specific nested case decision always outranks aggregate report text.
    return str(node.get("decision") or node.get("original",{}).get("decision")
               or parent.get("decision") or "")

def build(root=ROOT):
    events=[]
    unlinked=[]
    source_shas={}
    for directory in DIRS:
        base=root/directory
        if not base.is_dir():raise ValueError("Missing public research evidence directory: "+directory)
        for path in sorted(base.glob("20*.json")):
            relative=path.relative_to(root).as_posix()
            raw=path.read_bytes(); source_shas[relative]=sha(raw)
            doc=json.loads(raw)
            if not isinstance(doc,dict):raise ValueError("Non-object source note: "+relative)
            resolved=list(node_ids(doc))
            if not resolved:
                unlinked.append({"path":relative,"sha256":sha(raw),
                                 "reason":"NO_EXPLICIT_STRUCTURED_CASE_IDENTIFIER"})
            for raw_id,node,role in resolved:
                doi=norm_doi(raw_id)
                code_url=norm_url(raw_id) if not doi else ""
                if not doi and not code_url:
                    raise ValueError("Invalid research case identifier in "+relative)
                identity=("doi:"+doi) if doi else "url:"+code_url
                decision=source_decision(doc,node)
                explicit=stable_decision(decision)
                action=str(node.get("next_action") or doc.get("next_action") or "")
                if not action:
                    action="Source-specific research evidence needs the next bounded identity or project check"
                timestamp=str(doc.get("recorded_at") or doc.get("observed_at")
                    or doc.get("mission_local_time") or doc.get("mission_local")
                    or doc.get("observed_on") or path.name)
                # A named research lane is useful provenance, not eligibility.
                route=str(doc.get("lane") or doc.get("research_lane") or doc.get("origin")
                          or doc.get("case_type") or "SOURCE_LANE_UNCLASSIFIED")
                urls=sorted(set(extract_sources(node))|set(extract_sources(doc.get("sources",[])))
                            |set(extract_sources(doc.get("initial_research_sources",[])))
                            |set(extract_sources(doc.get("distinct_followup_sources",[]))))
                # Only an explicit human question with bounded sources can be
                # recommended for later human handoff; no auto feed publication.
                human_ready=explicit==HUMAN and len(urls)>=2 and bool(action.strip())
                event={"event_id":sha((relative+"\n"+identity+"\n"+sha(raw)).encode())[:24],
                    "identity":identity,"doi":doi or None,"url_only":code_url or None,
                    "role_in_note":role,"research_lane":route,
                    "source_path":relative,"source_sha256":sha(raw),
                    "source_time":timestamp,"raw_decision":decision or "NOT_DECLARED",
                    "operational_disposition":explicit,"next_action":action[:1200],
                    "checked_evidence_urls":urls,
                    "source_count":len(urls),
                    "bounded_human_question_to_verify":human_ready,
                    "formal_original_closed":False,"separate_expansion_closed":False,
                    "new_public_proposal":False,"private_hub_import":"NOT_VERIFIED",
                    "reviewer_approval":"NOT_VERIFIED"}
                events.append(event)
    # Group note history per public research identity without discarding
    # any source record or losing project-title vs historical provenance.
    grouped=defaultdict(list)
    for event in events:grouped[event["identity"]].append(event)
    entries=[]
    for identity,history in sorted(grouped.items()):
        history.sort(key=lambda e:(e["source_path"],e["event_id"]))
        latest=history[-1]
        # Preserve history of stronger deferral/human questions; a subsequent
        # generic evidence note must not erase an earlier bounded outcome.
        dispositions=sorted(set(e["operational_disposition"] for e in history))
        entries.append({"identity":identity,"latest_event_id":latest["event_id"],
            "latest_evidence_path":latest["source_path"],"latest_operational_disposition":latest["operational_disposition"],
            "observed_dispositions":dispositions,"source_file_count":len(set(e["source_path"] for e in history)),
            "event_ids":[e["event_id"] for e in history],
            "project_judgment_referral_possible":any(e["bounded_human_question_to_verify"] for e in history),
            "human_review_staged":False,"private_hub_import":"NOT_VERIFIED"})
    counts=dict(sorted(Counter(e["operational_disposition"] for e in events).items()))
    return {"schema":VERSION,"source_dirs":list(DIRS),
        "source_sha256":dict(sorted(source_shas.items())),
        "evidence_files_scanned":len(source_shas),
        "source_files_without_explicit_output_id":unlinked,
        "research_note_events":len(events),"distinct_research_identities":len(entries),
        "operational_disposition_counts":counts,
        "bounded_human_question_identities":sum(x["project_judgment_referral_possible"] for x in entries),
        "original_status_changes":0,"expansion_status_changes":0,
        "new_public_review_proposals":0,"private_hub_imports":"NOT_VERIFIED",
        "note":"Research outcome register only. A bounded research outcome is NOT formal original/expansion closure. Public/source evidence cannot attest private Hub decisions.",
        "events":events,"cases":entries}

def main():
    report=build()
    body=json.dumps(report,indent=2,ensure_ascii=False)+"\n"
    if not OUT.exists() or OUT.read_text(encoding="utf-8")!=body:
        OUT.write_text(body,encoding="utf-8")
    print(json.dumps({"files":report["evidence_files_scanned"],
                      "events":report["research_note_events"],
                      "identities":report["distinct_research_identities"],
                      "unlinked":len(report["source_files_without_explicit_output_id"]),
                      "dispositions":report["operational_disposition_counts"]},indent=2))

if __name__=="__main__":main()
