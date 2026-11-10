# Hourly Scout mission measurement and guarded closeout — v1
Effective proposal: November 10, 2026. This contract supplements SCOUT_OPERATING_POLICY_V2.md and does not override its privacy, evidence, eligibility, or intake priorities.

## One record per ACTUALLY completed hourly mission
Write a privacy-minimized JSON record at `scout-operations/reports/hourly-missions/YYYY-MM-DDTHHMMSSZ-<mission-id>.json` only after the mission has actually finished. Never infer mission completion from a scheduled trigger or a successful CI test. Required fields:

```json
{
  "schema": "reach-scout-hourly-mission-outcome-v1",
  "mission_id": "unique non-personal ID",
  "started_at_utc": "ISO-8601",
  "completed_at_utc": "ISO-8601",
  "policy_commit_sha": "40-character SHA or NOT_VERIFIED",
  "memory_source_fingerprint": "SHA-256 or NOT_VERIFIED",
  "memory_builder_policy_sha256": "SHA-256 or NOT_VERIFIED",
  "lane": "monthly_original | historical_crossref_original | historical_datacite_original | independent_original | related_expansion | mixed",
  "selected_original_dois": [],
  "selected_expansion_seed_dois": [],
  "fast_exited_public_reach": [],
  "fast_exited_public_scout": [],
  "new_original_full_decisions": [],
  "new_expansion_decisions": [],
  "research_only_holds": [],
  "technical_or_funding_holds": [],
  "published_public_batch_urls": [],
  "guarded_handoff_run_urls": [],
  "handoff_status": "PUBLISHED_PUBLIC_SCOUT | VERIFIED_ALREADY_PUBLIC | BLOCKED | NOT_ATTEMPTED | NOT_VERIFIED",
  "handoff_blocker": null,
  "prior_note_sha256_reused": [],
  "prior_metadata_fingerprints_reused": [],
  "cache_hits_observed": null,
  "external_requests_observed": null,
  "avoided_requests_measured": null,
  "private_hub_import": "NOT_VERIFIED",
  "human_decision": "NOT_VERIFIED",
  "public_reach_addition": "NOT_VERIFIED"
}
```

Use null for uninstrumented request metrics, NEVER zero. Include source URLs and source SHAs in individual disposition notes; do not copy confidential reviewer identifiers or private feedback into public reports. Distinct DOI identities must be canonicalized; count each identity only once per mission and across overlapping lanes. A new original full decision requires a source-backed, identity-checked disposition; a note-only project-evidence hold is not a completion. A public handoff requires the canonical 24-column validation and confirmation in the ACTIVE public manifest. A staged draft is not a published handoff. A known REACH original remains an eligible independent expansion seed, not a new original.

## Immediate guarded closeout when eligible
After bounded source screening and REACH + public Scout duplicate checks, route a novel eligible original to the existing guarded public-review mechanism in the SAME mission when the workflow supports that lane and a safe execution path is available. Reuse the current historical Crossref 459 guarded processor; do not bypass its source freshness, exact-output funding, preprint, identity, 24-column, manifest, concurrency, or privacy checks. For other lanes retain their existing guarded intake; do not claim cross-lane integration. When the mission cannot initiate or verify the guarded handoff, record BLOCKED or NOT_VERIFIED with the exact reason and next retry, then advance to another distinct candidate if time allows. Never call a queued workflow, draft, or source note a completed publication.

## Reuse measurement
Before each external lookup, check applicable graph/node source fingerprints, prior immutable notes, verified metadata cache and previous dispositions. Record actual note SHAs and cache fingerprint identifiers consulted. Instrument cache hits and real network requests at the lookup boundary where observable; record null otherwise. Count demonstrably avoided requests only where a measured comparison exists; do not extrapolate from the independent 16/16 reuse test. Distinguish source-note changes from regenerated index artifacts. Preserve original/expansion lane boundaries, monthly intake priority and preprint watchlist exclusions.

## Evaluation and QA
Compute completed-mission denominators from timestamped mission records only. Separately report original full decisions, public handoffs, research holds, expansion cases, fast exits, cache reuse and observed requests; deduplicate DOI identities across lanes. Do not equate GitHub Actions success with hourly mission success. Run schema validation on sample successful, blocked and uninstrumented mission fixtures before enabling automated reporting. No private Hub import, reviewer approval, Smartsheet insertion or REACH addition may be inferred from public artifacts.
