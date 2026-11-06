const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const crypto = require('node:crypto');
const src = fs.readFileSync(__dirname + '/DiscoveryHubDownstreamVerification.gs', 'utf8');
const DOI = '10.1000/boundary-test';
let candidates = [], decisions = [], files = {};
const digest = (s, n=32) => crypto.createHash('sha256').update(s).digest('hex').slice(0,n);
const fingerprint = r => digest(['Title','DOI','Output URL','Output Type','NOAA Award Number(s)',
  'WPO Program','Proposed Project Title','Suggested Parent Project','Authors / PI',
  'Principal Investigators','Principal Investigator Email(s)','Publication Date','Brief Abstract',
  'IR?','IR Status','IR Pub Date','IR Repository URL','Evidence URL','Funding Evidence URL',
  'Scout Discovery Rationale','Existing REACH Match'].map(k=>String(r[k]||'').trim()).join('\x1e'),64);
const publicRow = {'Title':'Example','DOI':DOI,'Source Run ID':'test-run','IR Repository URL':'https://repository.library.noaa.gov/view/noaa/77039'};
const id = 'scoutnew-v1-' + digest('doi:'+DOI);
const context={
  Logger:{log(){}},
  Utilities:{DigestAlgorithm:{SHA_256:'sha256'},
    computeDigest:(alg,b)=>[...crypto.createHash('sha256').update(Buffer.from(b)).digest()].map(x=>x>127?x-256:x),
    parseCsv:s=>s.trim().split(/\r?\n/).map(x=>x.split(','))},
  UrlFetchApp:{fetch:(url)=>({getResponseCode:()=>files[url]?200:404,
    getContent:()=>[...Buffer.from(files[url]||'')],getContentText:()=>files[url]||''})},
  reachDiscoveryNormalizeDoi_:s=>String(s||'').toLowerCase().replace(/^https?:\/\/doi.org\//,''),
  reachDiscoveryDigest_:digest,
  reachDiscoveryFingerprint_:fingerprint,
  reachDiscoveryReviewer_:()=>true,
  reachDiscoveryBook_:()=>({getSheetByName:n=>n==='Discovery Candidates'?'c':n==='Discovery Decisions'?'d':null}),
  reachDiscoveryRead_:sh=>sh==='c'?candidates:decisions,
  REACH_DISCOVERY_V1:{CANDIDATES:'Discovery Candidates',DECISIONS:'Discovery Decisions'}
};
vm.createContext(context);vm.runInContext(src,context);
const state=(row=publicRow)=>context.scoutDownstreamPrivateState_(DOI,row);
const base=()=>({'Candidate ID':id,DOI,'Finding Fingerprint':fingerprint(publicRow),
  'Decision Fingerprint':fingerprint(publicRow), 'Queue Status':'Current',
  'Review Freshness':'Reviewed', 'Reviewer Decision':'Approved for Staging',
  'Source Run ID':'test-run','Reviewed At':'2026-11-06T12:00:00.000Z'});
const log=()=>({'Candidate ID':id,'Decision':'Approved for Staging',
  'Finding Fingerprint':fingerprint(publicRow),'Timestamp (UTC)':'2026-11-06T12:00:00.000Z'});
const test=(name,fn)=>{fn();console.log('PASS',name)};
test('no private import is not mistaken for an imported candidate',()=>{
  candidates=[];decisions=[];
  assert.equal(state().status,'NOT_IMPORTED_OR_DIFFERENT_HUB');
});
test('fresh reviewer approval only permits staging, not publication',()=>{
  candidates=[base()];decisions=[log()];
  const x=state();
  assert.equal(x.status,'IMPORTED_MATCHES_PUBLISHED_SCOUT_FINDING');
  assert.equal(x.decisionStatus,'PRIVATE_REVIEW_LOG_MATCHES_CURRENT_FINDING');
  assert.equal(x.smartsheetStatus,'APPROVED_FOR_STAGING_PARENT_AND_INSERTION_NOT_VERIFIED');
});
test('stale Scout finding triggers re-review',()=>{
  candidates=[{...base(),'Finding Fingerprint':'a'.repeat(64)}];decisions=[log()];
  assert.equal(state().status,'IMPORTED_BUT_SOURCE_CHANGED_REVIEW_REQUIRED');
  assert.equal(state().decisionStatus,'DECISION_LOG_OR_FINGERPRINT_MISMATCH');
});
test('recorded native row is not represented as live API verified',()=>{
  candidates=[{...base(),'Created Sheet ID':'private-sheet', 'Created Row ID':'private-row'}];decisions=[log()];
  const x=state();
  assert.equal(x.smartsheetStatus,'PRIVATE_HUB_INSERTION_RECORDED_NOT_LIVE_API_VERIFIED');
  assert.equal(JSON.stringify(x).includes('private-row'),false);
});
test('half-created native row fields are flagged as inconsistent',()=>{
  candidates=[{...base(),'Created Row ID':'private-row'}];decisions=[log()];
  assert.equal(state().smartsheetStatus,'INCONSISTENT_PRIVATE_INSERTION_FIELDS');
});
test('private decision without auditable decision log is not verified',()=>{
  candidates=[base()];decisions=[];
  assert.equal(state().decisionStatus,'DECISION_LOG_OR_FINGERPRINT_MISMATCH');
});
test('URLs require exact match, not title similarity',()=>{
  assert.equal(context.scoutDownstreamSameUrl_('https://doi.org/'+DOI,'https://doi.org/'+DOI+'/'),true);
  assert.equal(context.scoutDownstreamSameUrl_('https://example.com/other','https://doi.org/'+DOI),false);
});
test('checksum mismatch fails closed without private mutations',()=>{
  const url='https://raw.githubusercontent.com/PART-WPO/reach-dashboard/main/agent-data/index/part-001.csv';
  files[url]='a,b\n1,2\n';
  assert.throws(()=>context.scoutDownstreamFetch_('https://raw.githubusercontent.com/PART-WPO/reach-dashboard/main/',
    'agent-data/index/part-001.csv','a'.repeat(64)),/checksum mismatch/);
});