#!/usr/bin/env python3
"""Fast independent DOI metadata lookups; no historical-feed dependencies."""
import argparse,json,re,os,urllib.request,urllib.error,datetime
from pathlib import Path
from urllib.parse import quote
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"scout-operations/reports/independent-doi-lookup/latest.json"
DOI=re.compile(r"10\.\d{4,9}/[^\s<>]+",re.I)
def normalize(v):
 v=re.sub(r"^(?:doi:|https?://(?:dx\.)?doi\.org/)","",str(v).strip(),flags=re.I).lower().rstrip(".,;")
 return v if DOI.fullmatch(v) else ""
def fetch(host,path):
 url="https://"+host+path
 try:
  req=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"NOAA-WPO-Scout-Independent-DOI/1.0"})
  with urllib.request.urlopen(req,timeout=18) as r:return json.load(r),url,None
 except urllib.error.HTTPError as e:return None,url,{"kind":"http","code":e.code}
 except (urllib.error.URLError,TimeoutError,ValueError) as e:return None,url,{"kind":"access","detail":str(e)[:160]}
def date_parts(obj):
 try:
  p=obj.get("date-parts",[])[0]
  if len(p)==3:return datetime.date(*p).isoformat(),"day"
  if len(p)==2:return datetime.date(p[0],p[1],1).isoformat(),"month_imputed"
 except (TypeError,ValueError,IndexError):pass
 return "",""
def metadata(doi):
 attempts=[]
 for provider,host,route in (("datacite","api.datacite.org","/dois/"),("crossref","api.crossref.org","/works/")):
  data,url,error=fetch(host,route+quote(doi,safe="/"))
  attempts.append({"provider":provider,"url":url,"error":error})
  if not data:continue
  a=(data.get("data") or {}).get("attributes",{}) if provider=="datacite" else data.get("message",{})
  returned=normalize(a.get("doi") or a.get("DOI"))
  if returned!=doi:attempts[-1]["error"]={"kind":"identity_mismatch"};continue
  if provider=="datacite":
   created=str(a.get("created") or "")[:10]
   try:pub_date=datetime.date.fromisoformat(created).isoformat()
   except ValueError:pub_date=""
   return {"status":"ok","provider":provider,"evidence":url,"title":"; ".join(x.get("title","") for x in a.get("titles",[])[:3]),"creators":[x.get("name","") for x in a.get("creators",[])],"resource_type":(a.get("types") or {}).get("resourceTypeGeneral"),"abstract":" ".join(x.get("description","") for x in a.get("descriptions",[]) if x.get("descriptionType")=="Abstract")[:3500],"pub_date":pub_date,"pub_date_basis":"DataCite created (office convention)","version":a.get("version"),"publisher":a.get("publisher"),"funding_references":a.get("fundingReferences",[])[:30],"related_identifiers":a.get("relatedIdentifiers",[])[:30],"attempts":attempts}
  keys=("posted","published-print","published-online","published","issued") if a.get("type")=="posted-content" else ("published-print","published-online","published","issued")
  pub_date=basis=precision=""
  for key in keys:
   pub_date,precision=date_parts(a.get(key) or {})
   if pub_date:basis="Crossref "+key;break
  return {"status":"ok","provider":provider,"evidence":url,"title":"; ".join(a.get("title",[])[:3]),"creators":[(" ".join(filter(None,(x.get("given"),x.get("family"))))) for x in a.get("author",[])],"resource_type":a.get("type"),"abstract":str(a.get("abstract") or "")[:3500],"pub_date":pub_date,"pub_date_basis":basis,"pub_date_precision":precision,"publisher":a.get("publisher"),"funding_references":a.get("funder",[])[:30],"related_identifiers":a.get("relation",{}),"attempts":attempts}
 return {"status":"unavailable_or_not_found","attempts":attempts}
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--doi",action="append",default=[])
 args=p.parse_args()
 targets={}
 for raw in args.doi:
  d=normalize(raw)
  if not d:raise ValueError("Invalid DOI: "+raw)
  targets[d]={"doi":d,"lead_files":[]}
 for path in sorted((ROOT/"scout-operations/research-leads").glob("*.json")):
  doc=json.loads(path.read_text(encoding="utf8"))
  for lead in doc.get("leads",[]):
   d=normalize(lead.get("identity") or lead.get("output_url"))
   if d:
    entry=targets.setdefault(d,{"doi":d,"lead_files":[]})
    entry["lead_files"].append(str(path.relative_to(ROOT)))
 records=[]
 for d,entry in sorted(targets.items()):
  records.append({**entry,"metadata":metadata(d)})
 result={"schema":"reach-scout-independent-doi-lookup-v1","read_only":True,"record_count":len(records),"successful":sum(r["metadata"]["status"]=="ok" for r in records),"records":records,"policy":"DataCite created is office Pub Date; Crossref print then online then published/issued; month-only becomes first day, year-only never invented. Human decisions unchanged."}
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf8")
 print("Independent DOI lookups:",result["record_count"],"successful:",result["successful"])
if __name__=="__main__":main()
