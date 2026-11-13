#!/usr/bin/env python3
"""INFERRED: Read-only artifact-first evidence collection; writes new revision-1 artifacts only.
No operational imports, credentials, publication, approval or catalog edits.
"""
import concurrent.futures,csv,datetime,hashlib,html,json,re,threading,urllib.request,urllib.parse,urllib.error
from pathlib import Path
from gold_proposal import apply_source_review, read_csv
O=Path(__file__).resolve().parent;PREV=O.parent;R=PREV.parents[1];RECEIPTS=O/'receipts';RECEIPTS.mkdir(exist_ok=True)
from collections import defaultdict
url_locks=defaultdict(threading.Lock)
lock=threading.Lock();counts={'network_requests':0,'cached_receipts':0}
def write(n,d):
 p=O/n
 if p.exists():raise ValueError('New files only: '+str(p))
 p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def fetch(u):
 with url_locks[u]: return _fetch(u)
def _fetch(u):
 key=hashlib.sha256(u.encode()).hexdigest();p=RECEIPTS/(key+'.json')
 if p.exists():
  with lock:counts['cached_receipts']+=1
  return json.loads(p.read_text())
 status=None;body=None;headers={};final=u
 try:
  with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'NOAA-WPO-public-artifact-review/1.0','Accept':'application/json,text/plain,text/html'}),timeout=18) as r:
   status=r.status;raw=r.read(2500001);final=r.geturl();headers={k:r.headers[k] for k in ['Content-Type','ETag','Last-Modified','Retry-After'] if k in r.headers}
   if len(raw)>2500000:body={'error':'SOURCE_TOO_LARGE'}
   else:
    text=raw.decode('utf-8',errors='replace')
    try:body=json.loads(text)
    except ValueError:body=text
 except Exception as e:
  status=getattr(e,'code',None);body={'error':str(e)}
  if getattr(e,'headers',None):headers={k:e.headers[k] for k in ['Retry-After','Content-Type'] if k in e.headers}
 d={'claim_label':'VERIFIED_SOURCE','url':u,'final_url':final,'http_status':status,'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'headers':headers,'body':body}
 with lock:counts['network_requests']+=1
 p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
 return d
def source(d):return 'scout-operations/analysis-v3/revision-1/receipts/'+hashlib.sha256(d['url'].encode()).hexdigest()+'.json:1'
def doi(s):
 s=urllib.parse.unquote(str(s or '').strip());s=re.sub(r'^(?:doi:|https?://(?:dx\.)?doi\.org/)','',s,flags=re.I).rstrip('.,;)]}').lower()
 return s if re.fullmatch(r'10\.\d{4,9}/[^\s<>"\x27]+',s) else ''
def dois(s):return {d for v in re.findall(r'10\.\d{4,9}/[^\s<>"\x27\[\]{}]+',html.unescape(s),re.I) if (d:=doi(v))}
def normtitle(s):return re.sub(r'[^a-z0-9]','',html.unescape(str(s)).lower())
projection=json.loads((PREV/'reach-public-projection.json').read_text());allr=[r for p in projection['parts'] for r in p['projected_records']];art=[r for r in allr if r['Output Type'] in ['2','3']];pub=[r for r in allr if r['Output Type']=='1']
seed=json.loads((PREV/'seed-ledger.json').read_text())['seeds'];seedbyid={s['reach_record_id']:s for s in seed};bydoi={}
for s in seed:
 for d in s['seed_dois']:bydoi.setdefault(d,[]).append(s['reach_record_id'])
pubbyid={r['Record ID']:r for r in pub};pairs=[]
def artifact_check(a):
 u=a['Link to Output'];d=doi(u);parsed=urllib.parse.urlsplit(u);out={'claim_label':'VERIFIED_SOURCE','artifact_record_id':a['Record ID'],'artifact_title':a['Title'],'artifact_type':'code/software' if a['Output Type']=='2' else 'data','primary_url':u,'sources':[],'explicit_relations':[],'document_doi_mentions':[],'native_metadata_doi':None,'status':'NOT_DETERMINED'}
 if not d:
  z=re.search(r'zenodo.org/(?:records?|record)/(\d+)',u)
  if z:d='10.5281/zenodo.'+z[1]
  v=re.search(r'(?:doi%3A|doi:|doi/)(10\.[^&\s]+)',u,re.I)
  if v:d=doi(v[1])
 if d:
  q=fetch('https://api.datacite.org/dois/'+urllib.parse.quote(d,safe='/'));out['sources'].append(source(q))
  attrs=(q.get('body',{}).get('data',{}).get('attributes',{}) if isinstance(q.get('body'),dict) else {})
  if q['http_status']==200 and doi(attrs.get('doi'))==d:
   out.update(status='OFFICIAL_ARTIFACT_METADATA_OBSERVED',artifact_doi=d,resource_type=attrs.get('types'),funding_references=attrs.get('fundingReferences',[]),registry_title=attrs.get('titles'),descriptions=attrs.get('descriptions',[]))
   for rel in attrs.get('relatedIdentifiers',[]):
    target=doi(rel.get('relatedIdentifier'))
    if target:out['explicit_relations'].append({'target_doi':target,'relation':rel.get('relationType'),'target_resource_type':rel.get('resourceTypeGeneral'),'reach_publication_ids':bydoi.get(target,[]),'source':source(q)})
   text=' '.join(x.get('description','') for x in attrs.get('descriptions',[]))
   out['document_doi_mentions']=[{'doi':v,'reach_publication_ids':bydoi.get(v,[]),'source':source(q)} for v in sorted(dois(text)-{d})]
   out['native_metadata_doi']=d
  else:out.update(status='REGISTRY_SOURCE_NOT_AVAILABLE_OR_NOT_DATACITE',artifact_doi=d,registry_status=q['http_status'])
 elif parsed.netloc.lower()=='github.com':
  bits=parsed.path.strip('/').split('/')
  if len(bits)>=2:
   repo='/'.join(bits[:2]).removesuffix('.git');q=fetch('https://raw.githubusercontent.com/'+repo+'/HEAD/README.md');out['sources'].append(source(q))
   if q['http_status']==404:q=fetch('https://raw.githubusercontent.com/'+repo+'/HEAD/README.rst');out['sources'].append(source(q))
   if q['http_status']==200 and isinstance(q['body'],str):
    text=q['body'];out['status']='AUTHOR_README_OBSERVED';out['document_doi_mentions']=[{'doi':v,'reach_publication_ids':bydoi.get(v,[]),'source':source(q),'context':text[max(0,text.lower().find(v)-180):text.lower().find(v)+len(v)+180]} for v in sorted(dois(text))]
   else:out['status']='AUTHOR_README_UNAVAILABLE'
 else:
  q=fetch(u.replace('http://','https://',1));out['sources'].append(source(q));out['status']='NATIVE_PAGE_OBSERVED' if q['http_status']==200 else 'NATIVE_SOURCE_UNAVAILABLE'
  if q['http_status']==200 and isinstance(q['body'],str):
   text=q['body'];out['document_doi_mentions']=[{'doi':v,'reach_publication_ids':bydoi.get(v,[]),'source':source(q)} for v in sorted(dois(text))]
   # Page DOI is a locator, not a paper association.
   md=re.search(r'<meta[^>]*(?:name|property)=["\x27]citation_doi["\x27][^>]*content=["\x27]([^"\x27]+)',text,re.I)
   if md:out['native_metadata_doi']=doi(md[1])
 return out
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:reviews=list(pool.map(artifact_check,art))
write('artifact-side-review.json',{'claim_label':'VERIFIED_SOURCE','unit':'Existing code/data record, inspected from artifact toward paper','artifacts':reviews})
# Separate strong typed relations, generic citations and title clues; no human adjudication inferred.
strong={'IsSupplementTo','IsDocumentedBy','IsDescribedBy'}
for a in reviews:
 for rel in a['explicit_relations']:
  for rid in rel['reach_publication_ids']:
   pairs.append({'claim_label':'VERIFIED_SOURCE','artifact_record_id':a['artifact_record_id'],'artifact_title':a['artifact_title'],'paper_record_id':rid,'paper_doi':rel['target_doi'],'paper_title':pubbyid[rid]['Title'],'relation':rel['relation'],'evidence_class':'EXPLICIT_TYPED_SUPPORT_RELATION' if rel['relation'] in strong else 'EXPLICIT_RELATION_REQUIRES_ROLE_REVIEW','source':rel['source'],'human_adjudication':'NOT_DETERMINED','claim_tier':'supporting output of a named paper' if rel['relation'] in strong else 'unverified','gold_state':'CANDIDATE_NOT_FROZEN'})
 for mention in a['document_doi_mentions']:
  for rid in mention['reach_publication_ids']:
   if any(x['artifact_record_id']==a['artifact_record_id'] and x['paper_record_id']==rid and x['paper_doi']==mention['doi'] for x in pairs):continue
   pairs.append({'claim_label':'VERIFIED_SOURCE','artifact_record_id':a['artifact_record_id'],'artifact_title':a['artifact_title'],'paper_record_id':rid,'paper_doi':mention['doi'],'paper_title':pubbyid[rid]['Title'],'relation':'DOI mentioned in artifact documentation; relationship role NOT_DETERMINED','evidence_class':'DOCUMENT_DOI_MENTION_REQUIRES_REVIEW','source':mention['source'],'human_adjudication':'NOT_DETERMINED','claim_tier':'unverified','gold_state':'CANDIDATE_NOT_FROZEN'})
 # Explicit artifact title descriptions identify a named paper, but still do not adjudicate identity/version.
 for r in pub:
  title=normtitle(r['Title'])
  if len(title)>35 and title in normtitle(a['artifact_title']) and not any(x['artifact_record_id']==a['artifact_record_id'] and x['paper_record_id']==r['Record ID'] for x in pairs):
   pairs.append({'claim_label':'INFERRED','artifact_record_id':a['artifact_record_id'],'artifact_title':a['artifact_title'],'paper_record_id':r['Record ID'],'paper_doi':' | '.join(seedbyid[r['Record ID']]['seed_dois']),'paper_title':r['Title'],'relation':'Full publication title in artifact title','evidence_class':'TITLE_ASSOCIATION_REQUIRES_CONFIRMATION','source':'scout-operations/analysis-v3/reach-public-projection.json:1','human_adjudication':'NOT_DETERMINED','claim_tier':'unverified','gold_state':'CANDIDATE_NOT_FROZEN'})
# Typed relations are evidence, not proposal membership. Reuse only the
# specifically reasoned rows from the written source-review proposal.
proposal_path = O/'gold-source-reviewed.csv'
pairs = apply_source_review(pairs, read_csv(proposal_path) if proposal_path.exists() else [])
with (O/'artifact-first-gold-candidates.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(pairs[0]));w.writeheader();w.writerows(pairs)
# Resolve DOI-less publication records via native authoritative page meta; title search remains a candidate only.
unresolved=[s for s in seed if not s['seed_dois']]
def resolve(s):
 r=pubbyid[s['reach_record_id']];u=r['Link to Output'];out={'claim_label':'VERIFIED_SOURCE','record_id':r['Record ID'],'title':r['Title'],'primary_url':u,'status':'NOT_DETERMINED','resolved_doi':None,'sources':[],'title_search_candidates':[]}
 if u:
  q=fetch(u.replace('http://','https://',1));out['sources'].append(source(q))
  if q['http_status']==200 and isinstance(q['body'],str):
   text=q['body'];tags=re.findall(r'<meta\b[^>]*>',text,re.I);md=[];titles=[]
   for tag in tags:
    at=dict((k.lower(),html.unescape(v)) for k,_,v in re.findall(r'([\w:-]+)\s*=\s*(["\x27])(.*?)\2',tag,re.S))
    name=(at.get('name') or at.get('property') or '').lower()
    if name in ['citation_doi','dc.identifier.doi','dc.identifier'] and doi(at.get('content')):md.append(doi(at['content']))
    if name in ['citation_title','dc.title']:titles.append(at.get('content',''))
   if len(set(md))==1 and any(normtitle(t)==normtitle(r['Title']) for t in titles):out.update(status='RESOLVED_NATIVE_EXACT_DOI_AND_TITLE',resolved_doi=md[0])
 if out['resolved_doi'] is None:
  q=fetch('https://api.crossref.org/works?'+urllib.parse.urlencode({'query.title':r['Title'],'rows':3,'select':'DOI,title,type,published'}));out['sources'].append(source(q))
  body=q['body'];items=body.get('message',{}).get('items',[]) if isinstance(body,dict) else []
  for v in items:
   if any(normtitle(t)==normtitle(r['Title']) for t in v.get('title',[])):out['title_search_candidates'].append({'doi':v.get('DOI'),'title':v.get('title'),'type':v.get('type'),'identity':'NOT_DETERMINED: title-only result is not accepted as resolved identity'})
 return out
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:resolution=list(pool.map(resolve,unresolved))
write('doi-resolution-review.json',{'claim_label':'VERIFIED_SOURCE','rule':'Only native exact DOI metadata plus exact title accepted; title search alone remains unresolved','records':resolution})
# Collect public primary award identifiers and their encoded fiscal-year evidence.
q=fetch('https://raw.githubusercontent.com/PART-WPO/SPARK/main/agent-data/manifest.json');manifest=q['body'];awards=[];shards=[]
if q['http_status']==200 and isinstance(manifest,dict):
 for shard in manifest.get('awards',{}).get('files',[]):
  u='https://raw.githubusercontent.com/PART-WPO/SPARK/main/'+shard['path'];z=fetch(u)
  if z['http_status']!=200 or not isinstance(z['body'],str):continue
  raw=z['body'].encode();valid=hashlib.sha256(raw).hexdigest()==shard['sha256'];shards.append({'path':shard['path'],'sha256_verified':valid,'source':source(z)})
  if not valid:continue
  import io
  for row in csv.DictReader(io.StringIO(z['body'])):
   if row.get('Match Basis') in ['primary_noaa_award','primary_unparsed_identifier']:
    value=row.get('Award Number','');awards.append({'award':value,'encoded_fiscal_year':2000+int(m[1]) if (m:=re.search(r'\bNA(\d{2})',value)) else None,'source':source(z)})
write('public-primary-award-years.json',{'claim_label':'VERIFIED_SOURCE','manifest_source':source(q),'shards':shards,'primary_award_rows':awards,'minimum_encoded_fiscal_year':min((a['encoded_fiscal_year'] for a in awards if a['encoded_fiscal_year'] is not None),default=None),'meaning':'Fiscal year encoded in public primary NOAA identifiers; actual award start dates and completeness beyond this snapshot NOT_DETERMINED.'})
from collections import Counter
summary={'claim_label':'VERIFIED_SOURCE','artifacts_inspected':len(reviews),'artifact_source_outcomes':dict(Counter(a['status'] for a in reviews)),'artifact_first_candidate_pairs':len(pairs),'candidate_evidence_classes':dict(Counter(p['evidence_class'] for p in pairs)),'unique_artifacts_with_candidate_papers':len({p['artifact_record_id'] for p in pairs}),'human_adjudicated_pairs':0,'prior_confirmed_direct_url_pair_preserved_separately':1,'doi_less_records_checked':len(resolution),'native_dois_resolved':sum(bool(r['resolved_doi']) for r in resolution),'still_unresolved':sum(not r['resolved_doi'] for r in resolution),'records_with_title_only_doi_candidates':sum(bool(r['title_search_candidates']) for r in resolution),'request_accounting':counts,'method_scope':'Artifact metadata/README/native-page review and DOI-resolution checks only; not a full 933-seed deterministic sweep or registry award campaign.'}
write('revision-summary.json',summary);print(json.dumps(summary,indent=2),flush=True)
