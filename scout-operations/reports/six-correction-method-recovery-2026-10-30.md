# REACH Scout: six missing discovery methods recovered

**Evidence audit:** October 30, 2026 (Eastern). **Status:** Method classifications integrated into automated attribution metrics; private Discovery Hub state not inspected.

## Terminology

Stable machine-readable methods remain unchanged for compatibility. Public display labels are:

| Canonical route | Plain-language label | Definition |
|---|---|---|
| Direct API | Found in API results | Award-targeted API returned the exact output |
| API-seeded expansion | Discovered by following API leads | Scout followed an API seed to a different output |
| Independent discovery | Found through independent research | Scout began with SPARK awards/projects or other research without an API seed |
| Unclassified | Discovery method unknown | Original path not confirmed |

These describe how Scout **found the work**, not whether the work should be added or modified in REACH.

## Six source-backed original methods recovered

The separate [method-recovery-followups.json](../method-recovery-followups.json) stores exact immutable batch SHA-256, source run ID, row number, output identity and public evidence URLs.

| Original candidate DOI | Method recovered | Why |
|---|---|---|
| `10.17603/ds2-0fwc-wy13` | Found in API results | Exact Hurricane Ian evacuation-orders DOI present in original historical DataCite award-targeted intake |
| `10.17603/ds2-j9hc-xy24` | Found in API results | Exact Laura/Marco instruments DOI present in original historical intake |
| `10.17603/ds2-rgbs-xd77` | Found in API results | Exact Laura/Marco survey dataset DOI present in original historical intake |
| `10.17603/ds2-xjyf-nc93` | Found in API results | Exact Survivor Stories protocol DOI present in original historical intake |
| `10.1175/BAMS-D-23-0036.1` | Discovered by following API leads | This related BAMS article was investigated from the separately captured Survivor Stories protocol DOI `10.17603/ds2-xjyf-nc93` |
| `10.15191/nwajom.2023.1109` | Found through independent research | October 30 07:29 mission documented NORMAL HISTORICAL DISCOVERY, SPARK/WoFS project, and publisher/NOAA IR checks, without an API seed |

The **purpose for all six remains metadata correction**, not a new research output. The four directly API-found datasets were already in REACH; Scout proposed additional award attribution.

## Verified revised totals

| Method (69 staged review proposals) | Count |
|---|---:|
| Found through independent research | **39** |
| Found in API results | **14** |
| Discovered by following API leads | **15** |
| Discovery method unknown | **1** |

Finding purpose remains **39 new-output reviews; 23 metadata corrections; 2 possible duplicates; 2 known duplicates; 3 needs investigation**. No public output additions or private human approvals can be inferred.

**Later provenance clarification:** Great Lakes cyclone DOI `10.1029/2024GL109890` is classified as **Discovered by following API leads**, supported by the October 28 15:30 ET DataCite mission report identifying it as a linked publication. Its exact seed DOI remains NOT VERIFIED, separately from the now-supported research method. This supersedes the earlier unknown-method status.

## Implementation and preservation

- **Only supplemental provenance and documentation were written**. All original 22 validated batches and their 69 rows remain unmodified.
- The GitHub Actions metrics generator, `scout-discoveries/tools/rebuild_discovery_rollup.py`, now overlays the six findings only after matching each immutable SHA-256 manifest entry, CSV row, run ID, title, and DOI/URL; otherwise metrics publication fails.
- The [rollup](../discovery-origin-rollup.json) now exposes `discovery_method_display_labels`, `effective_discovery_method_counts`, `effective_finding_purpose_counts`, and `metadata_correction_method_recovery`, with technical source fields retained for parsers.
- Tests were added to ensure a correction's method can be recovered without changing its purpose and that wrong hashes, low confidence, and duplicate ledger keys are rejected.
- The existing hourly Scout, first-day-of-month weekend Scout, and weekday morning briefing tasks now use the plain-language labels and retain their original schedules.
- **Private Discovery Hub Impact UI itself was not edited or independently inspected.** Public rollup fields and scheduled-report language are ready for the corresponding UI display mapping.

## Tool-level GitHub write incident

Previous GitHub connector write calls in the earlier session were blocked by a platform safety-check response. During this authorized follow-up, regular `create_file` and `update_file` GitHub operations succeeded and committed changes to main, and their content was re-fetched and verified. Therefore the earlier refusal is **not evidence of a persistent GitHub repository permission or branch protection problem**. The platform did not supply a specific underlying safety-rule explanation; its exact cause cannot be diagnosed from the available tools. Continue using small auditable commits, checking live blob SHA before updates and reading back each write. Do not try to bypass a future block.

**No paid GitHub AI worker, PR, manual manifest edit, immutable batch rewrite, Smartsheet change, or human approval was performed.**
