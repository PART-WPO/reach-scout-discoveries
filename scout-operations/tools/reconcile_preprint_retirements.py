#!/usr/bin/env python3
"""Retire REACH-confirmed published preprint families; retain immutable evidence and tombstones."""
import argparse, json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
WATCH="scout-operations/preprint-watchlist.json"
LEADS="scout-operations/preprint-publication-leads.json"
ARCHIVE="scout-operations/preprint-retirement-archive.json"
DOI=re.compile(r"^10\.\d{4,9}/\S+$",re.I)
def norm(x):
 x=re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)","",str(x or "").strip(),flags=re.I)
 return x.lower().rstrip(".,);")
def read(root,path):return json.loads((root/path).read_text(encoding="utf-8"))
def save(root,path,obj):(root/path).write_text(json.dumps(obj,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
def confirmed(lead):
 proof=lead.get("confirmed_reach_duplicate") or {}
 return (lead.get("status")=="already_in_reach" and
         bool(proof.get("reach_ids")) and
         bool(proof.get("basis")) and
         norm(lead.get("published_doi")) and
         bool(proof.get("source")))
def reconcile(watch,leads,archive):
 if archive.get("schema")!="reach-scout-preprint-retirement-archive-v1":raise ValueError("Unknown archive schema")
 tombstones={norm(x["preprint_doi"]):x for x in archive.get("entries",[])}
 confirmed_leads={}
 for lead in leads["entries"]:
  if confirmed(lead):
   final=norm(lead["published_doi"])
   if not DOI.fullmatch(final):raise ValueError("Invalid published DOI")
   confirmed_leads[final]=lead
 for final,lead in sorted(confirmed_leads.items()):
  versions=set(norm(x) for x in lead.get("preprint_dois",[]))
  versions.add(norm(lead.get("preprint_doi")))
  for version in versions:
   if not DOI.fullmatch(version):continue
   prior=tombstones.get(version)
   if prior and prior["published_doi"]!=final:raise ValueError("Conflicting published identity for "+version)
   if not prior:
    tombstones[version]={"preprint_doi":version,"published_doi":final,
      "reach_ids":sorted(set(lead["confirmed_reach_duplicate"]["reach_ids"])),
      "verification_basis":lead["confirmed_reach_duplicate"]["basis"],
      "verification_source":lead["confirmed_reach_duplicate"]["source"],
      "reason":"OFFICIAL_PUBLISHED_VERSION_CONFIRMED_IN_PUBLIC_REACH"}
 active=[x for x in watch["entries"] if norm(x["preprint_doi"]) not in tombstones]
 retired=len(watch["entries"])-len(active)
 watch["entries"]=active
 watch["metrics"]={
  "preprints_tracked":len(active),
  "preprints_still_waiting_for_official_publication":sum(not x.get("verified_published_dois") for x in active),
  "preprints_with_verified_published_versions":sum(bool(x.get("verified_published_dois")) for x in active),
  "verified_official_article_doi_research_leads":len(leads["entries"]),
  "automatically_forwarded_to_discovery_hub":0,
  "retired_preprint_versions_total":len(tombstones)}
 archive["entries"]=[tombstones[k] for k in sorted(tombstones)]
 archive["retired_preprint_versions_total"]=len(tombstones)
 archive["confirmed_published_articles_total"]=len(set(x["published_doi"] for x in tombstones.values()))
 return retired
def run(root=ROOT):
 watch,leads=read(root,WATCH),read(root,LEADS)
 p=root/ARCHIVE
 archive=read(root,ARCHIVE) if p.exists() else {"schema":"reach-scout-preprint-retirement-archive-v1","policy":"Public evidence only. Retired identities never reseeded. Prior human decisions and original sources untouched.","entries":[]}
 retired=reconcile(watch,leads,archive)
 save(root,WATCH,watch);save(root,ARCHIVE,archive)
 print(json.dumps({"retired_from_active":retired,"archived_versions":len(archive["entries"]),"published_articles":archive["confirmed_published_articles_total"],"remaining_active":len(watch["entries"])}))
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=ROOT);a=p.parse_args();run(a.root)
