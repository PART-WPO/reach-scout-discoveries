# REACH Scout — Authoritative Operating Contract
**Effective November 9, 2026 (consolidated).** This is the **single active policy** for Scout's discovery, hourly research and guarded public-review handoffs. In conflicts, it supersedes all dated and cumulative task instructions. Preserve older evidence and decisions without rewriting history. The full previous policy was copied *verbatim* to [the November 9 archive](policy-archive/SCOUT_OPERATING_POLICY_V2_2026-11-09_pre_consolidation.md); archival policy text is not active instructions.

## Mission and operating boundaries
Discover distinct, authentic WPO-funded outputs (publications, data, instruments, code and reports); eliminate existing REACH/Scout records early; research plausible leads with bounded source evidence; and send **validated public proposals for authorized human review**. The planning capacity target is ~20+ reviewer decisions/week, **not** verified throughput or a quota to manufacture candidate records.

Keep existing ChatGPT hourly task schedule unchanged. The **GitHub guarded historical Crossref backstop** runs at UTC minute :34 on Eastern weekdays (GitHub cron is approximate, with a source-checked Eastern weekday gate). Existing first-of-month monthly DataCite/Crossref intake takes priority, including the established weekend first-of-month exception and the monthly preprint watchlist. Then process outstanding monthly original decisions, historical Crossref/DataCite, independently discovered research, and distinct DOI-seeded expansions. Keep each original-output decision separate from research into related outputs. The morning briefing is a read-only weekday 8 AM summary.

## Decision order — every discovery mode
1. **Exact identity and feedback.** Consult SHA-verified complete REACH shards/cache, published Scout manifest **and inbox**, canonical DOI/title/URLs, official NOAA IR DOI-to-REACH URL and unique UID, plus signed private review feedback **only if available**. An exact DOI+matching title or unique official IR URL+title+REACH UID can establish an existing public identity. Ambiguous versions, multiple candidates or title-only overlap require bounded identity review. An existing public Scout proposal is one review unit across monthly/historical mirrors, even without confirmed private import. Exit known new-output duplicates promptly, but retain eligible *separate* expansion leads.
2. **Publication/version.** Original preprint and posted-content DOIs remain outside public Scout, Discovery Hub and REACH. Track through the scheduled first-of-month watchlist; if an official published version is found, research its separate DOI and retire earlier watchlist iterations when that published version already exists in REACH. Original correction, corrigendum, erratum, retraction and expression-of-concern *notices* go to the separate special-publication eligibility lane (below), not the standard original-article queue.
3. **Funding on this exact output.** An official publisher-deposited Crossref funder award for the **same DOI** with the program segment **459 immediately after OAR or OARX** confirms WPO funding (e.g., `NA21OAR4590367`, `NA26OARX459C0001`). Other segments `432`, `011`, `469` and `419` alone are **not** WPO confirmation, but do not negate an independently verified exact-DOI 459. A 459-looking SPARK lead, author overlap, project title, related DOI or unverified note alone is not output-level award proof. SPARK attribution queries use the primary **Award Number(s)** only, never **Related Award Numbers**. Validate full FY25+ award formats; do not invent or truncate identifiers.
4. **Disposition.** For an officially published, publicly novel output with exact-DOI publisher-deposited 459 matching award context, use **NEW CANDIDATE** and populate the verified full WPO award and official funding URL. Human reviewers must select/verify the correct SPARK primary parent, especially with multiple awards; leave unselected parent metadata blank. For plausible output-level associations without verified funding, use bounded **NEEDS INVESTIGATION** and a concise reviewer question, not an invented award; publish only if the corresponding eligibility/identity gates pass. Strong source contradictions can support deferral or exclusion, but a missing award or 432-only context alone is not proof an output is unrelated. Previous reviewer decisions require authenticated reconciliation, never replacement by guesswork.
5. **Metadata and provenance.** Use canonical **24-column** Scout validation for all public proposals. Crossref publication date: `published-print`, then `published-online`, then `published`/`issued`, recording imputed first-of-month dates for year-month precision. Never use Crossref created/deposit date as Pub Date. For legitimate DataCite datasets/instruments use DataCite **created** calendar date as WPO's default Pub Date. Official NOAA IR: fill IR? TRUE and the verified canonical IR URL only when identified, otherwise keep UNKNOWN/not verified rather than asserting FALSE. Honor source checksums, original report URLs, authorized output types and exact DOI/URL identity. For REACH metadata changes use the explicit **Update** route and UID, not a duplicate new output.

