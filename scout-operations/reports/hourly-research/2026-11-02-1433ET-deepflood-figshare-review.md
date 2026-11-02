# REACH Scout 14:33 ET — DeepFlood Figshare dataset identity follow-up

Run `REACH-SCOUT-2026-11-02-HOURLY-1433ET`. Recorded 2026-11-02T19:37:08.832520Z. **Primary mode: normal historical discovery.** The current 13 October monthly primary-award records are all checked: nine original DOI proposals are published to the public Scout review feed and four have documented no-actions; coverage missing_from_ledger=0. Historical DataCite 188/188 investigated, zero remaining, 28 human-metadata-needed cases. The Scout manifest currently reports 30 batches / 85 staged proposals. The private Discovery Hub import, human approvals and public REACH additions are NOT VERIFIED.

## New independently discovered research lead — underlying DeepFlood dataset

**Finding:** A previously staged *Scientific Data* article DOI `10.1038/s41597-025-04554-3` directly acknowledges WPO primary award `NA21OAR4590358`, matching SPARK project `spark-000338` (Rapid Floodwater Extent and Depth Measurements Using Optical UAV and SAR). The paper identifies a separate Figshare DeepFlood dataset under DOI `10.6084/m9.figshare.26791243`. A later 2026 Springer paper cites a Figshare DeepFlood dataset DOI `10.6084/m9.figshare.28328339`. The two Figshare IDs could be different versions or records for the same dataset; that relationship is **not verified**. The 2026 SARGANet paper acknowledges NSF and NASA, not a WPO award, so its own publication is **not** attributed to this WPO project merely because it uses DeepFlood.

**Duplicate screening:** Checked all 10 current REACH public index shards (1,238 rows), all 30 active Scout batch CSVs (85 staged proposals), and all 16 public inbox drafts. Neither Figshare DOI is a standalone candidate or exact REACH index match. The already-staged Scientific Data article explicitly mentions DOI 26791243 as a *related dataset*, not as a separate proposed record. This does not constitute full REACH detail/secondary-link dedup; private Hub decisions are inaccessible.

**Metadata limits:** Exact DataCite DOI and Figshare API lookups and DOI landing could not be retrieved in this runtime; no native created date, version relation, complete file inventory, or access status is verified. A community complaint about possible missing Figshare files is unconfirmed and cannot be presented as verified file absence. No DOI date, author, or file inventory was invented.

**What to check before adding this output:** Recover exact DataCite JSON for both Figshare DOIs and native Figshare version metadata | Establish whether the two IDs refer to the same dataset, versions or genuinely distinct outputs | Verify file inventory and public access rather than relying on article claims | Verify dataset-specific connection to spark-000338 primary award NA21OAR4590358 | Complete all REACH detail/secondary URL and pending/private Scout decision comparisons | Apply DataCite created YYYY-MM-DD only after verifying the exact canonical DOI's created field.

**Reviewer question:** Is there one separate eligible WPO-funded DeepFlood dataset, and which DOI/version should REACH represent? **Disposition:** `PENDING_EXACT_NATIVE_METADATA_AND_VERSION_IDENTITY_HUMAN_REVIEW`. This is **one provisional research identity group, zero new Scout drafts, zero Hub imports, zero approvals**. Independent discovery provenance is preserved; a later API metadata lookup must not reclassify its discovery method.

## Monthly reviewer-story parity spot check

Read the currently published eight-row `2026-11-02-monthly-reviewer-story-parity-001` batch and the one-row enriched Fire Radiative Power batch. Each contains `Finding:`, `What to check before adding this output:`, and `Reviewer question:` sections (8/8 and 1/1). These are public staged review narratives, **not** proof of private Hub synchronization or reviewer approval. The current one-row Fire Radiative Power case remains NEEDS INVESTIGATION for exact parent award attribution. No old human decision was changed.

## Sources and next actions

- https://www.nature.com/articles/s41597-025-04554-3
- https://link.springer.com/article/10.1007/s12145-026-02164-0
- https://api.datacite.org/dois/10.6084/m9.figshare.26791243 (access failed)
- https://api.datacite.org/dois/10.6084/m9.figshare.28328339 (access failed)
- https://api.figshare.com/v2/articles/28328339 (access failed)
- https://github.com/PART-WPO/reach-dashboard/blob/main/agent-data/manifest.json
- https://github.com/PART-WPO/reach-scout-discoveries/blob/main/scout-discoveries/manifest.json

Next mission: resume this source-linked identity group after exact DOI metadata is available, alongside the existing Atlantic drifter year-attribution holds and pending monthly Zenodo expansion intake. Do not stage duplicates or modify public REACH/SPARK/Smartsheet.