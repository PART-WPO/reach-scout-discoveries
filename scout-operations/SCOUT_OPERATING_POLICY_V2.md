# REACH Scout 2.0 — Current Operating Policy
**Effective November 5, 2026.** This document is authoritative for new Scout missions. Older dated policy documents, GitHub evidence files and historic task instructions remain immutable audit history; where they disagree, this current operating policy takes precedence. This document does not retroactively change any old research or human decision.

## November 9, 2026 (evening) — confirmed WPO award code (LATEST USER RULE)
**This section supersedes older statements below describing 459 as only a funding clue or requiring project-deliverable proof before labeling the WPO funding connection confirmed.**

- The exact NOAA award *program code immediately after OAR or OARX* is decisive: `459` means Weather Program Office funding. Accept established variants such as `NA21OAR4590367` and `NA26OARX459C0001`. Other codes such as `432`, `011`, `469` (or `419`) do **not** by themselves establish WPO funding. A non-459 award listed *alongside* a verified 459 does not cancel the WPO connection.
- Verify that the **exact article/DOI's official publisher-deposited Crossref funding references** contain the matching `459` award; merely finding a code in a SPARK project, search note, parent article, related DOI, title, or unverified lead does not verify that *this output* was funded. When exact official metadata and research-award context agree, mark **WPO funding CONFIRMED** and send the distinct officially published item as **NEW CANDIDATE** with the verified full 459 award in `NOAA Award Number(s)` and the official Crossref funding evidence URL. Do not force `NEEDS INVESTIGATION` solely over whether 459 indicates WPO.
- Human reviewers **still** select and validate the proper SPARK primary parent and may question product eligibility/scope. Never automatically approve the proposal, claim private Hub ingestion, insert into Smartsheet or publish REACH. Keep parent blank until approved; maintain all REACH/Scout/IR duplicate screens, prior signed reviews, and monthly preprint exclusion.
- Without an official same-DOI 459 award, a 459-looking research lead is **not** enough to fill authoritative award fields or automatically declare WPO-funded output; a bounded `NEEDS INVESTIGATION` review can still be appropriate. Record reviewer-readiness scores separately from the categorical WPO funding determination; 70/100 must never be interpreted as 70% WPO probability.
- This rule applies to monthly Crossref, historical backfill, independent research and DOI-seeded expansion when the same output-level evidence is present. Earlier public candidate batches are immutable; never create a second reviewer unit for a DOI already in public Scout.

## Purpose and measure of success
Find authentic, overlooked WPO-funded research outputs (papers, datasets, instruments, code, reports and reusable knowledge products), screen out known REACH/Scout duplicates and ineligible records, investigate uncertain cases in a bounded manner, and deliver a defensible, manageable **human-review queue**. Aim to support **20+ meaningful human decisions per week** once verified private feedback is connected; do not create proposals merely to satisfy a quota. Judge impact by reviewer acceptance, genuinely missing outputs found, false duplicate rate, case completion and reviewer time—not by number of DOIs harvested.

## One shared decision process for every source

**1. Discover, retain provenance, but do not presume relevance.**
- Current month: run DataCite + Crossref direct primary-award API harvest first on the **1st**, including weekend month starts; use immutable raw batches, primary SPARK `Award Number(s)` only, and full FY25+ hyphenated award identifiers. Never treat SPARK `Related Award Numbers` or broad NOAA/cooperative funding as equivalent.
- Supplemental on the **1st** (weekends included): Crossref indexed-date changes for prior month and a small project-title search pilot. Indexed dates are metadata changes, **not publication dates**. Source results are research leads, not proposals or new outputs; nonstandard award strings must be excluded from literal award queries with a visible skipped count. See `index-project-discovery-policy.md`.
- Then historical Crossref, historical DataCite, independent SPARK project/output searches and verified related-output expansion. Preserve `Direct API`, `Discovered by following API leads`, `Found through independent research`, and `Metadata correction` origin/purpose separately.
- A unique DOI or canonical URL is a candidate identity, not proof of funding. URL-only reports/software are still legitimate potential discoveries but require their own URL identity and WPO project evidence.

**2. Fast public identity screen (reuse verified cache).**
- Use checksum-verified complete REACH comparison cache and the shared public Scout published and inbox index, including exact DOI, canonical publisher/NOAA IR URL, normalized title, version/secondary links and unique REACH UID.
- Exact DOI + matching normalized title + unique REACH UID, or officially verified NOAA IR DOI-to-canonical-REACH-URL + title + unique UID, may confirm *public identity* in the source snapshot. Multiple records, title-only matches or version contradictions require **one bounded identity review**; never auto-confirm or automatically deny novel versions.
- For historical Crossref use `historical-crossref-screening/actionable-routing.json` and its strict bulk gate. Never repeat the initial 614-DOI screening if the latest SHA-verified report is current. Historical/current counts are evidence snapshots, not instructions to hardcode.
- Public negative identity means only `NO_PUBLIC_IDENTITY_MATCH`; private Hub history is **NOT VERIFIED** unless a signed export exists. Prevent duplicate public proposals and honor signed prior human reviews without automatically rejecting a distinct new product.

