<div align="center">

# 知衡 RuleShift

**多版本中文规程的条件、例外与证据推理**

[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB)](#快速开始)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Stars](https://img.shields.io/github/stars/Darvin-shaw/RuleShift)](https://github.com/Darvin-shaw/RuleShift/stargazers)

[面向用户](#面向用户) · [面向开发者](#面向开发者) · [Star 用户](#star-用户)

</div>

RuleShift 围绕制造业不合格品处置与批次放行，对照规程版本、业务事实和目标日期，
判断结论是否成立，并提供条款证据与缺失事实。当前提供基于合成规程的离线规则评测。

## 面向用户

### 项目特点

| 能力 | 说明 |
|---|---|
| 版本对照 | 检查规程修订前后的判断是否应当改变 |
| 三类判断 | 输出支持、否定或无法确定，区分事实不满足与事实缺失 |
| 证据追溯 | 保留条款引用、缺失字段与数据版本记录 |

例如，同一批次有 2 个缺陷：旧版允许“不超过 3 个”，判断为支持；新版改为“不超过 1 个”，
判断为否定。未提供缺陷数时，判断为无法确定。

### 快速开始

准备 Python 3.12+。离线评测使用标准库，无需安装依赖或配置模型服务。

```bash
git clone https://github.com/Darvin-shaw/RuleShift.git
cd RuleShift
python -B scripts/run_w3_eval.py
```

终端显示两种基线的评测指标，完整结果保存在 `data/generated/w3-eval.json`，
包含逐题判断、证据和缺失事实。

当前规则解析覆盖预设合成模板，尚不支持任意规程文本。评测数据与结果见
[评测说明](docs/w3-evaluation.md)。

### 调整配置

默认配置位于 [configs/w3-eval.json](configs/w3-eval.json)。

| 配置项 | 说明 |
|---|---|
| `split` | 评测分区：`train`、`dev` 或 `test` |
| `models` | `majority`（多数类）和 `rule_text`（规则文本），可选一种或两种 |
| `output` | 报告保存位置，须位于 `data/generated/` |

使用其他配置文件：

```bash
python -B scripts/run_w3_eval.py --config configs/w3-eval.json
```

配置内的相对路径以仓库根目录为准。数据来源、冻结文件等完整字段见[配置说明](docs/w3-evaluation.md#运行与配置)。

---

## 面向开发者

### 项目结构

```text
configs/       评测配置
scripts/       数据生成、规则基线与评测入口
tests/         单元测试与回归检查
data/public/   公开样本与冻结分区
data/sources/  来源、许可与文件哈希
docs/          设计、数据和开发文档
```

评测入口为 [run_w3_eval.py](scripts/run_w3_eval.py)，规则解析位于
[w3_baselines.py](scripts/w3_baselines.py)。参考标签与预测输入分开处理，数据按规程族划分。

受控句式的条件与例外抽取见 [规则抽取接口](docs/rule-extraction.md)。
运行 `python -B scripts/run_w4.py` 可生成条件树与版本对应报告，支持条款修改、措辞变化和结构拆合；
配置及匹配边界见 [版本对齐说明](docs/w4-development.md)。
真实规章的初步检查尚未通过，结果与限制见 [真实文本验收](docs/real-text-acceptance.md)。

### 本地检查

在仓库根目录执行：

```bash
python -B -m unittest discover -s tests -v
python -B scripts/generate_ai_trial_set.py --check
python -B scripts/source_registry.py --purpose research
python -B scripts/source_registry.py --purpose redistribution
python -B scripts/check_data_release.py
```

发布检查覆盖工作区和暂存区，提交前暂存文件后需再次运行。

### 开发文档

| 主题 | 入口 |
|---|---|
| 设计与研究 | [总体设计](docs/ruleshift-development-plan.md) · [创新设计](docs/innovation-log.md) |
| 数据与评测 | [试验集](docs/datasets/w3-ai-trial.md) · [评测指标](docs/w3-evaluation.md) · [来源登记](docs/source-registry.md) |
| 开发与贡献 | [开发规范](docs/development-conventions.md) · [发布检查](docs/data-release-check.md) |
| 可选集成 | [Nexent 部署清单](deploy/nexent-deploy-checklist.md) |

问题反馈请附复现命令、配置和错误信息，提交至 [Issues](https://github.com/Darvin-shaw/RuleShift/issues)。

代码采用 [MIT](LICENSE) 许可；数据与依赖的使用范围见[第三方声明](THIRD_PARTY_NOTICES.md)。

---

### Star 用户

<!-- STARGAZERS:START -->

感谢 52 位 Star 用户！

[@3aseer](https://github.com/3aseer) · [@asHOH](https://github.com/asHOH) · [@bort2an](https://github.com/bort2an) · [@bt9527q](https://github.com/bt9527q) · [@btngana](https://github.com/btngana) · [@build23w](https://github.com/build23w) · [@chaowenguo](https://github.com/chaowenguo) · [@Chengchcc](https://github.com/Chengchcc) · [@chernistry](https://github.com/chernistry) · [@chrisholloway5](https://github.com/chrisholloway5) · [@Clashforwinodws](https://github.com/Clashforwinodws) · [@cto2006](https://github.com/cto2006) · [@Darvin-shaw](https://github.com/Darvin-shaw) · [@DeepOceanFBM](https://github.com/DeepOceanFBM) · [@Euler1024](https://github.com/Euler1024) · [@ExpiredMinotaur](https://github.com/ExpiredMinotaur) · [@frekyynckyy-art](https://github.com/frekyynckyy-art) · [@GongChang2020](https://github.com/GongChang2020) · [@guapimm](https://github.com/guapimm) · [@H47R15](https://github.com/H47R15) · [@Ho-Tung](https://github.com/Ho-Tung) · [@Illusionna](https://github.com/Illusionna) · [@jagmarques](https://github.com/jagmarques) · [@joeljollyhere](https://github.com/joeljollyhere) · [@kerokero2333](https://github.com/kerokero2333) · [@kgnio](https://github.com/kgnio) · [@knisar1](https://github.com/knisar1) · [@lenacarter7](https://github.com/lenacarter7) · [@LovelyMuu](https://github.com/LovelyMuu) · [@MakeItorTakeIt](https://github.com/MakeItorTakeIt) · [@mdomartouhid1-design](https://github.com/mdomartouhid1-design) · [@moy852591265](https://github.com/moy852591265) · [@ncardian](https://github.com/ncardian) · [@otonielpv12](https://github.com/otonielpv12) · [@pardnchiu](https://github.com/pardnchiu) · [@PraveenMyakala](https://github.com/PraveenMyakala) · [@RaptorVampire](https://github.com/RaptorVampire) · [@scholar-by](https://github.com/scholar-by) · [@Scottcjn](https://github.com/Scottcjn) · [@Slayok](https://github.com/Slayok) · [@sleep3r](https://github.com/sleep3r) · [@sophiaeagent-beep](https://github.com/sophiaeagent-beep) · [@strelov1](https://github.com/strelov1) · [@thehackmanyt-beep](https://github.com/thehackmanyt-beep) · [@Turing-Neo](https://github.com/Turing-Neo) · [@victrhugo](https://github.com/victrhugo) · [@wh1024k](https://github.com/wh1024k) · [@xerox7x](https://github.com/xerox7x) · [@xunlulearn](https://github.com/xunlulearn) · [@zatooona](https://github.com/zatooona) · [@zicowarn](https://github.com/zicowarn) · [@Zirakin](https://github.com/Zirakin)

<!-- STARGAZERS:END -->
