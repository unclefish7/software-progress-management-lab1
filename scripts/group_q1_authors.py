#!/usr/bin/env python3
"""Reproducible, explicitly heuristic contributor grouping for Lab1 Q1."""
import collections
import csv
import html
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / 'evidence'
# Exact author names, not transitive email unions. Preserve ambiguous pairs.
GROUPS = [
    ('creatixchu', ['creatixchu', 'CreatixChu'], '用户名仅大小写不同', '较高'),
    ('Turtle', ['Turtle', 'turtle1999', 'Turtle 2099'], '共享邮箱及一致的 turtle1999 账号线索；2099/+1 变体为推测', '中等'),
    ('Hypatia May', ['Hypatia May', 'hypatiamay'], '共享邮箱，名称为大小写及空格变体', '较高'),
    ('kingwl', ['kingwl', 'Wenlu Wang'], '共享 kingwenlu 邮箱', '较高'),
    ('ZiyaZhang', ['ZiyaZhang', 'Ziya'], '两组邮箱均交叉出现这两个署名', '较高'),
    ('Yudong Han', ['Yudong Han', 'Yudong', 'yudshj', 'HYD@OVERTON'], '共享 maghsk2017 邮箱', '较高'),
    ('ihsiang', ['ihsiang', 'yixiangihsiang'], '共享 ihsiang 邮箱', '较高'),
    ('Ruilin Geng', ['Ruilin Geng', 'gengruilin'], '共享 grllll 邮箱且拼音名称一致', '较高'),
    ('Jiaying Ding', ['Jiaying Ding', 'Ag'], '共享 silver.ding 邮箱', '较高'),
    ('NI0317', ['NI0317', 'Terra', 'Ni Shentu'], '相同 GitHub 数字账号 87308515，邮箱含 NI0317', '较高'),
    ('mektpoy', ['mektpoy', 'Xu Hanxiang'], 'GitHub 邮箱明确含 mektpoy 用户名', '较高'),
    ('lintianle', ['lintianle', 'TianleLin'], '拼音姓名顺序对应，但邮箱不同，属于推测', '中等'),
    ('Dudu-0223', ['Dudu-0223', 'Dudu'], '昵称主体相同，邮箱不同，属于推测', '中等'),
]
lookup = {alias:(canonical, reason, confidence) for canonical, aliases, reason, confidence in GROUPS for alias in aliases}
raw = list(csv.DictReader((OUT/'authors.csv').open()))
commits = list(csv.DictReader((OUT/'commits.csv').open()))
summary = json.loads((OUT/'q1-summary.json').read_text())
mapping = []
by_key = {}
for r in raw:
    name, email = r['name'], r['email']
    group, reason, confidence = lookup.get(name, (name, '相同署名的多邮箱记录按同一人估计；单一身份保持原样', '估计'))
    kind = 'bot' if r['explicit_bot_label']=='True' else ('unresolved' if name=='Ubuntu' else 'person_estimate')
    if (name,email) in {('pku-xht','53024+tianyicui@users.noreply.github.com'), ('Tianyi Cui','276526105+imccyu@users.noreply.github.com')}:
        reason = '署名与其他核心成员邮箱交叉：暂按作者署名归属，不因此合并两人'
        confidence = '中等'
    row = dict(name=name,email=email,group=group,kind=kind,commits=int(r['commits']),reason=reason,confidence=confidence)
    mapping.append(row)
    by_key[(name,email)] = row

def write_csv(name, rows):
    with (OUT/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)

write_csv('author-group-mapping.csv',mapping)
counts = collections.defaultdict(lambda:dict(commits=0,non_merges=0,merges=0,identities=0))
for r in mapping:
    counts[(r['group'],r['kind'])]['identities'] += 1
for r in commits:
    m=by_key[(r['author_name'],r['author_email'])]
    c=counts[(m['group'],m['kind'])]
    c['commits']+=1
    c['merges' if r['merge']=='True' else 'non_merges']+=1
people=sorted([dict(person=n,**c) for (n,k),c in counts.items() if k=='person_estimate'],key=lambda r:(-r['commits'],r['person']))
excluded=[dict(group=n,kind=k,**c) for (n,k),c in counts.items() if k!='person_estimate']
total=sum(r['commits'] for r in people)
non_total=sum(r['non_merges'] for r in people)
running=0
for i,r in enumerate(people):
    running+=r['commits']
    r.update(rank=i+1,share_pct=r['commits']/total*100,cumulative_pct=running/total*100,
             gap_to_next=r['commits']-people[i+1]['commits'] if i+1<len(people) else '')
