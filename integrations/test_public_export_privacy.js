const fs=require('node:fs');
const vm=require('node:vm');
const assert=require('node:assert/strict');
const src=fs.readFileSync(__dirname+'/REACH_PublicExportPrivacyGuard.gs','utf8');
const ctx={};vm.createContext(ctx);vm.runInContext(src,ctx);

const clean={'REACH UID':'reachuid-v1-public','Title':'Public project research',
'Principal Investigators':'Public Investigator','Link to Output':'https://doi.org/10.1175/WAF-D-26-0001.1',
'Award Number(s)':'NA25OAR4590001-01','Brief Abstract':'Public weather evaluation'};
assert.equal(ctx.reachScoutVerifyPublicReachExport_([clean]).checkedRows,1);

for(const obj of [
 {'Reviewer Email':''},
 {'Principal Investigator Email(s)':''},
 {'Link to Output':'https://app.smartsheetgov.com/b/home'},
 {'Brief Abstract':'For private contact, reviewer@example.org'},
 {'Brief Abstract':'Reviewer Decision: Rejected'},
 {'Output URL':'https://example.com/?access_token='+('x'.repeat(40))},
 {'Title':'Public','Smartsheet Row ID':'123456'}]){
  assert.throws(()=>ctx.reachScoutVerifyPublicReachExport_([obj]),/privacy hold/);
}
assert.throws(()=>ctx.reachScoutVerifyPublicReachExport_([]),/privacy hold/);
console.log('PASS: final REACH export mapping privacy gate blocks seven private cases');
