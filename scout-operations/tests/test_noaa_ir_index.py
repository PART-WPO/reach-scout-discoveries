"""NOAA Central Library indexer is complete, DOI-exact and checksum-verified."""
import sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from build_noaa_ir_index import doi_values, collect, write_index
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scout-discoveries/tools"))
from noaa_ir_lookup import trusted_index

class IndexTests(unittest.TestCase):
    def test_official_mods_doi_and_pid(self):
        doc={"PID":"noaa:77174",
             "mods.sm_digital_object_identifier":["https://doi.org/10.1016/j.pdisas.2026.100696"]}
        self.assertEqual(doi_values(doc),{"10.1016/j.pdisas.2026.100696"})
        self.assertEqual(doi_values({"PID":"noaa:1","mods.sm_digital_object_identifier":"not doi"}),set())
    def test_complete_pagination_and_metadata(self):
        docs=[{"PID":"noaa:77174","mods.sm_digital_object_identifier":["https://doi.org/10.1234/KNOWN"]},
              {"PID":"noaa:123","mods.sm_digital_object_identifier":"10.1234/other"}]
        def fake(params,tries=5):
            start=params.get("start",0)
            return {"response":{"numFound":2,"start":start,"docs":docs[start:start+params["rows"]]}}
        with patch("build_noaa_ir_index.fetch_json",side_effect=fake),patch("build_noaa_ir_index.time.sleep"):
            count,found=collect(page_size=1)
        self.assertEqual(count,2)
        self.assertEqual(found["10.1234/known"],{"https://repository.library.noaa.gov/view/noaa/77174"})
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);write_index(count,found,root/"scout-operations/noaa-ir")
            loaded=trusted_index(root)
            self.assertEqual(loaded["dois"]["10.1234/known"],
                             ["https://repository.library.noaa.gov/view/noaa/77174"])
            self.assertEqual(loaded["manifest"]["distinct_dois"],2)
            index_shard=root/"scout-operations/noaa-ir/shards/"+(
                __import__("hashlib").sha256(b"10.1234/known").hexdigest()[0]+".json")
            index_shard.write_text("{}")
            with self.assertRaises(ValueError):trusted_index(root)
    def test_pagination_change_fails_closed(self):
        def fake(params,tries=5):
            if params.get("rows")==1 and params.get("start")==0:
                return {"response":{"numFound":2,"start":0,"docs":[]}}
            return {"response":{"numFound":3,"start":0,"docs":[]}}
        with patch("build_noaa_ir_index.fetch_json",side_effect=fake):
            with self.assertRaises(RuntimeError):collect(page_size=2)

if __name__=="__main__":unittest.main()
