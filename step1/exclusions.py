#!/usr/bin/env python3
"""memory-tilt step 1 (PREREG r11): exclusion log over the whole pool, one reason per removed item:
(i) not a decision (automated, spam; A rows with no request to me; P recurring slots), (ii) situation text
unrecoverable (empty), (iii) the decision is the cited origin of a note present at its commit time (its id appears in
a memory file at that commit), (iv) P only: revision announced earlier than due - 24 h. Keys are joined here from
R_keys.tsv (scripted), A_keys.tsv, C_keys.tsv, P_keys.tsv (hand). Output: exclusions.tsv, pool.jsonl (kept items with key)."""
import json, csv, subprocess, os, re
D = os.path.dirname(os.path.abspath(__file__))
M = os.path.expanduser('~/.claude/projects/-home-board-work/memory')
rd = lambda f: {r['id']: r for r in csv.DictReader(open(f'{D}/{f}'), delimiter='\t')}
keys = {'R': rd('R_keys.tsv'), 'A': rd('A_keys.tsv'), 'C': rd('C_keys.tsv'), 'P': rd('P_keys.tsv')}
single = {(s['type'], str(s['id'])): s for s in map(json.loads, open(f'{D}/single.jsonl'))}
snap = {}
def memtext(h):
    if h not in snap:
        files = subprocess.run(['git', '-C', M, 'ls-tree', '--name-only', h], capture_output=True, text=True).stdout.split()
        snap[h] = '\n'.join(subprocess.run(['git', '-C', M, 'show', f'{h}:{f}'], capture_output=True, text=True).stdout
                            for f in files if f.endswith('.md'))
    return snap[h]
excl, pool = ['type\tid\treason\tdetail'], []
for l in open(f'{D}/candidates.jsonl'):
    c = json.loads(l); i = str(c['id']); k = keys[c['type']].get(i)
    if k is None: excl.append(f"{c['type']}\t{i}\tmissing-key\tno key row"); continue
    key = k['key']
    reason = None
    if c['type'] == 'A' and key == 'n/a': reason = ('i', k.get('subcase', ''))
    elif c['type'] == 'P' and k.get('exclusion') == 'i': reason = ('i', 'recurring slot')
    elif not (c.get('text') or '').strip(): reason = ('ii', 'empty situation text')
    elif c['type'] == 'P' and k.get('exclusion') == 'iv': reason = ('iv', k.get('evidence', ''))
    else:
        s = single[(c['type'], i)]
        if c['src'] in ('board', 'kept') and re.fullmatch(r'\d{5,6}', i) and re.search(rf'(?<!\d){i}(?!\d)', memtext(s['commit'])):
            reason = ('iii', f"id {i} cited in memory at {s['commit'][:8]}")
    if reason: excl.append(f"{c['type']}\t{i}\t{reason[0]}\t{reason[1]}"); continue
    if key not in ('yes', 'no'): excl.append(f"{c['type']}\t{i}\tunlabelled\t{key}"); continue
    pool.append({**c, 'key': key, 'decision_time': single[(c['type'], i)]['decision_time'],
                 'commit': single[(c['type'], i)]['commit'], 'single': single[(c['type'], i)]['single']})
open(f'{D}/exclusions.tsv', 'w').write('\n'.join(excl) + '\n')
with open(f'{D}/pool.jsonl', 'w') as f:
    for r in pool: f.write(json.dumps(r, ensure_ascii=False) + '\n')
import collections
print('excluded', len(excl) - 1, collections.Counter((e.split('\t')[0], e.split('\t')[2]) for e in excl[1:]))
print('pool', len(pool), collections.Counter((r['type'], r['key']) for r in pool))
