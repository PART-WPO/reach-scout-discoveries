# Historical Crossref seeded-discovery test — November 2, 2026

**Scope:** Independently harvest all available years of Crossref publications with an exact structured `funder.award` match to one or more SPARK **primary** award identifiers. Search the complete published SPARK primary-award shard catalog; related/umbrella-only funding identifiers are not eligible search seeds. Preserve full FY25+ task-qualified award identifiers, including suffixes. Monthly DataCite/Crossref, the 188 completed historical DataCite records, and all prior human decisions remain untouched.

**Research inputs:**
- `api-discoveries/historical-crossref/manifest.json` with immutable, SHA-verified `batches/*.csv`.
- `scout-operations/historical-crossref-triage.json`, and `historical-crossref-coverage.json`.
- `scout-operations/active-workstream.json` should route to `historical_crossref_triage` once monthly original and expansion work is clear.
- GitHub Actions harvest only creates a **research** backlog. It does not inspect full REACH, make final duplicate decisions, stage in private Discovery Hub, or publish to REACH.

**Per-DOI expedited Scout mission protocol (two independent lanes):**

1. **Original publication identity/dedup lane.** Read all shards of full public REACH agent-data/manifest.json and every detail/secondary DOI/URL link; compare normalized DOI, publisher URL, title/award, preprint versus final, concept/version, and Smartsheet-backed publication identifiers when publicly visible. Also inspect every published Scout manifest/batch plus research queues and retained feedback. Match on exact identity before declaring `already_in_reach`, and record the specific REACH match and its current snapshot. If already an active Scout candidate or preexisting review unit, **do not create a second candidate**; link/retain the original queue entry and evidence. Existing REACH records may support a separately evidenced metadata correction but not a duplicate new-output proposal. Treat cross-queue matches in the auto-reconciled ledger as hints until checked. Only genuinely new, eligible records with exact primary-award support and critical author, date, abstract, type, link and parent evidence may go through the verified 24-column CSV intake + validated manifest and human approval. Keep all private Hub imports/approvals explicitly unverified until observed.

2. **Independently preserved API-seeded expansion lane.** **EVERY Crossref DOI remains a research seed, including `already_in_reach`, `no_action` and already-in-Scout originals.** Examine Crossref relations/references, publisher data/code availability and supporting-information links, linked repository DOIs, connected software, datasets/instruments, NOAA IR entries, code and WPO project publications. Follow credible project-specific leads. Record original seed DOI, link path, award evidence, checked source URLs, and whether a lead is already in REACH or the Scout queue. A related output is never automatically a new eligible output; independently establish standalone identity, primary-award or corroborated same-project WPO funding, current DOI/version deduplication, required metadata, and a valid review path. Publish only individually verified new outputs via the existing Scout intake protocol. Do not change the seed's original `Direct API` origin or mislabel related discoveries; verified new related outputs use `API-seeded expansion`.

**Ledger and closure:** The Crossref source DOI and its seed-expansion investigation remain separate. A confirmed existing original may be closed while `seed_expansion_status` stays pending. A full case is research-complete only when both original disposition and documented expansion are complete. Record checked_sources, full REACH SHA, verified exact primary awards, source-specific duplicates, expansion evidence/limits, and appropriate no-action or human-needed findings. Use initial plus one bounded distinct-source follow-up before escalation; do not loop indefinitely or claim a missing citation proves ineligibility. DataCite created date convention is unchanged; Crossref Pub Date prefers published-print, then published-online, with first-of-month normalization for month precision; never substitute Crossref created.

**Evaluation metrics:**
- Award IDs searched, Crossref award/output matches, unique source DOIs, full source checksum coverage, API failures.
- Exact REACH duplicates, already-in-Scout candidates, previously queued but not published, ambiguous title/version matches requiring review.
- New eligible originals staged in validated public Scout feed; private Hub imports separately observed; human approvals/public REACH additions separately observed.
- Existing-publication seeds explored, source links traversed, distinct expansion leads, new verified related outputs, already-REACH expanded matches, and blocked research.
- Median elapsed time from source intake to first duplicate assessment and to defensible final source disposition, separating originals from expansions.

**Priority and schedule:** Crossref historical backlog follows current month's completed original and expansion work, then precedes ordinary completed-DataCite reassessment and unsystematic older-award exploration. A new monthly intake preempts it. Use existing weekday hourly Scout missions; no additional always-on worker, weekend historical research, or paid service. After the Crossref backlog is truly cleared, return to normal SPARK award research.


