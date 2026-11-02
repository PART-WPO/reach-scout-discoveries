# API follow-up completion and research-priority policy (2026-10-29)


## AUTHORITATIVE monthly intake-first operating policy — November 1, 2026

**Overrides the earlier original-output fast-path policy wherever that older policy
requires independent publisher project proof or completing DOI-seeded research before
placing ordinary primary-award API matches into the human-review feed.**

### Order of operations

**1. Monthly records to human review FIRST.** On every newly published DataCite +
Crossref monthly harvest, run `scout-operations/tools/quick_monthly_intake.py`
against the SHA-verified public REACH complete index **and every detail/secondary
link**, the validated Scout manifest/batches and unpublished inbox, and SPARK's
literal **PRIMARY Award Number(s)**. Compare exact normalized DOI, title, output
URL, secondary links and known concept/version or preprint/final identity. Normalize
HTML/XML title markup and enrich only verified fields; never assume an article's
authors are necessarily its project's PIs.

For an ordinary original DOI with a publisher/repository **structured funding
award number matching a SPARK primary WPO award**, source metadata and no
concrete contradictory project evidence, that funding evidence is **sufficient to
propose human review**. No additional deep article/funder investigation is
required before human review. This is not a determination that the output is
definitively attributable to a particular WPO-funded project: show the basis
and let the human reviewer verify the funding connection.

Submit the original to the standard validated 24-column Scout inbox → preflight
→ append-only public Scout discovery feed **immediately** after duplicate screening.
Use `Direct API` provenance and source month. Neither project-specific deeper
research nor expanding references is a prerequisite. The existing human
Discovery Hub approval and REACH publishing process is unchanged. Public Scout
manifest staging is explicitly **NOT** proof of actual private Hub import. If the
private Hub has not been observed importing the candidate, record `NOT VERIFIED`.

**2. Exception path.** Hold actual conflicting funding evidence for an
investigation; keep distinct award/project associations when multiple primary
awards match, route uncertain parent attribution to the existing human
Needs Investigation classification without assigning one arbitrarily. Existing
REACH or Scout outputs, previously reviewed historical DOIs, and concept/version
families must not create repeat candidates. Missing abstracts or reviewer-required
PI attribution must remain visibly missing, never invented; send a compatible
Needs Investigation draft when permitted by the validated Hub schema, otherwise
record a pending handoff with exact missing metadata. Normalized Pub Date policies
remain DataCite 'created', Crossref print-first (partial month→day 1), and
source-specific online-first fallback. No date guessing.

**3. Subsequent missions follow the original DOI seeds.** Continue API-seeded
publication, dataset, code and report investigation in
`scout-operations/monthly-expansion-leads.json`. Maintain the original seed DOI,
distinct output identity and exact relationship evidence, independent WPO project
funding and REACH/Scout dedup. A reused input dataset, cited paper, generic
library, supplement or a version of the original is not automatically another
new WPO output. Each genuinely new related output can separately enter human review.

### Automated reporting and scheduling

`monthly-fast-intake.json` is the rapid reviewer funnel: original records,
fast-track, metadata/parent review, funding exceptions, version-family holds
and validated inbox status. `monthly-triage.json` status
`staged_for_hub_import` is a **terminal Scout verification stage**, not Hub
delivery or human approval; `coverage.json` separately counts
`staged_for_hub_import` versus `forwarded_to_hub`.
`monthly-decision-queue.json` and `active-workstream.json` are for
remaining exceptions and related expansion leads.

GitHub Actions first-of-month coverage/intake schedule checks new harvests
during the early hours of the 1st (including weekends) because GitHub-bot harvest
commits do not automatically trigger another workflow. No paid external worker,
manual Hub approval bypass, personal emails, or direct Smartsheet/REACH changes.
Never overwrite old monthly source batches or historical reviewer decisions.

Report the actual funnel separately: original API rows, validated public Scout
review candidates, private Hub imports VERIFIED or NOT VERIFIED, human approvals,
public REACH additions, exception cases, and verified additional DOI-seeded
discoveries. An unanswered private Hub ingestion step is an integration status,
not grounds for repeating completed Scout original-output research.


## AUTHORITATIVE monthly Scout operating rule — November 1, 2026

