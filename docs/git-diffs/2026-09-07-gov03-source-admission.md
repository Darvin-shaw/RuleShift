# GOV-03：来源登记与准入校验

日期：2026-09-07。

## 涉及文件

`.gitattributes`、`README.md`、`data/README.md`、`data/public/SYN-W1-001.txt`、
`data/sources/manifest.json`、`docs/datasets/w1-fixture.md`、`docs/source-registry.md`、
`docs/innovation-log.md`、`docs/ruleshift-development-plan.md`、`scripts/source_registry.py`、
`tests/test_source_registry.py`、本总结。

## 要点

- 新增标准库只读 CLI、严格 JSON 字段契约、五项用途和有效期校验。
- 检查精确字节哈希、保守路径、唯一 ID／文件、上游依赖环与权限升级。
- 加入 1 份原创技术 fixture、透明数据卡和 LF 换行规则，不引入真实标准正文。
- README、WBS、创新台账同步；GOV-04 仍待实现。

## 验证与影响

- 定向 19 项：18 通过、1 跳过（Windows 缺少符号链接创建权限，错误 1314）。
- 全量 88 项：87 通过、同一符号链接测试跳过；旧 69 项全部通过。
- research／redistribution CLI 通过；training 拒绝及非零退出、报错脱敏已测试。
- 已审阅 git diff 和新增文件暂存差异；git diff --cached --check 通过。
- 技术检查不认证来源权利、审查者身份或事实真实性；无外部模型调用与新依赖。
