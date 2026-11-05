#!/usr/bin/env python3
"""Monthly Crossref index-change + bounded SPARK project-context discovery.

Research leads ONLY. Not a monthly original harvest, private Hub import,
new public Scout candidate, approved project attribution, or REACH output.
Only SPARK *primary* award numbers are allowed for structured searches.
"""
import argparse
import calendar
import datetime as dt
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[0]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scout-operations/tools"))
from harvest import fetch, spark_awards, match_crossref
from decision_pipeline import build_index, lookup, norm_doi, norm_title

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"scout-operations/index-and-project-discovery-leads.json"
SELECT="DOI,title,URL,type,created,updated,indexed,published-print,published-online,funder,relation"
CROSSREF="https://api.crossref.org/works"
NOAA_PRIMARY=re.compile(r"^NA\\d{2}(?:OAR|NWS)[A-Z0-9-]{7,}$",re.I)

def valid_noaa_primary(award):
    return bool(NOAA_PRIMARY.fullmatch(str(award or "").strip()))
STOP=set("and the of for in to on with by from a an at as based using through toward improving advance research development forecasting forecast weather climate observations modeling system systems project methods new applications".split())

def prev_month(today=None):
    today=today or dt.datetime.now(dt.timezone.utc).date()
    previous=today.replace(day=1)-dt.timedelta(days=1)
    return previous.strftime("%Y-%m")

def window(month):
    if not re.fullmatch(r"20\d{2}-(0[1-9]|1[0-2])",month):
        raise ValueError("Invalid normalized YYYY-MM research update window")
    year,mon=map(int,month.split("-"))
    last=calendar.monthrange(year,mon)[1]
    return f"{year:04d}-{mon:02d}-01",f"{year:04d}-{mon:02d}-{last:02d}"

def useful_tokens(text):
    return {w for w in re.findall(r"[a-z0-9]{4,}",str(text or "").lower()) if w not in STOP}

def project_search_plan(awards,max_projects=5):
    candidates=[]
    used_titles=set()
    for obj in awards:
        for title in obj.get("projects",[]):
            key=norm_title(title)
            if key in used_titles or len(title)<30 or len(useful_tokens(title))<3:
                continue
            used_titles.add(key)
            candidates.append({"project_title":title,"primary_spark_award":obj["award"],
                "program":(obj.get("programs") or ["Unspecified"])[0],
                "keywords":sorted(useful_tokens(title))[:10]})
    # Seed a small, auditable cross-program sample. This is NOT a claim of
    # representative recall or an exhaustive project discovery search.
    selected=[]
    programs=set()
    for c in sorted(candidates,key=lambda x:(x["program"],x["project_title"],x["primary_spark_award"])):
        if c["program"] not in programs:
            selected.append(c);programs.add(c["program"])
        if len(selected)>=max_projects:return selected
    for c in sorted(candidates,key=lambda x:(x["project_title"],x["primary_spark_award"])):
        if c not in selected:
            selected.append(c)
        if len(selected)>=max_projects:break
    return selected

def crossref_index_updates(award,start,end,max_pages=10,page_size=100):
    cursor="*"
    items=[]
    for page_num in range(max_pages):
        params={"filter":f"award.number:{award},from-index-date:{start},until-index-date:{end}",
                "rows":page_size,"cursor":cursor,"select":SELECT}
        response=fetch(CROSSREF,params=params)["message"]
        batch=response.get("items",[])
        items.extend(x for x in batch if match_crossref(x,award))
        if len(batch)<page_size:
            return items
        nxt=response.get("next-cursor")
        if not nxt or nxt==cursor:
            raise RuntimeError("Crossref incremental cursor stalled for "+award)
        cursor=nxt
    raise RuntimeError("Crossref incremental maximum pages exceeded for "+award+"; partial results cannot publish")

