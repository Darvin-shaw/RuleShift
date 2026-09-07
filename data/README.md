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
