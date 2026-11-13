#!/usr/bin/env python3
"""VERIFIED_SOURCE: Offline checks of analysis deliverables; no scheduler test implementation or external calls."""
import csv,hashlib,json,re,subprocess,datetime
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[1];PREFIX='scout-operations/analysis-v3/';BASE='b21f3271c92ad1e7a4643104920bfb214c65b186'
def rows(n):return list(csv.DictReader((O/n).open()))
def doc(n):return json.loads((O/n).read_text())
checks=[]
def check(name,condition,details):
 checks.append({'claim_label':'VERIFIED_SOURCE','check':name,'passed':bool(condition),'evidence':details})
 if not condition:raise AssertionError(name)
originals=rows('source-files.csv');tracked=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE],cwd=R,text=True).splitlines()
check('Inventory covers every original asset',set(x['path'] for x in rows('inventory.csv'))==set(tracked),'inventory.csv:1 and source-files.csv:1')
check('All original file hashes remain identical to captured source',all((R/x['path']).is_file() and hashlib.sha256((R/x['path']).read_bytes()).hexdigest()==x['sha256'] for x in originals),'source-files.csv:1; every original file recomputed')
diff=subprocess.check_output(['git','diff','--name-only',BASE],cwd=R,text=True).splitlines()
check('No existing tracked file differs from pinned Git source',all(p.startswith(PREFIX) for p in diff),'git diff --name-only '+BASE)
untracked=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=R,text=True).splitlines()
check('All added or untracked repository files stay inside requested folder',all(p.startswith(PREFIX) for p in untracked+diff),'git diff and git ls-files --others --exclude-standard')
seeds=doc('seed-ledger.json')['seeds'];summary=doc('import-summary.json');pilot=rows('pilot-seeds.csv');gold=rows('gold-candidates.csv')
check('One row for each of 933 public publication seeds',len(seeds)==933 and len({x['seed_id'] for x in seeds})==933,'seed-ledger.json:1; import-summary.json:1')
check('Import partition adds up',summary['seed_records_with_importable_method_observations']+summary['seed_records_with_context_only']+summary['seed_records_without_linked_prior_work']==len(seeds),'import-summary.json:1')
check('Each seed has all four method states',all(set(x['methods'])=={'award_search','related_identifier_sweep','full_text_link_scan','agent_review'} for x in seeds),'seed-ledger.json:1')
check('Unknown methods retain unknown attempts and no claimed completion',all(v['attempts'] is None and not v['completion_verified'] for x in seeds for v in x['methods'].values() if v['status']=='NOT_DETERMINED'),'seed-ledger.json:1')
check('No imported method is falsely marked complete',all(not v['completion_verified'] for x in seeds for v in x['methods'].values()),'seed-ledger.json:1')
check('Every seed has retry, blocker, input hash and attempts fields per method',all(all(k in v for k in ['retry_after','blocker_class','input_hash','attempts']) for x in seeds for v in x['methods'].values()),'seed-ledger.json:1')
check('Pilot has 40 distinct seed IDs separate from all gold candidates',len(pilot)==40 and len({x['seed_uid'] for x in pilot})==40 and not ({x['record_id'] for x in pilot}&{x['seed_record_id'] for x in gold}),'pilot-seeds.csv:1 and gold-candidates.csv:1')
check('Pilot has no known DOI overlap with gold candidates',not ({d.strip() for x in pilot for d in x['dois'].split('|') if d.strip()} & {d.strip() for x in gold for d in x['seed_dois'].split('|') if d.strip()}),'pilot-seeds.csv:1 and gold-candidates.csv:1')
projection=doc('reach-public-projection.json');rr={r['Record ID']:r for part in projection['parts'] for r in part['projected_records']}
goldaw={a.strip() for x in gold for a in rr[x['seed_record_id']]['Award Number(s)'].split(',') if a.strip()};pilotaw={a.strip() for x in pilot for a in rr[x['record_id']]['Award Number(s)'].split(',') if a.strip()}
check('Pilot has no gold-candidate award overlap',not goldaw&pilotaw,'reach-public-projection.json:1; pilot-seeds.csv:1; gold-candidates.csv:1')
leads=doc('artifact-leads.json')['leads'];check('Artifact IDs unique and tiers restricted',len({x['artifact_id'] for x in leads})==len(leads) and all(x['claim_tier'] in {'same-DOI award','supporting output of a named paper','unverified'} for x in leads),'artifact-leads.json:1')
check('Exactly 20 specification cases and no implementation',len(re.findall(r'^\| \d+ \|', (O/'scheduler-test-spec.md').read_text(),re.M))==20,'scheduler-test-spec.md:1; specs only')
check('All specified public detail shards were projected',len(projection['parts'])==len(doc('reach-manifest.json')['body']['details']['files']) and sum(p['rows'] for p in projection['parts'])==1238,'reach-manifest.json:1 and reach-public-projection.json:1')
invalid=[]
for p in [O/'OWNER-REPORT.md',O/'ledger-design.md',O/'inventory-ownership.md']:
 for path,num in re.findall(r'([\w./-]+\.(?:py|md|csv|json|yml|gs)):(\d+)',p.read_text()):
  q=R/path
  if not q.is_file() or int(num)>len(q.read_text(errors='replace').splitlines()):invalid.append((p.name,path,num))
check('Report source citations resolve to existing lines',not invalid,str(invalid))
# Revision-1's candidate flags must describe the same exact pairs as the
# written proposal. Equal aggregate counts alone cannot establish agreement.
proposal_module = O / 'revision-1' / 'gold_proposal.py'
if (O / 'revision-1' / 'gold-source-reviewed.csv').exists():
 import importlib.util
 spec = importlib.util.spec_from_file_location('analysis_gold_proposal', proposal_module)
 module = importlib.util.module_from_spec(spec)
 spec.loader.exec_module(module)
 proposal_result = module.validate_files(proposal_module.parent)
 check('Gold candidate supported pairs exactly match written proposal',
       proposal_result['supported_pair_sets_equal'], json.dumps(proposal_result, sort_keys=True))
branch=subprocess.check_output(['git','branch','--show-current'],cwd=R,text=True).strip()
check('Analysis is on its own local branch',branch.startswith('analysis-v3-'),'git branch --show-current')
report={'claim_label':'VERIFIED_SOURCE','checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_commit':BASE,'branch':branch,'checks':checks,'result':'PASS','scope':'Analysis integrity only. Discovery/workflow scripts and the 20 scheduler test cases were not executed.'}
(O/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS:',len(checks),'analysis integrity checks')
