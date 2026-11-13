#!/usr/bin/env python3
"""INFERRED: Reproducible offline analysis; reads pinned public files, writes only this folder.
Run from repository root. No repository modules are imported or executed. No network calls.
"""
import ast,csv,hashlib,json,re,subprocess,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
REL='scout-operations/analysis-v3/'
BASE_COMMIT='b21f3271c92ad1e7a4643104920bfb214c65b186'
def dump(name,obj): (OUT/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n')
def load(p): return json.loads((ROOT/p).read_text())
def sha(p): return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def normdoi(s):
 s=re.sub(r'^(?:https?://(?:dx\.)?doi.org/|doi:)','',str(s).strip(),flags=re.I).lower()
 return s if re.fullmatch(r'10\.\d{4,9}/\S+',s) else ''
def url(s): return str(s).strip().lower().rstrip('/')
def line(p,needle=''):
 lines=(ROOT/p).read_text().splitlines()
 return next((i for i,s in enumerate(lines,1) if needle and needle in s),1)
def cite(p,needle=''): return f'{p}:{line(p,needle)}'
def csvout(name,rows,cols=None):
 with (OUT/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=cols or list(rows[0]));w.writeheader();w.writerows(rows)
tracked=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE_COMMIT],cwd=ROOT,text=True).splitlines()
texts={p:(ROOT/p).read_text(errors='replace') for p in tracked if Path(p).suffix not in ['.xlsx']}
base=collections.defaultdict(list)
for p in tracked: base[Path(p).name].append(p)
refs=collections.defaultdict(list)
for p,t in texts.items():
 if Path(p).suffix not in ['.py','.yml','.gs','.js','.md']:continue
 for i,s in enumerate(t.splitlines(),1):
  for token in set(re.findall(r'[\w./-]+\.(?:py|json|csv|xlsx|yml|trigger)',s)):
   matches=[q for q in base.get(Path(token).name,[]) if q!=p]
   for q in matches:
    exact=q in s or len(matches)==1
    if not exact:continue
    ctx=' '.join(t.splitlines()[max(0,i-4):min(len(t.splitlines()),i+3)])
    direction='REFERENCE_DIRECTION_NOT_DETERMINED'
    if Path(p).suffix=='.md': direction='REFERENCE_DIRECTION_NOT_DETERMINED'
    elif re.search(r'git add|write_text|write_bytes|json.dump|to_csv|DictWriter|--output',ctx): direction='INFERRED_WRITER_OR_OUTPUT_REFERENCE'
    elif re.search(r'read_text|read_bytes|json.load|DictReader|sha256|--input|from |import |python |pytest|unittest',ctx):direction='INFERRED_READER_OR_CALLER'
    refs[q].append({'source':f'{p}:{i}','direction':direction,'text':s.strip()[:350]})
