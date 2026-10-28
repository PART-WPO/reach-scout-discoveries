#!/usr/bin/env python3
"""SPARK -> DataCite / Crossref public API discovery. No Sheets, no approvals.
Outputs per-shard JSON for GitHub Actions aggregation; an API error is not zero results.
"""
import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import quote, urlencode, urlparse
import requests

SPARK="https://raw.githubusercontent.com/PART-WPO/SPARK/main/"
UA="REACH-Scout-Open-Science-Harvest/1.0 (https://github.com/PART-WPO/reach-scout-discoveries)"
SESSION=requests.Session()
SESSION.headers.update({"User-Agent":UA,"Accept":"application/json"})
ERRORS=(requests.ConnectionError,requests.Timeout,ValueError)
AWARD_PATTERN=re.compile(r"(?<![A-Z0-9])NA\d{2}OAR[A-Z0-9-]+(?![A-Z0-9])",re.I)
INPUT=[
 "Candidate ID","Title","DOI","Output URL","Output Type","NOAA Award Number(s)",
 "WPO Program","Proposed Project Title","Suggested Parent Project",
 "Authors / PI","Principal Investigators","Principal Investigator Email(s)",
 "Publication Date","Brief Abstract","IR?","IR Status","IR Pub Date",
 "IR Repository URL","Evidence URL","Funding Evidence URL",
 "Scout Discovery Rationale","Existing REACH Match","Scout Confidence","Source Run ID"
]
def fetch(url,params=None):
    if urlparse(url).netloc not in {"api.datacite.org","api.crossref.org","raw.githubusercontent.com"}:
        raise ValueError("Unexpected API endpoint "+url)
    delay=1.0
    for attempt in range(6):
        try:
            r=SESSION.get(url,params=params,timeout=45)
            if r.status_code in (429,500,502,503,504):
                if attempt==5:raise RuntimeError("API exhausted retries: %s HTTP %s"%(r.url,r.status_code))
                v=r.headers.get("Retry-After","")
                time.sleep(min(45,max(delay,float(v) if v.isdigit() else delay)))
                delay=min(30,delay*2);continue
            r.raise_for_status()
            return r.json() if (params or "api." in url or url.endswith(".json")) else r.text
        except (requests.Timeout,requests.ConnectionError):
            if attempt==5:raise
            time.sleep(delay);delay=min(30,delay*2)
    raise RuntimeError("Unexpected retry exhaustion")

def clean_award(x):
    # Public SPARK data can contain stray quote characters rather than
    # genuine award identifiers. Keep valid hyphenated WPO/OWAQ IDs.
    raw=re.sub(r"\s+","",str(x or "")).upper().strip().strip("\"'")
    # SPARK includes partial parenthetical annotations such as (SSP and (IAA.
    # Preserve the meaningful public project/award identifier before the note.
    raw=raw.split("(")[0]
    if not raw or not re.fullmatch(r"[A-Z0-9][A-Z0-9_.:/-]{1,90}",raw):
        return ""
    return raw
def parse_awards(text):
    z=list(csv.DictReader(io.StringIO(text)))
    if not z or "Award Number" not in z[0]:raise ValueError("SPARK award shard schema unexpected")
    return z
def spark_awards():
    manifest=fetch(SPARK+"agent-data/manifest.json")
    if manifest.get("feed")!="spark-agent-feed" or not manifest.get("awards",{}).get("files"):
        raise ValueError("SPARK award manifest missing")
    by_award={}
    for f in manifest["awards"]["files"]:
        path=f["path"]
        if not re.fullmatch(r"agent-data/awards/part-\d{3}[.]csv",path):raise ValueError("Unsafe SPARK shard")
        res=SESSION.get(SPARK+path,timeout=45)
        res.raise_for_status()
        data=res.content
        if hashlib.sha256(data).hexdigest()!=f["sha256"]:raise ValueError("SPARK award shard checksum "+path)
        rows=parse_awards(data.decode("utf-8-sig"))
        if len(rows)!=f["rows"]:raise ValueError("SPARK award shard count "+path)
        for x in rows:
            a=clean_award(x["Award Number"])
            if not a:continue
            d=by_award.setdefault(a,{"award":a,"programs":set(),"projects":set(),"basis":set()})
            if x.get("Managing WPO Program"):d["programs"].add(x["Managing WPO Program"].strip())
            if x.get("Project Title"):d["projects"].add(x["Project Title"].strip())
            d["basis"].add(x.get("Match Basis",""))
    return [
        {"award":a,"programs":sorted(x["programs"]),"projects":sorted(x["projects"]),"basis":sorted(x["basis"])}
        for a,x in sorted(by_award.items())
    ],manifest["source"]["sha256"]

def exact_awards(raw,award):
    key=clean_award(award)
    if not key:return False
    fields=raw if isinstance(raw,list) else [raw]
    for f in fields:
        # A funding array sometimes includes semicolon/comma-separated awards.
        s=str(f or "").upper()
        if re.search(r"(?<![A-Z0-9])"+re.escape(key)+r"(?![A-Z0-9])",s):
            return True
    return False
