#!/usr/bin/env python3
"""Complete two annotated SPARK identifiers and enrich historical DataCite date facts.
Does not modify original immutable research batches or human review decisions.
"""
import csv,datetime as dt,hashlib,io,json,re,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import harvest as h
import publish_harvest as p
ROOT=Path(__file__).resolve().parents[2]
HIST=ROOT/"api-discoveries/historical"
manifest=HIST/"manifest.json"
m=json.loads(manifest.read_text())
assert m["schema"]=="reach-historical-api-feed-v1"
original=[x for x in m["batches"] if "spark-all" in x["id"]]
assert original,"Original all-SPARK historical run missing"
dois=set()
for batch in original:
    raw=(ROOT/batch["path"]).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==batch["sha256"]
    rows=list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    assert len(rows)==batch["record_count"]
    for r in rows:dois.add(r["DOI"].strip().lower())
datefacts={}
for i,doi in enumerate(sorted(dois),1):
    a=h.fetch("https://api.datacite.org/dois/"+h.quote(doi,safe="/"))["data"]["attributes"]
    dates=a.get("dates") or []
    verified=""
    basis="unknown"
    for typ in ("Issued","Available"):
        vals=[h.iso_date(x.get("date","")) for x in dates if str(x.get("dateType","")).lower()==typ.lower()]
        candidates=[x for x in vals if len(x)==10]
        if candidates:
            verified=candidates[0];basis="datacite_"+typ.lower();break
    if not verified:
        v=h.iso_date(a.get("published",""))
        if len(v)==10:verified=v;basis="datacite_published"
    datefacts[doi]={"verified_publication_date":verified,"date_basis":basis,
       "metadata_source":"https://api.datacite.org/dois/"+h.quote(doi,safe="/")}
    if i%25==0:print("Enriched",i,"of",len(dois),"DOIs",flush=True)
    time.sleep(0.15)
target=HIST/"metadata-enrichment-2026-10-28.json"
content=(json.dumps({"schema":"reach-historical-datacite-enrichment-v1",
  "source_manifest_sha256":hashlib.sha256(manifest.read_bytes()).hexdigest(),
  "records":datefacts},indent=2,sort_keys=True)+"\n").encode("utf-8")
p.immutable_file(target,content)
# Recover two plausible WPO award bases from incomplete public parenthetical labels.
extra=["WPO20-SSP-E-1","OWAQOBS001"]
candidates=[]
for award in extra:
    records=h.query_datacite(award,"historical","",max_pages=25)
    print("Supplemental award",award,"matched",len(records),"DataCite records",flush=True)
    for a in records:
        row=h.to_candidate(a,"datacite",award,"historical","")
        if row:
            # Publication dates use true record-level issued/release metadata.
            dates=a.get("dates") or []
            for typ in ("Issued","Available"):
                vals=[h.iso_date(x.get("date","")) for x in dates if str(x.get("dateType","")).lower()==typ.lower()]
                exact=next((v for v in vals if len(v)==10),"")
                if exact:
                    row["date"]=exact;row["date_basis"]="published_"+typ.lower();break
            row["programs"]=[];row["projects"]=[]
            candidates.append(row)
combined={}
from collections import defaultdict
groups=defaultdict(list)
for c in candidates:groups[c["doi"]].append(c)
out=[p.merge_record(v) for k,v in sorted(groups.items()) if k not in dois]
run="REACH-HISTORICAL-DATACITE-2026-10-28-ANNOTATED"
batch=p.batches([p.output_row(x,"historical","",run) for x in out],
    HIST/"batches","2026-10-28-historical-datacite-annotated-awards",run)
existing={x["id"]:x for x in m["batches"]}
for x in batch:existing[x["id"]]=x
m["batches"]=[existing[k] for k in sorted(existing)]
m["batch_count"]=len(m["batches"])
m["candidate_rows"]=sum(x["record_count"] for x in m["batches"])
m["generated_at"]=dt.datetime.now(dt.timezone.utc).isoformat() if batch else m["generated_at"]
manifest.write_text(json.dumps(m,indent=2)+"\n")
summary={"schema":"reach-historical-datacite-supplement-v1",
  "annotated_awards_checked":extra,"new_distinct_dois":len(out),
  "original_unique_dois_enriched":len(datefacts),
  "verified_exact_dates":sum(bool(x["verified_publication_date"]) for x in datefacts.values()),
  "result_batch_count":len(batch),"scout_review_state":"unchecked_research_input_only"}
p.immutable_file(ROOT/"api-discoveries/runs/historical-datacite-annotated-2026-10-28.json",
(json.dumps(summary,indent=2)+"\n").encode("utf-8"))
print(json.dumps(summary,indent=2))
