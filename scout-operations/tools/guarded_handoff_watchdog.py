#!/usr/bin/env python3
"""Independent heartbeat for the guarded GitHub Crossref handoff.

Uses actual workflow-run data, not a successful cron trigger or CI test.
Outputs a recovery recommendation; the separate GitHub Actions workflow
dispatches the existing guarded handoff with the normal immutable gates.
"""
import argparse
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

SCHEMA = "reach-scout-guarded-handoff-watchdog-v1"
TARGET = "scout-hourly-guarded-handoff.yml"
ACTIVE = {"queued", "in_progress", "waiting", "requested", "pending"}


def stamp(value):
    t = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if t.tzinfo is None:
        raise ValueError("Workflow timestamps must include UTC offset")
    return t.astimezone(timezone.utc)


def evaluate(payload, now, max_age_minutes=85, recovery_cooldown_minutes=75):
    if now.tzinfo is None:
        raise ValueError("Watchdog time must be offset-aware")
    now = now.astimezone(timezone.utc)
    if max_age_minutes < 60 or recovery_cooldown_minutes < 45:
        raise ValueError("Unsafe heartbeat threshold")
    runs = payload.get("workflow_runs")
    if not isinstance(runs, list):
        raise ValueError("Missing actual GitHub workflow runs")
    # The guarded processor currently enforces an Eastern weekday schedule.
    # Manual dispatch remains available during weekends, but watchdog does
    # not silently change the authoritative existing weekday cadence.
    if now.astimezone(ZoneInfo("America/New_York")).weekday() >= 5:
        action = "EXPECTED_WEEKEND_PAUSE"
        successful = []
        active = []
        recent_dispatch = []
    else:
        relevant = [
            r for r in runs
            if r.get("head_branch") == "main"
            and r.get("name") == "Scout hourly guarded DOI decision handoff"
            and r.get("event") in {"schedule", "workflow_dispatch", "push"}
        ]
        successful = sorted([
            r for r in relevant
            if r.get("status") == "completed" and r.get("conclusion") == "success"
            and r.get("updated_at")
        ], key=lambda x: stamp(x["updated_at"]), reverse=True)
        active = [
            r for r in relevant if r.get("status") in ACTIVE
            and r.get("created_at")
            and now - stamp(r["created_at"]) < timedelta(minutes=55)
        ]
        recent_dispatch = [
            r for r in relevant if r.get("event") == "workflow_dispatch"
            and r.get("created_at")
            and now - stamp(r["created_at"]) < timedelta(minutes=recovery_cooldown_minutes)
        ]
        last_success = stamp(successful[0]["updated_at"]) if successful else None
        if last_success and now - last_success <= timedelta(minutes=max_age_minutes):
            action = "HEALTHY"
        elif active:
            action = "RUN_IN_PROGRESS"
        elif recent_dispatch:
            action = "RECOVERY_COOLDOWN"
        else:
            action = "RECOVERY_REQUIRED"
    last = successful[0] if successful else None
    age = int((now - stamp(last["updated_at"])).total_seconds() / 60) if last else None
    return {
        "schema": SCHEMA, "observed_at_utc": now.isoformat(),
        "action": action, "watchdog_target": TARGET,
        "latest_success_run_id": last.get("id") if last else None,
        "latest_success_ended_at_utc": last.get("updated_at") if last else None,
        "latest_success_age_minutes": age,
        "active_recent_run_ids": [r.get("id") for r in active],
        "recent_dispatch_run_ids": [r.get("id") for r in recent_dispatch],
        "max_success_age_minutes": max_age_minutes,
        "recovery_cooldown_minutes": recovery_cooldown_minutes,
        "recovery_guard": "existing guarded GitHub workflow, shared concurrency lock, fresh-main ledger and manifest checks",
        "chatgpt_hourly_mission_completed": "NOT_INFERRED",
        "new_public_candidate_count": "NOT_INFERRED",
        "private_hub_import": "NOT_VERIFIED",
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--runs-file", type=Path, required=True)
    p.add_argument("--output-file", type=Path, required=True)
    p.add_argument("--now-utc", default=None)
    a = p.parse_args()
    now = stamp(a.now_utc) if a.now_utc else datetime.now(timezone.utc)
    out = evaluate(json.loads(a.runs_file.read_text()), now)
    a.output_file.parent.mkdir(parents=True, exist_ok=True)
    a.output_file.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, sort_keys=True))


if __name__ == "__main__":
    main()
