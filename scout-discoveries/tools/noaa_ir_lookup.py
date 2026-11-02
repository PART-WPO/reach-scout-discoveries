#!/usr/bin/env python3
"""Offline, evidence-only NOAA Institutional Repository DOI check for NEW Scout drafts.

The full public NOAA IR collection is indexed by a separate GitHub Action.
A missing/stale/unavailable index does NOT mean IR? FALSE. Do not change
existing REACH items, metadata corrections, or published immutable batches.
"""
import hashlib
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
MANIFEST=ROOT/"scout-operations/noaa-ir/manifest.json"
DOI=re.compile(r"^10\.\d{4,9}/[^\s]+$",re.I)
IR_LINK=re.compile(r"^https://repository\.library\.noaa\.gov/view/noaa/(\d+)$")

def normalize_doi(value):
    s=str(value or "").strip().lower()
    s=re.sub(r"^https?://(?:dx\.)?doi\.org/","",s)
    s=re.sub(r"^doi:\s*","",s).strip()
    return s if DOI.fullmatch(s) else ""

def shard_for(doi):
    return hashlib.sha256(doi.encode("utf-8")).hexdigest()[0]

def trusted_index(root=ROOT):
    """Verify every shard's SHA and record-count before trusting any DOI.

    If index is missing, incomplete, or stale, treat as unavailable, never
    as proof that a DOI is not held in NOAA IR.
    """
    manifest=root/"scout-operations/noaa-ir/manifest.json"
    if not manifest.exists():return None
    m=json.loads(manifest.read_text(encoding="utf-8"))
    if m.get("schema")!="reach-scout-noaa-ir-doi-index-v1" or not m.get("complete"):
        raise ValueError("NOAA IR index not marked complete")
    shards=m.get("shards",[])
    if len(shards)!=16 or {x.get("prefix") for x in shards}!=set("0123456789abcdef"):
        raise ValueError("NOAA IR index missing expected 16 shards")
    result={}
    total=0
    for item in shards:
        rel=item.get("path","")
        if rel!=f"scout-operations/noaa-ir/shards/{item['prefix']}.json":
            raise ValueError("Unexpected NOAA IR index path")
        raw=(root/rel).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=item["sha256"]:
            raise ValueError("NOAA IR index checksum mismatch "+rel)
        payload=json.loads(raw)
        if payload.get("schema")!="reach-scout-noaa-ir-doi-shard-v1" or payload.get("prefix")!=item["prefix"]:
            raise ValueError("NOAA IR shard identity mismatch")
        records=payload.get("records",{})
        if len(records)!=item["record_count"]:raise ValueError("NOAA IR shard count mismatch")
        for doi,matches in records.items():
            if not normalize_doi(doi) or shard_for(doi)!=item["prefix"]:
                raise ValueError("Malformed NOAA IR indexed DOI")
            if not isinstance(matches,list) or not matches or not all(IR_LINK.fullmatch(str(url)) for url in matches):
                raise ValueError("Invalid NOAA IR official item URL")
            result[doi]=matches
        total+=len(records)
    if total!=m.get("distinct_dois"):raise ValueError("NOAA IR manifest DOI count mismatch")
    return {"manifest":m,"dois":result}

def new_output_gate(classification,existing_match,provenance):
    if classification not in {"NEW CANDIDATE","NEEDS INVESTIGATION"}:
        return False
    # Requiring an explicit completed *negative* REACH comparison prevents
    # an accidentally mislabeled NEW CANDIDATE from enriching a duplicate.
    if provenance.get("existing_reach_uid"):
        return False
    text=str(existing_match or "").strip().lower()
    return text.startswith((
        "no match", "no doi/normalized-title/url match",
        "not found in the verified", "not found after complete"
    ))

def enrich(fields,provenance,index=None):
    """Returns (safe copied fields, explanation). Does not mutate input.

    Exact unique DOI is required. For a missing match leave the IR fields
    completely unchanged (blank unless reviewer supplied them already).
    """
    out=dict(fields)
    if not new_output_gate(provenance.get("classification"),out.get("Existing REACH Match"),provenance):
        return out,"not_applicable_existing_or_unconfirmed_new_output"
    doi=normalize_doi(out.get("DOI"))
    if not doi:return out,"doi_missing_or_invalid"
    if index is None:return out,"noaa_ir_index_unavailable"
    hits=index["dois"].get(doi,[])
    if not hits:return out,"not_found_in_index_not_a_negative_determination"
    if len(hits)!=1:return out,"ambiguous_multiple_noaa_ir_records"
    url=hits[0]
    if not IR_LINK.fullmatch(url):
        raise ValueError("Untrusted NOAA IR URL")
    explicit=str(out.get("IR Repository URL") or "").strip()
    if explicit and explicit!=url:
        raise ValueError("Conflicting pre-existing NOAA IR link; do not overwrite")
    flag=str(out.get("IR?") or "").strip().upper()
    if flag and flag not in {"TRUE","YES"}:
        raise ValueError("Contradictory prior NOAA IR flag; do not overwrite")
    out["IR?"]="TRUE"
    out["IR Repository URL"]=url
    return out,"exact_doi_matched_official_noaa_ir_index"
