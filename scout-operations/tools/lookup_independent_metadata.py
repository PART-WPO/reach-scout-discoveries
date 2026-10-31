#!/usr/bin/env python3
"""Unified independent research metadata: DOI registries and GitHub releases."""
import argparse,importlib.util,json,re,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
TOOLS=ROOT/"scout-operations/tools"
OUT=ROOT/"scout-operations/reports/independent-metadata-lookup/latest.json"
def load(name):
 spec=importlib.util.spec_from_file_location(name,TOOLS/(name+".py"))
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 return module
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--doi",action="append",default=[])
 p.add_argument("--github-url",action="append",default=[])
 args=p.parse_args()
 doi=load("lookup_independent_dois")
 github=load("audit_github_code_metadata")
 targets={}
 for raw in args.doi:
  d=doi.normalize(raw)
  if not d:raise ValueError("Invalid DOI: "+raw)
  targets[d]={"doi":d,"lead_files":[]}
 code={}
 for raw in args.github_url:
  if not github.PAT.fullmatch(raw):raise ValueError("Invalid GitHub repository/release URL: "+raw)
  code[raw]={"output_url":raw,"identity":raw}
 for file in sorted((ROOT/"scout-operations/research-leads").glob("*.json")):
  document=json.loads(file.read_text(encoding="utf8"))
  for lead in document.get("leads",[]):
   d=doi.normalize(lead.get("identity") or lead.get("output_url"))
   if d:targets.setdefault(d,{"doi":d,"lead_files":[]})["lead_files"].append(str(file.relative_to(ROOT)))
   url=str(lead.get("output_url") or "")
   if github.PAT.fullmatch(url):code.setdefault(url,lead)
 doi_records=[{**v,"metadata":doi.metadata(d)} for d,v in sorted(targets.items())]
 code_records=[]
 for url,lead in sorted(code.items()):
  result=github.lookup(lead)
  if result:code_records.append(result)
 result={"schema":"reach-scout-independent-metadata-lookup-v1","read_only":True,"doi_records":doi_records,"github_records":code_records,"doi_count":len(doi_records),"github_count":len(code_records),"doi_successful":sum(x["metadata"]["status"]=="ok" for x in doi_records),"github_successful":sum(x["status"]=="ok" for x in code_records),"policy":"Metadata enrichment does not change independent discovery provenance, establish funding/standalone eligibility, approve review or publish REACH outputs. Crossref created and GitHub repository created are not publication dates."}
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf8")
 print(json.dumps({k:v for k,v in result.items() if k not in ("doi_records","github_records")},indent=2))
if __name__=="__main__":main()
