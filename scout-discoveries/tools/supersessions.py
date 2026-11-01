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