This rule takes precedence over older directions that imply **every related DOI, source,
dataset or code lead must be completely researched before the original monthly output
can be submitted to human review**. Original-output verification and API-seeded
discovery expansion are two separate, independently tracked lanes.

### Lane A — original monthly output fast path (first priority)

Read `api-discoveries/manifest.json`, `scout-operations/monthly-triage.json`,
`scout-operations/monthly-decision-queue.json`, and the active REACH and Scout catalogs.
For each original Crossref/DataCite DOI, confirm (a) the exact work, DOI/URL/version,
required metadata and source-appropriate date; (b) absence of its identity under any
REACH/Scout DOI, alternate URL, detail/secondary link, preprint/final version or
concept/version DOI; and (c) **specific WPO primary-funded SPARK project attribution**,
not merely an award-string or topic overlap. Preserve separate project associations
when more than one is genuinely evidenced.

**As soon as these original-output checks pass, prepare a candidate for human review
without waiting for Lane B**. Explicitly document the four independently verified
`original_output_gate` booleans:
`same_project_wpo_funding_verified`,
`all_reach_and_scout_identities_checked`,
`distinct_output_or_canonical_version_verified`, and
`required_metadata_verified`, plus two or more truthful `checked_sources` URLs.
These are **attestations that checks actually happened**, not flags to set based on
mere API receipt, an absent index DOI or a scheduled mission. The decision-queue
builder will not label a case ready for a draft without this complete explicit gate.

An eligible case goes through the **existing** `scout-discoveries/tools/prepare_batch.py`
24-column schema, unique `scout-discoveries/inbox/` draft, automated validation and
append-only Scout batches/manifest. Never edit the manifest directly or claim the
private Discovery Hub imported it without observing that import. Never approve or
publish to REACH automatically. Keep the original's true origin as **Direct API**
and `Intake origin: Monthly API`; do not mislabel an original as API-seeded expansion.

### Lane B — independent API-seeded related-output discovery

Track each *distinct* publication, dataset, software release or report discovered
through an original DOI in `scout-operations/monthly-expansion-leads.json`, with
`original_seed_doi`, exact `identity`, evidence-bearing source-to-lead path,
and `origin_method: API-seeded expansion`. Follow the evidence; substantively
investigate independently (same-project bridge, metadata/date, full REACH/Scout
identity and version comparisons) before any **separate** review proposal. Reused
code, citations, third-party input datasets, related preprint/final manifestations,
supplements and existing REACH items are not automatically new outputs. Deduplicate
cross-cohort research and preserve historical human review units.

Lane B may progress within the same hourly mission as Lane A, and remains a monthly
workstream after Lane A is cleared, **but it never holds a verified original-output
draft hostage**. Prefer completing the highest-confidence original final checks early
in the mission, then use remaining investigation effort to expand and verify links.
Treat both lanes as separate accounting in hourly reports.

### Enforce a decision after bounded research

One initial research round plus one substantive *distinct-source* follow-up is normally
enough to warrant a **decision review**, not indefinite `needs_more_research`.
The deterministic `scout-operations/tools/build_monthly_decision_queue.py` flags
already-researched open cases as `decision_review_due` and ranks evidence-supported
originals for final checks; its output is **research prioritization, never proof** of
funding, eligibility, duplicate status, human approval or Hub delivery.

At that decision point, either:
1. Complete missing **specific** checks immediately and submit a fully verified
   new-output candidate through the validated Scout inbox;
2. Close an evidenced duplicate/ineligible/no-project-bridge original with a
   source-backed, appropriate terminal disposition;
3. Escalate a credible project-specific case with exhausted metadata/identity
   recovery to the existing, compatible human **Needs Investigation** path.
   If Hub import is unsupported, preserve a truthful pending-Hub-intake record;
   report **NOT DELIVERED**, never force a fake required field or invalid draft.

Avoid rerunning complete primary-index/title scans or cycling through the same
unspecified "more verification needed" note. If a check cannot be completed,
document the exact blocker, attempted distinct sources, reviewer question and
reason for the final outcome. **Do not** resolve a material funding mismatch by
calling it a confirmed WPO output. Human decisions and older research provenance
are preserved. Public GitHub staging, private Hub import, approval and public REACH
publication are separate reported states.

### Mandatory reporting

