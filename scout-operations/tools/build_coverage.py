import csv,json,re,hashlib
from datetime import datetime,timezone
from pathlib import Path
root=Path(__file__).resolve().parents[2]
manifest=json.loads((root/'api-discoveries/manifest.json').read_text())
ledger=json.loads((root/'scout-operations/monthly-triage.json').read_text())
assert manifest['schema']=='reach-monthly-api-discovery-feed-v1'
assert ledger['schema']=='reach-scout-monthly-triage-v1'
expected={}
for batch in manifest['batches']:
    path=batch['path']
    assert re.fullmatch(r'api-discoveries/batches/[A-Za-z0-9_.-]+[.]csv',path)
    raw=(root/path).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==batch['sha256']
    rows=list(csv.DictReader(raw.decode('utf-8-sig').splitlines()))
    assert len(rows)==batch['record_count']
    for row in rows:
        doi=re.sub(r'^(https?://(dx[.])?doi[.]org/|doi: *)','',row['DOI'],flags=re.I).lower()
        identity='doi:'+doi if doi else 'url:'+row['Output URL'].lower().split('#')[0].rstrip('/')
        k=batch['id']+'|'+identity
        assert k not in expected and identity not in ('doi:','url:')
        run=row['Source Run ID']
        m=re.search(r'(20[0-9]{2}-[0-9]{2})',run)
        expected[k]=m.group(1) if m else 'unknown'
terminal={'already_in_reach','forwarded_to_hub','metadata_update_forwarded','no_action','human_metadata_needed'}
counts={m:{'received':0,'checked':0,'already_in_reach':0,'forwarded_to_hub':0,'human_metadata_needed':0,'needs_research':0} for m in set(expected.values())}
for month in expected.values():counts[month]['received']+=1
seen=set();errors=[];checked=dupes=forwarded=stale=0
for e in ledger['entries']:
    k=e['source_batch_id']+'|'+e['identity']
    if k in seen or k not in expected:errors.append('Unknown or repeated ledger case '+k);continue
    seen.add(k)
    if e['status'] not in terminal|{'awaiting_research','investigating','needs_more_research'}:errors.append('Unsupported status '+k);continue
    if e['status'] in terminal:
        if not re.fullmatch('[a-f0-9]{40,64}',e.get('reach_snapshot','')) or not e.get('evidence_url','').startswith('https://'):
            errors.append('Missing research proof '+k);continue
        if e['status']=='already_in_reach' and not e.get('reach_match'):errors.append('Missing exact REACH match '+k);continue
        if e['status'] in {'forwarded_to_hub','metadata_update_forwarded'} and not e.get('scout_batch_path','').startswith('scout-discoveries/batches/'):
            errors.append('Missing reviewed batch '+k);continue
        if e['status']=='human_metadata_needed':
            # The Scout research round is closed, NOT an automatic Hub submission.
            if not (e.get('metadata_recovery_exhausted') is True and e.get('missing_evidence') and
                    e.get('reviewer_question') and e.get('verified_awards') and
                    e.get('human_handoff_status') in {'pending_hub_intake','staged_for_review'}):
                errors.append('Human metadata handoff missing completed research proof '+k);continue
            if e['human_handoff_status']=='pending_hub_intake':
                if not e.get('hub_intake_blocker') or e.get('scout_batch_path'):
                    errors.append('Pending Hub handoff has invalid delivery evidence '+k);continue
            elif not e.get('scout_batch_path','').startswith('scout-discoveries/batches/'):
                errors.append('Hub-visible human handoff missing reviewed batch '+k);continue
        checked+=1;counts[expected[k]]['checked']+=1
        if e['status']=='already_in_reach':dupes+=1;counts[expected[k]]['already_in_reach']+=1
        if e['status']=='human_metadata_needed':counts[expected[k]]['human_metadata_needed']+=1
        if e['status'] in {'forwarded_to_hub','metadata_update_forwarded'}:forwarded+=1;counts[expected[k]]['forwarded_to_hub']+=1
    else:
        try:
            t=datetime.fromisoformat(str(e.get('updated_at','')).replace('Z','+00:00'))
            if t.tzinfo and (datetime.now(timezone.utc)-t).days>=7:stale+=1
        except (TypeError,ValueError):pass
for c in counts.values():c['needs_research']=c['received']-c['checked']
result={'schema':'reach-scout-coverage-v1','repository':'PART-WPO/reach-scout-discoveries','received':len(expected),'checked':checked,'already_in_reach':dupes,'forwarded_to_hub':forwarded,'missing_from_ledger':len(set(expected)-seen),'stale_investigations':stale,'human_metadata_needed':sum(c['human_metadata_needed'] for c in counts.values()),'by_month':counts,'errors':errors}
(root/'scout-operations/coverage.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
if errors:raise ValueError('; '.join(errors[:5]))
print('Research coverage:',len(expected),'received,',checked,'completed')
