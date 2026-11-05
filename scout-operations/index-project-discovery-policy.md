# Scout 2.0 — Metadata-change and project-based discovery

## Why this check exists
The monthly award-based Crossref harvest finds publications with publication dates in the previous month, while some WPO-relevant publications were published earlier and received delayed or corrected metadata/funding acknowledgments. A publication-date filter alone can miss those new API records. A project can also produce research without its literal grant award appearing in Crossref/DataCite structured funding.

The separate, public `.github/workflows/scout-incremental-project-discovery.yml` combines:
1. **Crossref from-index-date** incremental metadata changes for SPARK **primary** Award Number(s), strict matching against actual `funder.award` values. Index date means Crossref metadata changed or was indexed; it is **not** the article's publication date. No publication metadata may be invented from `created`, `indexed` or `updated`.
2. **Bounded project-specific bibliographic search** for up to five SPARK primary-award project titles, across public Crossref records without requiring structured grant matches. Shared title words are only an untrusted research breadcrumb; never assert WPO project funding from common topic, program or investigator.

The existing first-of-month API-original intake is untouched. The supplemental workflow runs first of each month including weekends; the release/pull-request pilot checks only five primary awards for fast, safe production testing, then the scheduled full metadata-index pass checks the primary SPARK award catalogue (initial historical snapshot ~693 award identifiers). It fails on API pagination ceiling, response errors or incomplete source coverage; no incomplete run becomes an asserted empty result.

## Output and use
- Immutable, SHA-verified report: `api-discoveries/index-update-runs/<month>-<digest>.json`.
- Pointer with count, run mode and SHA: `scout-operations/index-and-project-discovery-leads.json`.
- Every DOI lead contains exact API evidence URL, public REACH/Scout identity status, preprint hold, raw project/title context, and a clear next research action.
- **No Scout candidate feed staging, private Discovery Hub import, human approval, Smartsheet insertion or REACH addition** is authorized by this workflow.
- A DOI found through a change to old publication metadata should first be checked against REACH/Scout/human history, then its same-project WPO funding/eligibility established. A project-title hit needs stronger evidence than an explicit exact primary structured award.
- Source-specific attribution stays with each lead; if a DOI appears in multiple searches, preserve its original route and linked evidence without inventing multiple novel outputs.

## Next safeguards
Project-title searching is initially limited to a few representative SPARK projects to measure distinct, legitimate WPO discoveries before broader scale. It does not yet cover all possible public reports, applications and software without DOIs; those require a separate, source-specific discovery adapter, project product catalogs and verified URL identities. Do not claim universal recall from DOI-only APIs.

Reviewer planning goal remains 20+ defensible human decisions per week. Discovery volume alone is not a measure of Scout's success. Track unique verified WPO candidates, false positives, duplicate rate and reviewer effort before adding more API providers.
