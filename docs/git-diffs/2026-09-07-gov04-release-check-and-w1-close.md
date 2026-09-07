# GOV-04：发布检查与 W1 收尾

日期：2026-09-07。

## 涉及文件

- README.md、data/README.md
- docs/data-governance.md、docs/data-release-check.md
- docs/ruleshift-development-plan.md、docs/innovation-log.md
- scripts/check_data_release.py、scripts/source_registry.py
- tests/test_data_release.py、tests/test_source_registry.py
- docs/git-diffs/2026-09-07-gov04-release-check-and-w1-close.md（本总结）

## 变更要点

- 新增工作区与实际 Git 索引双检查，按捕获的 blob ID 校验清单、权限、血缘及哈希。
- 拒绝隔离目录强制暂存、未登记文件、链接、二进制及不支持类型；扫描部分敏感模式，错误不回显原文。
- 新增 17 项临时 Git 仓库对抗测试；补充深层 JSON 拒绝／错误脱敏及跨平台跳过信息。
- 修复 Windows junction 测试夹具的 PowerShell 参数传递；用环境变量传递路径，不拼接脚本。
- README、数据治理、WBS、创新台账和发布操作说明同步到本周技术验收完成状态。

## 验证

- 定向 GOV-04：17 项通过；全量 105 项：104 通过、1 跳过。
- 跳过原因：GOV-03 真实 symlink 创建缺少 Windows 权限（1314）；
  真实 Windows junction 和 Git 索引 symlink 模式拒绝测试均通过。
- 深层 JSON 在本机可解析成数组，按清单 Schema 拒绝；测试兼容解析深度超限时的拒绝，均要求非零退出且无原文或堆栈泄露。
- research／redistribution 准入、工作区＋索引发布检查、旧 10 条 Golden 格式及 Agent 蓝图校验通过。
- 已审阅已跟踪差异与新增文件暂存差异；相对链接、git diff --cached --check 通过。

## 影响、限制与停止点

- 无新外部依赖、真实语料采集、模型调用、服务端保护规则或常驻任务。
- 内容检查仅覆盖新公开目录和登记清单；不覆盖全仓历史，不构成合规认证或全面防泄漏保障。
- GOV-01～04 本周技术任务已验收。本批提交推送后暂停开发，不自动进入 W2。
- 真实授权、领域双人标注、版本对齐与 NLP 实验仍待开展；INNO-2026-002 整体科研创新尚未完成。
- GitHub 已提示仓库迁移至 Darvin-shaw/RuleShift，保持用户配置的 origin，通过其重定向推送；未擅自修改远端配置。
