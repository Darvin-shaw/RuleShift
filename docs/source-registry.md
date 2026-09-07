# 来源登记接口 v1（GOV-03）

入口：`python -B scripts/source_registry.py --purpose research`。
`--root` 指定数据所在根目录；默认使用仓库根。仅只读，不下载、不审批、不训练。
退出码 0 表示登记技术检查通过；1 表示拒绝；参数错误为 2。

清单位于 `data/sources/manifest.json`，顶层仅 `schema_version: 1` 与非空 `sources` 数组。
空清单不能作为完成数据准入的证据。JSON 重复键、缺少字段和多余字段均拒绝。
暂未具备授权的来源不要放入可用清单；候选元数据单独登记、审批后再导入。

## 每项来源字段（完整键集）

| 字段 | 约束 |
|---|---|
| id | 唯一大写标识；原创技术样例以 SYN- 开头 |
| class | A/B/C/S，对应数据治理四类来源 |
| title / origin / license | 非空，不能填 unknown/pending/unverified/n/a；许可证据另行人工核验 |
| status | 只有 approved 可准入；candidate/revoked 等一律拒绝 |
| review | kind、reviewer、reviewed_on、evidence_ref；不得上传敏感合同或人员详情 |
| permissions | research/model_input/training/external_model/redistribution 五项严格布尔值 |
| valid_from / valid_until | 使用权限起始日期／截止日期，YYYY-MM-DD；无截止填 null，非规程生效时间 |
| parents | 父来源 ID 列表，禁止缺失父项、重复父项、环和用途权限升级 |
| artifacts | 非空数组，每项仅 path 与 sha256（精确字节，64 位小写十六进制） |

review.kind 为 human 或 technical_fixture；后者仅限原创 S 类、SYN- 编号、
`project:original/` 来源及 `codex:technical-fixture` 自检身份。
reviewed_on 不得晚于今天；CLI 不确认 reviewer 真实身份或 evidence_ref 有效性。
来源权威性、事实真实性、授权书有效性仍须 DATA-01 人工复核。

路径为根目录下 `data/public|restricted|quarantine|derived/`，保守使用 ASCII 字母、
数字、连字符、下划线、点和斜杠；禁止绝对路径、空段、点段、反斜杠、ADS、保留设备名、符号链接与 junction。
quarantine 不准入；再分发还要求 public 路径。文件路径跨大小写也不允许重复。
检查全清单及每个父项，派生数据不能通过换 ID 获得上游未允许的用途。
授权有效期按本机日期检查（含截止日）；自动化环境应固定正确时区。
错误仅包含代码及来源行索引（从 0 开始），不回显原文、许可材料或敏感字段。

## W1 可复现样例

```powershell
python -B scripts/source_registry.py --purpose research
python -B scripts/source_registry.py --purpose redistribution
python -B scripts/source_registry.py --purpose training
```

前两条应通过，第三条应以 1 退出（项目策略禁止训练）。
本周仅引入 [原创技术样例](datasets/w1-fixture.md)，无真实标准或企业语料。
公共文本固定 LF，以避免 Windows Git 换行转换破坏字节哈希。
