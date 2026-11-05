/**
 * Scout 2.0 — ADDITIVE private Discovery Hub feedback exporter.
 * Install alongside REACH_Discovery_Review.gs v1.5; never replace its
 * decision/approval functions. No reviewer email, comments, spreadsheet IDs,
 * or private Smartsheet IDs leave the authorized private spreadsheet.
 *
 * Requires ScriptProperties.SCOUT_FEEDBACK_HMAC_KEY, configured by an
 * authorized administrator; DO NOT store the key in GitHub/Sheets/source.
 */
const SCOUT_FB_V1 = Object.freeze({
  schema:'reach-scout-signed-review-feedback-v1',
  source:'DiscoveryHubPrivateExport',
  codes:Object.freeze({
    'Approved for Staging':'APPROVED_FOR_STAGING',
    'On Hold':'ON_HOLD',
    'Rejected':'REJECTED',
    'Already in REACH':'ALREADY_IN_REACH',
    'Update Needed':'UPDATE_NEEDED',
    'Updated in Smartsheet':'UPDATED_IN_SMARTSHEET_REVIEWER_REPORTED',
    'No Update Needed':'NO_UPDATE_NEEDED'
  })
});
function scoutFeedbackHex_(bytes){
  return bytes.map(x=>(x<0?x+256:x).toString(16).padStart(2,'0')).join('');
}
function scoutFeedbackCanonical_(e){
  return [
    'reach-scout-feedback-v1',e.candidate_id,e.doi,
    e.decision,e.reviewed_at,e.finding_fingerprint,
    e.decision_fingerprint
  ].join('\n');
}
/** A human-authorized export: private history read ONLY, no writes. */
function scoutFeedbackExportSigned(){
  reachDiscoveryReviewer_();
  const secret=PropertiesService.getScriptProperties()
     .getProperty('SCOUT_FEEDBACK_HMAC_KEY');
  if(!secret||secret.length<32)throw new Error(
    'Missing strong private Scout feedback signing key in Script Properties');
  const book=reachDiscoveryBook_();
  const sh=book.getSheetByName(REACH_DISCOVERY_V1.CANDIDATES);
  if(!sh)throw new Error('Discovery candidates sheet has not been configured');
  const records=reachDiscoveryRead_(sh);
  const events=[];
  let skipped=0;
  for(const c of records){
    const current=c['Queue Status']==='Current'
      &&c['Review Freshness']!=='Needs re-review'
      &&c['Finding Fingerprint']===c['Decision Fingerprint'];
    const code=SCOUT_FB_V1.codes[c['Reviewer Decision']];
    const id=String(c['Candidate ID']||'').trim();
    const doi=reachDiscoveryNormalizeDoi_(c.DOI||'').toLowerCase();
    const at=String(c['Reviewed At']||'').trim();
    const fp=String(c['Finding Fingerprint']||'').trim().toLowerCase();
    const dfp=String(c['Decision Fingerprint']||'').trim().toLowerCase();
    if(!current||!code||!/^scoutnew-v1-[0-9a-f]{32}$/.test(id)
       ||!/^10\.\d{4,9}\/\S+$/i.test(doi)
       ||!/^\d{4}-\d\d-\d\dT.*Z$/.test(at)
       ||!/^[0-9a-f]{32,128}$/.test(fp)
       ||!/^[0-9a-f]{32,128}$/.test(dfp)){
      skipped++;continue;
    }
    const e={candidate_id:id,doi:doi,decision:code,reviewed_at:at,
             finding_fingerprint:fp,decision_fingerprint:dfp};
    const mac=Utilities.computeHmacSha256Signature(
       scoutFeedbackCanonical_(e),secret,Utilities.Charset.UTF_8);
    e.signature=scoutFeedbackHex_(mac);
    events.push(e);
  }
  events.sort((a,b)=>a.reviewed_at.localeCompare(b.reviewed_at)||
    a.candidate_id.localeCompare(b.candidate_id));
  const json=JSON.stringify({schema:SCOUT_FB_V1.schema,
                             source:SCOUT_FB_V1.source,events:events},null,2);
  return {json:json,count:events.length,skipped:skipped,
    notice:'Only redacted signed candidate decisions. Review notes and reviewer email remain private. No GitHub write or REACH change performed.'};
}
/**
 * EXPLICIT OPT-IN: reviewer/admin calls this function to send a redacted
 * signed bundle to the public Scout GitHub inbox. Requires an approved
 * fine-grained GitHub token with contents:write ONLY for this one repository,
 * stored in private Script Properties SCOUT_FEEDBACK_GITHUB_TOKEN.
 * Does not run on a timer or on every review decision.
 */
function scoutFeedbackPushToGithub(){
  reachDiscoveryReviewer_();
  const token=PropertiesService.getScriptProperties()
    .getProperty('SCOUT_FEEDBACK_GITHUB_TOKEN');
  if(!token)throw new Error('Authorized private GitHub token is not configured');
  const exported=scoutFeedbackExportSigned();
  if(!exported.count)return {published:false,reason:'No eligible current reviewer decision exports'};
  const digest=reachDiscoveryDigest_(exported.json,32);
  const path='scout-operations/reviewer-feedback-inbox/'+'hub-'+digest+'.json';
  const api='https://api.github.com/repos/PART-WPO/reach-scout-discoveries/contents/'+path;
  const payload=JSON.stringify({
    message:'Append redacted signed Discovery Hub reviewer outcomes',
    branch:'main',
    content:Utilities.base64Encode(Utilities.newBlob(exported.json)
                .getBytes())
  });
  const response=UrlFetchApp.fetch(api,{
    method:'put',contentType:'application/json',
    headers:{
      Authorization:'Bearer '+token,
      Accept:'application/vnd.github+json',
      'X-GitHub-Api-Version':'2022-11-28'
    },
    payload:payload,muteHttpExceptions:true
  });
  const status=response.getResponseCode();
  if(status!==201){
    if(status===422)throw new Error('A signed feedback bundle already exists. Do not overwrite; re-export only after a new human decision.');
    throw new Error('Scout feedback upload failed HTTP '+status+
      '; existing human decisions and public repository remain unchanged');
  }
  return {published:true,path:path,count:exported.count,
    validation:'Pending GitHub Action signature and public candidate identity checks',
    no_smartsheet_or_reach_write:true};
}