**3. Publication eligibility and metadata.**
- Original **preprints** must NOT enter Discovery Hub or public REACH. Keep them on the existing **monthly first-of-month watchlist**. A verified official journal DOI is a **separate** research lead subject to the full pipeline; never automatically stage the preprint DOI.
- Crossref REACH publication date: `published-print` preferred, `published-online` fallback, then `published`/`issued` where meaningful. A valid YYYY-MM date becomes YYYY-MM-01 with source precision recorded; never use Crossref `created`/DOI deposit timestamp as publication date.
- DataCite created calendar date is the chosen REACH **default Pub Date** for valid DataCite DOI records; source provenance retained; no date-only missing-field flag when valid. Human reviewers may change based on evidence.
- For each genuinely new DOI, recover critical metadata via exact DOI DataCite/Crossref, publisher and official NOAA IR/native repository BEFORE human missing-metadata referral. Treat API access failures as failures, not missing metadata. Required 24-column staging validation, IR? TRUE only with verified canonical URL; otherwise UNKNOWN, never FALSE.

**4. Same-project WPO relevance.**
- A DOI listed in REACH is already a WPO catalog output and may seed *targeted related-output research*. It does NOT establish funding for every related publication, dataset or code repository.
- **Monthly direct API** candidates with exact structured SPARK primary award support, no contradiction, identity/eligibility/metadata checks may follow the expedited human-review path. Multiple parents require reviewer selection.
- **Historical/independent/API-seeded related** outputs need specific output-level funding/workstream evidence, not just shared authors, an umbrella/cooperative grant, or topical similarity. A same-DOI official Crossref 459 funding record establishes the WPO funding connection; exact parent selection remains a human step.
- Apply `expansion-relevance-priority.json`: (a) verified WPO seeds receive targeted expansion, (b) uncertain cases get a short project-specific WPO scope check first, (c) documented uncertain attribution/source anomalies get a **reversible deferral**, reopened only with new positive, SHA-backed evidence or explicit human instruction. Never mark a deferred DOI unrelated with certainty or close its expansion ledger.
- For every new related product, check its OWN DOI/URL, official publication version, project scope and uniqueness. Never count a citation, shared paper supplement, preprint sibling or same Zenodo concept/version as a distinct eligible product without explicit evidence.

**5. Research stopping rules and decisions.**
- Normally one initial investigation plus one **distinct-source** follow-up. Repeated reads of the same evidence do not extend the budget. At the bound, record a supported decision, identify one specific technical repair, or create `research complete; human judgment needed`. Reopen only on material project/identity evidence or an explicit human request.
- Every original DOI and independently discovered related output has its own research status; historical original disposition and DOI-seeded expansion are **separate**. Verified REACH screening, relevance priority and research-note counts are NOT formal terminal dispositions.
- Use shared `decision_pipeline.py` and `unified-source-preflight.json`, then immutable case checkpoints. Reconcile historical status only through existing strict completion validators. The `reconciliation-repair-worklist.json` identifies unsupported terminal claims; never manufacture award/snapshot data, restore intentionally retired feeds, or overwrite prior human decisions.

**6. Human review, privacy and system boundaries.**
- Only truly eligible, independently checked outputs proceed to validated public Scout inbox/manifest, then to the **private Discovery Hub** for human parent selection, metadata editing and deliberate approval/rejection. Private Hub import, review approval, Smartsheet insertion and actual public REACH addition remain independently verified outcomes; a public candidate CSV cannot prove any of them.
- Update existing REACH metadata only through the explicit `Update` route, with exact existing UID and evidence; never create a duplicate new output as a workaround.
- Discovery Hub reviewer feedback is accepted only via signed, privacy-minimized exports verified against the public Scout candidate ID and exact DOI. Current integration file is `integrations/DiscoveryHubScoutFeedback.gs`; it is **NOT installed in the live private Apps Script** unless separately verified. Do not claim a reviewer decision in the absence of an authenticated export; reviewer email, notes and private IDs never belong in public GitHub.
- No scheduled Scout mission can insert into Smartsheet, change REACH/SPARK, approve a reviewer decision, or infer a private import. Do not put API tokens or secrets in public sources.

