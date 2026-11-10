#!/usr/bin/env python3
"""GitHub-hosted, source-verified Crossref original -> guarded Scout reviewer handoff.

The queue is only a selection hint. Independently verify publisher-deposited
funding, official publication, public REACH/Scout/NOAA IR identity, preprint
status, and authenticated reviewer feedback before appending a research note.
Never claim private Hub import, human approval, or public REACH insertion.
"""
import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scout-operations/tools"))
sys.path.insert(0, str(ROOT / "scout-discoveries/tools"))

from build_human_project_referrals import build as build_referrals
from build_research_outcome_registry import build as build_registry
from decision_pipeline import norm_doi, norm_title
from ir_reach_identity import verified_snapshot, identity_check
from lookup_independent_dois import metadata as fetch_metadata
from reviewer_feedback_guard import known_feedback_by_doi
from wpo_awards import official_459_awards

QUEUE = "scout-operations/crossref-candidate-queue.json"
LEDGER = "scout-operations/decision-handoff-ledger.json"
REPORT = "scout-operations/reports/hourly-decision-handoff.json"
REGISTRY = "scout-operations/research-outcome-registry.json"
REFERRALS = "scout-operations/human-project-referrals.json"
NOTES = "scout-operations/historical-crossref-phase2"
SCHEMA = "reach-scout-hourly-decision-handoff-v1"
PUBLISHABLE = {"NOVEL_IDENTITY_RESEARCH", "HUMAN_REVIEW_FAST_SCREEN_DUE"}
MAX_ATTEMPTS = 5
BLOCK_HOURS = {
    "OFFICIAL_METADATA_UNAVAILABLE": 3,
    "OFFICIAL_PUBLICATION_UNVERIFIED": 24,
    "PUBLISHER_459_NOT_VERIFIED": 24,
    "DOI_TITLE_CONFLICT": 24,
    "AMBIGUOUS_PUBLIC_IDENTITY": 24,
    "PREPRINT_WATCHLIST": 24 * 30,
    "HUMAN_FEEDBACK_ALREADY_EXISTS": 24 * 30,
    "SPECIAL_PUBLICATION_TYPE": 24 * 14,
    "NOT_NEW_IN_REACH_OR_SCOUT": 24 * 30,
    "REVIEWER_HANDOFF_NOT_READY": 3,
}
SPECIAL = re.compile(r"\b(corrigendum|erratum|correction|retraction|expression of concern)\b", re.I)


def checksum(data):
    return hashlib.sha256(data).hexdigest()


def verified_queue(root):
    raw = json.loads((root / QUEUE).read_text(encoding="utf-8"))
    if raw.get("schema") != "reach-scout-crossref-candidate-queue-v2":
        raise ValueError("Unexpected source selection queue version")
    sources = raw.get("source_sha256") or {}
    if len(sources) < 4:
        raise ValueError("Crossref queue has insufficient source fingerprints")
    for rel, expected in sources.items():
        if (not isinstance(rel, str) or rel.startswith("/") or ".." in Path(rel).parts
            or not (root / rel).is_file()
            or checksum((root / rel).read_bytes()) != expected):
            raise ValueError("STALE_QUEUE_SOURCE: " + str(rel))
    return raw


def read_ledger(root):
    path = root / LEDGER
    if not path.exists():
        return {"schema": SCHEMA, "cases": {}, "last_mission": None}
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != SCHEMA or not isinstance(data.get("cases"), dict):
        raise ValueError("Unknown persistent blocker-ledger schema")
    return data


def blocked(case, now):
    if not case or case.get("state") != "BLOCKED":
        return False
    try:
        until = datetime.fromisoformat(case["retry_after"].replace("Z", "+00:00"))
    except (KeyError, ValueError, TypeError):
        return False
    return now < until


def candidate_order(queue, ledger, now, limit=MAX_ATTEMPTS):
    due = []
    skipped = []
    for item in queue.get("items", []):
        doi = norm_doi(item.get("doi"))
        if (not doi or item.get("lane") not in PUBLISHABLE
            or item.get("funding_signal") != "CONFIRMED_WPO_459"
            or item.get("already_in_public_scout_queue")):
            continue
        prior = ledger["cases"].get(doi)
        if blocked(prior, now):
            skipped.append({"doi": doi, "retry_after": prior["retry_after"],
                            "reason": prior.get("reason")})
            continue
        if prior and prior.get("state") in {"PUBLISHED_PUBLIC_SCOUT", "STAGED_VALIDATED_INBOX"}:
            # A fresh official identity lookup is still required for any new proposal.
            # Staged records are handled by the dedicated publisher, not recreated.
            skipped.append({"doi": doi, "reason": prior["state"]})
            continue
        due.append(item)
    # Ordinary articles first. Corrigenda need distinct eligibility review.
    due.sort(key=lambda x: (bool(SPECIAL.search(str(x.get("title") or ""))),
                            -int(x.get("priority") or 0), str(x["doi"])))
    return due[:limit], skipped


