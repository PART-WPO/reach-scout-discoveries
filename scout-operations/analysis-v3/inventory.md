# Complete source inventory

VERIFIED_SOURCE: This inventory enumerates every file tracked at the pinned source commit. Analysis additions are excluded. Each file has a row in `inventory.csv`. Recommendations are INFERRED, not changes made.

INFERRED: Reader/writer lists use literal references and nearby source context. They are candidates for ownership review, not proof of execution. NOT_DETERMINED means no exact reader or writer could be established statically. Directory scans and computed paths can add dependencies; `code-io.json` preserves those operations.


## .github/workflows/build-monthly-api-manifest.yml

INFERRED: Purpose: Validate and Publish Monthly API Discovery Feed. Source: `.github/workflows/build-monthly-api-manifest.yml:1`.

INFERRED: CHANGE. Route writes through a reviewed branch and a shared scheduler.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/build-monthly-coverage.yml

INFERRED: Purpose: Build Scout monthly research coverage. Source: `.github/workflows/build-monthly-coverage.yml:1`.

INFERRED: CHANGE. Route writes through a reviewed branch and a shared scheduler.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/build-reach-comparison-cache.yml

INFERRED: Purpose: Build verified REACH comparison cache. Source: `.github/workflows/build-reach-comparison-cache.yml:1`.

INFERRED: CHANGE. Route writes through a reviewed branch and a shared scheduler.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/build-scout-discovery-manifest.yml

INFERRED: Purpose: Validate and Publish Scout Discovery Feed. Source: `.github/workflows/build-scout-discovery-manifest.yml:1`.

INFERRED: CHANGE. Route writes through a reviewed branch and a shared scheduler.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/datacite-date-reconciliation.yml

INFERRED: Purpose: DataCite date reconciliation - historical and monthly. Source: `.github/workflows/datacite-date-reconciliation.yml:1`.

INFERRED: CHANGE. Route writes through a reviewed branch and a shared scheduler.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/flash-drought-positive-control-preflight.yml

INFERRED: Purpose: Flash drought Crossref positive-control preflight. Source: `.github/workflows/flash-drought-positive-control-preflight.yml:1`.

INFERRED: CHANGE. Route writes through a reviewed branch and a shared scheduler.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/historical-crossref-actionable-routing.yml

INFERRED: Purpose: Historical Crossref actionable routing. Source: `.github/workflows/historical-crossref-actionable-routing.yml:1`.

INFERRED: CHANGE. Route writes through a reviewed branch and a shared scheduler.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/historical-crossref-backfill.yml

INFERRED: Purpose: REACH historical Crossref backfill (primary SPARK awards). Source: `.github/workflows/historical-crossref-backfill.yml:1`.

INFERRED: CHANGE. Route writes through a reviewed branch and a shared scheduler.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/historical-crossref-screening-coverage.yml

INFERRED: Purpose: Historical Crossref screening coverage. Source: `.github/workflows/historical-crossref-screening-coverage.yml:1`.

INFERRED: CHANGE. Route writes through a reviewed branch and a shared scheduler.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/historical-datacite-report.yml

INFERRED: Purpose: Historical DataCite - Excel comparison with Scout. Source: `.github/workflows/historical-datacite-report.yml:1`.

INFERRED: CHANGE. Route writes through a reviewed branch and a shared scheduler.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/noaa-ir-dataset-index.yml

INFERRED: Purpose: Refresh NOAA Institutional Repository DOI index for Scout. Source: `.github/workflows/noaa-ir-dataset-index.yml:1`.

INFERRED: CHANGE. Route writes through a reviewed branch and a shared scheduler.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/reach-api-checks.yml

INFERRED: Purpose: Validate DataCite and Crossref harvest logic. Source: `.github/workflows/reach-api-checks.yml:1`.

INFERRED: KEEP. Retain read-only checks; combine redundant invocations only after coverage review.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/reach-api-harvest.yml

INFERRED: Purpose: REACH API harvest - DataCite and Crossref. Source: `.github/workflows/reach-api-harvest.yml:1`.

INFERRED: CHANGE. Route writes through a reviewed branch and a shared scheduler.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/reach-api-smoke.yml

INFERRED: Purpose: REACH DataCite and Crossref live API smoke test. Source: `.github/workflows/reach-api-smoke.yml:1`.

INFERRED: KEEP. Retain read-only checks; combine redundant invocations only after coverage review.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/reach-historical-followup.yml

INFERRED: Purpose: Complete historical DataCite metadata and annotated awards. Source: `.github/workflows/reach-historical-followup.yml:1`.

INFERRED: CHANGE. Route writes through a reviewed branch and a shared scheduler.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/reconcile-historical-backlog.yml

INFERRED: Purpose: Reconcile historical DataCite Scout backlog. Source: `.github/workflows/reconcile-historical-backlog.yml:1`.

INFERRED: CHANGE. Route writes through a reviewed branch and a shared scheduler.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/reconcile-historical-crossref.yml

INFERRED: Purpose: Reconcile historical Crossref Scout research and expansion coverage. Source: `.github/workflows/reconcile-historical-crossref.yml:1`.

INFERRED: CHANGE. Route writes through a reviewed branch and a shared scheduler.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/scout-bounded-expansion-fallback.yml

INFERRED: Purpose: Scout bounded verified-REACH expansion research. Source: `.github/workflows/scout-bounded-expansion-fallback.yml:1`.

INFERRED: CHANGE. Route writes through a reviewed branch and a shared scheduler.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/scout-chatgpt-hourly-measurement.yml

INFERRED: Purpose: Scout ChatGPT hourly mission measurement reconciliation. Source: `.github/workflows/scout-chatgpt-hourly-measurement.yml:1`.

INFERRED: CHANGE. Route writes through a reviewed branch and a shared scheduler.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/scout-crosslane-research-memory.yml

INFERRED: Purpose: Scout cross-lane research memory and expansion checkpoint. Source: `.github/workflows/scout-crosslane-research-memory.yml:1`.

INFERRED: CHANGE. Route writes through a reviewed branch and a shared scheduler.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/scout-crossref-candidate-queue.yml

INFERRED: Purpose: Scout Crossref candidate queue refresh. Source: `.github/workflows/scout-crossref-candidate-queue.yml:1`.

INFERRED: CHANGE. Route writes through a reviewed branch and a shared scheduler.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/scout-decision-pipeline.yml

INFERRED: Purpose: Scout decision pipeline validation. Source: `.github/workflows/scout-decision-pipeline.yml:1`.

INFERRED: CHANGE. Route writes through a reviewed branch and a shared scheduler.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/scout-doi-metadata-checkpoint.yml

INFERRED: Purpose: REACH Scout direct DOI metadata checkpoint. Source: `.github/workflows/scout-doi-metadata-checkpoint.yml:1`.

INFERRED: CHANGE. Route writes through a reviewed branch and a shared scheduler.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/scout-evidence-action-pilot.yml

INFERRED: Purpose: Scout evidence evaluator and decision compiler pilot. Source: `.github/workflows/scout-evidence-action-pilot.yml:1`.

INFERRED: CHANGE. Route writes through a reviewed branch and a shared scheduler.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/scout-evidence-to-action-pilot.yml

INFERRED: Purpose: Scout evidence-to-action pilot (read-only). Source: `.github/workflows/scout-evidence-to-action-pilot.yml:1`.

INFERRED: KEEP. Retain read-only checks; combine redundant invocations only after coverage review.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/scout-five-case-replay.yml

INFERRED: Purpose: Scout five real-case end-to-end replay. Source: `.github/workflows/scout-five-case-replay.yml:1`.

INFERRED: CHANGE. Route writes through a reviewed branch and a shared scheduler.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/scout-github-code-metadata-checkpoint.yml

INFERRED: Purpose: REACH Scout GitHub code metadata checkpoint. Source: `.github/workflows/scout-github-code-metadata-checkpoint.yml:1`.

INFERRED: CHANGE. Route writes through a reviewed branch and a shared scheduler.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/scout-guarded-handoff-watchdog.yml

INFERRED: Purpose: Scout guarded handoff watchdog and recovery. Source: `.github/workflows/scout-guarded-handoff-watchdog.yml:1`.

