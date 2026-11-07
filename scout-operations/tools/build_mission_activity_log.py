#!/usr/bin/env python3
"""Append-only, evidence-pinned Scout mission activity observations.

Observations are not inferred human actions, research completions, or time savings.
An unchanged source fingerprint produces no additional event.
"""
import argparse,hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOG="scout-operations/scout-mission-activity-log.json"
SCORE="scout-operations/scout-throughput-scorecard.json"
REG="scout-operations/research-outcome-registry.json"
def digest(data):return hashlib.sha256(data).hexdigest()
def build(root,now=None):
 score_bytes=(root/SCORE).read_bytes();score=json.loads(score_bytes)
 registry_bytes=(root/REG).read_bytes();reg=json.loads(registry_bytes)
 if score["source_sha256"][REG]!=digest(registry_bytes):raise ValueError("Scorecard registry source is stale")
 p=root/LOG
 log=json.loads(p.read_text()) if p.exists() else {"schema":"reach-scout-mission-activity-log-v1","events":[]}
 if log["schema"]!="reach-scout-mission-activity-log-v1":raise ValueError("Unknown activity log schema")
 events=log["events"]
 fingerprints={e["evidence_fingerprint"] for e in events}
 # Event identity is deterministic for identical verified inputs; reruns never inflate throughput.
 fingerprint=digest((digest(score_bytes)+":"+digest(registry_bytes)).encode())
 if fingerprint not in fingerprints:
  metrics={"crossref_verified_completed":score["verified_original_research"]["crossref_completed"],
   "datacite_verified_completed":score["verified_original_research"]["datacite_completed"],
   "crossref_expansion_verified_completed":score["separate_related_output_expansion"]["crossref_verified_completed"],
   "public_scout_feed_rows":score["public_candidate_pipeline"]["public_feed_rows"],
   "research_evidence_events":reg["research_note_events"],
   "research_evidence_identities":reg["distinct_research_identities"],
   "archived_preprint_versions":score["preprint_workload"]["archived_versions"]}
  previous=events[-1]["metrics"] if events else None
  delta={k:metrics[k]-previous[k] for k in metrics} if previous else None
  event={"event_id":fingerprint[:24],"observed_at_utc":(now or datetime.now(timezone.utc)).isoformat(),
   "event_type":"VERIFIED_PUBLIC_ARTIFACT_SNAPSHOT","evidence_fingerprint":fingerprint,
   "scorecard_sha256":digest(score_bytes),"research_registry_sha256":digest(registry_bytes),
   "metrics":metrics,"delta_since_previous_observation":delta,
   "baseline_only":previous is None,
   "interpretation":"Public artifact deltas, not proof of causal mission output. Research-note event growth is not verified formal research completion; public feed rows are not Hub approvals."}
  events.append(event)
 log["events"]=events
 log["observation_count"]=len(events)
 log["last_event_id"]=events[-1]["event_id"] if events else None
 p.write_text(json.dumps(log,indent=2,ensure_ascii=False)+"\n")
 print(json.dumps({"observations":len(events),"new_observation":fingerprint not in fingerprints,"last_delta":events[-1]["delta_since_previous_observation"] if events else None}))
 return log
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=ROOT);a=p.parse_args();build(a.root)
