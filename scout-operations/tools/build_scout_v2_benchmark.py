#!/usr/bin/env python3
"""Deterministic, privacy-safe 100-case Scout evaluation sampling.

All cases are public DOI identities. Never label a 'truth' from Scout's own
predictions; human independent reference labels must be collected PRIVATELY.
"""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"scout-operations/scout-v2-benchmark-100.json"
SCHEMA="reach-scout-v2-blinded-benchmark-v1"
TARGETS=[
    ("known_reach_identity",20),("ambiguous_identity",20),
    ("index_negative_original",20),("preprint_version_family",10),
    ("monthly_original",10),("historical_datacite",10),
    ("independent",5),("monthly_related",5)
]
RISK_CONTROL=["10.1007/s12035-019-01667-w","10.1007/s00330-020-07133-9"]

def read_sha(root,rel):
    b=(root/rel).read_bytes()
    return json.loads(b),hashlib.sha256(b).hexdigest()

def create(root=ROOT):
    preflight,pre_sha=read_sha(root,"scout-operations/unified-source-preflight.json")
    routing,route_sha=read_sha(root,"scout-operations/historical-crossref-screening/actionable-routing.json")
    repairs,repair_sha=read_sha(root,"scout-operations/reconciliation-repair-worklist.json")
    by_route={x["doi"]:x["outcome"] for x in routing["entries"]}
    candidates=preflight["cases"]
    use=set()
    groups={}
    control=set(RISK_CONTROL)
    def group_filter(label,c):
        lane=c["discovery_lane"]
        decision=c["effective_identity_or_preflight"]
        if label=="known_reach_identity":
            return lane=="historical_crossref" and decision=="EXISTING_IN_REACH_VERIFIED_BULK"
        if label=="ambiguous_identity":
            return lane=="historical_crossref" and decision=="IDENTITY_REVIEW_REQUIRED_FROM_BULK"
        if label=="index_negative_original":
            return (lane=="historical_crossref" and
                    by_route.get(c["doi"])=="NOT_FOUND_IN_REACH_INDEX" and
                    decision!="PREPRINT_HOLD")
        if label=="preprint_version_family":
            return decision=="PREPRINT_HOLD"
        if label=="monthly_original":return lane=="monthly_api"
        if label=="historical_datacite":return lane=="historical_datacite"
        if label=="independent":return lane=="independent"
        if label=="monthly_related":return lane=="monthly_related_outputs"
        return False
    for label,n in TARGETS:
        options=[c for c in candidates if group_filter(label,c)
                 and c["discovery_lane"]+":"+c["doi"] not in use]
        # Ensure two previously identified source-attribution anomalies get
        # explicit independent human review without asserting their gold labels.
        if label=="index_negative_original":
            forced=[c for c in options if c["doi"] in control]
            if len(forced)!=len(control):
                raise ValueError("Required independent-attribution test controls missing")
            options=forced+[c for c in options if c["doi"] not in control]
        else:
            forced=[]
        scored=sorted((c for c in options if c not in forced),
               key=lambda c:hashlib.sha256((label+":"+c["doi"]).encode()).hexdigest())
        picked=(forced+scored)[:n]
        if len(picked)!=n:raise ValueError("Not enough source cases for "+label+": "+str(len(picked)))
        for c in picked:use.add(c["discovery_lane"]+":"+c["doi"])
        groups[label]=[{"case_id":c["discovery_lane"]+":"+c["doi"],
                        "doi":c["doi"],"source":c["discovery_lane"],
                        "shared_engine_preflight":c["effective_identity_or_preflight"],
                        "recorded_research_status":c["recorded_status_unchanged"],
                        "stratum":label,
                        "private_independent_gold_label":"NOT_COLLECTED",
                        "private_reviewer_minutes":"NOT_COLLECTED",
                        "source_evidence_expected":True}
                        for c in picked]
    rows=[x for label,_ in TARGETS for x in groups[label]]
    if len(rows)!=100 or len(set(x["case_id"] for x in rows))!=100:
        raise ValueError("Benchmark sample not 100 unique lane DOI cases")
    return {"schema":SCHEMA,"source_sha256":{"preflight":pre_sha,"crossref_routing":route_sha,
                                             "repair_worklist":repair_sha},
            "sample_size":100,"strata_counts":dict(Counter(x["stratum"] for x in rows)),
            "controls_source_award_ambiguity":RISK_CONTROL,
            "human_truth_labels_collected":0,
            "candidate_identity_only":True,
            "note":"This is a blinded review sample, NOT an accuracy score or a newly proposed public Scout feed. Keep reference labels/reviewer minutes in an authorized private file; do not publish private reviewer decisions.",
            "cases":rows}

def main():
    report=create()
    text=json.dumps(report,indent=2,ensure_ascii=False)+"\n"
    if not OUT.exists() or OUT.read_text(encoding="utf-8")!=text:
        OUT.write_text(text,encoding="utf-8")
    print(json.dumps({"selected":len(report["cases"]),
                      "groups":report["strata_counts"],
                      "independent_truth_labels":report["human_truth_labels_collected"]},indent=2))

if __name__=="__main__":main()
