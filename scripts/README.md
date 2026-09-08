# scripts/

RuleShift W2：

- `generate_revision_fixture.py --check`：检查三个原创规程族、十二对修订样本可复现。
- `annotation_tasks.py export --output <新目录>`：导出两份各 24 条的空白盲标表，拒绝覆盖已有目录。
- `annotation_tasks.py check <标注文件>`：检查任务完整性与填写格式；空表失败，不代表人工或语义验收。
  标注文件保存在仓库外，完整步骤见 [标注规范](../docs/annotation-guide.md)。

M1 阶段脚本：

- `generate_synthetic_data.py`：T1.2 合成数据生成器。
  - 直接运行：`python scripts/generate_synthetic_data.py`
  - 只读自检：`python scripts/generate_synthetic_data.py --dry-run`