io=[];inventory=[];cards=['# Complete source inventory\n','VERIFIED_SOURCE: This inventory enumerates every file tracked at the pinned source commit. Analysis additions are excluded. Each file has a row in `inventory.csv`. Recommendations are INFERRED, not changes made.\n','INFERRED: Reader/writer lists use literal references and nearby source context. They are candidates for ownership review, not proof of execution. NOT_DETERMINED means no exact reader or writer could be established statically. Directory scans and computed paths can add dependencies; `code-io.json` preserves those operations.\n']
for p in tracked:
 suffix=Path(p).suffix;t=texts.get(p,'');purpose='';evidence=cite(p) if t else REL+'source-files.csv:'+str(tracked.index(p)+2)
 kind='reference or immutable evidence'
 if suffix=='.py':
  kind='Python test' if '/tests/' in p or Path(p).name.startswith('test_') else 'Python script'
  try:
   tree=ast.parse(t);doc=ast.get_docstring(tree)
   purpose=(doc.split('\n\n')[0].replace('\n',' ') if doc else ('Checks '+Path(p).stem.removeprefix('test_').replace('_',' ') if kind=='Python test' else Path(p).stem.replace('_',' ')))
   for n in ast.walk(tree):
    if isinstance(n,ast.Call):
     s=ast.get_source_segment(t,n) or ''
     if re.search(r'\b(?:open|read_text|read_bytes|write_text|write_bytes|load|dump|DictReader|DictWriter|add_argument|glob|rglob)\s*\(',s) and len(s)<1600:
      io.append({'claim_label':'VERIFIED_SOURCE','source':f'{p}:{n.lineno}','operation':s,'meaning':'Source expression only; runtime paths and actual execution NOT_DETERMINED.'})
  except SyntaxError:purpose='NOT_DETERMINED: parser could not inspect this file'
 elif suffix=='.yml':
  kind='GitHub workflow';purpose=next((s.split(':',1)[1].strip() for s in t.splitlines() if s.startswith('name:')),Path(p).stem.replace('-',' '))
 elif suffix=='.json':
  kind='state, memory, decision ledger or saved evidence'
  try:
   d=json.loads(t);purpose=(d.get('schema') or d.get('purpose') or d.get('description') or 'Saved public JSON evidence') if isinstance(d,dict) else 'Saved public list'
  except Exception:purpose='NOT_DETERMINED: JSON could not be parsed'
  declared=purpose
  name=Path(p).stem.replace('-',' ').replace('_',' ')
  if '/case-checkpoints/' in p:purpose='Saved decision checkpoint for this identity and revision'
  elif '/noaa-ir/shards/' in p:purpose='Part of the public NOAA repository DOI-to-record lookup index'
  elif '/metadata-cache/' in p:purpose='Saved official metadata response for reuse'
  elif '/reports/' in p:purpose='Saved '+name+' report; records observations rather than scheduling authority'
  elif '/research-memory/' in p:purpose='Shared '+name+' memory of prior public research'
  else:purpose=name.capitalize()+' state or evidence'
  purpose+=' (declared format: '+str(declared)+')'
 elif suffix=='.csv': purpose='Immutable published findings' if '/batches/' in p else ('Unpublished public candidate draft' if '/inbox/' in p else 'Public tabular input or audit')
 elif suffix=='.md':purpose=next((s.lstrip('# ').strip() for s in t.splitlines() if s.startswith('#')),'Policy or supporting explanation')
 else:purpose='Saved report, integration, trigger or reference asset'
 if kind=='Python test':rec='KEEP';why='Retain behavior checks during migration; review duplicates only after replacement passes.'
 elif suffix=='.yml':rec='CHANGE' if 'git push' in t else 'KEEP';why='Route writes through a reviewed branch and a shared scheduler.' if rec=='CHANGE' else 'Retain read-only checks; combine redundant invocations only after coverage review.'
 elif '/batches/' in p or '/reports/' in p or '/case-checkpoints/' in p or '/policy-archive/' in p or any(x in p for x in ['/historical-crossref-phase2/','/monthly-research/','/monthly-expansion-evidence/','/hourly-run-audits/','/research-leads/','/noaa-ir/','/identity-cache/','/tests/']) or suffix in ['.xlsx','.trigger']:rec='KEEP';why='Preserve source history and evidence; never turn snapshots into independent scheduling authorities.'
 elif suffix=='.json':rec='MERGE';why='Import evidence into shared ledger or derive as a view; preserve this source snapshot.'
 elif suffix=='.py':
  rec='MERGE' if any(x in Path(p).stem for x in ['select_','scorecard','reconcile_','build_coverage','build_candidate_queue','build_monthly_decision']) else 'KEEP'
  why='Unify overlapping scheduling/reporting responsibilities behind one ledger.' if rec=='MERGE' else 'Retain reusable validation, source collection or publication gate; adapt its ledger interface.'
 else:rec='KEEP';why='Preserve contract and public evidence; review documentation after ledger design is accepted.'
 rr=refs.get(p,[])
 inventory.append({'path':p,'kind':kind,'claim_label':'VERIFIED_SOURCE' if suffix!='.py' or 'NOT_DETERMINED' not in purpose else 'NOT_DETERMINED','purpose':str(purpose),'purpose_label':'INFERRED: English description derived from source; declared format/name is VERIFIED_SOURCE','source':evidence,'inputs_it_reads':(' | '.join(x['source']+' '+x['operation'][:240] for x in io if x['source'].startswith(p+':') and re.search(r'read_text|read_bytes|json.load|DictReader|\bopen\(',x['operation'])) or 'NOT_DETERMINED; see source references and computed path operations'),'outputs_it_writes':(' | '.join(x['source']+' '+x['operation'][:240] for x in io if x['source'].startswith(p+':') and re.search(r'write_text|write_bytes|json.dump|DictWriter',x['operation'])) or 'NOT_DETERMINED; see workflow git-add and source references'),'reads_or_calls_it':' | '.join(x['source'] for x in rr if 'READER' in x['direction']) or 'NOT_DETERMINED','writes_or_produces_it':' | '.join(x['source'] for x in rr if 'WRITER' in x['direction']) or 'NOT_DETERMINED','other_references':' | '.join(x['source'] for x in rr if x['direction']=='REFERENCE_DIRECTION_NOT_DETERMINED') or 'NOT_DETERMINED','dependency_label':'INFERRED; static references, not observed executions','recommendation':rec,'recommendation_label':'INFERRED','reason':why,'overlap_group':('scheduling/reporting' if rec=='MERGE' else 'preserved source or reusable gate')})
 if suffix in ['.py','.yml']:
  cards.append(f'\n## {p}\n\nINFERRED: Purpose: {purpose}. Source: `{evidence}`.\n\nINFERRED: {rec}. {why}\n\nINFERRED: Readers/callers: '+('; '.join(x['source'] for x in rr if 'READER' in x['direction']) or 'NOT_DETERMINED')+'. Writers/producers: '+('; '.join(x['source'] for x in rr if 'WRITER' in x['direction']) or 'NOT_DETERMINED')+'. Full operation evidence is in `code-io.json`; file references are in `dependency-references.json`.\n')
