#!/usr/bin/env python3
"""Historical Crossref primary-SPARK-award harvest, intentionally separate from monthly and DataCite.

Actions scan creates one auditable JSON per shard; publish verifies all eight shards,
then saves immutable research-only 24-column batches. No REACH/Hub writes or approval.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from collections import Counter, defaultdict
from pathlib import Path

from harvest import spark_awards, fetch, match_crossref, to_candidate
from publish_harvest import merge_record, output_row, batches, immutable_file

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"api-discoveries/historical-crossref"
SELECT="DOI,title,author,published-online,published-print,published,issued,posted,created,funder,type,abstract,URL,relation"
def crossref_award(award,max_pages=30):
    cursor="*"
    found=[]
    for page_i in range(max_pages):
        message=(fetch("https://api.crossref.org/works",params={
            "filter":"award.number:"+award,"rows":100,"cursor":cursor,"select":SELECT
        }).get("message") or {})
        page=message.get("items") or []
        found.extend(x for x in page if match_crossref(x,award))
        if len(page)<100:
            return found
        nxt=message.get("next-cursor")
        if not nxt or nxt==cursor:
            raise RuntimeError("Crossref pagination cursor stalled for "+award)
        cursor=nxt
    raise RuntimeError("Crossref pagination ceiling for "+award+"; never treat incomplete retrieval as zero")

def scan(args):
    import time
    awards,source_sha=spark_awards()
    selected=[x for i,x in enumerate(awards) if i%args.shards==args.shard]
    attempted=[];failed=[];records=[]
    for entry in selected:
        award=entry["award"];attempted.append(award)
        try:
            for work in crossref_award(award,args.max_pages):
                rec=to_candidate(work,"crossref",award,"historical","")
                if rec:
                    rec["programs"]=entry["programs"]
                    rec["projects"]=entry["projects"]
                    records.append(rec)
        except Exception as exc:
            failed.append({"award":award,"error":str(exc)[:250]})
        time.sleep(0.5)
    dest=Path(args.output);dest.mkdir(parents=True,exist_ok=True)
    filename=dest/("historical-crossref-shard%02d.json"%args.shard)
    filename.write_text(json.dumps({
        "schema":"reach-historical-crossref-shard-v1","source":"crossref",
        "shard":args.shard,"shards":args.shards,"total_awards":len(awards),
        "spark_source_sha256":source_sha,"attempted_awards":attempted,
        "failures":failed,"records":records
    },ensure_ascii=False),encoding="utf-8")
    print("Historical Crossref shard",args.shard,"awards",len(attempted),
          "matched records",len(records),"failures",len(failed),flush=True)
    if failed:raise SystemExit(2)

def publish(args):
    sources=[Path(args.output)/("historical-crossref-shard%02d.json"%i) for i in range(args.shards)]
    if any(not x.exists() for x in sources):
        raise RuntimeError("Missing Crossref shard(s): "+str([x.name for x in sources if not x.exists()]))
    shards=[json.loads(p.read_text(encoding="utf-8")) for p in sources]
    keys={(x["total_awards"],x["spark_source_sha256"],x["shards"]) for x in shards}
    if len(keys)!=1:raise RuntimeError("Inconsistent SPARK snapshots or shard counts")
    total,source_sha,nshards=keys.pop()
    if nshards!=args.shards:raise RuntimeError("Inconsistent shard count")
    attempted=[];all_found=[]
    for i,shard in enumerate(shards):
        if shard.get("schema")!="reach-historical-crossref-shard-v1" or shard["shard"]!=i:
            raise RuntimeError("Invalid Crossref shard identity")
        if shard.get("failures"):raise RuntimeError("Crossref shard failure must not be published")
        attempted.extend(shard["attempted_awards"])
        all_found.extend(shard["records"])
    if len(attempted)!=total or len(set(attempted))!=total:
        raise RuntimeError("Partial or overlapping Crossref award coverage")
    grouped=defaultdict(list)
    for rec in all_found:
        doi=str(rec.get("doi") or "").strip().lower()
        if not doi.startswith("10.") or not match_candidate_award(rec,attempted):
            raise RuntimeError("Invalid Crossref DOI/award evidence")
        grouped[doi].append(rec)
    merged=[merge_record(grouped[k]) for k in sorted(grouped)]
    day=dt.datetime.now(dt.timezone.utc).date().isoformat()
    run_id="REACH-HISTORICAL-CROSSREF-"+str(args.run_id)
    suffix=str(args.run_id)
    output_rows=[]
    for item in merged:
        row=output_row(item,"historical","",run_id)
        row["Scout Discovery Rationale"]="\n".join([
          "Intake origin: Historical Crossref API Backfill",
          "Historical coverage: All SPARK primary award identifiers",
          "API provenance: Crossref structured funder award",
          "API publication status: "+("Preprint" if item.get("is_preprint") else "Not identified as preprint by source"),
          "API funding basis: Exact award match within Crossref funder.award metadata",
          "Pub date basis: "+", ".join(item["date_bases"]),
          "Scout verification: Not started",
          "Research-only DOI seed; check complete REACH and Scout queues before proposing.",
          "Even if already in REACH or Scout queue, retain as a seed for independent related-output exploration."
        ])
        output_rows.append(row)
    dest=OUT/"batches"
    paths=batches(output_rows,dest,day+"-historical-crossref-spark-primary-"+suffix,run_id)
    manifest=OUT/"manifest.json"
    old=json.loads(manifest.read_text(encoding="utf-8")) if manifest.exists() else {}
    if old and old.get("schema")!="reach-historical-crossref-feed-v1":
        raise RuntimeError("Historical Crossref manifest schema mismatch")
    all_batches={x["id"]:x for x in old.get("batches",[])}
    for batch in paths:
        prior=all_batches.get(batch["id"])
        if prior and prior!=batch:raise RuntimeError("Immutable Crossref batch conflict")
        all_batches[batch["id"]]=batch
    result={"schema":"reach-historical-crossref-feed-v1",
      "repository":"PART-WPO/reach-scout-discoveries",
      "generated_at":dt.datetime.now(dt.timezone.utc).isoformat(),
      "source":"Crossref","scope":"SPARK primary award numbers, all available years",
      "spark_source_sha256":source_sha,"awards_checked_per_complete_run":total,
      "batches":[all_batches[k] for k in sorted(all_batches)],
      "candidate_rows":sum(x["record_count"] for x in all_batches.values()),
      "batch_count":len(all_batches),
      "policy":"Research-only historical Crossref leads, keep duplicates as expansion seeds; never auto-stage in Hub"}
    manifest.parent.mkdir(parents=True,exist_ok=True)
    manifest.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    summary={"run":run_id,"matched_award_output_pairs":len(all_found),
      "distinct_dois_in_run":len(merged),"awards_checked":total,
      "Crossref_api_errors":0,"manifest_batch_count":len(all_batches),
      "state":"API harvest only; Scout research and private Hub import NOT VERIFIED"}
    archive=ROOT/"api-discoveries/runs"/("historical-crossref-"+suffix+".json")
    immutable_file(archive,(json.dumps(summary,indent=2)+"\n").encode("utf-8"))
    print(json.dumps(summary,indent=2))

def match_candidate_award(rec,attempted):
    return str(rec.get("award") or "").upper() in set(attempted) and str(rec.get("src"))=="crossref"

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("stage",choices=["scan","publish"])
    ap.add_argument("--shards",type=int,default=8)
    ap.add_argument("--shard",type=int,default=0)
    ap.add_argument("--max-pages",type=int,default=30)
    ap.add_argument("--output",default="api-discoveries/tmp")
    ap.add_argument("--run-id",default=os.environ.get("GITHUB_RUN_ID","manual"))
    args=ap.parse_args()
    if args.shards<1 or not 0<=args.shard<args.shards:raise ValueError("Bad shard")
    scan(args) if args.stage=="scan" else publish(args)