def iso_date(v):
    """Return full YYYY-MM-DD or partial YYYY-MM / YYYY without inventing a day."""
    s=str(v or "").strip()
    m=re.match(r"^(\d{4}(?:-\d{2})?(?:-\d{2})?)",s)
    return m.group(1) if m else ""
def date_in_month(s,month):
    return bool(s and (s==month or s.startswith(month+"-")))
def month_window(month):
    if not re.fullmatch(r"20\d{2}-(0[1-9]|1[0-2])",month):raise ValueError("Month must be YYYY-MM")
    year,m=map(int,month.split("-"))
    first=dt.date(year,m,1)
    next_month=dt.date(year+1,1,1) if m==12 else dt.date(year,m+1,1)
    return first.isoformat(),(next_month-dt.timedelta(days=1)).isoformat()

def datacite_date(a,month):
    dates=a.get("dates") or []
    for typ in ("Issued","Available"):
        for d in dates:
            if str(d.get("dateType","")).lower()==typ.lower():
                x=iso_date(d.get("date",""))
                if x and date_in_month(x,month):return x,"published_"+typ.lower()
                if len(x)>=7:return "","published_outside_window"
    pub=iso_date(a.get("published",""))
    if len(pub)>=7:
        return (pub,"published") if date_in_month(pub,month) else ("","published_outside_window")
    # Date not sufficiently precise; registration may establish a new lead,
    # but must NOT be represented as proof of publication in the month.
    registered=iso_date(a.get("registered",""))
    if len(registered)>=10 and date_in_month(registered,month):
        return "","registration_only_publication_unverified"
    return "","out_of_window"

def crossref_date(a,month):
    dates=[]
    for k in ("published-online","published-print","published","issued"):
        dp=(a.get(k) or {}).get("date-parts") or []
        if dp and dp[0]:
            parts=dp[0]
            date="-".join([str(parts[0]).zfill(4)]+[str(v).zfill(2) for v in parts[1:3]])
            dates.append((date,len(parts)))
    for date,length in dates:
        if date_in_month(date,month):
            return (date if length>=3 else ""),("published_exact" if length>=3 else "published_month_only")
    return "","published_outside_window" if dates else "out_of_window"

def match_datacite(a,award):
    return exact_awards([f.get("awardNumber","") for f in a.get("fundingReferences",[]) or []],award)
def match_crossref(a,award):
    awards=[]
    for f in (a.get("funder") or []):
        for x in (f.get("award") or []):awards.append(x)
    return exact_awards(awards,award)

def query_datacite(award,mode,month,max_pages):
    if mode=="historical":
        q='fundingReferences.awardNumber:"%s"'%award
    else:
        start,end=month_window(month)
        q='fundingReferences.awardNumber:"%s" AND (publicationYear:%s OR registered:[%s TO %s])'%(
           award,month[:4],start,end)
    url="https://api.datacite.org/dois"
    params={"query":q,"page[size]":100}
    items=[]
    for p in range(max_pages):
        result=fetch(url,params=params)
        items.extend(x["attributes"] for x in (result.get("data") or []))
        nxt=(result.get("links") or {}).get("next")
        if not nxt:break
        if urlparse(nxt).netloc!="api.datacite.org":raise ValueError("Unexpected DataCite next URL")
        url=nxt;params=None
    else:
        raise RuntimeError("DataCite pagination ceiling for "+award)
    return [a for a in items if match_datacite(a,award)]
def query_crossref(award,month,max_pages):
    start,end=month_window(month)
    url="https://api.crossref.org/works"
    cursor="*";items=[]
    for p in range(max_pages):
        result=fetch(url,params={
          "filter":f"award.number:{award},from-pub-date:{start},until-pub-date:{end}",
          "rows":100,"cursor":cursor,
          "select":"DOI,title,author,published-online,published-print,published,issued,funder,type,abstract,URL,relation"
        })
        response=result.get("message") or {}
        page=response.get("items") or []
        items.extend(x for x in page if match_crossref(x,award))
        if len(page)<100:break
        new_cursor=response.get("next-cursor")
        if not new_cursor or new_cursor==cursor:raise RuntimeError("Crossref cursor stalled for "+award)
        cursor=new_cursor
    else:raise RuntimeError("Crossref pagination ceiling for "+award)
    return items