## Special scholarly-publication review — low priority, not automatic rejection
Leading editorial title cues such as **Corrigendum**, **Erratum**, **Correction:**, **Correction to**, **Retraction**, or **Expression of Concern** indicate a possible notice rather than a distinct original research output. Route eligible *unreviewed* identities to `SPECIAL_PUBLICATION_TYPE_REVIEW` (priority 12) for later human eligibility checking; do **not** place them in normal automatic original-article screening or count them as completed New Candidates. Preserve REACH/Scout duplicate fast exits and original preprint holds **before** this route. Assess parent-article links and eligibility separately, with human review if genuinely distinct and eligible. Do not demote substantive scientific titles such as *Bias Correction of Weather Forecasts* or *Correction of Radar Bias*. This is a conservative title-based **triage cue**, never definitive evidence that a paper is ineligible.

## Bounded research and delegated GitHub completion
- Use one initial independent investigation plus one genuinely distinct-source follow-up for attribution ambiguity where feasible; do not repeat the same API read merely to fill a mission. Preserve immutable research notes and verified cached metadata. For unresolved sources, record a specific technical blocker or reversible hold and advance to another DOI.
- The GitHub workflow `.github/workflows/scout-hourly-guarded-handoff.yml` owns automated **historical Crossref original OAR459** completion. Its processor `scout-operations/tools/hourly_decision_handoff.py` verifies fresh queue SHA, exact-DOI publisher award/publication status, full public REACH/Scout/IR identity, signed feedback, the preprint gate, 24-column candidate validation and a SHA-verified active manifest. It persists `scout-operations/decision-handoff-ledger.json`, rotates across up to five eligible original DOIs when blocked, and reports `scout-operations/reports/hourly-decision-handoff.json`. The shared `scout-operations/tools/build_candidate_queue.py` constructs the canonical ranked queue and separate special-notice lane; neither queue row nor research note alone is a completed decision.
- ChatGPT hourly research should read the **latest completed** GitHub handoff evidence, avoid repeating those verification checks or reselecting blocked 459 Crossref originals, and focus on nonoverlapping monthly, independent and related-output research. GitHub's scheduled trigger is not proof it finished. Other discovery modes keep their current independent, source-verified review path until intentionally connected to the guarded backstop.
- GitHub Actions must fail closed on stale fingerprints, missing official records, ambiguous identities, preprints, bad formats, privacy failures and concurrent pushes. Retry safely from fresh main; do not force-push old derived results, overwrite old candidate batches or claim a blocked/staged draft as public publication.

## Confidentiality, review limits and reporting
A public Scout **inbox draft**, **active published candidate**, **private Discovery Hub import**, **signed human decision**, **Smartsheet insertion** and **public REACH addition** are six separate events. None implies the next. Only privacy-minimized **signed private Hub exports** can establish decisions; a public repo does not verify that the private Hub connector is installed or imported a candidate. No scheduled Scout workflow can independently approve, insert Smartsheet records, change SPARK/REACH, expose reviewer emails/notes/IDs or publish secrets.

Report only source-backed metrics: originals fast-exited/blocked, full public-review handoffs confirmed in active manifest, separately verified related DOI expansions, source failures and retry times, any authenticated human decisions, and known outstanding private ingestion. Do not conflate GitHub success with a newly published candidate or assert reviewer precision without independently labeled reference cases. Uncalibrated 0–100 reviewer-readiness scores are **not probabilities** or award verification. Evaluate screening recall, duplicate avoidance, reviewer acceptance and labor with authorized independent truth data.

