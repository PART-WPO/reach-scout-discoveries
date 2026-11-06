#!/usr/bin/env python3
"""Promote validated, immutable Scout inbox drafts into the published batch folder.

Only GitHub Actions should execute this during publication. Failure of one
unvalidated draft leaves existing published batches and manifest untouched.
Scout writes new draft files into scout-discoveries/inbox/ (never overwrite).
"""
import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path

from build_manifest import ROOT
from prepare_batch import validate_canonical

INBOX = ROOT / "inbox"
BATCHES = ROOT / "batches"
REPO = ROOT.parent

def changed_inbox(before, after, verified_referrals_only=False):
    if verified_referrals_only:
        # Only the exact newly authorized source-backed human referrals,
        # never old test drafts or unrelated stale inbox records.
        report_path=REPO/"scout-operations/human-project-referrals.json"
        report=json.loads(report_path.read_text(encoding="utf-8"))
        if report.get("schema")!="reach-scout-bounded-project-human-referral-v1":
            raise ValueError("Missing verified human referral report")
        if report.get("private_hub_imports")!="NOT_VERIFIED" or report.get("new_approved_reach_outputs")!=0:
            raise ValueError("Invalid private/human state on referral report")
        accepted={x["doi"] for x in report.get("referrals",[])
                  if x.get("disposition")=="READY_FOR_VALIDATED_HUMAN_PROJECT_REFERRAL"
                  and x.get("scout_inbox_status") in {
                    "VALIDATED_INBOX_DRAFT_NOT_PRIVATE_HUB",
                    "EXISTING_VERIFIED_INBOX_DRAFT"}}
        paths=[]
        for rel in report.get("draft_paths",[]):
            candidate=REPO/rel
            if candidate.parent.resolve()!=INBOX.resolve() or not candidate.is_file():
                raise ValueError("Human referral is not an actual immutable Scout inbox file")
            # Every draft must bear a DOI that passed the prior source/identity
            # analysis, not just be present in the inbox.
            with candidate.open(encoding="utf-8-sig",newline="") as stream:
                import csv
                rows=list(csv.DictReader(stream))
            if len(rows)!=1 or rows[0].get("DOI","").strip().lower() not in accepted:
                raise ValueError("Unrecognized DOI or candidate count in human referral")
            paths.append(candidate)
        if len(paths)!=report.get("human_referral_drafts_prevalidated"):
            raise ValueError("Reported human draft count does not reconcile")
        return sorted(set(paths))
    if before and after and before != ("0" * 40):
        output = subprocess.check_output(
            ["git", "diff", "--name-only", "--diff-filter=AM", before, after, "--", "scout-discoveries/inbox/"],
            cwd=REPO, text=True)
        paths = [REPO / name for name in output.splitlines() if name.endswith(".csv")]
    else:
        paths = sorted(p for p in INBOX.glob("*.csv") if not (BATCHES / p.name).exists()) if INBOX.exists() else []
    for path in paths:
        if path.resolve().parent != INBOX.resolve():
            raise ValueError(f"Unexpected inbox path: {path}")
        if not path.is_file():
            raise ValueError(f"Missing submitted inbox draft: {path}")
    return sorted(set(paths))

def is_preprint_gate_eligible(path):
    report_path = REPO / "scout-operations/preprint-intake-gate.json"
    if not report_path.exists():
        raise ValueError("Universal preprint intake gate report missing")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("schema") != "reach-scout-preprint-intake-gate-v1":
        raise ValueError("Unknown preprint intake gate schema")
    rel = str(path.relative_to(REPO)).replace("\\", "/")
    matches = [x for x in report["checks"] if x["path"] == rel]
    if len(matches) != 1 or matches[0]["sha256"] != hashlib.sha256(path.read_bytes()).hexdigest():
        raise ValueError("Missing or stale preprint verification for " + rel)
    return matches[0]["verdict"] == "eligible"


def promote(before=None, after=None, verified_referrals_only=False):
    drafts = changed_inbox(before, after, verified_referrals_only)
    # Validate all drafts before writing even one destination.
    prepared = []
    for source in drafts:
        if os.getenv("SCOUT_PREPRINT_GATE_REQUIRED") == "1" and not is_preprint_gate_eligible(source):
            print("HELD outside Discovery Hub (preprint or publication status unverified):", source.name)
            continue
        result = validate_canonical(source)
        target = BATCHES / source.name
        if target.exists() and target.read_bytes() != source.read_bytes():
            raise ValueError(f"Refusing to overwrite a published immutable batch: {target.name}")
        prepared.append((source, target, result))
    for source, target, entry in prepared:
        if target.exists():
            print(f"ALREADY PUBLISHED (unchanged): {entry['id']}")
            continue
        BATCHES.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as out:
            out.write(source.read_bytes())
        print(f"VALIDATED AND PROMOTED: {entry['id']}, {entry['record_count']} candidate(s)")
    print(f"Inbox new submissions inspected: {len(prepared)}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--before", default="", help="Previous push commit; omit for workflow_dispatch")
    ap.add_argument("--after", default="", help="Current push commit")
    ap.add_argument("--verified-referrals-only",action="store_true",
                    help="Promote only source-verified human referral report paths")
    args = ap.parse_args()
    promote(args.before, args.after, args.verified_referrals_only)

if __name__ == "__main__":
    main()
