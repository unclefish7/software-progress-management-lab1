# 软件过程管理课程 Lab1：开发过程分析

本仓库用于完成“软件过程管理与工程伦理”课程的个人实验：借助 AI 编程助手分析 deepseek-harness 的 Git 提交历史，理解团队与 AI 协作者如何组织开发，并提炼适用于后续小组开发的协作规范。

研究重点是开发过程，包括提交频率、贡献分布、合并、文档、测试与质量管理。作业要求见 [Lab1.md](Lab1.md)，分析结果见 [分析报告.md](分析报告.md)。

## 当前进度

六个问题均已完成证据分析和个人审阅。报告覆盖开发周期与团队、AI 参与、合并冲突、文档用途、需求到测试的过程，以及发布、命名重构和持久化迁移等现象，并整理了适用于后续小组开发的实践启示。

固定分析快照为 `0d1f50007f9bca3f52b06e1c3074fa14d5fb0720`，覆盖默认分支 `master` 在该提交处可达的历史。主要发现：

- 可观察开发跨度约 96.51 天，98 个日历日中有 97 天存在提交。
- 共 17,177 条提交，其中 7,097 条为合并提交。
- 合理归并作者身份后估计约 39 名贡献者，机器人与身份不明账号单列；前五名贡献约 69.87%，前十名约 88.43%。

人数是基于记录归并的估计，提交次数也不等于工作量或贡献价值。统计口径、合并依据与局限在报告中说明。

## 文件说明

| 路径 | 用途 |
|---|---|
| `Lab1.md` | 原始作业要求 |
| `分析报告.md` | 按六个问题组织的完整报告，包含证据、论证、局限与个人判断 |
| `scripts/analyze_q1.py` | 固定快照，提取 Git 历史，统计时间和身份分布并交叉核对 |
| `scripts/group_q1_authors.py` | 按明确规则归并身份，生成贡献排名、人数分布与图表 |
| `scripts/analyze_q2.py` | 检索 AI 评审证据，追踪工具命名分支并分层抽查 |
| `scripts/analyze_q3.py` | 统计合并类型与冲突记录，保存父版本对比和修复案例 |
| `scripts/analyze_q4.py` | 保存文档读者案例、提交说明及提示词调用证据 |
| `scripts/analyze_q5.py` | 追踪两条开发线索，保存实现、测试及 CI 演变证据 |
| `scripts/analyze_q6.py` | 统计发布节奏，保存命名重构和持久化迁移证据 |
| `evidence/` | 原始输出、统计表、身份映射、提交案例、图表和复核记录 |
| `deepseek-harness/` | 本地研究对象的完整克隆，由 `.gitignore` 排除 |

证据索引与执行记录见 [evidence/README.md](evidence/README.md)。证据材料纳入版本管理，以便审阅者直接核查报告数字；研究对象的源码和 Git 对象不纳入本仓库。

## 复现第一问

需要 Git 和 Python 3；脚本仅使用 Python 标准库，无需安装或运行研究对象的项目依赖。以下命令使用 bash。

首次准备研究对象时，在本仓库根目录执行完整克隆；已有完整仓库则跳过，不使用 `--depth`：

```bash
git clone https://github.com/deepseek-ai/deepseek-harness.git deepseek-harness
```

随后按顺序运行：

```bash
python3 scripts/analyze_q1.py
python3 scripts/group_q1_authors.py
```

第一个脚本读取已提交的 `evidence/snapshot.json`，复用固定提交而非最新 HEAD，并重新生成相关证据；第二个脚本读取这些证据，生成合并后的贡献分布。研究仓库必须包含该快照提交。脚本不会修改研究对象源码或 Git 历史。

原始统计有 7 项计数交叉核对，归并统计有 6 项映射和总量核对。此前完整重跑的一致性记录保存在 `evidence/q1-reverification.json`；该文件是当次执行记录，不会因上述两个脚本运行而自动更新。

## 复现第二问

```bash
python3 scripts/analyze_q2.py
```

使用同一研究仓库和固定快照，输出至 `evidence/q2/`。方法与证据见 [第二问证据索引](evidence/q2/README.md)。可见的 AI 评审与工具命名分支关联率不等于实际 AI 生成代码比例。

## 复现第三问

```bash
python3 scripts/analyze_q3.py
```

使用同一固定快照，输出至 `evidence/q3/`。方法与案例见 [第三问证据索引](evidence/q3/README.md)。合并数量、冲突记录数量和处理正确性分别讨论，七项核对通过。

## 复现第四问

```bash
python3 scripts/analyze_q4.py
```

从固定快照提取定向案例，输出至 `evidence/q4/`。见 [第四问证据索引](evidence/q4/README.md)。读者分类依据内容与用途，不估计全仓库读者比例。

## 复现第五问

```bash
python3 scripts/analyze_q5.py
```

从固定历史提取功能、修复及 CI 案例，见 [第五问证据索引](evidence/q5/README.md)。本轮未运行研究项目测试，源码与配置证据不等于实际通过记录。

## 复现第六问

```bash
python3 scripts/analyze_q6.py
```

统计固定历史中的 dsh 版本提交，并提取命名规范重构和会话格式迁移案例，见[第六问证据索引](evidence/q6/README.md)。发布提交不等于注册表发布成功，项目记录中的迁移测试与基准未在本轮重跑。

## 提交与后续工作

本仓库保留 AI 分析证据与个人判断的区分。六个问题均已完成并经过本人审阅，统计口径、案例哈希、复现脚本和证据限制保存在报告及 `evidence/` 中。

提交信息采用 Conventional Commits 格式，类型使用标准前缀，主题和正文使用中文。远端推送由仓库所有者自行执行。