def disposition(ledger, doi, reason, now, *, evidence="", details=""):
    row = ledger["cases"].get(doi, {})
    count = int(row.get("attempt_count") or 0) + 1
    hours = BLOCK_HOURS.get(reason, 3)
    ledger["cases"][doi] = {
        "state": "BLOCKED", "reason": reason, "attempt_count": count,
        "checked_at": now.isoformat(), "retry_after": (now + timedelta(hours=hours)).isoformat(),
        "official_evidence_url": evidence or None, "detail": str(details)[:280],
        "private_hub_import": "NOT_VERIFIED",
    }
    return {"doi": doi, "decision": reason, "status": "BLOCKED",
            "retry_after": ledger["cases"][doi]["retry_after"]}


def screened_note(doi, item, meta, award, identity, now):
    sha = checksum(doi.encode("utf-8"))[:18]
    path = NOTES + "/auto-verified-oar459-" + sha + ".json"
    source_url = meta["evidence"]
    archive = item["award_evidence_source_batches"][0]
    return path, {
        "schema": "scout-source-backed-research-evidence-v1",
        "recorded_at": now.isoformat(),
        "lane": "historical_crossref_original",
        "original_doi": doi,
        "title": meta["title"],
        "decision": "NEW_CANDIDATE_PUBLIC_REFERRAL_REQUEST_SUBJECT_TO_GUARDED_CHECKS",
        "operational_disposition": "BOUNDED_PROJECT_QUESTION_FOR_HUMAN",
        "structured_award": award,
        "spark_primary_award_context": award,
        "funding": "OFFICIAL_CROSSREF_EXACT_DOI_WPO459_CONFIRMED",
        "publication_status": "OFFICIALLY_PUBLISHED_JOURNAL_ARTICLE",
        "publisher_published_date": meta["pub_date"],
        "preprint_original": False,
        "source_evidence": [
            {"url": source_url, "type": "exact_doi_official_crossref_funding",
             "finding": "Official Crossref article-level funding records explicitly identify " + award + " for " + doi},
            {"url": "https://github.com/PART-WPO/reach-scout-discoveries/blob/main/" + archive,
             "type": "sha_verified_historical_crossref_batch",
             "finding": "Historical Crossref intake independently indexed the same full WPO award against the same DOI."},
            {"url": "https://doi.org/" + doi, "type": "persistent_official_publication_identifier",
             "finding": "Official journal publication identity and date confirmed from exact DOI metadata."},
        ],
        "identity_status": identity["status"],
        "noaa_ir_reach_check": identity.get("noaa_ir_reach_check"),
        "award_evidence_source_batches": item.get("award_evidence_source_batches", []),
        "exact_primary_spark_award_verified_for_output": True,
        "output_to_specific_primary_wpo_project_verified": False,
        "public_proposal_eligible": False,
        "private_hub_action": "NONE",
        "original_status_changed": False,
        "expansion_completed": False,
        "next_action": "Guarded GitHub 24-column NEW CANDIDATE handoff; human reviewer selects and verifies SPARK parent; do not infer private Hub import or REACH publication.",
        "research_counts": {"originals_screened": 1, "originals_deeply_examined": 1,
                            "expansion_cases_examined": 0, "new_explicit_child_doi_links": 0,
                            "private_hub_outcomes_verified": 0},
    }


