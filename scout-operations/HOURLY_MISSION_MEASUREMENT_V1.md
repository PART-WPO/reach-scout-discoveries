# Hourly Scout mission measurement and guarded closeout — v1
Effective proposal: November 10, 2026. This contract supplements SCOUT_OPERATING_POLICY_V2.md and does not override its privacy, evidence, eligibility, or intake priorities.

## One record per ACTUALLY completed hourly mission
Write a privacy-minimized JSON record at `scout-operations/reports/hourly-missions/YYYY-MM-DDTHHMMSSZ-<mission-id>.json` only after the mission has actually finished. Never infer mission completion from a scheduled trigger or a successful CI test. Required fields:

```json
{
  "schema": "reach-scout-hourly-mission-outcome-v1",
  "producer": "chatgpt_hourly_mission",
  "not_chatgpt_hourly_mission": false,
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

## Production integration: distinct measurement producers
- **ChatGPT hourly Scout task:** At the beginning of actual execution capture the observed start timestamp; at completed closeout capture the actual end time. If connected GitHub write access and accurate observed timestamps are available, validate and commit ONE new immutable public record under `scout-operations/reports/hourly-missions/`; use `producer: chatgpt_hourly_mission` and `not_chatgpt_hourly_mission: false`. Record new original decisions only when source-backed and truly completed; a research hold, queued handoff, duplicate exit or failed lookup never satisfies the one-original target. If no safe write access or reliable observation is possible, report `NOT_INSTRUMENTED` with the blocker in the mission response and **do not fabricate a record**.
- **GitHub guarded Crossref backstop:** The existing end-to-end processor runs its own exact-DOI publication gates and now creates source-backed records under `scout-operations/reports/guarded-backstop-missions/` via `write_hourly_mission_metrics.py`, with `producer: github_guarded_crossref_backstop` and `not_chatgpt_hourly_mission: true`. The workflow writes the record only after its bounded run and the applicable guarded-publication gate, then commits the record with the validated batch or blocker. These jobs are NOT ChatGPT hourly research missions, and pre-existing queue skips are not counted as new mission fast exits.
- **Independent metadata lookups:** `audit_independent_lookup.py` measures persistent cache reuse actually reported by the existing SHA/TTL-verifying resolver and counts real DataCite/Crossref provider attempts from uncached responses. Reports are under `scout-operations/reports/research-memory-reuse/`. The count deliberately excludes Zenodo scope checks, GitHub metadata, IR checks, other HTTP calls, and all requests originally recorded inside reused cached responses. Avoided requests remain `null` without a measured counterfactual.
- **Scorecard:** `summarize_hourly_missions.py` aggregates the two mission-producer folders separately. Rates divide by *actually recorded completed mission records*, not schedules or GitHub test runs. A missing record means **missing coverage**, not proof no run occurred. A current public batch does not imply a private Hub import.

Do not rewrite or backfill earlier runs with guessed timestamps or inferred hits. Existing records are append-only; use canonical DOI identities and source fingerprints. Before each ChatGPT hourly mission, read the existing guarded backstop outcomes to avoid duplicate research. Where a **lane-compatible** guarded publication path is available, carry it through in the same mission; otherwise record the precise unavailable intake gate and advance to another distinct candidate. Never use the Crossref 459 automated gate for ineligible/other cohorts merely to meet the target.


## Instrumentation closeout and source-driven discovery
The hourly ChatGPT executor must commit one unique, schema-validated, immutable record for each truly executed run, including zero-discovery runs, whenever observed start/end times and GitHub write permission can be verified. A missing record is a coverage gap, not proof no run occurred. Never backfill runs from scheduler timestamps. If write permission or reliable event time is absent, report NOT_INSTRUMENTED with a specific blocker. Existing GitHub guarded-backstop records are separate observations and cannot be copied into ChatGPT records.

In the current scorecard, github_bounded_expansion_research is a third, separate research-only section, not another producer of completed original handoffs. Count unique SHA-supported REACH seeds and separately discovered DOI identities, with a distinct count of official metadata retrieval; an API/publisher/NOAA IR source match alone never increments completed expansions, public Scout handoffs, private reviewer approvals, or public REACH additions. Counts derive from immutable scout-operations/reports/bounded-expansion-research/*.json reports and de-duplicate identities across retries.
