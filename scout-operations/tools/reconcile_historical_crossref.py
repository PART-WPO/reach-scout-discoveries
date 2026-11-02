#!/usr/bin/env python3
"""Persistent historical Crossref DOI/expansion queue. Ingestion != investigation.

Copies only source-backed identity hints from other queues; never transfers a
completion, human decision, or assumed REACH publication.
"""
import csv,hashlib,io,json,re
from collections import Counter,defaultdict
from pathlib import Path
from reconcile_historical import verified_terminal

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/"api-discoveries/historical-crossref/manifest.json"
LEDGER=ROOT/"scout-operations/historical-crossref-triage.json"
COVERAGE=ROOT/"scout-operations/historical-crossref-coverage.json"
REVIEW=ROOT/"scout-discoveries/manifest.json"
OPEN={"awaiting_research","investigating","needs_more_research"}
DONE={"already_in_reach","forwarded_to_hub","metadata_update_forwarded","no_action","human_metadata_needed"}
SEED_OPEN={"awaiting_exploration","investigating","needs_more_research"}
SEED_DONE={"complete","not_applicable"}

def canonical(value):
    d=str(value or "").strip().lower()
    d=re.sub(r"^https?://(?:dx\.)?doi\.org/","",d)
    return "doi:"+d if re.fullmatch(r"10\.\d{4,9}/[^\s]+",d) else ""

def read(rel):
    path=ROOT/rel
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}

def cases():
    manifest=json.loads(SOURCE.read_text(encoding="utf-8"))
    if manifest.get("schema")!="reach-historical-crossref-feed-v1":
        raise ValueError("Wrong historical Crossref manifest schema")
    cases={}
    count=0
    for batch in manifest.get("batches",[]):
        rel=batch["path"]
        if not re.fullmatch(r"api-discoveries/historical-crossref/batches/[\w.-]+\.csv",rel):
            raise ValueError("Unexpected batch path "+rel)
        blob=(ROOT/rel).read_bytes()
        if hashlib.sha256(blob).hexdigest()!=batch["sha256"]:
            raise ValueError("Crossref batch SHA mismatch "+rel)
        rows=list(csv.DictReader(io.StringIO(blob.decode("utf-8-sig"))))
        if len(rows)!=batch["record_count"]:
            raise ValueError("Crossref batch row-count mismatch "+rel)
        count+=len(rows)
        for row in rows:
            key=canonical(row.get("DOI"))
            if not key:raise ValueError("Invalid Crossref DOI in "+rel)
            d=cases.setdefault(key,{"identity":key,"award_numbers":set(),
                "source_batch_ids":set(),"source_evidence_urls":set(),
                "titles":set()})
            d["source_batch_ids"].add(batch["id"])
            d["award_numbers"].update(x.strip().upper() for x in
                (row.get("NOAA Award Number(s)") or "").split(",") if x.strip())
            if row.get("Evidence URL","").startswith("https://"):
                d["source_evidence_urls"].add(row["Evidence URL"])
            if row.get("Title"):d["titles"].add(row["Title"])
    if count!=manifest["candidate_rows"]:
        raise ValueError("Crossref source manifest incomplete")
    return manifest,cases

def verified_seed(e):
    if e.get("seed_expansion_status")=="not_applicable":
        return len(str(e.get("seed_not_applicable_reason","")).strip())>=25 and bool(e.get("checked_sources"))
    if e.get("seed_expansion_status")!="complete":return False
    return bool(e.get("seed_checked_sources")) and all(
        str(u).startswith("https://") for u in e["seed_checked_sources"]) and (
        len(str(e.get("seed_research_notes","")).strip())>=25
    )

