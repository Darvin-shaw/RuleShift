"""Test annotation integrity without claiming human annotation has occurred."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.annotation_tasks import build_form, export_forms, validate_form
from scripts.generate_revision_fixture import OUTPUT


class AnnotationTaskTests(unittest.TestCase):
    def setUp(self):
        self.raw = OUTPUT.read_bytes()
        self.form = build_form(self.raw)

    def completed(self):
        form = copy.deepcopy(self.form)
        form["annotator"] = "test-only-not-a-human-review"
        for task in form["tasks"]:
            task.update(label="支持", evidence=task["version"]["text"], reason="test-only")
        return form

    def test_export_is_blind_and_incomplete(self):
        self.assertEqual(len(self.form["tasks"]), 24)
        serialized = json.dumps(self.form)
        for field in ("candidate_label", "expected_change", "judgments", "revision_type"):
            self.assertNotIn(field, serialized)
        self.assertIn("invalid_label", validate_form(self.form, self.raw))
        self.assertIn("missing_annotator", validate_form(self.form, self.raw))

    def test_complete_format_is_not_semantic_certification(self):
        self.assertEqual(validate_form(self.completed(), self.raw), [])

    def test_duplicate_missing_and_unknown_tasks_rejected(self):
        for mutation in ("duplicate", "missing", "unknown"):
            form = self.completed()
            if mutation == "duplicate":
                form["tasks"][-1] = form["tasks"][0]
            elif mutation == "missing":
                form["tasks"].pop()
            else:
                form["tasks"][0]["task_id"] = "unknown"
            self.assertIn("task_coverage", validate_form(form, self.raw))

    def test_modified_prompt_or_source_rejected(self):
        for field, value in (("facts", {}), ("target_time", "2099-01-01"), ("claim", "changed")):
            form = self.completed()
            form["tasks"][0][field] = value
            self.assertIn("prompt_changed", validate_form(form, self.raw))
        form = self.completed()
        form["source_sha256"] = "0" * 64
        self.assertIn("source_changed", validate_form(form, self.raw))

    def test_invalid_answers_and_types_fail_closed(self):
        cases = [("label", [], "invalid_label"), ("evidence", "invented", "invalid_evidence"),
                 ("reason", " ", "missing_reason"), ("missing_facts", [0], "invalid_missing_facts"),
                 ("missing_facts", ["defects"], "invalid_missing_facts")]
        for field, value, error in cases:
            form = self.completed()
            form["tasks"][0][field] = value
            self.assertIn(error, validate_form(form, self.raw))
        form = self.completed()
        form["tasks"][0]["label"] = "无法确定"
        self.assertIn("invalid_missing_facts", validate_form(form, self.raw))

    def test_reordering_is_allowed(self):
        form = self.completed()
        form["tasks"].reverse()
        self.assertEqual(validate_form(form, self.raw), [])

    def test_export_never_overwrites(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "forms"
            export_forms(output, self.raw)
            path = output / "annotator-a.json"
            self.assertEqual(json.loads(path.read_bytes()), self.form)
            path.write_bytes(b"existing work")
            with self.assertRaises(FileExistsError):
                export_forms(output, self.raw)
            self.assertEqual(path.read_bytes(), b"existing work")

    def test_cli_rejects_duplicate_keys_and_redacts_input(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "bad.json"
            path.write_text('{"sensitive-marker":1,"sensitive-marker":2}', encoding="utf-8")
            command = [sys.executable, "-B", str(OUTPUT.parents[2] / "scripts/annotation_tasks.py"), "check", str(path)]
            result = subprocess.run(command, capture_output=True)
            self.assertEqual(result.returncode, 1)
            self.assertNotIn(b"sensitive-marker", result.stdout + result.stderr)
