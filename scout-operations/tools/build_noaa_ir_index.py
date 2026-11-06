#!/usr/bin/env python3
"""Create checksum-verified, minimized DOI -> NOAA IR item URL index.

Uses NOAA Central Library's public JSON API (entire IR, not just OAR).
No private data, human decisions, REACH changes, inferred title matches or
negative statements. A partial API harvest never overwrites the old index.
"""
import datetime as dt
import hashlib
import json
import re
import time
from collections import defaultdict
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[2]
DEST=ROOT/"scout-operations/noaa-ir"
API="https://repository.library.noaa.gov/fedora/export/view"
HEADERS={"User-Agent":"REACH-Scout-NOAA-IR-Index/1.0 (https://github.com/PART-WPO/reach-scout-discoveries)","Accept":"application/json"}
DOI=re.compile(r"^10\.\d{4,9}/\S+$",re.I)
PID=re.compile(r"^(?:noaa:)?(\d+)$",re.I)
KEYS=("mods.sm_digital_object_identifier", "mods.doi", "dc.identifier")

def normalize_doi(value):
    s=str(value or "").strip().lower()
    s=re.sub(r"^https?://(?:dx\.)?doi\.org/","",s)
    s=re.sub(r"^doi:\s*","",s).strip()
    return s if DOI.fullmatch(s) else ""

def doi_values(doc):
    vals=set()
    for key in KEYS:
        data=doc.get(key,[])
        if not isinstance(data,list):data=[data]
        for item in data:
            doi=normalize_doi(item)
            if doi: vals.add(doi)
    return vals

def pid_url(doc):
    match=PID.fullmatch(str(doc.get("PID","")).strip())
    return f"https://repository.library.noaa.gov/view/noaa/{match.group(1)}" if match else ""

def fetch_json(params,tries=5):
    url=API+"?"+urlencode(params)
    for attempt in range(tries):
        try:
            with urlopen(Request(url,headers=HEADERS),timeout=90) as response:
                if response.status!=200:raise RuntimeError(f"Unexpected NOAA IR HTTP {response.status}")
                # NOAA IR pages are deliberately bounded; fail closed on huge responses.
                data=response.read(50_000_001)
                if len(data)>50_000_000:raise RuntimeError("NOAA IR page exceeded configured size limit")
            obj=json.loads(data)
            if not isinstance(obj.get("response"),dict):raise ValueError("NOAA IR JSON response schema changed")
            return obj
        except (HTTPError,URLError,TimeoutError,ConnectionError) as exc:
            if attempt==tries-1:raise RuntimeError("NOAA IR API request failed after retries: "+str(exc)) from exc
            delay=min(30,2**attempt)
            print("NOAA IR retry",attempt+1,"in",delay,"s",flush=True)
            time.sleep(delay)

def collect(page_size=1000,max_pages=400):
    init=fetch_json({"rows":1,"start":0})
    expected=init["response"].get("numFound")
    if not isinstance(expected,int) or expected<0 or expected>page_size*max_pages:
        raise RuntimeError("Invalid/too large NOAA IR API total")
    doi_to_urls=defaultdict(set)
    pids=set()
    scanned=0
    invalid_pids=0
    unresolved=set()
    for start in range(0,expected,page_size):
        payload=fetch_json({"rows":min(page_size,expected-start),"start":start})
        result=payload["response"]
        if result.get("numFound")!=expected:
            raise RuntimeError("NOAA IR changed during pagination; retry after stabilization")
        if result.get("start")!=start:
            raise RuntimeError("NOAA IR did not respect pagination start")
        docs=result.get("docs")
        if not isinstance(docs,list) or len(docs)!=min(page_size,expected-start):
            raise RuntimeError("Incomplete NOAA IR page starting "+str(start))
        for doc in docs:
            if not isinstance(doc,dict):raise RuntimeError("Invalid NOAA IR item")
            ids=doi_values(doc)
            url=pid_url(doc)
            if not url:
                invalid_pids+=1
                unresolved.update(ids)
                continue
            if url in pids:raise RuntimeError("NOAA IR pagination duplicated a PID")
            pids.add(url)
            for doi in ids:
                doi_to_urls[doi].add(url)
        scanned+=len(docs)
        print("NOAA IR catalog records scanned",scanned,"of",expected,flush=True)
        time.sleep(0.15)
    if scanned!=expected or len(pids)+invalid_pids!=expected:
        raise RuntimeError("Incomplete NOAA IR DOI index; never commit partial index")
    for doi in unresolved:
        doi_to_urls.pop(doi,None)
    print("Invalid PID records:",invalid_pids,"DOI identities held unknown:",len(unresolved),flush=True)
    return expected,doi_to_urls,{"invalid_pid_records":invalid_pids,"unresolved_dois":len(unresolved)}