INFERRED: KEEP. Retain read-only checks; combine redundant invocations only after coverage review.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/scout-hourly-guarded-handoff.yml

INFERRED: Purpose: Scout hourly guarded DOI decision handoff. Source: `.github/workflows/scout-hourly-guarded-handoff.yml:1`.

INFERRED: CHANGE. Route writes through a reviewed branch and a shared scheduler.

INFERRED: Readers/callers: scout-operations/tools/guarded_handoff_watchdog.py:15. Writers/producers: .github/workflows/scout-guarded-handoff-watchdog.yml:49. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/scout-human-project-referrals.yml

INFERRED: Purpose: Scout bounded human project referrals. Source: `.github/workflows/scout-human-project-referrals.yml:1`.

INFERRED: CHANGE. Route writes through a reviewed branch and a shared scheduler.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/scout-incremental-project-discovery.yml

INFERRED: Purpose: Scout Crossref indexed-updates and SPARK project leads. Source: `.github/workflows/scout-incremental-project-discovery.yml:1`.

INFERRED: CHANGE. Route writes through a reviewed branch and a shared scheduler.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/scout-independent-doi-lookup.yml

INFERRED: Purpose: REACH Scout independent DOI lookup. Source: `.github/workflows/scout-independent-doi-lookup.yml:1`.

INFERRED: CHANGE. Route writes through a reviewed branch and a shared scheduler.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/scout-independent-metadata-lookup.yml

INFERRED: Purpose: REACH Scout independent metadata lookup. Source: `.github/workflows/scout-independent-metadata-lookup.yml:1`.

INFERRED: CHANGE. Route writes through a reviewed branch and a shared scheduler.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/scout-one-output-full-dryrun.yml

INFERRED: Purpose: Scout one-output full-screening dry run. Source: `.github/workflows/scout-one-output-full-dryrun.yml:1`.

INFERRED: KEEP. Retain read-only checks; combine redundant invocations only after coverage review.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/scout-preprint-identity-reconciliation.yml

INFERRED: Purpose: Scout targeted published preprint identity reconciliation. Source: `.github/workflows/scout-preprint-identity-reconciliation.yml:1`.

INFERRED: CHANGE. Route writes through a reviewed branch and a shared scheduler.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/scout-preprint-retirement.yml

INFERRED: Purpose: Scout retire REACH-confirmed preprint families. Source: `.github/workflows/scout-preprint-retirement.yml:1`.

INFERRED: CHANGE. Route writes through a reviewed branch and a shared scheduler.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/scout-preprint-watchlist.yml

INFERRED: Purpose: REACH Scout first-of-month preprint watchlist. Source: `.github/workflows/scout-preprint-watchlist.yml:1`.

INFERRED: CHANGE. Route writes through a reviewed branch and a shared scheduler.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/scout-public-reach-author-pilot.yml

INFERRED: Purpose: Scout public REACH author-seed pilot (manual, read only). Source: `.github/workflows/scout-public-reach-author-pilot.yml:1`.

INFERRED: KEEP. Retain read-only checks; combine redundant invocations only after coverage review.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/scout-queued-doi-recovery.yml

INFERRED: Purpose: Scout recover DOI metadata after research access failures. Source: `.github/workflows/scout-queued-doi-recovery.yml:1`.

INFERRED: CHANGE. Route writes through a reviewed branch and a shared scheduler.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/scout-reach-artifact-url-regression.yml

INFERRED: Purpose: Scout same-mission REACH artifact URL verification. Source: `.github/workflows/scout-reach-artifact-url-regression.yml:1`.

INFERRED: KEEP. Retain read-only checks; combine redundant invocations only after coverage review.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/scout-reconciliation-repair-worklist.yml

INFERRED: Purpose: Scout evidence-repair worklist. Source: `.github/workflows/scout-reconciliation-repair-worklist.yml:1`.

INFERRED: CHANGE. Route writes through a reviewed branch and a shared scheduler.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/scout-research-decision-closeout.yml

INFERRED: Purpose: Scout evidence-to-decision closeout. Source: `.github/workflows/scout-research-decision-closeout.yml:1`.

INFERRED: CHANGE. Route writes through a reviewed branch and a shared scheduler.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/scout-research-outcomes.yml

INFERRED: Purpose: Scout all-lane research outcome registry. Source: `.github/workflows/scout-research-outcomes.yml:1`.

INFERRED: CHANGE. Route writes through a reviewed branch and a shared scheduler.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/scout-reviewer-feedback.yml

INFERRED: Purpose: Enforce private Discovery Hub reviewer-feedback boundary. Source: `.github/workflows/scout-reviewer-feedback.yml:1`.

INFERRED: KEEP. Retain read-only checks; combine redundant invocations only after coverage review.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/scout-throughput-scorecard.yml

INFERRED: Purpose: Scout evidence-based throughput scorecard. Source: `.github/workflows/scout-throughput-scorecard.yml:1`.

INFERRED: CHANGE. Route writes through a reviewed branch and a shared scheduler.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/scout-unified-source-preflight.yml

INFERRED: Purpose: Scout unified discovery preflight. Source: `.github/workflows/scout-unified-source-preflight.yml:1`.

INFERRED: CHANGE. Route writes through a reviewed branch and a shared scheduler.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/scout-v2-impact-report.yml

INFERRED: Purpose: Scout 2.0 verified impact and independent evaluation. Source: `.github/workflows/scout-v2-impact-report.yml:1`.

INFERRED: CHANGE. Route writes through a reviewed branch and a shared scheduler.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/select-scout-workstream.yml

INFERRED: Purpose: Verify Scout API-to-historical workstream switching. Source: `.github/workflows/select-scout-workstream.yml:1`.

INFERRED: CHANGE. Route writes through a reviewed branch and a shared scheduler.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/validate-crossref-actionable-routing.yml

INFERRED: Purpose: Validate actionable Crossref dedup routing. Source: `.github/workflows/validate-crossref-actionable-routing.yml:1`.

INFERRED: KEEP. Retain read-only checks; combine redundant invocations only after coverage review.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/validate-expansion-relevance.yml

INFERRED: Purpose: Validate Scout 2.0 expansion relevance. Source: `.github/workflows/validate-expansion-relevance.yml:1`.

INFERRED: KEEP. Retain read-only checks; combine redundant invocations only after coverage review.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/validate-metadata-blockers.yml

INFERRED: Purpose: Validate Scout metadata blocker ledger. Source: `.github/workflows/validate-metadata-blockers.yml:1`.

INFERRED: KEEP. Retain read-only checks; combine redundant invocations only after coverage review.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/validate-monthly-shared-identity.yml

INFERRED: Purpose: Validate monthly shared identity preflight. Source: `.github/workflows/validate-monthly-shared-identity.yml:1`.

INFERRED: KEEP. Retain read-only checks; combine redundant invocations only after coverage review.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/validate-research-decision-reconciliation.yml

INFERRED: Purpose: Validate Scout research closeout and reconciliation. Source: `.github/workflows/validate-research-decision-reconciliation.yml:1`.

INFERRED: KEEP. Retain read-only checks; combine redundant invocations only after coverage review.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/validate-scout-author-safeguards.yml

INFERRED: Purpose: Validate Scout author-identity and evidence safeguards. Source: `.github/workflows/validate-scout-author-safeguards.yml:1`.

INFERRED: KEEP. Retain read-only checks; combine redundant invocations only after coverage review.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/validate-scout-crossmode.yml

INFERRED: Purpose: Validate Scout cross-mode disposition and REACH-only author pilot. Source: `.github/workflows/validate-scout-crossmode.yml:1`.

INFERRED: KEEP. Retain read-only checks; combine redundant invocations only after coverage review.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/validate-scout-downstream.yml

INFERRED: Purpose: Verify Scout downstream read-only boundary. Source: `.github/workflows/validate-scout-downstream.yml:1`.

INFERRED: KEEP. Retain read-only checks; combine redundant invocations only after coverage review.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/validate-scout-public-privacy.yml

INFERRED: Purpose: Verify Scout public metadata privacy gate. Source: `.github/workflows/validate-scout-public-privacy.yml:1`.

INFERRED: KEEP. Retain read-only checks; combine redundant invocations only after coverage review.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/validate-scout-research-memory.yml