## November 3 REACH-first backlog screening — authoritative two-phase override

This section supersedes any older instruction requiring full funding, source, or expansion research before a first-pass REACH identity decision on every historical Crossref original.

**Phase 1 — screen the ENTIRE 614-DOI historical Crossref original backlog first.** Build or reuse a checksum-verified snapshot of ALL public REACH index and detail shards (DOI, DOI URLs, secondary URLs, titles, versions, and record UID). Normalize all source DOI identities, then process them in large bounded batches using the same snapshot; do not reload every REACH shard for every DOI. Record one of: CONFIRMED_IN_REACH (exact DOI/official canonical DOI, or sufficiently corroborated title + secondary URL/version identity; save REACH UID, path and evidence), NOT_FOUND_IN_REACH (not a verified new output), or POSSIBLE_MATCH (ambiguous title/version/secondary URL, with precise follow-up). A source DOI may also have ALREADY_IN_SCOUT flag independently; that is not an REACH yes. Existing historical-crossref-triage.json status values must remain schema-compatible; add screening metadata fields rather than forcing unsupported status changes. Preserve existing terminal original dispositions and human decisions. For confirmed REACH matches, mark original already_in_reach only when verified, and do not spend time verifying its funding or preparing a new candidate. Preserve every source DOI as a separate expansion seed regardless of original screening result. Do not treat a missing DOI string alone as proof of absence if REACH uses a publisher/NOAA IR URL.

**Phase 2 — only after all source originals receive first-pass REACH screening:** investigate NOT_FOUND originals for already published/pending Scout candidates and human decisions, exact same-project SPARK primary award including FY25+ suffix, preprint/version eligibility, metadata, and candidate staging. Investigate POSSIBLE_MATCH with narrow identity checks before any funding work. Independently research related outputs in the expansion lane, including seeds whose originals are already in REACH; expansion does not hold up original screening or closure. Monthly new arrivals still preempt historical screening. Keep the preprint intake gate and optional NOAA IR lookup for genuinely new outputs; do not perform hourly watchlist/IR sweeps.

**Every hourly mission during Phase 1:** process a substantial bounded screening batch, persist DOI-level evidence and cursor/progress in the existing ledger or a dedicated screening checkpoint, commit researched/validated changes, and regenerate existing coverage/workstream via repository scripts where execution is available. Do not claim regeneration if unavailable. Report total screened/614, confirmed REACH yes, not found, possible match, Scout overlap, remaining unscreened, and independent original/expansion completed counts. Avoid repeating full funding checks and detailed expansion work during Phase 1. No automated REACH, Smartsheet, Hub approval, or private import; existing 24-column inbox and GitHub Action gates remain mandatory for later candidates. No paid worker or schedule change.


## November 4 actionable cache routing — overrides blanket POSSIBLE_MATCH handling

The checksum-validated read-only router `scout-operations/historical-crossref-screening/build_actionable_routing.py` derives `actionable-routing.json` from the original immutable Crossref source batches, screening checkpoints and verified REACH comparison cache. Do not interpret the old 613 POSSIBLE_MATCH screening labels as 613 genuine ambiguities. Regenerate routing when source/checkpoint/cache SHA changes; never use a stale routing report. Do not rewrite historical screening batches or overwrite any human decisions.

Routing rules:
- `CONFIRMED_IN_REACH`: retain the original verified REACH identity; skip further original funding/metadata work, but preserve its independent DOI-seeded expansion lane.
- `LIKELY_IN_REACH`: one bounded DOI/title/version/detail verification using listed matching REACH UID and detail shard, then either confirm existing identity or advance to original investigation. A title-only hit is NOT a confirmed duplicate. Do not spend time on funding first.
- `NOT_FOUND_IN_REACH_INDEX`: zero exact DOI and normalized-title hits in the complete validated index; advance to the second gate (Scout feed/active queue/human decisions) and then primary-award, publication eligibility and metadata work. This does not assert global absence or automatically stage a candidate.
- `SCREENING_INCOMPLETE`: repair missing source title or stale/incomplete cache, then rerun. Never classify a failed cache lookup as not found.

The routing report is a screening worklist, not a replacement for `historical-crossref-triage.json`, its verified terminal statuses, or the expansion seed queue. Prioritize the 146 currently not-found originals after existing monthly intake and dedup against Scout feed; process likely matches with bounded detail checks. Keep preprint hold, NOAA IR only for genuinely new eligible outputs, primary-award-only inclusion, 24-column staging validation and no automatic private Hub/REACH writes. Every mission should report: routing snapshot hash, confirmed, likely, not-found, incomplete, number of bounded checks resolved, originals advanced, originals closed, seed expansions explored, and public Scout feed additions. Do not claim a screening route is completed original research. If router validation fails, stop routing changes and report the failure.


