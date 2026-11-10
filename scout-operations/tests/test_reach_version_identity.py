"""Regression controls for REACH same-work preprint/final DOI identities.

Uses the real MJO DOI pair and exact existing public REACH ID/UID, with
synthetic local sources. No live NOAA systems, private Hub, or network calls.
"""
import csv
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from reach_version_identity import (REACH_BASE, version_links, version_decision,
                                    fetch_reach_index, public_staged_dois)
from verify_preprint_intake import verify

PRE = "10.5194/egusphere-2025-1142"
FINAL = "10.5194/gmd-18-7969-2025"
RID = "reach-000460"
UID = "reachuid-v1-5e51cfb8d4bb28f5094f75b0463b735b"
JOURNAL = {"type": "journal-article",
           "published-online": {"date-parts": [[2025, 10, 28]]}}
ARTICLE = {"record_id": RID, "reach_uid": UID, "output_type": "1",
           "title": "A Python diagnostics package for evaluation of MJO-Teleconnections in S2S forecast systems",
           "award": "NA22OAR4590216", "link": "https://doi.org/" + PRE}
INDEX = {"by_doi": {PRE: [ARTICLE]}, "by_id": {RID: ARTICLE}, "records": 1238}
HEADERS = ["DOI", "Output Type", "Title", "Output URL", "Existing REACH Match",
           "Scout Discovery Rationale", "NOAA Award Number(s)"]


def fixture(root):
    (root / "scout-operations").mkdir()
    (root / "scout-discoveries/inbox").mkdir(parents=True)
    (root / "scout-discoveries/batches").mkdir()
    (root / "scout-discoveries/manifest.json").write_text(json.dumps({"batches": []}))
    (root / "scout-operations/preprint-watchlist.json").write_text(json.dumps({
        "schema": "reach-scout-preprint-watchlist-v1",
        "entries": [{"preprint_doi": PRE, "verified_published_dois": [FINAL],
                     "status": "published_version_found"}]}))


def make_row(classification="NEW CANDIDATE", match="", route="API-seeded expansion",
             doi=FINAL, output_type="1", update_fields=False):
    rationale = "Scout classification: " + classification + "\nScout discovery route: " + route
    if update_fields:
        rationale += "\nExisting REACH UID: " + UID
        rationale += "\nREACH update fields: title, final journal DOI, publication date, IR record URL"
    return {"DOI": doi, "Output Type": output_type,
            "Title": "A Python diagnostics package for evaluation of Madden-Julian Oscillation teleconnections",
            "Output URL": "https://doi.org/" + doi,
            "Existing REACH Match": match,
            "NOAA Award Number(s)": "NA22OAR4590216",
            "Scout Discovery Rationale": rationale}


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=HEADERS)
        writer.writeheader()
        writer.writerows(rows)