INFERRED: Purpose: Validate Scout persistent metadata and research memory (read only). Source: `.github/workflows/validate-scout-research-memory.yml:1`.

INFERRED: KEEP. Retain read-only checks; combine redundant invocations only after coverage review.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## .github/workflows/validate-scout-shared-identity.yml

INFERRED: Purpose: Validate Scout shared identity and disposition (read only). Source: `.github/workflows/validate-scout-shared-identity.yml:1`.

INFERRED: KEEP. Retain read-only checks; combine redundant invocations only after coverage review.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## api-discoveries/tests/test_export_xlsx.py

INFERRED: Purpose: Checks export xlsx. Source: `api-discoveries/tests/test_export_xlsx.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## api-discoveries/tests/test_harvest.py

INFERRED: Purpose: Checks harvest. Source: `api-discoveries/tests/test_harvest.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## api-discoveries/tests/test_reconcile_datacite_dates.py

INFERRED: Purpose: Local, network-free tests for DataCite date evidence classification.. Source: `api-discoveries/tests/test_reconcile_datacite_dates.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/datacite-date-reconciliation.yml:39. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## api-discoveries/tools/build_manifest.py

INFERRED: Purpose: Build public, append-only monthly API intake manifest for Discovery Hub.. Source: `api-discoveries/tools/build_manifest.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/build-monthly-api-manifest.yml:28. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## api-discoveries/tools/export_comparison_xlsx.py

INFERRED: Purpose: Produce review-only, comparison-friendly .xlsx from validated monthly API shards.. Source: `api-discoveries/tools/export_comparison_xlsx.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/reach-api-harvest.yml:141. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## api-discoveries/tools/export_historical_comparison_xlsx.py

INFERRED: Purpose: Read-only historical DataCite vs Scout Excel comparison; no ingestion or approvals.. Source: `api-discoveries/tools/export_historical_comparison_xlsx.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## api-discoveries/tools/harvest.py

INFERRED: Purpose: SPARK -> DataCite / Crossref public API discovery. No Sheets, no approvals. Outputs per-shard JSON for GitHub Actions aggregation; an API error is not zero results.. Source: `api-discoveries/tools/harvest.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: scout-operations/tests/test_crossref_metadata_checkpoint.py:15. Writers/producers: .github/workflows/reach-api-harvest.yml:73. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## api-discoveries/tools/historical_crossref.py

INFERRED: Purpose: Historical Crossref primary-SPARK-award harvest, intentionally separate from monthly and DataCite.. Source: `api-discoveries/tools/historical_crossref.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: .github/workflows/historical-crossref-backfill.yml:31; .github/workflows/historical-crossref-backfill.yml:62. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## api-discoveries/tools/historical_followup.py

INFERRED: Purpose: Complete two annotated SPARK identifiers and enrich historical DataCite date facts. Does not modify original immutable research batches or human review decisions.. Source: `api-discoveries/tools/historical_followup.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/reach-historical-followup.yml:24. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## api-discoveries/tools/incremental_crossref.py

INFERRED: Purpose: Monthly Crossref index-change + bounded SPARK project-context discovery.. Source: `api-discoveries/tools/incremental_crossref.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/scout-incremental-project-discovery.yml:46; .github/workflows/scout-incremental-project-discovery.yml:74; .github/workflows/scout-incremental-project-discovery.yml:76. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## api-discoveries/tools/publish_harvest.py

INFERRED: Purpose: Publish completed API harvest as immutable, UNREVIEWED Scout research inputs. Never send raw API results directly to the Discovery Hub or modify source systems.. Source: `api-discoveries/tools/publish_harvest.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/reach-api-harvest.yml:117; api-discoveries/tools/export_comparison_xlsx.py:303. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## api-discoveries/tools/reconcile_datacite_dates.py

INFERRED: Purpose: Read-only DataCite date audit for historical and monthly REACH Scout API intake.. Source: `api-discoveries/tools/reconcile_datacite_dates.py:1`.

INFERRED: MERGE. Unify overlapping scheduling/reporting responsibilities behind one ledger.

INFERRED: Readers/callers: .github/workflows/datacite-date-reconciliation.yml:44; api-discoveries/tests/test_reconcile_datacite_dates.py:9. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-discoveries/tools/build_manifest.py

INFERRED: Purpose: Validate append-only public Scout Discovery batches and build a manifest.. Source: `scout-discoveries/tools/build_manifest.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/build-scout-discovery-manifest.yml:107; .github/workflows/scout-hourly-guarded-handoff.yml:146; .github/workflows/validate-scout-public-privacy.yml:25. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-discoveries/tools/noaa_ir_lookup.py

INFERRED: Purpose: Offline, evidence-only NOAA Institutional Repository DOI check for NEW Scout drafts.. Source: `scout-discoveries/tools/noaa_ir_lookup.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-discoveries/tools/prepare_batch.py

INFERRED: Purpose: Build/preflight 24-column Scout candidates BEFORE GitHub publication.. Source: `scout-discoveries/tools/prepare_batch.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: .github/workflows/flash-drought-positive-control-preflight.yml:67; .github/workflows/flash-drought-positive-control-preflight.yml:70. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-discoveries/tools/promote_inbox.py

INFERRED: Purpose: Promote validated, immutable Scout inbox drafts into the published batch folder.. Source: `scout-discoveries/tools/promote_inbox.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/build-scout-discovery-manifest.yml:94; .github/workflows/build-scout-discovery-manifest.yml:96; .github/workflows/build-scout-discovery-manifest.yml:98; .github/workflows/scout-hourly-guarded-handoff.yml:145. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-discoveries/tools/public_privacy.py

INFERRED: Purpose: Fail-closed privacy gate for PUBLIC REACH Scout output metadata.. Source: `scout-discoveries/tools/public_privacy.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-discoveries/tools/rebuild_discovery_rollup.py

INFERRED: Purpose: Reconcile Scout discovery-origin metrics from verified manifest CSV bytes.. Source: `scout-discoveries/tools/rebuild_discovery_rollup.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/build-scout-discovery-manifest.yml:112. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-discoveries/tools/supersessions.py

INFERRED: Purpose: Read a JSON-defined Scout batch replacement with audit history.. Source: `scout-discoveries/tools/supersessions.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-discoveries/tools/tests/test_monthly_recovery_gate.py

INFERRED: Purpose: Offline critical-metadata first tests for monthly fast intake.. Source: `scout-discoveries/tools/tests/test_monthly_recovery_gate.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-discoveries/tools/tests/test_noaa_ir_lookup.py

INFERRED: Purpose: NOAA IR metadata enrichment cannot invent FALSE or touch existing output reviews.. Source: `scout-discoveries/tools/tests/test_noaa_ir_lookup.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/flash-drought-positive-control-preflight.yml:56; .github/workflows/noaa-ir-dataset-index.yml:32. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-discoveries/tools/tests/test_pipeline.py

INFERRED: Purpose: Offline tests for canonical Scout CSV preparation and attribution reconciliation.. Source: `scout-discoveries/tools/tests/test_pipeline.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-discoveries/tools/tests/test_public_privacy.py

INFERRED: Purpose: Privacy checks for Scout's public discovery-feed boundary.. Source: `scout-discoveries/tools/tests/test_public_privacy.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/validate-scout-public-privacy.yml:23. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-discoveries/tools/tests/test_referral_promotion.py

INFERRED: Purpose: Sourced human referral promotion never consumes unrelated stale inbox drafts.. Source: `scout-discoveries/tools/tests/test_referral_promotion.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-discoveries/tools/tests/test_wpo_confirmation_supersession.py

INFERRED: Purpose: Regression: one immutable 4:24 Scout review unit receives a validated 459 correction.. Source: `scout-discoveries/tools/tests/test_wpo_confirmation_supersession.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/historical-crossref-screening/build_actionable_routing.py

