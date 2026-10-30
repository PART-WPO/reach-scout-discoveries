#!/usr/bin/env python3
"""Read-only DataCite date audit for historical and monthly REACH Scout API intake.

Source CSVs are immutable; output is a replaceable evidence snapshot and an Excel
comparison only. No changes to Scout triage, Hub, Smartsheet or public REACH.
Python stdlib only; all source files and batch checksums are validated.
"""
import argparse
import collections
import csv
import datetime as dt
import hashlib
from html.parser import HTMLParser
import io
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "api-discoveries" / "tools"))
import export_comparison_xlsx as excel

AUDITS = ROOT / "api-discoveries/date-audits"
REPORTS = ROOT / "api-discoveries/reports"
HIST_MANIFEST = ROOT / "api-discoveries/historical/manifest.json"
MONTHLY_MANIFEST = ROOT / "api-discoveries/manifest.json"
API_HOST = "api.datacite.org"
NATIVE_DOMAINS = {
    "designsafe-ci.org", "www.designsafe-ci.org",
    "datadryad.org", "zenodo.org", "figshare.com", "www.figshare.com",
    "repository.library.noaa.gov", "www.designsafe-ci.org",
}
HEADERS = ["DOI", "Original API Title", "NOAA Award(s)", "Output Type",
    "Proposed Parent Project", "DataCite Title (live)", "DataCite Published",
    "DataCite Publication Year", "DataCite Created (record)", "DataCite Registered (DOI)",
    "DataCite Updated (metadata)", "Typed Issued Dates", "Typed Available Dates",
    "Other Typed Dates", "Native Page", "Native Publication Date",
    "Native DOI Matched?", "Date Evidence Classification",
    "Verified REACH Date", "Provisional Date to Check", "Date Basis / Reviewer Question",
    "Related Version DOI(s)", "API Retrieval", "DataCite Evidence URL",
    "Source Batch"]
excel.WIDTHS.update({
    "Summary": [38, 94],
    "Date Reconciliation": [37, 66, 36, 24, 67, 67, 23, 19, 31, 31, 31, 39, 39, 52, 69, 26, 20, 35, 23, 25, 96, 55, 38, 67, 78],
    "Repository Breakdown": [35, 21, 24, 24, 24, 24, 22, 25],
    "Needs Reviewer Check": [37, 66, 25, 35, 25, 82, 60],
    "Read Me": [34, 112],
})

def iso_date(value):
    """Full literal ISO date only; never turn year/month into a fictional day."""
    s = str(value or "").strip()
    match = re.match(r"^(\d{4}-\d{2}-\d{2})(?:[Tt ].*)?$", s)
    if not match:
        return ""
    try:
        dt.date.fromisoformat(match.group(1))
    except ValueError:
        return ""
    return match.group(1)

def text(value):
    return str(value or "").strip()

def canonical_doi(value):
    x = text(value).lower()
    x = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", x)
    x = re.sub(r"^doi:\s*", "", x)
    if not re.fullmatch(r"10\.\d{4,9}/[^\s]+", x):
        raise ValueError("Invalid DOI: "+repr(value))
    return x

def checked_source(mode,month):
    p = HIST_MANIFEST if mode=="historical" else MONTHLY_MANIFEST
    manifest = json.loads(p.read_text(encoding="utf-8"))
    expected = "reach-historical-api-feed-v1" if mode=="historical" else "reach-monthly-api-discovery-feed-v1"
    if manifest.get("schema")!=expected:
        raise ValueError("Unexpected source manifest schema "+str(manifest.get("schema")))
    records={}
    rawsha=hashlib.sha256(p.read_bytes()).hexdigest()
    for b in manifest.get("batches", []):
        name=text(b.get("path"))
        prefix="api-discoveries/historical/batches/" if mode=="historical" else "api-discoveries/batches/"
        if not name.startswith(prefix) or not re.fullmatch(r"[\w.-]+\.csv", name[len(prefix):]):
            raise ValueError("Unsafe batch path "+name)
        if mode=="monthly" and month not in name:
            continue
        data=(ROOT/name).read_bytes()
        if hashlib.sha256(data).hexdigest()!=b.get("sha256"):
            raise ValueError("Source checksum mismatch: "+name)
        reader=csv.DictReader(io.StringIO(data.decode("utf-8-sig"),newline=""))
        rows=list(reader)
        if len(rows)!=b["record_count"]:
            raise ValueError("Source row count mismatch: "+name)
        for r in rows:
            reason=r.get("Scout Discovery Rationale","")
            if mode=="monthly":
                api=(re.search(r"(?im)^API provenance:\s*([^\r\n]+)",reason) or [None,""])[1]
                if "datacite" not in api.lower():
                    continue
            doi=canonical_doi(r["DOI"])
            if doi in records:
                previous=records[doi]
                if previous["Title"]!=r["Title"]:
                    raise ValueError("Conflicting title for same DOI in "+name)
                continue
            r["_source_batch"]=name
            records[doi]=r
    if mode=="historical" and len(records)!=manifest.get("candidate_rows"):
        raise ValueError("Historical DOI count does not match immutable source manifest")
    return dict(sorted(records.items())),rawsha

