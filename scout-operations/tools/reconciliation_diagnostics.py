"""Explain failed terminal gates without changing past statuses or decisions."""
import re

def missing_evidence(entry, reviewed_paths, *, crossref=False):
    result=[]
    def need(field, good):
        if not good:
            result.append(field)
    checked=entry.get("checked_sources") or []
    need("checked_sources_https",bool(checked) and all(
        isinstance(x,str) and x.startswith("https://") for x in checked))
    need("research_notes_25_chars",len(str(entry.get("research_notes") or "").strip())>=25)
    need("verified_at",bool(entry.get("verified_at")))
    snap=str(entry.get("reach_snapshot") or "")
    valid_snapshot=bool(re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}",snap))
    if crossref:
        valid_snapshot=valid_snapshot or bool(re.search(r"source SHA-256 [0-9a-f]{64}",snap))
    need("reach_snapshot_sha",valid_snapshot)
    need("funding_basis_12_chars",len(str(entry.get("funding_basis") or "").strip())>=12)
    need("related_outputs_checked_12_chars",len(str(entry.get("related_outputs_checked") or "").strip())>=12)
    status=entry.get("status")
    if status=="already_in_reach":
        match=entry.get("reach_match") or entry.get("existing_reach_match")
        need("exact_existing_reach_identity",bool(match))
        if crossref:
            need("reach_uid_record_id",bool(match and
                re.fullmatch(r"reach-\d+",str(match.get("record_id") or "")) and
                str(match.get("reach_uid") or "").startswith("reachuid-v1-")))
            need("reach_detail_shard_evidence",any(
                "reach-dashboard" in str(s) and "/details/" in str(s) for s in checked))
    if status in ("forwarded_to_hub","metadata_update_forwarded"):
        need("active_scout_feed_batch",entry.get("scout_batch_path") in reviewed_paths)
    if status=="no_action":
        need("no_action_reason_20_chars",len(str(entry.get("no_action_reason") or "").strip())>=20)
    if status=="human_metadata_needed":
        need("metadata_recovery_exhausted",entry.get("metadata_recovery_exhausted") is True)
        need("reviewer_question",bool(str(entry.get("reviewer_question") or "").strip()))
        need("missing_evidence_list",bool(entry.get("missing_evidence")))
        need("reviewer_handoff_status",entry.get("human_handoff_status") in
             ("pending_hub_intake","staged_for_review"))
    # Preprint originals can close without a WPO award attribution.
    preprint_exception=(crossref and status=="no_action" and
        entry.get("no_action_subtype")=="PREPRINT_NOT_ELIGIBLE_AS_NEW_OUTPUT")
    if preprint_exception:
        need("preprint_status_verified",entry.get("publication_status")=="preprint"
             and entry.get("source_posted_content_verified") is True)
        need("preprint_watchlist_entry",entry.get("preprint_watchlist_status")=="tracking_preprint")
        need("original_output_not_eligible", (entry.get("original_output_gate") or {}).get(
            "eligible_for_new_output_review") is False)
    else:
        awards=set(entry.get("award_numbers") or [])
        verified=set(entry.get("verified_awards") or [])
        if crossref and status=="already_in_reach":
            need("award_evidence_subset_only",verified.issubset(awards))
        elif status=="human_metadata_needed":
            need("verified_project_award_subset",bool(verified) and verified.issubset(awards))
        else:
            need("verified_award_alignment",verified==awards)
    return sorted(set(result))
