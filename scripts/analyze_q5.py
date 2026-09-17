#!/usr/bin/env python3
"""保存第五问两条过程线索及 CI 演变，仅读取固定历史。"""
import json
from pathlib import Path
import subprocess

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / 'evidence/q5'
HEAD = json.loads((BASE / 'evidence/snapshot.json').read_text())['head']
COMMANDS = []


def git(*args):
    p = subprocess.run(['git', '--no-optional-locks', '-C', str(BASE / 'deepseek-harness'), *args],
                       capture_output=True, text=True, check=True)
    COMMANDS.append({'args': list(args), 'exit_code': p.returncode})
    return p.stdout


def main():
    OUT.mkdir(exist_ok=True)
    before = git('status', '--porcelain')
    refs = {}
    for short in ['25555c9cfc', '33fa98b3c2', 'fced51d4eb', '43d81b67ce', '3c4c6c3d7b', 'a2d0f7f411']:
        sha = git('rev-parse', short).strip()
        git('merge-base', '--is-ancestor', sha, HEAD)
        refs[short] = sha
    diff_cases = {
        'goal-initial': ('25555c9cfc', ['docs/rfc/implemented/feature/2026-07-19-same-session-goal-round-driver.md',
            'packages/goal/goal-session/src', 'packages/goal/goal-session/tests']),
        'goal-pause-fix': ('33fa98b3c2', ['packages/goal/goal-round-driver/src/index.ts',
            'packages/goal/goal-round-driver/tests/goal-round-driver.spec.ts']),
        'env-acp-fix': ('fced51d4eb', ['packages/subagent/subagent-acp']),
        'env-shared-fix': ('43d81b67ce', ['packages/subprocess/subprocess', 'packages/subagent/subagent-acp/src/run.ts',
            'packages/lsp/lsp-local']),
        'ci-cancellation-change': ('3c4c6c3d7b', ['.github/workflows/ci.yml', '.github/workflows/ci-master.yml',
            'scripts/ci-workflow.spec.ts', 'scripts/tests/ci-master-platforms.spec.ts']),
    }
    for name, (short, paths) in diff_cases.items():
        sha = refs[short]
        body = git('show', '-s', '--format=fuller', sha)
        body += git('show', '--format=', '--no-ext-diff', '--no-textconv', sha, '--', *paths)
        (OUT / f'{name}.txt').write_text(body)
    documents = {
        'goal-design-at-introduction': (refs['25555c9cfc'], 'docs/rfc/implemented/feature/2026-07-19-same-session-goal-round-driver.md'),
        'goal-design-at-snapshot': (HEAD, '.agents/notes/archived/feature/2026-07-19-same-session-goal-round-driver.md'),
        'ci-current': (HEAD, '.github/workflows/ci.yml'),
        'ci-master-current': (HEAD, '.github/workflows/ci-master.yml'),
        'ci-change-rationale': (refs['3c4c6c3d7b'], '.agents/notes/implemented/process/2026-09-09-cancel-superseded-ci.md'),
    }
    for name, (sha, path) in documents.items():
        body = git('show', f'{sha}:{path}')
        (OUT / f'{name}.txt').write_text(f'提交：{sha}\n路径：{path}\n\n' + ''.join(
            f'{i:4d} | {line}\n' for i, line in enumerate(body.splitlines(), 1)))
    (OUT / 'goal-path-history.txt').write_text(git('log', '--follow', '--format=%H %cI %s', HEAD,
        '--', 'packages/goal/goal-round-driver/src/prompt.ts'))
    (OUT / 'goal-test-history.txt').write_text(git('log', '--follow', '--format=%H %cI %s', HEAD,
        '--', 'packages/goal/goal-round-driver/tests/goal-round-driver.spec.ts'))
    (OUT / 'goal-rename.txt').write_text(git('show', '--format=fuller', '--name-status', '--find-renames',
        refs['a2d0f7f411'], '--', 'packages/goal/goal-session', 'packages/goal/goal-round-driver'))
    git('merge-base', '--is-ancestor', refs['25555c9cfc'], refs['33fa98b3c2'])
    parent = git('rev-parse', refs['43d81b67ce'] + '^').strip()
    checks = {'all_six_commits_reachable': True,
              'goal_initial_is_ancestor_of_later_fix': True,
              'shared_env_fix_directly_follows_acp_fix': parent == refs['fced51d4eb'],
              'research_worktree_unchanged': before == git('status', '--porcelain')}
    summary = {'head': HEAD, 'commits': refs, 'checks': checks,
               'scope': '两条定向过程线索和一条 CI 配置演变；未运行研究项目测试或查询 CI 运行结果'}
    (OUT / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    (OUT / 'commands.json').write_text(json.dumps(COMMANDS, ensure_ascii=False, indent=2) + '\n')
    assert all(checks.values())
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