## Mission completion and measured research reuse (November 10)
Use [HOURLY_MISSION_MEASUREMENT_V1.md](HOURLY_MISSION_MEASUREMENT_V1.md) as the authoritative measurement extension. An actual ChatGPT hourly research run may record one immutable, privacy-minimized `chatgpt_hourly_mission` outcome with its **observed** start/completion times; never infer these from the schedule or an unrelated Actions success. A separate `github_guarded_crossref_backstop` record is emitted by the existing bounded historical Crossref processor only after source verification and applicable public publication checks; **never combine denominators or count a pre-existing queue skip as fresh work**. Record genuine original decisions, independent expansion cases, public batch URLs, holds and absent intake gates separately. If emission cannot be verified, mark coverage unknown rather than inventing events. The code may publish a validated public proposal but must never act in a private Hub.

The independent DOI evidence audit reports verified persistent metadata-cache hits and observed provider requests using the existing source-SHA/TTL cache; the guarded Crossref processor measures in-process metadata reuse and actual resolver attempts separately. Counts not observed are `null`, not zero. Reuse of a prior immutable note is counted only when its source SHA is actually consulted. A 16/16 control test is not proof of real mission savings. Generated graph/index refreshes are not new research or child relationships. The separate completed-mission scorecard is an observational report, not proof of causality.

## Mandatory completed-original gate and bounded independent research rotation — November 11, 2026

**Before any external metadata request or research selection**, use the latest
SHA-verified `scout-operations/research-memory/mission-index.json` and
`historical-coverage.json`, canonical historical triage and active public
`scout-discoveries/manifest.json`. Do not select a DOI as a NEW original if
its historical DataCite research status is validated terminal, if its exact DOI
is in a verified public Scout staging batch, or if the complete REACH identity
gate confirms it already exists. An existing original remains a potential
seed for *genuinely distinct* related output research, not a new original.
The research-memory builder now separates `historical_reconciliation_needed`
from `historical_datacite_original`. Entries with missing evidence for an
older terminal handoff are **reconciliation actions**, never automatically
new research or a fresh Discovery Hub proposal. Do not infer private reviewer
approval, Smartsheet insertion or production REACH publication.

If an eligible DOI's official DataCite/Crossref endpoint is unavailable, first
reuse a fresh SHA/TTL-verified official metadata cache if available. Consult
the matching immutable historical source batch and its SHA-verified native
repository links before declaring metadata unobtainable; when practical use
the official institution's native DOI record, the original publisher
repository, or a separately verified source. The
`tools/recover_historical_datacite.py` helper returns
`archived_source_recovered` as **research-only prior evidence**, never a
verified live publication date, official funding decision or Hub-ready item.
Never treat a search result by itself as authoritative publication or project
attribution. Record the exact source access failure and checked fallback.

**A source access failure must not consume the whole hourly mission.**
When no additional distinct authoritative source is accessible for an
eligible DOI, record a reversible DOI-specific source hold and immediately
rotate to another eligible DOI. Attempt up to five **distinct** DOI identities
per mission using `tools/select_independent_mission_candidates.py`
(or equivalent SHA-verified index filtering when running via connected tools);
do not count a blocked/previously staged original as a completed decision.
Do not repeatedly spend a full mission on the same unchanged DOI or retry the
same unavailable endpoint; reopen only on new source fingerprint, evidenced
new source or a documented cooldown expiry. If all eligible entries are
blocked, report an explicit zero-completion mission rather than manufacture
progress. The historical Crossref OAR459 guarded lane retains its own
independent processor; do not duplicate its already delegated checks.

Record separately: previously completed originals skipped, archived
recoveries (not live verifications), native official page checks, source
holds, distinct DOIs attempted, source-backed complete original decisions,
separate expansion evidence, validated public staging, unresolved terminal
reconciliations, and privately verified human outcomes. The completed
original denominator excludes all unchanged public notes and technical holds.

