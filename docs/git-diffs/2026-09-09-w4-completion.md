# W4 抽取与对齐收尾

日期：2026-09-09。

涉及文件：scripts/extract_rules.py、scripts/align_versions.py、scripts/run_w4.py、
scripts/README.md、configs/w4.json、tests/test_align_versions.py、README.md、
docs/rule-extraction.md、docs/w4-development.md、docs/ruleshift-development-plan.md、
docs/innovation-log.md、本总结。

变更要点：完善全文字符跨度、例外结果、兜底引用及递归限制；新增条件树归一、
修改和措辞变化识别、相邻 2–4 条款结构拆合、稳定 ID 对应及文字候选。
候选和歧义不自动判为语义等价。新增注册来源准入的 CLI、配置和可追溯报告。
将原合并 W4–5 计划细分为 W4 抽取与对齐、W5 检索基线，W4 后暂停。

验证：全量 140 项中 139 通过、1 因符号链接权限跳过；抽取／对齐共 18 项测试通过。
默认 5 族、10 版本输出 4 项修改、1 项措辞变化；文档链接、数据复现、研究准入、
再分发准入、Git 空白与双快照发布检查通过。

影响与限制：只完成受控语法及结构对齐工程范围，任意中文语义改写与真实数据泛化未验收。
没有新增依赖或第三方数据，不改 W3 冻结数据、参考标签、模型、本体、MCP 或部署。
参考 Python difflib 官方文档，方法依据及边界记录在 W4 说明中。