def evaluate(item, root, public, ir_index, known_reviews, watched, metadata_fn, now, ledger):
    doi = norm_doi(item["doi"])
    if SPECIAL.search(str(item.get("title") or "")):
        return disposition(ledger, doi, "SPECIAL_PUBLICATION_TYPE", now,
                           details="Distinct correction/corrigendum eligibility requires manual review.")
    # GitHub Actions is the verification authority; queue is NOT proof.
    md = metadata_fn(doi)
    if md.get("status") != "ok" or md.get("provider") != "crossref":
        return disposition(ledger, doi, "OFFICIAL_METADATA_UNAVAILABLE", now,
                           details="Fresh exact DOI Crossref data unavailable; rotate to the next candidate.")
    evidence = "https://api.crossref.org/works/" + doi
    if md.get("evidence") != evidence or not norm_title(md.get("title")) or (
        norm_title(item.get("title")) != norm_title(md.get("title"))
    ):
        return disposition(ledger, doi, "DOI_TITLE_CONFLICT", now, evidence=evidence)
    if md.get("resource_type") != "journal-article" or md.get("publication_status") != "official_journal_article" or not md.get("pub_date"):
        return disposition(ledger, doi, "OFFICIAL_PUBLICATION_UNVERIFIED", now,
                           evidence=evidence, details=str(md.get("resource_type")))
    if doi in watched or md.get("publication_status") == "preprint":
        return disposition(ledger, doi, "PREPRINT_WATCHLIST", now, evidence=evidence)
    verified_awards = set(official_459_awards(md)) & set(item.get("wpo_459_award_numbers") or [])
    if not verified_awards:
        return disposition(ledger, doi, "PUBLISHER_459_NOT_VERIFIED", now, evidence=evidence,
                           details="Historical award context does not match current exact DOI funding deposit.")
    check = identity_check(public, ir_index, doi, md["title"], "https://doi.org/" + doi)
    if check["status"] in {"CONFIRMED_PUBLIC_REACH_IDENTITY", "IN_PUBLIC_SCOUT_QUEUE"}:
        return disposition(ledger, doi, "NOT_NEW_IN_REACH_OR_SCOUT", now, evidence=evidence)
    if check["status"] != "NO_PUBLIC_IDENTITY_MATCH" or check.get("noaa_ir_reach_check", {}).get("status") in {
        "IR_INDEX_UNAVAILABLE_HOLD", "AMBIGUOUS_IR_DOI_HOLD",
        "MULTIPLE_REACH_RECORDS_HOLD", "REACH_DOI_CONFLICT_VERSION_REVIEW",
        "IR_URL_MATCH_REQUIRES_REVIEW",
    }:
        return disposition(ledger, doi, "AMBIGUOUS_PUBLIC_IDENTITY", now, evidence=evidence,
                           details=str(check.get("status")))
    if known_reviews.get(doi):
        return disposition(ledger, doi, "HUMAN_FEEDBACK_ALREADY_EXISTS", now, evidence=evidence)
    award = sorted(verified_awards)[0]
    path, note = screened_note(doi, item, md, award, check, now)
    target = root / path
    if target.is_file():
        old = json.loads(target.read_text(encoding="utf-8"))
        if norm_doi(old.get("original_doi")) != doi or old.get("structured_award") != award:
            raise ValueError("Existing immutable research note contradicts verified source")
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(note, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"doi": doi, "decision": "SOURCE_VERIFIED_FOR_GUARDED_REVIEW",
            "status": "SOURCE_VERIFIED", "award": award, "evidence_url": evidence,
            "source_note": path, "metadata": md}


