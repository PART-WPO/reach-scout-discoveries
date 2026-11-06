/**
 * REACH Scout private decision export — PRIVACY HOLD.
 *
 * The earlier optional export would place DOI-linked reviewer decisions and
 * timestamps in a PUBLIC GitHub repository. HMAC authenticates messages;
 * it does not make them confidential.
 *
 * Keep the original review history and decisions inside the private Hub.
 * Do not install an older exporter. This additive file intentionally
 * preserves the old callable entry-point names but disables BOTH actions.
 *
 * A future access-controlled, approved design must be reviewed separately.
 * No GitHub credentials or HMAC secrets are required by this safe version.
 */
const SCOUT_FEEDBACK_PRIVACY_HOLD = true;

function scoutFeedbackExportSigned() {
  throw new Error(
    'Privacy hold: exporting private Discovery Hub decisions is disabled. ' +
    'Use the read-only private verifier; do not upload decision records to public GitHub.'
  );
}

function scoutFeedbackPushToGithub() {
  throw new Error(
    'Privacy hold: public GitHub reviewer-feedback publishing is disabled. ' +
    'Private decisions, timestamps and fingerprints must remain inside the Hub.'
  );
}
