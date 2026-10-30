# REACH Scout targeted metadata recovery and human-intake policy (2026-10-30)

The research and reviewer workflows are **separate gates**. A missing field does not prove an item is ineligible, but neither does a credible grant/project connection prove that it is a unique catalogable output. Preserve all original DOI dispositions, Hub decisions and existing 24-column Discovery Hub CSV contract.

## Step 0 — output eligibility before metadata
For each DOI/URL separately verify: public standalone output identity; actual specific WPO project bridge (direct output-level award evidence, or qualified independent SPARK-linked association with clear uncertainty); candidate type; dates/creators where known; existing REACH and Scout duplicate/version-family checks and private reviewer decisions when available. Broad NOAA CI awards, author/topic overlap and inaccessible repository pages by themselves do not prove WPO funding or uniqueness.

## Targeted recovery by missing field
- **Dataset release/publication date**: Inspect native repository landing and API (e.g., DesignSafe, Dryad, Figshare, Zenodo, Scripps ERDDAP, HydroShare, Dataverse), repository version-history provenance, DataCite `dates.dateType` and recorded created/published/available date type, primary paper data availability and project data catalog. Never substitute paper year, DOI registration, dataset observation period, conference date, report submission or last-modified timestamp for FIRST public release.
- **Software initial release**: GitHub/GitLab release/tag provenance, README version notes, Zenodo archived releases and concept/version relations. Distinguish release dates from source revisions.
- **Poster, conference abstract, technical report**: Official conference program and first publicly posted archive version, repository issue/publication date, report series record and author-hosted copy. A presentation/submission date is not proof of public availability.
- **Duplicate/version/canonical identity**: exact DOI and URL, DataCite `relatedIdentifiers` relationship type, Zenodo concept/version chain, Figshare canonical version/identifier, repository record ID, file inventory and differences, public REACH record UID and known staged human dispositions. Group probable families for ONE human decision **without presuming duplicate identity**.
- **Public scope/access**: native files and download/permission state, accessible public abstract vs restricted participant data, selected project components; never treat closed datasets as publicly retrievable data, or publish sensitive files.
- **Award bridge**: direct output acknowledgement/publisher funding, official repository funding metadata, specific funded SPARK primary project output list, independent corroboration. Broad CI award alone insufficient.

## Recovery budget, evidence and stopping
Use source-aware checks rather than repeating the same generic search. Capture each distinct method, URL, source date type and result, conflicts, source failures, verified fields and remaining questions. Run an initial pass and ONE bounded diverse-source follow-up (normally <=5 new substantive checks), with a documented exception only for genuinely material new evidence. If a source is blocked, record **access failure**, not 'metadata does not exist'. Keep meaningful leads for human intake; do not continue indefinitely on required metadata that may not be published.

## Status and human workflow
1. `RESEARCH_ACTIVE`: meaningful unused sources remain.
2. `RESEARCH_COMPLETE_VERIFIED`: complete eligibility + required fields -> standard unique reviewed 24-column candidate.
3. `RESEARCH_COMPLETE_HUMAN_INTAKE`: credible project/output with unresolved date, version, distinctness or public scope -> **separate private intake queue**, with evidence and explicit review question. It is NOT a candidate published in Scout discovery batches, a Hub-verified imported card, an approval, nor public REACH.
4. `RESEARCH_COMPLETE_NO_ACTION`: evidenced duplicate, non-output, or insufficient project attribution -> preserve negative evidence; no proposal.
5. `HUMAN_REVIEWED`: reviewer records Needs Investigation / On Hold / Approved for Addition subject to final validation / Rejected or Already in REACH; do not infer approval, overwrite decisions or auto-publish.

The 37 pending_hub_handoff source cases from 2026-10-30 are grouped as **31 human decision units** in [metadata-review-units.json](metadata-review-units.json); six groups are provisional Zenodo/Figshare concept-version or Scripps alternate identity pairs and may or may not correspond to single outputs. All original 37 DOI/URL identities remain traceable, no automatic merge/reject has occurred. No Hub ingestion is claimed.

## Integration gate and safety
Existing 24-column Discovery Hub batch format stays unchanged. A proposed *additive private Apps Script review intake* may read the public [metadata-review-units.json](metadata-review-units.json) and present these in an independent review sheet/modal without writing existing Cases, decisions, REACH/SPARK/Smartsheet or staging CSVs. DO NOT claim this is installed or Hub-visible without observing a real authorized test/import in the bound spreadsheet. No publication date invention. Publishing to REACH still requires original destination schema validation; a reviewer may waive a missing field only where source policy/schema expressly permits it. Deployment requires the current Apps Script Hub source/version compatibility check and a controlled smoke test with a backup.

## Report independently
Count source cases; distinct review units; research-complete unresolved; private human intake installed and successfully imported (only with evidence); human-reviewed; verified approved; staged Hub candidates; verified public REACH additions, separately. An unresolved date and an unresolved identity are not the same type of blocker. Do not conflate counts.