INFERRED: Purpose: Actionable, read-only Crossref-to-REACH gate; never mutates source checkpoints.. Source: `scout-operations/historical-crossref-screening/build_actionable_routing.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/historical-crossref-actionable-routing.yml:67; .github/workflows/scout-decision-pipeline.yml:43; .github/workflows/validate-crossref-actionable-routing.yml:24; .github/workflows/validate-crossref-actionable-routing.yml:27; .github/workflows/validate-research-decision-reconciliation.yml:52. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/historical-crossref-screening/build_coverage.py

INFERRED: Purpose: Validate small Crossref screening batches and generate reproducible coverage.. Source: `scout-operations/historical-crossref-screening/build_coverage.py:1`.

INFERRED: MERGE. Unify overlapping scheduling/reporting responsibilities behind one ledger.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: .github/workflows/historical-crossref-screening-coverage.yml:38. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/reach-comparison-cache/build_cache.py

INFERRED: Purpose: Build a checksum-verified, compact public REACH comparison cache.. Source: `scout-operations/reach-comparison-cache/build_cache.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/build-reach-comparison-cache.yml:37; .github/workflows/scout-reach-artifact-url-regression.yml:26. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_bulk_reach_dedup.py

INFERRED: Purpose: Deterministic bulk duplicate gate: fast-path only uniquely verified identities.. Source: `scout-operations/tests/test_bulk_reach_dedup.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/historical-crossref-actionable-routing.yml:64; .github/workflows/validate-crossref-actionable-routing.yml:25; .github/workflows/validate-scout-shared-identity.yml:34. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_cache_attestation.py

INFERRED: Purpose: Cache SHA/freshness regression: no source failures may imply novelty.. Source: `scout-operations/tests/test_cache_attestation.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/scout-reach-artifact-url-regression.yml:28. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_candidate_queue.py

INFERRED: Purpose: Checks candidate queue. Source: `scout-operations/tests/test_candidate_queue.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/scout-crossref-candidate-queue.yml:54; .github/workflows/scout-one-output-full-dryrun.yml:21. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_compile_research_evidence.py

INFERRED: Purpose: Multi-case Scout overnight evidence must retain each original DOI independently.. Source: `scout-operations/tests/test_compile_research_evidence.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_crosslane_research_memory.py

INFERRED: Purpose: Source-verified historical discovery graph never collapses distinct expansion.. Source: `scout-operations/tests/test_crosslane_research_memory.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/scout-crosslane-research-memory.yml:67. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_crossref_metadata_checkpoint.py

INFERRED: Purpose: Offline regression tests: WPO prefers Crossref print, online fallback, month -> day 01.. Source: `scout-operations/tests/test_crossref_metadata_checkpoint.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/scout-doi-metadata-checkpoint.yml:47. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_decision_pipeline.py

INFERRED: Purpose: Deterministic regression tests for the read-only Scout decision pipeline.. Source: `scout-operations/tests/test_decision_pipeline.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/scout-decision-pipeline.yml:40; .github/workflows/scout-queued-doi-recovery.yml:42; .github/workflows/scout-research-decision-closeout.yml:61; .github/workflows/scout-unified-source-preflight.yml:47; .github/workflows/validate-research-decision-reconciliation.yml:33; .github/workflows/validate-scout-crossmode.yml:41; .github/workflows/validate-scout-shared-identity.yml:32. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_discovery_metrics_reconciliation.py

INFERRED: Purpose: Offline regression tests for separated Scout discovery throughput and origins.. Source: `scout-operations/tests/test_discovery_metrics_reconciliation.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/scout-bounded-expansion-fallback.yml:65; .github/workflows/scout-hourly-guarded-handoff.yml:69. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_evidence_action_pilot.py

INFERRED: Purpose: Evidence-to-action pilot: deterministic, safe, source-pinned, bounded.. Source: `scout-operations/tests/test_evidence_action_pilot.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/scout-evidence-action-pilot.yml:35. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_evidence_to_action_pilot.py

INFERRED: Purpose: Safety and decision semantics of the read-only evidence-to-action pilot.. Source: `scout-operations/tests/test_evidence_to_action_pilot.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/scout-evidence-to-action-pilot.yml:27. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_expansion_fallback_research.py

INFERRED: Purpose: Offline bounded expansion work: rotate and record real external lookups, never claim staging.. Source: `scout-operations/tests/test_expansion_fallback_research.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/scout-bounded-expansion-fallback.yml:61. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_expansion_relevance.py

INFERRED: Purpose: Scout 2.0 project relevance is a reversible research priority, never an approval.. Source: `scout-operations/tests/test_expansion_relevance.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/historical-crossref-actionable-routing.yml:66; .github/workflows/scout-v2-impact-report.yml:68; .github/workflows/validate-expansion-relevance.yml:28. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_five_case_replay.py

INFERRED: Purpose: Exercise real Scout decisions for five known research pathways, with zero writes.. Source: `scout-operations/tests/test_five_case_replay.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/scout-five-case-replay.yml:34. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_guarded_handoff_watchdog.py

INFERRED: Purpose: Offline regression tests for missing-run recovery, status and weekday gating.. Source: `scout-operations/tests/test_guarded_handoff_watchdog.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/scout-guarded-handoff-watchdog.yml:12; .github/workflows/scout-guarded-handoff-watchdog.yml:43. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_historical_crossref.py

INFERRED: Purpose: Regression tests for historical Crossref as a non-duplicating seed cohort.. Source: `scout-operations/tests/test_historical_crossref.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_historical_crossref_title_normalization.py

INFERRED: Purpose: Regression: inline XML/HTML in publisher titles cannot hide existing REACH outputs.. Source: `scout-operations/tests/test_historical_crossref_title_normalization.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/historical-crossref-actionable-routing.yml:63. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_hourly_decision_handoff.py

INFERRED: Purpose: Offline regression tests for GitHub-owned verified original handoff and cooldown.. Source: `scout-operations/tests/test_hourly_decision_handoff.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/scout-hourly-guarded-handoff.yml:65. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_hourly_mission_metrics.py

INFERRED: Purpose: Offline tests: record only actual completed public backstop outcomes.. Source: `scout-operations/tests/test_hourly_mission_metrics.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/scout-chatgpt-hourly-measurement.yml:39; .github/workflows/scout-hourly-guarded-handoff.yml:75. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_hourly_mission_scorecard.py

INFERRED: Purpose: Scorecard counts only verifiable per-run records, with producers separated.. Source: `scout-operations/tests/test_hourly_mission_scorecard.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/scout-chatgpt-hourly-measurement.yml:38; .github/workflows/scout-hourly-guarded-handoff.yml:79. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_human_project_referrals.py

INFERRED: Purpose: Checks human project referrals. Source: `scout-operations/tests/test_human_project_referrals.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/scout-hourly-guarded-handoff.yml:81; .github/workflows/scout-human-project-referrals.yml:48; .github/workflows/scout-one-output-full-dryrun.yml:22. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_identity_disposition.py

INFERRED: Purpose: Read-only cross-mode identity and author-source privacy regressions.. Source: `scout-operations/tests/test_identity_disposition.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/scout-decision-pipeline.yml:41; .github/workflows/scout-public-reach-author-pilot.yml:29; .github/workflows/validate-scout-author-safeguards.yml:27; .github/workflows/validate-scout-crossmode.yml:41; .github/workflows/validate-scout-research-memory.yml:31; .github/workflows/validate-scout-shared-identity.yml:33. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_incremental_crossref_discovery.py

INFERRED: Purpose: API update discovery is a research lead, never a direct review proposal.. Source: `scout-operations/tests/test_incremental_crossref_discovery.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/scout-incremental-project-discovery.yml:47. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_independent_hourly_recovery.py

INFERRED: Purpose: Regression: avoid repeating a staged DataCite DOI or wasting a mission on API failure.. Source: `scout-operations/tests/test_independent_hourly_recovery.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/scout-crosslane-research-memory.yml:66. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_independent_lookup_audit.py

INFERRED: Purpose: Exercise real vs cached provider attempts and stale snapshot safety.. Source: `scout-operations/tests/test_independent_lookup_audit.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/scout-hourly-guarded-handoff.yml:77. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_ir_reach_identity.py

INFERRED: Purpose: Regression tests for independent DOI and historical NOAA IR→REACH duplicate gate.. Source: `scout-operations/tests/test_ir_reach_identity.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/scout-decision-pipeline.yml:42; .github/workflows/validate-scout-crossmode.yml:41. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_mission_activity_log.py

INFERRED: Purpose: Checks mission activity log. Source: `scout-operations/tests/test_mission_activity_log.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/scout-throughput-scorecard.yml:45. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_monthly_decision_queue.py

