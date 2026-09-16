#!/usr/bin/env python3
"""Freeze the default-branch snapshot on first run; reproduce Q1 using stdlib."""
import collections
import csv
import datetime as dt
import json
from pathlib import Path
import subprocess

BASE = Path(__file__).resolve().parents[1]
REPO = BASE / 'deepseek-harness'
OUT = BASE / 'evidence'
OUT.mkdir(exist_ok=True)
commands = []

def git(*args):
    p = subprocess.run(['git', '-C', str(REPO), *args], check=True, stdout=subprocess.PIPE)
    result = p.stdout.decode('utf-8', errors='replace')
    commands.append({'argv': ['git', '-C', 'deepseek-harness', *args], 'stdout': result})
    return result.strip()

def save(name, obj):
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')

def table(name, rows, fields):
    with (OUT / name).open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

def utc(epoch):
    return dt.datetime.fromtimestamp(int(epoch), dt.timezone.utc)

shallow = git('rev-parse', '--is-shallow-repository')
assert shallow == 'false', 'Full history required'
git('fsck', '--connectivity-only', '--no-dangling')
snapshot_path = OUT / 'snapshot.json'
if snapshot_path.exists():
    snapshot = json.loads(snapshot_path.read_text())
else:
    branch = git('symbolic-ref', 'refs/remotes/origin/HEAD')
    head = git('rev-parse', branch)
    snapshot = {'retrieved_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
                'remote': git('remote', 'get-url', 'origin'), 'default_ref': branch,
                'head': head, 'shallow': False,
                'roots': git('rev-list', '--max-parents=0', head).splitlines()}
    save('snapshot.json', snapshot)
head = snapshot['head']
# Use snapshot mailmap, not a potentially changed working tree or user config.
mailmap = git('ls-tree', '--name-only', head, '.mailmap')
mapped_args = ['-c', 'mailmap.file=/dev/null', '-c', f'mailmap.blob={head}:.mailmap'] if mailmap else ['-c', 'mailmap.file=/dev/null', '-c', 'mailmap.blob=']
if mailmap:
    (OUT / 'snapshot.mailmap').write_text(git('show', f'{head}:.mailmap') + '\n')
raw = git(*mapped_args, 'log', head, '--format=%H%x00%P%x00%an%x00%ae%x00%aN%x00%aE%x00%cn%x00%ce%x00%cN%x00%cE%x00%at%x00%ct%x00%s')
fields = ['hash','parents','author_name_raw','author_email_raw','author_name','author_email','committer_name_raw','committer_email_raw','committer_name','committer_email','author_epoch','committer_epoch','subject']
rows = [dict(zip(fields, line.split('\0'))) for line in raw.splitlines()]
for r in rows:
    r['merge'] = len(r['parents'].split()) > 1
    r['author_utc'] = utc(r['author_epoch']).isoformat()
    r['committer_utc'] = utc(r['committer_epoch']).isoformat()
table('commits.csv', rows, fields + ['merge','author_utc','committer_utc'])
days = collections.Counter(r['committer_utc'][:10] for r in rows)
author_days = collections.Counter(r['author_utc'][:10] for r in rows)
merges = collections.Counter(r['committer_utc'][:10] for r in rows if r['merge'])
start, end = min(days), max(days)
d = dt.date.fromisoformat(start)
daily = []
while d <= dt.date.fromisoformat(end):
    day = d.isoformat()
    daily.append({'date_utc': day, 'commits': days[day], 'merges': merges[day], 'non_merges': days[day]-merges[day], 'by_author_date': author_days[day]})
    d += dt.timedelta(days=1)
table('daily.csv', daily, list(daily[0]))
# Full author-time series can extend beyond committer-time boundaries.
table('author_daily.csv', [{'date_utc': k, 'commits': v} for k,v in sorted(author_days.items())], ['date_utc','commits'])
identities = {}
for role in ['author', 'committer']:
    counts = collections.Counter((r[role+'_name'],r[role+'_email']) for r in rows)
    result = [{'name': n, 'email': e, 'commits': c,
               'explicit_bot_label': '[bot]' in n.lower() or '[bot]' in e.lower()}
              for (n,e),c in counts.most_common()]
    identities[role] = result
    table(role+'s.csv', result, ['name','email','commits','explicit_bot_label'])
direct_total = int(git('rev-list', '--count', head))
direct_merges = int(git('rev-list', '--count', '--min-parents=2', head))
shortlog = git(*mapped_args, 'shortlog', '-sne', head)
shortlog_total = sum(int(line.split()[0]) for line in shortlog.splitlines())
direct_non_merges = int(git('rev-list', '--count', '--no-merges', head))
checks = {'git_total_matches_rows': direct_total == len(rows),
          'git_merge_count_matches_rows': direct_merges == sum(r['merge'] for r in rows),
          'git_non_merge_count_matches_rows': direct_non_merges == sum(not r['merge'] for r in rows),
          'daily_sum_matches': sum(days.values()) == direct_total,
          'author_sum_matches': sum(x['commits'] for x in identities['author']) == direct_total,
          'shortlog_total_matches': shortlog_total == direct_total,
          'shortlog_identity_count_matches': len(shortlog.splitlines()) == len(identities['author'])}
