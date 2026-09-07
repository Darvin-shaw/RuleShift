"""Fail-closed source admission checks; this does not certify legal permission."""

from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import re
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "data/sources/manifest.json"
PURPOSES = ("research", "model_input", "training", "external_model", "redistribution")
AREAS = ("public", "restricted", "quarantine", "derived")
SOURCE_FIELDS = {
    "id", "class", "title", "origin", "license", "status", "review",
    "permissions", "valid_from", "valid_until", "artifacts", "parents",
}


def strict_json(raw: bytes | str) -> object:
    """Reject duplicate JSON keys rather than silently trusting the last value."""
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate_key")
            result[key] = value
        return result

    return json.loads(raw, object_pairs_hook=pairs)


def safe_relative(value: object) -> bool:
    """Use a portable, conservative ASCII path subset (no ADS or dot segments)."""
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_./-]+", value):
        return False
    parts = value.split("/")
    return all(
        p not in ("", ".", "..") and not p.endswith(".")
        and not re.fullmatch(r"(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?", p)
        for p in parts
    )


def read_local(root: Path, relative: str) -> bytes:
    """Reject symlinks/junctions, including links that stay inside the root."""
    if not safe_relative(relative):
        raise ValueError("unsafe_path")
    root = root.resolve()
    target = root
    for part in relative.split("/"):
        target = target / part
        if target.is_symlink() or target.is_junction():
            raise ValueError("linked_path")
    if not target.resolve().is_relative_to(root):
        raise ValueError("escaped_path")
    return target.read_bytes()


def parse_date(value: object) -> date:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("invalid_date")
    return date.fromisoformat(value)


def validate_manifest(
    manifest: object,
    root: Path,
    purpose: str = "research",
    today: date | None = None,
    reader: Callable[[str], bytes] | None = None,
) -> list[dict]:
    """Validate every registered source for one purpose; return redacted issues."""
    issues = []
    today = today or date.today()
    reader = reader or (lambda path: read_local(root, path))

    def error(code, row=None):
        issues.append({"code": code, "row": row})

    if purpose not in PURPOSES:
        error("invalid_purpose")
        return issues
    if (not isinstance(manifest, dict) or set(manifest) != {"schema_version", "sources"}
            or type(manifest.get("schema_version")) is not int or manifest["schema_version"] != 1
            or not isinstance(manifest.get("sources"), list) or not manifest["sources"]):
        error("manifest_schema")
        return issues
    records = {}
    paths = set()
    for row, source in enumerate(manifest["sources"]):
        if not isinstance(source, dict) or set(source) != SOURCE_FIELDS:
            error("source_schema", row)
            continue
        sid = source["id"]
        if not isinstance(sid, str) or not re.fullmatch(r"[A-Z][A-Z0-9_-]{2,79}", sid):
            error("invalid_id", row)
            continue
        if sid in records:
            error("duplicate_id", row)
            continue
        records[sid] = (row, source)
        for field in ("title", "origin", "license"):
            value = source[field]
            if (not isinstance(value, str) or not value.strip()
                    or value.strip().lower() in {"unknown", "pending", "unverified", "n/a"}):
                error("missing_" + field, row)
        if source["class"] not in ("A", "B", "C", "S"):
            error("source_class", row)
        if source["status"] != "approved":
            error("not_approved", row)
        permissions = source["permissions"]
        if (not isinstance(permissions, dict) or set(permissions) != set(PURPOSES)
                or any(type(v) is not bool for v in permissions.values())):
            error("permission_schema", row)
        if not isinstance(permissions, dict) or permissions.get(purpose) is not True:
            error("purpose_denied", row)
        if purpose == "external_model" and (
                not isinstance(permissions, dict) or permissions.get("model_input") is not True):
            error("model_input_required", row)
        review = source["review"]
        if (not isinstance(review, dict)
                or set(review) != {"kind", "reviewer", "reviewed_on", "evidence_ref"}
                or any(not isinstance(v, str) or not v.strip() for v in review.values())):
            error("review_schema", row)
        else:
            if review["kind"] == "technical_fixture":
                if (source["class"] != "S" or not sid.startswith("SYN-")
                        or not str(source["origin"]).startswith("project:original/")
                        or review["reviewer"] != "codex:technical-fixture"):
                    error("fixture_review_scope", row)
            elif review["kind"] != "human":
                error("review_kind", row)
            try:
                if parse_date(review["reviewed_on"]) > today:
                    error("future_review", row)
            except ValueError:
                error("review_date", row)
        try:
            start = parse_date(source["valid_from"])
            end = parse_date(source["valid_until"]) if source["valid_until"] is not None else None
            if start > today or (end is not None and (end < today or end < start)):
                error("permission_period", row)
        except ValueError:
            error("permission_date", row)
        parents = source["parents"]
        if (not isinstance(parents, list) or any(not isinstance(p, str) for p in parents)
                or (all(isinstance(p, str) for p in parents) and len(set(parents)) != len(parents))):
            error("parent_schema", row)
        artifacts = source["artifacts"]
        if not isinstance(artifacts, list) or not artifacts:
            error("artifact_schema", row)
            continue
        for artifact in artifacts:
            if not isinstance(artifact, dict) or set(artifact) != {"path", "sha256"}:
                error("artifact_schema", row)
                continue
            path = artifact["path"]
            if not safe_relative(path) or not any(path.startswith(f"data/{area}/") for area in AREAS):
                error("unsafe_artifact_path", row)
                continue
            if path.casefold() in paths:
                error("duplicate_path", row)
            paths.add(path.casefold())
            if path.startswith("data/quarantine/"):
                error("quarantined", row)
            if purpose == "redistribution" and not path.startswith("data/public/"):
                error("not_public", row)
            digest = artifact["sha256"]
            if not isinstance(digest, str) or not re.fullmatch("[0-9a-f]{64}", digest):
                error("hash_schema", row)
                continue
            try:
                if hashlib.sha256(reader(path)).hexdigest() != digest:
                    error("hash_mismatch", row)
            except (OSError, ValueError):
                error("artifact_unreadable", row)

    # Parent-first Kahn traversal: bounded by graph size, no recursion-depth escape.
    indegree = {sid: 0 for sid in records}
    children = {sid: [] for sid in records}
    for sid, (row, source) in records.items():
        parents = source["parents"]
        if not isinstance(parents, list):
            continue
        for parent in parents:
            if not isinstance(parent, str) or parent not in records:
                error("missing_parent", row)
                continue
            indegree[sid] += 1
            children[parent].append(sid)
            upstream = records[parent][1]["permissions"]
            current = source["permissions"]
            if isinstance(upstream, dict) and isinstance(current, dict):
                for use in PURPOSES:
                    if current.get(use) is True and upstream.get(use) is not True:
                        error("lineage_permission_escalation", row)
    ready = [sid for sid, degree in indegree.items() if degree == 0]
    visited = 0
    while ready:
        sid = ready.pop()
        visited += 1
        for child in children[sid]:
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
    if visited != len(records):
        error("lineage_cycle")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--purpose", choices=PURPOSES, default="research")
    args = parser.parse_args()
    try:
        manifest = strict_json(read_local(args.root, MANIFEST))
        issues = validate_manifest(manifest, args.root, args.purpose)
    except (OSError, ValueError, UnicodeError, RecursionError):
        issues = [{"code": "manifest_unreadable", "row": None}]
    print(json.dumps({"ok": not issues, "purpose": args.purpose, "issues": issues}))
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