csvout('inventory.csv',inventory);dump('code-io.json',io);dump('dependency-references.json',dict(refs));(OUT/'inventory.md').write_text('\n'.join(cards))
# Public catalog projection is separately acquired and SHA-checked against its manifest.
projection=load(REL+'reach-public-projection.json');allrows=[];provenance={}
for part in projection['parts']:
 for r in part['projected_records']:
  allrows.append(r);provenance[r['Record ID']]={'source':cite(REL+'reach-public-projection.json',json.dumps(r['Record ID'])),'upstream_path':part['path'],'upstream_sha256':part['sha256']}
pubs=[r for r in allrows if r['Output Type']=='1'];artifacts=[r for r in allrows if r['Output Type'] in ['2','3']]
byid={r['Record ID']:r for r in pubs};byuid={r['REACH UID']:r for r in pubs};doimap=collections.defaultdict(set);dois_by_id=collections.defaultdict(set);doi_evidence=collections.defaultdict(list)
def associate(d,rid,src):
 if d and rid in byid:doimap[d].add(rid);dois_by_id[rid].add(d);doi_evidence[rid].append(src)
for r in pubs:
 for k in ['Link to Output','Publications','Journal Article Link']:
  d=normdoi(r[k]);associate(d,r['Record ID'],provenance[r['Record ID']]['source'])
# Existing NOAA IR index provides exact DOI-to-canonical URL association. No title-based matching.
urls=collections.defaultdict(set)
for r in pubs:
 for k in ['Link to Output','Publications','Journal Article Link']:
  if r[k]:urls[url(r[k])].add(r['Record ID'])