## Evidence and implementation references
Use current SHA-verified `scout-operations/crossref-candidate-queue.json`, `scout-operations/active-workstream.json`, `scout-operations/research-outcome-registry.json`, `scout-operations/human-project-referrals.json`, `scout-discoveries/manifest.json`, `scout-operations/preprint-watchlist.json`, `scout-operations/reach-comparison-cache/comparison-index.json`, `scout-operations/research-feedback.json` and NOAA IR index. Specialized procedures remain in `SCOUT_SHARED_IDENTITY_AND_PRIVACY_PILOT.md`, `index-project-discovery-policy.md`, and source-specific workflow scripts. They provide implementation detail, **not conflicting operating policy**. The [verbatim older policy archive](policy-archive/SCOUT_OPERATING_POLICY_V2_2026-11-09_pre_consolidation.md) is reference-only.


## Source-driven related-output discovery (November 10, 2026)
For an existing verified REACH original selected for expansion, do not stop at the graph's previously indexed child DOI links. The separate bounded GitHub expansion runner may inspect **only the exact seed's official Crossref reference metadata** and explicitly allowlisted publisher-hosted article HTML for data-availability, supplemental data/code and data/code citations. Keep each request byte/time bounded, retain the official source URL and SHA-256 in the research note, and record access restrictions rather than inventing a missing dataset. If publisher HTML is blocked and no verified data/code DOI was recovered, Scout may examine the **exact same seed's SHA-index-verified NOAA Institutional Repository public item** and only a PDF directly linked by that item's official page; extract bounded public text with a sandboxed PDF extractor. Never guess PDF paths, follow external PDF links, or treat absent/extraction-blocked text as evidence no data exist. Generic citations of scientific papers without a same-paragraph data/software cue are NOT distinct data/code discoveries.

For each new source-cited DOI, retrieve exact-DOI official DataCite/Crossref metadata, apply the SHA-verified REACH/Scout and NOAA IR identity gates, respect the preprint watchlist, and independently verify **the discovered output's** WPO project/award association. The parent article's 459 award is only a research lead for a linked dataset, not publisher-deposited funding for that dataset. A dataset without independently established attribution is **Needs Investigation / research-only**, not an automatically approved or staged candidate. Source inspection alone never counts as a completed related-output expansion. Keep no more than three discovered DOI leads per expansion pass, preserve the seed's cooldown and workstream priority, and never write to private Hub or Smartsheet. Manual positive-control seed selection must match a verified REACH graph task and cannot bypass its cooldown. GitHub expansion evidence remains distinct from ChatGPT hourly mission completion records.



## Discovery and outcome measurement reconciliation (November 10, 2026)
Every guarded public Scout publication and every bounded official-source expansion note must rebuild SHA-verified discovery-method attribution and the operational, throughput, impact, and mission scorecards against the current active public feed manifest, before committing public reporting artifacts. Use scout-operations/tools/reconcile_scout_metrics.py, including the existing protected identity-DAG rebuild when the manifest advanced, and fail closed on stale dependencies. Public-review rows and batches must equal the manifest; source-note events and research-only DOI leads do not count as human approvals or completed expansions.

For a historic Crossref bot referral, do NOT default the discovery method to Independent. Historical Direct API attribution requires the exact original DOI and verified WPO459 award in the captured historical Crossref batch, the batch recorded SHA, and the exact source-backed research note. If the method is not supported, leave it Unclassified; never guess from topic, grant alone, or a generic Crossref DOI. Published review CSVs are immutable; source-hash-verified retrospective method corrections affect only the effective attribution rollup and preserve the raw published method. Separate original discovery method from reviewer purpose.

Source-driven expansions count seeds investigated, distinct new DOI leads found from official sources, candidate metadata/identity/attribution checks, separately completed eligibility decisions, and valid public handoffs as different events. Prevent repeated identical leads from inflating unique discovery counts. Keep recorded ChatGPT hourly mission coverage separate from GitHub work; missing reports mean unknown coverage, not zero work.

