"""Export blind technical annotation tasks and validate completed forms."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

if __package__:
    from .generate_revision_fixture import OUTPUT
    from .source_registry import strict_json
else:
    from generate_revision_fixture import OUTPUT
    from source_registry import strict_json


LABELS = {"支持", "否定", "无法确定"}
ANSWER_FIELDS = {"label", "evidence", "missing_facts", "reason"}


def build_form(raw: bytes) -> dict:
    """Exclude candidate answers and paired outcomes from the annotation view."""
    fixture = strict_json(raw)
    tasks = []
    for family in fixture["families"]:
        versions = {v["version_id"]: v for v in family["versions"]}
        for pair in family["pairs"]:
            for judgment in pair["judgments"]:
                version = versions[judgment["version_id"]]
                tasks.append(dict(
                    task_id=f"{pair['pair_id']}:{version['version_id']}",
                    family_id=family["family_id"], version=version,
                    facts=pair["facts"], claim=pair["claim"],
                    target_time=judgment["target_time"],
                    label=None, evidence=None, missing_facts=[], reason=None,
                ))
    return dict(schema_version=1, source_sha256=hashlib.sha256(raw).hexdigest(),
                annotator=None, tasks=tasks)


def validate_form(form: object, raw: bytes) -> list[str]:
    """Check immutable prompts and completed fields, never certify human review."""
    expected = build_form(raw)
    if not isinstance(form, dict) or set(form) != set(expected):
        return ["invalid_form"]
    errors = set()
    if type(form["schema_version"]) is not int or form["schema_version"] != 1:
        errors.add("invalid_schema")
    if form["source_sha256"] != expected["source_sha256"]:
        errors.add("source_changed")
    if not isinstance(form["annotator"], str) or not form["annotator"].strip():
        errors.add("missing_annotator")
    tasks = form["tasks"]
    if not isinstance(tasks, list) or len(tasks) != len(expected["tasks"]):
        return sorted(errors | {"task_coverage"})
    reference = {t["task_id"]: t for t in expected["tasks"]}
    seen = set()
    for task in tasks:
        if not isinstance(task, dict) or not isinstance(task.get("task_id"), str):
            errors.add("invalid_task")
            continue
        key = task["task_id"]
        if key not in reference or key in seen:
            errors.add("task_coverage")
            continue
        seen.add(key)
        original = reference[key]
        if set(task) != set(original) or any(
            json.dumps(task.get(k), sort_keys=True, ensure_ascii=False)
            != json.dumps(v, sort_keys=True, ensure_ascii=False)
            for k, v in original.items() if k not in ANSWER_FIELDS
        ):
            errors.add("prompt_changed")
        label = task.get("label")
        if not isinstance(label, str) or label not in LABELS:
            errors.add("invalid_label")
        evidence = task.get("evidence")
        if not isinstance(evidence, str) or not evidence.strip() or evidence not in original["version"]["text"]:
            errors.add("invalid_evidence")
        reason = task.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            errors.add("missing_reason")
        missing = task.get("missing_facts")
        if not isinstance(missing, list) or any(not isinstance(x, str) or not x.strip() for x in missing):
            errors.add("invalid_missing_facts")
        elif len(set(missing)) != len(missing) or any(x in original["facts"] for x in missing):
            errors.add("invalid_missing_facts")
        elif (label == "无法确定") != bool(missing):
            errors.add("invalid_missing_facts")
    if seen != set(reference):
        errors.add("task_coverage")
    return sorted(errors)


def export_forms(output: Path, raw: bytes) -> None:
    """Create a fresh folder; never overwrite an existing annotator's work."""
    output.mkdir(parents=True, exist_ok=False)
    content = (json.dumps(build_form(raw), ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    for name in ("annotator-a.json", "annotator-b.json"):
        (output / name).write_bytes(content)


def main() -> int:
    """Expose export/check commands with redacted, machine-readable outcomes."""
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("export").add_argument("--output", type=Path, required=True)
    sub.add_parser("check").add_argument("path", type=Path)
    args = parser.parse_args()
    try:
        raw = OUTPUT.read_bytes()
        if args.command == "export":
            export_forms(args.output, raw)
            errors = []
        else:
            errors = validate_form(strict_json(args.path.read_bytes()), raw)
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        errors = ["invalid_input_or_output"]
    print(json.dumps(dict(ok=not errors, issues=errors)))
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