class ReachVersionIdentityTests(unittest.TestCase):
    def test_real_mjo_preprint_and_final_same_work_not_new(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture(root)
            linked = version_links(root)
            self.assertEqual(linked[FINAL]["preprints"], {PRE})
            verdict = version_decision(make_row(), linked, INDEX)
            self.assertEqual(verdict[0], "identity_hold")
            self.assertIn(RID, verdict[1])
            self.assertIn(UID, verdict[1])

    def test_metadata_update_preserves_existing_uid(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture(root)
            row = make_row("REACH METADATA UPDATE", RID + "; " + UID,
                           "Metadata correction", update_fields=True)
            self.assertEqual(version_decision(row, version_links(root), INDEX)[0], "eligible")
            # Missing UID or proposed fields must never silently become eligible.
            row["Existing REACH Match"] = RID
            row["Scout Discovery Rationale"] = row["Scout Discovery Rationale"].replace(
                "\nExisting REACH UID: " + UID, "")
            self.assertEqual(version_decision(row, version_links(root), INDEX)[0], "identity_hold")

    def test_final_not_present_as_preprint_allows_new_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture(root)
            self.assertEqual(version_decision(make_row(), version_links(root),
                                              {"by_doi": {}, "by_id": {}})[0], "eligible")
            self.assertIsNone(version_decision(make_row(doi="10.9999/unrelated"),
                                               version_links(root), INDEX))
            self.assertIsNone(version_decision(make_row(output_type="2"),
                                               version_links(root), INDEX))

    def test_retirement_archive_keeps_version_relationship(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture(root)
            (root / "scout-operations/preprint-watchlist.json").write_text(json.dumps({
                "schema": "reach-scout-preprint-watchlist-v1", "entries": []}))
            (root / "scout-operations/preprint-retirement-archive.json").write_text(json.dumps({
                "schema": "reach-scout-preprint-retirement-archive-v1",
                "entries": [{"preprint_doi": PRE, "published_doi": FINAL, "reach_ids": [RID]}]}))
            self.assertEqual(version_decision(make_row(), version_links(root), INDEX)[0],
                             "identity_hold")

    def test_sha_verified_index_and_corruption_fail_closed(self):
        raw = io.StringIO()
        writer = csv.DictWriter(raw, fieldnames=[
            "Record ID", "REACH UID", "Output Type", "Title",
            "Award Number(s)", "Link to Output"])
        writer.writeheader()
        writer.writerow({"Record ID": RID, "REACH UID": UID, "Output Type": "1",
                         "Title": ARTICLE["title"], "Award Number(s)": "NA22OAR4590216",
                         "Link to Output": "https://doi.org/" + PRE})
        blob = raw.getvalue().encode()
        path = "agent-data/index/part-001.csv"
        manifest = json.dumps({"source": {"rows": 1}, "index": {"files": [
            {"path": path, "rows": 1, "bytes": len(blob),
             "sha256": hashlib.sha256(blob).hexdigest()}]}}).encode()
        contents = {REACH_BASE + "agent-data/manifest.json": manifest,
                    REACH_BASE + path: blob}
        result = fetch_reach_index(fetch_bytes=contents.__getitem__)
        self.assertEqual(result["by_doi"][PRE][0]["reach_uid"], UID)
        contents[REACH_BASE + path] = blob + b"bad"
        with self.assertRaises(ValueError):
            fetch_reach_index(fetch_bytes=contents.__getitem__)

    def test_five_scout_modes_prevent_duplicate_mjo_candidate(self):
        modes = ["Monthly API", "Historical Crossref", "Historical DataCite",
                 "Independent discovery", "API-seeded expansion"]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture(root)
            for i, mode in enumerate(modes):
                row = make_row()
                row["Scout Discovery Rationale"] += "\nIntake origin: " + mode
                write_csv(root / f"scout-discoveries/inbox/2026-11-10-case-{i}.csv", [row])
            report = verify(root, fetch_crossref=lambda d: JOURNAL,
                            fetch_datacite=lambda d: None, fetch_reach=lambda: INDEX)
            self.assertEqual(report["eligible_batches"], 0)
            self.assertEqual(report["held_batches"], 5)
            self.assertTrue(all(c["rows"][0]["status"] == "identity_hold"
                                for c in report["checks"]))

    def test_correct_update_route_allowed_even_when_preprint_known(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture(root)
            row = make_row("REACH METADATA UPDATE", RID + " " + UID,
                           "Metadata correction", update_fields=True)
            write_csv(root / "scout-discoveries/inbox/2026-11-10-update.csv", [row])
            report = verify(root, fetch_crossref=lambda d: JOURNAL,
                            fetch_datacite=lambda d: None, fetch_reach=lambda: INDEX)
            self.assertEqual(report["eligible_batches"], 1)
            self.assertEqual(report["checks"][0]["rows"][0]["status"], "eligible")

    def test_public_staged_candidate_blocks_resubmitted_new_doi_without_private_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture(root)
            prior = root / "scout-discoveries/batches/2026-10-28-original.csv"
            write_csv(prior, [make_row()])
            raw = prior.read_bytes()
            (root / "scout-discoveries/manifest.json").write_text(json.dumps({
                "batches": [{"path": "scout-discoveries/batches/" + prior.name,
                             "sha256": hashlib.sha256(raw).hexdigest(),
                             "record_count": 1}]}))
            self.assertIn(FINAL, public_staged_dois(root))
            write_csv(root / "scout-discoveries/inbox/2026-11-10-again.csv", [make_row()])
            report = verify(root, fetch_crossref=lambda d: JOURNAL,
                            fetch_datacite=lambda d: None,
                            fetch_reach=lambda: self.fail("Staged DOI should be held before live lookup"))
            self.assertEqual(report["held_batches"], 1)
            self.assertIn("already exists", report["checks"][0]["rows"][0]["reason"])


if __name__ == "__main__":
    unittest.main()