Report (i) original DOI cases researched, decision reviews due, explicit fast-path
gates passed, original drafts validated/published, closed cases and unresolved holds;
(ii) independently tracked API-seeded expansion leads verified, existing in REACH,
still under investigation and separately staged; and (iii) private Hub imports as
NOT VERIFIED unless actually observed. A monthly ledger with every case open after
multiple substantive missions should trigger a decision-gate review rather than
more undirected discovery. See `scout-operations/monthly-decision-queue.json`.


## AUTHORITATIVE: original discovery method is separate from finding purpose — October 30, 2026

The original 40 legacy missing-route Scout rows have an approved, source-backed `scout-operations/legacy-provenance-backfill.json` companion ledger. The automated origin rollup validates each entry's **immutable manifest SHA-256, exact CSV row number, original source run ID, original DOI/URL and title** before counting it. The original October 28 15:30 ET DataCite mission report expressly distinguishes one API-returned dataset from two related publications. Thus **all 40 original legacy methods are now classified**: 33 SPARK-driven independent, five directly API-returned outputs, and two discoveries from following API leads. Great Lakes cyclone DOI `10.1029/2024GL109890` is API-led by original mission evidence, **but its exact starting seed DOI remains NOT VERIFIED**; do not invent that DOI or any precise path. DO NOT re-research every legacy record, duplicate Hub entries, edit published CSVs or assume approval.

For EVERY future candidate, explicitly record **two different concepts**: `Scout origin method: Independent discovery | Direct API | API-seeded expansion | Unclassified` (the verifiable path by which Scout first identified the output); and `Scout finding purpose: new_output_review | metadata_correction | possible_duplicate_review | existing_duplicate_review | needs_investigation` (the recommended reviewer action). Preserve `Scout discovery route` for compatibility with the old 24-column Hub importer. For `Scout discovery route: Metadata correction`, the JSON draft MUST specify separate `origin_method`, with supporting public evidence. Subsequent DOI metadata enrichment does NOT redefine the original discovery method.

**Use `effective_discovery_method_counts`, `effective_finding_purpose_counts`, and `legacy_provenance` in the newest automated scout-operations/discovery-origin-rollup.json** for real, reconciled attribution metrics. The old `route_counts` remain raw original-CSV labels only for audit comparison and still contain 40 missing legacy route lines; do not present that number as the current count of unidentified legacy research. Six later metadata corrections without an original-method label have separately been recovered by exact-DOI and mission evidence in `scout-operations/method-recovery-followups.json`. Current effective method Unknown is **zero**, while the Great Lakes article still has an unverified exact API seed relationship. Obtain latest counts from the live rollup rather than these historical baseline numbers. Staged output proposals, human-confirmed outcomes, private Hub imports and public REACH additions remain separate metrics; do not assert unverifiable human decisions. No schedule change.

## SUPERSEDING Scout feed-publishing protocol — October 30, 2026

**This section overrides every older instruction in this document to publish newly discovered CSVs directly to `scout-discoveries/batches/`.** All research routing and human approval rules below remain active.

For every eligible, deduplicated, evidence-backed new output or metadata-review proposal, build a unique 24-column CSV using the fixed structured provenance contract at [candidate draft format](../scout-discoveries/tools/CANDIDATE_DRAFT_FORMAT.md) and [prepare_batch.py](../scout-discoveries/tools/prepare_batch.py). Use exact fields including `Scout classification: NEW CANDIDATE` (or other evidence-supported canonical status), `Scout discovery route: API-seeded expansion`, distinct `Scout seed DOI: 10.xxxx/...`, and `Scout discovery path evidence: https://...` for API-linked output research. For normal independent discovery also include `Scout discovery method: ...`. Where appropriate use literal `Intake origin: Historical DataCite API Backfill` or `Intake origin: Monthly API`, `Scout verification: Completed`, REACH snapshot, checked sources, funding basis and related outputs. Preserve source route even after direct DOI metadata enrichment.

**Save and verify the Library draft first**. Run `python scout-discoveries/tools/prepare_batch.py --check ...` on the exact draft where execution is available; never claim a PASS if not run. Scout must commit a **new unique draft** to `scout-discoveries/inbox/` on main, **not directly to the immutable batches folder**. GitHub Actions now prevalidates all changed inbox drafts, promotes only valid bytes to `scout-discoveries/batches/`, and then publishes SHA-256 manifest and reconciled `scout-operations/discovery-origin-rollup.json` together. An invalid inbox draft cannot become a published batch or prevent previously verified manifest entries from remaining available. If validation fails, report the specific error, preserve the unique draft and prepare a new corrected inbox file without silently overwriting any prior file. The special October 30 URRD repair was one-time user-authorized and is complete.