INFERRED: Purpose: Regression tests for Scout monthly original fast path and separate expansion.. Source: `scout-operations/tests/test_monthly_decision_queue.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_noaa_ir_index.py

INFERRED: Purpose: NOAA Central Library indexer is complete, DOI-exact and checksum-verified.. Source: `scout-operations/tests/test_noaa_ir_index.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/noaa-ir-dataset-index.yml:31. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_preprint_retirements.py

INFERRED: Purpose: Checks preprint retirements. Source: `scout-operations/tests/test_preprint_retirements.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/scout-preprint-retirement.yml:25; .github/workflows/scout-preprint-watchlist.yml:32. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_preprint_watchlist.py

INFERRED: Purpose: Checks preprint watchlist. Source: `scout-operations/tests/test_preprint_watchlist.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/scout-preprint-watchlist.yml:30. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_private_benchmark_labels.py

INFERRED: Purpose: Blinded 100-case benchmark labels never become a public GitHub file.. Source: `scout-operations/tests/test_private_benchmark_labels.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/validate-scout-crossmode.yml:41. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_public_handoff_reconciliation.py

INFERRED: Purpose: Two real DOI regressions: retired REACH preprint and already-staged Scout article.. Source: `scout-operations/tests/test_public_handoff_reconciliation.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/scout-hourly-guarded-handoff.yml:67. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_quick_monthly_intake.py

INFERRED: Purpose: Fast monthly DOI intake regression checks. No private Hub is contacted.. Source: `scout-operations/tests/test_quick_monthly_intake.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/scout-decision-pipeline.yml:44; .github/workflows/validate-scout-crossmode.yml:41. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_reach_author_pilot.py

INFERRED: Purpose: Public REACH publication-anchored author exploration remains PII-safe.. Source: `scout-operations/tests/test_reach_author_pilot.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/scout-public-reach-author-pilot.yml:28; .github/workflows/validate-scout-author-safeguards.yml:26; .github/workflows/validate-scout-crossmode.yml:41. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_reach_version_identity.py

INFERRED: Purpose: Regression controls for REACH same-work preprint/final DOI identities.. Source: `scout-operations/tests/test_reach_version_identity.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/build-scout-discovery-manifest.yml:62; .github/workflows/build-scout-discovery-manifest.yml:82. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_reconcile_derived_reporting.py

INFERRED: Purpose: Offline issue #35 invariants: source freshness, chronology, privacy, safety.. Source: `scout-operations/tests/test_reconcile_derived_reporting.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/scout-research-decision-closeout.yml:60; .github/workflows/validate-research-decision-reconciliation.yml:34. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_reconciliation_repair_worklist.py

INFERRED: Purpose: Checks reconciliation repair worklist. Source: `scout-operations/tests/test_reconciliation_repair_worklist.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/scout-reconciliation-repair-worklist.yml:35. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_recover_queued_doi_metadata.py

INFERRED: Purpose: Checks recover queued doi metadata. Source: `scout-operations/tests/test_recover_queued_doi_metadata.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/scout-queued-doi-recovery.yml:40; .github/workflows/validate-scout-research-memory.yml:30. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_recover_related_output_source.py

INFERRED: Purpose: Offline provider fallback regression: no guesswork, no candidate/handoff.. Source: `scout-operations/tests/test_recover_related_output_source.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/scout-bounded-expansion-fallback.yml:62. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_related_output_identity.py

INFERRED: Purpose: Offline regression cases for complete live REACH plus public Scout identity.. Source: `scout-operations/tests/test_related_output_identity.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/scout-bounded-expansion-fallback.yml:63. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_replay_author_safeguards.py

INFERRED: Purpose: Safeguard regression tests: disambiguation, topic, award, and no SPARK.. Source: `scout-operations/tests/test_replay_author_safeguards.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/validate-scout-author-safeguards.yml:25. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_research_memory.py

INFERRED: Purpose: Source-sha-pinned DOI metadata reuse without any new author-name index.. Source: `scout-operations/tests/test_research_memory.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/validate-scout-research-memory.yml:29. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_research_outcome_registry.py

INFERRED: Purpose: Every source-backed research note gets a nonterminal operational disposition.. Source: `scout-operations/tests/test_research_outcome_registry.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/scout-crosslane-research-memory.yml:69; .github/workflows/scout-evidence-action-pilot.yml:36; .github/workflows/scout-human-project-referrals.yml:49; .github/workflows/scout-research-outcomes.yml:36. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_scout_v2_impact.py

INFERRED: Purpose: Scout 2.0 stage metrics and representative blinded evaluation checks.. Source: `scout-operations/tests/test_scout_v2_impact.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/scout-v2-impact-report.yml:67. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_select_workstream.py

INFERRED: Purpose: Checks select workstream. Source: `scout-operations/tests/test_select_workstream.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/historical-crossref-actionable-routing.yml:65; .github/workflows/validate-crossref-actionable-routing.yml:26; .github/workflows/validate-expansion-relevance.yml:29. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_source_driven_expansion.py

INFERRED: Purpose: Offline positive control: source-backed dataset DOI, not generic reference scraping.. Source: `scout-operations/tests/test_source_driven_expansion.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/scout-bounded-expansion-fallback.yml:64. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_structured_evidence_extraction.py

INFERRED: Purpose: Existing-note extraction must preserve source scope, attribution, and privacy.. Source: `scout-operations/tests/test_structured_evidence_extraction.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/scout-evidence-to-action-pilot.yml:28. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_sync_monthly_intake.py

INFERRED: Purpose: Offline regression checks for recurring monthly Scout ledger intake.. Source: `scout-operations/tests/test_sync_monthly_intake.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_unified_source_preflight.py

INFERRED: Purpose: Unifying public identity decisions may not fabricate output eligibility.. Source: `scout-operations/tests/test_unified_source_preflight.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/scout-crosslane-research-memory.yml:68; .github/workflows/scout-evidence-action-pilot.yml:37; .github/workflows/scout-incremental-project-discovery.yml:48; .github/workflows/scout-unified-source-preflight.yml:46; .github/workflows/scout-v2-impact-report.yml:69; .github/workflows/validate-scout-crossmode.yml:41. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_universal_preprint_gate.py

INFERRED: Purpose: Every discovery origin is subjected to the same preprint review gate.. Source: `scout-operations/tests/test_universal_preprint_gate.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/build-scout-discovery-manifest.yml:63; .github/workflows/build-scout-discovery-manifest.yml:81. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_validate_reviewer_feedback.py

INFERRED: Purpose: Checks validate reviewer feedback. Source: `scout-operations/tests/test_validate_reviewer_feedback.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/scout-reviewer-feedback.yml:38. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_verify_reach_artifact_url.py

INFERRED: Purpose: Regression: the exact objective_thresholds code URL is already in REACH.. Source: `scout-operations/tests/test_verify_reach_artifact_url.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: .github/workflows/scout-reach-artifact-url-regression.yml:30. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tests/test_wpo_awards.py

INFERRED: Purpose: Checks wpo awards. Source: `scout-operations/tests/test_wpo_awards.py:1`.

INFERRED: KEEP. Retain behavior checks during migration; review duplicates only after replacement passes.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/audit_doi_metadata.py

INFERRED: Purpose: Read-only DOI metadata enrichment across historical, staged and Scout leads.. Source: `scout-operations/tools/audit_doi_metadata.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/scout-doi-metadata-checkpoint.yml:46; .github/workflows/scout-doi-metadata-checkpoint.yml:55; scout-operations/tests/test_crossref_metadata_checkpoint.py:14. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/audit_github_code_metadata.py

INFERRED: Purpose: Read-only GitHub API enrichment of public Scout software research leads.. Source: `scout-operations/tools/audit_github_code_metadata.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/audit_independent_lookup.py

