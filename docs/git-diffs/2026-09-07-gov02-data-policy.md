# GOV-02：数据治理政策

日期：2026-09-07。

## 涉及文件

`.gitignore`、`README.md`、`THIRD_PARTY_NOTICES.md`、`data/README.md`、
`docs/data-governance.md`、`docs/data-spec.md`、`docs/development-conventions.md`、
`docs/innovation-log.md`、`docs/ruleshift-development-plan.md`、本总结。

## 要点

- 明确四类来源、五项用途、核验职责、撤回与派生血缘、合成数据科学性边界。
- 预留隔离目录并禁止提交，修正摘要改写和强制添加历史数据的表述。
- 核验官方标准平台的访问层级，不把公开访问视为使用许可。

## 验证与影响

- 已审阅 git diff、新文件暂存差异；相对链接、差异格式与四类目录忽略规则检查通过。
- 仅政策与配置；GOV-03/04 技术实现另行验收。
- 无真实数据采集或授权审批；忽略规则不能代替安全存储及 Git 索引检查。
