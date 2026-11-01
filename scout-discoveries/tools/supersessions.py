"""Read a JSON-defined Scout batch replacement with audit history."""

import json
from pathlib import Path

def get_rules(folder: Path):
    path = folder / "supersessions.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "reach-scout-feed-supersessions-v1":
        raise ValueError("Unexpected replacement rules")
    return data["superseded_batches"]

def approved_batches(folder, entries):
    rules = get_rules(folder)
    by_id = {entry["id"]: entry for entry in entries}
    for old_id, rule in rules.items():
        new_id = rule["replacement_id"]
        if old_id not in by_id or new_id not in by_id:
            raise ValueError("Batch replacement missing")
        if by_id[old_id]["sha256"] != rule["original_sha256"]:
            raise ValueError("Source batch digest changed")
    return [e for e in entries if e["id"] not in rules]
