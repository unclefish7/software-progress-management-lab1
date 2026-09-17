#!/usr/bin/env python3
"""从固定快照统计合并，并保存冲突案例；只读研究仓库。"""
import collections
import csv
import json
from pathlib import Path
import re
import subprocess

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / 'evidence/q3'
REPO = BASE / 'deepseek-harness'
HEAD = json.loads((BASE / 'evidence/snapshot.json').read_text())['head']
COMMANDS = []


def git(*args):
    result = subprocess.run(['git', '--no-optional-locks', '-C', str(REPO),
                             *args], capture_output=True, text=True, check=True)
    COMMANDS.append({'args': list(args), 'exit_code': result.returncode})
    return result.stdout


def save(name, data):
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def table(name, rows, fields):
    with (OUT / name).open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def category(subject):
    for prefix, label in [
        ('Merge pull request #', 'PR 标题'),
        ('Merge remote-tracking branch ', '远端跟踪分支标题'),
        ('Merge branch ', '本地分支标题'),
        ('Merge commit ', '指定提交标题'),
    ]:
        if subject.startswith(prefix):
            return label
    return '其他标题'


def main():
    OUT.mkdir(exist_ok=True)
    before = git('status', '--porcelain')
    raw = git('log', HEAD, '--format=%H%x00%P%x00%B%x00').split('\0')
    rows, candidates = [], []
    marker = re.compile(r'^\s*#?\s*Conflicts:\s*$', re.M | re.I)
    keyword = re.compile(r'conflict|冲突', re.I)
    for i in range(0, len(raw) - 1, 3):
        sha, parents, message = raw[i].strip(), raw[i + 1].split(), raw[i + 2]
        row = {'hash': sha, 'parents': ' '.join(parents),
               'parent_count': len(parents), 'subject': message.splitlines()[0],
               'category': category(message.splitlines()[0]) if len(parents) > 1 else '非合并',
               'conflicts_block': bool(marker.search(message))}
        rows.append(row)
        if keyword.search(message):
            candidates.append({**row, 'message': message})
    merges = [row for row in rows if row['parent_count'] > 1]
    first = git('rev-list', '--first-parent', '--min-parents=2', HEAD).splitlines()
    counts = collections.Counter(row['category'] for row in merges)
    parent_counts = collections.Counter(row['parent_count'] for row in rows)
    checks = {
        'total_matches_git': len(rows) == int(git('rev-list', '--count', HEAD)),
        'merges_match_git': len(merges) == int(git('rev-list', '--count', '--min-parents=2', HEAD)),
        'non_merges_match_git': len(rows) - len(merges) == int(git('rev-list', '--count', '--no-merges', HEAD)),
        'categories_sum_to_merges': sum(counts.values()) == len(merges),
        'first_parent_subset': set(first) <= {row['hash'] for row in merges},
    }
    table('merges.csv', merges, list(rows[0]))
    table('conflict-candidates.csv', candidates, [*rows[0], 'message'])
    table('merge-types.csv', [{'category': k, 'count': v} for k, v in counts.items()], ['category', 'count'])
    (OUT / 'first-parent-merges.txt').write_text('\n'.join(first) + '\n')
    # 定向选择：PR 汇入、同步主线且有冲突清单、显式解决文档冲突；另选两条非合并修复。
    cases = ['0d1f50007f', '1b7b50bbe1', 'a38c302e4a', 'eba45d9add', 'e8e0ec4176']
    case_records = []
    all_hashes = {row['hash'] for row in rows}
    for short in cases:
        sha = git('rev-parse', short).strip()
        assert sha in all_hashes
        body = git('show', '-s', '--format=fuller', sha)
        if short in ('eba45d9add', 'e8e0ec4176'):
            body += git('show', '--format=', '--no-ext-diff', '--no-textconv', sha)
        elif short == '1b7b50bbe1':
            # 分别与两个父提交比较同一文件，不把普通合入差异全算成冲突解决。
            for parent in (1, 2):
                body += f'\n与父提交 {parent} 比较 apps/web/package.json：\n'
                body += git('diff', '--no-ext-diff', '--no-textconv', f'{sha}^{parent}', sha,
                            '--', 'apps/web/package.json')
        (OUT / f'case-{short}.txt').write_text(body)
        case_records.append({'hash': sha, 'file': f'case-{short}.txt'})
    (OUT / 'branch-graph.txt').write_text(git('log', '--graph', '-12', '--format=%h %p %s', HEAD))
    # 直接核查冲突残留确实存在于父版本，并在修复后移除。
    path = 'packages/test-support/session-snapshot/src/normalize.ts'
    previous = git('show', f'e8e0ec4176^:{path}')
    repaired = git('show', f'e8e0ec4176:{path}')
    residue = '||||||| parent of 842fdd6a51'
    checks['residue_present_before_removed_after'] = residue in previous and residue not in repaired
    checks['research_worktree_unchanged'] = before == git('status', '--porcelain')
    summary = {
        'head': HEAD, 'git_version': git('--version').strip(),
        'total': len(rows), 'merges': len(merges),
        'merge_percent': 100 * len(merges) / len(rows),
        'parent_counts': dict(parent_counts), 'title_categories': dict(counts),
        'first_parent_merges': len(first),
        'first_parent_pr_titles': sum(row['category'] == 'PR 标题' for row in merges if row['hash'] in set(first)),
        'conflict_keyword_candidates': len(candidates),
        'conflicts_block_commits': sum(row['conflicts_block'] for row in rows),
        'conflicts_block_merge_commits': sum(row['conflicts_block'] for row in merges),
        'candidate_regex': keyword.pattern, 'conflicts_block_regex': marker.pattern,
        'cases': case_records, 'checks': checks,
    }
    save('summary.json', summary)
    save('commands.json', COMMANDS)
    assert all(checks.values()), checks
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
