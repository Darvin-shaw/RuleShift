# AI-only 标注协议

日期：2026-09-08；关联 DATA-03、INNO-2026-002。

项目不再设置手工标注、双人复核或专家裁决环节。RuleShift 的技术样本由 Codex 依据版本条款、
业务事实和现有候选结构生成机器参考标签。`ai_annotate.py` 只转存预设候选，校验导出一致性，
不是独立推理或语义裁决。W3 预测使用独立的 `w3_baselines.py`，不读取参考标签。结果必须标记为
`machine_generated`，不能称为人工 Golden、专家裁决或真实领域验收。

## 标签规则

- `支持`：条款及事实足以推出命题，且例外不阻止结论。
- `否定`：条款及事实明确推出命题不成立。
- `无法确定`：缺少决定性事实或适用版本关系无法确定。

只使用任务给出的版本和目标日期；`evidence` 必须是当前条款中的连续原文；
`missing_facts` 只填缺失字段名；缺少事实不能自动当作否定。

## 运行

```powershell
python -B scripts/ai_annotate.py --output data/public/SYN-AI-ANNOTATIONS-001.json
python -B scripts/ai_annotate.py --check data/public/SYN-AI-ANNOTATIONS-001.json
python -B scripts/generate_ai_trial_set.py --check
python -B scripts/ai_annotate.py --source data/public/SYN-W3-AI-TRIAL-001.json --check data/public/SYN-W3-AI-TRIAL-ANNOTATIONS-001.json
```

输出包含输入样本哈希、算法版本、任务 ID、标签、证据、缺失事实和机器理由。
校验失败时返回非零退出码，不回显输入原文。当前 W2 样本为 24 条，W3 合成试验集为 50 条；
扩充样本时必须增加独立规程事实，不能复制任务凑数。该流程不模拟人工身份，不生成授权或专家签名。

## 适用边界

当前产物用于工程回归、规则抽取和流程演示。真实标准、企业数据和第三方语料仍须按来源登记
和许可规则处理；AI 标签不能替代权利人授权、领域专家意见或生产放行决定。
