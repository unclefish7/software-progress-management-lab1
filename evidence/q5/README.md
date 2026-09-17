# 第五问证据：需求、设计、实现与测试

固定终点为 `0d1f50007f9bca3f52b06e1c3074fa14d5fb0720`。在根目录用 bash 执行 `python3 scripts/analyze_q5.py`，仅使用 Git 与 Python 标准库。所有历史提交先检查是否属于该快照，不联网、不运行研究项目测试、不修改研究仓库。

## 案例与复现材料

| 文件 | 用途 |
|---|---|
| [summary.json](summary.json) | 六条案例提交的完整哈希、分析范围、四项核对 |
| [commands.json](commands.json) | 实际 Git 参数和退出状态 |
| [goal-initial.txt](goal-initial.txt) | 初次功能提交中的设计笔记、实现及测试 diff |
| [goal-design-at-introduction.txt](goal-design-at-introduction.txt) | 初次实现时的 RFC 全文及原行号 |
| [goal-design-at-snapshot.txt](goal-design-at-snapshot.txt) | 终点快照中的归档版本，用于说明版本差异，不倒推初始设计 |
| [goal-path-history.txt](goal-path-history.txt) | 提示词路径沿重命名追踪的历史 |
| [goal-test-history.txt](goal-test-history.txt) | 单元测试沿重命名追踪的历史 |
| [goal-rename.txt](goal-rename.txt) | goal-session 到 goal-round-driver 的路径对应 |
| [goal-pause-fix.txt](goal-pause-fix.txt) | 后续暂停/恢复竞态修复与新增回归测试 |
| [env-acp-fix.txt](env-acp-fix.txt) | 首次 ACP 环境变量修复及测试、文档同步 |
| [env-shared-fix.txt](env-shared-fix.txt) | 直接后继提交中的评审发现、共享逻辑、LSP 回归测试 |
| [ci-current.txt](ci-current.txt) | 固定快照的 PR 检查工作流 |
| [ci-master-current.txt](ci-master-current.txt) | 固定快照的主线检查工作流 |
| [ci-cancellation-change.txt](ci-cancellation-change.txt) | CI 取消策略及对应配置测试的历史变更 |
| [ci-change-rationale.txt](ci-change-rationale.txt) | 同次提交记录的 CI 决策与取舍 |

## 证据边界

- 定向选择一条功能线索、一条修复线索及 CI 演变，不是完整项目过程模型普查。
- 设计说明读取初次实现提交的版本，而非将当前笔记内容当作最早需求。初次提交时已是 implemented，不能证明先写设计后写代码，也不能证明测试驱动开发。
- `--follow` 与重命名差异用于追踪选定文件，不能代表相关功能所有历史都已穷尽。全哈希、原始路径和提交时间保留于文本；先后关系以提交祖先关系核对，不仅依赖时间戳。
- 四项检查为六个提交均可达、功能初始提交是后续修复祖先、共享环境变量修复直接接在 ACP 修复之后，以及研究工作区前后状态一致。
- 测试源码说明验证意图，工作流配置说明预期执行安排。没有独立获取当时测试输出、CI 运行结果、分支保护设置或需求讨论记录；因此不声称测试通过、检查强制执行或需求已由人类验收。