For every actual **ChatGPT hourly** execution, the first tool action must capture a live actual UTC start timestamp before source reads or analysis (never scheduled_for). At closeout capture the actual UTC completion timestamp and attempt to commit one immutable, privacy-minimized `chatgpt_hourly_mission` JSON under `scout-operations/reports/hourly-missions/` per the validated `reach-scout-hourly-mission-outcome-v1` schema. Do not use a prior run's start time, invent tool request counts, or mark a source-only hold a completion. If capture or authenticated GitHub writing is unavailable, report `NOT_INSTRUMENTED` with the exact reason. The standalone `Scout ChatGPT hourly mission measurement reconciliation` GitHub workflow validates these source records and updates the **separate** ChatGPT/GitHub scorecard, without triggering a new research mission, publishing a new candidate, or modifying private Hub/REACH systems.

## Same-mission existing REACH artifact URL gate — November 11, 2026

For each distinct related code/software/dataset repository URL identified during a
ChatGPT or repository-owned expansion mission, verify the URL against **current
public REACH in that same mission before a novelty, attribution or technical
hold is finalized**. A source-verified exact REACH match is an immediate
existing-public-output fast exit; rotate to the next independent eligible seed
rather than using another mission to redo the check.

Use the SHA-pinned complete `reach-comparison-cache/comparison-index.json`
as a candidate locator, then independently read the **live original**
`PART-WPO/reach-dashboard/main/agent-data/index/part-XXX.csv` shard for
each matching record; check canonical `Link to Output`, `Output Type`,
`Record ID`, and `REACH UID`. The same artifact URL may occur in a
related article's *supporting links* and in a separate code-release record's
*primary output URL*. A supporting-link match alone is an ambiguity to
resolve, **not** proof the supporting article and software are one output.
Do not demand a software title equal its citing article's title when the
software's exact primary URL and code-release identity have already matched.
Normalize safe URL equivalents (GitHub host/case, http/https, trailing slash,
query/fragment and root `.git`), without collapsing forks, subpaths, file
versions or distinct DOIs. Source changes or inaccessible index shards fail
closed for any **negative** finding; check additional current REACH shards
where required. Then check the public Scout manifest/inbox before any
possible new-output handoff. No private review or approval may be inferred.

A read-only reference implementation is
`tools/verify_reach_artifact_url.py --url <full HTTPS artifact URL>`. It
verifies only cache-linked shard candidates. The status
`EXISTING_REACH_PRIMARY_OUTPUT_URL` is positive exact-current-primary-URL
evidence; `SUPPORTING_LINK_ONLY_FULL_REACH_GATE_REQUIRED` and
`NO_CACHE_LINK_MATCH_FULL_REACH_GATE_STILL_REQUIRED` are **not** proof an
output is novel. A source failure requires a source-specific reversible hold
and rotation. If no script execution is available, use connected GitHub
file reads to perform these same checks in the *same* ChatGPT mission.

Regression: the repository
`https://github.com/chrisrac/objective_thresholds` is already a REACH
**Code Release** (record `reach-000079`, UID
`reachuid-v1-2db795d7c2e4513ff44d2c5a7fd97532`,
primary award `NA19OAR4590411`). It is also linked as supporting
information by article `reach-000066`. Any rediscovery of this exact
software URL must fast-exit as existing REACH and continue to another
eligible seed in the **same mission**. Do not alter older immutable reports.


## Related-output native-source recovery and complete identity gate — November 11, 2026

This rule extends the same-mission REACH artifact URL gate. A DOI resolver rejecting a redirect or a native landing page being inaccessible is **SOURCE_ACCESS_FAILURE**, not proof that the output or metadata is absent, irrelevant, or a duplicate.