The attribution rollup counts `Direct API`, `API-seeded expansion`, `Independent discovery`, `Metadata correction`, and `Unclassified` from verified public CSVs. Legacy route-missing cases stay unclassified, not independent. Distinguish a research lead, unpublished inbox draft, verified GitHub staging, private Hub import, human decision and verified public REACH addition. No direct manifest edits, automatic approvals, fabricated metadata, paid GitHub AI worker or changes to public REACH/SPARK/Smartsheet. Private Hub import status must remain NOT VERIFIED without genuine private observation.


**Authoritative routing policy.** Supersedes older instructions allowing Scout to return to ordinary historical SPARK award discovery while unresolved monthly or historical DataCite research cases await a future retry date. This is research and review routing only; it does not change human decisions or REACH.

## Priority at every hourly mission

1. **Monthly API intake — new or unresearched original DataCite/Crossref records.** Research the original output independently; expand to related articles, datasets, software and reports.
2. **Monthly API original-output decision fast path and unresolved follow-ups.** Prioritize closing evidence-backed originals and submitting verified candidates without waiting for their independent related-output leads; then investigate those leads in their separately tracked monthly expansion queue. Keep unfinished monthly research and Hub handoff blockers visible.
3. **Historical DataCite intake — any original records awaiting first investigation** (the 2026-10-28 cohort has completed this pass).
4. **Historical DataCite unresolved follow-ups and linked-output blockers.** Immediately prioritize the October 29 baseline of **38** remaining original DOI cases. Continue across hourly runs until all 38 reach supported terminal research outcomes or a truthful, validated human-investigation handoff. Also address five previously tracked related-output metadata blockers when applicable, without equating them with 38 original cases.
5. **Other bounded award-attribution follow-ups** from previously investigated API records. Preserve original no-action conclusions; document project-specific evidence and close negative follow-ups rather than retry forever.
6. **Normal historical SPARK award-by-award discovery** only after all higher-priority research and handoff work is concluded. New monthly intake always preempts this work on the next hourly run.

The router's `mode` stays compatible with existing consumers: `monthly_api_triage`, `historical_api_triage`, or `normal_historical_discovery`. The additional `phase` distinguishes first-pass research, additional-evidence recovery, and attribution follow-up. `needs_more_research` and linked metadata blockers are **actionable research**, not cleared, merely because a date is in the future. Reconcile against source manifests and ledgers each mission and correct stale `active-workstream.json`.

## Bounded, immediate continuation: do not just recheck the same URL

When a case already has one first-pass investigation, begin **one bounded, substantive additional-source round now** using distinct reliable sources not already exhausted: repository native record/files/version history; publisher article or data availability statement; institutional/project technical or final reports; archived pages or software release history when publicly accessible; author data/code catalog; exact award/funding evidence and corroborating SPARK project workstream. Up to five genuinely distinct checks in this round, record source URLs, first/recovery timestamps, date basis, evidence and contradictions. Preserve earlier `next_research_at` dates as historical scheduling metadata; if the additional round starts before a seven-day waiting period, document an explicit `early_retry_reason` citing this user-directed, different-source research priority (the blocker validator already permits an evidenced exception). Never silently backdate or reset retries. No new work should be described as a completed investigation until sources actually establish a defensible result.

After this additional round, **do not leave the case in an endless `needs_more_research` loop**. Resolve using evidence: (a) a verified, distinct, eligible output with complete truthful required fields → publish a standard append-only 24-column Scout Discovery Hub candidate; (b) truly existing REACH work, a version-family duplicate, an ineligible output, or no corroborated project-specific WPO link → document a defensible already-in-REACH or no-action decision with evidence and independent original-seed outcome; (c) a credible output with a specific, corroborated WPO project connection but unresolvable publication date, version, public scope, etc. → **human Investigate** handoff, with missing fields, checked sources, conflicting evidence and exact reviewer question.

## Human Investigate and Hub compatibility

