#!/usr/bin/env python3
"""Reconcile every historical DataCite DOI into a persistent Scout research queue.

This does not perform research and never marks entries completed automatically.
Read all immutable API batches; prevent dropped candidates and unjustified
terminal decisions. A change in historical-award relations reopens that relation.
"""
import csv
import datetime as dt
import hashlib
import io
import json
import re
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/"api-discoveries/historical/manifest.json"
LEDGER=ROOT/"scout-operations/historical-triage.json"
REPORT=ROOT/"scout-operations/historical-coverage.json"
DOI_RE=re.compile(r"10\.[0-9]{4,9}/[^\s]+",re.I)
BATCH_RE=re.compile(r"api-discoveries/historical/batches/[A-Za-z0-9_.-]+\.csv")
STATUS_PENDING={"awaiting_research","investigating","needs_more_research"}
STATUS_DONE={"already_in_reach","forwarded_to_hub","metadata_update_forwarded","no_action"}
STATUS_ALL=STATUS_PENDING|STATUS_DONE
REVIEW=ROOT/"scout-discoveries/manifest.json"

def split_awards(value):
    return {x.strip().upper() for x in re.split(r"\s*[,;]\s*",str(value or "")) if x.strip()}

def source_cases():
    manifest=json.loads(SOURCE.read_text(encoding="utf-8"))
    if manifest.get("schema")!="reach-historical-api-feed-v1":
        raise ValueError("Unexpected historical DataCite manifest schema")
    expected={}
    for batch in manifest.get("batches",[]):
        rel=batch["path"]
        if not BATCH_RE.fullmatch(rel):raise ValueError("Untrusted historical batch path "+rel)
        data=(ROOT/rel).read_bytes()
        if hashlib.sha256(data).hexdigest()!=batch["sha256"]:
            raise ValueError("Historical batch checksum mismatch "+rel)
        rows=list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"))))
        if len(rows)!=batch["record_count"]:raise ValueError("Historical batch row mismatch "+rel)
        for row in rows:
            doi=str(row.get("DOI") or "").strip().lower()
            if doi.startswith("https://doi.org/"):doi=doi[16:]
            if not DOI_RE.fullmatch(doi):raise ValueError("Missing or invalid DOI "+rel)
            key="doi:"+doi
            src=expected.setdefault(key,{"identity":key,"source_batch_ids":set(),"award_numbers":set(),"programs":set(),"source_evidence_urls":set()})
            src["source_batch_ids"].add(batch["id"])
            src["award_numbers"].update(split_awards(row.get("NOAA Award Number(s)")))
            src["programs"].update(split_awards(row.get("WPO Program")))
            url=str(row.get("Evidence URL") or "").strip()
            if url.startswith("https://"):src["source_evidence_urls"].add(url)
    if sum(b.get("record_count",0) for b in manifest["batches"])!=manifest["candidate_rows"]:
        raise ValueError("Historical manifest totals inconsistent")
    return manifest,expected

def verified_terminal(entry,reviewed_paths):
    if entry["status"] not in STATUS_DONE:return False
    notes=str(entry.get("research_notes",""))
    checked=entry.get("checked_sources") or []
    snapshot=str(entry.get("reach_snapshot") or "")
    basis=str(entry.get("funding_basis") or "")
    related=str(entry.get("related_outputs_checked") or "")
    verified_at=str(entry.get("verified_at") or "")
    if len(notes.strip())<25 or not checked or not all(str(u).startswith("https://") for u in checked):
        return False
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}",snapshot):
        return False
    if len(basis.strip())<12 or len(related.strip())<12 or not verified_at:
        return False
    if entry["status"]=="already_in_reach" and not entry.get("reach_match"):
        return False
    if entry["status"] in ("forwarded_to_hub","metadata_update_forwarded"):
        path=entry.get("scout_batch_path","")
        if path not in reviewed_paths:return False
    if entry["status"]=="no_action" and len(str(entry.get("no_action_reason","")).strip())<20:
        return False
    if sorted(entry.get("verified_awards",[]))!=sorted(entry.get("award_numbers",[])):
        return False
    return True

