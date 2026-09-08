"""Small offline models; prediction inputs contain no reference labels."""

from datetime import date
import re

LABELS = ("支持", "否定", "无法确定")


def predict(task: dict) -> dict:
    """Interpret the documented W3 templates with three-valued logic."""
    version, facts = task["version"], task["facts"]
    text = version["text"]
    target = date.fromisoformat(task["target_time"])
    if (task["claim"] != "该批次允许放行"
            or target < date.fromisoformat(version["valid_from"])
            or (version["valid_until"] and target >= date.fromisoformat(version["valid_until"]))):
        return dict(label="无法确定", evidence="", missing_facts=[], reason="命题或日期不适用")

    def flag(key):
        value = facts.get(key)
        return value if type(value) is bool else None

    missing = []
    threshold = re.fullmatch(r"批次缺陷数不超过(\d+)时允许放行，否则禁止放行。", text)
    score = re.fullmatch(r"复检评分(?:至少|达到)(\d+)分时允许放行，否则禁止放行。", text)
    if threshold or score:
        key = "defects" if threshold else "score"
        value = facts.get(key)
        bound = int((threshold or score).group(1))
        valid = type(value) is int and value >= 0 and (key != "score" or value <= 100)
        decision = (value <= bound if threshold else value >= bound) if valid else None
        missing = [] if valid else [key]
    elif text == "检验合格时允许放行；但发生污染时禁止放行。检验不合格时禁止放行。":
        passed, dirty = flag("passed"), flag("contaminated")
        decision = False if passed is False or dirty is True else True if passed is True and dirty is False else None
        missing = [k for k in ("passed", "contaminated") if flag(k) is None]
    elif text in ("复检合格且审批通过时允许放行，否则禁止放行。",
                  "复检合格或让步获准时允许放行，否则禁止放行。"):
        conjunction = "且" in text
        keys = ("retested_passed", "approved" if conjunction else "waiver")
        values = [flag(k) for k in keys]
        decisive = False if conjunction else True
        decision = decisive if decisive in values else None if None in values else not decisive
        missing = [k for k in keys if flag(k) is None]
    elif text in ("检验合格时允许放行，否则禁止放行。", "复检合格时允许放行，否则禁止放行。"):
        key = "retested_passed" if text.startswith("复检") else "passed"
        decision = flag(key)
        missing = [key] if decision is None else []
    else:
        return dict(label="无法确定", evidence="", missing_facts=[], reason="未支持的条款模板")
    label = "无法确定" if decision is None else "支持" if decision else "否定"
    return dict(label=label, evidence=text, missing_facts=missing if decision is None else [],
                reason="规则文本基线：" + label)
