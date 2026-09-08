<div align="center">

# 知衡 RuleShift

**规程变了，判断该不该变？**

多版本中文规程的条件、例外与证据推理实验项目

[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB)](#快速开始)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Stars](https://img.shields.io/github/stars/Darvin-shaw/RuleShift)](https://github.com/Darvin-shaw/RuleShift/stargazers)

[快速开始](#快速开始) · [配置](#配置) · [特色与研究方向](#特色与研究方向) · [文档](#文档) · [Star 用户](#感谢-star-用户)

</div>

RuleShift 面向制造业不合格品处置与批次放行，研究如何结合规程版本、业务事实和目标日期，
输出 **支持／否定／无法确定**，并给出条款证据和缺失事实。

目前可直接运行 W3 离线合成评测：无需 API Key、数据库或模型下载，核心使用 Python 标准库。
项目尚处研究开发阶段，真实规程 NLP、生产应用和 Nexent 端到端集成尚未验收。

## 一个例子

同一批次有 2 个缺陷，命题为“该批次允许放行”：

| 适用版本 | 条款 | 判断 |
|---|---|---|
| 旧版 | 缺陷数不超过 3 时允许放行 | 支持 |
| 新版 | 缺陷数不超过 1 时允许放行 | 否定 |
| 任一版 | 未提供缺陷数 | 无法确定，并指出缺失字段 |

## 快速开始

安装 Python 3.12+，在终端执行：

```bash
git clone https://github.com/Darvin-shaw/RuleShift.git
cd RuleShift
python -B scripts/run_w3_eval.py
```

终端显示两种基线的指标；逐题预测、证据、缺失事实及哈希写入 `data/generated/w3-eval.json`。
默认测试集含 20 条判断（10 对），预期结果：

| 基线 | 准确率 | Macro-F1 | 双版本均正确率 |
|---|---:|---:|---:|
| 训练分区多数类 | 35% | 0.1728 | 20% |
| 规则文本解析 | 100% | 1.0000 | 100% |

规则模型针对已知合成模板编写；参考标签由机器预设。这些分数只验证工程一致性，不能推断真实文本泛化能力。

## 配置

编辑 [configs/w3-eval.json](configs/w3-eval.json)，或指定配置：

```bash
python -B scripts/run_w3_eval.py --config configs/w3-eval.json
```

| 字段 | 用途与可选值 |
|---|---|
| `schema_version` | 固定为 `1` |
| `source` | 合成数据 JSON 路径 |
| `freeze` | 数据哈希与分区冻结文件 |
| `split` | `train`、`dev`、`test`，默认 `test` |
| `models` | `majority`、`rule_text`，可选择一种或两种 |
| `output` | 报告路径，必须位于 `data/generated/` |

配置内相对路径以仓库根目录为准。修改冻结数据会导致评测拒绝运行；新增数据须另建版本并完成来源登记。
可选 Nexent 部署参见[部署清单](deploy/nexent-deploy-checklist.md)，需另行配置模型服务。

## 特色与研究方向

- **版本成对评测**：同时检查答案应该改变和应该保持的场景，已实现按规程族隔离的冻结评测。
- **缺失事实显式输出**：规则基线保留“无法确定”，不会把未知事实直接当作否定。
- **证据与来源可追溯**：报告记录条款证据及数据、冻结文件、模型代码哈希；公开数据有许可和血缘登记。
- **后续研究**：条件例外抽取、版本对齐、NLI 和成对监督尚待开发；创新设计见[创新台账](docs/innovation-log.md)。

## 进度

| 阶段 | 交付 | 状态 |
|---|---|---|
| W1 | 数据治理、来源准入与发布检查 | 技术验收完成 |
| W2 | 来源可行性、原创修订样本、机器标签 | 完成 |
| W3 | 5 族、25 对／50 条判断，双基线与冻结评测 | 完成 |
| W4–10 | NLP、真实数据实验、集成与交付 | 尚未开发 |

按当前约定，W3 完成后暂停开发。项目无手工标注环节；机器标签不替代第三方数据授权。

## 文档

- [W3 评测与指标](docs/w3-evaluation.md) · [试验集数据卡](docs/datasets/w3-ai-trial.md)
- [总体计划与 WBS](docs/ruleshift-development-plan.md) · [开发规范](docs/development-conventions.md)
- [AI-only 标注协议](docs/ai-annotation-protocol.md) · [数据库可行性](docs/data-source-feasibility.md)
- [数据治理](docs/data-governance.md) · [来源登记](docs/source-registry.md) · [发布检查](docs/data-release-check.md)

<details>
<summary>开发者检查</summary>

```bash
python -B -m unittest discover -s tests -v
python -B scripts/generate_ai_trial_set.py --check
python -B scripts/source_registry.py --purpose research
python -B scripts/source_registry.py --purpose redistribution
python -B scripts/check_data_release.py
```

提交前暂存所有文件后重跑发布检查，并依照 [AGENTS.md](AGENTS.md) 保存变更总结。
历史 `tests/run_eval.py` 仅校验旧 Golden 格式，不是 W3 模型评测入口。

</details>

欢迎通过 [Issues](https://github.com/Darvin-shaw/RuleShift/issues) 提交使用反馈或可复现问题。
代码采用 [MIT](LICENSE)，第三方数据按各自许可使用，见 [第三方声明](THIRD_PARTY_NOTICES.md)。

## 感谢 Star 用户

点击 Star 后，GitHub Actions 会触发名单同步，并每小时补充同步；取消 Star 也会移除。
支持在 Actions → Update stargazers 手动运行。工作流使用内置令牌，无需配置个人密钥。
GitHub 调度可能延迟，长期无活动时定时任务可能被平台暂停；同步失败会保留原名单。
实现见[工作流](.github/workflows/update-stargazers.yml)与[同步脚本](scripts/update_stargazers.py)。

<!-- STARGAZERS:START -->

感谢 28 位 Star 用户！

[@3aseer](https://github.com/3aseer) · [@bort2an](https://github.com/bort2an) · [@bt9527q](https://github.com/bt9527q) · [@btngana](https://github.com/btngana) · [@build23w](https://github.com/build23w) · [@chaowenguo](https://github.com/chaowenguo) · [@cto2006](https://github.com/cto2006) · [@Darvin-shaw](https://github.com/Darvin-shaw) · [@ExpiredMinotaur](https://github.com/ExpiredMinotaur) · [@frekyynckyy-art](https://github.com/frekyynckyy-art) · [@Ho-Tung](https://github.com/Ho-Tung) · [@Illusionna](https://github.com/Illusionna) · [@joeljollyhere](https://github.com/joeljollyhere) · [@kerokero2333](https://github.com/kerokero2333) · [@mohammadrezwankhan](https://github.com/mohammadrezwankhan) · [@moy852591265](https://github.com/moy852591265) · [@otonielpv12](https://github.com/otonielpv12) · [@pardnchiu](https://github.com/pardnchiu) · [@PraveenMyakala](https://github.com/PraveenMyakala) · [@sleep3r](https://github.com/sleep3r) · [@surelle-ha](https://github.com/surelle-ha) · [@thehackmanyt-beep](https://github.com/thehackmanyt-beep) · [@Turing-Neo](https://github.com/Turing-Neo) · [@wh1024k](https://github.com/wh1024k) · [@xerox7x](https://github.com/xerox7x) · [@xunlulearn](https://github.com/xunlulearn) · [@zatooona](https://github.com/zatooona) · [@Zirakin](https://github.com/Zirakin)

<!-- STARGAZERS:END -->
