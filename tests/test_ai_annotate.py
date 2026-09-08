"""Tests for provenance-labelled AI-only annotations."""

import copy
import json
import unittest

from scripts.ai_annotate import ALGORITHM, build_annotations, load_source, validate


class AIAnnotationTests(unittest.TestCase):
    def setUp(self):
        self.raw, self.fixture = load_source()
        self.result = build_annotations(self.raw, self.fixture)

    def test_machine_provenance_and_coverage(self):
        self.assertEqual(self.result["status"], "machine_generated")
        self.assertEqual(self.result["annotator"], "codex-assistant")
        self.assertEqual(self.result["algorithm"], ALGORITHM)
        self.assertEqual(len(self.result["tasks"]), 24)
        self.assertEqual(validate(self.result, self.raw, self.fixture), [])

    def test_tampering_and_missing_tasks_fail(self):
        changed = copy.deepcopy(self.result)
        changed["tasks"][0]["label"] = "专家确认"
        self.assertIn("invalid_label", validate(changed, self.raw, self.fixture))
        changed = copy.deepcopy(self.result)
        changed["tasks"].pop()
        self.assertIn("task_coverage", validate(changed, self.raw, self.fixture))

    def test_wrong_provenance_rejected(self):
        changed = copy.deepcopy(self.result)
        changed["status"] = "human_reviewed"
        changed["annotator"] = "expert"
        self.assertIn("invalid_status", validate(changed, self.raw, self.fixture))
        self.assertIn("invalid_annotator", validate(changed, self.raw, self.fixture))