For (c), a genuine human handoff should be the end of automated metadata recovery, not the start of an indefinite wait. However, this is a **human-review request, never approval**. Only claim delivery to the Discovery Hub if a valid and truthful candidate was actually accepted in an immutable Scout batch/manifest and its Hub-intake contract supports the missing metadata. Use `Scout classification: C NEEDS INVESTIGATION`, `Research escalation: Human Metadata Needed`, `Metadata recovery: Exhausted`, specific `Metadata missing:`, `Metadata checks:`, `Scout verification: Completed`, REACH comparison and public source evidence. If the Hub requires a filled publication date or another unknown required field, **never invent the field and never publish a deliberately invalid 24-column CSV**. Instead persist an explicit `human_metadata_needed` pending-handoff case in the existing metadata-blocker/lead ledger with the evidence and exact Hub-compatibility blocker; state **NOT DELIVERED TO HUB** and keep that operational handoff ahead of normal award discovery. Adapt the Hub intake only when its source is available and can be tested safely. Do not silently mark a handoff as successful.

Do not redirect plainly unrelated NOAA-funded or administrative grant-only materials to the Hub merely to clear the queue; close them with an evidence-backed no-action decision. Never infer that a grant-level match implies the funded WPO project produced an output. Scout remains responsible for checking linked products, deduplicating against all REACH and previously staged Scout entries, and preserving human reviewer decisions.

## Required hourly and briefing accounting

Report per cohort separately: original API inputs, initial investigations completed, final evidence-backed dispositions, unresolved needing another-source research, metadata exhausted / human evaluation needed, **actually delivered** Hub Investigate candidates, **blocked pending Hub support**, related distinct outputs verified, true duplicates, independent expansion discoveries, and progress before/after this mission. In the October 29 historical baseline, **150 of 188** original records had final research dispositions, **38** required follow-up; this is NOT equivalent to 188 resolved and must not be reported as such. Include provenance audit and GitHub feed integrity checks. Never count a staged candidate as human-approved or publicly added to REACH.

The monthly API intake is subject to the **same rules**, with original Crossref/DataCite records and related outputs independently researched before Scout reverts to older awards. An unsuccessful evidence search is not itself an automatic human-approved inclusion or an excuse for indefinite deferral. No Google Drive/Gmail and no direct REACH/SPARK/Smartsheet edits.

## Reviewer owns the decision after one credible, bounded research effort (clarification, 2026-10-29)

The purpose of Scout is to **find potential research outputs and explain the evidence**, not to become a permanent metadata-completeness gate. After the documented first investigation and one bounded distinct-source recovery effort, a credible eligible WPO project-linked finding with unavailable date, version or other metadata is **research complete / awaiting human decision**, not an open-ended Scout research failure. Do **not** repeat searches or postpone the human referral until another calendar date simply because a missing value may never be published.

**Give the reviewer a real choice** in the Discovery Hub when its intake supports it:
- **Needs Investigation** — retain the candidate in a human-review queue with the missing fields and sources already checked.
- **Approve for REACH despite missing metadata** — an explicit informed human decision to proceed *with only those omissions permitted by the receiving REACH/Smartsheet schema and validated publishing rules*. Show the missing fields before confirmation, keep them blank/unknown, and preserve the acceptance reason. Never fabricate a date, silently substitute a registration year, or waive an actually mandatory downstream field without an explicitly implemented and tested schema/rule change.
- **Reject / Already in REACH** — when evidence demonstrates ineligibility or duplicate identity; retain the reason.

If the **current Hub ingestion cannot display an incomplete case**, mark the research case `human_metadata_needed` with `research_completed: true`, maintain an auditable, separate **pending Hub intake** handoff record, and report **NOT DELIVERED TO HUB**. This is an integration queue for the reviewer tool, **not a reason for Scout to perform endless metadata searches or permanently postpone older-award discovery**. Reconciliation must preserve original identity, source evidence, missing fields, potential award, Scout's research trail and the outstanding reviewer intake action. Follow-up-first prioritization applies to *genuine unfinished research*; completed evidence recovery must move to human handoff rather than repeatedly consuming research missions. The team must be able to see the number awaiting Hub intake separately from those already visible to reviewers.

The public Scout GitHub checksum/manifest validator is **not** the same as the Discovery Hub or REACH publication gate. Do not weaken REACH insertion rules or claim reviewer access without verifying the Apps Script UI and Smartsheet write path. Changing the Apps Script intake/reviewer controls requires source access, a tested change and user deployment. The requirement to accept informed omissions does not itself authorize silent insertion.

