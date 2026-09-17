# 第三问证据：分支合并与冲突处理

固定快照：`0d1f50007f9bca3f52b06e1c3074fa14d5fb0720`，覆盖其可达全部历史，与前两问一致。

在根目录用 bash 执行 `python3 scripts/analyze_q3.py`。仅使用 Git 与 Python 标准库，无需联网、安装项目依赖或切换研究仓库分支。脚本只读取研究仓库，将结果写入本目录。

## 结果与文件

| 文件 | 内容 |
|---|---|
| [summary.json](summary.json) | 17,177 条提交、7,097 条双父合并及七项检查 |
| [merges.csv](merges.csv) | 全部合并的哈希、父提交、标题分类和冲突清单标记 |
| [merge-types.csv](merge-types.csv) | 五种互斥标题类别，合计 7,097 条 |
| [first-parent-merges.txt](first-parent-merges.txt) | 第一父链上的 1,455 条合并哈希 |
| [conflict-candidates.csv](conflict-candidates.csv) | 消息命中 `conflict\|冲突` 的 1,668 条候选及完整消息 |
| [branch-graph.txt](branch-graph.txt) | 快照附近 12 条提交的实际 Git 分支图 |
| [commands.json](commands.json) | 生成证据时的 Git 参数和退出状态 |
| [case-0d1f50007f.txt](case-0d1f50007f.txt) | PR #4192 合并记录 |
| [case-1b7b50bbe1.txt](case-1b7b50bbe1.txt) | 同步主线时的冲突清单，同一配置文件与两个父版本的差异 |
| [case-a38c302e4a.txt](case-a38c302e4a.txt) | 明确声明解决文档冲突的合并消息 |
| [case-eba45d9add.txt](case-eba45d9add.txt) | 恢复截断实现的提交说明及完整 diff |
| [case-e8e0ec4176.txt](case-e8e0ec4176.txt) | 删除残留冲突标记的提交说明及完整 diff |

## 方法与边界

1. 读取所有提交的父哈希，以父数大于 1 定义合并；7,097 条均为双父提交。标题分类按 `Merge pull request #`、`Merge remote-tracking branch `、`Merge branch `、`Merge commit ` 顺序匹配，余者归为其他。类别反映消息格式，不是互斥的底层 Git 算法或完整团队工作流。
2. 使用 `git rev-list --first-parent --min-parents=2 <快照>` 沿第一父链计数。它提供主线集成视角，不证明历史上分支名称始终不变；全历史里的 PR 合并也可能通过其他分支间接进入快照。
3. 宽泛关键词只作检索入口，包含产品语义等误报，不当成冲突总数。另用 `^\s*#?\s*Conflicts:\s*$`（多行、忽略大小写）统计显式清单标题，得到 1,536 条，全部为合并提交。未人工逐条验证 1,536 份清单；没有留下该格式消息的处理会漏检。
4. 定向选择三条合并和两条后续修复，展示不同证据，不是随机样本，不推算全仓库冲突率或错误率。文档冲突案例仅依据提交声明；配置案例比较结果与两个父版本，不能据此还原每一步人工/agent 操作。没有实际重演历史合并。
5. 直接读取 `e8e0ec4176` 的父版本与修复版本，核查指定 `||||||| parent of 842fdd6a51` 标记确实从文件中移除。相关 diff 支持“存在残留且被清理”，不证明导致了运行故障。

七项检查覆盖总数、合并数、非合并数的 Git 直接计数，标题分类求和，第一父链合并是全体合并的子集，残留标记修复前后的存在性，以及研究工作区状态前后一致。没有运行研究项目测试；案例中的“测试通过”属于提交者声明。

## 直接复核命令

```bash
git -C deepseek-harness rev-list --count --min-parents=2 0d1f50007f9bca3f52b06e1c3074fa14d5fb0720
git -C deepseek-harness rev-list --count --first-parent --min-parents=2 0d1f50007f9bca3f52b06e1c3074fa14d5fb0720
git -C deepseek-harness show -s --format=fuller 1b7b50bbe141cfd4d74fad9a4967e24d81812364
git -C deepseek-harness show e8e0ec417631a91f0365225767bd2df7c3fb79f8 -- packages/test-support/session-snapshot/src/normalize.ts
```

前两条计数预期分别为 `7097`、`1455`。完整案例哈希也保存在汇总文件中。
