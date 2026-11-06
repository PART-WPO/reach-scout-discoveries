# REACH Scout — private Discovery Hub review privacy hold (November 6, 2026)

## Current rule
**Do not export individual reviewer decisions, timestamps, notes, fingerprints, private identifiers, or review-history records to public GitHub.** Although the previous design used signed, redacted signals, a signature authenticates a message; it does not protect the confidentiality of a DOI-linked review decision.

The public repository now ships **disabled** implementations of both `scoutFeedbackExportSigned()` and `scoutFeedbackPushToGithub()`. Both fail closed and make no outbound request. Public GitHub CI also rejects any signed feedback bundle or nonempty public review-signal file; it no longer uploads reviewer outcomes or uses GitHub write permissions for this workflow.

## Where verification belongs
- **Private Discovery Hub:** retain the complete candidate, decision ledger, reviewer identity and notes, fingerprint history, parent associations and Smartsheet row receipts under the existing Google spreadsheet access controls.
- **Private read-only verifier:** use `integrations/DiscoveryHubDownstreamVerification.gs` in an authorized copy of the Hub. It reads private state and public Scout/REACH indices. Its detailed result is returned only to the authorized Apps Script caller; its execution log contains a generic completion marker without a DOI, decision code, person or internal row ID.
- **Public Scout:** use only already-public output identity, metadata and research evidence. Existing public `scout-operations/research-feedback.json` contains zero authenticated private reviewer events. A missing public event is **not** proof that a private reviewer never acted.
- **Public REACH:** publish only output metadata authorized under the REACH publishing process. A separate optional `REACH_PublicExportPrivacyGuard.gs` verifies export-ready rows immediately before the public CSV upload; it is not a replacement for authorization or the publishing code's column mapping.

## Installation / administrator action
1. Compare the files currently deployed in the **private** Apps Script project with the repository. GitHub changes **do not** update an already installed Apps Script file. If the earlier exporter was installed, replace it with the disabled version or remove it before any production use.
2. Do **not** run `scoutFeedbackExportSigned()` or `scoutFeedbackPushToGithub()`, and do not configure, activate or reuse `SCOUT_FEEDBACK_GITHUB_TOKEN` for this workflow.
3. If a dedicated GitHub token or HMAC key was provisioned for the old exporter, an authorized administrator should revoke unneeded credentials and remove unneeded Script Properties/repository secrets, after checking they are not used elsewhere. Never post credentials in chat or GitHub.
4. Keep the private verifier and the optional public-export guard in a **copied** Apps Script project for initial testing. Keep Smartsheet write flags disabled during validation.
5. Confirm the final public REACH CSV mapping excludes private reviewer fields, PI email addresses, internal tracker identifiers, and credentials. Integrate the privacy gate at the final export boundary only after examining that script.
6. Obtain the appropriate NOAA/WPO system-owner or information-security authorization before any future private-to-public review-status transport. A future design requires its own access-controlled destination, minimal schema, retention policy, and technical review.

## Important scope limits
- These GitHub changes cannot revoke an already deployed private Apps Script function or rotate credentials.
- The checks prevent automated publishing through the revised Scout workflow, but **cannot prevent an authorized GitHub writer from manually committing confidential material to a public repository**. Enforce repository branch rules, least-privilege access, staff procedures, and appropriate access review.
- The verifier does not independently read a live Smartsheet row and does not prove final publication. Keep those validation stages separate.
- Synthetic tests and GitHub CI prove code behavior, **not** that the private production Hub has been modified or reviewed.