## Broad-net discovery of outputs with missing award acknowledgments (2026-10-29)

Scout must search for outputs **without requiring a NOAA/WPO award number in the output itself**. The missing acknowledgement is a discovery gap to investigate, not automatic evidence of non-funding. Explore publications, NOAA IR reports, data, code, project pages, and author/institution product catalogs. Cross-reference SPARK projects and primary/related awards, PI/coauthor identities, institutions, topic and methods, project dates, deliverables, technical reports, and links among distinct outputs. Follow evidence-bearing links outward to additional products, recording source URLs and discovery path; do not limit discovery to 1–3 linked items arbitrarily.

**Attribution evidence tiers, not funding conclusions:** (1) *confirmed project bridge* — direct output-level award acknowledgement or independently corroborated primary project-specific documentary evidence linking this particular output to WPO-funded work; (2) *credible project-specific lead* — concrete author/project/deliverable or output-family evidence that warrants one bounded follow-up and potentially human evaluation, but does not yet establish funding; (3) *broad resemblance only* — NOAA affiliation, common cooperative-institute grant, shared PI, date, or topic without a specific workstream bridge. Multiple weak similarities alone do not equal independent corroboration. Document contradictory or alternative funding evidence; absence of an acknowledgement is **not** positive proof of WPO support, nor proof of non-support.

Maintain the original seed's evidence-backed no-action status when a bounded search fails to demonstrate WPO attribution. Preserve any separate lead and reopen only on **new positive project-specific evidence** or explicit reviewer request. Do not automatically send broadly related NOAA outputs to the Hub. Where a specific credible bridge remains uncertain after the bounded distinct-source follow-up, hand off an auditable attribution question to a human **only through a compatible validated review intake**, or keep it visibly pending intake; do not manufacture an award or bypass the metadata/24-column validation rules.

When a reviewer independently confirms an output was produced by WPO-funded work despite absent award acknowledgement, capture the corroborating project-output bridge and expand research to its related publications, data, code, reports, and authors. Never treat one confirmation as proof that all products from the author or project belong in REACH. Preserve distinct provenance: Direct API / API-seeded expansion / Independent discovery / Metadata correction, with source path and original seed DOI when applicable. Preserve private human decisions outside the public repository.

**Additional impact measure:** `WPO-funded outputs recovered without explicit award acknowledgment`. Count only *distinct outputs* whose lack of award acknowledgement was documented and whose project-specific WPO funding connection was subsequently confirmed by a human reviewer; report separately (a) credible leads awaiting attribution, (b) Hub-visible proposals, (c) reviewer-confirmed eligible outputs, and (d) verified new public REACH records. Do not equate staged candidates, reviewer approvals, or existing REACH corrections with new public outputs. Do not retroactively classify legacy discoveries without evidence. Include this funnel and expansion leads in hourly provenance audits and morning briefings when data are verifiable; otherwise label counts NOT VERIFIED.


## October 30 enhancement: typed metadata recovery and separate human intake

Read [metadata-recovery-policy.md](metadata-recovery-policy.md) before further metadata searches. Choose source-specific research methods for unknown first-public-release dates, version/concept DOI families, public/restricted file scope, poster/report eligibility and exact funded workstream bridges. One initial check round and one substantive different-source follow-up are enough unless genuinely new material evidence appears. An inaccessible native API means `source inaccessible`, not `metadata absent everywhere`. Preserve dates with provenance, never substitute manuscript publication or conference presentation dates for dataset/public release dates.

The 37 historical cases with `pending_hub_handoff` represent 31 provisional human review units in [metadata-review-units.json](metadata-review-units.json). These are **not 31 verified new outputs**: six units group possible concept/version or alternate DOIs for a single explicit reviewer identity decision. Keep all 37 original blocker entries and human dispositions intact. A separate additive Apps Script reviewer-intake prototype was prepared and tested OFFLINE, but **NOT DEPLOYED OR IMPORTED into the production Discovery Hub**. Public JSON publication does not imply actual Hub visibility. The reviewer can mark Needs Investigation, On Hold, Approved for Addition Pending Publication Validation, or Rejected/Already in REACH; none triggers REACH/Smartsheet edits. Preserve the existing 24-column new-output CSV validation and destination requirements; do not publish an incomplete CSV batch merely to force a Hub card.

