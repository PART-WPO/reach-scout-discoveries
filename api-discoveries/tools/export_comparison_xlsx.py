#!/usr/bin/env python3
"""Produce review-only, comparison-friendly .xlsx from validated monthly API shards.

No spreadsheet intermediary, third-party Excel dependency, human decisions or
changes to Scout's 24-column discovery feed. Writes standard OOXML with stdlib.
"""
import argparse
import io
import collections
import datetime as dt
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

NS="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
R="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG="http://schemas.openxmlformats.org/package/2006/relationships"
CT="http://schemas.openxmlformats.org/package/2006/content-types"
ET.register_namespace("",NS)
ET.register_namespace("r",R)
BAD_CHARS=re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
LINK_HEADERS={"DOI","Evidence URL","Source URL","Output URL"}
KIND={"1":"Publication","2":"Code / software","3":"Data / instrument","4":"Other output"}
HEADERS={
  "Combined Results":["DOI","Title","Output Type","Publication Date","Date Basis","NOAA Award Number(s)","WPO Program(s)","Source APIs","Creators / Authors","Evidence URL","Brief Abstract","Related Works","Scout Status"],
  "Crossref Results":["Award Number","DOI","Title","Published Date","Citation","Output Type","WPO Program","Date Basis","Evidence URL","Related Works"],
  "DataCite Results":["Award Number","DOI","Title","Published Date","Creators","Output Type","WPO Program","Date Basis","Evidence URL","Related Works"],
  "Crossref Legacy View":["Award Number","DOI","Title","Published Date","Citation"],
  "Awards Checked":["Award Number","DataCite DOIs","Crossref DOIs","Combined Unique DOIs","Programs in Matched Records"],
}
WIDTHS={
  "Combined Results":[29,54,21,17,39,39,35,22,39,48,62,15,24],
  "Crossref Results":[23,31,54,17,35,21,28,38,52,15],
  "DataCite Results":[23,31,54,17,41,21,28,38,52,15],
  "Crossref Legacy View":[24,35,65,19,36],
  "Awards Checked":[26,20,20,24,46],
  "Summary":[35,68],
  "Read Me":[36,92],
}

def q(parent,tag,attrs=None,text=None):
    node=ET.SubElement(parent,"{%s}%s"%(NS,tag),attrs or {})
    if text is not None:node.text=str(text)
    return node
def colname(n):
    s=""
    while n:
        n,c=divmod(n-1,26);s=chr(65+c)+s
    return s
def txt(value):
    if value is None:return ""
    s=BAD_CHARS.sub("",str(value))
    if len(s)>32000:s=s[:31997]+"..."
    return s
def add_sheet(rows,widths,freeze=True):
    root=ET.Element("{%s}worksheet"%NS)
    views=q(root,"sheetViews")
    view=q(views,"sheetView",{"workbookViewId":"0"})
    if freeze:q(view,"pane",{"ySplit":"1","topLeftCell":"A2","activePane":"bottomLeft","state":"frozen"})
    cols=q(root,"cols")
    for i,w in enumerate(widths,1):
        q(cols,"col",{"min":str(i),"max":str(i),"width":str(w),"customWidth":"1"})
    data=q(root,"sheetData")
    lastcol=colname(len(widths))
    for ridx,row in enumerate(rows,1):
        r=q(data,"row",{"r":str(ridx),"ht":"24" if ridx==1 else "18","customHeight":"1"})
        for cidx,value in enumerate(row,1):
            ref=colname(cidx)+str(ridx)
            if isinstance(value,(int,float)) and not isinstance(value,bool):
                c=q(r,"c",{"r":ref,"s":"2" if ridx>1 else "1"})
                q(c,"v",text=value)
            else:
                c=q(r,"c",{"r":ref,"s":"1" if ridx==1 else "0","t":"inlineStr"})
                is_el=q(c,"is")
                q(is_el,"t",{"{http://www.w3.org/XML/1998/namespace}space":"preserve"},txt(value))
    if len(rows)>1:
        q(root,"autoFilter",{"ref":"A1:%s%s"%(lastcol,len(rows))})
    q(root,"pageMargins",{"left":"0.4","right":"0.4","top":"0.6","bottom":"0.6","header":"0.3","footer":"0.3"})
    return ET.tostring(root,encoding="utf-8",xml_declaration=True)

def xml_bytes(root):
    return ET.tostring(root,encoding="utf-8",xml_declaration=True)

