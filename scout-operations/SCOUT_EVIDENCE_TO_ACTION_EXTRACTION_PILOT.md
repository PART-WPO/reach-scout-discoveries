# Scout evidence-to-action: structured public-note extraction pilot

Status: **read-only pilot**. No active hourly selection, private Discovery Hub, reviewer, SmartsheetGov, or public REACH behavior changes.

## Motivation

Scout's first evidence-to-action pilot evaluated 35 source-identified public research cases from 53 immutable research-note events on November 9, 2026. Twenty cases had earlier structured decision records. Fifteen cases relied on nonstandard raw note schemas and were initially treated as needing evidence extraction rather than immediately triggering more research.

This second pilot extracts **explicit machine-readable facts already in those source notes** before invoking the same decision compiler. The tool does not browse, generate new research notes, send review proposals, or alter the 24-column staging process.

## Reproducible procedure

1. `python scout-operations/tools/extract_structured_research_evidence.py` and `--check`: verify every research-note file against its registry SHA-256, emit source-scoped fields and exact field provenance into `scout-operations/reports/extracted-public-evidence-pilot.json`.
2. `python scout-operations/tools/evidence_to_action_pilot.py` and `--check`: compare original decision pilot vs using extracted data **only for identities missing a pre-existing curated structured decision**; emit before/after counts and exact next actions into `scout-operations/reports/evidence-to-action-pilot.json`.
3. `python -m unittest discover -s scout-operations/tests -p 'test_evidence_to_action_pilot.py' -v` and `python -m unittest discover -s scout-operations/tests -p 'test_structured_evidence_extraction.py' -v`.

The `scout-evidence-to-action-pilot.yml` Actions workflow performs these steps on code/data changes and manual dispatch, uploading both results as **temporary read-only artifacts**, not committing generated reports to main.

## Field provenance and safeguards

- Every extracted assertion preserves the exact public note path, SHA-256, case-scope JSON pointer and narrow status value. No raw source text or author lists are copied into a new public person index.
- Nested `cases[]` are matched by exact DOI. A `research_subject.child_dois[]` link is not allowed to inherit its parent's funding or publication status. URL-only code evidence is kept distinct from DOI identities.
- Official publication status is accepted only from explicit, recognized fields. An award cited in a publisher/NOAA IR document is **not** a verified SPARK primary award or same-project deliverable. Unverified, ambiguous and 432 umbrella grant cues stay unresolved.
- Monthly direct-API cases may use the published Scout policy's expedited exact primary-award threshold. Historical and independently discovered related products demand independently corroborated same-project project evidence. In both cases the complete fresh identity screen, publication version, metadata and current staging gates remain mandatory.
- A preprint original stays on the monthly watchlist; a journal DOI is separately investigated. Contradictory award evidence blocks new candidate proposals. A confirmed original duplicate does **not** complete related-output expansion.
- A prior source hold cannot overwrite newer explicit evidence; only the **latest** note's explicit reopen-only directive triggers that specific hold. Research-count budgets still require material new evidence to justify repeating searches.
- An old source snapshot never substitutes for a live SHA-matched complete REACH/Scout comparison. Missing metadata or repository access is not evidence that the output does not exist. Sources are historical **evidence context**, not presently live truth claims.
- Scout's `SCOUT_OPERATING_POLICY_V2.md`, `decision-contract-v1.md`, `research-closeout-policy.md`, `preprint-watchlist-policy.md`, `no-action-disposition-policy.md`, and `SCOUT_BATCH_PROJECT_FIRST_PILOT.md` remain authoritative and are hashed in the resulting pilot report.
- This pilot never creates a human decision, private import, public Scout staging row, formal original completion, expansion completion or REACH publication.

## What the pilot measures

For the November 9 source snapshot, CI reported 35 identities / 53 research events / 15 formerly unstructured cases; 14 of 35 proposed dispositions changed after existing-note extraction. This demonstrates **decision categorization from prior evidence**, not independently verified WPO output eligibility, faster hourly operations, human reviewer acceptance or new REACH publications.

Evaluate case-level changes against exact source notes and the current Scout operating contract before considering any hourly integration. If an upstream record changes, rerun extraction and pilot against fresh source hashes; do not reuse the frozen counts as current state.

**Potential next phase:** review the changed cases with a stratified human gold-standard sample; measure whether named source-level holds avoid repeat missions while eligible missed WPO outputs are still surfaced. Integrate only after the false-hold and missed-output controls pass.