## November 9 shared identity and public author-data boundary
- Reuse the SHA-verified shared public identity and explicit preprint
  disposition across monthly original intake, historical Crossref/DataCite
  preflight, API-seeded related output preflight, and independent DOI metadata
  research. Unique identifier **and title**, or unique official NOAA IR
  DOI-to-REACH URL **and title**, are required before treating a candidate as
  an existing public record. Mirrored published Scout batch + inbox entries
  with the same DOI and title are one public proposal, not human approval.
- **SPARK personnel are never author-discovery seeds.** The optional,
  manual-only `reach_author_pilot.py` starts with an existing verified public
  REACH award-associated publication, corroborates its DOI/title/type through
  official public Crossref metadata and keeps names transient in memory.
  No qualifying REACH publication means no author-based search. Author
  overlap alone never verifies WPO project funding; the resulting DOI leads
  must use the normal evidence gates before any human-review proposal.
- The 100-case private reference truth remains **NOT COLLECTED** until an
  authorized reviewer independently labels the frozen set outside GitHub.
  Never infer test accuracy from Scout's own prior classifications. See
  `SCOUT_SHARED_IDENTITY_AND_PRIVACY_PILOT.md` for runbook and controls.

## Operational cadence and source hierarchy
- **Hourly missions:** existing *weekday-only* task, monthly-first / newest actionable / historical corroboration / selective related-output research. No ordinary weekend hourly missions.
- **Weekend month-start exception:** perform first-of-month API intake, preprint status pass and eligible monthly discovery promptly when the 1st occurs on a weekend. Do not turn on all unrelated hourly research.
- **Morning briefing:** existing 8 AM **Monday–Friday**, read-only. Explain in plain language what new WPO candidates Scout *actually* verified, what remained uncertain, and practical next actions. Typical 250–450 words; do not turn into an engineer's hourly job log.
- Evidence source of truth: SHA-verified `scout-operational-scorecard.json`, `scout-v2-impact-report.json`, `active-workstream.json`, `unified-source-preflight.json`, raw official API manifests, `expansion-relevance-priority.json`, `reconciliation-repair-worklist.json`, `preprint-watchlist.json`, `preprint-publication-leads.json`, `noaa-ir/manifest.json`, and `research-feedback.json`.
- Always verify exact GitHub Actions run outcomes and SHA-linked artifact freshness before claiming a mission succeeded. A successful scheduled trigger is not evidence that meaningful research was completed.

## Evaluation and failure handling
- Test code and real source checks before deployment, merge only after CI passes, and verify a post-merge production run. Stop/report on stale REACH/NOAA IR index, source checksum mismatch, partial API harvest/pagination, missing case checkpoint, conflicting publication version, failed feed promotion or concurrent GitHub push. Refresh sources and re-run derived reports rather than rebasing stale generated JSON.
- Scoreboard separates raw discovery, duplicate/eligibility screening, original research, expansion research, validated Scout public proposals, inbox drafts, authenticated private reviewer events, actual approvals, Smartsheet writes and verified public REACH additions.
- Run a blinded/independently reviewed ~100-case benchmark representing existing duplicates, genuine novel outputs, ambiguous funding and preprint families before claiming accuracy/recall or reaching a numerical 8–9/10 system rating. Benchmark gold labels and reviewer time can remain private; publish only verified aggregate metrics with permission. The target of 20+ per week is a **planning capacity**, not observed throughput.

## November 9, 2026 — rapid screening and human Needs Investigation routing (current user direction)

**Operating priority:** Scout is a discovery and *fast-screen* assistant; it should not repeatedly research plausible WPO project attribution when an authorized human can adjudicate the connection efficiently. This section specifically supersedes any earlier requirement to establish the full output-to-project bridge **before offering a Needs Investigation review item**. It does **not** relax requirements for an eligible new-output recommendation, reviewer approval, Smartsheet insertion, REACH publication, or writing a WPO award as confirmed.

