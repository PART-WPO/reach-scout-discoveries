#!/usr/bin/env python3
"""Promote validated, immutable Scout inbox drafts into the published batch folder.

Only GitHub Actions should execute this during publication. Failure of one
unvalidated draft leaves existing published batches and manifest untouched.
Scout writes new draft files into scout-discoveries/inbox/ (never overwrite).
"""
import argparse
import subprocess
from pathlib import Path

from build_manifest import ROOT
from prepare_batch import validate_canonical

INBOX = ROOT / "inbox"
BATCHES = ROOT / "batches"
REPO = ROOT.parent

def changed_inbox(before, after):
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

def promote(before=None, after=None):
    drafts = changed_inbox(before, after)
    # Validate all drafts before writing even one destination.
    prepared = []
    for source in drafts:
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
    args = ap.parse_args()
    promote(args.before, args.after)

if __name__ == "__main__":
    main()
