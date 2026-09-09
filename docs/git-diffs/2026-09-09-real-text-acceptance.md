# 真实正文验收与机器来源核验

日期：2026-09-09。

涉及文件：scripts/source_registry.py、scripts/check_real_text.py、scripts/README.md；
tests/test_source_registry.py、tests/test_real_text.py；data/sources/manifest.json；
data/public/REAL-GMP-2010-RELEASE.json、data/public/REAL-GMP-2010-RESULT.json；
README.md、THIRD_PARTY_NOTICES.md；docs/data-governance.md、docs/source-registry.md、
docs/data-release-check.md、docs/data-source-feasibility.md、docs/real-text-acceptance.md、
docs/ruleshift-development-plan.md、docs/w4-development.md、docs/innovation-log.md、本总结。

变更：按用户明确指令取消强制人工审查、签核和专家前置条件，增加 machine 核验身份。
来源、使用依据、逐项权限、路径和哈希验证保留，human 仅作历史记录兼容。
依据官方规章正文的使用范围，准入 GMP 第 228–230 条完整正文及对应验收报告。
新增真实来源覆盖率检查，合成来源不得冒充真实验收；解析成功不直接等同语义正确。

结果：保持 W4 解析器不变，3 条原文全部不支持，覆盖率 0/3，验收未通过。
原文结构、失败原因、输入及代码哈希已保存；未用改写或合成样本替代真实正文。

验证：全量 145 项中 144 通过、1 因符号链接权限跳过；研究准入、再分发检查及双快照发布检查通过。
新增测试确认机器核验仍执行权限和哈希检查、拒绝合成冒充、覆盖率成功不自动判泛化通过。

影响：删除流程中的人工身份门槛不产生第三方授权，也不放开训练或外部模型权限。
本轮仅为单份规章的失败诊断，不代表跨领域统计评估；未改解析器、未进入 W5，提交后暂停。
