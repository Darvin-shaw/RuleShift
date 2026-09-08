# W3 AI-only 五十条合成试验集

来源：`SYN-W3-AI-TRIAL-001`；日期：2026-09-08；许可：MIT；类别：S。

v2 数据由 W2 原创规程族扩展生成，共 5 族、10 个版本、25 对／50 条判断，包含阈值、例外、措辞、且／或条件。
每族包含 5 个相关事实组合；成对判断并非统计独立样本。v1 重复组合已在 v2 替换。
按族冻结 train/dev/test 为 20/10/20 条，规则模板为已知设计；详见 [W3 评测](../w3-evaluation.md)。
对应标注产物为 `SYN-W3-AI-TRIAL-ANNOTATIONS-001.json`，状态为 `machine_generated`。

```powershell
python -B scripts/generate_ai_trial_set.py --check
python -B scripts/ai_annotate.py --source data/public/SYN-W3-AI-TRIAL-001.json --check data/public/SYN-W3-AI-TRIAL-ANNOTATIONS-001.json
```

这是原创技术试验集，不是自然修订、专家 Golden 或真实制造业数据；不得据此宣称真实 NLP 效果。