class NativeMetadata(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta={}
        self.jsonld=[]
        self.in_ld=False
        self.block=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=="meta":
            key=text(a.get("name") or a.get("property")).lower()
            if key and a.get("content"):
                self.meta.setdefault(key,[]).append(text(a["content"]))
        if tag=="script" and a.get("type","").lower().startswith("application/ld+json"):
            self.in_ld=True
            self.block=[]
    def handle_data(self,value):
        if self.in_ld and sum(map(len,self.block))<150000:
            self.block.append(value)
    def handle_endtag(self,tag):
        if tag=="script" and self.in_ld:
            try:self.jsonld.append(json.loads("".join(self.block)))
            except (ValueError,TypeError):pass
            self.in_ld=False
            self.block=[]

def native_date(raw,doi):
    """Accept a native date only with an exact DOI in page-level metadata."""
    p=NativeMetadata()
    p.feed(raw)
    validids=p.meta.get("citation_doi",[])+p.meta.get("dc.identifier",[])
    allvalues=[]
    def walk(node):
        if isinstance(node,dict):
            ids=node.get("identifier") or node.get("sameAs") or node.get("@id") or []
            for v in (ids if isinstance(ids,list) else [ids]):
                if isinstance(v,dict):v=v.get("value","")
                try:
                    if canonical_doi(v)==doi:
                        allvalues.extend([node.get("datePublished",""),node.get("dateCreated","")])
                except ValueError:pass
            for x in node.values():walk(x)
        elif isinstance(node,list):
            for x in node:walk(x)
    for obj in p.jsonld:walk(obj)
    matched=any((lambda v: canonical_doi(v)==doi)(v) for v in validids if re.fullmatch(r"(?:doi:|https?://(?:dx\.)?doi\.org/)?10\.\d{4,9}/[^\s]+",v,re.I))
    if matched:
        allvalues+=p.meta.get("citation_publication_date",[])+p.meta.get("dc.date.issued",[])
    dates=sorted({iso_date(x) for x in allvalues if iso_date(x)})
    return bool(matched or dates),dates

def safe_http(url,expected_host,max_bytes):
    u=urllib.parse.urlsplit(url)
    if u.scheme!="https" or u.hostname not in expected_host or u.username or u.password or u.port:
        raise ValueError("Unapproved source host")
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,req,fp,code,msg,headers,newurl):
            raise urllib.error.HTTPError(req.full_url,code,"Redirect not followed",headers,fp)
    opener=urllib.request.build_opener(NoRedirect())
    req=urllib.request.Request(url,headers={"Accept":"application/json, text/html;q=0.8","User-Agent":"REACH-Scout-Date-Audit/1.0 (public research metadata)"})
    with opener.open(req,timeout=16) as response:
        if response.status!=200:raise RuntimeError("HTTP "+str(response.status))
        blob=response.read(max_bytes+1)
        if len(blob)>max_bytes:raise ValueError("Source exceeds byte limit")
        return blob.decode("utf-8",errors="replace"),response.headers.get("content-type","")

def api_record(doi):
    url="https://api.datacite.org/dois/"+urllib.parse.quote(doi,safe="/")
    for attempt in range(3):
        try:
            raw,_=safe_http(url,{API_HOST},900000)
            obj=json.loads(raw)["data"]
            if canonical_doi(obj["id"])!=doi:
                raise ValueError("API returned wrong DOI identity")
            return obj["attributes"],"ok"
        except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError,OSError,ValueError,KeyError,TypeError,RuntimeError) as error:
            message=str(error)[:135]
            if attempt<2 and any(x in message for x in ("429","500","502","503","504","timed out")):
                time.sleep(1+attempt*2)
                continue
            return None,"unavailable: "+message
    return None,"unavailable"

def recorded_dates(a):
    dated=collections.defaultdict(list)
    for obj in (a.get("dates") or []):
        label=text(obj.get("dateType")).lower()
        if label:
            dated[label].append(text(obj.get("date")))
    return {k:sorted(set(v)) for k,v in dated.items()}