Fast-screen an official output as follows:
1. Check current source-verified complete REACH, public Scout and NOAA IR identities first; confirmed public REACH/Scout originals exit the **new-output review** route while preserving distinct related-output research. Treat an ambiguous version/duplicate as needing an identity check, never confidently new.
2. Check original preprint versus officially available distinct output; tracked preprints remain on the monthly watchlist, not the Hub.
3. Reject or park **convincingly documented non-WPO/non-project associations** and source-specific contradiction, but do not treat no exact award, an unverified project match, or an uncalibrated 432/459 funding pattern **alone** as proof an output is unrelated.
4. For a published, publicly novel exact DOI with a publisher-deposited 459 funding reference matching the WPO award context, route to **NEW CANDIDATE** and populate only the verified award and funding evidence. For plausible WPO leads lacking that direct DOI-level funding evidence, route to **NEEDS INVESTIGATION** with uncertain awards in the rationale only. Both use the canonical 24-column public Scout feed, require an authorized reviewer to select the parent and do not imply private Hub ingestion.
5. Give each Needs Investigation candidate a plain-language reason and an **explicit 0–100 uncalibrated Scout screening score** in its rationale and a compatible Low/Medium/High value in `Scout Confidence`. The score indicates prioritization of a potentially new WPO-related output, **not a statistical probability, verified funding, or review authorization**. An unconfirmed project cannot achieve the highest confidence tier. An approved output still requires the established human 24-column validation, correct parent project and deliberate insertion.
6. Prioritize the reviewer handoff over another full initial-plus-distinct-source research round for credible uncertain candidates. Cap validated new public reviewer drafts per workflow run (initially 3) to manage review load; record the number screened, independently ruled out, already in queue, and queued for reviewer action. Human feedback must not be exported to public GitHub.

The initial production implementation is confined to existing bounded human-project referral evidence and historical Crossref notes with traceable official DOI metadata, WPO search context and verified public duplicate screening. Monthly fast intake retains its own existing preprint, metadata and source-provenance validators. Extend the rapid policy across other discovery modes only after the first public-feed safety check; source history and provenance must never be silently reclassified. Existing private Discovery Hub synchronization remains a **separate, human-controlled step**.

## November 9 — one fully screened output decision per hourly mission (latest directive)

Each hourly Scout mission targets **one complete original-output screening decision or validated public human-review handoff**, not one publisher lookup, unverified funding hold, cache check, or research note. Previously screened original DOIs already in public Scout or REACH are FAST EXITS, **not** a newly completed screening: move to the next actionable DOI within the same hourly mission, while retaining independent DOI-linked expansion research.

**Initial public-identity gate before deep research:** consult freshest SHA-verified full REACH/Scout/NOAA IR identity and earlier monthly/other-lane research. Only classify as already in Scout when the exact DOI and normalized title agree with a verified public batch or inbox record. A bare scout_overlap hint is insufficient. Existing public Scout proposal does not establish private Hub import or approval.

**Award triage:** An exact OAR459 or OARX459C award is a WPO funding identifier. An official publisher-deposited award for this exact DOI, matched to the 459 context, is sufficient to mark WPO funding confirmed and route to NEW CANDIDATE after the other eligibility gates pass. Reviewer still chooses the correct SPARK parent. If the 459 is only a cached lead or research-note mention rather than official exact-output evidence, use bounded Needs Investigation instead of repeatedly researching. Never populate unverified award or parent fields.

432 generally indicates Cooperative Institute/umbrella support. Other OAR award program codes such as 011, 469 and 419 do not confirm WPO funding. Their presence alongside a source-verified 459 award does not negate WPO support. Absence of 459 does not prove an output unrelated; use bounded specific WPO project evidence when needed, and exclude only strongly documented non-WPO/disqualified cases.

**Single-mission completion requirement:** Select one not-yet-reviewed original. In the same run verify or reuse current complete REACH/Scout/IR identity and protected history, official publication status/date/version, project/WPO clues, and issue one defensible result: (a) new human Needs Investigation review item in the validated public feed; (b) validated new-output recommendation in public feed with all normal checks; (c) evidence-backed no-action/unrelated determination; (d) verified REACH or already-reviewed Scout duplicate fast exit, followed by a *second candidate* for the one-output goal; (e) preprint watchlist fast exit, followed by a second candidate. Never interpret a source or technical hold, research-memory refresh or skipped existing proposal as completed new-output screening.

If stale public source fingerprints, API downtime, ambiguous identity, unavailable protected reviewer history or 24-column validation prevent the result, record the exact technical blocker once and move to a different candidate during the same mission when possible. If no unblocked candidate exists, disclose the exception; do not fabricate a decision or claim Hub approval. Continue related-output expansion in separate capacity without counting it as a completed original.

**Measurements:** count genuinely new original-screening resolutions, publicly published candidate batches, fast-exited already existing records, blocked cases and independently investigated related outputs separately. No reused notes, publisher pages or public mirrors count as a new decision. Count one identity across mirrored Scout inbox/batches once. Private Hub ingestion, reviewer judgment and REACH addition remain independently verified.

**November 9 regression case:** DOI 10.1175/AIES-D-26-0004.1 had prior monthly records including primary award NA22OAR4590530, SPARK project spark-000179 and a publicly published Scout candidate. The November 9 historical PROJECT_EVIDENCE_HOLD merely duplicated that work. Correct response: reuse the existing review unit and select a *different* original for the mission. Preserve the publication-date discrepancy for reviewer validation; do not silently rewrite an existing public record.
