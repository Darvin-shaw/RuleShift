# scripts/

RuleShift W2：

- `generate_revision_fixture.py --check`：检查三个原创规程族、十二对修订样本可复现。
- `ai_annotate.py --output <文件>`：生成带输入哈希、算法版本和机器理由的 AI-only 标签。
- `ai_annotate.py --check <文件>`：校验标签、证据字段、任务覆盖和机器来源标识。
  完整流程见 [AI-only 标注协议](../docs/ai-annotation-protocol.md)。
- `generate_ai_trial_set.py --check`：检查 W3 的 25 对／50 条合成判断可复现。
- `run_w3_eval.py`：运行冻结基线，见 [W3 评测](../docs/w3-evaluation.md)。
- `run_w4.py`：批量抽取与版本对齐，见 [W4 配置与接口](../docs/w4-development.md)。
- `extract_rules.py <文件>`：抽取单条规程，见 [支持语法](../docs/rule-extraction.md)。

M1 阶段脚本：

- `generate_synthetic_data.py`：T1.2 合成数据生成器。
  - 直接运行：`python scripts/generate_synthetic_data.py`
  - 只读自检：`python scripts/generate_synthetic_data.py --dry-run`
