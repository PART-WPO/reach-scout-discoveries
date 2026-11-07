#!/usr/bin/env python3
"""Read-only deterministic Crossref original triage; no research/approval claims."""
import argparse, csv, hashlib, json, re
from collections import Counter
from pathlib import Path
ROUTING="scout-operations/historical-crossref-screening/actionable-routing.json"
REGISTRY="scout-operations/research-outcome-registry.json"
OUTPUT="scout-operations/crossref-candidate-queue.json"
MANIFEST="api-discoveries/historical-crossref/manifest.json"
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(root,p): return json.loads((root/p).read_text())
def norm(s):
 s=str(s or "").strip().lower()
 for prefix in ("https://doi.org/","http://doi.org/","doi:"):
  if s.startswith(prefix): s=s[len(prefix):]
 return s
def funding_signal(awards):
 found=set()
 for award in awards or []:
  m=re.fullmatch(r"NA\d{2}OARX?(432|459)C?\d{4,}(?:-[A-Z0-9]+)?",str(award).strip().upper())
  if m: found.add(m.group(1))
 return "MIXED_432_459" if len(found)>1 else ("POSSIBLE_WPO_459" if "459" in found else ("CI_432_NEEDS_PROJECT_PROOF" if "432" in found else "INCONCLUSIVE"))
def load_award_evidence(root):
 manifest=load(root,MANIFEST)
 evidence={}; source={MANIFEST:sha(root/MANIFEST)}
 for batch in manifest["batches"]:
  p=batch["path"]; file=root/p
  digest=sha(file)
  if digest!=batch["sha256"]: raise ValueError("Crossref batch SHA mismatch: "+p)
  source[p]=digest
  with file.open(newline="",encoding="utf-8-sig") as f:
   rows=list(csv.DictReader(f))
  if len(rows)!=batch["record_count"]: raise ValueError("Crossref batch row count mismatch: "+p)
  for row in rows:
   d=norm(row.get("DOI"))
   if not d: continue
   awards=[a.strip().upper() for a in re.split(r"[;,]",row.get("NOAA Award Number(s)","")) if a.strip()]
   old=evidence.setdefault(d,{"awards":set(),"source_batches":set()})
   old["awards"].update(awards);old["source_batches"].add(p)
 return evidence,source
def build(routing,registry,award_evidence=None):
 award_evidence=award_evidence or {}
 assert routing["total"]==len(routing["entries"])
 assert routing["bulk_identity_screening"]["source_dois"]==len(routing["entries"])
 cases={x["identity"]:x for x in registry.get("cases",[])}
 items=[];seen=set()
 for e in routing["entries"]:
  d=norm(e["doi"])
  assert d.startswith("10.") and d not in seen
  seen.add(d)
  gate=e["bulk_identity_gate"]["status"]
  if gate=="VERIFIED_EXISTING_REACH":
   assert e["bulk_identity_gate"].get("verified_reach_uid")
   lane,rank,action="EXISTING_REACH_FAST_EXIT",0,"No original research; separate project-linked expansion only"
  elif gate=="NEEDS_IDENTITY_REVIEW":
   lane,rank,action="BOUNDED_IDENTITY_REVIEW",70,"One identity/version check; no novelty assumption"
  elif gate=="NO_PUBLIC_REACH_MATCH":
   lane,rank,action="NOVEL_IDENTITY_RESEARCH",60,"Verify eligibility, primary SPARK project and funding"
  else: raise ValueError("Unknown gate: "+str(gate))
  prior=cases.get("doi:"+d,{})
  disposition=prior.get("latest_operational_disposition")
  if lane!="EXISTING_REACH_FAST_EXIT" and disposition in ("PROJECT_EVIDENCE_HOLD","PREPRINT_HOLD"):
   lane,rank,action="WAIT_FOR_NEW_EVIDENCE",10,"Reopen only on new evidence or official publication"
  ev=award_evidence.get(d,{})
  awards=sorted(ev.get("awards",[]))
  signal=funding_signal(awards)
  if lane=="NOVEL_IDENTITY_RESEARCH" and signal=="MIXED_432_459":
   rank,action=65,"Verify exact primary WPO project and distinguish CI umbrella"
  if lane=="NOVEL_IDENTITY_RESEARCH" and signal=="CI_432_NEEDS_PROJECT_PROOF":
   rank,action=25,"Bounded primary SPARK check; no umbrella grant attribution"
  elif lane=="NOVEL_IDENTITY_RESEARCH" and signal=="POSSIBLE_WPO_459": rank=80
  items.append({"doi":d,"title":e.get("title"),"lane":lane,"priority":rank,"next_action":action,"funding_signal":signal,"crossref_structured_award_numbers":awards,"award_evidence_source_batches":sorted(ev.get("source_batches",[])),"award_match_basis":"Historical Crossref feed structured award, matched to SPARK primary award at intake; output-to-project relevance still unverified","prior_disposition":disposition,"scout_overlap":bool(e.get("scout_overlap")),"verified_reach_uid":e["bulk_identity_gate"].get("verified_reach_uid"),"private_hub_review":"NOT_VERIFIED"})
 items.sort(key=lambda x:(-x["priority"],x["doi"]))
 return {"schema":"reach-scout-crossref-candidate-queue-v1","purpose":"Read-only selection; not completed research or approval","total":len(items),"lane_counts":dict(sorted(Counter(x["lane"] for x in items).items())),"items":items,"original_dispositions_changed":0,"new_review_proposals":0}
def main():
 p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[2]);p.add_argument("--check",action="store_true");a=p.parse_args()
 awards,award_sources=load_award_evidence(a.root)
 q=build(load(a.root,ROUTING),load(a.root,REGISTRY),awards)
 q["source_sha256"]={f:sha(a.root/f) for f in (ROUTING,REGISTRY)}
 q["source_sha256"].update(award_sources)
 q["funding_signal_counts"]=dict(sorted(Counter(x["funding_signal"] for x in q["items"]).items()))
 dest=a.root/OUTPUT;raw=json.dumps(q,indent=2,ensure_ascii=False)+"\n"
 if a.check: assert dest.is_file() and dest.read_text()==raw,"Queue stale"
 else: dest.write_text(raw)
 print(json.dumps({"total":q["total"],"lane_counts":q["lane_counts"]}))
if __name__=="__main__":main()
