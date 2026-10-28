#!/usr/bin/env python3
"""Choose Scout's next research workstream from GitHub-backed API backlog state.

This is a deterministic *routing recommendation*, not a Scout run, review
decision, or evidence of finished research. Runs during coverage refreshes.
"""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"scout-operations/active-workstream.json"

def read(rel):
    p=ROOT/rel
    if not p.exists():return None
    return json.loads(p.read_text(encoding="utf-8"))

def decide(monthly_manifest,monthly_coverage,historical_manifest,historical_coverage,historical_manifest_sha=""):
    monthly_total=int((monthly_manifest or {}).get("candidate_rows",0))
    monthly_checked=int((monthly_coverage or {}).get("checked",0))
    monthly_received=int((monthly_coverage or {}).get("received",0))
    monthly_missing=int((monthly_coverage or {}).get("missing_from_ledger",0))
    monthly_unfinished=max(0,monthly_total-monthly_checked,monthly_received-monthly_checked,monthly_missing)
    monthly_reconciled=(monthly_total==monthly_received and monthly_unfinished==0)
    hist_rows=int((historical_manifest or {}).get("candidate_rows",0))
    h_total=int((historical_coverage or {}).get("total_distinct_dois",0))
    h_done=int((historical_coverage or {}).get("fully_investigated",0))
    h_left=int((historical_coverage or {}).get("remaining",0))
    hist_matches=bool(historical_manifest_sha and historical_coverage and
        historical_coverage.get("source_manifest_sha256")==historical_manifest_sha)
    hist_complete=(not historical_manifest and not historical_coverage) or (
        bool(historical_coverage) and hist_matches and
        historical_coverage.get("research_complete") is True and
        h_left==0 and h_done==h_total)
    # Missing coverage is a reason to investigate/reconcile, not evidence of zero backlog.
    hist_pending=bool(historical_manifest) and not hist_complete
    if not monthly_reconciled:
        mode="monthly_api_triage"
        reason="Unresolved or unaccounted monthly DataCite/Crossref API candidates"
    elif hist_pending:
        mode="historical_api_triage"
        reason="Unfinished historical DataCite API test/backfill DOI cases"
    else:
        mode="normal_historical_discovery"
        reason="Both API research queues are accounted for and cleared"
    return {
        "schema":"reach-scout-workstream-v1",
        "mode":mode,
        "reason":reason,
        "switch_policy":"monthly API > historical API test backlog > normal SPARK historical discovery",
        "monthly_api":{"raw_records":monthly_total,"recorded_received":monthly_received,
                       "research_completed":monthly_checked,"remaining_or_untracked":monthly_unfinished},
        "historical_api":{"raw_batch_rows":hist_rows,"distinct_dois":h_total,
                          "research_completed":h_done,
                          "remaining_or_untracked":max(h_left,1 if hist_pending and not hist_matches else 0),
                          "coverage_matches_source_manifest":hist_matches},
        "note":"Priority is reevaluated each scheduled Scout mission. GitHub Actions do NOT instantly launch ChatGPT Scout missions. Complete research requires evidence-backed ledger status."
    }

def main():
    m=read("api-discoveries/manifest.json")
    mc=read("scout-operations/coverage.json")
    h=read("api-discoveries/historical/manifest.json")
    hc=read("scout-operations/historical-coverage.json")
    sha=hashlib.sha256((ROOT/"api-discoveries/historical/manifest.json").read_bytes()).hexdigest() if h else ""
    result=decide(m,mc,h,hc,sha)
    new=json.dumps(result,indent=2,sort_keys=True)+"\n"
    if not OUT.exists() or OUT.read_text(encoding="utf-8")!=new:
        OUT.write_text(new,encoding="utf-8")
    print(json.dumps(result,indent=2))

if __name__=="__main__":main()
