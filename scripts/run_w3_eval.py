"""Run the frozen W3 synthetic benchmark without external services."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

if __package__:
    from .source_registry import strict_json
    from .w3_baselines import LABELS, predict
else:
    from source_registry import strict_json
    from w3_baselines import LABELS, predict

ROOT = Path(__file__).resolve().parents[1]


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def prepare(raw: bytes, freeze: dict) -> list[dict]:
    """Verify frozen content and family isolation, then separate prompts from gold."""
    if freeze.get("schema_version") != 1 or freeze.get("source_sha256") != digest(raw):
        raise ValueError("freeze_mismatch")
    fixture = strict_json(raw)
    splits = freeze["splits"]
    if set(splits) != {"train", "dev", "test"} or not all(splits.values()):
        raise ValueError("invalid_splits")
    owners = {}
    for split, families in splits.items():
        for fid in families:
            if fid in owners:
                raise ValueError("family_leakage")
            owners[fid] = split
    family_ids = [f["family_id"] for f in fixture["families"]]
    if len(set(family_ids)) != len(family_ids) or set(family_ids) != set(owners):
        raise ValueError("family_coverage")
    records, ids, pairs, text_owners = [], set(), set(), {}
    for family in fixture["families"]:
        split = owners[family["family_id"]]
        versions = {v["version_id"]: v for v in family["versions"]}
        for version in versions.values():
            text = "".join(version["text"].split())
            if text in text_owners and text_owners[text] != split:
                raise ValueError("text_leakage")
            text_owners[text] = split
        for pair in family["pairs"]:
            key = json.dumps([family["family_id"], pair["facts"], pair["claim"]], sort_keys=True)
            if key in pairs:
                raise ValueError("duplicate_pair")
            pairs.add(key)
            if len(pair["judgments"]) != 2 or {j["version_id"] for j in pair["judgments"]} != set(versions):
                raise ValueError("version_coverage")
            for judgment in pair["judgments"]:
                tid = f"{pair['pair_id']}:{judgment['version_id']}"
                if tid in ids or judgment["candidate_label"] not in LABELS:
                    raise ValueError("invalid_task")
                ids.add(tid)
                records.append(dict(task_id=tid, pair_id=pair["pair_id"], split=split,
                                    prompt=dict(version=versions[judgment["version_id"]],
                                                facts=pair["facts"], claim=pair["claim"],
                                                target_time=judgment["target_time"]),
                                    reference=judgment["candidate_label"], evidence=judgment["evidence"]))
    if len(records) != freeze["task_count"]:
        raise ValueError("task_count")
    return records


def metrics(rows: list[dict]) -> dict:
    """Compute three-class and paired metrics from saved predictions."""
    matrix = {truth: {pred: 0 for pred in LABELS} for truth in LABELS}
    groups = {}
    for row in rows:
        matrix[row["reference"]][row["label"]] += 1
        groups.setdefault(row["pair_id"], []).append(row)
    count = len(rows)
    ratio = lambda n, d: n / d if d else None
    f1 = []
    for label in LABELS:
        tp = matrix[label][label]
        total = sum(matrix[label].values()) + sum(matrix[t][label] for t in LABELS)
        f1.append(2 * tp / total if total else 0)
    answered = [r for r in rows if r["label"] != "无法确定"]
    pairs = [g for g in groups.values() if len(g) == 2]
    return dict(count=count, accuracy=ratio(sum(r["label"] == r["reference"] for r in rows), count),
                macro_f1=sum(f1) / 3 if count else None, confusion_matrix=matrix,
                pair_accuracy=ratio(sum(all(r["label"] == r["reference"] for r in g) for g in pairs), len(pairs)),
                change_accuracy=ratio(sum((g[0]["label"] != g[1]["label"]) ==
                                         (g[0]["reference"] != g[1]["reference"]) for g in pairs), len(pairs)),
                answer_coverage=ratio(len(answered), count),
                answered_error_rate=ratio(sum(r["label"] != r["reference"] for r in answered), len(answered)),
                evidence_match=ratio(sum(bool(r["evidence"]) and r["reference_evidence"] in r["evidence"] for r in rows), count))


def run(config: dict) -> dict:
    """Evaluate selected models; train labels are used only by the majority model."""
    if set(config) != {"schema_version", "source", "freeze", "split", "models", "output"}:
        raise ValueError("config_fields")
    if type(config["schema_version"]) is not int or config["schema_version"] != 1:
        raise ValueError("config_schema")
    if config["split"] not in ("train", "dev", "test"):
        raise ValueError("invalid_split")
    models = config["models"]
    if not isinstance(models, list) or not models or any(m not in ("majority", "rule_text") for m in models):
        raise ValueError("invalid_models")
    if len(set(models)) != len(models):
        raise ValueError("duplicate_model")
    raw = (ROOT / config["source"]).read_bytes()
    frozen_raw = (ROOT / config["freeze"]).read_bytes()
    records = prepare(raw, strict_json(frozen_raw))
    counts = Counter(r["reference"] for r in records if r["split"] == "train")
    majority = max(LABELS, key=lambda label: counts[label])
    report = dict(dataset_sha256=digest(raw), freeze_sha256=digest(frozen_raw),
                  code_sha256={name: digest((ROOT / "scripts" / name).read_bytes())
                               for name in ("run_w3_eval.py", "w3_baselines.py")},
                  scope="synthetic_machine_reference", split=config["split"],
                  split_counts=dict(Counter(r["split"] for r in records)), models={})
    for model in models:
        rows = []
        for record in records:
            if record["split"] != config["split"]:
                continue
            prediction = predict(record["prompt"]) if model == "rule_text" else dict(
                label=majority, evidence="", missing_facts=[], reason="训练分区多数类")
            rows.append(dict(task_id=record["task_id"], pair_id=record["pair_id"],
                             reference=record["reference"], reference_evidence=record["evidence"], **prediction))
        report["models"][model] = dict(metrics=metrics(rows), predictions=rows)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/w3-eval.json")
    args = parser.parse_args()
    try:
        config = strict_json(args.config.read_bytes())
        report = run(config)
        output = (ROOT / config["output"]).resolve()
        if not output.is_relative_to(ROOT / "data/generated"):
            raise ValueError("output_must_be_generated")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps({m: r["metrics"] for m, r in report["models"].items()}, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError):
        print("W3 evaluation rejected: check configuration, input and frozen hashes")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
