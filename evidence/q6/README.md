# 第六问证据：发布、命名重构与持久化迁移

固定终点为 `0d1f50007f9bca3f52b06e1c3074fa14d5fb0720`。在根目录用 bash 执行 `python3 scripts/analyze_q6.py`，仅使用 Git 与 Python 标准库，不联网、不运行研究项目、不修改研究仓库。

本题定向选择三个过程现象，不声称它们是项目中唯一重要的现象。

| 文件 | 内容 |
|---|---|
| [summary.json](summary.json) | 发布统计、命名重构规模、迁移案例提交与七项检查 |
| [commands.json](commands.json) | 实际 Git 参数和退出状态 |
| [dsh-release-commits.csv](dsh-release-commits.csv) | 27 条符合规则的 dsh 版本提交、时间、渠道与相邻间隔 |
| [release-policy.txt](release-policy.txt) | 固定快照中的发布序列、版本与可重试发布规则 |
| [latest-release.txt](latest-release.txt) | `0.1.6-alpha.1` 对根清单、CLI 清单和锁文件的变更 |
| [naming-proposal.txt](naming-proposal.txt) | 大规模重命名前的 proposed 决策及重命名清单 |
| [naming-final.txt](naming-final.txt) | 固定快照中归档的 implemented 命名决策 |
| [naming-application-summary.txt](naming-application-summary.txt) | 应用命名规范的提交说明和 shortstat |
| [naming-application-name-status.txt](naming-application-name-status.txt) | 3,281 个路径的修改、重命名、新增和删除分类 |
| [session-migration-policy.txt](session-migration-policy.txt) | 固定快照中的已发布会话格式迁移规则、性能问题与验证要求 |
| [session-migration-commits.txt](session-migration-commits.txt) | 三条迁移相关提交的说明和文件统计 |
| [session-v2-v3-case.txt](session-v2-v3-case.txt) | V2→V3 迁移实现及测试的定向差异 |
| [session-migration-paths.txt](session-migration-paths.txt) | 固定快照中名称命中会话迁移或历史格式的路径 |

## 统计口径与限制

- 发布统计只匹配标题完整符合 `release(dsh): <数字版本>`，且版本后缀仅为 `alpha.N`、`rc.N` 或无后缀的提交。合并提交、vendor/native 发布、版本对齐修复及其他标题不计入。它统计 Git 中的版本提交，不是 npm 注册表发布次数，也不能证明发布成功。
- 相邻间隔使用提交者时间的绝对时间差。17 个活跃日、27 条提交和 21.23 小时中位间隔描述可见节奏，不代表团队规定的发布周期。版本序列存在跳号，仅凭提交标题不能解释原因。
- 命名重构规模来自提交 shortstat；路径状态用 `git diff-tree -M` 的相似度检测，得到 961 条 rename、2,205 条修改、59 条新增和 56 条删除，共 3,281 条。Git 的 rename 是内容相似度判断，不记录文件系统中的“移动动作”；该提交也不是纯重命名。
- 会话迁移分析读取固定快照的决策说明，并抽查三个实现、文档或审计提交。文档中的性能数据和测试结果属于项目记录，本轮未重新运行基准或测试。路径名称检索只是证据索引，不用于计算完整覆盖率。
- 七项检查覆盖发布表与汇总一致、渠道求和、命名路径求和及 rename 数量、六条案例提交均在快照历史、迁移路径非空、研究工作区前后状态一致。

这些材料支持对发布管理、配置管理和持久化兼容策略的点评，但不能证明每次发布成功、每个重命名都正确，或所有历史会话都能迁移。
