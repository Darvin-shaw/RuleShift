# AI-only 标注流程切换

日期：2026-09-08。

## 涉及文件

- 删除 `docs/annotation-guide.md`、`scripts/annotation_tasks.py`、`tests/test_annotation_tasks.py`。
- 新增 `docs/ai-annotation-protocol.md`、`scripts/ai_annotate.py`、`tests/test_ai_annotate.py`。
- 新增 `data/public/SYN-AI-ANNOTATIONS-001.json`，并在 `data/sources/manifest.json` 登记输入哈希、血缘和用途。
- 同步 `README.md`、`data/README.md`、`scripts/README.md`、WBS、创新台账和修订样本数据卡。

## 变更要点

按用户要求移除手工标注、双人复核和专家裁决环节，统一由 Codex 生成机器标签和理由。
产物固定记录 `machine_generated`、算法版本、输入 SHA-256、任务 ID、证据片段和缺失事实；
结构校验不宣称领域专业性或人工验收。

## 验证与影响

AI 标注定向测试 3 项通过；全量 111 项中 110 通过、1 项因符号链接权限跳过。
研究／再分发来源准入和工作区／暂存区发布检查通过。当前处理范围为 24 条原创技术样本，
不复制凑数、不生成专家签名、不改变外部数据许可边界。