assert all(checks.values()), checks
non_merge_authors = collections.Counter((r['author_name'], r['author_email']) for r in rows if not r['merge'])
non_merge_table = [{'name': n, 'email': e, 'commits': c} for (n,e),c in non_merge_authors.most_common()]
table('authors-non-merge.csv', non_merge_table, ['name','email','commits'])
monthly = collections.Counter(r['committer_utc'][:7] for r in rows)
month_merges = collections.Counter(r['committer_utc'][:7] for r in rows if r['merge'])
table('monthly.csv', [{'month_utc': m, 'commits': c, 'merges': month_merges[m], 'non_merges': c-month_merges[m]} for m,c in sorted(monthly.items())], ['month_utc','commits','merges','non_merges'])
by_email = collections.defaultdict(collections.Counter)
by_name = collections.defaultdict(collections.Counter)
for r in rows:
    by_email[r['author_email']][r['author_name']] += 1
    by_name[r['author_name']][r['author_email']] += 1
save('identity-candidates.json', {
    'policy': 'Candidates only: no automatic identity merge; shared email can also reflect misconfiguration.',
    'same_email_multiple_names': {k: dict(v) for k,v in by_email.items() if len(v)>1},
    'same_name_multiple_emails': {k: dict(v) for k,v in by_name.items() if len(v)>1}})
peak_day = max(days, key=days.get)
peak_rows = sorted([r for r in rows if r['committer_utc'][:10] == peak_day], key=lambda r:(int(r['committer_epoch']),r['hash']))
table('peak-day-commits.csv', peak_rows, fields + ['merge','author_utc','committer_utc'])
case_rows = [min(rows, key=lambda r:int(r['committer_epoch'])), max(rows, key=lambda r:int(r['committer_epoch']))]
case_rows += [next(r for r in peak_rows if r['merge']), next(r for r in peak_rows if not r['merge'])]
case_rows += [r for r in rows if (r['author_name'],r['author_email']) in {
    ('pku-xht','53024+tianyicui@users.noreply.github.com'),
    ('Tianyi Cui','276526105+imccyu@users.noreply.github.com')}]
case_output = []
for r in case_rows:
    case_output.append(git('show', '--format=fuller', '--stat', '--no-renames', r['hash']))
(OUT / 'q1-case-details.txt').write_text('\n\n'.join(case_output) + '\n')
summary = {'snapshot': snapshot, 'total_commits': direct_total, 'merge_commits': direct_merges,
           'non_merge_commits': direct_total-direct_merges,
           'earliest_committer': min(rows, key=lambda r:int(r['committer_epoch'])),
           'latest_committer': max(rows, key=lambda r:int(r['committer_epoch'])),
           'elapsed_days': (max(int(r['committer_epoch']) for r in rows)-min(int(r['committer_epoch']) for r in rows))/86400,
           'calendar_days_inclusive': len(daily), 'active_days': len(days),
           'peak_days': sorted(daily, key=lambda x: (-x['commits'], x['date_utc']))[:10],
           'author_identities': len(identities['author']), 'committer_identities': len(identities['committer']),
           'single_commit_author_identities': sum(x['commits']==1 for x in identities['author']),
           'top_authors': identities['author'][:10], 'top_committers': identities['committer'][:10],
           'author_committer_date_mismatch': sum(r['author_utc'][:10]!=r['committer_utc'][:10] for r in rows),
           'snapshot_mailmap_present': bool(mailmap), 'checks': checks}
summary.update({
    'zero_commit_dates': [r['date_utc'] for r in daily if not r['commits']],
    'mean_commits_per_calendar_day': direct_total/len(daily),
    'top1_author_share_pct': identities['author'][0]['commits']/direct_total*100,
    'top5_author_share_pct': sum(r['commits'] for r in identities['author'][:5])/direct_total*100,
    'top10_author_share_pct': sum(r['commits'] for r in identities['author'][:10])/direct_total*100,
    'top5_non_merge_author_share_pct': sum(r['commits'] for r in non_merge_table[:5])/direct_non_merges*100,
    'unique_author_emails': len(by_email), 'unique_author_names': len(by_name),
    'explicit_bot_authors': [r for r in identities['author'] if r['explicit_bot_label']],
    'author_identities_at_most_5_commits': sum(r['commits']<=5 for r in identities['author']),
    'peak_by_author_date': author_days.most_common(1),
    'case_hashes': [r['hash'] for r in case_rows]})
save('q1-summary.json', summary)
save('commands-q1.json', commands)
# A static SVG with daily bars and explicit zero-activity days.
width, height = 1100, 360
plot_w, plot_h = 980, 250
step = plot_w / len(daily)
maximum = max(days.values())
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
       '<rect width="100%" height="100%" fill="white"/>',
       f'<text x="60" y="25" font-size="16">Daily commits (UTC committer date), snapshot {head[:12]}</text>']
for tick in range(5):
    y = 300-tick*plot_h/4
    svg += [f'<path d="M60 {y} H1040" stroke="#ddd"/>', f'<text x="5" y="{y+4}" font-size="12">{maximum*tick/4:.0f}</text>']
for i, r in enumerate(daily):
    h = r['commits']/maximum*plot_h
    svg.append(f'<rect x="{60+i*step}" y="{300-h}" width="{max(.2,step*.85)}" height="{h}" fill="#2563eb"><title>{r["date_utc"]}: {r["commits"]}</title></rect>')
svg += [f'<text x="60" y="330" font-size="13">{start}</text>', f'<text x="950" y="330" font-size="13">{end}</text>', '</svg>']
(OUT / 'daily-commits.svg').write_text('\n'.join(svg))
print(json.dumps(summary, ensure_ascii=False, indent=2))
