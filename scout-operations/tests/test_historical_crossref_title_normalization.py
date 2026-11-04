"""Regression: inline XML/HTML in publisher titles cannot hide existing REACH outputs."""
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scout-operations/historical-crossref-screening"
spec = importlib.util.spec_from_file_location("historical_crossref_router", SCRIPTS / "build_actionable_routing.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class HistoricalCrossrefMarkupTests(unittest.TestCase):
    def test_actual_false_negative_titles(self):
        pairs = [
            (
                "Quantifying patterns of streamflow peaks over the southeastern United States "
                "using a <scp>long‐term</scp> retrospective data set",
                "Quantifying patterns of streamflow peaks over the southeastern United States "
                "using a long-term retrospective data set",
            ),
            (
                "Identification of flood‐prone areas with <scp>GeoFlood</scp>: "
                "Lessons learned from the Tiber River case study",
                "Identification of flood-prone areas with GeoFlood: "
                "Lessons learned from the Tiber River case study",
            ),
            (
                "Making Flood Inundation Mapping (\n <scp>FIM</scp>\n ) Work for Multiple Users: "
                "Improving the Design of\n <scp>FIM</scp>\n for Decision Support",
                "Making Flood Inundation Mapping (FIM) Work for Multiple Users: "
                "Improving the Design of FIM for Decision Support",
            ),
            (
                "<i>tobac</i>\n v1.5: introducing fast 3D tracking, splits and mergers, "
                "and other enhancements for identifying and analysing meteorological phenomena",
                "tobac v1.5: introducing fast 3D tracking, splits and mergers, "
                "and other enhancements for identifying and analysing meteorological phenomena",
            ),
        ]
        for crossref, reach in pairs:
            with self.subTest(reach=reach):
                self.assertEqual(module.title(crossref), module.title(reach))
                self.assertNotIn(" scp ", " " + module.title(crossref) + " ")
                self.assertNotIn(" i ", " " + module.title(crossref) + " ")

    def test_markup_does_not_produce_confirmed_identity(self):
        # Title-only equivalence signals a bounded identity check, not proof
        # that a DOI is exactly represented by the REACH record.
        self.assertEqual(module.title("<scp>FIM</scp>"), module.title("FIM"))
        self.assertNotEqual(module.title("FIM for different users"),
                            module.title("FIM for multiple users"))


if __name__ == "__main__":
    unittest.main()