def encode_json(obj):
    return (json.dumps(obj,indent=2,ensure_ascii=False,sort_keys=True)+"\n").encode("utf-8")

def write_index(expected,by_doi,dest=DEST,invalid_pid_records=0,unresolved_dois=0):
    dest.mkdir(parents=True,exist_ok=True)
    shard_dir=dest/"shards";shard_dir.mkdir(parents=True,exist_ok=True)
    shards=[]
    for prefix in "0123456789abcdef":
        records={d:sorted(urls) for d,urls in by_doi.items()
                 if hashlib.sha256(d.encode("utf-8")).hexdigest()[0]==prefix}
        name=f"scout-operations/noaa-ir/shards/{prefix}.json"
        content=encode_json({"schema":"reach-scout-noaa-ir-doi-shard-v1",
                             "prefix":prefix,"records":records})
        target=shard_dir/(prefix+".json")
        target.write_bytes(content)
        shards.append({"prefix":prefix,"path":name,
                       "sha256":hashlib.sha256(content).hexdigest(),
                       "record_count":len(records)})
    m={"schema":"reach-scout-noaa-ir-doi-index-v1",
       "repository":"PART-WPO/reach-scout-discoveries",
       "source_api":API,
       "generated_at":dt.datetime.now(dt.timezone.utc).isoformat(),
       "complete":True,"records_scanned":expected,
       "invalid_pid_records":invalid_pid_records,
       "unresolved_doi_identities_held_unknown":unresolved_dois,
       "distinct_dois":len(by_doi),
       "ambiguous_dois":sum(len(v)>1 for v in by_doi.values()),
       "policy":"Exact DOI matches only; absent DOI is UNKNOWN not FALSE; never infer IR membership from title or award",
       "shards":shards}
    (dest/"manifest.json").write_bytes(encode_json(m))
    print(json.dumps({"records_scanned":expected,"distinct_dois":len(by_doi),
                      "ambiguous_dois":m["ambiguous_dois"],"complete":True},indent=2))
    return m

def collect_with_stability_retries(attempts=3, pause_seconds=15):
    """Restart a complete harvest if the live catalog changes during pagination.

    Never combine pages from separate attempts or publish a partial harvest.
    All other validation failures remain fatal.
    """
    if attempts < 1:
        raise ValueError("At least one complete harvest attempt is required")
    for attempt in range(attempts):
        try:
            return collect()
        except RuntimeError as exc:
            if str(exc) != "NOAA IR changed during pagination; retry after stabilization":
                raise
            if attempt == attempts - 1:
                raise RuntimeError(
                    f"NOAA IR catalog changed during all {attempts} full-harvest attempts; "
                    "previous validated index preserved"
                ) from exc
            print(
                f"NOAA IR catalog changed during harvest {attempt + 1}/{attempts}; "
                "discarding this attempt and restarting from page zero",
                flush=True,
            )
            time.sleep(pause_seconds)


if __name__=="__main__":
    total,doi_links,stats=collect_with_stability_retries()
    write_index(total,doi_links,invalid_pid_records=stats["invalid_pid_records"],unresolved_dois=stats["unresolved_dois"])