def run():
    manifest,source=cases()
    prior=read("scout-operations/historical-crossref-triage.json")
    if prior and prior.get("schema")!="reach-scout-historical-crossref-triage-v1":
        raise ValueError("Unknown historical Crossref checkpoint")
    existing={}
    for e in prior.get("entries",[]):
        if e["identity"] in existing:raise ValueError("Duplicate ledger DOI")
        existing[e["identity"]]=e
    if set(existing)-set(source):
        raise ValueError("Existing historical Crossref history cannot disappear")
    other={}
    for path in ("scout-operations/historical-triage.json",
                 "scout-operations/monthly-triage.json"):
        for e in read(path).get("entries",[]):
            key=canonical(str(e.get("identity","")).removeprefix("doi:"))
            if key:other.setdefault(key,[]).append({
                "queue":Path(path).name,"status_at_crossref_intake":e.get("status",""),
                "source_identity":e.get("identity","")})
    reviewed=set()
    for batch in read("scout-discoveries/manifest.json").get("batches",[]):
        rel=batch.get("path","")
        if re.fullmatch(r"scout-discoveries/batches/[\w.-]+\.csv",rel):
            blob=(ROOT/rel).read_bytes()
            if hashlib.sha256(blob).hexdigest()!=batch["sha256"]:raise ValueError("Scout manifest checksum mismatch")
            for row in csv.DictReader(io.StringIO(blob.decode("utf-8-sig"))):
                key=canonical(row.get("DOI"))
                if key:reviewed.add(key)
    reviewed_paths={x["path"] for x in read("scout-discoveries/manifest.json").get("batches",[])}
    entries=[];stats=Counter()
    for key,found in sorted(source.items()):
        entry=existing.get(key)
        if entry is None:
            entry={"identity":key,"status":"awaiting_research",
              "seed_expansion_status":"awaiting_exploration",
              "first_seen_at":manifest["generated_at"],
              "updated_at":manifest["generated_at"],
              "research_notes":"","checked_sources":[],"reach_snapshot":"",
              "funding_basis":"","related_outputs_checked":"",
              "verified_at":"","verified_awards":[],"seed_checked_sources":[],
              "seed_research_notes":"","source_overlap_hints":other.get(key,[]),
              "present_in_published_scout_feed_at_intake":key in reviewed}
        if entry.get("status") not in OPEN|DONE:raise ValueError("Invalid Crossref research status "+key)
        if entry.get("seed_expansion_status") not in SEED_OPEN|SEED_DONE:
            raise ValueError("Invalid Crossref seed research status "+key)
        awards=sorted(found["award_numbers"])
        if entry.get("award_numbers") and entry["award_numbers"]!=awards and entry["status"] in DONE:
            entry["status"]="needs_more_research"
            entry["research_notes"]+="\nNew primary-award association requires fresh verification."
        entry["award_numbers"]=awards
        entry["source_batch_ids"]=sorted(found["source_batch_ids"])
        entry["source_evidence_urls"]=sorted(found["source_evidence_urls"])
        entry["titles"]=sorted(found["titles"])
        if entry["status"] in DONE and not verified_terminal(entry,reviewed_paths):
            raise ValueError("Unsupported unverified terminal Crossref status "+key)
        orig_ok=entry["status"] in DONE
        seed_ok=verified_seed(entry)
        stats["originals_completed"]+=int(orig_ok)
        stats["seed_expansions_completed"]+=int(seed_ok)
        stats["fully_researched"]+=int(orig_ok and seed_ok)
        stats[entry["status"]]+=1
        stats["seed_"+entry["seed_expansion_status"]]+=1
        stats["found_in_other_scout_queue"]+=int(bool(entry.get("source_overlap_hints")))
        stats["found_in_published_scout_feed_at_intake"]+=int(bool(entry.get("present_in_published_scout_feed_at_intake")))
        entries.append(entry)
    count=len(entries)
    ledger={"schema":"reach-scout-historical-crossref-triage-v1",
            "repository":"PART-WPO/reach-scout-discoveries",
            "entries":entries}
    report={"schema":"reach-scout-historical-crossref-coverage-v1",
            "source_manifest":"api-discoveries/historical-crossref/manifest.json",
            "source_manifest_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            "total_distinct_dois":count,"fully_investigated":stats["fully_researched"],
            "remaining":count-stats["fully_researched"],
            "originals_completed":stats["originals_completed"],
            "seed_expansions_completed":stats["seed_expansions_completed"],
            "awaiting_research":stats["awaiting_research"],
            "investigating":stats["investigating"],
            "needs_more_research":stats["needs_more_research"],
            "already_in_reach":stats["already_in_reach"],
            "forwarded_to_hub":stats["forwarded_to_hub"],
            "metadata_update_forwarded":stats["metadata_update_forwarded"],
            "no_action":stats["no_action"],
            "human_metadata_needed":stats["human_metadata_needed"],
            "seed_expansion_pending":count-stats["seed_expansions_completed"],
            "found_in_other_scout_queue_at_intake":stats["found_in_other_scout_queue"],
            "found_in_published_scout_feed_at_intake":stats["found_in_published_scout_feed_at_intake"],
            "research_complete":count>0 and stats["fully_researched"]==count,
            "note":"Cross-queue flags are hints only. REACH dedup and related-output expansion both require independent evidence. Even a confirmed existing publication remains a valid expansion seed."}
    for path,obj in ((LEDGER,ledger),(COVERAGE,report)):
        path.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))

if __name__=="__main__":run()
