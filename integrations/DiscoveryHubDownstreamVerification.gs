/**
 * REACH Scout 2.0: READ-ONLY downstream boundary verification.
 * Add to a COPY of the private Discovery Hub bound Apps Script, alongside
 * REACH_Discovery_Review.gs. No source writes, no review decisions, no external
 * requests containing private data and no public reviewer signals.
 */
const SCOUT_DOWNSTREAM_V1 = Object.freeze({
  scoutBase: 'https://raw.githubusercontent.com/PART-WPO/reach-scout-discoveries/main/',
  reachBase: 'https://raw.githubusercontent.com/PART-WPO/reach-dashboard/main/',
  scoutManifest: 'scout-discoveries/manifest.json',
  reachManifest: 'agent-data/manifest.json'
});

function scoutDownstreamSha_(bytes) {
  return Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, bytes)
    .map(b => (b < 0 ? b + 256 : b).toString(16).padStart(2, '0')).join('');
}
function scoutDownstreamFetch_(base, path, expectedSha) {
  if (!/^[\w./-]+$/.test(path) || path.includes('..'))
    throw new Error('Invalid public repository file path');
  const response = UrlFetchApp.fetch(base + path, {muteHttpExceptions: true, followRedirects: false});
  if (response.getResponseCode() !== 200)
    throw new Error('Cannot verify public source: ' + path + ' HTTP ' + response.getResponseCode());
  const bytes = response.getContent();
  const sha = scoutDownstreamSha_(bytes);
  if (expectedSha && sha !== expectedSha)
    throw new Error('Public source checksum mismatch: ' + path);
  return {text: response.getContentText('UTF-8'), sha: sha};
}
function scoutDownstreamCsv_(csv) {
  const rows = Utilities.parseCsv(csv);
  if (!rows.length) throw new Error('Empty public CSV');
  const headers = rows.shift();
  if (new Set(headers).size !== headers.length) throw new Error('Duplicate CSV headers');
  return rows.filter(r => r.some(x => String(x).trim()))
    .map(r => {
      if (r.length !== headers.length) throw new Error('CSV column count mismatch');
      return Object.fromEntries(headers.map((h, i) => [h, r[i] || '']));
    });
}
function scoutDownstreamSameUrl_(a, b) {
  return !!a && !!b && String(a).trim().replace(/#.*$/, '').replace(/\/$/, '').toLowerCase() ===
    String(b).trim().replace(/#.*$/, '').replace(/\/$/, '').toLowerCase();
}
function scoutDownstreamPublicScout_(doi, batchId) {
  const manifest = JSON.parse(scoutDownstreamFetch_(SCOUT_DOWNSTREAM_V1.scoutBase,
    SCOUT_DOWNSTREAM_V1.scoutManifest).text);
  if (manifest.schema !== 'reach-scout-discovery-feed-v1')
    throw new Error('Unexpected Scout manifest schema');
  const batch = (manifest.batches || []).find(b => b.id === batchId);
  if (!batch) throw new Error('Specified batch not published in Scout manifest');
  if (!/^scout-discoveries\/batches\/[\w.-]+\.csv$/.test(batch.path))
    throw new Error('Unexpected Scout batch path');
  const csv = scoutDownstreamFetch_(SCOUT_DOWNSTREAM_V1.scoutBase, batch.path, batch.sha256);
  const rows = scoutDownstreamCsv_(csv.text);
  if (rows.length !== batch.record_count) throw new Error('Scout batch row count mismatch');
  const matches = rows.filter(r => reachDiscoveryNormalizeDoi_(r.DOI) === doi);
  if (matches.length !== 1) throw new Error('Expected one DOI in named Scout batch, found ' + matches.length);
  return {record: matches[0], batchSha256: csv.sha, batchId: batch.id,
    manifestBatchCount: manifest.batch_count, manifestCandidateRows: manifest.candidate_rows};
}
function scoutDownstreamPublicReach_(doi, irUrl) {
  const manifest = JSON.parse(scoutDownstreamFetch_(SCOUT_DOWNSTREAM_V1.reachBase,
    SCOUT_DOWNSTREAM_V1.reachManifest).text);
  if (manifest.feed !== 'reach-agent-feed' || !Array.isArray(manifest.index.files))
    throw new Error('Unexpected REACH agent-data index manifest');
  const matches = [];
  let rowsChecked = 0;
  for (const file of manifest.index.files) {
    if (!/^agent-data\/index\/part-\d+\.csv$/.test(file.path))
      throw new Error('Unexpected REACH shard path');
    const csv = scoutDownstreamFetch_(SCOUT_DOWNSTREAM_V1.reachBase, file.path, file.sha256);
    const rows = scoutDownstreamCsv_(csv.text);
    if (rows.length !== file.rows) throw new Error('REACH index row count mismatch: ' + file.path);
    rowsChecked += rows.length;
    for (const row of rows) {
      const link = row['Link to Output'];
      if (scoutDownstreamSameUrl_(link, 'https://doi.org/' + doi) ||
          (irUrl && scoutDownstreamSameUrl_(link, irUrl)))
        matches.push({recordId: row['Record ID'], reachUid: row['REACH UID'],
          matchType: scoutDownstreamSameUrl_(link, irUrl) ? 'EXACT_NOAA_IR_URL' : 'EXACT_DOI_URL'});
    }
  }
  if (rowsChecked !== manifest.source.rows)
    throw new Error('REACH index is incomplete relative to source manifest');
  return {sourceRows: rowsChecked, exactIdentityMatches: matches,
    status: matches.length === 1 ? 'PUBLIC_REACH_IDENTITY_MATCH' :
      matches.length > 1 ? 'MULTIPLE_PUBLIC_IDENTITY_MATCHES_REVIEW' :
      'NO_EXACT_PUBLIC_URL_MATCH_NOT_PROOF_OF_ABSENCE'};
}
function scoutDownstreamPrivateState_(doi, publicRow) {
  reachDiscoveryReviewer_();
  const book = reachDiscoveryBook_();
  const csh = book.getSheetByName(REACH_DISCOVERY_V1.CANDIDATES);
  const dsh = book.getSheetByName(REACH_DISCOVERY_V1.DECISIONS);
  if (!csh || !dsh) throw new Error('Private Discovery Hub candidate/decision tabs missing');
  const id = 'scoutnew-v1-' + reachDiscoveryDigest_('doi:' + doi, 32);
  const candidates = reachDiscoveryRead_(csh).filter(c => c['Candidate ID'] === id);
  if (candidates.length > 1) throw new Error('Duplicate private candidate identity');
  if (!candidates.length) return {candidateId: id, status: 'NOT_IMPORTED_OR_DIFFERENT_HUB',
    decisionStatus: 'NOT_OBSERVED', smartsheetStatus: 'NOT_OBSERVED'};
  const c = candidates[0];
  if (reachDiscoveryNormalizeDoi_(c.DOI) !== doi) throw new Error('Private candidate DOI identity mismatch');
  const currentFingerprint = reachDiscoveryFingerprint_(publicRow);
  const sourceFresh = c['Finding Fingerprint'] === currentFingerprint;
  const log = reachDiscoveryRead_(dsh).filter(x => x['Candidate ID'] === id);
  const reviewed = c['Reviewer Decision'] && c['Reviewer Decision'] !== 'Pending';
  const matchingDecision = reviewed && log.some(x =>
    x.Decision === c['Reviewer Decision'] &&
    x['Timestamp (UTC)'] === c['Reviewed At'] &&
    x['Finding Fingerprint'] === c['Decision Fingerprint'] &&
    c['Decision Fingerprint'] === c['Finding Fingerprint']);
  const eligibleStaging = sourceFresh && matchingDecision &&
    c['Reviewer Decision'] === 'Approved for Staging' &&
    c['Queue Status'] === 'Current' && c['Review Freshness'] !== 'Needs re-review';
  const hasRow = !!c['Created Row ID'];
  const hasSheet = !!c['Created Sheet ID'];
  return {candidateId: id,
    status: sourceFresh ? 'IMPORTED_MATCHES_PUBLISHED_SCOUT_FINDING' : 'IMPORTED_BUT_SOURCE_CHANGED_REVIEW_REQUIRED',
    decisionStatus: !reviewed ? 'AWAITING_REVIEW' :
      matchingDecision && sourceFresh ? 'PRIVATE_REVIEW_LOG_MATCHES_CURRENT_FINDING' :
      'DECISION_LOG_OR_FINGERPRINT_MISMATCH',
    decisionCode: c['Reviewer Decision'] || 'Pending',
    smartsheetStatus: hasRow && hasSheet ? 'PRIVATE_HUB_INSERTION_RECORDED_NOT_LIVE_API_VERIFIED' :
      hasRow !== hasSheet ? 'INCONSISTENT_PRIVATE_INSERTION_FIELDS' :
      eligibleStaging ? 'APPROVED_FOR_STAGING_PARENT_AND_INSERTION_NOT_VERIFIED' :
      'NO_INSERTION_RECORDED',
    hasRecordedNativeRow: hasRow && hasSheet,
    sourceRunMatches: c['Source Run ID'] === publicRow['Source Run ID'],
    currentInQueue: c['Queue Status'] === 'Current'};
}
/**
 * Manual boundary test. Example:
 * scoutVerifyDownstream('10.1109/radarconf2248738.2022.9764246',
 *   '2026-11-06-human-project-b616c2488c1fe907f3')
 * Returns PUBLIC identifiers and derived state only; never rows, notes,
 * reviewer identities, native Smartsheet IDs or private sheet contents.
 */
function scoutVerifyDownstream(doiInput, publishedBatchId) {
  const doi = reachDiscoveryNormalizeDoi_(doiInput);
  if (!/^10\.\d{4,9}\/\S+$/.test(doi)) throw new Error('Supply a canonical DOI');
  const feed = scoutDownstreamPublicScout_(doi, publishedBatchId);
  const privateStatus = scoutDownstreamPrivateState_(doi, feed.record);
  const reach = scoutDownstreamPublicReach_(doi, feed.record['IR Repository URL'] || '');
  const result = {schema: 'reach-scout-private-boundary-audit-v1',
    mode: 'READ_ONLY', doi: doi, scoutBatch: feed.batchId,
    scoutBatchSha256: feed.batchSha256, scoutFeedRows: feed.manifestCandidateRows,
    privateHub: privateStatus, publicReach: reach,
    liveSmartsheetRowApiVerified: false, actualProductionSyncVerified: false,
    fullEndToEndProven: false,
    note: 'Private insertion flags are not a Smartsheet API read. Public REACH is checked against every index shard; exact URL identity is positive evidence, while no exact match is not proof of absence. Human actions never happen in this function.'};
  Logger.log(JSON.stringify(result));
  return result;
}