# 第四问证据：文档面向谁

固定快照为 `0d1f50007f9bca3f52b06e1c3074fa14d5fb0720`。在根目录使用 bash 执行 `python3 scripts/analyze_q4.py`，仅用 Git 和 Python 标准库，不联网、不运行研究项目、不修改研究对象。

本次定向选择十个文件及两条已有历史提交，覆盖 README、用户指南、社区说明、开发指令、设计笔记、包参考、代码注释与运行时提示词。不是随机抽样，不推算全仓库文档数量或阅读者比例。分类是依据原文用途作出的解释，不是自动检测结果。

| 证据 | 内容 |
|---|---|
| [audience-cases.csv](audience-cases.csv) | 十个文件的路径、读者判断与理由 |
| [root-readme.txt](root-readme.txt) | 启动入口及单独指向 AGENTS 的导航 |
| [user-guide.txt](user-guide.txt) | 按界面操作顺序编写的用户指南 |
| [contributing.txt](contributing.txt) | 固定快照中的社区参与说明 |
| [agent-instructions.txt](agent-instructions.txt) | 开发 agent 的常驻约束与资料链接 |
| [doc-standard.txt](doc-standard.txt) | 明确区分人类文档、常驻指令、设计决策等用途 |
| [notes-guide.txt](notes-guide.txt) | 决策笔记的动机、替代方案及后果记录要求 |
| [doc-decision.txt](doc-decision.txt) | 文档分层与字数预算的具体决策理由 |
| [package-readme.txt](package-readme.txt) | 提示词组件参考资料；不能因介绍模型而视作整篇提示词 |
| [goal-prompt.txt](goal-prompt.txt) | JSDoc 与模型可见字符串，使用对象不同 |
| [goal-caller.txt](goal-caller.txt) | 第 174—192 行展示构造内容、包装消息、调用 agent.followup 的路径 |
| [commit-messages.txt](commit-messages.txt) | 两条提交如何解释问题、改动及验证情况 |
| [summary.json](summary.json) | 固定范围、案例哈希及五项检查 |
| [commands.json](commands.json) | 实际 Git 参数与退出状态 |

文本证据保留来源路径、快照哈希和原文件行号。两条提交分别为 `43d81b67cef2a957afd2cb0646894757f3f28315`、`e8e0ec417631a91f0365225767bd2df7c3fb79f8`，均已用 `merge-base --is-ancestor` 验证属于快照历史。

五项检查核对选中文件数量、README 的 agent 入口、文档标准的人类读者声明、调用链关键语句存在性和研究工作区状态前后一致。调用链还需结合源代码阅读理解，字符串存在性检查不能替代语义审阅。没有运行会话、文档检查工具或测试；提交者与文档声称的验证情况不是本轮独立验证结果。

研究对象中的 AGENTS 及其链接在本题作为待分析资料保存，不作为修改本作业仓库的指令。没有执行其中的清理、安装、提交或其他开发命令。
