#!/usr/bin/env python3
"""Locally score a Scout evaluation sample against PRIVATE independent labels.

Never put private gold records or reviewer identities into the public repo.
Only aggregate metrics (no DOI or respondent-level records) may be shared
after explicit human authorization.
"""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path

LABELS={"EXISTING_IN_REACH","NEW_ELIGIBLE_WPO_OUTPUT",
        "NOT_WPO_ASSOCIATED","PREPRINT_ONLY","VERSION_AMBIGUOUS",
        "INSUFFICIENT_EVIDENCE"}
DUPLICATE_DECISIONS={"EXISTING_IN_REACH_VERIFIED_BULK",
                     "EXISTING_IN_REACH","EXISTING_IN_REACH_VERIFIED_CANONICAL_URL"}
PUBLIC=Path(__file__).resolve().parents[2]/"scout-operations/scout-v2-benchmark-100.json"

def ratio(n,d):
    return round(n/d,4) if d else None

def score(benchmark,gold):
    selected={e["case_id"]:e for e in benchmark["cases"]}
    if len(selected)!=100:
        raise ValueError("Benchmark source must include exactly 100 unique cases")
    rows={}
    for e in gold:
        k=e.get("case_id")
        if k in rows or k not in selected:
            raise ValueError("Duplicate or unknown PRIVATE benchmark case identifier")
        label=e.get("gold_label")
        if label not in LABELS:
            raise ValueError("Human gold label must be from authorized evaluation categories")
        minutes=e.get("reviewer_minutes","")
        if minutes:
            try: m=float(minutes)
            except ValueError: raise ValueError("Invalid private reviewer minutes")
            if m<0 or m>480:raise ValueError("Reviewer minutes outside expected interval")
        else:m=None
        rows[k]={"gold_label":label,"minutes":m}
    if len(rows)!=100:raise ValueError("100 gold-labelled independent cases required")
    predicted_positive=actual_positive=tp=fp=fn=tn=0
    time_sum=timed=0
    for k,g in rows.items():
        label=g["gold_label"]
        if g["minutes"] is not None:
            time_sum+=g["minutes"];timed+=1
        if label in ("VERSION_AMBIGUOUS","INSUFFICIENT_EVIDENCE"):
            continue
        predicted=selected[k]["shared_engine_preflight"] in DUPLICATE_DECISIONS
        actual=label=="EXISTING_IN_REACH"
        predicted_positive+=int(predicted)
        actual_positive+=int(actual)
        if predicted and actual:tp+=1
        elif predicted and not actual:fp+=1
        elif not predicted and actual:fn+=1
        else:tn+=1
    return {"schema":"reach-scout-v2-private-gold-aggregate-metrics-v1",
            "benchmark_size":len(rows),
            "decisions_with_timing":timed,
            "average_review_minutes":round(time_sum/timed,2) if timed else None,
            "duplicate_precision":ratio(tp,tp+fp),
            "duplicate_recall":ratio(tp,tp+fn),
            "false_duplicate_rate":ratio(fp,fp+tn),
            "undetermined_duplicate_gold_count":len(rows)-(tp+fp+fn+tn),
            "eligible_output_recall":"NOT_ESTIMABLE_FROM_CASE_CLASSIFICATION_ALONE",
            "verified_public_reach_additions":"NOT_MEASURED_BY_THIS_TEST",
            "privacy":"AGGREGATES_ONLY_NOT_APPROVED_FOR_PUBLIC_POSTING_WITHOUT_REVIEW"}

def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("--gold-private-csv",type=Path,required=True)
    args=cli.parse_args()
    with args.gold_private_csv.open(encoding="utf-8-sig",newline="") as f:
        gold=list(csv.DictReader(f))
    bench=json.loads(PUBLIC.read_text(encoding="utf-8"))
    print(json.dumps(score(bench,gold),indent=2))

if __name__=="__main__":main()
