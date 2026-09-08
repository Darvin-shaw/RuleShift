# DATA-02 原创修订技术样本

日期：2026-09-08。

## 涉及文件

- `scripts/generate_revision_fixture.py`、`data/public/SYN-REV-001.json`：确定性生成器及公开产物。
- `tests/test_revision_fixture.py`：候选标签、版本时间、证据、缺失事实、隔离与复现检查。
- `tests/test_source_registry.py`、`tests/test_data_release.py`：临时清单仅保留实际复制的首个来源。
- `data/sources/manifest.json`、`docs/datasets/revision-fixture.md`：来源登记、字节哈希和数据卡。
- `README.md`、`data/README.md`、`docs/source-registry.md`、`docs/ruleshift-development-plan.md`、
  `docs/innovation-log.md`：同步恢复开发、交付范围与限制。
- 本变更总结。

## 变更要点

按用户继续开发指令启动 W2–3，先交付 DATA-02：三个规程族、六个版本、十二组对照，
覆盖阈值收紧、新增例外、仅措辞变化及未知事实；提供只读 `--check` 复现入口。
沿用 INNO-2026-002，不新增外部依赖。

## 验证与影响

全量 108 项测试：107 通过、1 因符号链接权限跳过。
复现、研究／再分发准入及工作区／暂存区发布检查通过。
已检查 tracked diff 及新增文件暂存差异。
全部标签仅为技术候选；DATA-01 真实来源核验、DATA-03 人工标注冻结和 NLP 实验仍待办。
训练与外部模型输入继续禁止；没有外部调用或真实企业数据。
