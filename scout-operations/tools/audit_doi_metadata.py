#!/usr/bin/env python3
"""Read-only DOI metadata enrichment across historical, staged and Scout leads."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import argparse,csv,datetime as dt,hashlib,io,json,re
from pathlib import Path
from urllib.request import Request,build_opener,HTTPRedirectHandler
from urllib.error import HTTPError,URLError
from urllib.parse import quote
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"scout-operations/reports/doi-metadata-checkpoint"
M={
 "historical":("api-discoveries/historical/manifest.json","api-discoveries/historical/batches/","reach-historical-api-feed-v1"),
 "staged":("scout-discoveries/manifest.json","scout-discoveries/batches/","reach-scout-discovery-feed-v1"),
 "monthly":("api-discoveries/manifest.json","api-discoveries/batches/","reach-monthly-api-discovery-feed-v1")}
AWARD=re.compile(r"(?<![A-Za-z0-9])NA\d{2}OAR\d{7}(?![A-Za-z0-9])",re.I)
D=re.compile(r"10\.\d{4,9}/[^\s<>]+",re.I)
def doi(v):
 s=str(v or "").strip().lower()
 s=re.sub(r"^doi:\s*|^https?://(?:dx\.)?doi\.org/","",s).rstrip(".,;")
 return s if D.fullmatch(s) else ""
def date(v):
 s=str(v or "")[:10]
 try:return dt.date.fromisoformat(s).isoformat() if re.match(r"^\d{4}-\d\d-\d\d",s) else ""
 except ValueError:return ""
def j(path):return json.loads((ROOT/path).read_text(encoding="utf8"))
def merge(index,id,origin,row=None,key=""):
 if not id:return
 x=index.setdefault(id,{"doi":id,"origins":set(),"source_rows":[],"review_keys":set()})
 x["origins"].add(origin)
 if key:x["review_keys"].add(key)
 if row:
  x["source_rows"].append({"origin":origin,"title":row.get("Title",""),"authors":row.get("Authors / PI",""),
   "type":row.get("Output Type",""),"abstract":row.get("Brief Abstract",""),"date":row.get("Publication Date",""),
   "awards":row.get("NOAA Award Number(s)",""),"project":row.get("Proposed Project Title",""),"batch":row["_batch"]})
def inventory():
 index={};sizes={}
 for name,(manifest,prefix,schema) in M.items():
  m=j(manifest)
  if m["schema"]!=schema:raise ValueError("Unexpected manifest schema")
  count=0
  for b in m.get("batches",[]):
   path=str(b["path"])
   if not path.startswith(prefix) or not re.fullmatch(r"[\w.-]+\.csv",path[len(prefix):]):raise ValueError("Unsafe path "+path)
   raw=(ROOT/path).read_bytes()
   if hashlib.sha256(raw).hexdigest()!=b["sha256"]:raise ValueError("SHA mismatch "+path)
   rows=list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"),newline="")))
   if len(rows)!=b["record_count"]:raise ValueError("Row mismatch "+path+" "+str(len(rows)))
   count+=len(rows)
   for row in rows:
    row["_batch"]=path
    merge(index,doi(row.get("DOI")) or doi(row.get("Output URL")),name,row=row)
  if count!=m["candidate_rows"]:raise ValueError("Manifest total mismatch "+name)
  sizes[name]={"rows":count,"batches":len(m.get("batches",[]))}
 units=j("scout-operations/metadata-review-units.json")
 sizes["metadata_review"]={"units":len(units["units"]),"source_cases":sum(len(x.get("source_records",[])) for x in units["units"])}
 for unit in units["units"]:
  for r in unit.get("source_records",[]):
   merge(index,doi(r.get("identity")),"metadata_review",key=unit["review_key"])
 blockers=j("scout-operations/metadata-blockers.json")
 sizes["metadata_blockers"]={"entries":len(blockers["entries"])}
 for r in blockers["entries"]:merge(index,doi(r.get("identity")),"metadata_blocker")
 triage=j("scout-operations/historical-triage.json")
 sizes["historical_triage"]={"entries":len(triage["entries"])}
 for r in triage["entries"]:merge(index,doi(r.get("identity")),"historical_triage")
 audit=j("api-discoveries/date-audits/historical-2026-10-28.json")
 sizes["historical_datacite_date_audit"]={"records":len(audit["records"])}
 for a in audit["records"]:
  id=doi(a.get("doi"))
  merge(index,id,"historical_date_audit")
  index[id]["already_audited_created"]=date(a.get("created"))
 for x in index.values():
  x["origins"]=sorted(x["origins"]);x["review_keys"]=sorted(x["review_keys"])
 return index,sizes
class NoRedirect(HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,url):raise HTTPError(req.full_url,code,"Redirect rejected",headers,fp)
OPENER=build_opener(NoRedirect())
def get(host,url):
 if not url.startswith("https://"+host+"/"):raise ValueError("Unexpected API host")
 with OPENER.open(Request(url,headers={"Accept":"application/json","User-Agent":"NOAA-WPO-REACH-Scout-DOI-Audit/1.0"}),timeout=13) as r:
  blob=r.read(1100001)
  if len(blob)>1100000:raise ValueError("Response too large")
  return json.loads(blob)
def fetch(id):
 for src,host,route in (("datacite","api.datacite.org","/dois/"),("crossref","api.crossref.org","/works/")):
  url="https://"+host+route+quote(id,safe="/")
  try:
   doc=get(host,url)
   a=doc["data"]["attributes"] if src=="datacite" else doc["message"]
   returned=doi(a.get("doi") or a.get("DOI") or (doc.get("data") or {}).get("id"))
   if returned!=id:return {"status":"identity_mismatch","source":src,"evidence":url}
   if src=="datacite":
    title="; ".join(str(t.get("title","")) for t in (a.get("titles") or [])[:3])
    creators=[c.get("name","") for c in a.get("creators") or [] if c.get("name")]
    abstract=next((x.get("description","") for x in a.get("descriptions") or [] if str(x.get("descriptionType","")).lower()=="abstract"),"")
    typ=str((a.get("types") or {}).get("resourceTypeGeneral") or "")
    structured=sorted(set(str(x.get("awardNumber","")).strip() for x in a.get("fundingReferences") or [] if x.get("awardNumber")))
    created=str(a.get("created") or "")
    return {"status":"ok","source":"datacite","evidence":url,"title":title[:550],"creators":creators[:30],
      "abstract":re.sub(r"\s+"," ",abstract)[:3500],"publisher":str(a.get("publisher") or ""),
      "resource_type":typ,"reach_type":"3" if typ.lower() in ("dataset","datapaper") else "2" if typ.lower()=="software" else "1" if typ.lower() in ("journalarticle","preprint","text") else "4",
      "created":created,"registered":str(a.get("registered") or ""),"pub_date":date(created),
      "version":str(a.get("version") or ""),"funding_structured":structured,
      "funding_in_description":sorted(set(AWARD.findall(abstract+" "+title))),
      "related":[str(x.get("relationType",""))+": "+str(x.get("relatedIdentifier","")) for x in (a.get("relatedIdentifiers") or [])[:15]],
      "access_rights":[str(x.get("rights") or x.get("rightsUri") or "") for x in (a.get("rightsList") or [])[:7]],
      "listed_formats":len(a.get("formats") or []),"listed_sizes":len(a.get("sizes") or [])}
   title="; ".join((a.get("title") or [])[:3])
   authors=[" ".join(filter(None,[c.get("given"),c.get("family")])) for c in a.get("author") or []]
   abstract=re.sub(r"<[^>]+>"," ",str(a.get("abstract") or ""))
   return {"status":"ok","source":"crossref","evidence":url,"title":title[:550],"creators":authors[:30],
       "abstract":re.sub(r"\s+"," ",abstract)[:3500],"publisher":str(a.get("publisher") or ""),
       "resource_type":str(a.get("type") or ""),"reach_type":"1","created":"","registered":"",
       "pub_date":"","funding_structured":sorted(set(y for x in a.get("funder") or [] for y in x.get("award") or [])),
       "funding_in_description":sorted(set(AWARD.findall(abstract))),"related":[],"access_rights":[]}
  except HTTPError as e:
   if e.code==404:continue
   return {"status":"source_unavailable","source":src,"evidence":url,"error":"HTTP "+str(e.code)}
  except (OSError,URLError,ValueError,KeyError,TimeoutError) as e:
   return {"status":"source_unavailable","source":src,"evidence":url,"error":str(e)[:130]}
 return {"status":"not_found","source":"","evidence":""}
def classify(x,meta):
 rows=x["source_rows"];seen={
   "title":any(r["title"].strip() for r in rows),
   "creators":any(r["authors"].strip() for r in rows),
   "type":any(r["type"].strip() for r in rows),
   "abstract":any(r["abstract"].strip() for r in rows),
   "pub_date":any(r["date"].strip() for r in rows) or bool(x.get("already_audited_created"))}
 recovered=[]
 if meta.get("status")=="ok":
  for k,field in (("title","title"),("creators","creators"),("type","reach_type"),("abstract","abstract"),("pub_date","pub_date")):
   if not seen[k] and meta.get(field):recovered.append(k)
 if meta.get("status")!="ok":state="LOOKUP_UNAVAILABLE_OR_NOT_FOUND"
 elif recovered:state="FIELDS_RECOVERABLE"
 elif any(z in x["origins"] for z in ("staged","metadata_review","metadata_blocker")):state="SCOUT_FIELDS_ALREADY_COVERED"
 else:state="HISTORICAL_FIELDS_ALREADY_COVERED"
 return state,recovered,seen
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--offline",action="store_true");ap.add_argument("--workers",type=int,default=6);args=ap.parse_args()
 index,sizes=inventory()
 print("Validated source inventory:",json.dumps({"sources":sizes,"unique_dois":len(index)}),flush=True)
 previous={}
 if (OUT/"latest.json").exists():
  old=j("scout-operations/reports/doi-metadata-checkpoint/latest.json")
  previous={r["doi"]:r for r in old["records"]}
 def run(pair):
  id,x=pair
  meta={"status":"offline"} if args.offline else fetch(id)
  if meta["status"]=="source_unavailable" and id in previous:
   saved=previous[id]["metadata"]
   if saved.get("status")=="ok":
    meta=dict(saved);meta["access_warning"]="Current API inaccessible; previous successful response reused"
  state,fields,seen=classify(x,meta)
  return {"doi":id,"origins":x["origins"],"review_keys":x["review_keys"],"prior_fields":seen,
      "checkpoint_state":state,"recoverable_fields":fields,"original_rows":x["source_rows"],"metadata":meta}
 with ThreadPoolExecutor(max_workers=max(1,min(args.workers,8))) as pool:records=list(pool.map(run,sorted(index.items())))
 statuses=Counter(r["checkpoint_state"] for r in records)
 recovered=Counter(z for r in records for z in r["recoverable_fields"])
 output={"schema":"reach-scout-doi-enrichment-audit-v1","sources":sizes,"unique_dois":len(records),
   "successful_lookups":sum(r["metadata"]["status"]=="ok" for r in records),
   "state_counts":dict(statuses),"fields_recoverable":dict(recovered),
   "records_with_new_metadata":sum(bool(r["recoverable_fields"]) for r in records),
   "records":records,
   "read_only":True,"policy":"DOI created fully meets REACH Pub Date if DataCite. No reviewer decision, discovery batch or Smartsheet changed."}
 print(json.dumps({k:v for k,v in output.items() if k!="records"},indent=2),flush=True)
 if args.offline:return
 if not output["successful_lookups"]:raise RuntimeError("All source lookups failed; do not overwrite previous successful report")
 OUT.mkdir(parents=True,exist_ok=True)
 (OUT/"latest.json").write_text(json.dumps(output,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf8")
 leads=sorted((r for r in records if ("metadata_review" in r["origins"] or "metadata_blocker" in r["origins"])),key=lambda r:(-len(r["recoverable_fields"]),r["doi"]))
 lines=["# Scout — Direct DOI Metadata Checkpoint","","Verified-source research inventory, not human approval or REACH publication.",
        "","## Coverage","","| Metric | Count |","|---|---:|",
        "| Distinct DOI candidates | "+str(len(records))+" |",
        "| Successful direct DOI lookups | "+str(output["successful_lookups"])+" |",
        "| DOI records with newly recoverable metadata | "+str(output["records_with_new_metadata"])+" |",
        "| Historical DataCite intake records | "+str(sizes["historical"]["rows"])+" |",
        "| Staged Scout discovery records | "+str(sizes["staged"]["rows"])+" |",
        "| Human metadata review units | "+str(sizes["metadata_review"]["units"])+" |",
        "","## Fields recovered","","| Field | DOIs |","|---|---:|"]
 for k,v in sorted(recovered.items()):lines.append("| "+k+" | "+str(v)+" |")
 lines.extend(["","## Research state","","| Classification | DOIs |","|---|---:|"])
 for k,v in sorted(statuses.items()):lines.append("| "+k+" | "+str(v)+" |")
 lines.extend(["","## Related Scout leads and metadata-review cases","",
               "| DOI | Source | Title | Pub Date | Recoverable fields | Review key |",
               "|---|---|---|---|---|---|"])
 for r in leads:
  m=r["metadata"];name=str(m.get("title") or "").replace("|","/")[:65]
  lines.append("| "+r["doi"]+" | "+str(m.get("source") or m.get("status"))+" | "+name+" | "+str(m.get("pub_date") or "")+" | "+", ".join(r["recoverable_fields"])+" | "+", ".join(r["review_keys"])+" |")
 lines.extend(["","## Safety boundaries","",
    "An enriched DOI does not prove standalone REACH eligibility, funding, absence of duplicates or file-level access.",
    "DataCite fundingReferences can be empty despite an explicit NOAA award in the abstract.",
    "The valid created calendar date satisfies Pub Date by office policy, without separate date-only human review.",
    "The discovery route remains Scout expansion when the DOI was first found through related output research.",
    "No original feed, metadata-blocker decision, human-review sheet, Smartsheet row or public REACH record was changed.",""])
 (OUT/"README.md").write_text("\n".join(lines),encoding="utf8")
if __name__=="__main__":main()
