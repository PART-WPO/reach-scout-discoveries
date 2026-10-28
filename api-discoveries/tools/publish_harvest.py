#!/usr/bin/env python3
"""Publish completed API harvest as immutable, UNREVIEWED Scout research inputs.
Never send raw API results directly to the Discovery Hub or modify source systems.
"""
import argparse,csv,datetime as dt,hashlib,io,json,os,re,subprocess,sys
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
FIELDS=[
 "Candidate ID","Title","DOI","Output URL","Output Type","NOAA Award Number(s)",
 "WPO Program","Proposed Project Title","Suggested Parent Project",
 "Authors / PI","Principal Investigators","Principal Investigator Email(s)",
 "Publication Date","Brief Abstract","IR?","IR Status","IR Pub Date",
 "IR Repository URL","Evidence URL","Funding Evidence URL",
 "Scout Discovery Rationale","Existing REACH Match","Scout Confidence","Source Run ID"
]
def merge_record(records):
    records=sorted(records,key=lambda x: (x["src"]!="datacite",not bool(x.get("date"))))
    x=records[0].copy()
    for r in records[1:]:
        if not x.get("date") and r.get("date"):x["date"]=r["date"];x["date_basis"]=r.get("date_basis","")
        if x["title"].startswith("Provisional ") and not r["title"].startswith("Provisional "):x["title"]=r["title"]
        if not x.get("authors"):x["authors"]=r.get("authors",[])
        if not x.get("abstract"):x["abstract"]=r.get("abstract","")
        if x.get("outtype")=="4" and r.get("outtype")!="4":x["outtype"]=r["outtype"]
    x["awards"]=sorted(set(r["award"] for r in records))
    x["programs"]=sorted(set(p for r in records for p in r.get("programs",[])))
    x["projects"]=sorted(set(p for r in records for p in r.get("projects",[])))
    x["sources"]=sorted(set(r["src"] for r in records))
    x["evidence_urls"]=sorted(set(r["evidence"] for r in records))
    x["date_bases"]=sorted(set(r["date_basis"] for r in records))
    return x
def output_row(x,mode,month,run):
    doi=x["doi"]
    canonical="https://doi.org/"+doi
    sources=", ".join(x["sources"])
    if mode=="monthly":
        reason="\n".join([
            "Intake origin: Monthly API",
            "Monthly intake: "+month,
            "API provenance: "+sources,
            "API date basis: "+", ".join(x["date_bases"]),
            "API funding basis: Exact structured award number(s) in API funding metadata.",
            "Scout verification: Not started",
            "API candidate only; Scout must verify against full REACH and investigate connected outputs before human review."
        ])
    else:
        reason="\n".join([
            "Intake origin: Historical DataCite API Backfill",
            "Historical coverage: All SPARK award identifiers",
            "API provenance: "+sources,
            "API funding basis: Exact structured award number(s) in DataCite fundingReferences.",
            "Scout verification: Not started",
            "Historical API candidate only; Scout must check full REACH and relevant supporting evidence before human review."
        ])
    return {
      "Candidate ID":"","Title":x["title"],"DOI":doi,"Output URL":canonical,
      "Output Type":x["outtype"],"NOAA Award Number(s)":", ".join(x["awards"]),
      "WPO Program":", ".join(x["programs"]),
      "Proposed Project Title":(x["projects"][0] if len(x["projects"])==1 else ""),
      "Suggested Parent Project":(x["projects"][0] if len(x["projects"])==1 else ""),
      "Authors / PI":"; ".join(x["authors"][:12]),"Principal Investigators":"",
      "Principal Investigator Email(s)":"","Publication Date":x["date"],
      "Brief Abstract":x.get("abstract",""),"IR?":"","IR Status":"",
      "IR Pub Date":"","IR Repository URL":"","Evidence URL":x["evidence_urls"][0],
      "Funding Evidence URL":x["evidence_urls"][0],
      "Scout Discovery Rationale":reason,"Existing REACH Match":"Unchecked",
      "Scout Confidence":"","Source Run ID":run
    }
def csv_content(rows):
    buf=io.StringIO(newline="")
    w=csv.DictWriter(buf,fieldnames=FIELDS,lineterminator="\r\n")
    w.writeheader();w.writerows(rows)
    return buf.getvalue().encode("utf-8")
def immutable_file(path,data):
    if path.exists():
        if path.read_bytes()!=data:raise RuntimeError("Immutable harvest already exists with different contents: "+str(path))
        return False
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(data)
    return True
