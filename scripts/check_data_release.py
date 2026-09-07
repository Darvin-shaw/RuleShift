"""Read-only checks of public data and the actual Git index; not a DLP guarantee."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
from typing import Callable

if __package__:
    from .source_registry import MANIFEST, ROOT, read_local, safe_relative, strict_json, validate_manifest
else:
    from source_registry import MANIFEST, ROOT, read_local, safe_relative, strict_json, validate_manifest


TEXT_SUFFIXES = {".txt", ".md", ".json", ".jsonl", ".csv"}
MAX_TEXT_BYTES = 8 * 1024 * 1024
PATTERNS = {
    "possible_phone": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    "possible_identity": re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)"),
    "possible_email": re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"),
    "possible_secret": re.compile(
        r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
        r"|\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,})"
        r"|(?i:[\"']?(?:api[_-]?key|access[_-]?token|secret|password)[\"']?\s*[:=]\s*[\"']?[^\s\"',}]{8,})"
    ),
}


def issue(code: str, path: str = "") -> dict:
    # Paths may themselves contain sensitive identifiers; never print raw unsafe paths.
    display = path if safe_relative(path) and not any(p.search(path) for p in PATTERNS.values()) else "<redacted>"
    return {"code": code, "path": display}


def scan_text(path: str, raw: bytes) -> list[dict]:
    """Allow only bounded UTF-8 text; scan heuristics never return matched content."""
    if Path(path).suffix.lower() not in TEXT_SUFFIXES:
        return [issue("unsupported_file_type", path)]
    if len(raw) > MAX_TEXT_BYTES:
        return [issue("file_too_large", path)]
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeError:
        return [issue("not_utf8_text", path)]
    if any(ord(c) < 32 and c not in "\n\r\t" for c in text):
        return [issue("binary_or_control_content", path)]
    return [issue(code, path) for code, pattern in PATTERNS.items() if pattern.search(text) or pattern.search(path)]


def check_snapshot(root: Path, paths: list[str], reader: Callable[[str], bytes]) -> list[dict]:
    """Check a consistent manifest/data view, either the worktree or index blobs."""
    issues = []
    try:
        raw = reader(MANIFEST)
        issues.extend(scan_text(MANIFEST, raw))
        manifest = strict_json(raw)
        issues.extend(validate_manifest(manifest, root, "redistribution", reader=reader))
    except (OSError, ValueError, UnicodeError, RecursionError):
        manifest = {}
        issues.append(issue("manifest_unreadable", MANIFEST))
    registered = set()
    if isinstance(manifest, dict) and isinstance(manifest.get("sources"), list):
        for source in manifest["sources"]:
            if isinstance(source, dict) and isinstance(source.get("artifacts"), list):
                for artifact in source["artifacts"]:
                    if isinstance(artifact, dict) and isinstance(artifact.get("path"), str):
                        registered.add(artifact["path"])
    for path in paths:
        if not safe_relative(path):
            issues.append(issue("unsafe_public_path", path))
            continue
        if path == MANIFEST:
            continue
        if not path.startswith("data/public/") or path not in registered:
            issues.append(issue("unregistered_public_file", path))
        try:
            issues.extend(scan_text(path, reader(path)))
        except (OSError, ValueError):
            issues.append(issue("public_file_unreadable", path))
    return issues


def check_worktree(root: Path) -> list[dict]:
    """Walk public/source trees without following links, junctions or hidden files exemptions."""
    root = root.resolve()
    paths = []
    issues = []
    data = root / "data"
    if data.is_symlink() or data.is_junction():
        return [issue("linked_directory", "data")]
    stack = [data / "public", data / "sources"]
    while stack:
        path = stack.pop()
        relative = path.relative_to(root).as_posix()
        try:
            if path.is_symlink() or path.is_junction():
                issues.append(issue("linked_path", relative))
            elif path.is_dir():
                stack.extend(path.iterdir())
            elif path.is_file():
                paths.append(relative)
            else:
                issues.append(issue("missing_or_special_path", relative))
        except OSError:
            issues.append(issue("directory_unreadable", relative))
    issues.extend(check_snapshot(root, sorted(paths), lambda p: read_local(root, p)))
    return issues


def restricted_path(path: str) -> bool:
    normalized = path.replace("\\", "/").casefold()
    parts = normalized.split("/")
    name = parts[-1]
    return (
        any(normalized == f"data/{area}" or normalized.startswith(f"data/{area}/")
            for area in ("restricted", "quarantine", "derived", "generated"))
        or any(part == ".env" or (part.startswith(".env.") and part != ".env.example") for part in parts)
        or name in {"id_rsa", "id_ed25519", "credentials.json"}
        or Path(name).suffix in {".pem", ".key", ".p12", ".pfx"}
    )


def git(root: Path, *args: str) -> bytes:
    """No shell interpolation; errors deliberately omit command output/content."""
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, timeout=30)
    if result.returncode:
        raise ValueError("git_failed")
    return result.stdout


def check_index(root: Path) -> list[dict]:
    """Read captured blob IDs, not worktree files or a later mutable index lookup."""
    issues = []
    entries = {}
    try:
        # Reject a nested --root that would make Git interpret paths against a parent repo.
        top = Path(git(root, "rev-parse", "--show-toplevel").decode("utf-8").strip()).resolve()
        if top != root.resolve():
            return [issue("git_root_mismatch")]
        for item in git(root, "ls-files", "--stage", "-z").split(b"\0"):
            if not item:
                continue
            header, raw_path = item.split(b"\t", 1)
            mode, oid, stage = header.decode("ascii").split()
            path = raw_path.decode("utf-8")
            if stage != "0":
                issues.append(issue("unmerged_index", path))
                continue
            if mode not in ("100644", "100755"):
                issues.append(issue("linked_or_special_index_entry", path))
                continue
            if restricted_path(path):
                issues.append(issue("restricted_index_path", path))
            entries[path] = oid
        cache = {}

        def reader(path):
            if path not in entries:
                raise ValueError("missing_index_blob")
            if path not in cache:
                cache[path] = git(root, "cat-file", "blob", entries[path])
            return cache[path]

        public = [p for p in entries if p.casefold().startswith(("data/public/", "data/sources/"))]
        issues.extend(check_snapshot(root, sorted(public), reader))
    except (OSError, ValueError, UnicodeError, subprocess.TimeoutExpired):
        issues.append(issue("git_index_unreadable"))
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    workspace = check_worktree(args.root)
    index = check_index(args.root)
    print(json.dumps({"ok": not (workspace or index), "worktree": workspace, "index": index}))
    return 1 if workspace or index else 0


if __name__ == "__main__":
    raise SystemExit(main())