## November 4 shared decision/identity gate — operational integration

The versioned decision contract is `scout-operations/decision-contract-v1.md`;
the tested shared read-only CLI is `scout-operations/tools/decision_pipeline.py`.
Use the validated `scout-operations/identity-cache/public-identity-index.json`
as an indexed REACH **and** Scout published/inbox lookup for hourly DOI work,
only when its source fingerprint is current. The new GitHub Action
`.github/workflows/scout-decision-pipeline.yml` validates the public REACH
manifest against the verified comparison cache, rebuilds the index when source
snapshots or inbox change, runs regressions, and persists immutable test DOI
decision checkpoints. It does **not** insert candidates or certify any private
Discovery Hub state. GitHub Actions token-originated commits may not themselves
trigger a second workflow; verify refresh results rather than assuming a run.

For each actual newly investigated DOI, use the cached lookup in one batch
rather than reload all REACH shards; record exact DOI/URL, normalized-title
ambiguities, Scout published/inbox overlaps, source snapshot fingerprint and
any private-review decision availability. After initial and one distinct-source
follow-up, derive an evidence-backed checkpoint using the same CLI `evaluate`
command with source URLs and explicit checked fields. Reuse an unchanged
revision; new evidence produces an append-only revision. Do not mark a gate
passed from absence in the public index alone.

**Important exception:** monthly Direct API originals retain the authorized
structured-funding primary-award human-review fast path *unless conflicting
project evidence exists*. Historical/independently found items need a
specific same-project WPO bridge before a draft recommendation. Neither track
bypasses the existing validated 24-column intake or human approval. Keep
each original's independent expansion seed open until separately assessed.


## November 5, 2026 — Scout 2.0 improvement 1: bulk verified identity fast path (authoritative)

This section supersedes older instructions that route EVERY exact DOI/official NOAA IR URL match to repeated AI original-publication research, or rely on the old one-confirmed/479-likely/134-index-negative screening baseline. Read the CURRENT generated `scout-operations/historical-crossref-screening/actionable-routing.json` and its matching SHA-pinned operational scorecard; never hardcode those numbers.

A single source-SHA-verified GitHub Action compares all source DOIs against the full REACH index/detail cache, the complete public Scout queue/inbox, and the official checksum-verified NOAA IR DOI index. The shared deterministic helper `scout-operations/tools/bulk_reach_dedup.py` may mark the SCREENING outcome `CONFIRMED_IN_REACH` only if there is exactly one REACH UID with a stable detail/record path, normalized exact title agreement, and either:
1. A direct exact DOI match to the REACH record; or
2. An official uniquely mapped NOAA IR DOI -> canonical repository URL -> exact REACH URL identity with no conflicting DOI/version mapping.

Other matches remain `LIKELY_IN_REACH` for a **single bounded identity/version check**; title-only evidence, multiple REACH UIDs, contradictory normalized title, and ambiguous repository crosswalks must not auto-confirm. A current public index negative is only permission to proceed with Scout queue/human decision/funding/metadata research, NOT proof of a novel publication.

For strong verified public existing-REACH identity, do NOT repeat original-candidate WPO funding or metadata searches or create another new-output Hub proposal. Preserve source DOI, supporting evidence, the original immutable audit, and a separate linked-output exploration opportunity. Verified public identity in this routing report is **not** an automatically verified historical research terminal status, reviewer approval, private Hub import, or completed DOI-seeded expansion. Formal original-ledger closure still requires the protected evidence/reconciliation process. Subsequent candidate metadata correction requires its own case and human review.

At first dry-run test, 433/614 have a unique verified strong match (85 direct DOI, 348 official IR URL), 47 need narrow identity review (24 title-only, 12 multiple REACH records, 11 strong identity but title/version disagreement), and 134 have no match in the complete public REACH index. These are initial test figures only; update from each live source snapshot.

No new APIs, hourly workers, third-party services, automatic Smartsheet/REACH writes or changes to prior human decisions are authorized by this screening improvement. Reviewer-capacity planning target is **20 or more substantive review decisions per week**, to be addressed in a separate later improvement rather than artificially capped or filled with duplicative proposals.
