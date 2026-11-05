#!/usr/bin/env python3
"""Summarize immutable Scout decision checkpoints; no authority to close cases."""
import hashlib
import json
from collections import Counter
from pathlib import Path

from decision_pipeline import VERSION, check_index_fresh, evaluate, read_json, sha_bytes

ROOT = Path(__file__).resolve().parents[2]
CASES = ROOT/"scout-operations/research-decision-cases.json"
INDEX = ROOT/"scout-operations/identity-cache/public-identity-index.json"
OUTPUT = ROOT/"scout-operations/research-decision-rollup.json"


def build(root=ROOT):
    cases = read_json(root / CASES.relative_to(ROOT))
    index = read_json(root / INDEX.relative_to(ROOT))
    check_index_fresh(root, index)
    if cases.get("schema") != "reach-scout-decision-cases-v1":
        raise ValueError("Unexpected research case schema")
    rows = []
    for case in cases["cases"]:
        result = evaluate(case,index)
        signature = sha_bytes(json.dumps({"case":case,"index":index["source_fingerprint"],
            "version":VERSION}, sort_keys=True).encode())
        id_hash = sha_bytes(result["doi"].encode())[:16]
        rel = Path("scout-operations/case-checkpoints") / ("doi-"+id_hash) / ("rev-"+signature[:20]+".json")
        checkpoint = read_json(root / rel)
        if checkpoint.get("input_fingerprint") != signature or checkpoint.get("evaluation") != result:
            raise ValueError("Immutable decision checkpoint mismatch: "+str(rel))
        if checkpoint.get("human_decision_modified") is not False:
            raise ValueError("Unexpected human-decision mutation: "+str(rel))
        exhausted = case.get("research_budget_exhausted") is True
        if result["decision"] == "PREPRINT_HOLD":
            next_action = "MONTHLY_PREPRINT_WATCHLIST"
        elif result["decision"] == "EXISTING_IN_REACH":
            next_action = "VERIFY_EXISTING_ORIGINAL_IN_LEDGER_KEEP_EXPANSION_OPEN"
        elif result["decision"] == "EXISTING_SCOUT_CANDIDATE":
            next_action = "LINK_EXISTING_PUBLIC_REVIEW_UNIT_NO_DUPLICATE"
        elif result["decision"] == "READY_FOR_VALIDATED_DRAFT_PREFLIGHT":
            next_action = "REVIEW_VALIDATED_DRAFT_GATES_NO_AUTOSTAGING"
        elif exhausted:
            next_action = "BOUNDED_RESEARCH_COMPLETE_NEEDS_HUMAN_ASSESSMENT"
        else:
            next_action = "TARGETED_RESEARCH_OR_IDENTITY_VERIFICATION"
        rows.append({"doi":result["doi"],"decision":result["decision"],
                     "research_rounds":result["research_rounds"],"next_action":next_action,
                     "checkpoint_path":rel.as_posix(),
                     "expansion_status":"UNCHANGED_RESEARCH_SEED",
                     "public_scout_candidate_created":False,
                     "private_hub_decision":"NOT_VERIFIED"})
    counts = dict(sorted(Counter(x["decision"] for x in rows).items()))
    actions = dict(sorted(Counter(x["next_action"] for x in rows).items()))
    report = {"schema":"reach-scout-research-decision-rollup-v1",
              "source_cases_sha256":hashlib.sha256((root/CASES.relative_to(ROOT)).read_bytes()).hexdigest(),
              "identity_index_fingerprint":index["source_fingerprint"],
              "cases_evaluated":len(rows),"decision_counts":counts,"next_action_counts":actions,
              "private_hub_import":"NOT_VERIFIED","human_approvals":"NOT_VERIFIED",
              "public_reach_additions":"NOT_VERIFIED","automatically_staged":0,
              "original_terminal_statuses_modified":0,"expansion_seed_closures":0,
              "note":"Conservative research evidence processing only. Formal triage terminal closure requires independent proofs; no automatic human handoff is implied.",
              "cases":rows}
    return report


def main():
    report=build()
    rendered=json.dumps(report,indent=2,ensure_ascii=False)+"\n"
    if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8")!=rendered:
        OUTPUT.write_text(rendered,encoding="utf-8")
    print(json.dumps({"cases_evaluated":report["cases_evaluated"],
                      "next_action_counts":report["next_action_counts"]},indent=2))

if __name__=="__main__":
    main()