**Bounded provider-specific recovery:** For each publisher-cited dataset/software DOI, check fresh SHA/TTL-verified exact-DOI cached metadata, then the official DataCite API `/dois/{doi}` and, where applicable, Crossref. For `10.5281/zenodo.{record_id}`, try the exact Zenodo public records API `/api/records/{record_id}`, requiring the returned DOI to match the specific requested version (a concept DOI is not interchangeable). For Deep Blue Data or another institutional repository, follow only the exact DOI's verified DataCite `url` or a source-cited native landing URL; never guess internal data-set slugs. When official publisher/record metadata points to an author-maintained GitHub repository, independently inspect that exact public repository, matching README/DOI, releases and release publication timestamps; third-party upstream algorithms are not newly produced study releases. HTTPS only, known provider hosts, bounded response sizes/timeouts, no credentials in notes, record each attempted URL and failure type. Do not download large dataset payloads. If available tools cannot call an endpoint, record that specific tool limitation, not global repository downtime. Never convert a GitHub release date into a DOI date without the proper DOI/version association.

**Mandatory complete public identity gate, even under partial metadata access:** Before concluding novelty or promoting a lead, verify exact DOI, normalized primary artifact URL, relevant version family and title against the SHA-verified **full REACH comparison cache AND live canonical REACH shards**, the SHA-verified public Scout batches in `scout-discoveries/manifest.json` **AND the public `scout-discoveries/inbox/`**, and the official NOAA IR mapping where relevant. Keep secondary article links separate from a primary code/dataset record. If any required index or shard is missing/stale/unreadable, status must be `PUBLIC_IDENTITY_GATE_INCOMPLETE`, not `NOT_IN_REACH`. Complete the same-mission checks before recording an avoidable technical hold, or name precisely which gate failed.

**Evidence classification and reviewer routing:** Keep `OUTPUT_EXISTS_SOURCE_VERIFIED`, `SOURCE_ACCESS_FAILURE`, `PUBLIC_IDENTITY_GATE_INCOMPLETE`, `OUTPUT_METADATA_PARTIAL`, `PROJECT_ATTRIBUTION_UNVERIFIED` and `REVIEW_READY_NEEDS_INVESTIGATION` distinct. Parent-paper WPO award `NA21OAR4590367` is evidence to investigate *linked* outputs, not automatic output-level funding or SPARK parent proof. After full public identity screening shows no known match, a credible separately identified public output with a source-backed project association but missing noncritical metadata may be written to the **separate private human-investigation intake only if that integration is installed and verified**; ask one concise question about its remaining uncertainty. Do not manufacture the 24-column public candidate, assert a private Hub import, or mark verified WPO attribution without the required evidence. If private intake is unavailable, record `REVIEW_READY_NEEDS_INVESTIGATION_NOT_DELIVERED` as an explicit nonterminal handoff gap, not an indefinite generic repository hold.

**Mission behavior:** Record provider attempts, exact DOI/URL, verified fields, source fingerprint, complete/blocked duplicate gates, release/version evidence and a specific retry condition. A failed native read should trigger **one distinct provider/method fallback in that mission**, followed by an evidence-preserving disposition; then rotate to the next eligible seed (up to five) without repeating unchanged blocked URLs. Verify and record the current operating-policy commit SHA, or explicitly mark `NOT_VERIFIED`. This applies to independent research, seeded expansion and historical/monthly related-output discovery; it does not change the GitHub Crossref-original lane, monthly priorities, preprint handling, signed human review, or private REACH/Smartsheet boundaries.

**Regression leads:** The November 11 Great Lakes cyclone study (`10.1029/2024GL109890`) cites software `10.5281/zenodo.12627444` and Deep Blue dataset `10.7302/17vn-x488`. The public author repository `https://github.com/abkenyon/GLStormTrends_2024` states its Zenodo DOI and has a GitHub `v1.0` release on July 2, 2024. Its upstream dependency `https://github.com/ecjoliver/stormTracking` is not that new code release. Both distinct DOI leads need full public identity and **their own** project-attribution verification; neither should be silently discarded because the DOI redirect failed. Existing immutable mission records must not be rewritten.
