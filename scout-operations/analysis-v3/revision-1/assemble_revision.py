#!/usr/bin/env python3
"""INFERRED: Assemble follow-up analysis from saved public evidence; no network or operational writes."""
import pathlib,json,csv,hashlib,re,collections,urllib.parse,datetime,html,subprocess
O=pathlib.Path(__file__).resolve().parent;P=O.parent;R=P.parents[1];PREFIX='scout-operations/analysis-v3/revision-1/'
def dump(n,d):
 p=O/n
 if p.exists():raise ValueError('Refusing overwrite: '+str(p))
 p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
def load(n):return json.loads((O/n).read_text())
def rows(n):return list(csv.DictReader((P/n).open()))
def writecsv(n,rs):
 with (O/n).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
def normurl(v):
 v=str(v or '').strip();u=urllib.parse.urlsplit(v);host=(u.hostname or '').lower();path=urllib.parse.unquote(u.path).rstrip('/')
 if host in ['doi.org','dx.doi.org']:return 'doi:'+path.strip('/').lower()
 if host in ['zenodo.org','www.zenodo.org']:
  m=re.match(r'/(?:records?|record)/(\d+)',path)
  if m:return 'doi:10.5281/zenodo.'+m[1]
 if host=='github.com':path=path.lower().removesuffix('.git')
 return host+path
projection=json.loads((P/'reach-public-projection.json').read_text());catalog=[r for x in projection['parts'] for r in x['projected_records']];byid={r['Record ID']:r for r in catalog}
seeds=json.loads((P/'seed-ledger.json').read_text())['seeds'];doimap=collections.defaultdict(set)
for s in seeds:
 for d in s['seed_dois']:doimap[d].add(s['reach_record_id'])
resolution=load('doi-resolution-review.json')['records']
for r in resolution:
 if r['resolved_doi']:doimap[r['resolved_doi']].add(r['record_id'])
pilot=rows('pilot-seeds.csv');resolved={r['record_id']:r for r in resolution if r['resolved_doi']}
pilotstates=[{'record_id':r['record_id'],'original_stratum':r['stratum'],'current_doi_state':'newly_resolved' if r['record_id'] in resolved else ('previously_resolved' if r['dois'] else 'still_unresolved'),'resolved_doi':resolved.get(r['record_id'],{}).get('resolved_doi'),'source':PREFIX+'doi-resolution-review.json:1'} for r in pilot]
dump('pilot-strata-update.json',{'claim_label':'VERIFIED_SOURCE','pilot_size':40,'original_pilot_unchanged':True,'current_doi_states':dict(collections.Counter(r['current_doi_state'] for r in pilotstates)),'seeds':pilotstates,'interpretation':'INFERRED: Analyze strata separately; an unresolved query is not a negative discovery result.'})
# Source-review selected clear relationships, without asserting human approval or own-output award.
candidates=list(csv.DictReader((O/'artifact-first-gold-candidates.csv').open()));selected=[]
accepted_doc={('reach-000079','reach-000066'):'Author README explicitly tells users to cite this exact methods paper for this package; REACH also has the exact supporting code URL.',('reach-000087','reach-000085'):'Author README explicitly says the repository provides code and visualizations from the named paper.',('reach-000087','reach-000086'):'Author README explicitly says the repository provides code and visualizations from the named paper.',('reach-000076','reach-000075'):'Package README identifies the SoftwareX paper describing this exact HOST package under how to cite.',('reach-001076','reach-001071'):'Dataset native catalog identifies this exact paper in Publications; dataset title and scope describe its CFBM simulations and verification.',('reach-001077','reach-001072'):'Dataset native catalog identifies this exact paper in Publications; the dataset scope describes the study simulations.'}
for r in candidates:
 key=(r['artifact_record_id'],r['paper_record_id']);reason=None
 if r['evidence_class']=='EXPLICIT_TYPED_SUPPORT_RELATION':reason='Exact artifact metadata explicitly declares IsSupplementTo for the exact DOI associated with this REACH publication.'
 elif key in accepted_doc:reason=accepted_doc[key]
 if reason:
  selected.append({**r,'claim_tier':'supporting output of a named paper','agent_source_review':'RELATIONSHIP_SUPPORTED','review_reason':reason,'human_adjudication':'NOT_DETERMINED','freeze_status':'PROPOSED_REFERENCE_CASE_AWAITING_OWNER_RATIFICATION','own_artifact_award':'NOT_DETERMINED'})