def make_xlsx(target,sheets):
    target.parent.mkdir(parents=True,exist_ok=True)
    names=list(sheets)
    wb=ET.Element("{%s}workbook"%NS)
    ws=q(wb,"sheets")
    for idx,name in enumerate(names,1):
        q(ws,"sheet",{"name":name,"sheetId":str(idx),"{%s}id"%R:"rId%d"%idx})
    wrels=ET.Element("{%s}Relationships"%PKG)
    for idx in range(1,len(names)+1):
        ET.SubElement(wrels,"{%s}Relationship"%PKG,{"Id":"rId%d"%idx,
          "Type":R+"/worksheet","Target":"worksheets/sheet%d.xml"%idx})
    ET.SubElement(wrels,"{%s}Relationship"%PKG,{"Id":"rId%d"%(len(names)+1),
          "Type":R+"/styles","Target":"styles.xml"})
    content=ET.Element("{%s}Types"%CT)
    for ext,typ in [("rels","application/vnd.openxmlformats-package.relationships+xml"),
                    ("xml","application/xml")]:
        ET.SubElement(content,"{%s}Default"%CT,{"Extension":ext,"ContentType":typ})
    types=[("/xl/workbook.xml","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"),
           ("/xl/styles.xml","application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml")]
    types +=[("/xl/worksheets/sheet%d.xml"%i,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml") for i in range(1,len(names)+1)]
    for part,typ in types:
        ET.SubElement(content,"{%s}Override"%CT,{"PartName":part,"ContentType":typ})
    package_rels=ET.Element("{%s}Relationships"%PKG)
    ET.SubElement(package_rels,"{%s}Relationship"%PKG,{"Id":"rId1",
      "Type":R+"/officeDocument","Target":"xl/workbook.xml"})
    styles=ET.Element("{%s}styleSheet"%NS)
    num=q(styles,"numFmts",{"count":"0"})
    fonts=q(styles,"fonts",{"count":"2"})
    font=q(fonts,"font");q(font,"sz",{"val":"10"});q(font,"name",{"val":"Aptos"})
    font=q(fonts,"font");q(font,"b");q(font,"sz",{"val":"10"});q(font,"color",{"rgb":"FFFFFFFF"});q(font,"name",{"val":"Aptos"})
    fills=q(styles,"fills",{"count":"3"})
    for pattern in ["none","gray125","solid"]:
        fill=q(fills,"fill")
        pf=q(fill,"patternFill",{"patternType":pattern})
        if pattern=="solid":q(pf,"fgColor",{"rgb":"FF15324E"});q(pf,"bgColor",{"indexed":"64"})
    borders=q(styles,"borders",{"count":"1"});q(borders,"border")
    style_xfs=q(styles,"cellStyleXfs",{"count":"1"});q(style_xfs,"xf",{"numFmtId":"0","fontId":"0","fillId":"0","borderId":"0"})
    xfs=q(styles,"cellXfs",{"count":"3"})
    q(xfs,"xf",{"numFmtId":"0","fontId":"0","fillId":"0","borderId":"0","xfId":"0","applyAlignment":"1"})
    h=q(xfs,"xf",{"numFmtId":"0","fontId":"1","fillId":"2","borderId":"0","xfId":"0","applyFont":"1","applyFill":"1","applyAlignment":"1"})
    q(h,"alignment",{"vertical":"center"})
    q(xfs,"xf",{"numFmtId":"0","fontId":"0","fillId":"0","borderId":"0","xfId":"0"})
    styles_q=q(styles,"cellStyles",{"count":"1"})
    q(styles_q,"cellStyle",{"name":"Normal","xfId":"0","builtinId":"0"})
    # Fixed OOXML timestamps ensure byte-for-byte idempotence across reruns.
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,"w",zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        def put(name,content):
            item=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0))
            item.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(item,content,compress_type=zipfile.ZIP_DEFLATED,compresslevel=6)
        put("[Content_Types].xml",xml_bytes(content))
        put("_rels/.rels",xml_bytes(package_rels))
        put("xl/workbook.xml",xml_bytes(wb))
        put("xl/_rels/workbook.xml.rels",xml_bytes(wrels))
        put("xl/styles.xml",xml_bytes(styles))
        for idx,name in enumerate(names,1):
            put("xl/worksheets/sheet%d.xml"%idx,add_sheet(sheets[name],WIDTHS[name]))
    data=stream.getvalue()
    if target.exists():
        if target.read_bytes()!=data:
            raise RuntimeError("Monthly report exists with different content; publish a correction version instead: "+str(target))
    else:
        target.write_bytes(data)

