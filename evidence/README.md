# 分析证据与执行状态

第 1 题已完成实际统计、7 项计数交叉核对与代表提交抽查；报告见根目录的 [分析报告.md](../分析报告.md)。用户重新克隆仓库后，已使用 bash 完整重跑分析，汇总结果与此前完全一致，研究仓库分析前后工作区均无改动。目前无仓库恢复阻塞；学生已表达个人判断并确认第 1 问完成，观点已整理至报告 1.5 节。第 2 问已完成证据采集、量化与个人判断整理；第 3 问已完成合并与冲突证据分析、个人审阅及合并约定整理；第 4—6 问未开展。

## 当前命令约定

按用户最新要求，shell 命令使用 `/bin/bash`，工具设置 `login=false`，不启动交互式 zsh，也不执行 `proxy on/off`。下方代理与 zsh 内容仅是历史故障记录，不是现行操作流程。

## 当前结果与复现

- 快照：`0d1f50007f9bca3f52b06e1c3074fa14d5fb0720`，默认分支 `master`；详细元数据见 `snapshot.json`。该文件时间为首次分析记录时间，并非经独立确认的克隆完成时间。
- Git 对象连通性检查通过，非浅克隆；全部提交 17,177、合并 7,097、非合并 10,080。
- 日期跨度约 96.51 天，98 个日历日中 97 天有提交；峰值为 2026-07-30 的 846 条。
- 姓名＋邮箱作者身份 76 个，不等于真实人数；身份别名与异常线索见 `identity-candidates.json`。
- 按用户要求增加人员估计口径：合理合并后约 39 名贡献者，共 17,167 条提交；机器人 8 条、身份不明账号 2 条单列。前五占 69.87%，前十占 88.43%。本口径取代原始身份数作为报告人员分布的主要展示。
- 运行 `python3 scripts/group_q1_authors.py` 复现合并统计与图表。`author-group-mapping.csv` 记录每个原始身份的归属、理由和置信度，`contributors-grouped.csv` 包含完整排名、差值与累计占比，`contributor-distribution.csv` 按提交量区间统计人数，`q1-grouped-summary.json` 保存汇总及 6 项校验，`contributor-concentration.svg` 是报告引用的静态图。
- 在作业根目录使用 bash 运行 `python3 scripts/analyze_q1.py`，即可复用固定快照生成证据，无需重新下载。
- `q1-summary.json` 为汇总与检查结果；`commands-q1.json` 为实际 Git 参数及输出；各 CSV 为完整统计表；`daily-commits.svg` 为图表；`q1-case-details.txt` 为抽查证据。
- `q1-reverification.json` 记录本轮恢复后的快照、完整重跑一致性和工作区状态；本轮未执行代理命令。

## 获取过程历史记录

- 沙箱内完整克隆失败：无法连接本地代理 `127.0.0.1:7890`。
- 获准在沙箱外完整克隆后，传输因 TLS 连接异常中断，Git 返回 `early EOF` 与 `invalid index-pack output`。
- 随后使用 HTTP/1.1 重试完整克隆的权限请求被拒绝，未继续网络操作。
- 用户随后指定统一使用本用户 zsh，并在网络下载前后执行 `proxy on` / `proxy off`。非交互 zsh 未识别 `proxy`；本轮通过加载用户配置的交互式 `zsh -ic` 成功识别该函数。
- 最新一次完整克隆已输出 `Proxy ON -> 127.0.0.1:7890`，随后因 `gnutls_handshake() failed: The TLS connection was non-properly terminated` 失败，最后已输出 `Proxy OFF`。遵照用户约定，不再重试，等待用户手动下载完整仓库。
- 随后按用户要求尝试 SSH；本机配置将 GitHub 指向 `ssh.github.com:443`。用户告知仓库已就绪后，本轮确认本地仓库完整可读，实际 origin 为 HTTPS URL。不能据此确定最终仓库由哪一次下载产生。
- 第 1 题分析成功完成后，最终 `git status` 返回仓库目录不存在；原后台 SSH 克隆同期返回 `tmp_pack_bXnpME ... No such file or directory` 和 `invalid index-pack output`。该克隆进程已退出并执行 `proxy off`。不把时间上的重合断言为目录消失的原因。
- 用户再次手动克隆后，已确认仓库不是浅克隆、HEAD 与既定快照一致，重新执行全部第 1 题统计及连通性检查成功。此前阻塞已解除。

## 另一个环境首次获取仓库

仅在新环境尚无仓库时执行完整克隆；当前仓库已恢复，无需再次下载：

```bash
git clone https://github.com/deepseek-ai/deepseek-harness.git deepseek-harness
python3 scripts/analyze_q1.py
```

以上命令使用 bash；仅在克隆成功后运行统计脚本。不执行代理开关命令，下载失败后交由用户手动处理。

不要使用 `--depth`。如已有可用仓库，无需再次克隆。

脚本首次运行会保存 `snapshot.json`，后续运行复用其中的提交哈希；分析范围为该快照默认分支可达的所有提交，按 UTC committer 时间统计。作者时间另表输出。原始身份及快照 `.mailmap` 映射后的身份同时保留，仅有明确 `[bot]` 标签时自动标注机器人候选，其余身份需人工核查。

预期生成：完整提交 CSV、每日统计 CSV、作者与提交者贡献 CSV、每日提交 SVG、汇总 JSON，以及包含 Git 参数与原始输出的命令记录。脚本内核对 Git 直接计数、合并计数、每日与作者汇总、shortlog 总数及身份数。

已完成峰值日期、身份别名与代表提交抽查，并写入第 1 题报告；学生审阅与个人判断已完成。第一问完成；第二问证据见 [q2/README.md](q2/README.md)，个人判断已整理；第三问已完成证据分析、个人审阅与合并约定整理，统计与案例见 [q3/README.md](q3/README.md)；第四至第六问尚未开展。