write_csv('contributors-grouped.csv',people)
write_csv('contributors-excluded.csv',excluded)
bins=[]
for label,low,high in [('1–5',1,5),('6–50',6,50),('51–200',51,200),('201–1000',201,1000),('1001+',1001,10**9)]:
    selected=[r for r in people if low<=r['commits']<=high]
    bins.append(dict(commit_range=label,people=len(selected),commits=sum(r['commits'] for r in selected)))
write_csv('contributor-distribution.csv',bins)
checks={'all_identities_mapped_once':len(by_key)==len(raw),
        'all_commits_preserved':total+sum(r['commits'] for r in excluded)==summary['total_commits'],
        'merge_counts_preserved':sum(c['merges'] for c in counts.values())==summary['merge_commits'],
        'non_merge_counts_preserved':sum(c['non_merges'] for c in counts.values())==summary['non_merge_commits'],
        'bins_cover_people':sum(r['people'] for r in bins)==len(people),
        'bins_cover_commits':sum(r['commits'] for r in bins)==total}
assert all(checks.values()),checks
result=dict(snapshot=summary['snapshot']['head'],estimated_people=len(people),person_commits=total,
            excluded=excluded,top1_share_pct=people[0]['share_pct'],
            top5_share_pct=sum(r['commits'] for r in people[:5])/total*100,
            top10_share_pct=sum(r['commits'] for r in people[:10])/total*100,
            top5_non_merge_share_pct=sum(sorted([r['non_merges'] for r in people],reverse=True)[:5])/non_total*100,
            people_to_reach_80pct=next(r['rank'] for r in people if r['cumulative_pct']>=80),
            checks=checks)
(OUT/'q1-grouped-summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')

# Self-contained SVG: no dependencies or download required.
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1080" viewBox="0 0 1200 1080">',
     '<rect width="1200" height="1080" fill="white"/>',
     '<style>text{font-family:sans-serif;fill:#172033;font-size:14px}.small{font-size:12px}.title{font-size:21px;font-weight:bold}</style>']
def text(x,y,s,cls='',anchor='start'):
    svg.append(f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}">{html.escape(str(s))}</text>')
text(35,35,'Estimated contributor concentration · Q1','title')
text(35,59,f'Snapshot {result["snapshot"][:12]} | {len(people)} estimated people | {total:,} commits | bot/unresolved excluded','small')
text(35,88,'Top 15 contributors · linear scale · full ranking and alias mapping in CSV')
for tick in range(0,7000,1000):
    x=180+tick/7000*800
    svg.append(f'<path d="M{x} 120 V645" stroke="#e5e7eb"/>')
    text(x,113,str(tick),'small','middle')
for i,r in enumerate(people[:15]):
    y=130+i*34
    text(165,y+16,r['person'],anchor='end')
    a=r['non_merges']/7000*800; b=r['merges']/7000*800
    svg.append(f'<rect x="180" y="{y}" width="{a}" height="23" fill="#2563eb"/><rect x="{180+a}" y="{y}" width="{b}" height="23" fill="#93c5fd"/>')
    text(190+a+b,y+16,f'{r["commits"]:,} ({r["share_pct"]:.1f}%)','small')
text(180,668,'Blue: non-merge commits   Light blue: merge commits','small')
text(35,715,'Cumulative share by contributor rank')
for tick in [0,20,40,60,80,100]:
    y=985-tick*2
    svg.append(f'<path d="M75 {y} H600" stroke="#e5e7eb"/>')
    text(65,y+4,f'{tick}%','small','end')
points=['75,985']+[f'{75+r["rank"]/len(people)*525},{985-r["cumulative_pct"]*2}' for r in people]
svg.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="#2563eb" stroke-width="3"/>')
for rank in [1,5,10,len(people)]:
    text(75+rank/len(people)*525,1007,rank,'small','middle')
text(75,1040,f'Top 5: {result["top5_share_pct"]:.2f}% | Top 10: {result["top10_share_pct"]:.2f}%','small')
text(690,715,'People by commit-count range')
maximum=max(r['people'] for r in bins)
for i,r in enumerate(bins):
    y=765+i*47
    text(775,y+17,r['commit_range'],'small','end')
    w=r['people']/maximum*260
    svg.append(f'<rect x="790" y="{y}" width="{w}" height="25" fill="#14b8a6"/>')
    text(800+w,y+17,r['people'])
text(690,1040,'Counts are estimates; commits do not measure work value.','small')
svg.append('</svg>')
(OUT/'contributor-concentration.svg').write_text('\n'.join(svg))
print(json.dumps(result,ensure_ascii=False,indent=2))
