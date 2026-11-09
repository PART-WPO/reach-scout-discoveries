# REACH Scout decision contract v1 — 2026-11-04

**Operational scope:** The reusable, read-only decision and identity gates in
`scout-operations/tools/decision_pipeline.py`. This document consolidates
the conflicting funding thresholds in older append-only policies **for these
gates**, without rewriting original ledgers, immutable API batches, human
decisions or the 24-column Discovery Hub contract.

## One identity gate, three independently reported places

1. **REACH:** read the SHA-verified, complete public REACH comparison cache,
   including detail/secondary links and DOI identities. Exact DOI or exact
   canonical output URL is a confirmed **public snapshot** identity;
   normalized-title-only is an ambiguous match requiring version/detail review.
2. **Scout:** compare exact DOI, URL and normalized title against the entire
   SHA-verified public manifest/batches **and** every current inbox draft.
   A public queue match is not a REACH publication or a human decision.
3. **Private reviewer history:** when accessible, honor existing human
   decisions first. When not accessible, record `NOT_VERIFIED`; never invent a
   verified absence, private import, approval or REACH addition.

`NO_PUBLIC_IDENTITY_MATCH` means none of the above public identities matched
in **that source snapshot**. It is not a global newness attestation. An index
derived from stale REACH or Scout snapshots is invalid; refresh first.

## Shared identity/disposition hardening (November 9, 2026)

- The existing shared index remains the single public DOI/URL/title lookup. A
  unique exact DOI or canonical URL is **not** sufficient for a terminal
  duplicate call. Confirm a public REACH or Scout identity only when the
  supplied normalized source title matches exactly one record in that
  destination. Missing title, mismatched title, title-only overlap, and
  multiple destination identities produce a bounded identity/version review,
  never an automatic duplicate exclusion.
- The read-only `tools/identity_disposition.py` resolves a public disposition
  across REACH, Scout inbox/published queue and the separately maintained
  preprint watchlist. It preserves every previous preprint DOI pointing to a
  published version, but never treats a family relationship as proof of the
  final article's award attribution. An original/seed's DOI-seeded expansion
  remains open regardless of its original duplicate disposition.
- Public absence means only no match in a verified snapshot. No GitHub
  workflow can infer private Discovery Hub import, human decisions,
  Smartsheet insertion or REACH publication.
- **Author/privacy boundary:** NEVER pull author names, PIs, collaborators or
  personnel from SPARK for discovery, and never publish them back into SPARK.
  A future author-based discovery lane may take transient author seeds only
  from checksum-verified **public REACH publication metadata**, joined to an
  **exact primary award**. No verified REACH publication for the award means
  **no author-based seed**. Search via award, DOI, citations, related datasets,
  software, project title or other non-personal routes instead. A shared
  author name alone is never WPO-funding proof. The current REACH comparison
  cache has no author fields and thus deliberately returns zero author seeds.
- The public frozen 100-case set is a **coverage/regression replay only**;
  independent gold labels have not been collected. Do not publish accuracy,
  recall, reviewer-time or accepted-output rates from source-derived labels.
  Use `python scout-operations/tools/identity_disposition.py --benchmark`
  only after confirming source fingerprints. Private truth labels remain
  within authorized reviewer-controlled infrastructure.

## Funding-threshold distinction (do not flatten)

- **Monthly Direct API originals:** Publisher/repository structured funding
  explicitly matching a literal **primary** SPARK WPO award, an officially
  available distinct output, completed identity/metadata gates, and **no
  contradictory project evidence** can justify a *human-review proposal*.
  This is **not** certified project attribution, nor approval. A person
  confirms the proper parent; multiple plausible parents remain a reviewer
  question. Never stall ordinary eligible monthly originals to pursue DOI
  expansion or a more demanding proof standard.
- **Historical Crossref/DataCite and independent expansion:** an exact
  primary-award string is a **lead**, not adequate standalone evidence that
  the output belongs to that specific WPO project. Demand corroborated
  same-project evidence before recommending a new-output draft. Project-
  specific uncertainty can receive a documented research/human-intake hold;
  broad institutional awards or topical overlap alone should not burden
  Discovery Hub reviewers.
- **Contradictory source evidence:** stop proposal creation until reconciled,
  in either cohort. Shared blanket or umbrella/cooperative awards must not
  override an independently identified unrelated funding purpose. Full
  FY25+ task suffixes remain distinct; Related Award Numbers do not qualify
  as primary awards.

## Deterministic gate ordering

1. Existing private human decision, if **verified**, is respected.
2. Exact public REACH / Scout duplicate or ambiguous title/version identity
   is handled before further funding research.
3. Official final publication vs preprint hold; all modes prohibit preprint
   original new-output staging while preserving monthly watchlist and
   independently discovered final DOI leads.
4. Direct matching primary award, project-specific corroboration as required
   by cohort, and contradictory evidence.
5. Complete canonical secondary/version identity checks and required metadata.
6. `READY_FOR_VALIDATED_DRAFT_PREFLIGHT` is a **recommendation only**.
   Actual staged draft requires the existing 24-column `prepare_batch.py`
   validation and separate inbox GitHub Action promotion. Private Hub import,
   human approval, and REACH addition are distinct and remain **NOT VERIFIED**
   unless observed.

## Decision preservation and stopping rule

Each DOI has independent **original** and **DOI-seeded expansion** tracks,
even when the original is duplicate, held or research-complete. Initial
research plus one substantive distinct-source follow-up normally mandates a
documented determination/hold rather than indefinitely repeated generic
search. A hold can reopen on material new evidence or a human instruction.

Case checkpoint files are **immutable derived revisions**, keyed by canonical
DOI hash and by evidence+identity-snapshot fingerprint. A new source snapshot
or substantive evidence creates a new revision; old revisions are preserved.
The code does **not** update historical triage, human decision records, public
REACH, private Hub, SPARK or publish candidates.

## Runbook

Run `python -m unittest discover -s scout-operations/tests -p 'test_decision_pipeline.py'`
before deployment. Use the existing validated REACH comparison cache and
public Scout manifest. A GitHub Action must first verify that the live
public REACH manifest SHA agrees with the cached source manifest. Then:

```bash
python scout-operations/tools/decision_pipeline.py build-index
python scout-operations/tools/decision_pipeline.py lookup --doi 10.1002/qj.5049
python scout-operations/tools/decision_pipeline.py evaluate \
  --cases scout-operations/tests/published-crossref-decision-cases.json
```

Index source changes invalidate the saved cache rather than silently producing
negative matches. One cache construction supports all 614 Crossref DOI lookups
and the monthly and independent pipelines through this **shared CLI**.
Only the three bounded historical test DOIs are evaluated automatically by
the initial workflow. This does not claim the monthly intake script or private
Discovery Hub already invokes this new tool; these integrations require their
own verified changes.

## Success and burden metrics

Report source snapshot fingerprint, identities checked, REACH matches, Scout
batch/inbox matches, title/version review flags, original decisions and
expansion leads separately. Distinguish `READY_FOR_VALIDATED_DRAFT_PREFLIGHT`,
validated public inbox/batch, verified private Hub import, approval and
public REACH publication. Track time to first meaningful DOI decision,
repeated source checks and reviewer-ready decision units without inventing
private outcome counts.
