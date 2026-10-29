#!/usr/bin/env python3
"""Validate Scout metadata blocker ledger: max five distinct checks, one delayed retry."""
import json,re
from datetime import datetime,timezone
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'metadata-blockers.json'
d=json.loads(p.read_text())
assert d.get('schema')=='reach-scout-metadata-blockers-v1' and isinstance(d.get('entries'),list)
seen=set()
def dt(x):return datetime.fromisoformat(str(x).replace('Z','+00:00'))
for b in d['entries']:
    identity=str(b.get('identity',''))
    assert re.match(r'^(doi:10\.\d{4,9}/|url:https://)',identity,re.I)
    assert identity not in seen
    seen.add(identity)
    assert b.get('status') in {'blocked','retry_due','human_review','pending_hub_handoff','resolved','suppressed'}
    retry=b.get('retry_count',0)
    assert type(retry)==int and retry in (0,1)
    methods={0:set(),1:set()};times={0:[],1:[]}
    checks=b.get('attempts',[])
    assert isinstance(checks,list) and len(checks)<=10
    for a in checks:
        rnd=a['round'];method=a['method']
        assert rnd in (0,1) and rnd<=retry
        assert re.fullmatch(r'[a-z][a-z0-9_]{2,40}',method)
        assert method not in methods[rnd]
        methods[rnd].add(method)
        assert len(methods[rnd])<=5
        assert str(a.get('url','')).startswith('https://')
        times[rnd].append(dt(a['checked_at']))
    if retry:
        assert times[0] and times[1]
        assert (min(times[1])-max(times[0])).total_seconds()>=604800 or b.get('early_retry_reason')
    if b['status'] in {'blocked','retry_due'}:
        assert retry==0
        target=dt(b['next_retry_at'])
        if times[0]:assert (target-max(times[0])).total_seconds()>=604800
        if b['status']=='retry_due':assert target<=datetime.now(timezone.utc)
    if b['status'] in {'human_review','pending_hub_handoff'}:
        assert b.get('research_completed') is True and b.get('missing_fields') and b.get('funding_basis')
        assert any(str(u).startswith('https://') for u in b.get('evidence_urls',[]))
        assert b.get('metadata_recovery_exhausted') is True
        assert str(b.get('reviewer_question','')).strip()
        if b['status']=='human_review':
            assert re.fullmatch(r'scout-discoveries/batches/[A-Za-z0-9_.-]+[.]csv',str(b.get('scout_batch_path','')))
            assert b.get('hub_delivery_status')=='staged_for_review'
        else:
            # Human decision is ready but existing Hub import cannot represent
            # truthful missing metadata; no fabricated date and no fake delivery.
            assert b.get('hub_delivery_status')=='not_delivered'
            assert str(b.get('hub_intake_blocker','')).strip()
            assert not b.get('scout_batch_path')
print('Validated Scout metadata blockers',len(seen))
