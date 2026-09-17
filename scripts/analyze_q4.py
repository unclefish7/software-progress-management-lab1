#!/usr/bin/env python3
"""保存第四问定向案例；分类为人工解释，不按文件名自动判读者。"""
import csv
import json
from pathlib import Path
import subprocess

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / 'evidence/q4'
HEAD = json.loads((BASE / 'evidence/snapshot.json').read_text())['head']
COMMANDS = []
FILES = [
    ('root-readme', 'README.md', '人类为主', '启动入口、社区链接，并另指向 agent 指令'),
    ('user-guide', 'docs/user/guide/index.md', '人类为主', '按界面操作顺序指导配置模型、选择工作区和运行任务'),
    ('contributing', 'CONTRIBUTING.md', '人类为主', '面向社区说明贡献途径；仅描述固定快照政策'),
    ('agent-instructions', 'AGENTS.md', '开发 agent 为主', '常驻规则、验证要求以及链接导航；人类也需维护和审阅'),
    ('doc-standard', 'docs/AGENTS.md', '开发 agent 与维护者共享', '明确区分 human-facing docs、agent standing orders 和设计决策'),
    ('notes-guide', '.agents/notes/README.md', '人和开发 agent 共享', '保存动机、方案、替代方案与后果，避免重复争论'),
    ('doc-decision', '.agents/notes/implemented/process/2026-07-04-doc-tiers-and-budgets.md', '人和开发 agent 共享', '解释文档分层及字数预算的理由与取舍'),
    ('package-readme', 'packages/core/system-prompt/README.md', '人和开发 agent 共享', '解释提示词组件配置；描述模型体验不等于整篇是提示词'),
    ('goal-prompt', 'packages/goal/goal-round-driver/src/prompt.ts', '字符串面向运行时 agent；JSDoc 面向维护者与开发 agent', '同文件内有两种用途，结合调用链区分'),
    ('goal-caller', 'packages/goal/goal-round-driver/src/index.ts', '提示词调用位置证据', 'renderGoalRoundPrompt → createUserMessage → agent.followup'),
]
COMMITS = ['43d81b67cef2a957afd2cb0646894757f3f28315',
           'e8e0ec417631a91f0365225767bd2df7c3fb79f8']


def git(*args):
    result = subprocess.run(['git', '--no-optional-locks', '-C', str(BASE / 'deepseek-harness'),
                             *args], capture_output=True, text=True, check=True)
    COMMANDS.append({'args': list(args), 'exit_code': result.returncode})
    return result.stdout


def main():
    OUT.mkdir(exist_ok=True)
    before = git('status', '--porcelain')
    contents, rows = {}, []
    for name, path, audience, reason in FILES:
        content = git('show', f'{HEAD}:{path}')
        contents[name] = content
        # 带原文件行号保存，便于报告审阅；不复制为可执行的指令文件。
        (OUT / f'{name}.txt').write_text(f'快照：{HEAD}\n路径：{path}\n\n' +
            ''.join(f'{i:4d} | {line}\n' for i, line in enumerate(content.splitlines(), 1)))
        rows.append({'path': path, 'audience': audience, 'reason': reason, 'evidence': f'{name}.txt'})
    with (OUT / 'audience-cases.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    messages = []
    for sha in COMMITS:
        git('merge-base', '--is-ancestor', sha, HEAD)
        messages.append(git('show', '-s', '--format=fuller', sha))
    (OUT / 'commit-messages.txt').write_text('\n'.join(messages))
    checks = {
        'ten_selected_files_saved': len(contents) == 10,
        'readme_explicit_agent_entry': 'For agents, follow [AGENTS.md]' in contents['root-readme'],
        'standard_explicit_human_scope': 'These rules apply to human-facing documentation' in contents['doc-standard'],
        'prompt_caller_chain_present': all(x in contents['goal-caller'] for x in
            ['const content = renderGoalRoundPrompt(goal, round)', 'const message = createUserMessage({', 'agent.followup(message)']),
        'research_worktree_unchanged': before == git('status', '--porcelain'),
    }
    summary = {'head': HEAD, 'selection': '定向选择十个文件和两条提交，不作全仓库读者比例估计',
               'commit_cases': COMMITS, 'checks': checks}
    (OUT / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    (OUT / 'commands.json').write_text(json.dumps(COMMANDS, ensure_ascii=False, indent=2) + '\n')
    assert all(checks.values()), checks
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