def group_records(pieces,source):
    grouped=collections.defaultdict(list)
    for part in pieces:
        if part.get("source")!=source:continue
        if part.get("failures"):raise ValueError("Source shard has failures")
        for r in part.get("records",[]):
            doi=str(r.get("doi","")).strip().lower()
            if not re.fullmatch(r"10\.\d{4,9}/[^\s]+",doi):raise ValueError("Invalid DOI")
            grouped[(r.get("award","").strip().upper(),doi)].append(r)
    rows=[]
    for (award,doi),rs in sorted(grouped.items()):
        chosen=sorted(rs,key=lambda x: (not bool(x.get("date")),len(x.get("title",""))==0))[0]
        x=dict(chosen)
        x["award"]=award
        rows.append(x)
    return rows
def citation(r,month):
    authors=r.get("authors") or []
    first=str(authors[0] if authors else "").strip()
    first=first.split(",")[0] if "," in first else first.split()[-1] if first else "Unknown Author"
    year=(r.get("date") or month or "Unknown Year")[:4]
    return first+" et al. ("+year+")"
def date_txt(r):
    return r.get("date","") or ""
def srcrow(r,src,month):
    cols=[
      r.get("award",""),"https://doi.org/"+r["doi"],r.get("title",""),
      date_txt(r)
    ]
    if src=="crossref":
        cols.extend([r.get("citation") or citation(r,month),KIND.get(r.get("outtype"),"Other output")])
    else:
        cols.extend(["; ".join(r.get("authors") or []),KIND.get(r.get("outtype"),"Other output")])
    cols.extend([", ".join(r.get("programs") or []),
      r.get("date_basis",""),r.get("evidence",""),"Yes" if r.get("related") else "No"])
    return cols

