"""Build a deterministic 50-task AI-only synthetic trial set."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

if __package__:
    from .generate_revision_fixture import OUTPUT as BASE
else:
    from generate_revision_fixture import OUTPUT as BASE


ROOT = BASE.parents[2]
OUTPUT = ROOT / "data/public/SYN-W3-AI-TRIAL-001.json"


def build_trial() -> dict:
    """Keep the 24 W2 tasks and add 26 independent synthetic fact combinations."""
    source = json.loads(BASE.read_bytes())
    families = copy.deepcopy(source["families"])
    extra = {
        "SYN-REV-THRESHOLD": [
            ({"defects": value}, "支持" if value <= 3 else "否定", "支持" if value <= 1 else "否定", [])
            for value in range(5)
        ],
        "SYN-REV-EXCEPTION": [
            ({"passed": passed, "contaminated": contaminated},
             "支持" if passed else "否定",
             "支持" if passed and not contaminated else "否定",
             [])
            for passed, contaminated in ((True, True), (False, True), (True, False), (False, False))
        ],
        "SYN-REV-WORDING": [
            ({"retested_passed": value, "line": f"L{i}"},
             "支持" if value else "否定", "支持" if value else "否定", [])
            for i, value in enumerate((True, False, True, False))
        ],
    }
    for family in families:
        cases = extra[family["family_id"]]
        for offset, (facts, old, new, missing) in enumerate(cases, len(family["pairs"]) + 1):
            versions = family["versions"]
            family["pairs"].append({
                "pair_id": f"{family['family_id']}-W3P{offset}",
                "facts": facts,
                "claim": "该批次允许放行",
                "expected_change": old != new,
                "judgments": [
                    {"version_id": version["version_id"], "target_time": version["valid_from"],
                     "candidate_label": label, "evidence": version["text"],
                     "missing_facts": missing if label == "无法确定" else []}
                    for version, label in zip(versions, (old, new))
                ],
            })
    return {"schema_version": 1, "source_id": "SYN-W3-AI-TRIAL-001", "families": families}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    content = (json.dumps(build_trial(), ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if args.check:
        ok = OUTPUT.is_file() and OUTPUT.read_bytes() == content
        print("AI trial fixture: 50 tasks" if ok else "AI trial fixture missing or stale")
        return 0 if ok else 1
    OUTPUT.write_bytes(content)
    print("generated data/public/SYN-W3-AI-TRIAL-001.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