writecsv('gold-source-reviewed.csv',selected)
dump('gold-rebuild-summary.json',{'claim_label':'VERIFIED_SOURCE','direction':'234 existing artifacts toward named papers','candidate_pairs':len(candidates),'candidate_artifacts':len({r['artifact_record_id'] for r in candidates}),'source_reviewed_relationship_pairs':len(selected),'source_reviewed_unique_artifacts':len({r['artifact_record_id'] for r in selected}),'source_reviewed_relation_basis':dict(collections.Counter(r['evidence_class'] for r in selected)),'human_adjudicated_pairs':0,'frozen_benchmark_activated':False,'source':PREFIX+'gold-source-reviewed.csv:1','interpretation':'INFERRED: This rebuild enlarges the source-supported control proposal; owner ratification, work-family grouping and a frozen version precede benchmarking. It still measures rediscovery, not recall of outputs missing from REACH.'})
# Full current public catalog manifest must match the earlier independently projected shards.
live=load('live-reach-manifest.json')['body'];old=json.loads((P/'reach-manifest.json').read_text())['body'];same=live==old
# Scout identity checking uses primary DOI/Output URL of SHA-verified active manifested batches and inbox.
scout=[];manifest=json.loads((R/'scout-discoveries/manifest.json').read_text());verified_scout=[]
for b in manifest['batches']:
 path=b['path'];raw=(R/path).read_bytes();assert hashlib.sha256(raw).hexdigest()==b['sha256'];verified_scout.append(path)
 for row in csv.DictReader(raw.decode('utf-8-sig').splitlines()):scout.append({'path':path,'doi':str(row.get('DOI','')).lower(),'output_url':row.get('Output URL','')})
for path in (R/'scout-discoveries/inbox').glob('*.csv'):
 for row in csv.DictReader(path.open()):scout.append({'path':str(path.relative_to(R)),'doi':str(row.get('DOI','')).lower(),'output_url':row.get('Output URL','')})
code414=load('datacite-probe.json')['body']['data']['attributes'];code687=load('noah-cited-version.json')['body']['data']['attributes']
parents414={r.get('relatedIdentifier','').lower() for r in code414.get('relatedIdentifiers',[]) if r.get('relationType')=='IsVersionOf'};parents687={r.get('relatedIdentifier','').lower() for r in code687.get('relatedIdentifiers',[]) if r.get('relationType')=='IsVersionOf'}
findings=[]
for rid,alias in [('reach-000014',['https://github.com/yiwenff/WUS-SR-data-descriptor']),('reach-000016',['https://doi.org/10.5281/zenodo.7145414','https://doi.org/10.5281/zenodo.6873384','https://doi.org/10.5281/zenodo.5777820'])]:
 keys={normurl(v) for v in alias};matches=[{'record_id':r['Record ID'],'output_type':r['Output Type'],'primary_url':r['Link to Output']} for r in catalog if normurl(r['Link to Output']) in keys];sm=[s for s in scout if normurl(s['output_url']) in keys or 'doi:'+s['doi'] in keys]
 findings.append({'claim_label':'VERIFIED_SOURCE','paper_record_id':rid,'artifact_urls_or_verified_family':alias,'current_catalog_manifest_matches_projected_snapshot':same,'exact_primary_record_matches':matches,'scout_primary_identity_matches':sm,'disposition':'POSSIBLE_STANDALONE_ARTIFACT_RECORD_MISS_REQUIRES_REVIEW' if not matches and same else 'HOLD_IDENTITY_CHECK','relationship_tier':'supporting output of a named paper','own_artifact_award':'NOT_DETERMINED','sources':[PREFIX+('snow-journal-fulltext.json:1' if rid=='reach-000014' else 'noah-journal-fulltext.json:1'),PREFIX+('snow-readme.json:1' if rid=='reach-000014' else 'noah-zenodo-native.json:1')],'finding':'Publisher Code availability explicitly links this repository; author README confirms figure-generation scripts and data.' if rid=='reach-000014' else 'Publisher cites version 6873384; native version metadata establishes the shared concept DOI with 7145414. Files contain code and data, but registry resource type is JournalArticle. Crossref funders for the paper are Korean; output-specific WPO funding is not established.','noah_version_family_verified':bool(parents414&parents687) if rid=='reach-000016' else None,'limits':'No title-only absence or funding eligibility asserted; no proposal staged and no catalog correction made.'})
