"""Build 25 distinct version pairs for the frozen synthetic W3 benchmark."""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data/public/SYN-W3-AI-TRIAL-001.json"


def build_trial() -> dict:
    """Each family has five relevant fact combinations and two versions."""
    specs = [
        ("THRESHOLD", "threshold", [
            "批次缺陷数不超过3时允许放行，否则禁止放行。",
            "批次缺陷数不超过1时允许放行，否则禁止放行。"], [
            ({"defects": 0}, "支持", "支持", [], []),
            ({"defects": 1}, "支持", "支持", [], []),
            ({"defects": 2}, "支持", "否定", [], []),
            ({"defects": 4}, "否定", "否定", [], []),
            ({}, "无法确定", "无法确定", ["defects"], ["defects"])]),
        ("EXCEPTION", "exception", [
            "检验合格时允许放行，否则禁止放行。",
            "检验合格时允许放行；但发生污染时禁止放行。检验不合格时禁止放行。"], [
            ({"passed": True, "contaminated": False}, "支持", "支持", [], []),
            ({"passed": True, "contaminated": True}, "支持", "否定", [], []),
            ({"passed": False, "contaminated": False}, "否定", "否定", [], []),
            ({"passed": True}, "支持", "无法确定", [], ["contaminated"]),
            ({"contaminated": False}, "无法确定", "无法确定", ["passed"], ["passed"])]),
        ("SCORE", "wording", [
            "复检评分至少80分时允许放行，否则禁止放行。",
            "复检评分达到80分时允许放行，否则禁止放行。"], [
            ({"score": 79}, "否定", "否定", [], []),
            ({"score": 80}, "支持", "支持", [], []),
            ({"score": 81}, "支持", "支持", [], []),
            ({"score": 0}, "否定", "否定", [], []),
            ({}, "无法确定", "无法确定", ["score"], ["score"])]),
        ("APPROVAL", "condition_added", [
            "复检合格时允许放行，否则禁止放行。",
            "复检合格且审批通过时允许放行，否则禁止放行。"], [
            ({"retested_passed": True, "approved": True}, "支持", "支持", [], []),
            ({"retested_passed": True, "approved": False}, "支持", "否定", [], []),
            ({"retested_passed": False, "approved": True}, "否定", "否定", [], []),
            ({"retested_passed": True}, "支持", "无法确定", [], ["approved"]),
            ({"approved": True}, "无法确定", "无法确定", ["retested_passed"], ["retested_passed"])]),
        ("WAIVER", "alternative_added", [
            "复检合格时允许放行，否则禁止放行。",
            "复检合格或让步获准时允许放行，否则禁止放行。"], [
            ({"retested_passed": True, "waiver": False}, "支持", "支持", [], []),
            ({"retested_passed": False, "waiver": True}, "否定", "支持", [], []),
            ({"retested_passed": False, "waiver": False}, "否定", "否定", [], []),
            ({"retested_passed": False}, "否定", "无法确定", [], ["waiver"]),
            ({"waiver": False}, "无法确定", "无法确定", ["retested_passed"], ["retested_passed"])]),
    ]
    families = []
    for name, kind, texts, cases in specs:
        fid = f"SYN-W3-{name}"
        versions = [dict(version_id=f"{fid}-V{i+1}", text=text,
                         valid_from=f"2025-0{i+1}-01",
                         valid_until="2025-02-01" if i == 0 else None)
                    for i, text in enumerate(texts)]
        pairs = [dict(pair_id=f"{fid}-P{i+1}", facts=facts, claim="该批次允许放行",
                      expected_change=old != new, judgments=[
                          dict(version_id=v["version_id"], target_time=v["valid_from"],
                               candidate_label=label, evidence=v["text"], missing_facts=missing)
                          for v, label, missing in zip(versions, (old, new), (m1, m2))])
                 for i, (facts, old, new, m1, m2) in enumerate(cases)]
        families.append(dict(family_id=fid, revision_type=kind, split="technical_fixture",
                             versions=versions, pairs=pairs))
    return dict(schema_version=1, source_id="SYN-W3-AI-TRIAL-001", families=families)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    content = (json.dumps(build_trial(), ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if args.check:
        ok = OUTPUT.is_file() and OUTPUT.read_bytes() == content
        print("W3: 5 families, 25 pairs, 50 judgments" if ok else "fixture missing or stale")
        return int(not ok)
    OUTPUT.write_bytes(content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