def date_recommendation(a,doi,try_native=True):
    """Make no auto-claim of a first-publication date based on DOI record created."""
    typed=recorded_dates(a)
    issued=sorted({iso_date(x) for x in typed.get("issued",[]) if iso_date(x)})
    available=sorted({iso_date(x) for x in typed.get("available",[]) if iso_date(x)})
    issued_pub=iso_date(a.get("published")) if issued else ""
    source_dates=sorted(set(issued+available+([issued_pub] if issued_pub else [])))
    created=iso_date(a.get("created"))
    registered=iso_date(a.get("registered"))
    pub=iso_date(a.get("published"))
    nativeurl=text(a.get("url"))
    native_seen=False
    native_dates=[]
    native_note="not checked"
    if try_native and nativeurl:
        u=urllib.parse.urlsplit(nativeurl)
        if u.scheme=="https" and u.hostname in NATIVE_DOMAINS and not u.username and not u.password:
            try:
                raw,ctype=safe_http(nativeurl,NATIVE_DOMAINS,400000)
                if "html" in ctype.lower() or raw.lstrip().startswith("<"):
                    native_seen,native_dates=native_date(raw,doi)
                    native_note="exact DOI matched" if native_seen else "no exact DOI match in page metadata"
                else:native_note="not an HTML page"
            except Exception as error:
                native_note="unavailable: "+str(error)[:100]
        else:native_note="host unsupported for native extraction"
    else:native_note="native check off / no landing URL"
    verified=""
    candidate=""
    basis=""
    status=""
    if len(source_dates)>1 and len(set(source_dates))>1:
        # Different Issued/Available dates can be legitimate (e.g. embargo).
        # Do not choose between them without context.
        status="conflicting_typed_dates"
        basis="Different exact Issued/Available dates. Check public release semantics and versions."
    elif len(native_dates)>1:
        status="conflicting_native_dates"
        basis="Native page contains multiple exact publication dates for this DOI."
    elif len(native_dates)==1:
        d=native_dates[0]
        if source_dates and d not in source_dates:
            status="conflicting_api_native"
            candidate=d
            basis="Native DOI-matched date differs from DataCite typed date; review versions/publication basis."
        else:
            status="verified_native_exact_doi"
            verified=d
            basis="Exact DOI matched to machine-readable native publication date; confirm first-publication version for REACH."
    elif source_dates:
        status="structured_date_needs_native"
        candidate=source_dates[0]
        basis="DataCite typed Issued/Available full date; no independent DOI-matched native publication date verified."
    elif pub and not issued:
        status="published_fulldate_untyped"
        candidate=pub
        basis="DataCite published supplied a full date, but typed Issued information missing; confirm source semantics."
    elif created or registered:
        status="doi_record_timestamp_only"
        candidate=registered or created
        basis="Only DataCite DOI registration/record creation date has full precision; NOT confirmed first public release."
    else:
        status="year_only_or_unknown"
        basis="No supported exact date; retain year/partial values and request human assessment."
    related=[]
    for item in a.get("relatedIdentifiers") or []:
        relation=text(item.get("relationType"))
        if relation.lower() in ("isversionof","hasversion","isnewversionof","ispreviousversionof","isidenticalto","ispartof","haspart"):
            related.append(relation+": "+text(item.get("relatedIdentifier")))
    return {
        "issued_dates":issued,"available_dates":available,"all_typed_dates":typed,
        "published":text(a.get("published")),"publication_year":text(a.get("publicationYear")),
        "created":text(a.get("created")),"registered":text(a.get("registered")),"updated":text(a.get("updated")),
        "native_url":nativeurl,"native_dates":native_dates,"native_identity_match":native_seen,
        "native_check":native_note,"status":status,"verified_date":verified,"provisional_date":candidate,
        "reason":basis,"related_versions":related,
    }

