"""Read-only completion check for monthly intake and manual recovery."""
import argparse
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
import re

from build_manifest import inspect_batch, SCHEMA
from export_comparison_xlsx import report_filename

ROOT = Path(__file__).resolve().parents[2]
STATUS = "completed_API_research_input_only_not_Scout_reviewed_not_REACH_published"


def ready(root, month):
    first = date.fromisoformat(month + "-01")
    release = (first.replace(day=28) + timedelta(days=4)).replace(day=1)
    base = f"{release.isoformat()}-monthly-api-{month}"
    run_id = f"REACH-MONTHLY-API-{month}"
    api = root / "api-discoveries"
    summary_paths = sorted((api / "runs").glob(f"monthly-{month}*.json"))
    manifest = json.loads((api / "manifest.json").read_text())
    if manifest.get("schema") != SCHEMA:
        raise ValueError("Unexpected public monthly manifest schema")
    batches = [batch for batch in manifest["batches"] if run_id in batch["source_run_ids"]]
    if not summary_paths:
        if batches:
            raise ValueError("Published monthly batches have no completion summary")
        return False
    revisions = set()
    for batch in batches:
        expected = re.fullmatch(re.escape(base) + r"(?:-([a-z][a-z0-9-]*))?-part\d{3}", batch["id"])
        if not expected or batch["path"] != f"api-discoveries/batches/{batch['id']}.csv":
            raise ValueError("Unexpected monthly batch identity")
        revisions.add(expected[1] or "")
        if inspect_batch(root / batch["path"]) != batch or batch["source_run_ids"] != [run_id]:
            raise ValueError("Monthly batch does not match the published manifest")

    if not batches:
        # A fully completed harvest may legitimately find zero DOI records.
        revisions.add("")
    if len(revisions) != 1:
        raise ValueError("Multiple active monthly batch revisions")
    revision = revisions.pop()
    suffix = "-" + revision if revision else ""
    path = api / "runs" / f"monthly-{month}{suffix}.json"
    if not path.is_file():
        raise ValueError("Active monthly batches have no matching completion summary")
    record = json.loads(path.read_text())
    expected_rows = sum(batch["record_count"] for batch in batches)
    if (record["status"], record["cohort"], record["run"], record["source_apis"],
        record["batch_count"], record["distinct_dois"]) != (
        STATUS, month, run_id, ["datacite", "crossref"], len(batches), expected_rows
    ) or record["unique_awards_checked_per_api"] <= 0:
        raise ValueError("Monthly completion summary does not match published intake")
    workbook = root / "monthly-harvest-reports" / report_filename(month, revision)
    if not workbook.is_file() or workbook.stat().st_size == 0:
        raise ValueError("Completed monthly intake is missing its comparison workbook")
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--month")
    args = parser.parse_args()
    first = datetime.now(timezone.utc).date().replace(day=1)
    month = args.month or (first - timedelta(days=1)).strftime("%Y-%m")
    try:
        available = ready(args.root, month)
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(2, f"{month}: inconsistent intake: {error}\n")
    print(f"{month}: {'COMPLETE' if available else 'WAITING_FOR_COMPLETE_HARVEST'}")
    return 0 if available else 1


if __name__ == "__main__":
    raise SystemExit(main())