When new research-complete missing-metadata leads appear, update the review-unit queue by exact DOI/normalized URL without rewriting existing review keys, decisions or previous evidence. Add new units or append NEW evidence explicitly; never silently regroup a unit already reviewed. Resolve or escalate conflicting duplicate group identities for human decision. Report independently: original DOI research complete, missing-metadata cases, grouped review units, privately delivered review cards (only if observed), human decisions (only if verified), staged outputs, and verified public REACH additions. **An outstanding Hub integration is not unfinished Scout research and does not block the next substantive discovery mission.**

## November 2, 2026 — critical metadata before first Discovery Hub staging

**Mandatory order:** Scout receives the exact original monthly DataCite/Crossref API DOI and primary-SPARK-award match; runs rapid REACH/Scout deduplication and funding anomaly checks; then runs the **critical metadata pre-staging checkpoint** before preparing any new public Scout review CSV. Missing title, DOI/URL, type, authors/creators, REACH Pub Date, Brief Abstract, output evidence URL, or funding evidence URL must be flagged. Missing PIs or PI emails alone must NEVER be guessed or used to block intake; those are distinct from author lists.

**Do targeted recovery immediately**, not after Hub staging: exact DOI direct DataCite / Crossref metadata; native repository landing/versions/files; publisher full abstract, acknowledgments and data-availability section; NOAA Institutional Repository exact DOI/title; official institutional catalog and funded project's output list. Prefer the original source first, cross-check the same DOI, record checked URLs, results and access limitations. Do not infer funding simply from broad NOAA connections. Do not fill unrelated article dates or change output type to bypass the gate. For **DataCite** use a valid created YYYY-MM-DD as the approved default REACH Pub Date; clearly label it a source metadata creation date, not necessarily first public release. For **Crossref** prefer published-print, then published-online, then published/issued (posted first for preprints); YYYY-MM is normalized to YYYY-MM-01 with original month precision recorded. Never use Crossref created.

Record the outcome under `scout-operations/monthly-triage.json` entry `metadata_recovery`: `status=resolved|exhausted`, list of specific substantive `checks` each with `method`, `url` (HTTPS), `result`, and recovered values under `resolved_fields` with **exact field names** and source `evidence_url`. Run an initial source-specific search plus ONE different-source bounded follow-up (normally no more than five distinct substantive additional checks), then stop; do not loop hourly. The updated `quick_monthly_intake.py` rejects missing-critical-metadata drafts without this documented checkpoint, and `prepare_batch.py` rejects incomplete monthly staging without the recovery-completed/source-check evidence and an explicit NEEDS INVESTIGATION review classification.

After recovery: fully populated eligible output -> fast-track to human new-candidate review; credible but genuinely unresolved output -> human Needs Investigation with **concrete remaining checks** and no fabricated values, if valid Hub intake permits it; unverified output identity, duplicate family, unsupported funding or unavailable required schema field -> documented human integration or funding/identity hold, **not** automatic approved/public REACH. Related DOI-seeded expansion follows original first-pass stage separately; never block a valid original candidate just because connected outputs await research.

**Every candidate from every mission type** (Monthly API, Historical DataCite, API-seeded expansion, independent Scout) must carry a useful `What to check before adding this output:` rationale line. The 24-column CSV schema is unchanged. `prepare_batch.py` supplies a safety fallback if the mission omitted a case-specific line, but Scout should write **case-specific evidence, unanswered questions, source links and precise reviewer actions** rather than a generic slogan.

**Existing October DOI abstract example:** `10.1016/j.pdisas.2026.100696` NOAA IR source `https://repository.library.noaa.gov/view/noaa/77174` provides exact DOI, summary and direct WPO award. Original immutable monthly batch is retained; the active Scout feed now uses the audited, single-record supersession `2026-11-02-monthly-enriched-pdisas-100696-001`, preserving identity, original discovery method and NEEDS INVESTIGATION decision. This correction is **not** a new output, human approval, private Hub import, or public REACH publication. Reviewer must Sync to Scout and check the new rationale; if a saved Hub importer still treats monthly FAST findings as provenance-only, apply the attached additive Hub fix before expecting metadata refresh. All existing human decisions and publication gates remain in place.
