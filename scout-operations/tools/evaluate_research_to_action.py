#!/usr/bin/env python3
"""Read-only Evidence Evaluator + Decision Compiler pilot for Scout research.

Evaluates *recorded public evidence*, never fabricates new source research,
formal original/expansion completion, reviewer decisions or private Hub state.
Every outcome is a recommendation with source-SHA provenance, not authority
to publish. More research is recommended only against one specific open gate.
"""
import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit

from build_research_outcome_registry import build as build_journal
from decision_pipeline import norm_doi
from unified_source_preflight import preflight

ROOT = Path(__file__).resolve().parents[2]
DEST = "scout-operations/reports/evidence-action-pilot/latest.json"
ANNOTATED = "scout-operations/research-decision-cases.json"
SCHEMA = "reach-scout-read-only-evidence-action-pilot-v1"

# Only *public* statuses. A public staging entry does not establish Hub import.
PUBLIC_STAGED = {
    "staged_for_hub_import", "staged_for_human_review",
    "pending_human_intake", "forwarded_to_hub", "metadata_update_forwarded",
    "research_complete_human_intake", "research_complete_human_intake_pending_private_ui",
}
PUBLIC_NO_ACTION = {"no_action", "already_in_reach"}
PROJECT_CONFLICT_KEYS = {
    "contradictory_project_evidence_found", "funding",
    "funding_signal", "project_attribution", "award_evidence_status",
}
TRUSTED_PUBLISHED_STRINGS = {
    "PUBLISHED", "PUBLISHED_JOURNAL_ARTICLE", "OFFICIAL_JOURNAL_PUBLICATION_VERIFIED",
    "OFFICIAL_JOURNAL_ARTICLE_NOT_PREPRINT",
    "PUBLISHER_JOURNAL_ARTICLE_NOT_ORIGINAL_PREPRINT", "VERSION OF RECORD",
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def stable_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def json_source(root, relative):
    if Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise ValueError("Invalid public Scout evidence file path")
    path = root / relative
    data = path.read_bytes()
    return json.loads(data), digest(data)


def prior_cases(root):
    doc, source_sha = json_source(root, ANNOTATED)
    if not isinstance(doc.get("cases"), list):
        raise ValueError("Prior research decision case source unavailable")
    cases = {}
    for entry in doc["cases"]:
        d = norm_doi(entry.get("doi"))
        if not d or d in cases:
            raise ValueError("Duplicate/invalid prior decision case DOI")
        for source in entry.get("source_evidence", []):
            rel = source.get("path", "")
            expected = source.get("sha256")
            if (Path(rel).is_absolute() or ".." in Path(rel).parts or
                    not rel.startswith(("scout-operations/historical-crossref-phase2/",
                                        "scout-operations/monthly-research/"))):
                raise ValueError("Prior case evidence outside approved research files")
            if not expected or digest((root / rel).read_bytes()) != expected:
                raise ValueError("Prior case source evidence SHA mismatch: " + rel)
        cases[d] = entry
    return cases, source_sha


def identity_specific_note(doc, identity):
    """Prevent a multi-case research file from cross-contaminating DOI verdicts."""
    if isinstance(doc.get("cases"), list):
        selected = [entry for entry in doc["cases"]
                    if "doi:" + str(norm_doi(entry.get("doi"))) == identity]
        if len(selected) != 1:
            raise ValueError("Case note does not have exactly one matching DOI identity")
        return selected[0]
    if isinstance(doc.get("original"), dict) and doc["original"].get("doi"):
        if "doi:" + str(norm_doi(doc["original"]["doi"])) != identity:
            raise ValueError("Original note DOI identity mismatch")
        return doc["original"]
    if isinstance(doc.get("research_subject"), dict):
        children = {"doi:" + str(norm_doi(v))
                    for v in doc["research_subject"].get("child_dois", [])}
        if children and identity not in children:
            raise ValueError("Related-output note identity not in explicit child DOIs")
    return doc


def source_pointers(doc):
    """Collect explicit official/source URLs without mining names or source prose."""
    result = set()
    allowed = {"url", "evidence_url", "source_url", "official_publisher_url",
               "publisher_url", "publisher_source", "official_noaa_ir_url",
               "noaa_ir_url", "independent_institutional_source",
               "canonical_url", "source_evidence_url", "source"}
    branches = {"sources", "evidence", "source_evidence", "new_source_findings",
                "checked_sources", "initial_source", "distinct_source_followup"}

    def walk(obj):
        if isinstance(obj, list):
            for part in obj:
                walk(part)
        elif isinstance(obj, dict):
            for k, val in obj.items():
                if k in allowed and isinstance(val, str):
                    if val.startswith("https://") and urlsplit(val).netloc:
                        result.add(val)
                elif k in branches:
                    walk(val)
        elif isinstance(obj, str):
            if obj.startswith("https://") and urlsplit(obj).netloc:
                result.add(obj)
    walk(doc)
    return sorted(result)


def explicit_claims(doc):
    """Structured, known-meaning flags only; never mine author/title prose."""
    observations = {
        "preprint_claim": False,
        "official_publication_claim": False,
        "same_project_claim": False,
        "primary_spark_claim": False,
        "project_conflict_claim": False,
        "technical_access_failure_claim": False,
        "missing_project_proof_claim": False,
        "metadata_complete_claim": False,
        "workflow_failure_claim": False,
        "metadata_access_failure_claim": False,
    }

    def walk(obj):
        if isinstance(obj, list):
            for child in obj:
                walk(child)
        elif isinstance(obj, dict):
            if obj.get("same_project_wpo_funding_verified") is True:
                observations["same_project_claim"] = True
            if (obj.get("exact_primary_spark_award_verified") is True or
                    obj.get("primary_spark_award_verified") is True):
                observations["primary_spark_claim"] = True
            if obj.get("required_metadata_verified") is True:
                observations["metadata_complete_claim"] = True
            if obj.get("contradictory_project_evidence_found") is True:
                observations["project_conflict_claim"] = True
            if isinstance(obj.get("workflow_blocker"), dict) and (
                    obj["workflow_blocker"].get("conclusion") == "failure"):
                observations["workflow_failure_claim"] = True
            if any(isinstance(obj.get(k), str)
                   and "ACCESS_FAILURE" in obj[k].upper()
                   for k in ("source_failure", "metadata_failure", "metadata_access_status")):
                observations["metadata_access_failure_claim"] = True
            if isinstance(obj.get("decision_preview"), str) and (
                    "CONTRADICTED_WPO_ATTRIBUTION" in obj["decision_preview"].upper()):
                observations["project_conflict_claim"] = True
            if (obj.get("exact_primary_spark_award_verified") is False or
                    obj.get("primary_spark_award_verified") is False):
                observations["missing_project_proof_claim"] = True
            for k in ("publication_status", "preprint_status", "status",
                      "preprint_original", "preprint_eligibility", "publisher_version"):
                value = obj.get(k)
                if k == "preprint_original" and value is True:
                    observations["preprint_claim"] = True
                elif isinstance(value, str):
                    u = value.strip().upper()
                    if u in {"PREPRINT", "PREPRINT_HOLD", "PREPRINT_WATCHLIST_HOLD",
                             "PREPRINT_MONTHLY_WATCH"}:
                        observations["preprint_claim"] = True
                    if u in TRUSTED_PUBLISHED_STRINGS:
                        observations["official_publication_claim"] = True
            for k in PROJECT_CONFLICT_KEYS:
                value = obj.get(k)
                if isinstance(value, str):
                    u = value.upper()
                    if any(flag in u for flag in
                           ("CONTRADICTORY_AWARD", "CONTRADICTED",
                            "DIFFERENT_PRIMARY_AWARD", "PARENT_PUBLICATION_HAS_CONTRADICTORY_AWARD")):
                        observations["project_conflict_claim"] = True
                    if any(flag in u for flag in
                           ("UMBRELLA_REQUIRES_PROJECT_PROOF", "NOT_PRIMARY_SPARK_PROJECT_VERIFIED",
                            "UNRESOLVED")):
                        observations["missing_project_proof_claim"] = True
            for k, v in obj.items():
                # Untrusted free-text source narrative is NOT interpreted as
                # evidence of a positive grant link or adverse finding.
                if k not in {"title", "abstract", "authors", "creators", "pi",
                             "principal_investigators", "researchers", "findings",
                             "next_action", "notes", "description", "rationale"}:
                    walk(v)
    walk(doc)
    return observations


def public_identity_state(preflight_rows):
    dispositions = {r.get("public_identity_disposition") for r in preflight_rows}
    effective = {r.get("effective_identity_or_preflight") for r in preflight_rows}
    statuses = {str(r.get("recorded_status_unchanged", "")).lower()
                for r in preflight_rows}
    if "EXISTING_IN_REACH_VERIFIED_BULK" in effective or "EXISTING_IN_REACH" in dispositions:
        return "VERIFIED_EXISTING_PUBLIC_REACH", sorted(statuses)
    if statuses & PUBLIC_STAGED or "EXISTING_PUBLIC_SCOUT_CANDIDATE" in dispositions:
        return "PUBLIC_SCOUT_PROPOSAL_RECORDED", sorted(statuses)
    if statuses & PUBLIC_NO_ACTION:
        return "PUBLIC_NO_ACTION_OR_EXISTING_RECORDED", sorted(statuses)
    if "IDENTITY_REVIEW_REQUIRED" in dispositions or "IDENTITY_REVIEW_REQUIRED_FROM_BULK" in effective:
        return "AMBIGUOUS_PUBLIC_IDENTITY", sorted(statuses)
    if "PREPRINT_WATCHLIST_HOLD" in dispositions:
        return "PREPRINT_WATCHLIST_HOLD", sorted(statuses)
    if preflight_rows:
        return "PUBLIC_SCREEN_COMPLETED_NOT_NEW_OUTPUT_PROOF", sorted(statuses)
    return "NOT_IN_VERIFIED_PREFLIGHT_COHORT", []


def evidence_assessment(identity, history, preflight_rows, annotated, notes):
    urls = sorted({u for event in history
                   for u in event["checked_evidence_urls"]
                   if u.startswith("https://")} |
                  {u for doc in notes for u in source_pointers(doc)})
    # Existing earlier verified research decisions may have source URLs absent
    # from newer note schema. They remain *pointers*, not 2 fresh sources.
    prior_urls = sorted({u for u in (annotated or {}).get("checked_sources", [])
                         if isinstance(u, str) and u.startswith("https://")})
    all_urls = sorted(set(urls) | set(prior_urls))
    claims = {key: False for key in (
        "preprint_claim", "official_publication_claim", "same_project_claim",
        "primary_spark_claim", "project_conflict_claim",
        "technical_access_failure_claim", "missing_project_proof_claim",
        "metadata_complete_claim", "workflow_failure_claim",
        "metadata_access_failure_claim",
    )}
    for source in notes:
        found = explicit_claims(source)
        for key, flag in found.items():
            claims[key] = claims[key] or flag
    d = norm_doi(identity[4:]) if identity.startswith("doi:") else None
    prior_status = str((annotated or {}).get("publication_status") or "NOT_CHECKED").upper()
    claim_preprint = (claims["preprint_claim"] or prior_status == "PREPRINT"
                      or any(r.get("publication_status") == "PREPRINT"
                             for r in preflight_rows))
    claim_official = (claims["official_publication_claim"] or
                      prior_status == "PUBLISHED" or
                      any(r.get("publication_status") == "PUBLISHED"
                          for r in preflight_rows))
    public_state, statuses = public_identity_state(preflight_rows)
    if public_state == "PREPRINT_WATCHLIST_HOLD":
        claim_preprint = True
    is_reach = public_state == "VERIFIED_EXISTING_PUBLIC_REACH"
    is_staged = public_state == "PUBLIC_SCOUT_PROPOSAL_RECORDED"
    is_no_action = public_state == "PUBLIC_NO_ACTION_OR_EXISTING_RECORDED"
    identity_review = public_state == "AMBIGUOUS_PUBLIC_IDENTITY"

    existing_proof = bool((annotated or {}).get("primary_award_match") is True
                          and (annotated or {}).get("project_attribution") == "VERIFIED")
    source_project = (claims["same_project_claim"] and claims["primary_spark_claim"]
                      and len(all_urls) >= 2)
    project_verified = existing_proof or source_project
    conflict = claims["project_conflict_claim"] or (
        (annotated or {}).get("project_attribution") == "CONTRADICTED")
    note_dispositions = {h["operational_disposition"] for h in history}
    technical = "TECHNICAL_METADATA_RECOVERY" in note_dispositions
    human = any(h["bounded_human_question_to_verify"] for h in history)

    # These are proof-state summaries, not probabilistic "confidence scores."
    gates = {
        "identity": ("ALREADY_IN_REACH" if is_reach else
                     "ALREADY_PUBLICLY_STAGED" if is_staged else
                     "PUBLIC_NO_ACTION_RECORDED" if is_no_action else
                     "AMBIGUOUS_RECHECK" if identity_review else
                     "SCREENED_NEEDS_FINAL_VERSION_AND_SECONDARY_LINK_CHECK"
                     if preflight_rows else "NO_VERIFIED_PUBLIC_IDENTITY_GATE"),
        "publication": ("PREPRINT_NOT_ELIGIBLE" if claim_preprint and not is_reach else
                        "PUBLISHED_CLAIM_SUPPORTED_IN_PRIOR_SOURCE" if claim_official
                        else "OFFICIAL_RELEASE_NOT_VERIFIED"),
        "same_project_wpo_funding": ("SOURCE_PROOF_RECORDED_VERIFY_LIVE" if project_verified
                                     else "CONFLICT_SOURCE_RECORDED" if conflict
                                     else "EXACT_PRIMARY_PROJECT_PROOF_MISSING"),
        "required_metadata": ("PRIOR_SNAPSHOT_COMPLETE_RECHECK_LIVE"
                              if ((annotated or {}).get("required_metadata_verified") is True
                                  or claims["metadata_complete_claim"])
                              else "INCOMPLETE_OR_NOT_VERIFIED"),
        "contradictions": ("EXPLICIT_PROJECT_EVIDENCE_CONFLICT" if conflict
                           else "NOT_FOUND_IN_STRUCTURED_RESEARCH_NOT_A_NEGATIVE_PROOF"),
        "technical": ("PRIOR_WORKFLOW_RECONCILIATION_FAILURE_NOT_METADATA_ACCESS"
                      if claims["workflow_failure_claim"] else
                      "PRIOR_EXPLICIT_METADATA_ACCESS_FAILURE" if claims["metadata_access_failure_claim"]
                      else "UNSPECIFIED_TECHNICAL_NOTE_NOT_API_ABSENCE_PROOF" if technical
                      else "NO_TECHNICAL_HOLD_RECORDED"),
        "related_output_scope": ("RELATED_OUTPUT_INDEPENDENT_VERIFICATION_REQUIRED"
                                 if any(h["role_in_note"] == "related_output" for h in history)
                                 else "SEED_ORIGINAL_EXPANSION_REMAINS_SEPARATE"),
    }
    return {
        "doi": d, "public_identity": public_state, "public_recorded_statuses": statuses,
        "verified_public_reach": is_reach, "publicly_staged": is_staged,
        "public_no_action": is_no_action, "ambiguous_identity": identity_review,
        "preprint": claim_preprint, "published_claim": claim_official,
        "primary_project_supported_by_prior_evidence": project_verified,
        "contradictory_project_evidence": conflict,
        "technical_hold": technical,
        "prior_workflow_failure": claims["workflow_failure_claim"],
        "explicit_metadata_access_failure": claims["metadata_access_failure_claim"],
        "bounded_human_referral_evidence": human,
        "prior_research_rounds": (annotated or {}).get("research_rounds"),
        "prior_research_budget_exhausted": (annotated or {}).get("research_budget_exhausted") is True,
        "prior_secondary_identity_checked": (annotated or {}).get("secondary_identity_checked") is True,
        "source_url_count": len(all_urls), "source_url_pointers": all_urls[:10],
        "note_event_count": len(history),
        "source_note_sha256": [{"path": h["source_path"], "sha256": h["source_sha256"],
                                 "event_id": h["event_id"]}
                                for h in history],
        "gates": gates,
        "prior_dispositions": sorted(note_dispositions),
        "documented_source_claims": claims,
    }


def compile_decision(a):
    """A bounded next action, never self-approval or irreversible closure."""
    gates = a["gates"]
    d = a["doi"] or "the recorded public code URL"
    missing_project = not a["primary_project_supported_by_prior_evidence"]
    if a["preprint"] and not a["verified_public_reach"]:
        route, owner, reason = ("PREPRINT_MONTHLY_WATCH", "MONTHLY_WATCHLIST",
                                "Preprint is not eligible for new-output staging")
        action = "Monitor official published-version DOI(s) on monthly watchlist; independently screen any final DOI"
        trigger = "Official published version or corrected source publication status"
    elif a["verified_public_reach"]:
        route, owner, reason = ("REUSE_EXISTING_REACH_IDENTITY_KEEP_EXPANSION", "SCOUT_EXPANSION",
                                "Current public source verifies the existing REACH identity")
        action = "Do not propose this original again; separately explore relevant project-linked datasets, code or articles"
        trigger = "New related-output source evidence or a changed public identity"
    elif a["publicly_staged"] and a["contradictory_project_evidence"]:
        route, owner, reason = ("PUBLIC_STAGED_PROJECT_CONFLICT_FLAG_NO_RESTAGE",
                                "PUBLIC_HANDOFF_VERIFICATION",
                                "An existing public proposal has a recorded project-evidence contradiction")
        action = ("Flag contradictory funding evidence for authorized human review of the "
                  "existing public proposal; do not restage, infer import or modify the Hub")
        trigger = "Authenticated human assessment and corrected output-to-primary-project evidence"
    elif a["publicly_staged"]:
        route, owner, reason = ("PUBLIC_PROPOSAL_ALREADY_STAGED_NO_DUPLICATE", "PUBLIC_HANDOFF_VERIFICATION",
                                "Public Scout staging exists; private Hub import remains unknown")
        action = "Check whether the existing public staging was delivered through authorized reviewer workflow; do not create a duplicate"
        trigger = "Authenticated private handoff or materially changed source evidence"
    elif a["public_no_action"]:
        route, owner, reason = ("RETAIN_RECORDED_NO_ACTION_REOPEN_ON_NEW_EVIDENCE", "SCOUT_ON_NEW_EVIDENCE",
                                "Prior public no-action or existing-state disposition")
        action = "Preserve public disposition; separately pursue valid expansion leads only when new source evidence warrants"
        trigger = "Materially different exact DOI/project evidence or authorized reviewer instruction"
    elif a["contradictory_project_evidence"]:
        route, owner, reason = ("PROJECT_ATTRIBUTION_CONFLICT_HOLD", "SCOUT_ON_NEW_EVIDENCE",
                                "Structured source flags a conflicting project/funding association")
        action = "Do not propose. Reopen only with independent exact output-to-primary-WPO-project evidence resolving the contradiction"
        trigger = "New DOI-level funding evidence and matching primary SPARK project source"
    elif a["bounded_human_referral_evidence"] and a["source_url_count"] >= 2:
        route, owner, reason = ("BOUNDED_HUMAN_PROJECT_QUESTION", "HUMAN_PROJECT_ASSESSMENT",
                                "Earlier source-backed research explicitly requests one bounded human judgment")
        action = ("Ask whether " + d + " is an output of the exact primary WPO SPARK project; "
                  "present existing source URLs and disagreement, without reviewer justification requirement")
        trigger = "Specific reviewer response or new exact primary award/deliverable evidence"
    elif (a["technical_hold"] and a["explicit_metadata_access_failure"] and
          not a["prior_research_budget_exhausted"]):
        route, owner, reason = ("DOI_METADATA_RECOVERY_ONLY", "EXACT_DOI_METADATA_RECOVERY",
                                "An explicit DOI metadata access failure, not a workflow error")
        action = "Retry the specific official DOI registry/publisher endpoint once under recovery backoff; preserve an access hold if unavailable"
        trigger = "Recovery retry becomes due or source API responds"
    elif a["prior_workflow_failure"] and not a["published_claim"]:
        route, owner, reason = ("VERIFY_FAILED_WORKFLOW_AND_IDENTITY", "SCOUT_WORKFLOW_DIAGNOSTICS",
                                "Previous workflow validation failure is not failed DOI metadata access")
        action = "Check current reconciliation workflow and fresh public DOI/IR identity before interpreting original evidence"
        trigger = "A successful current validation run and exact source-backed DOI identity result"
    elif ("PROJECT_EVIDENCE_HOLD" in a["prior_dispositions"] or
          a["prior_research_budget_exhausted"]):
        route, owner, reason = ("BOUNDED_PROJECT_EVIDENCE_HOLD", "SCOUT_ON_NEW_EVIDENCE",
                                "Prior source-specific project evidence hold is unresolved")
        action = ("Preserve the lead without repeating generic searches; reopen only for a "
                  "new exact primary SPARK project/output funding source")
        trigger = "New project-specific evidence, verified human instruction, or changed DOI identity"
    elif a["ambiguous_identity"]:
        route, owner, reason = ("TARGETED_IDENTITY_VERSION_CHECK", "SCOUT_BOUNDED_RESEARCH",
                                "Possible REACH or Scout version/identity collision")
        action = "Run one authoritative exact DOI, official NOAA IR URL and canonical version comparison"
        trigger = "One independently corroborated canonical identity result"
    elif gates["publication"] == "OFFICIAL_RELEASE_NOT_VERIFIED":
        route, owner, reason = ("TARGETED_OFFICIAL_PUBLICATION_CHECK", "SCOUT_BOUNDED_RESEARCH",
                                "Official release remains unverified")
        action = "Verify publication/release status from official DOI registry and publisher; if preprint, route monthly watchlist"
        trigger = "Source-recorded official publication/release or preprint"
    elif missing_project:
        route, owner, reason = ("TARGETED_PRIMARY_PROJECT_PROOF", "SCOUT_BOUNDED_RESEARCH",
                                "Same-project primary WPO award remains unverified")
        action = "Check exact primary SPARK Award Number(s) against independent DOI-specific publisher/NOAA IR output evidence once"
        trigger = "Exact output-to-primary-project evidence or a documented contrary award"
    elif not a["prior_secondary_identity_checked"]:
        route, owner, reason = ("TARGETED_SECONDARY_IDENTITY_CHECK", "SCOUT_BOUNDED_RESEARCH",
                                "Secondary REACH/version links need one final screen")
        action = "Run source-pinned full REACH/Scout DOI, title, canonical NOAA IR and version identity check"
        trigger = "Complete source-verified secondary-link identity result"
    elif gates["required_metadata"] == "INCOMPLETE_OR_NOT_VERIFIED":
        route, owner, reason = ("TARGETED_MISSING_METADATA_RECOVERY", "EXACT_DOI_METADATA_RECOVERY",
                                "Required metadata remains unverified")
        action = "Recover only the named incomplete metadata from official DOI registry before normal reviewer preflight"
        trigger = "Verified complete standard 24-column metadata draft"
    elif (a["public_identity"] != "PUBLIC_SCREEN_COMPLETED_NOT_NEW_OUTPUT_PROOF"
          or a["source_url_count"] < 2):
        route, owner, reason = ("TARGETED_INDEPENDENT_IDENTITY_AND_SOURCE_CHECK",
                                "SCOUT_BOUNDED_RESEARCH",
                                "Current complete public identity and two source checks are not established")
        action = "Verify exact DOI against fresh public REACH/Scout and confirm two distinct primary sources once"
        trigger = "Verified source-identified original and independent evidence"
    else:
        # Safety: even this strongest path never automatically publishes.
        route, owner, reason = ("REVIEW_PREFLIGHT_CANDIDATE_NO_AUTO_STAGING",
                                "NORMAL_PUBLIC_REVIEW_PREFLIGHT",
                                "Recorded evidence supports entering normal live revalidation")
        action = "Run live publication, funding, complete identity and 24-column source gates before any reviewer proposal"
        trigger = "Successful independent existing mandatory preflight and authorized public staging"
    return {"recommended_disposition": route, "owner": owner,
            "decision_reason": reason, "next_action": action, "reopen_or_finish_trigger": trigger,
            "decision_is_research_route_only": True,
            "formal_original_completed": False, "separate_expansion_completed": False,
            "public_proposal_created": False,
            "private_hub_write": False, "human_reviewer_approval": False}


def independent_critique(a, decision):
    """Adversarial safety check based on unchanging evidence gates."""
    issues = []
    route = decision["recommended_disposition"]
    if a["preprint"] and not a["verified_public_reach"] and route != "PREPRINT_MONTHLY_WATCH":
        issues.append("PREPRINT_GUARD_VIOLATION")
    if a["verified_public_reach"] and route != "REUSE_EXISTING_REACH_IDENTITY_KEEP_EXPANSION":
        issues.append("REACH_DUPLICATE_FAST_EXIT_VIOLATION")
    if a["contradictory_project_evidence"] and not (
        a["verified_public_reach"] or a["publicly_staged"] or a["public_no_action"] or a["preprint"]
    ) and route != "PROJECT_ATTRIBUTION_CONFLICT_HOLD":
        issues.append("EXPLICIT_PROJECT_CONTRADICTION_IGNORED")
    if route == "BOUNDED_HUMAN_PROJECT_QUESTION" and (
        not a["bounded_human_referral_evidence"] or a["source_url_count"] < 2):
        issues.append("HUMAN_QUESTION_NOT_SOURCE_BACKED")
    if route == "REVIEW_PREFLIGHT_CANDIDATE_NO_AUTO_STAGING":
        if (a["gates"]["publication"] != "PUBLISHED_CLAIM_SUPPORTED_IN_PRIOR_SOURCE" or
                a["public_identity"] != "PUBLIC_SCREEN_COMPLETED_NOT_NEW_OUTPUT_PROOF" or
                a["source_url_count"] < 2 or
                not a["primary_project_supported_by_prior_evidence"] or
                a["contradictory_project_evidence"] or
                not a["prior_secondary_identity_checked"] or
                a["gates"]["required_metadata"] == "INCOMPLETE_OR_NOT_VERIFIED"):
            issues.append("REVIEW_PREFLIGHT_WITH_FAILED_MANDATORY_GATE")
    if a["technical_hold"] and a["gates"]["technical"] == "NO_TECHNICAL_HOLD_RECORDED":
        issues.append("TECHNICAL_ACCESS_FAILURE_RECAST_AS_ABSENCE")
    for b in ("formal_original_completed", "separate_expansion_completed",
              "public_proposal_created", "private_hub_write", "human_reviewer_approval"):
        if decision[b] is not False:
            issues.append("UNAUTHORIZED_ACTION_" + b.upper())
    return {
        "adversarial_gate_checks_passed": not issues,
        "blocking_safety_issues": issues,
        "missing_for_autonomous_reviewer_handoff": [
            label for label, tested in (
                ("LIVE_SAME_PROJECT_WPO_FUNDING", a["primary_project_supported_by_prior_evidence"]),
                ("OFFICIAL_RELEASE", a["gates"]["publication"] ==
                 "PUBLISHED_CLAIM_SUPPORTED_IN_PRIOR_SOURCE"),
                ("SECONDARY_IDENTITY_CHECK", a["prior_secondary_identity_checked"]),
                ("COMPLETE_METADATA", a["gates"]["required_metadata"] !=
                 "INCOMPLETE_OR_NOT_VERIFIED"),
                ("NO_CONTRADICTION", not a["contradictory_project_evidence"]),
            ) if not tested
        ],
        "grant_clue_or_author_overlap_never_confirms_funding": True,
        "official_metadata_pointer_not_current_without_recheck": True,
        "private_hub_delivery_not_inferred": True,
    }


def build(root=ROOT):
    registry = build_journal(root)
    if registry["schema"] != "reach-scout-all-lane-research-outcomes-v1":
        raise ValueError("Unrecognized source-backed research journal")
    verified = preflight(root)
    if verified["schema"] != "reach-scout-unified-source-preflight-v1":
        raise ValueError("Unrecognized current source preflight")
    annotated, annotated_sha = prior_cases(root)
    event_by_identity = defaultdict(list)
    docs_by_path = {}
    for e in registry["events"]:
        if e.get("formal_original_closed") or e.get("new_public_proposal"):
            raise ValueError("Research registry note violates human safety boundary")
        rel = e["source_path"]
        if rel not in registry["source_sha256"]:
            raise ValueError("Research evidence note is not source SHA-pinned")
        if rel not in docs_by_path:
            docs_by_path[rel], checksum = json_source(root, rel)
            if checksum != registry["source_sha256"][rel]:
                raise ValueError("Research note was modified during pilot run")
        event_by_identity[e["identity"]].append(e)

    # Research note scope is deliberately 34 distinct identities today;
    # this pilot must not silently expand to all 827 source-only records.
    if len(event_by_identity) != registry["distinct_research_identities"]:
        raise ValueError("Pilot dropped recorded research identities")
    current_identity = defaultdict(list)
    for item in verified["cases"]:
        d = norm_doi(item["doi"])
        current_identity["doi:" + d].append(item)
    output = []
    for original in registry["cases"]:
        identity = original["identity"]
        events = event_by_identity.pop(identity)
        if not events:
            raise ValueError("Registry identity lacks source event")
        d = norm_doi(identity[4:]) if identity.startswith("doi:") else None
        annotated_case = annotated.get(d)
        prior_docs = [identity_specific_note(docs_by_path[e["source_path"]], identity)
                      for e in events]
        a = evidence_assessment(identity, events, current_identity.get(identity, []),
                                annotated_case, prior_docs)
        decision = compile_decision(a)
        critique = independent_critique(a, decision)
        if not critique["adversarial_gate_checks_passed"]:
            raise ValueError("Pilot decision safety critique failed for " + identity +
                             ": " + str(critique["blocking_safety_issues"]))
        output.append({
            "identity": identity, "output_kind": ("DOI" if d else "PUBLIC_CODE_OR_URL"),
            "source_recorded_dispositions": original["observed_dispositions"],
            "latest_recorded_disposition_unchanged": original["latest_operational_disposition"],
            "evaluation": a, "compiled_decision": decision,
            "independent_critique": critique,
            "read_only": True, "existing_reviewer_status_unchanged": True,
        })
    if event_by_identity:
        raise ValueError("Registry cases do not cover each event's identity")
    counts = Counter(x["compiled_decision"]["recommended_disposition"] for x in output)
    owners = Counter(x["compiled_decision"]["owner"] for x in output)
    actions_requiring_active_work = {
        "BOUNDED_HUMAN_PROJECT_QUESTION", "DOI_METADATA_RECOVERY_ONLY",
        "TARGETED_IDENTITY_VERSION_CHECK", "TARGETED_OFFICIAL_PUBLICATION_CHECK",
        "TARGETED_PRIMARY_PROJECT_PROOF", "TARGETED_SECONDARY_IDENTITY_CHECK",
        "TARGETED_MISSING_METADATA_RECOVERY", "TARGETED_INDEPENDENT_IDENTITY_AND_SOURCE_CHECK",
        "VERIFY_FAILED_WORKFLOW_AND_IDENTITY",
        "PUBLIC_STAGED_PROJECT_CONFLICT_FLAG_NO_RESTAGE",
        "REVIEW_PREFLIGHT_CANDIDATE_NO_AUTO_STAGING",
    }
    flagged = [x for x in output
               if x["compiled_decision"]["recommended_disposition"] in actions_requiring_active_work]
    action_preview = [{
        "identity": x["identity"],
        "recommended_disposition": x["compiled_decision"]["recommended_disposition"],
        "owner": x["compiled_decision"]["owner"],
        "next_action": x["compiled_decision"]["next_action"],
        "evidence_note_paths": [s["path"] for s in x["evaluation"]["source_note_sha256"]],
    } for x in sorted(flagged, key=lambda x: (
        x["compiled_decision"]["owner"], x["identity"]))]
    note_events = sum(x["evaluation"]["note_event_count"] for x in output)
    if note_events != registry["research_note_events"]:
        raise ValueError("Pilot failed to preserve all research-note evidence")
    if not all(x["read_only"] and x["independent_critique"]["adversarial_gate_checks_passed"]
               for x in output):
        raise ValueError("Unverified safety critique or write activity")
    source_shas = {
        "annotated_prior_case_snapshot": annotated_sha,
        "live_unified_preflight_source_fingerprint": verified["identity_index_fingerprint"],
        "public_research_notes": registry["source_sha256"],
        "preflight_input_manifest_shas": verified["source_manifest_sha256"],
    }
    return {
        "schema": SCHEMA,
        "pilot_mode": "READ_ONLY_STRUCTURED_EVIDENCE_REVIEW_NO_REAL_WORLD_ACTIONS",
        "source_fingerprint": digest(stable_bytes(source_shas)),
        "source_sha256": source_shas,
        "source_research_note_events": note_events,
        "unique_research_identities": len(output),
        "annotated_decision_cases_available": len(annotated),
        "source_case_dispositions_unchanged": True,
        "recommended_disposition_counts": dict(sorted(counts.items())),
        "recommended_owner_counts": dict(sorted(owners.items())),
        "proposed_active_followups_not_executed": len(action_preview),
        "active_followup_preview": action_preview,
        "human_questions_identified_not_delivered": counts["BOUNDED_HUMAN_PROJECT_QUESTION"],
        "research_ready_review_proposals_automatically_created": 0,
        "private_hub_imports": "NOT_VERIFIED",
        "human_approvals": "NOT_VERIFIED",
        "published_reach_additions": 0,
        "formal_original_or_expansion_closures": 0,
        "source_author_pi_collaborator_names_copied": False,
        "policy": ("This rubric compiles decision-support suggestions for source-backed research "
                   "history. Unknown funding, source access and project scope are never recast "
                   "as negative proof. A held lead can be resolved as a bounded research *pass* "
                   "without formally closing originals or their expansion. The pilot does not "
                   "contact reviewers, publish Scout proposals, or write any downstream system."),
        "cases": sorted(output, key=lambda x: x["identity"]),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--check", action="store_true")
    a = p.parse_args()
    report = build()
    path = ROOT / DEST
    raw = json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    if a.check:
        if not path.is_file() or path.read_text(encoding="utf-8") != raw:
            raise ValueError("Evidence-action pilot is stale relative to source")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.is_file() or path.read_text(encoding="utf-8") != raw:
            path.write_text(raw, encoding="utf-8")
    print(json.dumps({
        "research_identities": report["unique_research_identities"],
        "preserved_note_events": report["source_research_note_events"],
        "recommended_routes": report["recommended_disposition_counts"],
        "proposals_published": report["research_ready_review_proposals_automatically_created"],
        "private_hub_imports": report["private_hub_imports"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
