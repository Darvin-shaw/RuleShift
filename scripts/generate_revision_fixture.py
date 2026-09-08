"""Build original revision fixtures for the AI-only annotation pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data/public/SYN-REV-001.json"


def build_fixture() -> dict:
    """Return deterministic, isolated families with explicit candidate labels."""
    specs = [
        ("threshold", [
            "批次缺陷数不超过3时允许放行，否则禁止放行。",
            "批次缺陷数不超过1时允许放行，否则禁止放行。",
        ], [({"defects": 0}, "支持", "支持", []),
            ({"defects": 2}, "支持", "否定", []),
            ({"defects": 4}, "否定", "否定", []),
            ({}, "无法确定", "无法确定", ["defects"])]),
        ("exception", [
            "检验合格时允许放行，否则禁止放行。",
            "检验合格时允许放行；但发生污染时禁止放行。检验不合格时禁止放行。",
        ], [({"passed": True, "contaminated": False}, "支持", "支持", []),
            ({"passed": True, "contaminated": True}, "支持", "否定", []),
            ({"passed": False, "contaminated": False}, "否定", "否定", []),
            ({"passed": True}, "支持", "无法确定", ["contaminated"])]),
        ("wording", [
            "复检合格时允许放行，否则禁止放行。",
            "若复检结果为合格，则允许放行；若为不合格，则禁止放行。",
        ], [({"retested_passed": True}, "支持", "支持", []),
            ({"retested_passed": False}, "否定", "否定", []),
            ({}, "无法确定", "无法确定", ["retested_passed"]),
            ({"retested_passed": True, "batch_color": "blue"}, "支持", "支持", [])]),
    ]
    families = []
    for kind, texts, cases in specs:
        family_id = f"SYN-REV-{kind.upper()}"
        versions = [dict(
            version_id=f"{family_id}-V{i + 1}",
            valid_from=f"2025-0{i + 1}-01",
            valid_until="2025-02-01" if i == 0 else None,
            text=content,
        ) for i, content in enumerate(texts)]
        pairs = []
        for index, (facts, old, new, missing) in enumerate(cases, 1):
            judgments = [dict(
                version_id=version["version_id"], target_time=version["valid_from"],
                candidate_label=label, evidence=version["text"],
                missing_facts=missing if label == "无法确定" else [],
            ) for version, label in zip(versions, (old, new))]
            pairs.append(dict(pair_id=f"{family_id}-P{index}", facts=facts,
                              claim="该批次允许放行", expected_change=old != new,
                              judgments=judgments))
        families.append(dict(family_id=family_id, revision_type=kind,
                             split="technical_fixture", versions=versions, pairs=pairs))
    return dict(schema_version=1, source_id="SYN-REV-001", families=families)


def fixture_bytes() -> bytes:
    """Serialize exact UTF-8/LF bytes for source registry hashing."""
    return (json.dumps(build_fixture(), ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def main() -> int:
    """Generate the fixture or check it without modifying any files."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    content = fixture_bytes()
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_bytes() != content:
            print("revision fixture missing or stale")
            return 1
        print("revision fixture reproducible: 3 families, 12 pairs")
    else:
        OUTPUT.write_bytes(content)
        print("generated data/public/SYN-REV-001.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
