# Scout 2.0 — Relevance-based related-output exploration
**Authoritative policy effective November 5, 2026; supersedes any older requirement to conduct full citation/reference expansion from every harvested DOI.**

## Purpose
Scout should discover overlooked WPO research products while avoiding hours of unrelated citation chasing. A DOI from Crossref, DataCite, independent discovery or monthly intake is **a persistent lead**, not a mandatory research expansion.

The priority gate is implemented in `scout-operations/tools/build_expansion_relevance.py`. Its SHA-pinned read-only output is `scout-operations/expansion-relevance-priority.json`, which is also reconciled into `active-workstream.json` and `scout-operational-scorecard.json`. The source Crossref manifest, all initial screening batches, historical research and seed ledgers, and prior human decisions are immutable.

## Three levels of exploration
1. **PRIORITIZE_VERIFIED_WPO_SEED.** An exact, unique REACH WPO catalog identity, corroborated by the current bulk DOI/title or NOAA Institutional Repository DOI-to-canonical-REACH-URL check, is a credible seed for targeted dataset, code, report or related-publication research. Existing REACH **is not** evidence that every citation or linked product is WPO-funded. Check each distinct related output independently before any public review suggestion. An explicitly corroborated same-project SPARK primary-award link can likewise support priority, but must be documented rather than inferred from topical overlap.
2. **VERIFY_WPO_PROJECT_SCOPE_FIRST.** An index-negative or ambiguous Crossref original, or a monthly/independent related lead with insufficient verified project connection, should receive a **bounded, project-specific WPO assessment** before searching a broad reference graph. A source structured award may initiate this check but does not prove the research was produced by the specific WPO project. Missing evidence is not permanent exclusion.
3. **DEFER_UNTIL_NEW_PROJECT_EVIDENCE.** Use only for a documented source-attribution anomaly or a previously bounded case with independently checked public sources that did **not** establish the proposed WPO project connection. It is a reversible research-priority hold, **not a declaration that the DOI is unrelated or no longer exists**. Do not chase its references until materially new project-specific support appears or a reviewer requests reconsideration.

### Reconsideration
A new independent source can reopen a soft-deferred case to **VERIFY_WPO_PROJECT_SCOPE_FIRST** (not immediate approval) through `scout-operations/expansion-scope-reconsiderations.json`. Require a source DOI, two distinct HTTPS evidence URLs, an explanation specific to the proposed WPO project, and SHA-256-verified supporting evidence files. Repeated searches or general institutional/subject similarity are not materially new evidence.

## Ordering
New monthly original outputs still take first priority. Separate already-researched monthly related-output leads retain their staged/private-handoff status: a change to exploration priorities must NEVER retract an existing public review proposal or change a human decision. Historical Crossref seeds with verified REACH identity receive targeted related-output exploration; others first undergo a short scope check. Known irrelevant/poorly attributed leads with documented bounded research are deferred. Independent-research leads follow the same conceptual scope standard, but retain their existing public/human-referral states.

**The research seed ledger remains separate from original-output research.** A relevance decision does not make any original DOI terminal, does not close an expansion lane and does not stage a candidate. The existing completion validator remains authoritative for those transitions. A recorded REACH duplicate can still seed distinct outputs when their own WPO project connection is established. No private Hub/Smartsheet/REACH modifications are authorized.

## Operating constraints and quality
- Require source manifest SHA, verified REACH cache SHA, NOAA IR index SHA, and each DOI identity to match before publishing priorities.
- Public REACH or canonical-URL identity is a research relevance signal, **not a human-approved project funding attestation** for unrelated related products.
- Avoid blanket searches, repeated source retrieval and automatic expansion of weak project matches.
- Record source-specific evidence, primary SPARK Award Number(s), version/preprint relationships and eligibility before any potential new output goes to a human.
- Preserve the first-of-month preprint publication watchlist; no preprint originals may be staged.
- Preserve public/reviewed/new-REACH distinctions and no automated approvals.
- The reviewer planning capacity of 20+ cases a week is a future **quality/conversion target**, not a quota that justifies pushing low-evidence candidates to Discovery Hub.

## Initial regression checkpoint (not a permanent target)
On the November 5, 2026 Crossref snapshot: 614 historical DOI leads persist; 433 have verified public REACH identity and are suitable for targeted project-related exploration; 179 require a WPO project scope check before broad expansion; and 2 researched biomedical attribution anomalies have a reversible, source-backed hold. All 614 original expansion statuses remain unchanged and no human reviews are altered. Current values must always be read from the latest SHA-verified priority and scorecard files.
