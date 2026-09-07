"""GOV-03 admission regression tests using only original temporary fixtures."""

import copy
from datetime import date
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.source_registry import MANIFEST, ROOT, read_local, strict_json, validate_manifest


TODAY = date(2026, 9, 7)


class SourceRegistryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest = strict_json(read_local(ROOT, MANIFEST))
        self.source = self.manifest["sources"][0]
        self.artifact = self.source["artifacts"][0]
        target = self.root / self.artifact["path"]
        target.parent.mkdir(parents=True)
        target.write_bytes(read_local(ROOT, self.artifact["path"]))

    def codes(self, purpose="research"):
        return {i["code"] for i in validate_manifest(self.manifest, self.root, purpose, TODAY)}

    def child(self):
        child = copy.deepcopy(self.source)
        child["id"] = "SYN-CHILD"
        child["parents"] = [self.source["id"]]
        path = "data/public/child.txt"
        content = b"Original derived fixture.\n"
        (self.root / path).write_bytes(content)
        child["artifacts"] = [{"path": path, "sha256": hashlib.sha256(content).hexdigest()}]
        self.manifest["sources"].append(child)
        return child

    def test_valid_and_denied_purposes(self):
        self.assertEqual(self.codes(), set())
        self.assertEqual(self.codes("redistribution"), set())
        self.assertIn("purpose_denied", self.codes("training"))
        self.assertIn("purpose_denied", self.codes("external_model"))

    def test_permissions_are_strict_booleans(self):
        for value in ("true", 1, None, [], {}):
            with self.subTest(value=value):
                self.source["permissions"]["research"] = value
                self.assertIn("permission_schema", self.codes())
                self.assertIn("purpose_denied", self.codes())

    def test_missing_unknown_permission(self):
        del self.source["permissions"]["research"]
        self.assertIn("purpose_denied", self.codes())
        self.source["permissions"]["typo"] = True
        self.assertIn("permission_schema", self.codes())

    def test_unknown_license(self):
        for value in ("unknown", "", None, " pending "):
            self.source["license"] = value
            self.assertIn("missing_license", self.codes())

    def test_unapproved_status(self):
        for value in ("candidate", "revoked", None):
            self.source["status"] = value
            self.assertIn("not_approved", self.codes())

    def test_period_and_dates(self):
        for start, end in (("2026-09-08", None), ("2026-01-01", "2026-09-06"),
                           ("2026-09-07", "2026-01-01")):
            self.source.update(valid_from=start, valid_until=end)
            self.assertIn("permission_period", self.codes())
        self.source.update(valid_from="2026-09-07", valid_until="2026-09-07")
        self.assertEqual(self.codes(), set())
        self.source["valid_until"] = "2026-02-30"
        self.assertIn("permission_date", self.codes())

    def test_no_fake_fixture_review_for_official_source(self):
        self.source["class"] = "A"
        self.assertIn("fixture_review_scope", self.codes())
        self.source["review"]["kind"] = "human"
        self.source["review"]["evidence_ref"] = ""
        self.assertIn("review_schema", self.codes())

    def test_future_review(self):
        self.source["review"]["reviewed_on"] = "2026-09-08"
        self.assertIn("future_review", self.codes())

    def test_hash_tampering_and_missing_file(self):
        target = self.root / self.artifact["path"]
        target.write_text("Changed", encoding="utf-8")
        self.assertIn("hash_mismatch", self.codes())
        target.unlink()
        self.assertIn("artifact_unreadable", self.codes())

    def test_unsafe_paths(self):
        for value in ("../secret", "/data/public/x", "C:/secret", "data/public/../x",
                      "data/public\\x", "data/public/x:stream", "data//public/x",
                      "data/public/NUL.txt", "data/public/x.", "data/public/./x", []):
            with self.subTest(path=value):
                self.artifact["path"] = value
                self.assertIn("unsafe_artifact_path", self.codes())

    def test_symlink_rejected(self):
        target = self.root / "data/public/link.txt"
        try:
            target.symlink_to(self.root / self.artifact["path"])
        except OSError as exc:
            self.skipTest(f"Symlink creation unavailable: {getattr(exc, 'winerror', exc.errno)}")
        self.artifact["path"] = "data/public/link.txt"
        self.assertIn("artifact_unreadable", self.codes())

    def test_duplicate_ids_and_casefold_paths(self):
        self.manifest["sources"].append(copy.deepcopy(self.source))
        self.assertIn("duplicate_id", self.codes())
        self.manifest["sources"][1]["id"] = "SYN-SECOND"
        self.manifest["sources"][1]["artifacts"][0]["path"] = self.artifact["path"].upper()
        # Uppercase data prefix is rejected, not accepted as a second data root.
        self.assertIn("unsafe_artifact_path", self.codes())
        self.manifest["sources"][1]["artifacts"][0]["path"] = self.artifact["path"]
        self.assertIn("duplicate_path", self.codes())

    def test_lineage_permission_escalation(self):
        child = self.child()
        self.assertEqual(self.codes(), set())
        child["permissions"]["training"] = True
        self.assertIn("lineage_permission_escalation", self.codes())

    def test_missing_parent_and_cycle(self):
        child = self.child()
        self.source["parents"] = [child["id"]]
        self.assertIn("lineage_cycle", self.codes())
        self.source["parents"] = ["UNKNOWN"]
        self.assertIn("missing_parent", self.codes())

    def test_invalid_schema_does_not_crash(self):
        for value in (None, [], {}, {"schema_version": True, "sources": []}):
            self.assertTrue(validate_manifest(value, self.root, today=TODAY))
        for field in self.source:
            with self.subTest(field=field):
                old = self.source[field]
                self.source[field] = None
                if field != "valid_until":
                    self.assertTrue(self.codes())
                self.source[field] = old

    def test_duplicate_json_key(self):
        with self.assertRaises(ValueError):
            strict_json('{"schema_version":1,"schema_version":2}')

    def test_quarantine_and_nonpublic(self):
        content = read_local(self.root, self.artifact["path"])
        for area, issue in (("quarantine", "quarantined"), ("restricted", "not_public")):
            self.artifact["path"] = f"data/{area}/sample.txt"
            target = self.root / self.artifact["path"]
            target.parent.mkdir(parents=True)
            target.write_bytes(content)
            self.assertIn(issue, self.codes("redistribution"))

    def test_external_model_requires_local_input_permission(self):
        self.source["permissions"].update(external_model=True, model_input=False)
        self.assertIn("model_input_required", self.codes("external_model"))

    def test_cli_exit_codes_and_redaction(self):
        target = self.root / MANIFEST
        target.parent.mkdir(parents=True)
        target.write_text(json.dumps(self.manifest), encoding="utf-8")
        command = [sys.executable, "-B", str(ROOT / "scripts/source_registry.py"), "--root", str(self.root)]
        self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
        failed = subprocess.run(command + ["--purpose", "training"], capture_output=True)
        self.assertEqual(failed.returncode, 1)
        self.assertIn(b"purpose_denied", failed.stdout)
        for invalid in ("TOP_SECRET_INVALID_JSON", "[" * 1500 + "]" * 1500):
            target.write_text(invalid, encoding="utf-8")
            failed = subprocess.run(command, capture_output=True)
            self.assertEqual(failed.returncode, 1)
            codes = {item["code"] for item in json.loads(failed.stdout)["issues"]}
            # A deep but valid JSON array may parse on some Python builds; it
            # must still fail the manifest schema, without printing a traceback.
            self.assertTrue(codes & {"manifest_unreadable", "manifest_schema"})
            self.assertNotIn(b"TOP_SECRET", failed.stdout + failed.stderr)
            self.assertNotIn(b"Traceback", failed.stderr)


if __name__ == "__main__":
    unittest.main()
