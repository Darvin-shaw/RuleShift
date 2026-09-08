# scripts/

RuleShift W2：

- `generate_revision_fixture.py --check`：检查三个原创规程族、十二对修订样本可复现。
- `ai_annotate.py --output <文件>`：生成带输入哈希、算法版本和机器理由的 AI-only 标签。
- `ai_annotate.py --check <文件>`：校验标签、证据字段、任务覆盖和机器来源标识。
  完整流程见 [AI-only 标注协议](../docs/ai-annotation-protocol.md)。

M1 阶段脚本：

- `generate_synthetic_data.py`：T1.2 合成数据生成器。
  - 直接运行：`python scripts/generate_synthetic_data.py`
  - 只读自检：`python scripts/generate_synthetic_data.py --dry-run`