def to_candidate(a,src,award,mode,month):
    citation=""
    doi=str(a.get("doi") or a.get("DOI") or "").strip().lower()
    if not doi.startswith("10."):return None
    if src=="datacite":
        pub,basis=datacite_date(a,month) if mode=="monthly" else ("","historical_undated")
        typ=((a.get("types") or {}).get("resourceTypeGeneral") or "").lower()
        outtype= "3" if "dataset" in typ or "instrument" in typ else "2" if "software" in typ else "1" if typ in ("journalarticle","text","preprint","report","dissertation") else "4"
        title=((a.get("titles") or [{}])[0].get("title") or "").strip()
        authors=[x.get("name","") for x in (a.get("creators") or [])]
        abstract=next((x.get("description","") for x in (a.get("descriptions") or []) if x.get("descriptionType","").lower()=="abstract"),"")
        evidence="https://api.datacite.org/dois/"+quote(doi,safe="/")
        relationships=a.get("relatedIdentifiers") or []
    else:
        pub,basis=crossref_date(a,month)
        if mode=="monthly" and basis=="published_outside_window":return None
        typ=str(a.get("type") or "").lower()
        outtype= "3" if "dataset" in typ else "2" if "software" in typ else "1" if typ in ("journal-article","posted-content","proceedings-article","book-chapter","report","dissertation") else "4"
        title=((a.get("title") or [""])[0] or "").strip()
        authors=[" ".join([str(x.get("given","")).strip(),str(x.get("family","")).strip()]).strip() for x in (a.get("author") or [])]
        # Preserve the family-name citation behavior of the former Google Sheet script.
        people=a.get("author") or []
        first=people[0] if people else {}
        family=first.get("family") or first.get("name") or "Unknown Author"
        prior_dp=(a.get("published-print") or {}).get("date-parts") or (a.get("published-online") or {}).get("date-parts") or (a.get("issued") or {}).get("date-parts") or []
        yr=prior_dp[0][0] if prior_dp and prior_dp[0] else "Unknown Year"
        citation=f"{family} et al. ({yr})"
        abstract=a.get("abstract","") or ""
        evidence="https://api.crossref.org/works/"+quote(doi,safe="/")
        relationships=a.get("relation") or {}
    if mode=="monthly" and basis in ("out_of_window","published_outside_window"):
        return None
    if mode=="monthly" and not (pub or basis=="registration_only_publication_unverified" or basis=="published_month_only"):
        return None
    text=re.sub(r"<[^>]+>"," ",str(abstract));text=re.sub(r"\s+"," ",text).strip()
    return {"doi":doi,"src":src,"award":award,
      "title":title or "Provisional metadata for DOI "+doi,
      "authors":[x for x in authors if x],"abstract":text[:800],
      "date":pub if len(pub)==10 else "","date_basis":basis,
      "outtype":outtype,"evidence":evidence,"related":bool(relationships),
      "citation":citation,
      "published_month":month if mode=="monthly" else ""}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--mode",choices=["monthly","historical"],required=True)
    p.add_argument("--source",choices=["datacite","crossref"],required=True)
    p.add_argument("--month",default="")
    p.add_argument("--shard",type=int,required=True)
    p.add_argument("--shards",type=int,default=8)
    p.add_argument("--limit-awards",type=int,default=0)
    p.add_argument("--max-pages",type=int,default=25)
    p.add_argument("--output",default="api-discoveries/tmp")
    args=p.parse_args()
    if args.mode=="historical" and args.source!="datacite":raise ValueError("Historical pilot is DataCite-only")
    if args.mode=="monthly" and not args.month:
        first=dt.datetime.now(dt.timezone.utc).date().replace(day=1)
        args.month=(first-dt.timedelta(days=1)).strftime("%Y-%m")
    if args.mode=="monthly":month_window(args.month)
    awards,source_sha=spark_awards()
    if args.limit_awards:awards=awards[:args.limit_awards]
    if args.shard<0 or args.shard>=args.shards:raise ValueError("Invalid shard index")
    selected=[x for i,x in enumerate(awards) if i%args.shards==args.shard]
    records=[];failures=[];attempted=[]
    for index,x in enumerate(selected):
        award=x["award"];attempted.append(award)
        try:
            matches=query_datacite(award,args.mode,args.month,args.max_pages) if args.source=="datacite" else query_crossref(award,args.month,args.max_pages)
            for a in matches:
                v=to_candidate(a,args.source,award,args.mode,args.month)
                if v:
                    v["programs"]=x["programs"];v["projects"]=x["projects"]
                    records.append(v)
        except Exception as ex:
            failures.append({"award":award,"error":str(ex)[:250]})
        if index%15==0:print(args.source,args.shard,index+1,"/",len(selected),"records",len(records),"failures",len(failures),flush=True)
        time.sleep(0.5)
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    file=out/("%s-%s-shard%02d.json"%(args.mode,args.source,args.shard))
    file.write_text(json.dumps({"mode":args.mode,"source":args.source,"month":args.month,
      "shard":args.shard,"shards":args.shards,"source_sha":source_sha,
      "total_awards":len(awards),"attempted_awards":attempted,
      "failures":failures,"records":records},ensure_ascii=False))
    print("Wrote",file,"awards",len(selected),"candidates",len(records),"errors",len(failures))
    if failures:sys.exit(2)
if __name__=="__main__":main()
