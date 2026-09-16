#!/usr/bin/env python3
"""Q2: separate AI process evidence from coding-product terminology."""
import collections
import csv
import datetime as dt
import json
from pathlib import Path
import random
import re
import subprocess

BASE = Path(__file__).resolve().parents[1]
OUT = BASE/'evidence/q2'
OUT.mkdir(exist_ok=True)
HEAD = json.loads((BASE/'evidence/snapshot.json').read_text())['head']
COMMANDS=[]
def git(*args):
    p=subprocess.run(['git','-C',str(BASE/'deepseek-harness'),*args],check=True,capture_output=True,text=True)
    COMMANDS.append({'args':list(args),'exit_code':p.returncode})
    return p.stdout
def save(name,data):
    (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def table(name,rows,fields):
    with (OUT/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n'); w.writeheader(); w.writerows(rows)
raw=git('log',HEAD,'--format=%H%x00%P%x00%ct%x00%B%x00').split('\0')
records=[]
for i in range(0,len(raw)-1,4):
    sha=raw[i].strip()
    if not sha: continue
    message=raw[i+3]
    records.append({'hash':sha,'parents':raw[i+1].split(),'month':dt.datetime.fromtimestamp(int(raw[i+2]),dt.timezone.utc).strftime('%Y-%m'),
                    'subject':message.splitlines()[0],'message':message})
by_sha={r['hash']:r for r in records}
save('messages.json',records)
non=[r for r in records if len(r['parents'])<2]
assert len(records)==int(git('rev-list','--count',HEAD))
assert len(non)==int(git('rev-list','--count','--no-merges',HEAD))
review_re=re.compile(r'(?:codex|claude)(?:[^\n]{0,65})(?:review|finding)|(?:review|finding)(?:[^\n]{0,40})(?:codex|claude)',re.I)
# Manual reading of all candidate lines: product/provider review is ambiguous.
ambiguous={'d495089ff7a0','e2315e3b149f','7d30a3961963','62da706b64b1','46db6088436d','36b562e4e95d','8e8c791eb0bd','84f3019310c6','39b3db4b9cc3'}
reviews=[]
for r in records:
    if not review_re.search(r['message']):continue
    category='explicit_ai_review_reference'
    reason='提交信息明确将评审或发现归于 Codex/Claude；仅证明记录了 AI 评审参与，不判为 AI 编码'
    if len(r['parents'])>1:
        category='merge_context'; reason='分支合并命名或合并上下文，排除独立评审计数'
    elif r['hash'][:12] in ambiguous:
        category='product_or_ambiguous'; reason='评审对象或产品功能涉及 Codex/Claude，不能确认评审者是 AI'
    reviews.append({'hash':r['hash'],'category':category,'reason':reason,'matched_lines':' | '.join(x for x in r['message'].splitlines() if review_re.search(x))})
table('review-candidates.csv',reviews,['hash','category','reason','matched_lines'])
explicit={r['hash'] for r in reviews if r['category']=='explicit_ai_review_reference'}
markers=[]
for r in records:
    lines=[x for x in r['message'].splitlines() if re.match(r'\s*co-authored-by:',x,re.I)]
    if lines: markers.append({'hash':r['hash'],'trailers':' | '.join(lines)})
table('coauthor-trailers.csv',markers,['hash','trailers'])
signature=re.compile(r'^\s*(?:co-authored-by:.*(?:\bClaude\b|\bCodex\b|\bChatGPT\b|\bCopilot\b)|(?:generated|written|implemented) (?:by|with) (?:an? )?(?:Claude|Codex|ChatGPT|Copilot)\b)',re.I|re.M)
signatures=[r['hash'] for r in records if signature.search(r['message'])]
pr_merges=[r for r in records if len(r['parents'])>1 and re.match(r'^Merge pull request #\d+ from ',r['subject'])]
codex_prs=[r for r in pr_merges if re.search(r' from [^\s]+/codex/',r['subject'],re.I)]
def ancestors(sha):
    seen=set(); stack=[sha]
    while stack:
        node=stack.pop()
        if node in seen:continue
        seen.add(node); stack.extend(by_sha[node]['parents'])
    return seen
associated=set()
branch_rows=[]
for r in codex_prs:
    introduced=ancestors(r['parents'][1])-ancestors(r['parents'][0])
    ids=sorted(x for x in introduced if len(by_sha[x]['parents'])<2)
    associated.update(ids)
    branch_rows.append({'merge_hash':r['hash'],'subject':r['subject'],'non_merge_count':len(ids),'non_merge_hashes':' '.join(ids)})
table('codex-pr-association.csv',branch_rows,['merge_hash','subject','non_merge_count','non_merge_hashes'])
table('codex-associated-commits.csv',[{'hash':h,'subject':by_sha[h]['subject']} for h in sorted(associated)],['hash','subject'])
if codex_prs:
    check=codex_prs[0]
    actual=set(git('rev-list','--no-merges',check['parents'][1],'^'+check['parents'][0]).splitlines())
    assert actual==set(branch_rows[0]['non_merge_hashes'].split())
# 4 months × feat/fix/other; fixed hash order and seed, at most five per stratum.
rng=random.Random(20260916)
strata=collections.defaultdict(list)
for r in non:
    match=re.match(r'^(feat|fix)(?:\([^)]*\))?!?:',r['subject'])
    kind=match.group(1) if match else 'other'
    strata[(r['month'],kind)].append(r)
samples=[]; excerpts=[]
for (month,kind),rs in sorted(strata.items()):
    selected=sorted(rng.sample(sorted(rs,key=lambda r:r['hash']),min(5,len(rs))),key=lambda r:r['hash'])
    for r in selected:
        diff=git('show','--format=','--no-ext-diff','--no-textconv','--no-renames','--unified=2',r['hash'])
        lines=diff.splitlines()
        excerpt='\n'.join(lines[:90])
        sample={'hash':r['hash'],'month':month,'type':kind,'stratum_population':len(rs),'stratum_sample':len(selected),
                'subject':r['subject'],'explicit_review':r['hash'] in explicit,'codex_branch_association':r['hash'] in associated,
                'diff_lines':len(lines),'excerpt_lines':min(90,len(lines))}
        samples.append(sample)
        excerpts.append(f'=== {month}/{kind} {r["hash"]} ===\n{r["message"]}\n[diff excerpt: first {min(90,len(lines))} of {len(lines)} lines]\n{excerpt}\n')
table('stratified-samples.csv',samples,list(samples[0]))
(OUT/'sample-diff-excerpts.txt').write_text('\n'.join(excerpts))
audit=[]
for r in samples:
    note='提交说明及 diff 片段呈现实现、测试或文档改动，未提供可验证的编码主体归属'
    if r['explicit_review']:
        note='明确提及 Codex 评审；改动涉及开发不变量，但不能据此确定实现代码由 AI 编写'
    elif r['hash'].startswith('9e91e206d4ad'):
        note='Codex 是被重构的产品后端；名称出现不能证明本提交作者使用了 Codex'
    elif r['subject'].startswith(('docs:', 'chore(docs):')):
        note='目录、图或说明更新也可能由确定性脚本生成；不视为生成式 AI 编码证据'
    audit.append({'hash':r['hash'],'coding_attribution':'无法从已审阅信息确定','review_note':note,
                  'inspection_scope':'提交说明及保存的 diff 片段；非完整逐行审计'})
table('sample-audit.csv',audit,['hash','coding_attribution','review_note','inspection_scope'])
docs=['.agents/notes/implemented/process/2026-06-11-quality-gates.md','.agents/notes/implemented/process/2026-07-19-web-styling-system.md']
doc_evidence=[]
for path in docs:
    doc_evidence.append(f'=== {HEAD}:{path} ===\n'+git('show',f'{HEAD}:{path}'))
    doc_evidence.append('Recent history:\n'+git('log',HEAD,'-3','--format=%H %s','--',path))
(OUT/'project-statements.txt').write_text('\n'.join(doc_evidence))
case_prefixes=['43d81b67cef2','b46dcb16cbb5','ac36c6b97539','ace0c4619e','c7e29f4b68']
cases=[]
for prefix in case_prefixes:
    r=next(r for r in records if r['hash'].startswith(prefix))
    cases.append(git('show','--format=fuller','--stat','--stat-count=12',r['hash']))
(OUT/'targeted-cases.txt').write_text('\n'.join(cases))
counts=dict(total_commits=len(records),non_merge_commits=len(non),merge_commits=len(records)-len(non),
            known_ai_signature_commits=len(signatures),coauthor_commits=len(markers),
            review_candidates=len(reviews),review_classification=dict(collections.Counter(r['category'] for r in reviews)),
            explicit_review_nonmerge=len(explicit),explicit_review_pct=len(explicit)/len(non)*100,
            named_pr_merges=len(pr_merges),codex_named_pr_merges=len(codex_prs),
            codex_branch_associated_nonmerge=len(associated),codex_branch_associated_pct=len(associated)/len(non)*100,
            keyword_commits={word:sum(bool(re.search(word,r['message'],re.I)) for r in records) for word in ['codex','claude','deepseek']},
            sample_count=len(samples),sample_strata=len(strata),sample_review_count=sum(r['explicit_review'] for r in samples),
            sample_branch_count=sum(r['codex_branch_association'] for r in samples))
save('summary.json',{'snapshot':HEAD,'seed':20260916,'counts':counts,'signature_pattern':signature.pattern,'review_pattern':review_re.pattern,
                     'checks':{'git_total':True,'git_nonmerge':True,'parent_difference_crosscheck':bool(codex_prs),
                               'samples_unique':len({r['hash'] for r in samples})==len(samples)}})
save('commands.json',COMMANDS)
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1060" height="300" viewBox="0 0 1060 300">',
     '<rect width="1060" height="300" fill="white"/>',
     '<style>text{font-family:sans-serif;fill:#172033;font-size:14px}</style>',
     '<text x="25" y="30" style="font-size:21px">Q2: visible process traces, NOT AI-generated code share</text>',
     f'<text x="25" y="55">Snapshot {HEAD[:12]} | denominator: {len(non):,} non-merge commits</text>']
for label,n,y in [('Explicit AI review references',len(explicit),105),('Codex-named PR branch association',len(associated),165)]:
    w=n/len(non)*600
    svg.extend([f'<text x="25" y="{y+18}">{label}</text>',f'<rect x="330" y="{y}" width="600" height="28" fill="#eef2f7"/>',
                f'<rect x="330" y="{y}" width="{w}" height="28" fill="#2563eb"/>',
                f'<text x="340" y="{y+48}">{n:,} / {len(non):,} = {n/len(non)*100:.2f}%</text>'])
svg.extend(['<text x="330" y="91">0%</text>','<text x="900" y="91">100%</text>',
            '<text x="25" y="255">Measures may overlap. The remainder is unclassified, not confirmed human coding.</text>',
            '<text x="25" y="278">Review evidence and branch naming cannot identify the author of each line.</text>','</svg>'])
(OUT/'visible-traces.svg').write_text('\n'.join(svg))
print(json.dumps(counts,ensure_ascii=False,indent=2))