irm=load('scout-operations/noaa-ir/manifest.json')
for part in irm['shards']:
 assert sha(part['path'])==part['sha256']
 for d,links in load(part['path'])['records'].items():
  if len(links)!=1:continue
  for rid in urls.get(url(links[0]),[]):associate(d,rid,cite(part['path'],json.dumps(d)))
prior=collections.defaultdict(list)
for p in ['scout-operations/monthly-triage.json','scout-operations/historical-triage.json','scout-operations/historical-crossref-triage.json']:
 for entry in load(p).get('entries',[]):
  d=normdoi(entry.get('identity',''));m=entry.get('reach_match') or {};m=m if isinstance(m,dict) else {}
  rid=m.get('record_id') or m.get('reach_id');uid=m.get('reach_uid')
  if uid in byuid:rid=byuid[uid]['Record ID']
  if rid in byid and entry.get('status')=='already_in_reach':associate(d,rid,cite(p,json.dumps(entry.get('identity'))))
  for rid in doimap.get(d,[]):prior[rid].append({'source':cite(p,json.dumps(entry.get('identity'))),'recorded_status':entry.get('status'),'meaning':'Recorded original-output state; discovery methods NOT_DETERMINED from aggregate status.','source_sha256':sha(p)})
# Explicit recorded selections only; previews, schedules, checkpoints and reference mentions excluded.
selections=[];seen=set()
for p in sorted((ROOT/'scout-operations/reports/hourly-missions').glob('*.json')):
 rel=str(p.relative_to(ROOT));d=load(rel);event=d.get('mission_id')
 if not event:continue
 for field,track in [('selected_original_dois','original'),('selected_expansion_seed_dois','expansion')]:
  for value in d.get(field,[]):
   doi=normdoi(value);key=(event,doi,track)
   if not doi or key in seen:continue
   seen.add(key);selections.append({'claim_label':'VERIFIED_SOURCE','event_id':event,'doi':doi,'track':track,'source':cite(rel,json.dumps(value)),'source_sha256':sha(rel),'fingerprint':d.get('memory_source_fingerprint'),'method':'NOT_DETERMINED; selection does not prove a method attempt'})
for p in sorted((ROOT/'scout-operations/reports/bounded-expansion-research').glob('*.json')):
 rel=str(p.relative_to(ROOT));d=load(rel);doi=normdoi(d.get('seed_doi'));event=p.stem
 key=(event,doi,'expansion')
 if doi and key not in seen:seen.add(key);selections.append({'claim_label':'VERIFIED_SOURCE','event_id':event,'doi':doi,'track':'expansion','source':cite(rel,'"seed_doi"'),'source_sha256':sha(rel),'fingerprint':d.get('seed_expansion_fingerprint'),'method':'bounded official-source pass'})
dump('selection-events.json',selections)
sel_by_doi=collections.defaultdict(list)
for e in selections:sel_by_doi[e['doi']].append(e)
# Method attempts are imported only from explicit structured bounded reports, not keyword interpretation of prose.
methods=['award_search','related_identifier_sweep','full_text_link_scan','agent_review'];attempts=collections.defaultdict(lambda:collections.defaultdict(list))
for p in sorted((ROOT/'scout-operations/reports/bounded-expansion-research').glob('*.json')):
 rel=str(p.relative_to(ROOT));doc=load(rel);doi=normdoi(doc.get('seed_doi'))
 for rid in doimap.get(doi,[]):
  for q in doc.get('source_lookups',[]):
   if normdoi(q.get('doi'))!=doi:continue
   status=q.get('source_status');attempts[rid]['award_search'].append({'status':'observed' if status=='ok' else 'blocked','blocker_class':None if status=='ok' else 'source_access','source':cite(rel,'"source_lookups"'),'source_sha256':sha(rel),'observed_at':doc.get('observed_at_utc'),'input_hash':doc.get('seed_expansion_fingerprint'),'legacy_result':q,'scope':'Official provider award-metadata inspection only; not a complete award search.'})
  for check in doc.get('source_driven_discovery',{}).get('source_checks',[]):
   k=check.get('kind','');method='related_identifier_sweep' if k=='crossref_references' else ('full_text_link_scan' if k in ['publisher_article_html','noaa_ir_accepted_manuscript_pdf','noaa_ir_pdf','noaa_ir_manuscript_pdf','noaa_ir_accepted_manuscript'] else None)
   if method:
    ok=check.get('status')=='SOURCE_READ'
    attempts[rid][method].append({'status':'observed' if ok else 'blocked','blocker_class':None if ok else 'source_access','source':cite(rel,'"source_checks"'),'source_sha256':sha(rel),'observed_at':doc.get('observed_at_utc'),'input_hash':check.get('source_sha256'),'legacy_result':check,'scope':'Recorded source only; method completion NOT_DETERMINED.'})
