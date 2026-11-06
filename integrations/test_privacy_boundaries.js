/** Offline checks: public GitHub export disabled, private result never logged. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');

const feedback=fs.readFileSync(path.join(__dirname,'DiscoveryHubScoutFeedback.gs'),'utf8');
const internal={};
vm.createContext(internal);
vm.runInContext(feedback,internal);
for(const entry of ['scoutFeedbackExportSigned','scoutFeedbackPushToGithub']){
  assert.equal(typeof internal[entry],'function');
  assert.throws(()=>internal[entry](),/Privacy hold/);
}
assert(!feedback.includes("UrlFetchApp.fetch"),"No outbound private exporter requests permitted");
console.log('PASS: signed reviewer decision export and public GitHub push remain disabled');

const source=fs.readFileSync(path.join(__dirname,'DiscoveryHubDownstreamVerification.gs'),'utf8');
const logs=[];
const ctx={Logger:{log:x=>logs.push(x)}};
vm.createContext(ctx);
vm.runInContext(source,ctx);
ctx.reachDiscoveryNormalizeDoi_=x=>x;
ctx.scoutDownstreamPublicScout_=()=>({
  batchId:'test-batch',
  batchSha256:'a'.repeat(64),
  manifestCandidateRows:1,
  record:{'IR Repository URL':''}
});
ctx.scoutDownstreamPrivateState_=()=>({
  decisionStatus:'PRIVATE_REVIEW_LOG_MATCHES_CURRENT_FINDING',
  decisionCode:'REJECTED',
  smartsheetStatus:'PRIVATE_HUB_INSERTION_RECORDED_NOT_LIVE_API_VERIFIED',
  sensitiveField:'reviewer@example.org'
});
ctx.scoutDownstreamPublicReach_=()=>({
  sourceRows:1,exactIdentityMatches:[],
  status:'NO_EXACT_PUBLIC_URL_MATCH_NOT_PROOF_OF_ABSENCE'
});
const result=ctx.scoutVerifyDownstream('10.1000/test', 'test-batch');
assert.equal(result.privateHub.decisionCode,'REJECTED');
assert.deepEqual(logs,['SCOUT_DOWNSTREAM_READ_ONLY_CHECK_COMPLETED']);
assert(!JSON.stringify(logs).includes('REJECTED'));
assert(!JSON.stringify(logs).includes('reviewer@example.org'));
assert(!JSON.stringify(logs).includes('10.1000/test'));
console.log('PASS: full private verification result only returned to authorized caller, logs minimal');
