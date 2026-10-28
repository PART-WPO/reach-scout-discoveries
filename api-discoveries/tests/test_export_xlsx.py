import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
import export_comparison_xlsx as ex

NS={"m":"http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
def record(source,award,doi,title,date="",basis="published_exact"):
    return {"src":source,"award":award,"doi":doi,"title":title,
       "date":date,"date_basis":basis,"outtype":"1" if source=="crossref" else "3",
       "programs":["JTTI"],"authors":["Jane Example"],"abstract":"Record example",
       "evidence":"https://api.crossref.org/works/"+doi if source=="crossref" else "https://api.datacite.org/dois/"+doi,
       "related":False}
def shards():
    source_sha="e"*64
    data=[]
    for src in ("crossref","datacite"):
        for i in range(8):
            awards=["NA16OAR4590234"] if i==0 else ["NA16OAR4590235"] if i==1 else []
            rows=[]
            if i==0 and src=="crossref":
                rows=[record("crossref","NA16OAR4590234","10.5555/test1","Test article","2026-10-01")]
            if i==1 and src=="crossref":
                rows=[record("crossref","NA16OAR4590235","10.5555/test1","Test article","2026-10-01")]
            if i==0 and src=="datacite":
                rows=[record("datacite","NA16OAR4590234","10.5555/test1","Test article","2026-10-01"),
                      record("datacite","NA16OAR4590234","10.5555/test2","Data deposit","",
                        "registration_only_publication_unverified")]
            data.append({"mode":"monthly","source":src,"month":"2026-10",
              "shard":i,"total_awards":2,"source_sha":source_sha,
              "attempted_awards":awards,"failures":[],"records":rows})
    return data

class ComparisonWorkbookTests(unittest.TestCase):
    def test_export_and_inspect_standard_excel_xml(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"REACH_API_Comparison_2026-10.xlsx"
            info=ex.build(shards(),"2026-10",path)
            self.assertEqual(info["awards_checked"],2)
            self.assertEqual(info["distinct_dois"],2)
            self.assertEqual(info["Crossref_award_doi_rows"],2)
            self.assertEqual(info["DataCite_award_doi_rows"],2)
            first=path.read_bytes()
            ex.build(shards(),"2026-10",path)
            self.assertEqual(path.read_bytes(),first)
            with zipfile.ZipFile(path) as z:
                self.assertIsNone(z.testzip())
                workbook=ET.fromstring(z.read("xl/workbook.xml"))
                sheetnames=[x.get("name") for x in workbook.findall(".//m:sheet",NS)]
                self.assertEqual(len(sheetnames),7)
                self.assertIn("Crossref Legacy View",sheetnames)
                self.assertIn("DataCite Results",sheetnames)
                self.assertIn("Combined Results",sheetnames)
                content=z.read("xl/worksheets/sheet5.xml").decode()
                for header in ("Award Number","Published Date","Citation"):
                    self.assertIn(header,content)
                self.assertIn("https://doi.org/10.5555/test1",content)
                self.assertIn("NA16OAR4590234",content)
                # Blank unknown date must not be filled with registration date
                combined=z.read("xl/worksheets/sheet2.xml").decode()
                self.assertIn("registration_only_publication_unverified",combined)
                self.assertIn("Unreviewed",combined)

    def test_different_rerun_does_not_change_immutable_report(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"monthly.xlsx"
            data=shards()
            ex.build(data,"2026-10",path)
            data[0]["records"][0]["title"]="Changed by API after first snapshot"
            with self.assertRaisesRegex(RuntimeError,"different content"):
                ex.build(data,"2026-10",path)

    def test_missing_source_coverage_rejected(self):
        data=shards()
        data[0]["attempted_awards"]=[]
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError,"check all SPARK awards"):
                ex.build(data,"2026-10",Path(d)/"bad.xlsx")

    def test_formula_like_text_is_literal(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"safe.xlsx"
            data=shards()
            data[0]["records"][0]["title"]='=HYPERLINK("http://evil","go")'
            ex.build(data,"2026-10",path)
            with zipfile.ZipFile(path) as z:
                combined=z.read("xl/worksheets/sheet2.xml").decode()
                self.assertIn('t="inlineStr"',combined)
                self.assertNotIn("<f>",combined)

if __name__=="__main__":
    unittest.main()