INFERRED: Purpose: Audit genuine prior-metadata reuse in an executed independent lookup report.. Source: `scout-operations/tools/audit_independent_lookup.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/build_candidate_queue.py

INFERRED: Purpose: Read-only deterministic Crossref original triage; no research/approval claims.. Source: `scout-operations/tools/build_candidate_queue.py:1`.

INFERRED: MERGE. Unify overlapping scheduling/reporting responsibilities behind one ledger.

INFERRED: Readers/callers: .github/workflows/scout-crossref-candidate-queue.yml:53; .github/workflows/scout-crossref-candidate-queue.yml:65; .github/workflows/scout-crossref-candidate-queue.yml:66; .github/workflows/scout-hourly-guarded-handoff.yml:130; .github/workflows/scout-hourly-guarded-handoff.yml:155; .github/workflows/scout-hourly-guarded-handoff.yml:156; scout-operations/tests/test_candidate_queue.py:5. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/build_coverage.py

INFERRED: Purpose: build coverage. Source: `scout-operations/tools/build_coverage.py:1`.

INFERRED: MERGE. Unify overlapping scheduling/reporting responsibilities behind one ledger.

INFERRED: Readers/callers: .github/workflows/build-scout-discovery-manifest.yml:117; api-discoveries/tools/publish_harvest.py:205. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/build_crosslane_research_memory.py

INFERRED: Purpose: SHA-pinned, nonterminal Scout cross-lane research relationship memory.. Source: `scout-operations/tools/build_crosslane_research_memory.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/scout-crosslane-research-memory.yml:64; .github/workflows/scout-crosslane-research-memory.yml:73; .github/workflows/scout-crosslane-research-memory.yml:74. Writers/producers: .github/workflows/scout-crosslane-research-memory.yml:132; .github/workflows/scout-crosslane-research-memory.yml:133. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/build_expansion_relevance.py

INFERRED: Purpose: Scout 2.0: evidence-only relevance gate for *research expansion*, not approvals.. Source: `scout-operations/tools/build_expansion_relevance.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/historical-crossref-actionable-routing.yml:68; .github/workflows/validate-crossref-actionable-routing.yml:28; .github/workflows/validate-expansion-relevance.yml:27; .github/workflows/validate-expansion-relevance.yml:35; .github/workflows/validate-research-decision-reconciliation.yml:53. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/build_human_project_referrals.py

INFERRED: Purpose: Source-bound Scout referrals for new outputs or funding-scope investigation.. Source: `scout-operations/tools/build_human_project_referrals.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/scout-human-project-referrals.yml:62; scout-operations/tests/test_human_project_referrals.py:240. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/build_impact_report.py

INFERRED: Purpose: Concise SHA-linked Scout impact report with honestly separated pipeline stages.. Source: `scout-operations/tools/build_impact_report.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/scout-v2-impact-report.yml:66; .github/workflows/scout-v2-impact-report.yml:72; scout-operations/tests/test_reconcile_derived_reporting.py:106. Writers/producers: .github/workflows/scout-v2-impact-report.yml:105. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/build_mission_activity_log.py

INFERRED: Purpose: Append-only, evidence-pinned Scout mission activity observations.. Source: `scout-operations/tools/build_mission_activity_log.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: scout-operations/tests/test_mission_activity_log.py:4. Writers/producers: .github/workflows/scout-throughput-scorecard.yml:47. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/build_monthly_decision_queue.py

INFERRED: Purpose: Generate an actionable monthly original-output decision queue and independent API-seeded expansion worklist. Research recommendations only: no approvals, unverified Hub claims, terminal dispositions, or drafts are created here.. Source: `scout-operations/tools/build_monthly_decision_queue.py:1`.

INFERRED: MERGE. Unify overlapping scheduling/reporting responsibilities behind one ledger.

INFERRED: Readers/callers: .github/workflows/build-scout-discovery-manifest.yml:118. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/build_noaa_ir_index.py

INFERRED: Purpose: Create checksum-verified, minimized DOI -> NOAA IR item URL index.. Source: `scout-operations/tools/build_noaa_ir_index.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/noaa-ir-dataset-index.yml:36. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/build_operational_scorecard.py

INFERRED: Purpose: Authoritative Scout phase scorecard from validated public artifacts.. Source: `scout-operations/tools/build_operational_scorecard.py:1`.

INFERRED: MERGE. Unify overlapping scheduling/reporting responsibilities behind one ledger.

INFERRED: Readers/callers: .github/workflows/historical-crossref-actionable-routing.yml:69; .github/workflows/validate-crossref-actionable-routing.yml:29; .github/workflows/validate-expansion-relevance.yml:37; .github/workflows/validate-research-decision-reconciliation.yml:54. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/build_reconciliation_repair_worklist.py

INFERRED: Purpose: Produce source-backed work orders for unresolved historical terminal claims.. Source: `scout-operations/tools/build_reconciliation_repair_worklist.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/scout-reconciliation-repair-worklist.yml:36; .github/workflows/validate-research-decision-reconciliation.yml:43. Writers/producers: .github/workflows/scout-reconciliation-repair-worklist.yml:58. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/build_research_outcome_registry.py

INFERRED: Purpose: Turn public Scout research evidence into an operational, non-terminal queue.. Source: `scout-operations/tools/build_research_outcome_registry.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/scout-human-project-referrals.yml:61; .github/workflows/scout-research-outcomes.yml:37. Writers/producers: .github/workflows/scout-research-outcomes.yml:61. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/build_scout_v2_benchmark.py

INFERRED: Purpose: Deterministic, privacy-safe 100-case Scout evaluation sampling.. Source: `scout-operations/tools/build_scout_v2_benchmark.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/scout-v2-impact-report.yml:66; .github/workflows/scout-v2-impact-report.yml:73. Writers/producers: .github/workflows/scout-v2-impact-report.yml:106. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/build_throughput_scorecard.py

INFERRED: Purpose: Evidence-pinned Scout throughput scorecard; never equate routing with research.. Source: `scout-operations/tools/build_throughput_scorecard.py:1`.

INFERRED: MERGE. Unify overlapping scheduling/reporting responsibilities behind one ledger.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: .github/workflows/scout-throughput-scorecard.yml:46; .github/workflows/scout-throughput-scorecard.yml:48. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/bulk_reach_dedup.py

INFERRED: Purpose: Conservative, evidence-only bulk REACH identity decision for public DOI leads.. Source: `scout-operations/tools/bulk_reach_dedup.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/validate-crossref-actionable-routing.yml:24. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/cache_attestation.py

INFERRED: Purpose: Reusable, fail-closed verification of the SHA-pinned REACH comparison snapshot.. Source: `scout-operations/tools/cache_attestation.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/scout-reach-artifact-url-regression.yml:26. Writers/producers: .github/workflows/build-reach-comparison-cache.yml:41. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/compile_research_evidence.py

INFERRED: Purpose: Compile checked Crossref research notes into conservative, reproducible decision inputs.. Source: `scout-operations/tools/compile_research_evidence.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/validate-research-decision-reconciliation.yml:32; .github/workflows/validate-research-decision-reconciliation.yml:47. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/decision_pipeline.py

INFERRED: Purpose: Read-only DOI identity catalog and evidence-gated Scout case checkpoints.. Source: `scout-operations/tools/decision_pipeline.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/scout-decision-pipeline.yml:68; .github/workflows/scout-decision-pipeline.yml:69; .github/workflows/scout-decision-pipeline.yml:70; .github/workflows/scout-decision-pipeline.yml:71; .github/workflows/validate-research-decision-reconciliation.yml:46; .github/workflows/validate-research-decision-reconciliation.yml:48; .github/workflows/validate-scout-shared-identity.yml:31. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/discovery_origin_evidence.py

INFERRED: Purpose: Conservative, source-hash-verified first-path attribution for historical Crossref originals.. Source: `scout-operations/tools/discovery_origin_evidence.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/evaluate_research_to_action.py

INFERRED: Purpose: Read-only Evidence Evaluator + Decision Compiler pilot for Scout research.. Source: `scout-operations/tools/evaluate_research_to_action.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/scout-evidence-action-pilot.yml:34; .github/workflows/scout-evidence-action-pilot.yml:41; .github/workflows/scout-evidence-action-pilot.yml:42. Writers/producers: .github/workflows/scout-evidence-action-pilot.yml:74; .github/workflows/scout-evidence-action-pilot.yml:75. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/evidence_to_action_pilot.py

INFERRED: Purpose: Read-only, evidence-pinned Scout decision pilot. Never stages or closes research.. Source: `scout-operations/tools/evidence_to_action_pilot.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/scout-evidence-to-action-pilot.yml:33; .github/workflows/scout-evidence-to-action-pilot.yml:34. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/expansion_fallback_research.py

INFERRED: Purpose: One bounded, source-backed expansion investigation when monthly originals are clear.. Source: `scout-operations/tools/expansion_fallback_research.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/scout-bounded-expansion-fallback.yml:60; .github/workflows/scout-bounded-expansion-fallback.yml:116. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/extract_structured_research_evidence.py

