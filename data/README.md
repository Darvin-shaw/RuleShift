# data/ 说明

## 目录用途

| 路径 | 内容 |
|---|---|
| `data/generated/` | 历史生成数据，默认忽略；不得直接强制提交或作为新研究语料发布 |
| `data/static/` | 供测试与文档使用的小型静态样例 |
| `data/sources/` | RuleShift 非敏感来源与用途登记 |
| `data/public/` | 经准入检查的公开文本和技术样例 |
| `data/restricted/`、`data/quarantine/`、`data/derived/` | 本地隔离预留路径，禁止入 Git；受限原文优先放工作区外 |

所有企业资料均为虚构合成数据，仅供演示；不应包含任何真实个人信息或企业机密。

新增材料按 [数据治理](../docs/data-governance.md) 分别核验权威性、真实性、用途权限。
目录忽略不是加密或访问控制。历史材料未自动取得 RuleShift 研究准入资格。

来源清单为 `sources/manifest.json`，含 W1 原创文本及
[DATA-02 修订样本](../docs/datasets/revision-fixture.md)；
使用方法见 [登记接口](../docs/source-registry.md)，限制见 [数据卡](../docs/datasets/w1-fixture.md)。
公开提交前运行 [发布检查](../docs/data-release-check.md)，同时验证工作区与暂存快照。

W2 的[来源可行性记录](../docs/data-source-feasibility.md)仅包含候选元数据与许可分析，
未自动导入外部数据库正文。标签由 [AI-only 协议](../docs/ai-annotation-protocol.md)生成，
24 条合成判断标记为 `machine_generated`，不冒充人工或专家结果。
