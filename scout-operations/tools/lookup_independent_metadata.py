#!/usr/bin/env python3
"""Unified independent research metadata: DOI registries and GitHub releases."""
import argparse,importlib.util,json,re,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
TOOLS=ROOT/"scout-operations/tools"
sys.path.insert(0,str(TOOLS))
from ir_reach_identity import verified_snapshot,identity_check,research_route
from identity_disposition import verified_disposition
from research_memory import read_index, metadata_result, write_index
from datetime import datetime,timezone
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
 scope=load("lookup_artifact_scope")
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
 # Reuse one verified REACH+Scout and official NOAA IR DOI snapshot for
 # independent DOI-to-URL duplicates. Private Hub decisions remain unknown.
 public,ir_index=verified_snapshot(ROOT)
 watch=json.loads((ROOT/"scout-operations/preprint-watchlist.json").read_text(encoding="utf8"))
 def independent_identity(d,title):
  check=identity_check(public,ir_index,d,title,"https://doi.org/"+d)
  shared=verified_disposition(public,watch,ir_index,doi=d,title=title,url="https://doi.org/"+d)
  return {"public_identity":check,"shared_public_disposition":shared,
          "noaa_ir_identity":check["noaa_ir_reach_check"]["status"],
          "official_ir_url":check["noaa_ir_reach_check"]["official_url"],
          "identity_next_action":shared["next_action"],
          "seed_expansion_preserved":True}

 memory=read_index(ROOT)
 hits=0
 doi_records=[]
 for d,v in sorted(targets.items()):
  md,observed,reason=metadata_result(ROOT,memory,d)
  cached=md is not None
  if cached:
   hits+=1
  else:
   md=doi.metadata(d)
   observed=datetime.now(timezone.utc).isoformat()
  doi_records.append({**v,"metadata":md,"metadata_observed_at":observed,
                      "metadata_memory_hit":cached,"metadata_memory_reason":reason,
                      "artifact_scope":scope.zenodo(d)})
 for entry in doi_records:
  entry["identity_gate"]=independent_identity(entry["doi"],entry["metadata"].get("title",""))
 code_records=[]
 for url,lead in sorted(code.items()):
  result=github.lookup(lead)
  if result:
   result["artifact_scope"]=scope.github_tree(url)
   code_records.append(result)
 resume=[]
 for entry in doi_records:
  m=entry["metadata"]
  resume.append({"public_identity_status":entry["identity_gate"]["public_identity"]["status"],"noaa_ir_identity":entry["identity_gate"]["noaa_ir_identity"],"identity":"doi:"+entry["doi"],"kind":"doi","lookup_status":m["status"],"metadata_source":m.get("provider"),"evidence":m.get("evidence"),"lead_files":entry["lead_files"],"next_action":entry["identity_gate"]["identity_next_action"] if m["status"]=="ok" else "retry_or_escalate_metadata"})
 for entry in code_records:
  resume.append({"identity":entry.get("identity"),"output_url":entry.get("output_url"),"kind":"github","lookup_status":entry.get("status"),"evidence":entry.get("evidence",[]),"next_action":"resume_research_verification" if entry.get("status")=="ok" else "retry_or_escalate_metadata"})
 result={"artifact_scope_policy":"Zenodo file listings and exact GitHub tag trees are read-only evidence, not funding or approval. Access failures do not mean files are absent.","resume_queue":resume,"schema":"reach-scout-independent-metadata-lookup-v1","read_only":True,"public_identity_source_fingerprint":public["source_fingerprint"],"noaa_ir_index_verified":ir_index is not None,"doi_records":doi_records,"github_records":code_records,"doi_count":len(doi_records),"github_count":len(code_records),"doi_metadata_memory_hits":hits,"doi_metadata_network_attempts":len(doi_records)-hits,"doi_successful":sum(x["metadata"]["status"]=="ok" for x in doi_records),"github_successful":sum(x["status"]=="ok" for x in code_records),"policy":"Metadata enrichment does not change independent discovery provenance, establish funding/standalone eligibility, approve review or publish REACH outputs. Crossref created and GitHub repository created are not publication dates."}
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf8")
 write_index(ROOT)
 print(json.dumps({k:v for k,v in result.items() if k not in ("doi_records","github_records")},indent=2))
if __name__=="__main__":main()
