#!/usr/bin/env python3
"""提取第六问的发布、重命名与持久化迁移证据。"""
import collections
import csv
import datetime as dt
import json
from pathlib import Path
import re
import statistics
import subprocess

BASE = Path(__file__).resolve().parents[1]
REPO = BASE / 'deepseek-harness'
OUT = BASE / 'evidence/q6'
HEAD = json.loads((BASE / 'evidence/snapshot.json').read_text())['head']
COMMANDS = []


def git(*args):
    result = subprocess.run(
        ['git', '--no-optional-locks', '-C', str(REPO), *args],
        capture_output=True, text=True, check=True,
    )
    COMMANDS.append({'args': list(args), 'exit_code': result.returncode})
    return result.stdout


def save_source(name, sha, path):
    content = git('show', f'{sha}:{path}')
    (OUT / name).write_text(
        f'提交：{sha}\n路径：{path}\n\n'
        + ''.join(f'{number:4d} | {line}\n' for number, line in enumerate(content.splitlines(), 1))
    )


def main():
    OUT.mkdir(exist_ok=True)
    before = git('status', '--porcelain')

    raw = git('log', HEAD, '--format=%H%x00%cI%x00%s%x00').split('\0')
    pattern = re.compile(r'release\(dsh\): (\d+\.\d+\.\d+(?:-(?:alpha|rc)\.\d+)?)$')
    releases = []
    for index in range(0, len(raw) - 1, 3):
        match = pattern.fullmatch(raw[index + 2].strip())
        if match:
            timestamp = dt.datetime.fromisoformat(raw[index + 1])
            version = match.group(1)
            releases.append({
                'hash': raw[index].strip(), 'committer_time': timestamp.isoformat(),
                'version': version,
                'channel': 'alpha' if '-alpha.' in version else 'rc' if '-rc.' in version else 'stable',
            })
    releases.sort(key=lambda row: row['committer_time'])
    for previous, current in zip(releases, releases[1:]):
        gap = dt.datetime.fromisoformat(current['committer_time']) - dt.datetime.fromisoformat(previous['committer_time'])
        current['hours_since_previous'] = f'{gap.total_seconds() / 3600:.6f}'
    releases[0]['hours_since_previous'] = ''
    with (OUT / 'dsh-release-commits.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(releases[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(releases)
    gaps = [float(row['hours_since_previous']) for row in releases[1:]]

    refs = {}
    for short in ['869b5c7bf2', 'a2d0f7f411', 'ea53423b60', 'f7a6221158', '98d2baf2e5', '5212603a4b']:
        sha = git('rev-parse', short).strip()
        git('merge-base', '--is-ancestor', sha, HEAD)
        refs[short] = sha

    save_source('release-policy.txt', HEAD,
                '.agents/notes/implemented/process/2026-08-10-npm-release-sequences.md')
    save_source('naming-proposal.txt', refs['869b5c7bf2'],
                '.agents/notes/proposed/architecture/2026-08-11-repository-naming-contract-and-rename-ledger.md')
    save_source('naming-final.txt', HEAD,
                '.agents/notes/archived/architecture/2026-08-11-repository-naming-contract-and-rename-ledger.md')
    save_source('session-migration-policy.txt', HEAD,
                '.agents/notes/implemented/architecture/2026-08-31-released-session-format-migrations.md')

    (OUT / 'latest-release.txt').write_text(
        git('show', '--format=fuller', '--stat', refs['ea53423b60'], '--', 'package.json',
            'apps/cli/package.json', 'pnpm-lock.yaml')
    )
    name_status = git('diff-tree', '--no-commit-id', '--name-status', '-r', '-M', refs['a2d0f7f411'])
    (OUT / 'naming-application-name-status.txt').write_text(name_status)
    (OUT / 'naming-application-summary.txt').write_text(
        git('show', '--format=fuller', '--shortstat', refs['a2d0f7f411'])
    )
    rename_counts = collections.Counter(line.split('\t', 1)[0][0] for line in name_status.splitlines())

    migration_cases = [refs['f7a6221158'], refs['98d2baf2e5'], refs['5212603a4b']]
    (OUT / 'session-migration-commits.txt').write_text('\n'.join(
        git('show', '-s', '--format=fuller', sha) + git('show', '--format=', '--stat', sha)
        for sha in migration_cases
    ))
    migration_paths = git('ls-tree', '-r', '--name-only', HEAD).splitlines()
    selected_paths = [path for path in migration_paths if
                      ('session-format' in path and ('migration' in path or 'historical-formats' in path))]
    (OUT / 'session-migration-paths.txt').write_text('\n'.join(selected_paths) + '\n')
    (OUT / 'session-v2-v3-case.txt').write_text(git(
        'show', '--format=fuller', refs['f7a6221158'], '--',
        'packages/session/session-format-v2-to-v3/src/migration.ts',
        'packages/session/session-format-v2-to-v3/tests/migration.spec.ts',
    ))

    release_summary = {
        'count': len(releases),
        'first': releases[0], 'last': releases[-1],
        'active_calendar_dates': len({row['committer_time'][:10] for row in releases}),
        'channels': dict(collections.Counter(row['channel'] for row in releases)),
        'median_gap_hours': statistics.median(gaps),
        'minimum_gap_hours': min(gaps), 'maximum_gap_hours': max(gaps),
        'matching_rule': pattern.pattern,
    }
    checks = {
        'release_rows_match_summary': len(releases) == release_summary['count'],
        'release_channels_sum': sum(release_summary['channels'].values()) == len(releases),
        'rename_statuses_sum_to_changed_files': sum(rename_counts.values()) == 3281,
        'rename_count_is_961': rename_counts['R'] == 961,
        'all_six_commits_reachable': True,
        'migration_paths_saved': len(selected_paths) > 0,
        'research_worktree_unchanged': before == git('status', '--porcelain'),
    }
    summary = {
        'head': HEAD, 'release_commits': release_summary,
        'naming_application': {
            'commit': refs['a2d0f7f411'], 'changed_files': 3281,
            'insertions': 21708, 'deletions': 21570,
            'status_counts': dict(rename_counts),
        },
        'session_migration_case_commits': migration_cases,
        'scope': '三个定向过程现象；发布数仅统计匹配规则的 dsh release 提交，不等于注册表发布次数',
        'checks': checks,
    }
    (OUT / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    (OUT / 'commands.json').write_text(json.dumps(COMMANDS, ensure_ascii=False, indent=2) + '\n')
    assert all(checks.values()), checks
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