def build(pieces,month,output):
    if not re.fullmatch(r"20\d{2}-(0[1-9]|1[0-2])",month):raise ValueError("Expected month YYYY-MM")
    cr=group_records(pieces,"crossref")
    dc=group_records(pieces,"datacite")
    if {x.get("month") for x in pieces}!={month}:
        raise ValueError("Shard months do not match "+month)
    if len({(x.get("source"),x.get("shard")) for x in pieces})!=16:
        raise ValueError("Expected 8 successful shards from each API")
    for src in ("crossref","datacite"):
        group=[x for x in pieces if x["source"]==src]
        all_awards=[a for x in group for a in x["attempted_awards"]]
        if len(all_awards)!=group[0]["total_awards"] or len(set(all_awards))!=group[0]["total_awards"]:
            raise ValueError("Source did not check all SPARK awards")
    if len({(x["source_sha"],x["total_awards"]) for x in pieces})!=1:
        raise ValueError("SPARK source snapshot mismatch")
    sha=pieces[0]["source_sha"]
    checked=sorted(set(a for x in pieces if x["source"]=="crossref" for a in x["attempted_awards"]))
    bydoi=collections.defaultdict(list)
    for x in cr+dc:bydoi[x["doi"]].append(x)
    combined=[]
    for doi,records in sorted(bydoi.items()):
        best=sorted(records,key=lambda x:(not bool(x.get("date")),x.get("src")!="datacite"))[0]
        awards=sorted(set(x["award"] for x in records))
        sources=sorted(set("DataCite" if x["src"]=="datacite" else "Crossref" for x in records))
        programs=sorted(set(p for x in records for p in (x.get("programs") or [])))
        dates=sorted(set(x.get("date_basis") or "" for x in records))
        combined.append(["https://doi.org/"+doi,best.get("title",""),
          KIND.get(best.get("outtype"),"Other output"),best.get("date",""),
          ", ".join(dates),", ".join(awards),", ".join(programs),
          ", ".join(sources),"; ".join(best.get("authors") or []),
          best.get("evidence",""),best.get("abstract",""),
          "Yes" if any(x.get("related") for x in records) else "No",
          "Unreviewed — Scout research inbox"])
    key=lambda xs:len(set(x["doi"] for x in xs))
    ad=collections.defaultdict(set);ac=collections.defaultdict(set);ap=collections.defaultdict(set)
    for r in dc:ad[r["award"]].add(r["doi"]);ap[r["award"]].update(r.get("programs") or [])
    for r in cr:ac[r["award"]].add(r["doi"]);ap[r["award"]].update(r.get("programs") or [])
    awards=[[a,len(ad[a]),len(ac[a]),len(ad[a]|ac[a]),", ".join(sorted(ap[a]))] for a in checked]
    year,mon=map(int,month.split("-"))
    first=dt.date(year,mon,1)
    nxt=dt.date(year+1,1,1) if mon==12 else dt.date(year,mon+1,1)
    last=nxt-dt.timedelta(days=1)
    summary=[
      ["REACH MONTHLY API COMPARISON","Public research data — no Scout or human verification implied"],
      ["Cohort",month],
      ["Publication window",first.isoformat()+" through "+last.isoformat()+" (inclusive)"],
      ["Award identifiers checked",len(checked)],
      ["Crossref award × DOI rows",len(cr)],
      ["Crossref distinct DOIs",key(cr)],
      ["DataCite award × DOI rows",len(dc)],
      ["DataCite distinct DOIs",key(dc)],
      ["Combined distinct DOIs",len(bydoi)],
      ["DOIs found by both APIs",len({r["doi"] for r in cr}&{r["doi"] for r in dc})],
      ["Publication date unverified",sum(not r[3] for r in combined)],
      ["SPARK source report SHA-256",sha],
      ["Output disposition","Unreviewed raw API research. Discovery Hub receives Scout-checked findings only."],
      ["Generated from","GitHub Actions source shard artifacts (DataCite + Crossref)"],
    ]
    instructions=[
      ["Workbook guidance","Purpose / interpretation"],
      ["Crossref Legacy View","Same five headers as the original Google Apps Script tab: Award Number, DOI, Title, Published Date, Citation. One row per matched award + DOI."],
      ["Crossref Results","Additional output type, program, date basis, evidence and related works flags. DOI link is an ordinary text URL."],
      ["DataCite Results","Equivalent DataCite view. A blank Published Date means record-level date verification remains necessary."],
      ["Combined Results","DOI-deduplicated results across APIs and across awards, with all matched awards retained."],
      ["Awards Checked","Complete SPARK award coverage. A zero means no verified exact funding metadata match returned from that API."],
      ["Important distinction","This workbook compares raw API findings only. It is not proof the outputs are new to REACH or approved for Smartsheet."],
      ["Date difference","The GitHub harvest uses the prior full calendar month; the old Crossref script preferred published-print over published-online. The two may disagree for a record with multiple dates."],
      ["Citation difference","Legacy-style citations are a convenience for comparison; check any compound author surnames, author metadata or uncertain year."],
      ["Duplicate comparison","Compare normalized DOI and award together; a DOI shared by two awards appears twice in source tabs but once in Combined Results."],
      ["Source limitations","Missing funding award metadata, late DOI deposits, and date-only records can cause differences. See Date Basis and source evidence."],
      ["Privacy","Only public API metadata and SPARK public award identifiers are included. No private reviewer, Smartsheet or authorization information."],
    ]
    sheets={
      "Summary":summary,
      "Combined Results":[HEADERS["Combined Results"]]+combined,
      "Crossref Results":[HEADERS["Crossref Results"]]+[srcrow(x,"crossref",month) for x in cr],
      "DataCite Results":[HEADERS["DataCite Results"]]+[srcrow(x,"datacite",month) for x in dc],
      "Crossref Legacy View":[HEADERS["Crossref Legacy View"]]+[
          [r["award"],"https://doi.org/"+r["doi"],r.get("title",""),date_txt(r),r.get("citation") or citation(r,month)] for r in cr],
      "Awards Checked":[HEADERS["Awards Checked"]]+awards,
      "Read Me":instructions,
    }
    make_xlsx(output,sheets)
    return {"cohort":month,"Crossref_award_doi_rows":len(cr),"DataCite_award_doi_rows":len(dc),
            "distinct_dois":len(bydoi),"awards_checked":len(checked),"sheets":list(sheets),"output":str(output)}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--month",default="")
    p.add_argument("--input",default="api-discoveries/tmp")
    p.add_argument("--output",default="")
    args=p.parse_args()
    if not args.month:
        today=dt.datetime.now(dt.timezone.utc).date().replace(day=1)
        args.month=(today-dt.timedelta(days=1)).strftime("%Y-%m")
    files=sorted(Path(args.input).glob("monthly-*-shard*.json"))
    data=[json.loads(x.read_text()) for x in files]
    if len(data)!=16:raise ValueError("16 monthly DataCite and Crossref shards are required")
    target=Path(args.output) if args.output else Path("api-discoveries/reports")/(f"REACH_API_Comparison_{args.month}.xlsx")
    res=build(data,args.month,target)
    print(json.dumps(res,indent=2))
if __name__=="__main__":main()
