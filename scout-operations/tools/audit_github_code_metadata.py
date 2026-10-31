#!/usr/bin/env python3
"""Read-only GitHub API enrichment of public Scout software research leads."""
import json,os,re,time,urllib.request,urllib.error
from pathlib import Path
from urllib.parse import quote
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"scout-operations/reports/github-code-metadata-checkpoint"
PAT=re.compile(r"^https://github[.]com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)(?:/(?:releases/tag|tree)/([^?#]+))?/?$")
def get(route):
 url="https://api.github.com"+route
 headers={"Accept":"application/vnd.github+json","User-Agent":"NOAA-WPO-REACH-Scout-Code-Metadata/1.0","X-GitHub-Api-Version":"2022-11-28"}
 if os.environ.get("GITHUB_TOKEN"):headers["Authorization"]="Bearer "+os.environ["GITHUB_TOKEN"]
 request=urllib.request.Request(url,headers=headers)
 try:
  with urllib.request.urlopen(request,timeout=20) as response:return json.load(response),None
 except urllib.error.HTTPError as e:return None,{"status":"http_error","code":e.code,"message":str(e)}
 except (urllib.error.URLError,TimeoutError,ValueError) as e:return None,{"status":"access_error","message":str(e)[:200]}
def lookup(lead):
 url=str(lead.get("output_url") or "")
 match=PAT.fullmatch(url)
 if not match:return None
 owner,repo,tag=match.groups()
 base="/repos/"+quote(owner,safe="")+"/"+quote(repo,safe="")
 item={"identity":lead.get("identity"),"output_url":url,"award":lead.get("project_award"),"origin_method":lead.get("research_origin_method"),"source":"github_api","status":"partial","evidence":[],"errors":[]}
 metadata,err=get(base)
 if err:item["errors"].append({"endpoint":"repository",**err})
 else:
  item["repository"]={"full_name":metadata.get("full_name"),"description":metadata.get("description"),"created_at":metadata.get("created_at"),"pushed_at":metadata.get("pushed_at"),"updated_at":metadata.get("updated_at"),"archived":metadata.get("archived"),"fork":metadata.get("fork"),"default_branch":metadata.get("default_branch"),"license":(metadata.get("license") or {}).get("spdx_id"),"homepage":metadata.get("homepage"),"topics":metadata.get("topics",[])}
  item["evidence"].append("https://api.github.com"+base)
 if tag:
  endpoint=base+"/releases/tags/"+quote(tag,safe="")
  release,err=get(endpoint)
  if err:
   item["errors"].append({"endpoint":"release",**err})
   ref,ref_err=get(base+"/git/ref/tags/"+quote(tag,safe=""))
   if ref_err:item["errors"].append({"endpoint":"tag_ref",**ref_err})
   else:
    item["tag_ref"]={"sha":(ref.get("object") or {}).get("sha"),"type":(ref.get("object") or {}).get("type")}
    item["evidence"].append("https://api.github.com"+base+"/git/ref/tags/"+quote(tag,safe=""))
    item["date_status"]="TAG_EXISTS_NO_VERIFIED_PUBLICATION_DATE"
  else:
   item["release"]={"tag_name":release.get("tag_name"),"name":release.get("name"),"published_at":release.get("published_at"),"created_at":release.get("created_at"),"draft":release.get("draft"),"prerelease":release.get("prerelease"),"assets":[{"name":a.get("name"),"size":a.get("size")} for a in release.get("assets",[])[:30]],"body_excerpt":str(release.get("body") or "")[:1500]}
   item["date_status"]="RELEASE_PUBLISHED_DATE_VERIFIED" if release.get("published_at") else "RELEASE_DATE_NOT_AVAILABLE"
   item["evidence"].append("https://api.github.com"+endpoint)
 item["status"]="ok" if item.get("repository") and (not tag or item.get("release")) else "partial"
 return item
def main():
 records=[];seen=set();lead_files=sorted((ROOT/"scout-operations/research-leads").glob("*.json"))
 for file in lead_files:
  data=json.loads(file.read_text(encoding="utf8"))
  for lead in data.get("leads",[]):
   url=str(lead.get("output_url") or "")
   if url in seen:continue
   if not PAT.fullmatch(url):continue
   seen.add(url)
   result=lookup(lead)
   if result:
    result["lead_file"]=str(file.relative_to(ROOT))
    records.append(result)
   time.sleep(0.25)
 OUT.mkdir(parents=True,exist_ok=True)
 result={"schema":"reach-scout-github-code-metadata-v1","read_only":True,"records":records,"lead_files_checked":len(lead_files),"record_count":len(records),"successful":sum(x["status"]=="ok" for x in records),"policy":"GitHub release published_at is source-specific evidence; repository created_at and pushed_at are not release dates. Tag existence alone does not establish a publication date. No automatic approval or publication."}
 (OUT/"latest.json").write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf8")
 print(json.dumps({k:v for k,v in result.items() if k!="records"}))
if __name__=="__main__":main()
