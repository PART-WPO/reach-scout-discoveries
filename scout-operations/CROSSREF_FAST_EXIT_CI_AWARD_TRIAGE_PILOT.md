# Crossref backlog fast-exit and Cooperative Institute award triage — pilot addendum (2026-11-06)

This addendum refines the batch pilot and does not supersede the authoritative operating policy or immutable historical decisions.

## Existing REACH fast exit

For every historical Crossref DOI, reuse current SHA-verified complete REACH identity cache, published Scout batches/inbox, official NOAA IR canonical mapping and source routing. Exact DOI plus compatible normalized title and unique REACH UID, or official IR canonical mapping plus compatible title and unique UID, is **already in REACH** for original-new-output screening. Stop further original discovery investigation on that identity; retain source and original status unchanged. Do **not** spend deep-research slots rechecking these matches. Distinct code/data/report expansion from verified WPO seed is a separate mission and case. Multiple UIDs, title/version contradictions and the 47 possible matches get one bounded identity resolution, not auto-closure. Index-negative alone never proves absent or unreviewed privately.

## Funding-prefix signals (triage only)

The user reports Cooperative Institute NOAA awards commonly containing `432`, versus WPO awards containing `459`. Extract these patterns from **actual structured award identifiers**; do not match arbitrary occurrences in DOI, year, title, or unrelated strings. Treat a 432-pattern NOAA CI umbrella award without exact primary SPARK WPO project evidence as **CI_UMBRELLA_REQUIRES_PROJECT_PROOF**: lower priority / short bounded project check / evidence hold, never auto-attribute to WPO. A 459-pattern award is **WPO_POSSIBLE_NEEDS_PRIMARY_SPARK_CONFIRMATION**, not independent proof of WPO funding. Unknown, mixed, legacy or nonconforming awards are **PREFIX_INCONCLUSIVE**, not automatically excluded. Primary SPARK `Award Number(s)` and specific output-to-project evidence outrank any pattern. Never use `Related Award Numbers` as funding proof.

## Suggested pilot funnel

1. Reuse validated REACH/Scout/IR identity: existing original -> fast exit; ambiguous -> one bounded identity check.
2. On novel originals, preprint eligibility check; defer preprint to watchlist.
3. Evaluate exact structured primary SPARK project evidence, then funding prefix as a *weak* prioritization signal.
4. Investigate only source-specific promising WPO candidates and previously ready recovery/referral cases; hold generic CI umbrella hits with one concrete missing primary project evidence item.
5. Count existing identities excluded from new-output research, CI umbrella holds, verified primary-WPO candidates, ambiguous matches, and eligible reviewer proposals separately. Never count an existing-REACH fast exit as an expansion closure or new review candidate.

No changes to private Hub, human decisions, REACH or SPARK are authorized by this addendum.

## Concrete FY26 award format example

User-confirmed example: `NA26OARX459C0001`. The WPO triage signal is the **459 award-program segment** in a structured NOAA award identifier, not an arbitrary substring. The optional `X` following `OAR` and `C` before the serial number are valid for this newer format; preserve the exact identifier including letters, leading zeros and any authorized suffix. Older WPO examples include `NA22OAR4590527`. Compare the complete normalized award to SPARK primary `Award Number(s)` for attribution; a matching 459 segment alone is a relevance signal only. Do not restrict screening to `NA..OAR459....` and accidentally reject `NA..OARX459C....`.