def batches(rows,root,base,run):
    result=[]
    chunks=[]
    for x in rows:
        if not chunks:chunks.append([])
        candidate=chunks[-1]+[x]
        if len(candidate)>100 or len(csv_content(candidate))>1500000:
            chunks.append([x])
        else:chunks[-1]=candidate
    for i,chunk in enumerate(chunks,1):
        if not chunk:continue
        name=f"{base}-part{i:03d}.csv"
        path=root/name;data=csv_content(chunk)
        if len(data)>1900000:raise ValueError("Batch too large")
        immutable_file(path,data)
        rel=path.relative_to(ROOT).as_posix()
        result.append({"id":path.stem,"path":rel,"sha256":hashlib.sha256(data).hexdigest(),
            "record_count":len(chunk),"source_run_ids":[run]})
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--mode",choices=["monthly","historical"],required=True)
    p.add_argument("--month",default="")
    p.add_argument("--input",default="api-discoveries/tmp")
    p.add_argument("--shards",type=int,default=8)
    args=p.parse_args()
    if args.mode=="monthly" and not args.month:
        first=dt.datetime.now(dt.timezone.utc).date().replace(day=1)
        args.month=(first-dt.timedelta(days=1)).strftime("%Y-%m")
    parts=sorted(Path(args.input).glob(args.mode+"-*-shard*.json"))
    sources=["datacite","crossref"] if args.mode=="monthly" else ["datacite"]
    expected={f"{args.mode}-{source}-shard{shard:02d}.json" for source in sources for shard in range(args.shards)}
    if {p.name for p in parts}!=expected:
        raise RuntimeError(f"Missing or extra harvest shard artifacts: missing={sorted(expected-{p.name for p in parts})}")
    pieces=[json.loads(f.read_text()) for f in parts]
    metas={(x["total_awards"],x["source_sha"]) for x in pieces}
    if len(metas)!=1:raise RuntimeError("SPARK snapshot mismatch between shards")
    award_total,source_sha=metas.pop()
    all_found=[]
    for source in sources:
        attempted=[]
        for x in pieces:
            if x["source"]!=source:continue
            if x.get("failures"):raise RuntimeError("API errors in shard "+str(x["shard"])+": "+json.dumps(x["failures"][:3]))
            if args.mode=="monthly" and x["month"]!=args.month:raise RuntimeError("Monthly window mismatch")
            attempted.extend(x["attempted_awards"])
            all_found.extend(x["records"])
        if len(attempted)!=award_total or len(set(attempted))!=award_total:
            raise RuntimeError("Incomplete award coverage for "+source)
    mapped=defaultdict(list)
    for x in all_found:
        key=x["doi"].lower().strip()
        if not re.match(r"^10\.\d{4,9}/",key):raise ValueError("Bad DOI in candidate")
        mapped[key].append(x)
    merged=[merge_record(records) for key,records in sorted(mapped.items())]
    now=dt.datetime.now(dt.timezone.utc).date()
    if args.mode=="monthly":
        first=dt.date.fromisoformat(args.month+"-01")
        release=dt.date(first.year+1,1,1) if first.month==12 else dt.date(first.year,first.month+1,1)
        run=f"REACH-MONTHLY-API-{args.month}"
        out=ROOT/"api-discoveries/batches"
        base=f"{release.isoformat()}-monthly-api-{args.month}"
    else:
        run="REACH-HISTORICAL-DATACITE-"+now.isoformat()
        out=ROOT/"api-discoveries/historical/batches"
        base=f"{now.isoformat()}-historical-datacite-spark-all"
    rows=[output_row(x,args.mode,args.month,run) for x in merged]
    info=batches(rows,out,base,run)
    summary={"mode":args.mode,"cohort":args.month if args.mode=="monthly" else "all-years",
        "run":run,"SPARK_source_sha256":source_sha,"unique_awards_checked_per_api":award_total,
        "source_apis":sources,"matched_award_output_pairs":len(all_found),
        "distinct_dois":len(merged),"batch_count":len(info),
        "publication_dates_verified_exact":sum(bool(x["date"]) for x in merged),
        "publication_date_requires_research":sum(not bool(x["date"]) for x in merged),
        "type_counts":dict(Counter(x["outtype"] for x in merged)),
        "status":"completed_API_research_input_only_not_Scout_reviewed_not_REACH_published"}
    run_tag=("monthly-"+args.month) if args.mode=="monthly" else "historical-datacite-"+now.isoformat()
    path=ROOT/"api-discoveries/runs"/(run_tag+".json")
    immutable_file(path,(json.dumps(summary,indent=2,sort_keys=True)+"\n").encode("utf-8"))
    if args.mode=="monthly":
        # Regenerate existing manifest in THIS job: GITHUB_TOKEN pushes don't
        # trigger separate push-based workflows.
        subprocess.run([sys.executable,str(ROOT/"api-discoveries/tools/build_manifest.py")],check=True)
    else:
        manifest=ROOT/"api-discoveries/historical/manifest.json"
        old=json.loads(manifest.read_text()) if manifest.exists() else {}
        existing={x["id"]:x for x in old.get("batches",[])}
        for b in info:
            if b["id"] in existing and existing[b["id"]]["sha256"]!=b["sha256"]:
                raise RuntimeError("Immutable historical manifest conflict")
            existing[b["id"]]=b
        entries=[existing[k] for k in sorted(existing)]
        m={"schema":"reach-historical-api-feed-v1",
           "repository":"PART-WPO/reach-scout-discoveries",
           "generated_at":old.get("generated_at") if entries==old.get("batches",[]) else dt.datetime.now(dt.timezone.utc).isoformat(),
           "batches":entries,"batch_count":len(entries),
           "candidate_rows":sum(x["record_count"] for x in entries),
           "policy":"Unreviewed DataCite historical results for Scout investigation ONLY"}
        manifest.parent.mkdir(parents=True,exist_ok=True)
        manifest.write_text(json.dumps(m,indent=2)+"\n")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":main()
