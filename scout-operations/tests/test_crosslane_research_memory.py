"""Source-verified historical discovery graph never collapses distinct expansion."""
import json
import sys
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from build_crosslane_research_memory import (
    build, source_links, metadata_pointers, mission_index, ROOT, SCHEMA,
)
from decision_pipeline import norm_doi


class CrosslaneMemoryTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.graph = build()

    def test_all_historical_and_related_source_lanes_preserved(self):
        g = self.graph
        self.assertEqual(g["schema"], SCHEMA)
        from unified_source_preflight import preflight
        from build_research_outcome_registry import build as notes_build
        live = preflight()
        notes = notes_build()
        self.assertGreaterEqual(g["preflighted_lane_doi_records"], 827)
        self.assertEqual(g["preflighted_lane_doi_records"], len(live["cases"]))
        self.assertEqual(g["lane_doi_counts"]["historical_crossref"],
                         len([x for x in live["cases"]
                              if x["discovery_lane"] == "historical_crossref"]))
        self.assertEqual(g["lane_doi_counts"]["historical_datacite"],
                         len([x for x in live["cases"]
                              if x["discovery_lane"] == "historical_datacite"]))
        self.assertEqual(g["lane_doi_counts"]["monthly_api"],
                         len([x for x in live["cases"]
                              if x["discovery_lane"] == "monthly_api"]))
        self.assertEqual(g["lane_doi_counts"]["monthly_related_outputs"],
                         len([x for x in live["cases"]
                              if x["discovery_lane"] == "monthly_related_outputs"]))
        self.assertEqual(g["lane_doi_counts"]["independent"],
                         len([x for x in live["cases"]
                              if x["discovery_lane"] == "independent"]))
        self.assertEqual(sum(g["lane_doi_counts"].values()),
                         g["preflighted_lane_doi_records"])
        self.assertGreaterEqual(g["historical_note_events_reused_as_context"], 50)
        self.assertEqual(g["historical_note_events_reused_as_context"],
                         len(notes["events"]))
        self.assertEqual(g["source_documented_doi_note_events"] +
                         g["source_documented_nondoi_note_events"],
                         len(notes["events"]))
        self.assertGreaterEqual(g["source_documented_nondoi_note_events"], 1)
        self.assertEqual(len(g["non_doi_code_or_url_research_notes"]),
                         g["source_documented_nondoi_note_events"])
        self.assertTrue(all(not e["research_complete_inferred"]
                            and not e["human_review_inferred"]
                            for e in g["non_doi_code_or_url_research_notes"]))
        self.assertTrue(any(x["track"] == "CODE_OR_URL_EVIDENCE"
                            for x in g["work_items"]))
        self.assertGreater(g["explicit_related_output_links"], 0)
        self.assertEqual(len(g["nodes"]), g["distinct_public_doi_nodes"])
        self.assertEqual(len(g["links"]), g["explicit_related_output_links"])
        self.assertEqual(g["historical_metadata_pointers_not_treated_as_current"] >= 0, True)

    def test_all_426_reach_verified_seeds_keep_expansion_even_when_original_screened(self):
        g = self.graph
        routing = json.loads((ROOT/"scout-operations/historical-crossref-screening/actionable-routing.json").read_text())
        verified_count = routing["counts"]["CONFIRMED_IN_REACH"]
        self.assertGreaterEqual(verified_count, 426)
        self.assertEqual(g["verified_reach_originals_preserved_as_expansion_seeds"],
                         verified_count)
        original = {x["doi"]: x for x in g["work_items"] if x["track"] == "ORIGINAL"}
        expansions = {x["doi"]: x for x in g["work_items"] if x["track"] == "EXPANSION"}
        reach_seeds = [x for x in g["nodes"] if x["public_reach_verified_existing"]]
        self.assertEqual(len(reach_seeds), verified_count)
        for node in reach_seeds:
            d = node["doi"]
            if node["preprint_or_version_hold"]:
                self.assertEqual(original[d]["next_action"],
                                 "PREPRINT_WATCHLIST_NOT_ELIGIBLE_AS_ORIGINAL")
            else:
                self.assertEqual(original[d]["next_action"],
                                 "REUSE_VERIFIED_REACH_IDENTITY_NO_DUPLICATE_ORIGINAL")
            self.assertEqual(expansions[d]["next_action"], "EXPAND_VERIFIED_WPO_REACH_SEED")
            self.assertFalse(original[d]["complete"])
            self.assertFalse(expansions[d]["complete"])
        self.assertEqual(g["expansions_closed_by_memory"], 0)

    def test_original_evidence_reuse_does_not_claim_funding_reviewer_or_stage(self):
        g = self.graph
        self.assertEqual(g["originals_closed_by_memory"], 0)
        self.assertEqual(g["human_reviewer_decisions_changed"], 0)
        self.assertEqual(g["hub_records_automatically_staged"], 0)
        self.assertEqual(g["new_reach_publications"], 0)
        self.assertTrue(g["read_only"])
        self.assertFalse(g["public_author_names_or_spark_personnel_indexed"])
        self.assertTrue(all(n["funding_and_same_project_inference"] == "NOT_VERIFIED_BY_MEMORY"
                            and not n["reviewer_approved"] and
                            n["private_hub_status"] == "NOT_VERIFIED" for n in g["nodes"]))
        self.assertTrue(all(x["private_hub_import"] == "NOT_VERIFIED"
                            and not x["funded_by_same_wpo_project"] == True
                            and not x["separate_expansion_complete"] for x in g["links"]))
        # Explicitly prevent person names, email addresses, and speculative
        # author or investigator fields in graph node/edge records.
        for x in g["nodes"] + g["links"] + g["work_items"]:
            self.assertFalse({"authors", "creators", "pi", "collaborators",
                              "email", "investigator"} & set(x))
        for node in g["nodes"]:
            self.assertTrue(node["no_authors_or_spark_personnel_in_graph"])

    def test_research_journal_note_is_reusable_only_as_nonterminal_provenance(self):
        g = self.graph
        journal_nodes = [n for n in g["nodes"]
                         if n["original_research"]["recorded_note_count"] > 0]
        self.assertGreater(len(journal_nodes), 7)
        self.assertTrue(all(n["original_research"]["reuse_prior_notes_before_new_queries"]
                            and not n["original_research"]["formal_original_closed_by_memory"]
                            for n in journal_nodes))
        self.assertTrue(all(
            len(x["source_evidence_file_sha256"]) == x["recorded_note_count"]
            for x in (n["original_research"] for n in journal_nodes)))
        self.assertTrue(all(n["expansion_research"]["separate_expansion_closed_by_memory"] is False
                            for n in journal_nodes))

    def test_explicit_related_child_link_preserved_and_research_remains_open(self):
        g = self.graph
        self.assertGreater(g["explicit_related_output_links"], 1)
        target = next(x for x in g["links"]
                      if x["related_doi"] == "10.1177/10506519261455873")
        self.assertEqual(target["source_doi"], "10.5194/egusphere-2026-5876")
        self.assertTrue(target["source_files"])
        self.assertFalse(target["proven_distinct_eligible_output"])
        self.assertFalse(target["separate_expansion_complete"])
        self.assertTrue(any(x["track"] == "RELATED_OUTPUT"
                            and x["doi"] == target["related_doi"]
                            for x in g["work_items"]))

    def test_each_zenodo_child_preserves_expansion_hold_without_original_closure(self):
        graph=self.graph
        compact=mission_index(graph)
        children={"10.5281/zenodo.4433147","10.5281/zenodo.5057616"}
        for child in children:
            node=next(n for n in graph["nodes"] if n["doi"]==child)
            self.assertEqual(node["original_research"]["recorded_note_count"],0)
            related=node["expansion_research"]
            self.assertEqual(related["recorded_related_note_count"],1)
            self.assertIn("PROJECT_EVIDENCE_HOLD",
                          related["nonterminal_related_dispositions"])
            self.assertTrue(related["reuse_prior_related_notes_before_new_queries"])
            self.assertFalse(related["separate_expansion_closed_by_memory"])
            self.assertIn("10.1029/2021gl096709",related["explicit_parent_dois"])
            self.assertEqual(len(related["related_source_evidence_file_sha256"]),1)
            link=next(x for x in graph["links"] if x["related_doi"]==child
                      and x["source_doi"]=="10.1029/2021gl096709")
            self.assertTrue(any(s["relationship_origin"]==
                "official_sources_verified_related_research_note"
                for s in link["source_files"]))
            self.assertEqual(link["funded_by_same_wpo_project"],"NOT_VERIFIED")
            self.assertFalse(link["separate_expansion_complete"])
            entries=[x for x in compact["recommended_preview"]["additional_related_output"]
                     if x["doi"]==child]
            self.assertEqual(len(entries),1)
            entry=entries[0]
            self.assertEqual(entry["original_prior_note_count"],0)
            self.assertEqual(entry["related_prior_note_count"],1)
            self.assertIn("PROJECT_EVIDENCE_HOLD",entry["related_prior_dispositions"])
            self.assertEqual(entry["next_action"],
                "REUSE_RECORDED_PROJECT_HOLD_REOPEN_ON_DISTINCT_EVIDENCE")
            self.assertFalse(entry["automatically_completed_or_staged"])
        self.assertEqual(graph["human_reviewer_decisions_changed"],0)
        self.assertEqual(graph["originals_closed_by_memory"],0)
        self.assertEqual(graph["expansions_closed_by_memory"],0)

    def test_related_note_change_only_reopens_expansion_fingerprint(self):
        from build_research_outcome_registry import build as registry_build
        journal=registry_build()
        key="10.5281/zenodo.4433147"
        normal=next(n for n in self.graph["nodes"] if n["doi"]==key)
        revised=dict(journal)
        revised["events"]=[dict(e) for e in journal["events"]]
        event=next(e for e in revised["events"] if e.get("doi")==key
                   and e.get("role_in_note")=="related_output")
        event["event_id"]="f" * 24
        with patch("build_crosslane_research_memory.research_registry",return_value=revised):
            updated=build()
        changed=next(n for n in updated["nodes"] if n["doi"]==key)
        self.assertEqual(changed["original_research"]["input_fingerprint"],
                         normal["original_research"]["input_fingerprint"])
        self.assertNotEqual(changed["expansion_research"]["input_fingerprint"],
                            normal["expansion_research"]["input_fingerprint"])
        self.assertFalse(changed["expansion_research"]["separate_expansion_closed_by_memory"])

    def test_related_note_without_independent_proof_adds_no_verified_edge(self):
        from build_research_outcome_registry import build as registry_build
        journal=registry_build()
        revised=dict(journal)
        revised["events"]=[dict(e) for e in journal["events"]]
        for e in revised["events"]:
            if e.get("role_in_note")=="related_output":
                e["relationship_verified_from_two_official_sources"]=False
        with patch("build_crosslane_research_memory.research_registry",return_value=revised):
            graph=build()
        for link in graph["links"]:
            if link["related_doi"] in {
                    "10.5281/zenodo.4433147","10.5281/zenodo.5057616"}:
                self.assertFalse(any(s["relationship_origin"]==
                    "official_sources_verified_related_research_note"
                    for s in link["source_files"]))

    def test_new_relation_changes_expansion_evidence_not_original_identity(self):
        baseline = self.graph
        seed = next(x["doi"] for x in baseline["nodes"]
                    if x["public_reach_verified_existing"])
        baseline_node = next(x for x in baseline["nodes"] if x["doi"] == seed)
        edges, shas = source_links(ROOT)
        extra = "10.9999/new-independent-dataset"
        self.assertNotIn((seed, extra), edges)
        edges[(seed, extra)] = {
            ("scout-operations/monthly-expansion-leads.json", "monthly_related_outputs")}
        self.assertIn("scout-operations/monthly-expansion-leads.json", shas)
        with patch("build_crosslane_research_memory.source_links", return_value=(edges, shas)):
            changed = build()
        node = next(x for x in changed["nodes"] if x["doi"] == seed)
        self.assertEqual(node["original_research"]["input_fingerprint"],
                         baseline_node["original_research"]["input_fingerprint"])
        self.assertNotEqual(node["expansion_research"]["input_fingerprint"],
                            baseline_node["expansion_research"]["input_fingerprint"])
        self.assertIn(extra, node["expansion_research"]["explicit_related_dois"])
        self.assertTrue(any(x["track"] == "RELATED_OUTPUT"
                            and x["doi"] == extra for x in changed["work_items"]))

    def test_tampering_a_research_note_fails_closed(self):
        root = ROOT
        from build_research_outcome_registry import build as journal
        registry = journal()
        with patch("build_crosslane_research_memory.research_registry") as fake:
            fake.return_value = registry.copy()
            shas = dict(registry["source_sha256"])
            target = next(iter(shas))
            shas[target] = "0" * 64
            fake.return_value["source_sha256"] = shas
            with self.assertRaisesRegex(ValueError, "source changed"):
                build(root)

    def test_historical_completed_original_never_reselected(self):
        graph = self.graph
        doi = "10.13012/b2idb-0704763_v1"
        node = next(n for n in graph["nodes"] if n["doi"] == doi)
        self.assertTrue(node["historical_original_verified_terminal"])
        self.assertTrue(node["public_staged_in_scout_manifest"])
        original = next(x for x in graph["work_items"]
                        if x["doi"] == doi and x["track"] == "ORIGINAL")
        self.assertEqual(
            original["next_action"], "REUSE_VERIFIED_PUBLIC_SCOUT_PROPOSAL_NO_REPROPOSAL")
        compact = mission_index(graph)
        self.assertFalse(any(x["doi"] == doi for x in
                             compact["recommended_preview"]["historical_datacite_original"]))
        self.assertGreater(compact["group_counts_before_preview_bound"][
            "existing_public_original_disposition"], 0)
        # Terminal original statuses do not erase separately eligible expansions.
        self.assertTrue(any(x["doi"] == doi and x["track"] == "EXPANSION"
                            for x in graph["work_items"]))

    def test_unsupported_historical_terminal_exceptions_remain_actionable(self):
        compact = mission_index(self.graph)
        open_dois = {x["doi"] for x in
                     compact["recommended_preview"]["historical_datacite_original"]}
        coverage = json.loads((ROOT / "scout-operations/historical-coverage.json").read_text())
        exceptions = json.loads((ROOT / "scout-operations/historical-reconciliation-exceptions.json").read_text())
        held = {n["doi"] for n in self.graph["nodes"]
                if n["preprint_or_version_hold"]}
        expected = {norm_doi(e["identity"]) for e in exceptions["exceptions"]} - held
        if coverage["remaining"] <= compact["max_preview_per_group"]:
            self.assertEqual(open_dois, expected)
        self.assertGreater(compact["group_counts_before_preview_bound"][
            "existing_public_original_disposition"], 0)
        self.assertFalse(any(x["doi"] == "10.13012/b2idb-0704763_v1"
                             for x in compact["recommended_preview"]["historical_datacite_original"]))

    def test_compact_hourly_index_is_bounded_and_maintains_expansion(self):
        m = mission_index(self.graph)
        self.assertEqual(m["source_fingerprint"], self.graph["source_fingerprint"])
        self.assertEqual(m["graph_schema"], SCHEMA)
        self.assertEqual(m["verified_reach_expansion_total_preserved"],
                         self.graph["verified_reach_originals_preserved_as_expansion_seeds"])
        self.assertEqual(m["group_counts_before_preview_bound"]["verified_reach_expansion"],
                         self.graph["verified_reach_originals_preserved_as_expansion_seeds"])
        historical = json.loads((ROOT / "scout-operations/historical-coverage.json").read_text())
        exceptions = json.loads((ROOT / "scout-operations/historical-reconciliation-exceptions.json").read_text())
        held = sum(any(n["doi"] == norm_doi(e["identity"]) and
                       n["preprint_or_version_hold"] for n in self.graph["nodes"])
                   for e in exceptions["exceptions"])
        self.assertEqual(m["group_counts_before_preview_bound"]["historical_datacite_original"],
                         historical["remaining"] - held)
        self.assertGreaterEqual(m["group_counts_before_preview_bound"]["historical_crossref_original"], 50)
        self.assertGreaterEqual(
            m["group_counts_before_preview_bound"]["monthly_related"] +
            m["group_counts_before_preview_bound"]["existing_public_related_or_staged"],
            1)
        self.assertGreaterEqual(m["group_counts_before_preview_bound"]["code_or_url_research"], 1)
        self.assertEqual(m["builder_policy_sha256"], self.graph["builder_policy_sha256"])
        self.assertTrue(all(len(v) <= 12 for v in m["recommended_preview"].values()))
        self.assertTrue(all(not item["automatically_completed_or_staged"]
                            for rows in m["recommended_preview"].values()
                            for item in rows if "automatically_completed_or_staged" in item))
        self.assertFalse(m["reviewer_approval_or_publication_inferred"])
        self.assertFalse(m["spark_author_or_personnel_data_used"])
        self.assertIn("active-workstream.json", m["priority_policy"])
        self.assertLess(len(json.dumps(m)), 65000)
        self.assertEqual(m, mission_index(self.graph))

    def test_monthly_originals_survive_cross_lane_overlap_and_preprints_stay_monthly_only(self):
        g = self.graph
        m = mission_index(g)
        originals = {x["doi"] for x in g["work_items"] if x["track"] == "ORIGINAL"}
        monthly_nodes = [x for x in g["nodes"] if "monthly_api" in x["lanes"]]
        self.assertGreaterEqual(len(monthly_nodes), 13)
        self.assertTrue({x["doi"] for x in monthly_nodes}.issubset(originals))
        not_preprint = [x for x in monthly_nodes if not x["preprint_or_version_hold"]]
        staged_or_noaction = {"staged_for_hub_import", "staged_for_human_review",
                              "pending_human_intake", "already_in_reach",
                              "no_action", "forwarded_to_hub",
                              "metadata_update_forwarded", "human_metadata_needed",
                              "research_complete_human_intake"}
        prior = [x for x in not_preprint
                 if {z.lower() for z in x["public_recorded_statuses_by_lane"]
                     ["monthly_api"]} & staged_or_noaction]
        eligible = [x for x in not_preprint if x not in prior]
        self.assertEqual(m["group_counts_before_preview_bound"]["monthly_original"],
                         len(eligible))
        self.assertEqual(
            m["group_counts_before_preview_bound"]["monthly_existing_public_disposition"],
            len(prior))
        self.assertTrue(all(x["next_action"] in {
            "PUBLIC_STAGING_RECORDED_PRIVATE_IMPORT_NOT_VERIFIED",
            "PUBLIC_NO_ACTION_RECORDED_REOPEN_ONLY_ON_NEW_EVIDENCE"}
            for x in m["recommended_preview"]["monthly_existing_public_disposition"]))
        holds = {x["doi"] for x in g["nodes"]
                 if x["preprint_or_version_hold"] and x["doi"] in originals}
        self.assertEqual(m["group_counts_before_preview_bound"]["preprint_watchlist_only"],
                         len(holds))
        self.assertTrue(all(x["hourly_original_research_allowed"] is False for x in
                            m["recommended_preview"]["preprint_watchlist_only"]))
        self.assertTrue(all(
            "monthly_api" in next(n for n in g["nodes"] if n["doi"] == item["doi"])["lanes"]
            for item in m["recommended_preview"]["monthly_original"]
        ))
        self.assertFalse(
            {x["doi"] for x in m["recommended_preview"]["monthly_original"]} &
            {x["doi"] for x in m["recommended_preview"]["historical_crossref_original"]}
        )

    def test_monthly_existing_public_status_not_misreported_as_private_import(self):
        graph = self.graph
        mini = mission_index(graph)
        remembered = mini["recommended_preview"]["monthly_existing_public_disposition"]
        self.assertGreaterEqual(len(remembered), 8)
        self.assertTrue(all(not r["automatically_completed_or_staged"] for r in remembered))
        self.assertTrue(all("monthly_api" in r["public_recorded_statuses_by_lane"]
                            for r in remembered))
        self.assertFalse(mini["reviewer_approval_or_publication_inferred"])
        self.assertEqual(mini["private_hub_state"], "NOT_VERIFIED")

    def test_public_staged_related_outputs_not_recommended_for_reapproval(self):
        g = self.graph
        m = mission_index(g)
        staged = m["recommended_preview"]["existing_public_related_or_staged"]
        self.assertGreaterEqual(m["group_counts_before_preview_bound"]
                                ["existing_public_related_or_staged"], 1)
        self.assertTrue(all(
            x["next_action"] == "PRESERVE_EXISTING_PUBLIC_STATUS_DO_NOT_RESTAGE"
            for x in staged
        ))
        relevant = [x for x in g["nodes"] if "monthly_related_outputs" in x["lanes"]]
        self.assertGreaterEqual(len(relevant), 6)
        self.assertTrue(all("public_recorded_statuses_by_lane" in x for x in relevant))
        self.assertTrue(all(not x["automatically_completed_or_staged"] for x in staged))

    def test_deterministic_replay_ignores_wall_clock(self):
        self.assertEqual(build()["source_fingerprint"], self.graph["source_fingerprint"])
        self.assertEqual(build()["work_action_counts"], self.graph["work_action_counts"])
        self.assertEqual(build()["nodes"], self.graph["nodes"])


if __name__ == "__main__":
    unittest.main()