def query_project_titles(project,rows=5):
    # An award-free targeted bibliographic query is a LEAD, not proof of WPO.
    params={"query.bibliographic":project["project_title"],"rows":rows,"select":SELECT}
    response=fetch(CROSSREF,params=params)["message"]
    wanted=set(project["keywords"])
    result=[]
    for work in response.get("items",[]):
        titles=work.get("title") or []
        title=titles[0] if titles else ""
        overlap=wanted & useful_tokens(title)
        if len(overlap)>=2:
            result.append((work,sorted(overlap)))
    return result

def checked_lead(work,index,kind,scope,month,preprints):
    d=norm_doi(work.get("DOI"))
    if not d:
        raise ValueError("Malformed external DOI in index change or project search")
    titles=work.get("title") or []
    title=titles[0] if titles else ""
    u=str(work.get("URL") or "")
    identity=lookup(index,d,title,u)
    is_preprint=d in preprints or work.get("type")=="posted-content"
    return {"doi":d,"title":title,"output_url":u,
        "source_kind":kind,"evidence_url":"https://api.crossref.org/works/"+d,
        "crossref_publication_type":work.get("type"),
        "crossref_indexed_timestamp":work.get("indexed"),
        "crossref_updated_timestamp":work.get("updated"),
        "source_month":month,
        "public_identity_status":identity["status"],
        "recorded_public_matches":identity["matches"],
        "preprint_original_hold":is_preprint,
        "required_next_action":("TRACK_PREPRINT_OFFICIAL_JOURNAL_VERSION"
            if is_preprint else
            "VERIFY_EXISTING_REACH_OR_SCOUT_VERSION_NO_NEW_PROPOSAL"
            if identity["status"]!="NO_PUBLIC_IDENTITY_MATCH" else
            "CHECK_EXACT_SAME_PROJECT_WPO_PRIMARY_AWARD_BEFORE_REVIEW"),
        "funding_status":"STRUCTURED_AWARD_LEAD_NOT_PROJECT_VERIFIED"
            if kind=="CROSSREF_INDEX_UPDATE" else "PROJECT_TITLE_QUERY_ONLY_NOT_WPO_VERIFIED",
        "source_context":scope,
        "candidate_staged":False,"private_hub_import":"NOT_VERIFIED",
        "human_approval":"NOT_VERIFIED","public_reach_addition":"NOT_VERIFIED"}