def build(mode,month,offline=False,native=True):
    source,manifestsha=checked_source(mode,month)
    if mode=="monthly" and not source:
        print("No monthly DataCite records yet; no report generated for",month)
        return None
    suffix="historical-2026-10-28" if mode=="historical" else "monthly-"+month
    jsonout=AUDITS/(suffix+".json")
    filename=("REACH_DataCite_Date_Reconciliation_Historical_2026-10-28.xlsx"
             if mode=="historical" else "REACH_DataCite_Date_Reconciliation_"+month+".xlsx")
    xlsxout=REPORTS/filename
    previous={}
    if jsonout.exists():
        old=json.loads(jsonout.read_text(encoding="utf-8"))
        previous={r["doi"]:r for r in old.get("records",[])}
    results=[]
    for i,(doi,src) in enumerate(source.items(),1):
        entry={"doi":doi,"original_title":src.get("Title",""),"award_numbers":src.get("NOAA Award Number(s)",""),
            "output_type":src.get("Output Type",""),"proposed_parent":src.get("Proposed Project Title",""),
            "source_batch":src["_source_batch"],"api_evidence_url":"https://api.datacite.org/dois/"+doi}
        a=None
        result="offline"
        if not offline:
            a,result=api_record(doi)
        if a:
            findings=date_recommendation(a,doi,try_native=native)
            entry.update(findings)
            entry["data_title"]=(a.get("titles") or [{}])[0].get("title","")
            entry["retrieval"]="live"
        elif doi in previous and previous[doi].get("retrieval") in ("live","prior_success_preserved"):
            entry.update({k:v for k,v in previous[doi].items() if k not in entry})
            entry["retrieval"]="prior_success_preserved"
            entry["api_failure"]=result
        else:
            entry.update({"status":"api_unavailable","verified_date":"","provisional_date":"","published":"",
                "publication_year":"","created":"","registered":"","updated":"","all_typed_dates":{},
                "issued_dates":[],"available_dates":[],"native_url":"","native_dates":[],
                "native_identity_match":False,"native_check":"not checked",
                "reason":"Could not retrieve DataCite DOI; absence of retrieved metadata is NOT evidence that no date exists.",
                "related_versions":[],"data_title":"","retrieval":"unavailable","api_failure":result})
        results.append(entry)
        if i%25==0:print("Date audit",i,"/",len(source),flush=True)
    counts=collections.Counter(x["status"] for x in results)
    groups=collections.defaultdict(list)
    for row in results:groups[row["doi"].split("/")[0]].append(row)
    def datecell(d):
        return "; ".join(f"{k}: {', '.join(v)}" for k,v in sorted(d.items()) if k not in {"issued","available"})
    sheet=[HEADERS]
    for r in results:
        sheet.append(["https://doi.org/"+r["doi"],r["original_title"],r["award_numbers"],
            excel.KIND.get(r["output_type"],r["output_type"]),r["proposed_parent"],r.get("data_title",""),
            r["published"],r["publication_year"],r["created"],r["registered"],r["updated"],
            "; ".join(r["issued_dates"]),"; ".join(r["available_dates"]),datecell(r["all_typed_dates"]),
            r["native_url"],"; ".join(r["native_dates"]),"Yes" if r["native_identity_match"] else "No",
            r["status"],r["verified_date"],r["provisional_date"],r["reason"],
            "; ".join(r["related_versions"]),r["retrieval"],r["api_evidence_url"],r["source_batch"]])
    problems=[["DOI","Title","Award Number(s)","Date Category","Suggested Date","Why Reviewer Should Check","DataCite Evidence URL"]]
    for r in results:
        if r["status"]!="verified_native_exact_doi":
            problems.append(["https://doi.org/"+r["doi"],r["original_title"],r["award_numbers"],
                r["status"],r["provisional_date"],r["reason"],r["api_evidence_url"]])
    repo_rows=[["DOI Prefix","Original DOIs","Native-verified exact","Structured date pending",
            "Timestamp-only","Year/unknown","Conflicts","API inaccessible"]]
    for p,rows in sorted(groups.items(),key=lambda x:(-len(x[1]),x[0])):
        c=collections.Counter(x["status"] for x in rows)
        repo_rows.append([p,len(rows),c["verified_native_exact_doi"],
            c["structured_date_needs_native"]+c["published_fulldate_untyped"],
            c["doi_record_timestamp_only"],c["year_only_or_unknown"],
            sum(v for k,v in c.items() if k.startswith("conflicting")),
            c["api_unavailable"]])
    summary=[
        ["REACH DATACITE DATE RECONCILIATION","Evidence audit only; no updates to original API, Scout, Hub or REACH"],
        ["Cohort",("Historical 2026-10-28" if mode=="historical" else "Monthly "+month)],
        ["Original DataCite DOI records",len(source)],
        ["Live DataCite DOI fetches successful",sum(r["retrieval"]=="live" for r in results)],
        ["Previous successful snapshots retained after fetch errors",sum(r["retrieval"]=="prior_success_preserved" for r in results)],
        ["DataCite DOI fetches unavailable",counts["api_unavailable"]],
        ["Exact date supported by DOI-matched native page metadata",counts["verified_native_exact_doi"]],
        ["Typed Issued/Available exact date needs independent native verification",counts["structured_date_needs_native"]],
        ["Published full date lacks typed context",counts["published_fulldate_untyped"]],
        ["DOI created/registered date only — candidate, not publication",counts["doi_record_timestamp_only"]],
        ["Year-only/other unresolved",counts["year_only_or_unknown"]],
        ["Conflicting dates requiring individual review",sum(v for k,v in counts.items() if k.startswith("conflicting"))],
        ["Original source manifest SHA-256",manifestsha],
        ["DataCite date semantics","created = DOI record created; registered = DOI became registered; published = Issued or fallback publication year; updated = metadata change"],
        ["REACH publication dates modified","NONE — all proposed dates remain separate, no automated approval"],
    ]
    notes=[
        ["Field / status","Meaning"],
        ["Verified REACH Date","Full date on native repository machine-readable metadata with exact DOI identity. Still verify output/version and eligibility before insertion."],
        ["Structured date pending","Typed DataCite Issued or Available full date exists, but independent native DOI-level evidence was not extracted. The candidate is not auto-published."],
        ["Provisional Date","DataCite created/registered is NOT first publication; it is just a suggested date to compare with native source. Dates can predate repository publication."],
        ["Publication Year","Retain 2025 as 2025 when exact month/day is not confirmed. Never synthesize 2025-01-01."],
        ["DataCite Published","May be a year-only value; based on Issued date if present, otherwise publicationYear (DataCite documentation)."],
        ["Native checks","Read only allowlisted repository HTML; only DOI-matched citation metadata or DOI-specific JSON-LD date counts. Dynamic pages, login barriers and API-only landing pages remain unresolved."],
        ["Conflicts","Different full Issued/Available dates can be reasonable, e.g. embargo; never silently pick earliest or latest. Version DOI relationships also require review."],
        ["Date types","An observation-period, submission, acceptance, last-updated or DOI registration date is not a substitute for the first public release."],
        ["Original catalog metadata","Title, output type, award and parent are taken from the original checksum-verified DataCite intake; no overwrites."],
        ["Reviewer action","This sheet is evidence for Scout or a human reviewer, not a Discovery Hub intake, decision, Smartsheet update or REACH publication."],
        ["API failure","Failed fetch is shown explicitly. A previously successful snapshot is retained with an access-failure note, not described as a live result."],
        ["DesignSafe example","10.17603/ds2-58ft-kp27: compare created 2025-04-10 with a verified DesignSafe publication date and exact version; the existing parent reach-000816 raises an independent duplicate/eligibility question."],
        ["Source docs","https://support.datacite.org/docs/what-is-the-difference-between-the-created-and-registered-date-in-the-datacite-rest-api"],
    ]
    AUDITS.mkdir(parents=True,exist_ok=True);REPORTS.mkdir(parents=True,exist_ok=True)
    output={"schema":"reach-datacite-date-reconciliation-v1","cohort":suffix,
        "source_manifest_sha256":manifestsha,"original_dois":len(source),
        "status_counts":dict(sorted(counts.items())),"records":results,
        "policy":"Read-only. Dates are suggestions/evidence only; no automatic REACH date, reviewer decision or CSV change."}
    newjson=json.dumps(output,indent=2,ensure_ascii=False,sort_keys=True)+"\n"
    if not jsonout.exists() or jsonout.read_text(encoding="utf-8")!=newjson:
        jsonout.write_text(newjson,encoding="utf-8")
    # Existing exporter intentionally rejects changed files (immutable monthly
    # source reports). This date audit is explicitly refreshable, so rebuild.
    if xlsxout.exists():xlsxout.unlink()
    excel.make_xlsx(xlsxout,{
        "Summary":summary,"Date Reconciliation":sheet,
        "Repository Breakdown":repo_rows,"Needs Reviewer Check":problems,"Read Me":notes
    })
    import zipfile
    with zipfile.ZipFile(xlsxout) as z:
        if z.testzip():raise ValueError("Generated XLSX failed ZIP integrity")
    print(json.dumps({"mode":mode,"cohort":suffix,"records":len(results),
        "counts":dict(counts),"xlsx":str(xlsxout),"json":str(jsonout)},indent=2))
    return output

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--mode",choices=["historical","monthly"],required=True)
    p.add_argument("--month",default="")
    p.add_argument("--offline",action="store_true",help="Test input/output without public network")
    p.add_argument("--skip-native",action="store_true",help="Only retrieve authoritative DataCite record dates")
    args=p.parse_args()
    if args.mode=="monthly" and not re.fullmatch(r"20\d\d-(?:0[1-9]|1[0-2])",args.month):
        p.error("--month YYYY-MM required for monthly mode")
    build(args.mode,args.month,offline=args.offline,native=not args.skip_native)

if __name__=="__main__":
    main()