graph=load('scout-operations/research-memory/crosslane-relationship-graph.json')
graph_seeds={n['doi'] for n in graph['nodes'] if n.get('public_reach_verified_existing')}
legacy_fallback=load('scout-operations/research-memory/expansion-fallback-ledger.json')['cases']
ledger=[]
for r in pubs:
 rid=r['Record ID'];ds=sorted(dois_by_id[rid]);events={e['event_id']:e for d in ds for e in sel_by_doi.get(d,[])};states={}
 for m in methods:
  aa=attempts[rid].get(m,[])
  states[m]={'status':aa[-1]['status'] if aa else 'NOT_DETERMINED','input_hash':None,'legacy_input_hashes':sorted({a['input_hash'] for a in aa if a['input_hash']}),'attempts':len(aa) if aa else None,'attempts_is_lower_bound':True,'blocker_class':aa[-1]['blocker_class'] if aa else 'legacy_method_history_unknown','retry_after':None,'retry_after_meaning':'NOT_DETERMINED: do not schedule automatically from this dry-run import.','completion_verified':False,'evidence':aa}
 observed=any(attempts[rid].values())
 record={'claim_label':'VERIFIED_SOURCE','seed_id':r['REACH UID'] or rid,'reach_record_id':rid,'title':r['Title'],'seed_url':r['Link to Output'],'seed_dois':ds,'existing_graph_expansion_seed':bool(set(ds) & graph_seeds),'legacy_scheduler_state':[{'doi':d,'recorded':legacy_fallback[d],'source':cite('scout-operations/research-memory/expansion-fallback-ledger.json',json.dumps(d))} for d in ds if d in legacy_fallback],'identity_source':provenance[rid],'doi_association_sources':sorted(set(doi_evidence[rid])),'input_hash':hashlib.sha256(json.dumps({'record':r,'policy':'analysis-v3-proposal-1'},sort_keys=True).encode()).hexdigest(),'input_hash_meaning':'INFERRED: snapshot hash for migration review; not a historical per-method request hash.','methods':states,'prior_original_state_evidence':prior[rid],'recorded_selection_events':list(events.values()),'recorded_selection_count':len(events),'reselected_in_recorded_events':len(events)>1,'import_class':'METHOD_OBSERVATIONS_IMPORTABLE' if observed else ('CONTEXT_ONLY_IMPORTABLE' if prior[rid] or events else 'NO_LINKED_WORK_FOUND'),'unreconstructable_reason':'Complete four-method request hashes, all attempt timestamps and terminal method evidence are not recorded together. No absence-of-work conclusion is made.'}
 ledger.append(record)
