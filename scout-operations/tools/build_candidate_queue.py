#!/usr/bin/env python3
"""Read-only deterministic Crossref original triage; no research/approval claims."""
import argparse, csv, hashlib, json, re
from collections import Counter
from pathlib import Path
ROUTING="scout-operations/historical-crossref-screening/actionable-routing.json"
REGISTRY="scout-operations/research-outcome-registry.json"
OUTPUT="scout-operations/crossref-candidate-queue.json"
MANIFEST="api-discoveries/historical-crossref/manifest.json"
WATCHLIST="scout-operations/preprint-watchlist.json"
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
def verified_public_scout_matches(entry):
 # Exact DOI AND normalized title must both agree before the previous
 # public Scout proposal is reused. A vague "scout_overlap" flag alone
 # is never sufficient to suppress a potentially novel output.
 matches=[]
 for m in entry.get("scout_public_queue_matches",[]) or []:
  if (m.get("source") in {"SCOUT_PUBLISHED","SCOUT_INBOX"} and
      {"exact_doi","normalized_title"}.issubset(set(m.get("basis",[]))) and
      str(m.get("location","")).startswith("scout-discoveries/")):
   matches.append(m["location"])
 return sorted(set(matches))

def build(routing,registry,award_evidence=None,preprints=None):
 preprints=preprints or {}
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
  public_matches=verified_public_scout_matches(e)
  ev=award_evidence.get(d,{})
  awards=sorted(ev.get("awards",[]))
  signal=funding_signal(awards)
  prior=cases.get("doi:"+d,{})
  disposition=prior.get("latest_operational_disposition")
  if gate=="VERIFIED_EXISTING_REACH":
   assert e["bulk_identity_gate"].get("verified_reach_uid")
   lane,rank,action="EXISTING_REACH_FAST_EXIT",0,"Already in REACH: skip original; keep independent expansion"
  elif public_matches:
   # Reuse the previous public review unit even if a historical source
   # describes the DOI as novel, awaiting project proof, or on hold.
   # A public proposal is NOT proof of private Hub import/approval.
   lane,rank,action="ALREADY_IN_SCOUT_REVIEW_FAST_EXIT",0,"Already in Scout's public review pipeline: do not repeat original research or create another proposal; keep independent expansion"
  elif gate=="NEEDS_IDENTITY_REVIEW":
   lane,rank,action="BOUNDED_IDENTITY_REVIEW",70,"Complete one bounded identity/version check and record a final screening decision in this mission"
  elif gate=="NO_PUBLIC_REACH_MATCH":
   lane,rank,action="NOVEL_IDENTITY_RESEARCH",60,"Complete fast published/identity check, then route plausible output to Needs Investigation in the same mission"
  else: raise ValueError("Unknown gate: "+str(gate))
  if lane in ("NOVEL_IDENTITY_RESEARCH","BOUNDED_IDENTITY_REVIEW") and disposition=="PROJECT_EVIDENCE_HOLD":
   if signal in ("POSSIBLE_WPO_459","MIXED_432_459"):
    lane,rank,action="HUMAN_REVIEW_FAST_SCREEN_DUE",85,"Prior research stopped at unverified funding. Reuse its source evidence; complete identity/publication checks and route plausible 459 WPO lead to Needs Investigation in this mission, not another generic project-proof round"
   elif signal=="CI_432_NEEDS_PROJECT_PROOF":
    lane,rank,action="NON_459_PROJECT_EVIDENCE_CHECK",30,"One specific SPARK primary-project check; refer only with credible WPO project scope, otherwise document evidence-limited decision"
   else:
    lane,rank,action="WAIT_FOR_NEW_EVIDENCE",10,"Unresolved earlier hold without a specific WPO award clue: do not repeat original attribution searches unless source evidence materially changes"
  elif lane in ("NOVEL_IDENTITY_RESEARCH","BOUNDED_IDENTITY_REVIEW") and disposition=="PREPRINT_HOLD":
   lane,rank,action="WAIT_FOR_NEW_EVIDENCE",10,"Original preprint remains monthly watchlist; do not re-research hourly"
  preprint=preprints.get(d)
  published=sorted(set(norm(x) for x in (preprint or {}).get("verified_published_dois",[]) if x))
  if lane=="NOVEL_IDENTITY_RESEARCH" and signal=="MIXED_432_459":
   rank,action=78,"459 WPO cue is strong, but distinguish CI umbrella; fast-screen then send plausible cases to Needs Investigation"
  elif lane=="NOVEL_IDENTITY_RESEARCH" and signal=="CI_432_NEEDS_PROJECT_PROOF":
   rank,action=25,"432 is not direct WPO attribution: verify a specific SPARK primary award/project before proposing a reviewer item"
  elif lane=="NOVEL_IDENTITY_RESEARCH" and signal=="POSSIBLE_WPO_459":
   rank,action=90,"Strong WPO award signal: fast-check publisher, current REACH/Scout/IR duplicate and preprint gates; send plausible distinct output to Needs Investigation with confidence score in THIS mission. Full project proof belongs to human review"
  if preprint and lane!="EXISTING_REACH_FAST_EXIT":
   lane="PREPRINT_PUBLISHED_VERSION_LEAD" if published else "PREPRINT_WATCHLIST_HOLD"
   rank=15 if published else 5
   action=("Investigate official published DOI(s) as separate identities; never stage preprint DOI" if published else "Await scheduled publication recheck; no hourly deep research")
  items.append({"preprint_status":(preprint or {}).get("status"),"already_in_public_scout_queue":bool(public_matches),
  "matched_public_review_locations":public_matches,"one_mission_disposition_required":lane in (
  "NOVEL_IDENTITY_RESEARCH","HUMAN_REVIEW_FAST_SCREEN_DUE","BOUNDED_IDENTITY_REVIEW",
  "NON_459_PROJECT_EVIDENCE_CHECK"),"verified_published_dois":published,"doi":d,"title":e.get("title"),"lane":lane,"priority":rank,"next_action":action,"funding_signal":signal,"crossref_structured_award_numbers":awards,"award_evidence_source_batches":sorted(ev.get("source_batches",[])),"award_match_basis":"Historical Crossref feed structured award, matched to SPARK primary award at intake; output-to-project relevance still unverified","prior_disposition":disposition,"scout_overlap":bool(e.get("scout_overlap")),"verified_reach_uid":e["bulk_identity_gate"].get("verified_reach_uid"),"private_hub_review":"NOT_VERIFIED"})
 items.sort(key=lambda x:(-x["priority"],x["doi"]))
 due=[x for x in items if x["one_mission_disposition_required"]]
 return {"schema":"reach-scout-crossref-candidate-queue-v2",
 "purpose":"Read-only selection; not completed research or approval",
 "completion_target":"Each hourly mission handles at least one full novel-output screening through a concrete disposition or public human-review handoff. Skipped known records do not count; technical blockers must be reported, not represented as completed.",
 "one_mission_actionable_original_count":len(due),
 "next_one_mission_original_preview":[{
   "doi":x["doi"],"lane":x["lane"],"priority":x["priority"],
   "funding_signal":x["funding_signal"],"required_outcome":"FINISH_ORIGINAL_SCREENING_DECISION_THIS_RUN",
   "action":x["next_action"]} for x in due[:8]],
 "total":len(items),"lane_counts":dict(sorted(Counter(x["lane"] for x in items).items())),
 "items":items,"original_dispositions_changed":0,"new_review_proposals":0}
def load_preprints(root):
 w=load(root,WATCHLIST); result={}
 for e in w["entries"]:
  d=norm(e["preprint_doi"])
  if d in result: raise ValueError("Duplicate preprint watchlist DOI: "+d)
  result[d]=e
 return result
def main():
 p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[2]);p.add_argument("--check",action="store_true");a=p.parse_args()
 awards,award_sources=load_award_evidence(a.root)
 q=build(load(a.root,ROUTING),load(a.root,REGISTRY),awards,load_preprints(a.root))
 q["source_sha256"]={f:sha(a.root/f) for f in (ROUTING,REGISTRY)}
 q["source_sha256"].update(award_sources)
 q["source_sha256"][WATCHLIST]=sha(a.root/WATCHLIST)
 q["funding_signal_counts"]=dict(sorted(Counter(x["funding_signal"] for x in q["items"]).items()))
 dest=a.root/OUTPUT;raw=json.dumps(q,indent=2,ensure_ascii=False)+"\n"
 if a.check: assert dest.is_file() and dest.read_text()==raw,"Queue stale"
 else: dest.write_text(raw)
 print(json.dumps({"total":q["total"],"lane_counts":q["lane_counts"]}))
if __name__=="__main__":main()
