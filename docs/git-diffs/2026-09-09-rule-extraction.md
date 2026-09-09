# 受控规程条件抽取

日期：2026-09-09。

涉及文件：scripts/extract_rules.py、tests/test_extract_rules.py、docs/rule-extraction.md、
README.md、docs/ruleshift-development-plan.md、docs/innovation-log.md、本总结。

变更：恢复 W4，增加受控中文规程解析 CLI，输出条件树、例外、结果及原文跨度。
支持括号、且／或和前缀否定；未知句式拒绝解析，不猜测业务字段。
采用标准库和直接优先级解析，无新增依赖。同步开发入口、任务状态及创新记录。

验证：全量 127 项，126 通过、1 因符号链接权限跳过；覆盖逻辑优先级、嵌套条件、
原文跨度、例外兜底、数值词中的否定和不支持输入。提交前检查 Git 差异与数据发布。

影响：NLP-01 仅完成受控解析，真实语料和通用抽取待验收；W3 模型与冻结数据未改动。
