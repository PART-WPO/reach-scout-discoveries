"""NOAA IR metadata enrichment cannot invent FALSE or touch existing output reviews."""
import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from noaa_ir_lookup import enrich, normalize_doi
from prepare_batch import prepare

INDEX={"dois":{"10.1234/known":["https://repository.library.noaa.gov/view/noaa/77174"],
               "10.1234/ambiguous":["https://repository.library.noaa.gov/view/noaa/10",
                                     "https://repository.library.noaa.gov/view/noaa/11"]}}
def candidate(classification="NEW CANDIDATE",existing="No match in full REACH index"):
    return {"fields":{"Title":"Synthetic study with NOAA repository proof",
                       "DOI":"10.1234/known",
                       "Output URL":"https://doi.org/10.1234/known",
                       "Output Type":"1",
                       "NOAA Award Number(s)":"NA25OARX459C0342-T1-01",
                       "Publication Date":"2026-10-01",
                       "Evidence URL":"https://example.org/source",
                       "Funding Evidence URL":"https://example.org/award",
                       "Existing REACH Match":existing,
                       "Source Run ID":"REACH-SCOUT-TEST-IR-ONLY"},
            "provenance":{"classification":classification,"route":"Direct API",
                          "path_evidence":"https://example.org/source",
                          "notes":["Reviewer question: Verify output funding and scope?"]}}
class LookupTests(unittest.TestCase):
    def test_exact_doi_only(self):
        f,p=candidate()["fields"],candidate()["provenance"]
        o,status=enrich(f,p,INDEX)
        self.assertEqual(status,"exact_doi_matched_official_noaa_ir_index")
        self.assertEqual(o["IR?"],"TRUE")
        self.assertEqual(o["IR Repository URL"],"https://repository.library.noaa.gov/view/noaa/77174")
        self.assertNotIn("IR?",f)
    def test_missing_is_unknown_not_false(self):
        f,p=candidate()["fields"],candidate()["provenance"]
        f["DOI"]="10.1234/not-in-ir"
        o,status=enrich(f,p,INDEX)
        self.assertIn("not_found",status)
        self.assertFalse(o.get("IR?"))
        self.assertFalse(o.get("IR Repository URL"))
    def test_ambiguous_not_true(self):
        item=candidate();item["fields"]["DOI"]="10.1234/ambiguous"
        o,status=enrich(item["fields"],item["provenance"],INDEX)
        self.assertIn("ambiguous",status)
        self.assertFalse(o.get("IR?"))
    def test_no_index_remains_blank(self):
        item=candidate()
        o,status=enrich(item["fields"],item["provenance"])
        self.assertIn("unavailable",status)
        self.assertFalse(o.get("IR?"))
    def test_existing_reach_and_corrections_untouched(self):
        for classification in ("REACH METADATA UPDATE","KNOWN DUPLICATE","POSSIBLE DUPLICATE"):
            item=candidate(classification)
            o,status=enrich(item["fields"],item["provenance"],INDEX)
            self.assertFalse(o.get("IR?"))
        item=candidate("NEEDS INVESTIGATION","Existing REACH UID reach-000123")
        o,status=enrich(item["fields"],item["provenance"],INDEX)
        self.assertFalse(o.get("IR?"))
    def test_new_investigation_without_reach_match(self):
        item=candidate("NEEDS INVESTIGATION")
        o,status=enrich(item["fields"],item["provenance"],INDEX)
        self.assertEqual(o["IR?"],"TRUE")
    def test_conflicting_existing_ir_link_fails_closed(self):
        item=candidate()
        item["fields"]["IR Repository URL"]="https://repository.library.noaa.gov/view/noaa/222"
        with self.assertRaises(ValueError):enrich(item["fields"],item["provenance"],INDEX)
    def test_prepare_batch_adds_verifiable_columns(self):
        item=candidate()
        with tempfile.TemporaryDirectory() as tmp:
            src=Path(tmp)/"input.json";src.write_text(json.dumps({"candidates":[item]}))
            dest=Path(tmp)/"2026-11-02-noaa-ir-enrichment-test.csv"
            with patch("prepare_batch.read_noaa_ir_index",return_value=INDEX):
                prepare(src,dest)
            with dest.open(newline="",encoding="utf-8") as file:
                row=list(csv.DictReader(file))[0]
            self.assertEqual(row["IR?"],"TRUE")
            self.assertEqual(row["IR Repository URL"],"https://repository.library.noaa.gov/view/noaa/77174")
            self.assertIn("NOAA IR check: TRUE",row["Scout Discovery Rationale"])

if __name__=="__main__":unittest.main()
