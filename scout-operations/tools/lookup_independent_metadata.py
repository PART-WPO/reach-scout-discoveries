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
 # Shared public identity gate precedes any new-output recommendation. NOAA IR is
 # consulted only after a verified DOI/title/URL REACH+Scout negative.
 identity=load("decision_pipeline")
 import hashlib
 from urllib.parse import urlsplit
 idx_path=ROOT/"scout-operations/identity-cache/public-identity-index.json"
 idx=json.loads(idx_path.read_text())
 identity.check_index_fresh(ROOT,idx)
 ir_manifest_path=ROOT/"scout-operations/noaa-ir/manifest.json"
 ir_manifest=json.loads(ir_manifest_path.read_text())
 if not ir_manifest.get("complete"): raise ValueError("NOAA IR index incomplete")
 ir_shards={s["prefix"]:s for s in ir_manifest["shards"]}
 if len(ir_shards)!=16: raise ValueError("NOAA IR shard manifest incomplete")
 ir_cache={}
 def independent_identity(d,title):
  initial=identity.lookup(idx,doi=d,title=title)
  result={"public_identity":initial,"noaa_ir_identity":"NOT_CHECKED_DUPLICATE_OR_POSSIBLE_MATCH","official_ir_url":None}
  if initial["status"]!="NO_PUBLIC_IDENTITY_MATCH":return result
  prefix=hashlib.sha256(d.encode()).hexdigest()[0]
  if prefix not in ir_cache:
   s=ir_shards[prefix]
   p=ROOT/s["path"]
   raw=p.read_bytes()
   if hashlib.sha256(raw).hexdigest()!=s["sha256"]:raise ValueError("NOAA IR shard SHA mismatch: "+s["path"])
   payload=json.loads(raw)
   if len(payload["records"])!=s["record_count"]:raise ValueError("NOAA IR shard count mismatch")
   ir_cache[prefix]=payload["records"]
  hits=ir_cache[prefix].get(d,[])
  if len(hits)!=1:
   result["noaa_ir_identity"]="AMBIGUOUS" if hits else "NOT_FOUND_IN_VERIFIED_IR_INDEX"
   return result
  url=hits[0]
  if not re.fullmatch(r"https://repository\\.library\\.noaa\\.gov/view/noaa/\\d+",url):
   raise ValueError("Invalid official NOAA IR landing URL")
  second=identity.lookup(idx,doi=d,title=title,url=url)
  result.update(public_identity=second,official_ir_url=url,
                noaa_ir_identity=("EXACT_OFFICIAL_IR_URL_IN_REACH" if second["status"]=="CONFIRMED_PUBLIC_REACH_IDENTITY"
                                  else "EXACT_OFFICIAL_IR_URL_IN_SCOUT" if second["status"]=="IN_PUBLIC_SCOUT_QUEUE"
                                  else "OFFICIAL_IR_URL_NOT_IN_PUBLIC_REACH_OR_SCOUT"))
  return result

 doi_records=[{**v,"metadata":doi.metadata(d),"artifact_scope":scope.zenodo(d)} for d,v in sorted(targets.items())]
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
  resume.append({"public_identity_status":entry["identity_gate"]["public_identity"]["status"],"noaa_ir_identity":entry["identity_gate"]["noaa_ir_identity"],"identity":"doi:"+entry["doi"],"kind":"doi","lookup_status":m["status"],"metadata_source":m.get("provider"),"evidence":m.get("evidence"),"lead_files":entry["lead_files"],"next_action":("skip_duplicate_original_preserve_expansion_seed" if entry["identity_gate"]["public_identity"]["status"] in ("CONFIRMED_PUBLIC_REACH_IDENTITY","IN_PUBLIC_SCOUT_QUEUE") else "verify_possible_identity" if entry["identity_gate"]["public_identity"]["matches"] else "resume_research_verification" if m["status"]=="ok" else "retry_or_escalate_metadata")})
 for entry in code_records:
  resume.append({"identity":entry.get("identity"),"output_url":entry.get("output_url"),"kind":"github","lookup_status":entry.get("status"),"evidence":entry.get("evidence",[]),"next_action":"resume_research_verification" if entry.get("status")=="ok" else "retry_or_escalate_metadata"})
 result={"artifact_scope_policy":"Zenodo file listings and exact GitHub tag trees are read-only evidence, not funding or approval. Access failures do not mean files are absent.","resume_queue":resume,"schema":"reach-scout-independent-metadata-lookup-v1","read_only":True,"doi_records":doi_records,"github_records":code_records,"doi_count":len(doi_records),"github_count":len(code_records),"doi_successful":sum(x["metadata"]["status"]=="ok" for x in doi_records),"github_successful":sum(x["status"]=="ok" for x in code_records),"policy":"Metadata enrichment does not change independent discovery provenance, establish funding/standalone eligibility, approve review or publish REACH outputs. Crossref created and GitHub repository created are not publication dates."}
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf8")
 print(json.dumps({k:v for k,v in result.items() if k not in ("doi_records","github_records")},indent=2))
if __name__=="__main__":main()
