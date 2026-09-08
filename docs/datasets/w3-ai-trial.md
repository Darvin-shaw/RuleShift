# W3 AI-only 五十条合成试验集

来源：`SYN-W3-AI-TRIAL-001`；日期：2026-09-08；许可：MIT；类别：S。

该数据由 W2 原创规程族扩展生成，共 50 条独立事实组合，包含阈值、例外和措辞变化。
对应标注产物为 `SYN-W3-AI-TRIAL-ANNOTATIONS-001.json`，状态为 `machine_generated`。

```powershell
python -B scripts/generate_ai_trial_set.py --check
python -B scripts/ai_annotate.py --source data/public/SYN-W3-AI-TRIAL-001.json --check data/public/SYN-W3-AI-TRIAL-ANNOTATIONS-001.json
```

这是原创技术试验集，不是自然修订、专家 Golden 或真实制造业数据；不得据此宣称真实 NLP 效果。