def reconcile():
    manifest,source=source_cases()
    existing=json.loads(LEDGER.read_text(encoding="utf-8"))
    if existing.get("schema")!="reach-scout-historical-triage-v1":
        raise ValueError("Unexpected Scout historical ledger schema")
    by_key={}
    for x in existing.get("entries",[]):
        key=x.get("identity")
        if key in by_key:raise ValueError("Duplicate historical ledger identity "+str(key))
        by_key[key]=x
    orphaned=set(by_key)-set(source)
    if orphaned:raise ValueError("Ledger references missing public input(s): "+str(sorted(orphaned)[:3]))
    reviewed_paths=set()
    if REVIEW.exists():
        review=json.loads(REVIEW.read_text(encoding="utf-8"))
        reviewed_paths={b["path"] for b in review.get("batches",[])}
    entries=[]
    for identity,src in sorted(source.items()):
        b=by_key.get(identity)
        if b is None:
            b={"identity":identity,"status":"awaiting_research",
               "first_seen_at":manifest["generated_at"],
               "updated_at":manifest["generated_at"],
               "research_notes":"","checked_sources":[],
               "reach_snapshot":"","funding_basis":"","related_outputs_checked":"",
               "verified_at":"","verified_awards":[]}
        if b.get("status") not in STATUS_ALL:
            raise ValueError("Unsupported historical disposition "+identity)
        original=set(b.get("award_numbers",[]))
        b["source_batch_ids"]=sorted(src["source_batch_ids"])
        b["award_numbers"]=sorted(src["award_numbers"])
        b["programs"]=sorted(src["programs"])
        b["source_evidence_urls"]=sorted(src["source_evidence_urls"])
        # New funding connections require fresh review; do not silently count
        # a previously closed DOI as fully examined for newly linked awards.
        if original and original!=set(b["award_numbers"]) and b["status"] in STATUS_DONE:
            b["status"]="needs_more_research"
            b["research_notes"]=str(b.get("research_notes",""))+"\nNew source award relationship requires verification."
        entries.append(b)
    counts=Counter()
    valid=[]
    problems=[]
    for entry in entries:
        status=entry["status"]
        if status in STATUS_DONE:
            if verified_terminal(entry,reviewed_paths):
                valid.append(entry);counts["completed"]+=1;counts[status]+=1
            else:
                problems.append(entry["identity"]+" declared "+status+" without required research proof")
        else:
            counts[status]+=1
    if problems:
        raise ValueError("Unsupported completed statuses; ledger not updated: "+"; ".join(problems[:6]))
    total=len(entries)
    progress={
        "schema":"reach-scout-historical-coverage-v1",
        "source_manifest": "api-discoveries/historical/manifest.json",
        "source_manifest_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "total_distinct_dois":total,
        "fully_investigated":counts["completed"],
        "remaining":total-counts["completed"],
        "awaiting_research":counts["awaiting_research"],
        "investigating":counts["investigating"],
        "needs_more_research":counts["needs_more_research"],
        "already_in_reach":counts["already_in_reach"],
        "forwarded_to_hub":counts["forwarded_to_hub"],
        "metadata_update_forwarded":counts["metadata_update_forwarded"],
        "no_action":counts["no_action"],
        "research_complete":bool(total and counts["completed"]==total),
        "note":"A completed status requires individual Scout evidence and REACH comparison; DataCite date enrichment alone does not close an item."
    }
    proposed={"schema":"reach-scout-historical-triage-v1",
        "repository":existing.get("repository","PART-WPO/reach-scout-discoveries"),
        "entries":entries}
    new_ledger=json.dumps(proposed,indent=2,ensure_ascii=False)+"\n"
    new_report=json.dumps(progress,indent=2,ensure_ascii=False)+"\n"
    if LEDGER.read_text(encoding="utf-8")!=new_ledger:LEDGER.write_text(new_ledger,encoding="utf-8")
    if not REPORT.exists() or REPORT.read_text(encoding="utf-8")!=new_report:
        REPORT.write_text(new_report,encoding="utf-8")
    print(json.dumps(progress,indent=2))
    return progress

if __name__=="__main__":reconcile()
