"""GOV-04 adversarial worktree/index tests in disposable Git repositories."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from scripts.check_data_release import check_index, check_worktree, git, scan_text
from scripts.source_registry import MANIFEST, ROOT, read_local, strict_json


class DataReleaseTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest = strict_json(read_local(ROOT, MANIFEST))
        self.manifest["sources"] = self.manifest["sources"][:1]
        self.artifact = self.manifest["sources"][0]["artifacts"][0]
        self.write(self.artifact["path"], read_local(ROOT, self.artifact["path"]))
        self.save_manifest()
        git(self.root, "init", "--quiet")
        git(self.root, "config", "core.autocrlf", "false")
        git(self.root, "add", "-A")

    def write(self, path, content):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)

    def save_manifest(self):
        self.write(MANIFEST, json.dumps(self.manifest).encode("utf-8"))

    def codes(self, index=False):
        return {i["code"] for i in (check_index(self.root) if index else check_worktree(self.root))}

    def test_valid_worktree_and_index(self):
        self.assertEqual(self.codes(), set())
        self.assertEqual(self.codes(True), set())

    def test_unregistered_even_when_ignored(self):
        self.write(".gitignore", b"data/public/extra.txt\n")
        self.write("data/public/extra.txt", b"unregistered\n")
        self.assertIn("unregistered_public_file", self.codes())
        self.assertEqual(self.codes(True), set())

    def test_force_added_restricted_files(self):
        for path in ("data/restricted/a.txt", "data/quarantine/a.txt", "data/derived/a.txt",
                     "data/generated/a.txt", "nested/.env", "nested/.env.production",
                     "secret.pem", "credentials.json", "Data/Restricted/case.txt"):
            self.write(path, b"SYNTHETIC_RESTRICTED_FIXTURE\n")
        self.write(".gitignore", b"data/restricted/\n.env\n")
        git(self.root, "add", "-f", "-A")
        issues = check_index(self.root)
        self.assertEqual(sum(i["code"] == "restricted_index_path" for i in issues), 9)

    def test_staged_secret_not_hidden_by_clean_worktree(self):
        clean = read_local(self.root, self.artifact["path"])
        secret = b"api_key=synthetic_fixture_value_only\n"
        self.write(self.artifact["path"], secret)
        git(self.root, "add", "-A")
        self.write(self.artifact["path"], clean)
        self.assertEqual(self.codes(), set())
        self.assertIn("possible_secret", self.codes(True))
        self.assertIn("hash_mismatch", self.codes(True))

    def test_staged_manifest_not_hidden_by_clean_worktree(self):
        clean = read_local(self.root, MANIFEST)
        self.manifest["sources"][0]["permissions"]["redistribution"] = False
        self.save_manifest()
        git(self.root, "add", "-A")
        self.write(MANIFEST, clean)
        self.assertEqual(self.codes(), set())
        self.assertIn("purpose_denied", self.codes(True))

    def test_secret_patterns_are_redacted(self):
        for content, code in ((b"13900000000", "possible_phone"),
                              (b"110000200001010000", "possible_identity"),
                              (b"fixture@example.invalid", "possible_email"),
                              (b"password=synthetic_only", "possible_secret")):
            issues = scan_text("data/public/test.txt", content)
            self.assertIn(code, {i["code"] for i in issues})
            self.assertNotIn(content.decode(), json.dumps(issues))
        issues = scan_text("data/public/13900000000.txt", b"fixture")
        self.assertNotIn("13900000000", json.dumps(issues))

    def test_metadata_is_scanned(self):
        self.manifest["sources"][0]["title"] = "fixture@example.invalid"
        self.save_manifest()
        self.assertIn("possible_email", self.codes())

    def test_binary_archive_and_unknown_extensions(self):
        for path, content in (("data/public/file.zip", b"PK\x03\x04"),
                              ("data/public/file.txt", b"PK\x03\x04"),
                              ("data/public/file.txt", b"\xff\xfe\x00"),
                              ("data/public/file.pdf", b"%PDF original fixture")):
            with self.subTest(path=path, content=content):
                self.assertTrue(scan_text(path, content))

    def test_oversized_text(self):
        with patch("scripts.check_data_release.MAX_TEXT_BYTES", 3):
            self.assertEqual(scan_text("data/public/x.txt", b"1234")[0]["code"], "file_too_large")

    def test_registered_sensitive_file_still_rejected(self):
        content = b"api_key=synthetic_fixture_value_only\n"
        self.write(self.artifact["path"], content)
        self.artifact["sha256"] = hashlib.sha256(content).hexdigest()
        self.save_manifest()
        self.assertIn("possible_secret", self.codes())
        self.assertNotIn("hash_mismatch", self.codes())

    def test_missing_index_manifest(self):
        git(self.root, "rm", "--cached", "--", MANIFEST)
        self.assertIn("manifest_unreadable", self.codes(True))

    def test_unknown_registry_file(self):
        self.write("data/sources/unreviewed.json", b"{}")
        self.assertIn("unregistered_public_file", self.codes())

    def test_git_symlink_mode_without_os_symlink_privilege(self):
        oid = git(self.root, "hash-object", "--", MANIFEST).decode().strip()
        git(self.root, "update-index", "--add", "--cacheinfo", f"120000,{oid},data/public/link.txt")
        self.assertIn("linked_or_special_index_entry", self.codes(True))

    def test_index_reader_uses_captured_blobs(self):
        # Removing a worktree file must not affect inspection of the staged snapshot.
        (self.root / self.artifact["path"]).unlink()
        self.assertEqual(self.codes(True), set())
        self.assertIn("artifact_unreadable", self.codes())

    @unittest.skipUnless(os.name == "nt", "Windows junction test")
    def test_windows_junction_rejected(self):
        target = self.root / "outside-public"
        target.mkdir()
        link = self.root / "data/public/junction"
        command = ("$ErrorActionPreference='Stop'; New-Item -ItemType Junction "
                   "-Path $env:RULESHIFT_TEST_LINK -Target $env:RULESHIFT_TEST_TARGET | Out-Null")
        environment = dict(os.environ, RULESHIFT_TEST_LINK=str(link), RULESHIFT_TEST_TARGET=str(target))
        # Pass temporary paths as data, not interpolated PowerShell source.
        result = subprocess.run(["powershell", "-NoProfile", "-Command", command],
                                env=environment, capture_output=True, timeout=30)
        if result.returncode:
            self.fail("Could not create junction fixture")
        self.assertTrue(link.is_junction())
        self.assertIn("linked_path", self.codes())
        with self.assertRaises(ValueError):
            read_local(self.root, "data/public/junction/anything.txt")

    def test_non_repository_and_nested_root_rejected(self):
        with tempfile.TemporaryDirectory() as other:
            self.assertIn("git_index_unreadable", {i["code"] for i in check_index(Path(other))})
        self.assertIn("git_root_mismatch", {i["code"] for i in check_index(self.root / "data")})

    def test_cli_rejects_and_never_echoes_sensitive_text(self):
        command = [sys.executable, "-B", str(ROOT / "scripts/check_data_release.py"), "--root", str(self.root)]
        self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
        self.write("data/public/extra.txt", b"password=synthetic_fixture_secret\n")
        failed = subprocess.run(command, capture_output=True)
        self.assertEqual(failed.returncode, 1)
        self.assertNotIn(b"synthetic_fixture_secret", failed.stdout + failed.stderr)
        self.write(MANIFEST, b"[" * 1500 + b"]" * 1500)
        failed = subprocess.run(command, capture_output=True)
        self.assertEqual(failed.returncode, 1)
        codes = {item["code"] for item in json.loads(failed.stdout)["worktree"]}
        self.assertTrue(codes & {"manifest_unreadable", "manifest_schema"})
        self.assertNotIn(b"Traceback", failed.stderr)


if __name__ == "__main__":
    unittest.main()
