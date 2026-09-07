# 知衡 RuleShift — 多版本中文规程的条件与例外推理

本项目由衡策 EvoNex 升级，聚焦制造业不合格品处置与批次放行：给定多版本规程、
业务事实和目标时间，判断结论是否被支持、否定或无法确定，并定位条件、例外和原文证据。
研究重点是跨版本“应改变／不应改变”的答案一致性。Nexent 用于后续交互与 MCP 集成。

## 当前进度（2026-09-07）

- W1（9 月 7–13 日）：数据治理、来源登记、准入与公开发布检查已完成技术验收。
- 全量 105 项测试：104 通过、1 因本机缺少符号链接创建权限跳过；Git 链接模式与 Windows junction 测试通过。
- EvoNex 可复用基础：合成数据、资产卡片、SQLite 图谱、规则候选抽取、审核逻辑、
  标准映射差异、证据链渲染、评测函数和回归门。
- 上一轮 69 项单测通过属于工程测试，不代表真实 NLP 实验效果。
- 目前 LLM 候选抽取为空接口，演化指标为演示预设，Agent 文件为蓝图。
- RuleShift 条件例外抽取、版本对齐、NLI、成对监督和历史复核尚待开发。
- Nexent 曾有启动记录；模型配置、知识库上传和 MCP 端到端联调尚未验收。

## 本周任务

| 编号 | 工作 | 状态 | 验收 |
|---|---|---|---|
| GOV-01 | 范围与新 WBS | 已完成 | 历史判断与新版情景评估明确区分 |
| GOV-02 | 数据治理 | 已完成 | 研究、训练、外部模型输入、再分发分别授权 |
| GOV-03 | 来源登记与准入校验 | 已完成 | 默认拒绝不明授权，验证路径、哈希和血缘 |
| GOV-04 | 发布检查与目录隔离 | 已完成 | 公开目录及 Git 索引受限内容检查 |

二级任务完成并验收后，按 AGENTS.md 生成变更总结、提交并推送 GitHub。
按用户约定，本周 GOV-01～04 验收推送后暂停开发，不自动进入 W2；等待用户另行启动。
企业授权、专家标注和真实标准使用许可均需实际证据，不能由技术验收替代。

## 数据原则

官方材料、企业授权材料、许可科研语料和自编合成材料分别登记。
来源权威性、用途权限、内容真实性分别审查；公开可访问、摘要改写或代码 MIT 许可不自动赋予数据使用权。
自然修订、合成挑战、受限企业验证集分别管理和报告。
历史合成的“2026 标准更新”仅供测试，不代表真实国家标准修订。

## 路线图

| 阶段 | 内容 | 状态 |
|---|---|---|
| W1 | 数据治理、来源登记与准入 | 已验收；后续开发暂停 |
| W2–3 | 来源核验、修订样本、标注规范与试标 | 待开发 |
| W4–5 | 条件抽取、版本对齐、时间检索和实验基线 | 待开发 |
| W6–7 | NLI、缺失事实、版本对照和证据验证 | 待开发 |
| W8 | 历史复核、MCP 与 Nexent 联调 | 待开发 |
| W9–10 | 冻结测试、消融、权威数据试点与交付 | 待开发 |

以上为相对排期。授权语料或领域标注资源未落实时，真实试点不得标记完成。

## 现有离线工具

Python 3.12+，核心逻辑使用标准库。在仓库根目录执行：

```powershell
python -B -m unittest discover -s tests -v
python -B tests/run_eval.py
python -B scripts/validate_agent_blueprints.py
python -B scripts/source_registry.py --purpose research
python -B scripts/source_registry.py --purpose redistribution
python -B scripts/check_data_release.py
```

`run_eval.py` 当前命令行仅校验 10 条旧 Golden 样本，不运行真实模型评分。
历史合成数据通过 `python -B scripts/generate_synthetic_data.py` 生成到 `data/generated/`；
图片生成需要可选 matplotlib。运行 MCP 包装前安装 requirements.txt 中相应依赖。

发布检查同时检查工作区和 Git 暂存区；提交前须在 `git add -A` 后重跑。
这是本地检查，不是服务端强制关卡或全仓合规认证。当前公开登记仅含 1 份原创技术样例。

## 文档入口

- [RuleShift 总体计划与 WBS](docs/ruleshift-development-plan.md)
- [数据治理与准入政策](docs/data-governance.md)
- [来源登记接口](docs/source-registry.md)与[W1 原创技术样例数据卡](docs/datasets/w1-fixture.md)
- [发布检查、提交顺序与限制](docs/data-release-check.md)
- [历史 EvoNex 方案](docs/2026-nexent-evolvable-agent-plan.md)
- [开发规范](docs/development-conventions.md)
- [创新流程](docs/innovation-process.md)与[创新台账](docs/innovation-log.md)
- [历史数据规格](docs/data-spec.md)与[知识库准备](docs/knowledge-base-plan.md)
- [Nexent 部署清单](deploy/nexent-deploy-checklist.md)

## 开源与使用范围

代码采用 [MIT](LICENSE)。第三方依赖及数据按各自权利范围使用，详见
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。受限原文、授权合同、密钥和真实企业数据不得提交 Git。
