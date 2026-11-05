# Scout 2.0 — Private Discovery Hub feedback connection

## Current deployment boundary
The **public GitHub consumer, HMAC verification tests, redacted feedback inbox and downstream same-DOI review hold** can be deployed and verified now. The user-owned private Discovery Hub Google Apps Script is NOT editable through the available GitHub interface. The additive private exporter `integrations/DiscoveryHubScoutFeedback.gs` is an installation-ready companion for the previously supplied `REACH_Discovery_Review.gs` v1.5. Do not claim it is currently installed, that private reviewer history was imported, or that any output was approved.

## Private-to-public contract
A private reviewer decision is eligible for a signed signal only if:
- An authenticated reviewer already saved a supported decision in the bound Hub.
- The candidate is current, not due for re-review; its decision fingerprint equals its current finding fingerprint.
- The record has a canonical DOI, valid public candidate ID, and ISO review timestamp.
- Only these fields leave the Hub: `candidate_id`, `doi`, `decision`, `reviewed_at`, `finding_fingerprint`, `decision_fingerprint`, and HMAC `signature`.

**Never export** reviewer email, reviewer notes, associated private records, Smartsheet sheet/row IDs, names of reviewer users, or internal authorization tokens. These remain private. A signal that says `APPROVED_FOR_STAGING` does not assert a human-approved addition to public REACH; `UPDATED_IN_SMARTSHEET_REVIEWER_REPORTED` reflects the human's own claim, not a separately verified API write.

## One-time authorized setup (after IT/security approval)
1. Verify the actual currently installed private Discovery Hub is compatible with the previously uploaded `REACH_Discovery_Review.gs` v1.5. Do not replace the existing decision script; add `integrations/DiscoveryHubScoutFeedback.gs` as a separate file in a copied test Apps Script project first.
2. Generate a strong random HMAC key **privately**. Put the same value in **Apps Script → Project Settings → Script Properties** under `SCOUT_FEEDBACK_HMAC_KEY`, and in **GitHub repository → Settings → Secrets and variables → Actions** under `SCOUT_FEEDBACK_HMAC_KEY`. Never share the key in chat, commit it, or place it in Sheets cells.
3. For the optional one-click GitHub handoff, create an authorized fine-grained token limited to `PART-WPO/reach-scout-discoveries` with repository contents:write and an appropriate expiry. Store it in Script Properties as `SCOUT_FEEDBACK_GITHUB_TOKEN`; never write it in code or review exports. If direct GitHub writes are not approved, run `scoutFeedbackExportSigned()` privately and have an authorized operator submit its JSON into `scout-operations/reviewer-feedback-inbox/` through the normal GitHub code review process.
4. In a copied workbook, create a test reviewer decision through the original `reachDiscoveryDecide()` flow. Run `scoutFeedbackExportSigned()` and inspect the entire JSON for absence of reviewer PII. Only then run `scoutFeedbackPushToGithub()` through an explicit authorized action; it does not automatically run when a reviewer clicks Save.
5. Verify the GitHub Action `Scout reviewer feedback` succeeded, `scout-operations/research-feedback.json` contains one signed verified event, and `scout-operations/unified-source-preflight.json` identifies the exact candidate/DOI as previously reviewed. Confirm an attempted re-proposal becomes a **review-history reconciliation hold**, not a new candidate or automatic rejection. The test must not insert anything in Smartsheet or REACH.
6. Verify repeat exports are idempotent and a changed finding needing re-review does not export an outdated decision. Restore the private test workbook before production adoption.

## Security and limitations
- This repository is **public**. Signed/redacted signals are visible; do not add case narratives, reviewers' names, reviewer emails, notes or identifiers from private Smartsheet.
- The GitHub Action fails closed if an unsigned/altered event is present or the HMAC secret is unavailable. It accepts only DOI-specific public Scout candidate identities; mismatched candidates need manual reconciliation.
- The consumer prevents blindly re-proposing an exact previously reviewed DOI, but an alternate version or newly supported distinct product may still merit human review. `REJECTED` is NOT universal output ineligibility.
- A missing export is not a verified lack of reviewer decisions. Historical private decisions and live Smartsheet rows remain unknown until observed.
- Only authorized administrators may enable the optional GitHub write handoff. No deployment to private Apps Script has been performed by the public GitHub CI.