INFERRED: Purpose: Conservative, source-SHA-pinned extraction from existing public Scout notes.. Source: `scout-operations/tools/extract_structured_research_evidence.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/scout-evidence-to-action-pilot.yml:31; .github/workflows/scout-evidence-to-action-pilot.yml:32. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/guarded_handoff_watchdog.py

INFERRED: Purpose: Independent heartbeat for the guarded GitHub Crossref handoff.. Source: `scout-operations/tools/guarded_handoff_watchdog.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/scout-guarded-handoff-watchdog.yml:42. Writers/producers: .github/workflows/scout-guarded-handoff-watchdog.yml:50. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/hourly_decision_handoff.py

INFERRED: Purpose: GitHub-hosted, source-verified Crossref original -> guarded Scout reviewer handoff.. Source: `scout-operations/tools/hourly_decision_handoff.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/scout-hourly-guarded-handoff.yml:63; .github/workflows/scout-hourly-guarded-handoff.yml:133; .github/workflows/scout-hourly-guarded-handoff.yml:148. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/identity_disposition.py

INFERRED: Purpose: One read-only public identity/disposition decision for all Scout entry paths.. Source: `scout-operations/tools/identity_disposition.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/validate-scout-shared-identity.yml:31; .github/workflows/validate-scout-shared-identity.yml:38. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/ir_reach_identity.py

INFERRED: Purpose: Evidence-only NOAA IR DOI to existing REACH URL identity fallback.. Source: `scout-operations/tools/ir_reach_identity.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/scout-decision-pipeline.yml:43. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/lookup_artifact_scope.py

INFERRED: Purpose: Read-only artifact file-scope inventory for DOI and tagged GitHub research leads.. Source: `scout-operations/tools/lookup_artifact_scope.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/lookup_independent_dois.py

INFERRED: Purpose: Fast independent DOI metadata lookups; no historical-feed dependencies.. Source: `scout-operations/tools/lookup_independent_dois.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/scout-crosslane-research-memory.yml:65; .github/workflows/scout-decision-pipeline.yml:43; .github/workflows/validate-scout-research-memory.yml:28. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/lookup_independent_metadata.py

INFERRED: Purpose: Unified independent research metadata: DOI registries and GitHub releases.. Source: `scout-operations/tools/lookup_independent_metadata.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/scout-crosslane-research-memory.yml:65; .github/workflows/scout-decision-pipeline.yml:43; .github/workflows/validate-scout-research-memory.yml:28. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/preprint_watchlist.py

INFERRED: Purpose: First-of-month, public-only preprint tracking. NEVER stages a Scout candidate.. Source: `scout-operations/tools/preprint_watchlist.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: .github/workflows/scout-preprint-watchlist.yml:42. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/quick_monthly_intake.py

INFERRED: Purpose: Rapid, risk-based monthly DOI-to-human-review intake.. Source: `scout-operations/tools/quick_monthly_intake.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/validate-monthly-shared-identity.yml:23. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/reach_author_pilot.py

INFERRED: Purpose: Optional, bounded public REACH publication -> Crossref author research pilot.. Source: `scout-operations/tools/reach_author_pilot.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: .github/workflows/scout-public-reach-author-pilot.yml:48. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/reach_version_identity.py

INFERRED: Purpose: Public-only, fail-closed identity gate for published versions of REACH preprints.. Source: `scout-operations/tools/reach_version_identity.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/reconcile_derived_reporting.py

INFERRED: Purpose: Issue #35: rebuild Scout's public-source-derived reports in dependency order.. Source: `scout-operations/tools/reconcile_derived_reporting.py:1`.

INFERRED: MERGE. Unify overlapping scheduling/reporting responsibilities behind one ledger.

INFERRED: Readers/callers: .github/workflows/scout-research-decision-closeout.yml:59; .github/workflows/scout-research-decision-closeout.yml:66; .github/workflows/scout-research-decision-closeout.yml:68; .github/workflows/scout-research-decision-closeout.yml:101; .github/workflows/scout-v2-impact-report.yml:62; .github/workflows/validate-expansion-relevance.yml:32; .github/workflows/validate-research-decision-reconciliation.yml:37; scout-operations/tools/reconcile_scout_metrics.py:126. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/reconcile_historical.py

INFERRED: Purpose: Reconcile every historical DataCite DOI into a persistent Scout research queue.. Source: `scout-operations/tools/reconcile_historical.py:1`.

INFERRED: MERGE. Unify overlapping scheduling/reporting responsibilities behind one ledger.

INFERRED: Readers/callers: .github/workflows/reconcile-historical-backlog.yml:30; .github/workflows/validate-research-decision-reconciliation.yml:32; .github/workflows/validate-research-decision-reconciliation.yml:41. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/reconcile_historical_crossref.py

INFERRED: Purpose: Persistent historical Crossref DOI/expansion queue. Ingestion != investigation.. Source: `scout-operations/tools/reconcile_historical_crossref.py:1`.

INFERRED: MERGE. Unify overlapping scheduling/reporting responsibilities behind one ledger.

INFERRED: Readers/callers: .github/workflows/reconcile-historical-crossref.yml:40; .github/workflows/validate-research-decision-reconciliation.yml:32; .github/workflows/validate-research-decision-reconciliation.yml:42. Writers/producers: .github/workflows/historical-crossref-backfill.yml:63. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/reconcile_monthly_staging.py

INFERRED: Purpose: Reconcile validated, manifest-published monthly proposals back to original DOI cases.. Source: `scout-operations/tools/reconcile_monthly_staging.py:1`.

INFERRED: MERGE. Unify overlapping scheduling/reporting responsibilities behind one ledger.

INFERRED: Readers/callers: .github/workflows/build-scout-discovery-manifest.yml:116. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/reconcile_preprint_retirements.py

INFERRED: Purpose: Retire REACH-confirmed published preprint families; retain immutable evidence and tombstones.. Source: `scout-operations/tools/reconcile_preprint_retirements.py:1`.

INFERRED: MERGE. Unify overlapping scheduling/reporting responsibilities behind one ledger.

INFERRED: Readers/callers: scout-operations/tests/test_preprint_retirements.py:3. Writers/producers: .github/workflows/scout-preprint-retirement.yml:35. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/reconcile_public_handoff.py

INFERRED: Purpose: Reconcile terminal *public identity* evidence without inventing Hub decisions.. Source: `scout-operations/tools/reconcile_public_handoff.py:1`.

INFERRED: MERGE. Unify overlapping scheduling/reporting responsibilities behind one ledger.

INFERRED: Readers/callers: .github/workflows/scout-hourly-guarded-handoff.yml:128; .github/workflows/scout-hourly-guarded-handoff.yml:129. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/reconcile_published_preprint_identities.py

INFERRED: Purpose: Read-only, SHA-verified public REACH/NOAA IR reconciliation for active published preprints.. Source: `scout-operations/tools/reconcile_published_preprint_identities.py:1`.

INFERRED: MERGE. Unify overlapping scheduling/reporting responsibilities behind one ledger.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: .github/workflows/scout-preprint-identity-reconciliation.yml:31. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/reconcile_scout_metrics.py

INFERRED: Purpose: Rebuild and verify all public Scout discovery/throughput/impact measurements.. Source: `scout-operations/tools/reconcile_scout_metrics.py:1`.

INFERRED: MERGE. Unify overlapping scheduling/reporting responsibilities behind one ledger.

INFERRED: Readers/callers: .github/workflows/scout-bounded-expansion-fallback.yml:66; .github/workflows/scout-bounded-expansion-fallback.yml:67; .github/workflows/scout-bounded-expansion-fallback.yml:121; .github/workflows/scout-bounded-expansion-fallback.yml:122; .github/workflows/scout-hourly-guarded-handoff.yml:72; .github/workflows/scout-hourly-guarded-handoff.yml:73; .github/workflows/scout-hourly-guarded-handoff.yml:168; .github/workflows/scout-hourly-guarded-handoff.yml:169. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/reconciliation_diagnostics.py

