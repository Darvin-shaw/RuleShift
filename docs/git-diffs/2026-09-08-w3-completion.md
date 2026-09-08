# W3 完成与用户文档

日期：2026-09-08。

涉及文件：README.md；configs/w3-eval.json；.github/workflows/update-stargazers.yml；
scripts/{generate_ai_trial_set,ai_annotate,w3_baselines,run_w3_eval,update_stargazers}.py；
tests/test_w3_eval.py；data/public/SYN-W3-*.json；data/sources/manifest.json；
docs/{w3-evaluation,ai-annotation-protocol,data-governance,innovation-log,ruleshift-development-plan}.md；
docs/datasets/w3-ai-trial.md；本总结。

变更要点：修正重复样本，生成 5 族、25 对／50 条机器参考判断，按族冻结为 20/10/20；
新增不读取参考答案的规则文本模型及训练分区多数类模型、配置入口和逐题评测报告。
导出标签校验增加任务一致性核验。README 面向使用者重写，加入配置、特色、限制和 Star 名单。
Star 工作流响应新增事件、每小时同步并支持手动运行；只有名单变化才提交，自动附带变更总结。

验证：全量 122 项，121 通过、1 因符号链接权限跳过；生成器复现、两份机器标签校验、
研究／再分发准入、Agent 蓝图、旧 Golden 格式及暂存区发布检查通过。
冻结测试 20 条：多数类准确率 35%，规则文本 100%；仅是已知合成模板一致性。

影响与限制：无新增 Python 依赖或第三方语料；真实 NLP 和领域验收未完成。
Actions 需仓库允许内置令牌写入；平台调度可能延迟或因长期不活跃暂停。
W3 收尾后暂停开发，不进入 W4。
