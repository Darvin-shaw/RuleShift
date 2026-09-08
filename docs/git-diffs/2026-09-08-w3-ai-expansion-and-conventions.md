# W3 AI 标注扩展与简洁工程约定

日期：2026-09-08。

## 涉及文件

- `scripts/generate_ai_trial_set.py`：生成 50 条独立合成试验任务。
- `scripts/ai_annotate.py`、`data/public/SYN-W3-AI-TRIAL-ANNOTATIONS-001.json`：生成并校验机器标签。
- `tests/test_ai_annotate.py`：验证 50 条覆盖、来源标识和篡改拒绝。
- `data/sources/manifest.json`、`docs/datasets/w3-ai-trial.md`：登记来源、哈希、血缘和限制。
- `README.md`、WBS、脚本说明、AI-only 协议：同步 W3 状态。
- `AGENTS.md`、`docs/development-conventions.md`：新增简洁代码、克制注释、DOCX 渲染核验约定。

## 变更要点

W3 从 24 条扩展到 50 条独立合成任务，仍由 AI-only 流程处理；不引入人工标注或专家裁决。
DOCX 只在确需办公文档时生成，并要求渲染后逐页检查。

## 验证与影响

50 条试验集可复现，机器标注校验通过；全量测试、研究／再分发准入和发布检查需在提交前重跑。
数据仍是原创技术样本，不代表真实制造业语料、专家 Golden 或自然修订效果。