dump('seed-ledger.json',{'claim_label':'INFERRED','schema':'proposed-seed-ledger-v3-dry-run','source_commit':BASE_COMMIT,'seeds':ledger})
flat=[]
for x in ledger:
 row={k:x[k] for k in ['reach_record_id','seed_id','title','seed_url','input_hash','import_class','recorded_selection_count','reselected_in_recorded_events']};row['seed_dois']=' | '.join(x['seed_dois']);row['source']=x['identity_source']['source'];row['claim_label']='VERIFIED_SOURCE';row['method_interpretation']='INFERRED; only explicitly recorded observations imported'
 for m in methods:
  for k in ['status','input_hash','attempts','blocker_class','retry_after']:row[m+'_'+k]=x['methods'][m][k]
 flat.append(row)
csvout('seed-ledger.csv',flat)
# Gold: direct exact artifact URL in a publication plus separate code/data primary record.
gold=[];candidates=[]
def tn(s):return re.sub('[^a-z0-9]','',s.lower())
for r in pubs:
 for a in artifacts:
  direct=bool(a['Link to Output']) and url(a['Link to Output']) in {url(r['Code']),url(r['Data & Instruments'])}
  titled=len(tn(r['Title']))>35 and tn(r['Title']) in tn(a['Title'])
  if not (direct or titled):continue
  row={'claim_label':'VERIFIED_SOURCE' if direct else 'INFERRED','seed_record_id':r['Record ID'],'seed_uid':r['REACH UID'],'seed_title':r['Title'],'seed_dois':' | '.join(sorted(dois_by_id[r['Record ID']])),'artifact_record_id':a['Record ID'],'artifact_type':'code/software' if a['Output Type']=='2' else 'data','artifact_title':a['Title'],'artifact_url':a['Link to Output'],'relationship_basis':'Exact publication supporting URL equals separate artifact primary URL' if direct else 'Normalized full paper title appears in artifact title; source relation needs owner confirmation','seed_source':provenance[r['Record ID']]['source'],'artifact_source':provenance[a['Record ID']]['source'],'freeze_recommendation':'INFERRED: include as confirmed control' if direct else 'INFERRED: reserve; confirm paper-artifact relation and DOI families before freezing'}
  candidates.append(row)
  if direct:gold.append(row)
csvout('gold-candidates.csv',candidates);csvout('gold-confirmed.csv',gold)
excluded={x['seed_record_id'] for x in candidates};excluded_dois={d for rid in excluded for d in dois_by_id[rid]};excluded_awards={a.strip() for r in pubs if r['Record ID'] in excluded for a in r['Award Number(s)'].split(',') if a.strip()}
# Forty pilot seeds in four deterministic strata, apart from all gold candidates and their award contexts.
strata=collections.defaultdict(list)
for r in pubs:
 rid=r['Record ID'];ds=dois_by_id[rid];aw={a.strip() for a in r['Award Number(s)'].split(',') if a.strip()}
 if rid in excluded or ds & excluded_dois or aw & excluded_awards:continue
 s=('doi_with_recorded_work' if prior[rid] or any(sel_by_doi.get(d,[]) for d in ds) else 'doi_without_linked_work') if ds else ('no_doi_multiple_awards' if len(aw)>1 else 'no_doi_single_or_no_award')
 strata[s].append(r)
pilot=[];used_dois=set()
for s in ['doi_with_recorded_work','doi_without_linked_work','no_doi_multiple_awards','no_doi_single_or_no_award']:
 selected=0
 for r in sorted(strata[s],key=lambda r:hashlib.sha256(r['REACH UID'].encode()).hexdigest()):
  ds=dois_by_id[r['Record ID']]
  if ds & used_dois:continue
  used_dois.update(ds);pilot.append({'claim_label':'INFERRED','record_id':r['Record ID'],'seed_uid':r['REACH UID'],'title':r['Title'],'dois':' | '.join(sorted(ds)),'primary_url':r['Link to Output'],'stratum':s,'source':provenance[r['Record ID']]['source'],'reason':'Deterministic pilot selection, separate from every gold candidate, known DOI overlap and gold-candidate award context'});selected+=1
  if selected==10:break