INFERRED: Purpose: Explain failed terminal gates without changing past statuses or decisions.. Source: `scout-operations/tools/reconciliation_diagnostics.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/recover_historical_datacite.py

INFERRED: Purpose: Recover an exact historical DataCite identity without inventing fresh evidence.. Source: `scout-operations/tools/recover_historical_datacite.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/scout-crosslane-research-memory.yml:65. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/recover_queued_doi_metadata.py

INFERRED: Purpose: Bounded exact-DOI recovery for access failures in Scout's research notes.. Source: `scout-operations/tools/recover_queued_doi_metadata.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/scout-queued-doi-recovery.yml:41; .github/workflows/scout-queued-doi-recovery.yml:53; .github/workflows/validate-scout-research-memory.yml:28; scout-operations/tools/reconcile_scout_metrics.py:146. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/recover_related_output_source.py

INFERRED: Purpose: Bounded native-source recovery for a publisher-cited related DOI.. Source: `scout-operations/tools/recover_related_output_source.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/scout-bounded-expansion-fallback.yml:60. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/related_output_identity.py

INFERRED: Purpose: Fail-closed, read-only same-mission related DOI public identity screen.. Source: `scout-operations/tools/related_output_identity.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/scout-bounded-expansion-fallback.yml:60. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/replay_author_safeguards.py

INFERRED: Purpose: Read-only triage of earlier public-REACH-anchored Crossref author pilot leads.. Source: `scout-operations/tools/replay_author_safeguards.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/validate-scout-author-safeguards.yml:24. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/replay_five_scout_cases.py

INFERRED: Purpose: Read-only replay of five verified Scout case paths using the actual engine.. Source: `scout-operations/tools/replay_five_scout_cases.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/scout-five-case-replay.yml:33; .github/workflows/scout-five-case-replay.yml:37. Writers/producers: .github/workflows/scout-five-case-replay.yml:62. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/replay_full_output_dryrun.py

INFERRED: Purpose: One-output real preflight replay, public evidence only.. Source: `scout-operations/tools/replay_full_output_dryrun.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/scout-one-output-full-dryrun.yml:25. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/research_memory.py

INFERRED: Purpose: Evidence-only, source-SHA-pinned DOI research memory.. Source: `scout-operations/tools/research_memory.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/validate-scout-research-memory.yml:28; .github/workflows/validate-scout-research-memory.yml:35; .github/workflows/validate-scout-research-memory.yml:36. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/reviewer_feedback_guard.py

INFERRED: Purpose: Consumer-side, read-only human-decision awareness.. Source: `scout-operations/tools/reviewer_feedback_guard.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/score_private_benchmark.py

INFERRED: Purpose: Locally score a Scout evaluation sample against PRIVATE independent labels.. Source: `scout-operations/tools/score_private_benchmark.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/scout-v2-impact-report.yml:66. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/select_independent_mission_candidates.py

INFERRED: Purpose: Bounded, source-fingerprint-aware rotation for independent hourly Scout work.. Source: `scout-operations/tools/select_independent_mission_candidates.py:1`.

INFERRED: MERGE. Unify overlapping scheduling/reporting responsibilities behind one ledger.

INFERRED: Readers/callers: .github/workflows/scout-crosslane-research-memory.yml:65. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/select_workstream.py

INFERRED: Purpose: Choose Scout's next research workstream from GitHub-backed API backlog state.. Source: `scout-operations/tools/select_workstream.py:1`.

INFERRED: MERGE. Unify overlapping scheduling/reporting responsibilities behind one ledger.

INFERRED: Readers/callers: .github/workflows/build-scout-discovery-manifest.yml:119; .github/workflows/historical-crossref-actionable-routing.yml:70; .github/workflows/reconcile-historical-crossref.yml:41; .github/workflows/select-scout-workstream.yml:45; .github/workflows/validate-crossref-actionable-routing.yml:30; .github/workflows/validate-expansion-relevance.yml:36. Writers/producers: .github/workflows/historical-crossref-backfill.yml:64; .github/workflows/select-scout-workstream.yml:59. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/source_discovery_metrics.py

INFERRED: Purpose: Evidence-based counters for independently executed GitHub expansion research.. Source: `scout-operations/tools/source_discovery_metrics.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/source_driven_expansion.py

INFERRED: Purpose: Bounded DOI discovery from official publisher source and structured references.. Source: `scout-operations/tools/source_driven_expansion.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/scout-bounded-expansion-fallback.yml:60. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/special_publication_types.py

INFERRED: Purpose: Conservative editorial-publication cues for routing, never conclusive rejection.. Source: `scout-operations/tools/special_publication_types.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/summarize_hourly_missions.py

INFERRED: Purpose: Separate measured ChatGPT hourly mission outcomes from GitHub backstop outcomes.. Source: `scout-operations/tools/summarize_hourly_missions.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/scout-chatgpt-hourly-measurement.yml:40; .github/workflows/scout-hourly-guarded-handoff.yml:164. Writers/producers: .github/workflows/scout-chatgpt-hourly-measurement.yml:75. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/summarize_research_decisions.py

INFERRED: Purpose: Summarize immutable Scout decision checkpoints; no authority to close cases.. Source: `scout-operations/tools/summarize_research_decisions.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/validate-research-decision-reconciliation.yml:32; .github/workflows/validate-research-decision-reconciliation.yml:49. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/sync_monthly_intake.py

INFERRED: Purpose: Synchronize active monthly API DOI cases into Scout's persistent research queue.. Source: `scout-operations/tools/sync_monthly_intake.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/build-monthly-coverage.yml:51. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/unified_source_preflight.py

INFERRED: Purpose: Use ONE SHA-verified public identity/eligibility engine across Scout sources.. Source: `scout-operations/tools/unified_source_preflight.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/scout-unified-source-preflight.yml:45; .github/workflows/scout-unified-source-preflight.yml:50; .github/workflows/validate-monthly-shared-identity.yml:27; .github/workflows/validate-scout-crossmode.yml:47. Writers/producers: .github/workflows/scout-unified-source-preflight.yml:74. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/validate_hourly_mission.py

INFERRED: Purpose: Validate public, privacy-minimized Scout hourly mission records (stdlib only).. Source: `scout-operations/tools/validate_hourly_mission.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/scout-chatgpt-hourly-measurement.yml:40; .github/workflows/scout-hourly-guarded-handoff.yml:63. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/validate_metadata_blockers.py

INFERRED: Purpose: Validate Scout metadata blocker ledger: max five distinct checks, one delayed retry.. Source: `scout-operations/tools/validate_metadata_blockers.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/validate_reviewer_feedback.py

INFERRED: Purpose: Validate redacted, HMAC-signed Discovery Hub review feedback.. Source: `scout-operations/tools/validate_reviewer_feedback.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/verify_preprint_intake.py

INFERRED: Purpose: One publication-status gate for ALL new Scout review feed entries.. Source: `scout-operations/tools/verify_preprint_intake.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/build-scout-discovery-manifest.yml:83; .github/workflows/build-scout-discovery-manifest.yml:110; .github/workflows/scout-hourly-guarded-handoff.yml:144; .github/workflows/scout-hourly-guarded-handoff.yml:147. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/verify_reach_artifact_url.py

INFERRED: Purpose: Read-only, same-mission check for a related artifact's PRIMARY URL in REACH.. Source: `scout-operations/tools/verify_reach_artifact_url.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/scout-reach-artifact-url-regression.yml:26. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/wpo_awards.py

INFERRED: Purpose: Canonical NOAA OAR award parsing and source-grounded WPO funding evidence.. Source: `scout-operations/tools/wpo_awards.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: NOT_DETERMINED. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.


## scout-operations/tools/write_hourly_mission_metrics.py

INFERRED: Purpose: Emit evidence-backed, privacy-minimized GitHub backstop mission metrics.. Source: `scout-operations/tools/write_hourly_mission_metrics.py:1`.

INFERRED: KEEP. Retain reusable validation, source collection or publication gate; adapt its ledger interface.

INFERRED: Readers/callers: .github/workflows/scout-hourly-guarded-handoff.yml:63; .github/workflows/scout-hourly-guarded-handoff.yml:160. Writers/producers: NOT_DETERMINED. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.