dump('embedded-code-findings.json',{'claim_label':'VERIFIED_SOURCE','checked_public_scout_batch_count':len(verified_scout),'public_reach_record_count':len(catalog),'cases':findings})
# Import all active registry appearances from existing historical and monthly batches, deduplicating by DOI.
registry=collections.defaultdict(list);manifests=['api-discoveries/historical-crossref/manifest.json','api-discoveries/historical/manifest.json','api-discoveries/manifest.json'];manifestfacts=[]
for mpath in manifests:
 m=json.loads((R/mpath).read_text());count=0
 for b in m['batches']:
  if b.get('superseded'):continue
  path=b['path'];raw=(R/path).read_bytes();assert hashlib.sha256(raw).hexdigest()==b['sha256']
  import io
  for line,row in enumerate(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))),2):
   d=row.get('DOI','').strip().lower()
   if not d:continue
   registry[d].append({'source':f'{path}:{line}','source_file_sha256':b['sha256'],'award_identifiers':row.get('NOAA Award Number(s)',''),'output_type':row.get('Output Type'),'title':row.get('Title'),'source_run_id':row.get('Source Run ID'),'legacy_intake_scope':'Recorded source campaign; primary-only current attribution not automatically re-certified'});count+=1
 manifestfacts.append({'path':mpath,'source_sha256':m.get('spark_source_sha256'),'record_appearances_imported':count})
subjects=[]
for d,ap in sorted(registry.items()):
 ids=sorted(doimap.get(d,[]));subjects.append({'claim_label':'VERIFIED_SOURCE','subject_id':'doi:'+d,'doi':d,'campaign_memberships':['award_registry_recall']+(['reach_rediscovery'] if ids else []),'reach_publication_ids':ids,'public_identity_state':'EXACT_DOI_ASSOCIATION_WITH_EXISTING_PUBLICATION' if ids else 'NO_EXACT_PUBLICATION_DOI_ASSOCIATION_IDENTITY_CHECK_REQUIRED','source_appearances':ap,'source_method_status':'REGISTERED_INPUT_NOT_RESEARCH_COMPLETION','input_hash':hashlib.sha256(json.dumps(ap,sort_keys=True).encode()).hexdigest(),'attempts':None,'blocker_class':'legacy_complete_method_history_unknown','retry_after':None})
