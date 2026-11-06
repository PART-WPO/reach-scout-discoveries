/**
 * OPTIONAL REACH publication boundary guard: deploy only in the PRIVATE
 * Apps Script that builds the final PUBLIC REACH CSV.
 *
 * Run on the final export-mapped rows BEFORE generating/uploading the
 * public CSV. Never run on the private internal Smartsheet source records;
 * they may legitimately contain restricted internal columns.
 *
 * This file does not publish anything and does not log row contents.
 * It is NOT installed in production by GitHub.
 */
const REACH_PUBLIC_EXPORT_PRIVACY_V1 = Object.freeze({
  forbiddenField: /^(?:candidate id|principal investigator e-?mail\(s\)?|pi e-?mail|reviewer(?: email| name| identity| decision| notes?)|review notes|reviewed at|created (?:row|sheet) id|smartsheet(?:gov)? (?:row|sheet) id|decision fingerprint|finding fingerprint|authorization token)$/i,
  email: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/i,
  privateLabel: /\b(?:(?:reviewer\s+(?:e-?mail|name|identity|notes?|decision|user(?:name)?|id)|review\s+notes?)|reviewed\s+(?:by|at)|(?:decision|finding)\s+fingerprint|(?:created|smartsheet|smartsheetgov|private|source)\s+(?:sheet|row)\s+id|private\s+(?:review|decision)\s+(?:note|record|history|log))\s*[:=]/i,
  secret: /(?:\bgithub_pat_[A-Za-z0-9_]{20,}|\bgh[pousr]_[A-Za-z0-9]{20,}|\bxox[baprs]-[A-Za-z0-9-]{15,}|\bAIza[0-9A-Za-z_-]{25,}|\bsk-(?:proj-)?[0-9A-Za-z_-]{20,}|\bBearer\s+[0-9A-Za-z._~-]{12,}|[?&](?:api_?key|access_?token|refresh_?token|auth|token|client_secret|signature|sig)=)/i,
  trackerUrl: /https?:\/\/[^\s/]*(?:smartsheet\.com|smartsheetgov\.com)(?:\/|\b)/i
});
function reachScoutCheckPublicExportRow_(record, rowNumber) {
  if (!record || typeof record !== 'object' || Array.isArray(record))
    throw new Error('Public export privacy hold: invalid mapped output row');
  for (const [field, raw] of Object.entries(record)) {
    if (REACH_PUBLIC_EXPORT_PRIVACY_V1.forbiddenField.test(String(field).trim()))
      throw new Error('Public export privacy hold: private column at row ' + rowNumber);
    const value = String(raw == null ? '' : raw);
    for (const [label, rule] of [
      ['email', REACH_PUBLIC_EXPORT_PRIVACY_V1.email],
      ['private review/row data', REACH_PUBLIC_EXPORT_PRIVACY_V1.privateLabel],
      ['credential or signed URL', REACH_PUBLIC_EXPORT_PRIVACY_V1.secret],
      ['Smartsheet tracker URL', REACH_PUBLIC_EXPORT_PRIVACY_V1.trackerUrl]]) {
      if (rule.test(value))
        throw new Error('Public export privacy hold: ' + label +
          ' in row ' + rowNumber + ' / ' + String(field));
    }
  }
  return true;
}
/**
 * Integrate into a private publisher:
 *   const publicRows = buildPublicReachRows_(...); // pseudocode
 *   reachScoutVerifyPublicReachExport_(publicRows);
 *   publishReachCsv_(publicRows); // only if guard returned successfully
 *
 * Note: this checks *public export rows*, not restricted source rows.
 */
function reachScoutVerifyPublicReachExport_(publicRows) {
  if (!Array.isArray(publicRows) || !publicRows.length)
    throw new Error('Public export privacy hold: no mapped output rows');
  publicRows.forEach((row, i) => reachScoutCheckPublicExportRow_(row, i + 2));
  return {privacyCheck:'PASS', checkedRows: publicRows.length};
}
