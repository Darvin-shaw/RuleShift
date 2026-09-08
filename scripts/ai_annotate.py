"""Generate and validate machine-only annotations for the revision fixture."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

if __package__:
    from .generate_revision_fixture import OUTPUT as SOURCE
else:
    from generate_revision_fixture import OUTPUT as SOURCE


ROOT = SOURCE.parents[1]
ALLOWED = {"支持", "否定", "无法确定"}
ALGORITHM = "codex-rule-projection-v1"


def load_source(path: Path = SOURCE) -> tuple[bytes, dict]:
    raw = path.read_bytes()
    return raw, json.loads(raw)


def build_annotations(raw: bytes, fixture: dict) -> dict:
    """Project fixture candidates into a provenance-labelled machine result."""
    tasks = []
    for family in fixture["families"]:
        versions = {v["version_id"]: v for v in family["versions"]}
        for pair in family["pairs"]:
            for judgment in pair["judgments"]:
                version = versions[judgment["version_id"]]
                label = judgment["candidate_label"]
                missing = list(judgment["missing_facts"])
                if label == "支持":
                    reason = "给定事实满足条款条件，未发现阻止结论的例外。"
                elif label == "否定":
                    reason = "给定事实触发条款中的禁止条件。"
                else:
                    reason = "缺少决定性事实，无法确定命题。"
                tasks.append({
                    "task_id": f"{pair['pair_id']}:{version['version_id']}",
                    "family_id": family["family_id"],
                    "version_id": version["version_id"],
                    "target_time": judgment["target_time"],
                    "facts": pair["facts"],
                    "claim": pair["claim"],
                    "label": label,
                    "evidence": version["text"],
                    "missing_facts": missing,
                    "reason": reason,
                })
    return {
        "schema_version": 1,
        "status": "machine_generated",
        "annotator": "codex-assistant",
        "algorithm": ALGORITHM,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "tasks": tasks,
    }


def validate(result: object, raw: bytes, fixture: dict) -> list[str]:
    """Validate provenance and structure without claiming semantic expertise."""
    if not isinstance(result, dict):
        return ["invalid_result"]
    errors = set()
    if result.get("schema_version") != 1:
        errors.add("invalid_schema")
    if result.get("status") != "machine_generated":
        errors.add("invalid_status")
    if result.get("annotator") != "codex-assistant":
        errors.add("invalid_annotator")
    if result.get("algorithm") != ALGORITHM:
        errors.add("invalid_algorithm")
    if result.get("source_sha256") != hashlib.sha256(raw).hexdigest():
        errors.add("source_changed")
    expected = build_annotations(raw, fixture)
    tasks = result.get("tasks")
    if not isinstance(tasks, list) or len(tasks) != len(expected["tasks"]):
        return sorted(errors | {"task_coverage"})
    ids = set()
    for task in tasks:
        if not isinstance(task, dict) or not isinstance(task.get("task_id"), str):
            errors.add("invalid_task")
            continue
        if task["task_id"] in ids:
            errors.add("duplicate_task")
        ids.add(task["task_id"])
        if task["label"] not in ALLOWED:
            errors.add("invalid_label")
        if not isinstance(task["evidence"], str) or not task["evidence"].strip():
            errors.add("invalid_evidence")
        if task["label"] == "无法确定" and not task["missing_facts"]:
            errors.add("missing_fact_reason")
        if task["label"] != "无法确定" and task["missing_facts"]:
            errors.add("unexpected_missing_facts")
    if ids != {t["task_id"] for t in expected["tasks"]}:
        errors.add("task_coverage")
    return sorted(errors)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", type=Path)
    parser.add_argument("--source", type=Path, default=SOURCE)
    args = parser.parse_args()
    if bool(args.output) == bool(args.check):
        parser.error("choose exactly one of --output or --check")
    try:
        raw, fixture = load_source(args.source)
        if args.output:
            args.output.write_text(json.dumps(build_annotations(raw, fixture), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
            issues = []
        else:
            issues = validate(json.loads(args.check.read_text(encoding="utf-8")), raw, fixture)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        issues = ["invalid_input_or_output"]
    print(json.dumps({"ok": not issues, "issues": issues}, ensure_ascii=False))
    return int(bool(issues))


if __name__ == "__main__":
    raise SystemExit(main())
