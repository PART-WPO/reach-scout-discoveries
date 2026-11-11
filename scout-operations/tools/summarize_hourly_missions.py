#!/usr/bin/env python3
"""Separate measured ChatGPT hourly mission outcomes from GitHub backstop outcomes."""
import argparse
import json
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
from validate_hourly_mission import validate
from source_discovery_metrics import summary as source_discovery_summary

ROOT = Path(__file__).resolve().parents[2]
INPUTS = {
    "chatgpt_hourly_mission": "scout-operations/reports/hourly-missions",
    "github_guarded_crossref_backstop": "scout-operations/reports/guarded-backstop-missions",
}


def summarize(root=ROOT):
    categories = {}
    for producer, location in INPUTS.items():
        paths = sorted((root / location).glob("*.json"))
        records = []
        for path in paths:
            record = json.loads(path.read_text(encoding="utf-8"))
            errors = validate(record)
            if errors:
                raise ValueError(f"Invalid mission {path}: " + "; ".join(errors))
            if record.get("producer") != producer:
                raise ValueError(f"Mission producer mismatches directory: {path}")
            if bool(record.get("not_chatgpt_hourly_mission")) != (producer != "chatgpt_hourly_mission"):
                raise ValueError(f"Misleading ChatGPT/GitHub runner identity: {path}")
            records.append(record)
        ids = [r["mission_id"] for r in records]
        if len(ids) != len(set(ids)):
            raise ValueError("Repeated completed mission ID: " + producer)
        n = len(records)
        completed = [r for r in records if r["new_original_full_decisions"]]
        public = [r for r in records if r["handoff_status"] == "PUBLISHED_PUBLIC_SCOUT"]
        req = [r["external_requests_observed"] for r in records if r["external_requests_observed"] is not None]
        cache = [r["cache_hits_observed"] for r in records if r["cache_hits_observed"] is not None]
        cases = sorted({d.lower() for r in records for d in r["new_original_full_decisions"]})
        # A bounded negative is not a formal expansion closure. Do not treat a
        # technical/funding hold or simply zero candidates as a negative result.
        bounded_negative = [
            r for r in records
            if r["selected_expansion_seed_dois"]
            and r["research_only_holds"]
            and not r["new_expansion_decisions"]
            and not r["technical_or_funding_holds"]
        ]
        negative_seeds = sorted({
            d.lower() for r in bounded_negative for d in r["selected_expansion_seed_dois"]
        })
        explored_seeds = sorted({
            d.lower() for r in records for d in r["selected_expansion_seed_dois"]
        })
        seed_mission_counts = {
            d: sum(d in {x.lower() for x in r["selected_expansion_seed_dois"]} for r in records)
            for d in explored_seeds
        }
        categories[producer] = {
            "verified_report_count": n,
            "distinct_expansion_seeds_investigated": len(explored_seeds),
            "bounded_seed_no_new_output_missions": len(bounded_negative),
            "distinct_bounded_seed_no_new_output_dois": negative_seeds,
            "distinct_bounded_seed_no_new_output_count": len(negative_seeds),
            "expansion_seeds_revisited_across_missions": sum(v > 1 for v in seed_mission_counts.values()),
            "formal_expansion_decision_missions": sum(bool(r["new_expansion_decisions"]) for r in records),
            "bounded_negative_definition": "Explicit seed plus research-only hold, no formal expansion decision or technical/funding hold; not exhaustive proof of absence.",
            "no_report_is_not_proof_no_mission_ran": True,
            "completed_original_decision_missions": len(completed),
            "confirmed_public_handoff_missions": len(public),
            "completed_original_decisions_counted_per_mission": sum(
                len(set(r["new_original_full_decisions"])) for r in records
            ),
            "distinct_completed_original_dois": cases,
            "decision_missions_per_recorded_mission": len(completed) / n if n else None,
            "public_handoff_missions_per_recorded_mission": len(public) / n if n else None,
            "prior_note_sha256_reused_count": sum(
                len(set(r["prior_note_sha256_reused"])) for r in records
            ),
            "external_http_counts_instrumented_missions": len(req),
            "observed_metadata_requests_sum_only_instrumented_missions": sum(req) if req else None,
            "cache_reuse_counts_instrumented_missions": len(cache),
            "observed_cache_reuse_sum_only_instrumented_missions": sum(cache) if cache else None,
            "avoided_requests_claimed": None,
            "private_hub_imports_verified": None,
            "private_hub_status": "NOT_VERIFIED",
        }
    expansion = source_discovery_summary(root)
    return {
        "schema": "reach-scout-separated-completed-mission-scorecard-v1",
        "github_bounded_expansion_research": expansion,
        "measurement_limitation": "Only timestamped reports in source folders; record count is not the number of scheduled task attempts. GitHub backstop is never an hourly ChatGPT mission. In-process reuse differs from persistent cache reuse. No causal inference.",
        "by_producer": categories,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=ROOT)
    args = p.parse_args()
    result = summarize(args.root)
    target = args.root / "scout-operations/reports/hourly-mission-scorecard/latest.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