csvout('pilot-seeds.csv',pilot)
# Retain all existing artifact records, plus explicit DOI research edges; no guessed artifact classification.
leads=[]
for a in artifacts:
 leads.append({'claim_label':'VERIFIED_SOURCE','artifact_id':a['REACH UID'],'artifact_record_id':a['Record ID'],'artifact_identity':a['Link to Output'],'artifact_type':'code/software' if a['Output Type']=='2' else 'data','named_paper_doi':None,'seed_id':None,'claim_tier':'unverified','claim_tier_label':'INFERRED: conservative attribution tier; catalog membership is separately verified','funding_award_observed_in_reach':a['Award Number(s)'],'artifact_own_award_evidence':None,'relationship_evidence':[],'in_reach':True,'status':'existing_public_record','input_hash':hashlib.sha256(json.dumps(a,sort_keys=True).encode()).hexdigest(),'attempts':None,'blocker_class':'output_level_award_not_revalidated','retry_after':None,'source':provenance[a['Record ID']]['source']})
# Explicit named paper support in saved public research notes; does not imply own award.
p='scout-operations/historical-crossref-phase2/2026-11-05-1426ET-gulf-stream-publisher-data-availability-seed-expansion.json';d=load(p)
for a in d['related_dataset_leads']:
 leads.append({'claim_label':'VERIFIED_SOURCE','artifact_id':'doi:'+a['doi'],'artifact_record_id':None,'artifact_identity':'https://doi.org/'+a['doi'],'artifact_type':'data','named_paper_doi':d['published_related_doi'].lower(),'seed_id':None,'claim_tier':'supporting output of a named paper','claim_tier_label':'INFERRED from explicit recorded publisher data-availability evidence; primary text not re-fetched','funding_award_observed_in_reach':None,'artifact_own_award_evidence':None,'relationship_evidence':d['evidence_urls'],'in_reach':'NOT_DETERMINED by this import','status':'relationship_observed_funding_unverified','input_hash':sha(p),'attempts':None,'blocker_class':'artifact_own_award_unverified','retry_after':None,'source':cite(p,json.dumps(a['doi']))})
dump('artifact-leads.json',{'claim_label':'INFERRED','schema':'proposed-artifact-leads-v3-dry-run','leads':leads})
csvout('artifact-leads.csv',[{**x,'relationship_evidence':' | '.join(x['relationship_evidence'])} for x in leads])
# Full workflow safety register, with exact commit/push/trigger source lines.
workflows=[]
for p in tracked:
 if not p.startswith('.github/workflows/'):continue
 t=texts[p];ls=t.splitlines();push=[f'{p}:{i}' for i,s in enumerate(ls,1) if re.search(r'\bgit push\b',s) and not s.lstrip().startswith('#')];commits=[f'{p}:{i}' for i,s in enumerate(ls,1) if re.search(r'\bgit commit\b',s)];crons=[s.strip() for s in ls if 'cron:' in s]
 workflows.append({'claim_label':'VERIFIED_SOURCE','workflow':p,'name':next((s[5:].strip() for s in ls if s.startswith('name:')),''),'commit_commands':' | '.join(commits),'push_commands':' | '.join(push),'explicit_main_target':'HEAD:main' in t,'checkout_main':'ref: main' in t or 'checkout -B main' in t,'declared_contents_write':bool(re.search(r'contents:\s*write',t)),'schedules':' | '.join(crons),'interpretation':'INFERRED: configured to write main' if push and ('HEAD:main' in t or 'ref: main' in t or 'branches: [main]' in t) else ('INFERRED: pushes current ref; inspect trigger and checkout' if push else 'No literal push command found; indirect behavior NOT_DETERMINED'),'recommendation':'INFERRED: reviewed pull request for generated changes; shared scheduler lock' if push else 'INFERRED: retain read-only verification'})
