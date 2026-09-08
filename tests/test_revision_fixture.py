"""Independent expectations for the original revision challenge fixture."""

from datetime import date
import json
import unittest

from scripts.generate_revision_fixture import OUTPUT, fixture_bytes


class RevisionFixtureTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(OUTPUT.read_bytes())

    def test_reproducible_bytes(self):
        self.assertEqual(OUTPUT.read_bytes(), fixture_bytes())

    def test_candidate_labels(self):
        expected = {
            "threshold": [("支持", "支持"), ("支持", "否定"),
                          ("否定", "否定"), ("无法确定", "无法确定")],
            "exception": [("支持", "支持"), ("支持", "否定"),
                          ("否定", "否定"), ("支持", "无法确定")],
            "wording": [("支持", "支持"), ("否定", "否定"),
                        ("无法确定", "无法确定"), ("支持", "支持")],
        }
        self.assertEqual(len(self.data["families"]), 3)
        for family in self.data["families"]:
            actual = [tuple(j["candidate_label"] for j in p["judgments"])
                      for p in family["pairs"]]
            self.assertEqual(actual, expected[family["revision_type"]])

    def test_references_time_missing_facts_and_isolation(self):
        ids = set()
        for family in self.data["families"]:
            self.assertEqual(family["split"], "technical_fixture")
            versions = {v["version_id"]: v for v in family["versions"]}
            self.assertEqual(len(versions), 2)
            self.assertEqual(family["versions"][0]["valid_until"],
                             family["versions"][1]["valid_from"])
            for pair in family["pairs"]:
                self.assertNotIn(pair["pair_id"], ids)
                ids.add(pair["pair_id"])
                labels = [j["candidate_label"] for j in pair["judgments"]]
                self.assertEqual(pair["expected_change"], labels[0] != labels[1])
                self.assertEqual({j["version_id"] for j in pair["judgments"]}, set(versions))
                for judgment in pair["judgments"]:
                    version = versions[judgment["version_id"]]
                    self.assertEqual(judgment["evidence"], version["text"])
                    target = date.fromisoformat(judgment["target_time"])
                    self.assertGreaterEqual(target, date.fromisoformat(version["valid_from"]))
                    if version["valid_until"]:
                        self.assertLess(target, date.fromisoformat(version["valid_until"]))
                    self.assertEqual(bool(judgment["missing_facts"]),
                                     judgment["candidate_label"] == "无法确定")
                    self.assertTrue(set(judgment["missing_facts"]).isdisjoint(pair["facts"]))
        self.assertEqual(len(ids), 12)