def run(root=ROOT, metadata_fn=fetch_metadata, now=None, limit=MAX_ATTEMPTS,
        *, stage=True, public=None, ir_index=None):
    now = now or datetime.now(timezone.utc)
    queue = verified_queue(root)
    ledger = read_ledger(root)
    if public is None:
        public, ir_index = verified_snapshot(root)
    reviews = known_feedback_by_doi(root)
    watch = json.loads((root / "scout-operations/preprint-watchlist.json").read_text(encoding="utf-8"))
    if watch.get("schema") != "reach-scout-preprint-watchlist-v1":
        raise ValueError("Unverified preprint watchlist")
    watched = {norm_doi(x.get("preprint_doi")) for x in watch.get("entries", [])}
    selected, skipped = candidate_order(queue, ledger, now, limit)
    outcomes = []
    memo = {}
    for item in selected:
        outcome = evaluate(item, root, public, ir_index, reviews, watched, metadata_fn, now, ledger)
        if outcome["status"] == "SOURCE_VERIFIED":
            memo[outcome["doi"]] = outcome.pop("metadata")
            if stage:
                registry = build_registry(root)
                (root / REGISTRY).write_text(
                    json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                def reuse_verified(doi):
                    return memo[doi] if doi in memo else metadata_fn(doi)
                result = build_referrals(root=root, metadata=reuse_verified, stage=True)
                (root / REFERRALS).write_text(
                    json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                doi = outcome["doi"]
                rows = [r for r in result["referrals"] if r["doi"] == doi]
                valid = [r for r in rows if r.get("disposition") == "READY_FOR_VALIDATED_HUMAN_PROJECT_REFERRAL"
                         and r.get("scout_inbox_status") in {
                             "VALIDATED_INBOX_DRAFT_NOT_PRIVATE_HUB", "EXISTING_VERIFIED_INBOX_DRAFT",
                         }]
                if len(valid) != 1:
                    # Record an actual failed handoff; keep the source note
                    # append-only and try the NEXT DOI in the SAME mission.
                    outcome.update(disposition(ledger, doi, "REVIEWER_HANDOFF_NOT_READY", now,
                        evidence=outcome.get("evidence_url", ""),
                        details=rows[0]["disposition"] if len(rows) == 1
                                else "NO_EXACT_DOI_REFERRAL_RECORD"))
                else:
                    ledger["cases"][doi] = {
                        "state": "STAGED_VALIDATED_INBOX", "reason": "PENDING_PUBLICATION_GATE",
                        "checked_at": now.isoformat(), "attempt_count":
                            int(ledger["cases"].get(doi, {}).get("attempt_count") or 0) + 1,
                        "source_note": outcome["source_note"],
                        "private_hub_import": "NOT_VERIFIED"}
                    outcome["status"] = "STAGED_VALIDATED_INBOX"
        outcomes.append(outcome)
        if outcome["status"] == "STAGED_VALIDATED_INBOX" or (
            not stage and outcome["status"] == "SOURCE_VERIFIED"
        ):
            break
    report = {"schema": SCHEMA, "ran_at": now.isoformat(),
              "source_selection_sha256": checksum((root / QUEUE).read_bytes()),
              "attempted_originals": len(outcomes), "public_review_batches_validated_this_run": 0,
              "public_review_handoffs_staged": sum(x["status"] == "STAGED_VALIDATED_INBOX" for x in outcomes),
              "outcomes": outcomes, "skipped_cooldown_or_already_staged": skipped[:25],
              "private_hub_import": "NOT_VERIFIED", "human_approval": "NOT_VERIFIED",
              "note": "Publication status counted only after the universal preprint gate, canonical 24-column check and active manifest verify."}
    ledger["last_mission"] = {"at": now.isoformat(), "attempted": len(outcomes),
                              "staged": report["public_review_handoffs_staged"]}
    for rel, obj in ((LEDGER, ledger), (REPORT, report)):
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def confirm_published(root=ROOT):
    """Only manifest-active, exact DOI/CSV evidence may count as a completed handoff."""
    report = json.loads((root / REPORT).read_text(encoding="utf-8"))
    ledger = read_ledger(root)
    manifest = json.loads((root / "scout-discoveries/manifest.json").read_text(encoding="utf-8"))
    active = {b["path"]: b["sha256"] for b in manifest["batches"]}
    import csv
    done = 0
    for outcome in report["outcomes"]:
        if outcome["status"] != "STAGED_VALIDATED_INBOX":
            continue
        doi = outcome["doi"]
        matches = []
        for rel, expected in active.items():
            if not rel.startswith("scout-discoveries/batches/"):
                continue
            path = root / rel
            if checksum(path.read_bytes()) != expected:
                raise ValueError("Published manifest SHA conflict")
            with path.open(newline="", encoding="utf-8-sig") as f:
                rows = list(csv.DictReader(f))
            for row in rows:
                if norm_doi(row.get("DOI")) == doi:
                    matches.append((rel, row))
        if len(matches) != 1:
            outcome["status"] = "PENDING_OR_HELD_PUBLICATION_GATE"
            ledger["cases"][doi].update({"state": "BLOCKED",
                 "reason": "REVIEWER_HANDOFF_NOT_READY",
                 "retry_after": (datetime.now(timezone.utc) + timedelta(hours=3)).isoformat()})
            continue
        rel, row = matches[0]
        if ("Scout classification: NEW CANDIDATE" not in row.get("Scout Discovery Rationale", "")
            or row.get("NOAA Award Number(s)") != outcome["award"]):
            raise ValueError("Published candidate does not match verified 459 handoff")
        ledger["cases"][doi].update({"state": "PUBLISHED_PUBLIC_SCOUT",
            "reason": "SOURCE_VERIFIED_AND_MANIFEST_VALIDATED", "published_batch": rel})
        outcome.update({"status": "PUBLISHED_PUBLIC_SCOUT", "published_batch": rel})
        done += 1
    report["public_review_batches_validated_this_run"] = done
    report["public_review_handoffs_staged"] = sum(
        x["status"] == "STAGED_VALIDATED_INBOX" for x in report["outcomes"])
    for rel, obj in ((LEDGER, ledger), (REPORT, report)):
        (root / rel).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"verified_public_scout_new_candidates": done,
                      "attempted": report["attempted_originals"],
                      "private_hub_import": "NOT_VERIFIED"}))
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--confirm-published", action="store_true")
    ap.add_argument("--limit", type=int, default=MAX_ATTEMPTS)
    args = ap.parse_args()
    if args.confirm_published:
        confirm_published()
    else:
        print(json.dumps(run(limit=max(1, min(args.limit, MAX_ATTEMPTS))),
                         indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