dump('registry-campaign-import.json',{'claim_label':'VERIFIED_SOURCE','unit':'Registry DOI identity; retains all intake appearances and exact REACH publication associations','subjects':subjects,'source_manifests':manifestfacts,'query_enumeration_completion':'NOT_DETERMINED','completion_reason':'Historical source universes differ from current SPARK snapshot and retained per-query page receipts do not prove current complete enumeration.','interpretation':'No exact publication DOI association is not a completed full-catalog novelty check; artifact primary identities and versions must still be checked.'})
# Campaign query receipt template includes zero-result/failed units absent from subject tables.
universe=load('award-campaign-universe.json');qs=[{'query_unit_id':provider+':'+award,'provider':provider,'primary_award':award,'status':'NOT_STARTED_BY_THIS_ANALYSIS','cursor':None,'terminal_page_evidence':None,'records_seen':None,'blocker_class':None,'retry_after':None} for award in universe['normalized_primary_awards'] for provider in ['crossref','datacite']]
dump('registry-campaign-run-template.json',{'claim_label':'INFERRED','campaign_id':'all-primary-awards-since-start','award_universe_source':PREFIX+'award-campaign-universe.json:1','planned_query_units':len(qs),'publication_window':'All available registry years for this primary award universe; current populated Year Funded begins in FY15','as_of_policy':'Freeze registry response observation times; later passes use update watermarks plus periodic reconciliation','query_units':qs,'completion':'NOT_DETERMINED; no full campaign launched'})
rawreceipts=[json.loads(f.read_text()) for f in (O/'receipts').glob('*.json')];ratelimits=[{'source':PREFIX+'receipts/'+hashlib.sha256(x['url'].encode()).hexdigest()+'.json:1','url':x['url'],'retry_after':x.get('headers',{}).get('Retry-After')} for x in rawreceipts if x['http_status']==429]
dump('followup-accounting.json',{'claim_label':'VERIFIED_SOURCE','unique_saved_request_urls':len(rawreceipts),'http_429_observations':len(ratelimits),'rate_limits':ratelimits,'actual_total_network_requests':'NOT_DETERMINED across the interrupted and resumed invocations; unique receipts are not a request counter','completed_invocation_accounting':load('revision-summary.json')['request_accounting'],'full_933_method_sweep_performed':False,'registry_award_sweep_performed':False,'registry_subjects_imported':len(subjects),'registry_subjects_with_exact_existing_publication_association':sum(bool(s['reach_publication_ids']) for s in subjects),'registry_subjects_requiring_further_identity_checks':sum(not s['reach_publication_ids'] for s in subjects)})
# Scope report captures old content preservation, PR identity and proposed separation condition.
changed=subprocess.check_output(['git','diff','--name-only','b21f3271c92ad1e7a4643104920bfb214c65b186'],cwd=R,text=True).splitlines();untracked=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=R,text=True).splitlines();allpaths=sorted(set(changed+untracked));orig=rows('source-files.csv');all_originals=all(hashlib.sha256((R/r['path']).read_bytes()).hexdigest()==r['sha256'] for r in orig)
previous_changed=subprocess.check_output(['git','diff','--name-only','0806a8878923f7674b264897fdd333ba378c250e','--','scout-operations/analysis-v3/'],cwd=R,text=True).splitlines();pr=load('pr-one-status.json')['body'];prfiles=load('pr-one-files.json')['body']
dump('scope-and-approval-check.json',{'claim_label':'VERIFIED_SOURCE','original_source_files_unchanged':all_originals,'previous_analysis_files_modified':previous_changed,'all_changes_under_analysis_v3':all(p.startswith('scout-operations/analysis-v3/') for p in allpaths),'local_change_file_count_before_this_receipt':len(allpaths),'local_changed_paths_before_this_receipt':allpaths,'open_prs':load('public-prs.json')['body'],'actual_github_pr_1':{'title':pr.get('title'),'state':pr.get('state'),'merged':pr.get('merged'),'paths':[r['filename'] for r in prfiles],'all_under_analysis_v3':all(r['filename'].startswith('scout-operations/analysis-v3/') for r in prfiles)},'formal_pr_approval_submitted':False,'policy_inventory_only_split_satisfied':False,'reason':'Current local analysis includes ledger artifacts. A policy/inventory PR needs a separate allowlisted diff; actual GitHub #1 is an unrelated merged setup PR.','ledger_pr_2':'HOLD: owner review of artifact-first gold and campaign amendment pending'})
print(json.dumps({'gold_source_reviewed':len(selected),'registry_subjects':len(subjects),'embedded_findings':[(r['paper_record_id'],len(r['exact_primary_record_matches']),len(r['scout_primary_identity_matches'])) for r in findings],'scope_preserved':all_originals,'rate_limits':len(ratelimits)},indent=2))
