# Git Diff 总结：创新提案机制与开源合规

- 日期：2026-09-07
- 变更类型：项目治理、开发规范与开源合规文档

## 涉及文件

- `AGENTS.md`
- `README.md`
- `LICENSE`
- `THIRD_PARTY_NOTICES.md`
- `docs/2026-nexent-evolvable-agent-plan.md`
- `docs/development-conventions.md`
- `docs/innovation-process.md`
- `docs/innovation-log.md`
- `docs/git-diffs/2026-09-07-innovation-process-and-compliance.md`

## 变更要点

1. 新增仓库级创新提案与联动更新强制约定，要求新创新先汇报、按影响分级，并在纳入后同步更新所有受影响产物。
2. 新增创新流程文档，明确 L1/L2/L3 分级、提案模板、决策流程、影响矩阵和完成定义。
3. 新增创新提案台账，登记 `INNO-2026-001` 动态创新提案与项目文件联动更新机制。
4. 在开发规范和总体方案中接入创新提案流程，要求创新任务纳入 WBS、评测和验收闭环。
5. README 增加创新流程、台账以及开源合规文档入口。
6. 新增 MIT `LICENSE` 和第三方声明，说明 Nexent、标准摘要、合成数据和 Python 依赖的使用边界。

## 注意事项与影响

- 本次变更只调整项目治理与文档，不改变运行时代码、数据 Schema 或现有接口。
- 标准内容继续使用自编二次改写摘要和概念锚点，不将标准原文作为仓库内容分发。
- 后续创新若影响数据来源、许可、核心架构、模型路线、外部服务或排期，须按新流程完成确认和联动更新。
- 提交前应执行 Markdown 路径检查和 `git diff --cached --check`；代码测试不因本次文档变更新增要求。
