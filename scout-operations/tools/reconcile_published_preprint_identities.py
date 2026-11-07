#!/usr/bin/env python3
"""Read-only, SHA-verified public REACH/NOAA IR reconciliation for active published preprints."""
import argparse, json, sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"scout-operations/tools"))
from ir_reach_identity import verified_snapshot, identity_check
from decision_pipeline import lookup, norm_title, norm_doi, norm_url
WATCH="scout-operations/preprint-watchlist.json"
LEADS="scout-operations/preprint-publication-leads.json"
REPORT="scout-operations/preprint-13-identity-reconciliation.json"
def reconcile(root):
 watch=json.loads((root/WATCH).read_text()); leads=json.loads((root/LEADS).read_text())
 leadmap={norm_doi(x["published_doi"]):x for x in leads["entries"]}
 public,ir=verified_snapshot(root)
 result=[]
 for e in watch["entries"]:
  finals=e.get("verified_published_dois") or []
  if not finals:continue
  for final in finals:
   final=norm_doi(final); lead=leadmap.get(final,{})
   title=e.get("title","")
   direct=identity_check(public,ir,final,title=title)
   preprint=lookup(public,doi=e["preprint_doi"],title=title)
   final_doi_hits=[m for m in direct["matches"] if m["source"]=="REACH" and "exact_doi" in m["match_bases"]]
   official=direct["noaa_ir_reach_check"]
   ir_uid=official.get("match_uid") if official.get("status")=="VERIFIED_OFFICIAL_IR_DOI_TO_EXISTING_REACH_URL" else None
   verified_uids={m["identity"] for m in final_doi_hits}
   if ir_uid:verified_uids.add(ir_uid)
   # An exact final DOI or verified official IR link is required; title-only and preprint-only are holds.
   if len(verified_uids)==1 and (not final_doi_hits or all(norm_title(m["title"])==norm_title(title) for m in final_doi_hits)):
    classification="CONFIRMED_REACH_FINAL_IDENTITY" if (ir_uid or (final_doi_hits and norm_title(title))) else "VERSION_REVIEW_REQUIRED"
   elif verified_uids or any(m["source"]=="REACH" for m in direct["matches"]+preprint["matches"]):
    classification="VERSION_REVIEW_REQUIRED"
   elif any(m["source"].startswith("SCOUT_") for m in direct["matches"]):
    classification="IN_PUBLIC_SCOUT_FEED"
   else:classification="NO_CONFIRMED_PUBLIC_REACH_MATCH"
   result.append({"preprint_doi":norm_doi(e["preprint_doi"]),"published_doi":final,"title":title,
    "classification":classification,"confirmed_reach_uids":sorted(verified_uids) if classification=="CONFIRMED_REACH_FINAL_IDENTITY" else [],
    "final_doi_reach_matches":final_doi_hits,"final_identity_status":direct["status"],
    "official_ir_reach_check":official,"preprint_identity_matches":preprint["matches"],
    "published_lead_previous_status":lead.get("status"),"private_hub_status":"NOT_VERIFIED"})
 counts=dict(sorted(Counter(x["classification"] for x in result).items()))
 doc={"schema":"reach-scout-targeted-preprint-identity-reconciliation-v1","scope":"All active preprint records with verified published DOIs","source_public_reach_sha256":public["sources"]["reach_cache_sha256"],"public_identity_fingerprint":public["source_fingerprint"],"total":len(result),"counts":counts,"entries":result,"policy":"Read-only evidence screening. Do not retire title-only, preprint-only or conflicting-version matches. No private Hub or REACH write."}
 (root/REPORT).write_text(json.dumps(doc,indent=2,ensure_ascii=False)+"\n")
 print(json.dumps({"total":len(result),"counts":counts}))
 return doc
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=ROOT);a=p.parse_args();reconcile(a.root)