csvout('workflow-safety.csv',workflows)
# Source hashes pin every original asset, making the added analysis auditable.
csvout('source-files.csv',[{'claim_label':'VERIFIED_SOURCE','path':p,'sha256':sha(p),'bytes':(ROOT/p).stat().st_size} for p in tracked])
repeats=[{'claim_label':'VERIFIED_SOURCE','doi':d,'recorded_event_count':len({e['event_id'] for e in es}),'matched_seed_records':' | '.join(sorted(doimap[d])),'sources':' | '.join(e['source'] for e in es),'meaning':'Recorded selection recurrence only; unchanged method repetition NOT_DETERMINED'} for d,es in sorted(sel_by_doi.items()) if len({e['event_id'] for e in es})>1]
csvout('reselected-seeds.csv',repeats)
summary={'claim_label':'VERIFIED_SOURCE','source_commit':BASE_COMMIT,'tracked_files':len(tracked),'python_scripts_including_tests':sum(p.endswith('.py') for p in tracked),'workflows':len(workflows),'public_reach_records':len(allrows),'publication_seed_records':len(pubs),'existing_graph_verified_reach_expansion_dois':len(graph_seeds),'publication_seed_records_linked_to_existing_graph_seed':sum(x['existing_graph_expansion_seed'] for x in ledger),'distinct_resolved_seed_dois':sum(bool(v) for v in doimap.values()),'seed_records_without_resolved_doi':sum(not dois_by_id[r['Record ID']] for r in pubs),'seed_records_with_importable_method_observations':sum(x['import_class']=='METHOD_OBSERVATIONS_IMPORTABLE' for x in ledger),'seed_records_with_context_only':sum(x['import_class']=='CONTEXT_ONLY_IMPORTABLE' for x in ledger),'seed_records_without_linked_prior_work':sum(x['import_class']=='NO_LINKED_WORK_FOUND' for x in ledger),'seed_records_with_any_importable_prior_context':sum(x['import_class']!='NO_LINKED_WORK_FOUND' for x in ledger),'complete_four_method_histories_reconstructed':0,'seed_records_with_incomplete_four_method_history':len(pubs),'explicit_recorded_selection_events':len({e['event_id'] for e in selections}),'selection_doi_track_rows':len(selections),'distinct_selected_dois':len({e['doi'] for e in selections}),'distinct_dois_selected_in_multiple_events':len(repeats),'reselected_dois_matching_publication_seeds':sum(bool(doimap[r['doi']]) for r in repeats),'publication_seed_records_reselected_in_recorded_events':sum(x['reselected_in_recorded_events'] for x in ledger),'gold_confirmed_pairs':len(gold),'gold_candidate_pairs_including_reserves':len(candidates),'pilot_seeds':len(pilot),'artifact_lead_rows':len(leads),'workflows_with_literal_push':sum(bool(w['push_commands']) for w in workflows),'source':'build_analysis.py; see seed-ledger.json, selection-events.json, source-files.csv for row-level evidence','interpretation_label':'INFERRED: counts are reproducible over stated snapshot and strict import rules; missing observations do not prove no work.'}
dump('import-exceptions.json',{'claim_label':'VERIFIED_SOURCE','unmapped_graph_verified_reach_dois':[{'doi':d,'reason':'No strict publication-record mapping in this import','source':cite('scout-operations/research-memory/crosslane-relationship-graph.json',json.dumps(d))} for d in sorted(graph_seeds) if not doimap.get(d)],'publication_seeds_without_resolved_doi':[{'record_id':r['Record ID'],'reason':'No exact DOI in primary publication links or unique existing IR mapping; UID and public URL retained','source':provenance[r['Record ID']]['source']} for r in pubs if not dois_by_id[r['Record ID']]],'doi_associations_with_multiple_publication_records':[{'doi':d,'record_ids':sorted(ids),'interpretation':'INFERRED: potential same-work records; retain until identity/version review'} for d,ids in sorted(doimap.items()) if len(ids)>1]})
dump('import-summary.json',summary)
print(json.dumps(summary,indent=2))