def generate(month,*,pilot=False,awards=None,index=None,preprints=None,
             max_pages=10,max_projects=5):
    start,end=window(month)
    if awards is None:awards,source_sha=spark_awards()
    else:source_sha="TEST_ONLY_VERIFIED_SPARK_FIXTURE"
    if index is None:index=build_index(ROOT)
    if preprints is None:
        watch=json.loads((ROOT/"scout-operations/preprint-watchlist.json").read_text())
        preprints={norm_doi(e.get("preprint_doi")) for e in watch["entries"]}
    valid_awards=[a for a in awards if valid_noaa_primary(a.get("award"))]
    skipped_awards=[a["award"] for a in awards if not valid_noaa_primary(a.get("award"))]
    selected=valid_awards[:5] if pilot else valid_awards
    if not selected:raise ValueError("No valid, full NOAA primary award identifiers in SPARK catalogue")
    provenance={}
    by_key={}
    pages_complete=0
    for a in selected:
        award=a["award"]
        for work in crossref_index_updates(award,start,end,max_pages=max_pages):
            d=norm_doi(work.get("DOI"))
            key=("CROSSREF_INDEX_UPDATE",d)
            if key not in by_key:
                by_key[key]=checked_lead(work,index,"CROSSREF_INDEX_UPDATE",
                    {"matching_primary_spark_award_numbers":[award],
                     "same_project_wpo_link":"NOT_VERIFIED"},
                    month,preprints)
            else:
                ids=by_key[key]["source_context"]["matching_primary_spark_award_numbers"]
                if award not in ids:ids.append(award)
        pages_complete+=1
    projects=project_search_plan(valid_awards,max_projects)
    for project in projects:
        for work,overlap in query_project_titles(project):
            d=norm_doi(work.get("DOI"))
            key=("PROJECT_TITLE_SEARCH",d)
            context={"spark_project_title":project["project_title"],
                     "primary_spark_award_search_context":project["primary_spark_award"],
                     "matched_title_terms":overlap,
                     "same_project_wpo_link":"NOT_VERIFIED"}
            if key not in by_key:
                by_key[key]=checked_lead(work,index,"PROJECT_TITLE_SEARCH",context,month,preprints)
            else:
                # Distinct project associations are research HINTS only.
                old=by_key[key]["source_context"]
                old.setdefault("other_possible_project_contexts",[]).append(context)
    rows=sorted(by_key.values(),key=lambda x:(x["doi"],x["source_kind"]))
    counts={}
    for r in rows:
        key=r["source_kind"]+":"+r["public_identity_status"]
        counts[key]=counts.get(key,0)+1
    return {"schema":"reach-scout-incremental-index-project-pilot-v1",
        "source":"Crossref public REST, verified SPARK primary award catalogue",
        "run_mode":"PILOT" if pilot else "MONTHLY_COMPLETE_AWARD_COVERAGE",
        "month":month,"index_date_start":start,"index_date_end":end,
        "spark_primary_awards_in_catalog":len(awards),
        "valid_noaa_primary_awards_in_catalog":len(valid_awards),
        "non_normalized_primary_identifiers_skipped":len(skipped_awards),
        "non_normalized_primary_identifier_examples":skipped_awards[:12],
        "spark_primary_awards_queried":len(selected),
        "spark_source_sha256":source_sha,
        "project_context_queries":len(projects),
        "identity_index_fingerprint":index["source_fingerprint"],
        "counts":dict(sorted(counts.items())),"leads":rows,
        "complete_selected_awards":pages_complete==len(selected),
        "new_public_scout_candidates":0,
        "new_private_discovery_hub_imports":0,
        "new_reach_additions":0,
        "notes":"Index-date changes can reflect citation updates, not new publications. Publication dates are not inferred from indexing. Project-title search without funder acknowledgment is a low-confidence breadcrumb only; verify true same-project connection and duplicates before human review. This does not affect prior month original harvest or reviewer decisions."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--month",default=None)
    p.add_argument("--pilot",action="store_true")
    p.add_argument("--max-pages",type=int,default=10)
    p.add_argument("--max-projects",type=int,default=5)
    args=p.parse_args()
    month=args.month or prev_month()
    report=generate(month,pilot=args.pilot,max_pages=args.max_pages,max_projects=args.max_projects)
    stable=json.dumps(report,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    digest=hashlib.sha256(stable).hexdigest()[:20]
    rel=f"api-discoveries/index-update-runs/{month}-{digest}.json"
    path=ROOT/rel
    path.parent.mkdir(parents=True,exist_ok=True)
    rendered=json.dumps(report,indent=2,ensure_ascii=False)+"\n"
    if path.exists() and path.read_text()!=rendered:
        raise ValueError("Immutable monthly update evidence file mismatch")
    if not path.exists():path.write_text(rendered,encoding="utf-8")
    pointer={"schema":"reach-scout-index-project-leads-pointer-v1",
        "latest_path":rel,"latest_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
        "month":month,"pilot":args.pilot,"count":len(report["leads"]),
        "new_scout_candidates":0,"private_hub_import":"NOT_VERIFIED"}
    OUT.write_text(json.dumps(pointer,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"archive":rel,"month":month,"pilot":args.pilot,
                      "award_queries":report["spark_primary_awards_queried"],
                      "project_queries":report["project_context_queries"],
                      "leads":len(report["leads"]),"counts":report["counts"]},indent=2))

if __name__=="__main__":main()
