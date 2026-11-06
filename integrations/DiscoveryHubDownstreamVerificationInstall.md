# REACH Scout 2.0 — downstream boundary validation (2026-11-06)

**Status:** Read-only verifier implemented and tested with synthetic private workbook state. **NOT deployed** in the private Discovery Hub. No real private sync, reviewer approval, live Smartsheet row insertion, or public REACH publication has been observed by this test.

## What this verifies

1. **Published Scout candidate**: requires an explicit immutable batch ID from the public manifest, validates the batch SHA-256 and row count, and locates the exact DOI once. It never treats an inbox-only draft as published.
2. **Private Hub ingestion**: in the authorized, bound Google spreadsheet, matches the canonical candidate ID, DOI, and 21-field finding fingerprint against the exact published Scout record. Imported content with a changed fingerprint is treated as requiring review.
3. **Reviewer decision**: checks the current candidate state against the private **Discovery Decisions** audit row, reviewer decision timestamp, current finding fingerprint, and decision fingerprint. Merely showing a button or a review status does not prove a valid current decision.
4. **Insertion boundary**: reports whether the private Hub records both source sheet and row IDs, but does **not** call Smartsheet. It never claims that recorded IDs prove a successful API write. A saved approval alone is only staging authorization; parent selection, Smartsheet write and reconciliation remain separate.
5. **Public REACH**: downloads all ten public `agent-data/index/part-*.csv` shards referenced by the REACH manifest, verifies each checksum and row count, and checks exact DOI URL or exact NOAA IR URL matches. It does not guess from title similarity or a missing DOI in the visible link, and no exact URL match is *not* proof of absence.

## Install safely

1. Make a **copy** of the live Discovery Hub bound spreadsheet and its Apps Script project. Keep `REACH_DISCOVERY_WRITE_ENABLED=false` and any other Smartsheet write flags disabled. The last available reference Hub code is `REACH_Discovery_Review.gs` v1.5; compare the actual current deployed version before installation. Do **not** replace existing functions or the insertion module.
2. Add `DiscoveryHubDownstreamVerification.gs` as one new `.gs` file to the **copied** Apps Script project. It reuses the Hub's authenticated functions but does not mutate any spreadsheet.
3. In the copy, use an existing, human-visible published candidate from the Scout queue. Run:

   `scoutVerifyDownstream('10.1109/radarconf2248738.2022.9764246', '2026-11-06-human-project-b616c2488c1fe907f3')`

   This is the APAR **Needs Investigation** candidate, not an approved publication. The existing batch is part of the published manifest. Since the copy may not have the candidate imported, `NOT_IMPORTED_OR_DIFFERENT_HUB` is a valid outcome.
4. In the copied Hub only, run the ordinary **Sync from Scout** once; rerun the verifier. Confirm the canonical DOI and public source fingerprint match and that original review history was not erased. Then repeat Sync and compare the result again for idempotence.
5. **Reviewer-decision test:** use a synthetic copy-only candidate to exercise Pending → On Hold, then ensure the audit-log proof is current. To exercise an approval, an authorized reviewer must inspect and explicitly verify the *real* publication and funding evidence; no automated or mock human approval should be inserted into production.
6. **Staging test:** in the copy, inspect source parent choices, award-to-parent match (including multi-award candidates), and the 24-column metadata preview. Do not click a live write action. Simulate a private row-ID result only in synthetic/unit tests, not in the live sheet.
7. **Live insertion / publication proof, separately:** when an authorized reviewer actually approves a legitimate candidate, verify the chosen parent row exists in the correct live Smartsheet, the insertion response is deterministic (not `UNCERTAIN`), the exact child row exists by API read, and its metadata matches. After the normal Smartsheet → REACH publishing pipeline runs, rerun the verifier and confirm a matching canonical DOI URL or NOAA IR URL plus public REACH UID. If the public link uses a third URL, perform a human corroboration against the full REACH details before calling it published.

## Safety requirements

- This verifier is **read only**. It must not trigger decisions, write to Smartsheet, append to the public Scout feed, or modify REACH.
- Neither its source nor logs include reviewer names/emails, private review notes, native Smartsheet sheet/row IDs or credentials. Results contain public candidate IDs, DOIs, and derived status only.
- Do not confuse the optional, redacted signed reviewer feedback exporter with a live Smartsheet receipt. The current public `scout-operations/research-feedback.json` contains **zero signed reviewer events** and the private connection is not verified.
- The upstream five-case replay from November 6 passed **5/5** with no staging or REACH publication. The downstream private tests cannot be truthfully marked complete until the copied/live Hub and Smartsheet read-only inspection are performed by an authorized connected operator.

## Test results

`node test_downstream_verification.js` — eight synthetic boundary tests passed: missing import, fresh approval/staging separation, changed-source hold, recorded-but-unverified Smartsheet row, inconsistent row fields, review log mismatch, exact URL identity, and manifest checksum rejection.

For fuller automated coverage, add an authenticated *private-only* Smartsheet row lookup after the existing insertion module has been inspected. Do not use public GitHub to store private Smartsheet IDs, PI emails, reviewer audit data or private tracker content.
## Privacy restrictions added November 6, 2026

- The private verifier now logs **only** `SCOUT_DOWNSTREAM_READ_ONLY_CHECK_COMPLETED` to the Apps Script execution log. Its detailed output is returned to the authenticated script caller, not included in persistent logs or GitHub.
- The optional signed exporter and public GitHub decision-feedback consumer are now held/disabled. Do not configure or use either public decision export entry point.
- A separate `integrations/REACH_PublicExportPrivacyGuard.gs` is available as an **installation-ready**, source-independent final export check. After converting private source data to the authorized PUBLIC REACH CSV rows—but BEFORE publishing the CSV—call `reachScoutVerifyPublicReachExport_(publicRows)`. It fails closed if a final row includes email addresses, internal reviewer or Smartsheet identifiers, credentials or private tracker URLs. Do not call it on the private Smartsheet source rows.
- The private REACH publishing script has **not** been accessible for editing or installation through this repository. An authorized owner must inspect the actual script and connect this guard to its final public-CSV handoff. Keep production writes disabled during initial test.
- Never paste a detailed private verifier return object into GitHub issues, workflow logs, or a public spreadsheet; even without names, it can expose DOI-linked private review state.
