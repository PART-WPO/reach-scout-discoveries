#!/usr/bin/env python3
"""Read-only deterministic Crossref original triage; no research/approval claims."""
import argparse, csv, hashlib, json, re
from collections import Counter
from pathlib import Path
from wpo_awards import is_wpo_459, oar_segment
from special_publication_types import special_publication_type
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
 """459 is a confirmed WPO funding code; other OAR codes are not."""
 segments={oar_segment(a) for a in (awards or [])}
 segments.discard(None)
 if "459" in segments:
  return "CONFIRMED_WPO_459"
 if "432" in segments:
  return "CI_432_NEEDS_PROJECT_PROOF"
 if segments:
  return "NON_WPO_OAR_AWARD"
 return "INCONCLUSIVE"
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
   if signal in ("CONFIRMED_WPO_459",):
    lane,rank,action="HUMAN_REVIEW_FAST_SCREEN_DUE",85,"459 is a WPO funding code. Reuse source evidence and confirm exact published DOI, publisher-deposited 459 award, public identity and preprint gates. Route verified WPO outputs to New Candidate; only unresolved attribution to Needs Investigation."
   elif signal=="CI_432_NEEDS_PROJECT_PROOF":
    lane,rank,action="NON_459_PROJECT_EVIDENCE_CHECK",30,"One specific SPARK primary-project check; refer only with credible WPO project scope, otherwise document evidence-limited decision"
   else:
    lane,rank,action="WAIT_FOR_NEW_EVIDENCE",10,"Unresolved earlier hold without a verified 459 lead: do not repeat original attribution searches unless source evidence materially changes"
  elif lane in ("NOVEL_IDENTITY_RESEARCH","BOUNDED_IDENTITY_REVIEW") and disposition=="PREPRINT_HOLD":
   lane,rank,action="WAIT_FOR_NEW_EVIDENCE",10,"Original preprint remains monthly watchlist; do not re-research hourly"
  preprint=preprints.get(d)
  published=sorted(set(norm(x) for x in (preprint or {}).get("verified_published_dois",[]) if x))
  if lane=="NOVEL_IDENTITY_RESEARCH" and signal=="CI_432_NEEDS_PROJECT_PROOF":
   rank,action=25,"432 is not direct WPO attribution: verify a specific SPARK primary award/project before proposing a reviewer item"
  elif lane=="NOVEL_IDENTITY_RESEARCH" and signal=="CONFIRMED_WPO_459":
   rank,action=90,"459 program code confirms WPO funding when deposited for this exact article. Fast-check official publisher award, REACH/Scout/IR duplicate and preprint gates; send verified published output as New Candidate in THIS mission, not Needs Investigation solely for WPO connection. Reviewer selects the SPARK parent."
  if preprint and lane!="EXISTING_REACH_FAST_EXIT":
   lane="PREPRINT_PUBLISHED_VERSION_LEAD" if published else "PREPRINT_WATCHLIST_HOLD"
   rank=15 if published else 5
   action=("Investigate official published DOI(s) as separate identities; never stage preprint DOI" if published else "Await scheduled publication recheck; no hourly deep research")
  # Editorial notices are not ordinary original research. Preserve verified
  # REACH/Scout duplicate exits, preprint holds, and existing evidence holds.
  # Route them to a distinct low-priority human eligibility question instead.
  notice=special_publication_type(e.get("title"))
  if notice and lane in ("NOVEL_IDENTITY_RESEARCH","HUMAN_REVIEW_FAST_SCREEN_DUE","BOUNDED_IDENTITY_REVIEW","NON_459_PROJECT_EVIDENCE_CHECK"):
   lane,rank="SPECIAL_PUBLICATION_TYPE_REVIEW",12
   action=("Editorial notice ("+notice+"): verify distinct output eligibility, parent-article identity "
           "and any prior REACH/Scout notice before proposing a human-review item. "
           "Do not auto-stage as an original scientific publication.")
  items.append({"preprint_status":(preprint or {}).get("status"),"already_in_public_scout_queue":bool(public_matches),
  "matched_public_review_locations":public_matches,"special_publication_type":notice or None,"one_mission_disposition_required":lane in (
  "NOVEL_IDENTITY_RESEARCH","HUMAN_REVIEW_FAST_SCREEN_DUE","BOUNDED_IDENTITY_REVIEW",
  "NON_459_PROJECT_EVIDENCE_CHECK"),"verified_published_dois":published,"doi":d,"title":e.get("title"),"lane":lane,"priority":rank,"next_action":action,"funding_signal":signal,"crossref_structured_award_numbers":awards,"wpo_459_award_numbers":[a for a in awards if is_wpo_459(a)],"award_evidence_source_batches":sorted(ev.get("source_batches",[])),"award_match_basis":"Historical Crossref publisher-deposited award for exact DOI; 459 identifies WPO funding. Exact SPARK parent and output identity still require verification before addition","prior_disposition":disposition,"scout_overlap":bool(e.get("scout_overlap")),"verified_reach_uid":e["bulk_identity_gate"].get("verified_reach_uid"),"private_hub_review":"NOT_VERIFIED"})
 items.sort(key=lambda x:(-x["priority"],x["doi"]))
 due=[x for x in items if x["one_mission_disposition_required"]]
 return {"schema":"reach-scout-crossref-candidate-queue-v2",
 "purpose":"Read-only selection; not completed research or approval",
 "completion_target":"Each hourly mission handles at least one full novel-output screening through a concrete disposition or public human-review handoff. Skipped known records do not count; technical blockers must be reported, not represented as completed.",
 "one_mission_actionable_original_count":len(due),
 "special_publication_type_review_count":sum(x["lane"]=="SPECIAL_PUBLICATION_TYPE_REVIEW" for x in items),
 "special_publication_review_preview":[{"doi":x["doi"],"title":x["title"],"type":x["special_publication_type"],"action":x["next_action"]} for x in items if x["lane"]=="SPECIAL_PUBLICATION_TYPE_REVIEW"][:8],
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
