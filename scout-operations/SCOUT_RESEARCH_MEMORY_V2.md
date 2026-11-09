# Scout research memory — Historical Crossref/DataCite and related-output expansion (v2)

This phase extends the source-verified DOI memory from independent metadata lookups to a **cross-lane relationship and research-work graph**.

## Public evidence inputs

The graph rebuilds the current unified preflight from its SHA-verified source files and the research-outcome registry from its immutable note files. It also checks explicit related-output DOI relationships in the monthly expansion and independent discovery ledgers, and structured DOI leads recorded in the public research-leads files. The historical direct DOI metadata checkpoint is indexed as **provenance only**; an old checkpoint is not asserted to be a fresh Crossref or DataCite response.

The output lives at `scout-operations/research-memory/crosslane-relationship-graph.json`, with source fingerprint, per-DOI lane identity, separate original and related-output research fingerprints, source-note checksums and source-linked DOI-to-DOI relationships. It intentionally excludes authors, PI names, collaborators, email addresses, funding claims and private reviewer information.

## Separating identity and discovery

For historical Crossref DOIs **already in REACH**, Scout may reuse the source-verified original identity and avoid another new-original screen. **Every such DOI remains a separate expansion seed** for datasets, code, citations and related research; source identity does not imply completed expansion.

An earlier research note is reusable evidence *context*, not proof of finished original investigation. Existing related-output DOI links remain separate identities with their own identity, version, publication, funding and project-evidence checks. An independent related-output link never inherits funding from its parent seed. A new explicit relationship changes the expansion fingerprint without changing the original source fingerprint.

Preprint originals retain existing monthly-watchlist policy. A failed metadata request is not a negative result. New public source evidence is checked against all source hashes; stale or mismatched input stops the graph from being represented as verified.

## Compact hourly mission index

The full relation graph is detailed (over 1 MB) and is not an efficient file
to read on every hourly run. The same source-verified generation now writes
`scout-operations/research-memory/mission-index.json` — a bounded preview of
at most 12 candidate DOI tasks per lane, with the same input source fingerprint.

Every hourly mission should read this compact index **after** reading the
existing authoritative `active-workstream.json`, not replace its prioritization.
A DOI can belong to several source cohorts; **monthly-original work takes
precedence even when the same DOI is also in historical Crossref/DataCite**.
Original research from preprints stays in the monthly watchlist, never an
hourly new-output lookup. A monthly original already recorded as staged for Hub import, existing
in REACH, or no action stays in `monthly_existing_public_disposition` and
does not enter `monthly_original` for redundant research or review.
A published public-stage disposition does not verify a private Hub import.
A related output with a recorded public
already-in-REACH or staged-for-human-review status is preserved in a separate
`existing_public_related_or_staged` research group rather than selected
for duplicate review. This records public status only, not private Hub import.
The mission index shares **both** the graph's source fingerprint and its
builder-policy SHA, to detect code changes as well as evidence changes.
The preview includes separate monthly originals, monthly related, Crossref
identity/research, verified-REACH related-output expansion, historical DataCite,
and DOI-less code research lanes. It downranks previously researched evidence
without discarding it, preserves exact DOI paths and independent expansion.
The hourly agent may select a different DOI if new evidence or the workstream
indicates a better task. A fixed preview is not a finished scan or a mandate to
repeat the same item. If the graph and preview fingerprints disagree, do not
reuse them; refresh from verified public input.

The compact index is a **selection aid**, not proof of previous research
completion. Do not claim API requests or reviewer effort were saved without
measuring actual subsequent mission behavior.

## How to use the memory as a research tool

For an hourly mission or a manual investigation, read the graph's `work_items` for the requested DOI or `primary_role`:

- `ORIGINAL`: reuse public identity and prior notes before new source queries; do not declare formal closure
- `EXPANSION`: check already identified child DOIs, then continue *new* project-linked related-output discovery when appropriate
- `RELATED_OUTPUT`: investigate the child as an independent DOI; verify distinct published identity and exact WPO/project evidence

Match the item's `input_fingerprint` to the current graph; if unchanged, do not re-fetch identical historical evidence just to repeat its conclusions. Use source evidence as a starting point; recheck live REACH, NOAA IR and preprint/version identity where needed. A changed source checksum, new explicit child DOI or new research evidence should be investigated. Source memory can reduce repeated work but cannot infer human approval, guaranteed completeness or grant attribution.

The 426 confirmed REACH Crossref originals are **high-value potential expansion seeds**, not 426 completed explorations. The historical DataCite cohort remains separately available, regardless of Crossref original screening. Research mission priority remains governed by monthly intake and existing workstream policy, not by this memory graph alone.

## Quality and privacy gates

- Rebuild: `python scout-operations/tools/build_crosslane_research_memory.py`
- Validate immutable source state: `python scout-operations/tools/build_crosslane_research_memory.py --check`
- CI: `python -m unittest discover -s scout-operations/tests -p test_crosslane_research_memory.py -v`

GitHub Actions refreshes the graph on relevant source changes and after successful source refresh workflows. It has no authority to create a public Scout candidate, private Discovery Hub record, human reviewer decision, Smartsheet insertion or public REACH addition. Public SPARK project titles and exact primary award identifiers may inform separate project matching, but this graph never ingests SPARK investigator/personnel fields.

## Limits and next validation

This phase produces a **source-linked research workload and durable evidence relationships**, not a general automatic scholarly crawler. New citation/reference traversals and exact DOI metadata refreshes remain separate research actions. Evaluate whether actual hourly agents consume the graph and reduce duplicate source fetches; report real before/after counts rather than claiming performance solely from the existence of an index. Independent 100-case human labels are still needed to quantify missed WPO outputs or false-negative research deferrals.
