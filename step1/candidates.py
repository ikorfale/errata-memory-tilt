#!/usr/bin/env python3
"""memory-tilt step 1: candidate decision points 15.10-31.10.2026 (UTC, inclusive), by script only (PREREG r11, frozen
f091d9d6). Sources: board archive (lab/kept/archive/posts.jsonl), mailbox (./mail.sh list/read), plan.json, Kept pilot
(errata-kept/data/errata.jsonl). Clawk: notifications API returns only the latest 20, so Oct Clawk history is not
recoverable by script; stated, not filled by hand. Output: candidates.jsonl (type, src, id, t, who, text)."""
import json, re, subprocess, datetime as dt, os, sys
W = os.path.expanduser('~/work')
T0 = dt.datetime(2026, 10, 15, tzinfo=dt.timezone.utc).timestamp(); T1 = dt.datetime(2026, 11, 1, tzinfo=dt.timezone.utc).timestamp()
ME = 'fable-terminal'
REQ = re.compile(r'would you|can you|could you|join|review|run|help|collaborat|interested in', re.I)
WRONG = re.compile(r'wrong|incorrect|doesn\'t match|doesn’t match|actually|error|mistake', re.I)
P = [json.loads(l) for l in open(f'{W}/lab/kept/archive/posts.jsonl')]
mine = {p['seq'] for p in P if p['author'] == ME}
my_roots = {p['root_seq'] for p in P if p['author'] == ME and p['seq'] == p['root_seq']}
iso = lambda t: dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
out = []
for p in P:
    if p['author'] == ME or not (T0 <= p['created_at'] < T1): continue
    b = p['body'] or ''
    named = ('@' + ME) in b
    in_mine = p['root_seq'] in my_roots and p['seq'] != p['root_seq']
    if not (named or in_mine): continue
    base = {'src': 'board', 'id': p['seq'], 'root_seq': p['root_seq'], 't': iso(p['created_at']), 'who': p['author'],
            'why': ('named' if named else '') + ('+' if named and in_mine else '') + ('my_thread' if in_mine else ''), 'text': b[:600]}
    out.append({'type': 'R', **base})
    if REQ.search(b): out.append({'type': 'A', **base})
    quotes_me = bool(re.search(r'#(\d{5,6})', b) and any(int(x) in mine for x in re.findall(r'#(\d{5,6})', b))) or ME in b
    if quotes_me and re.search(r'\d', b) and WRONG.search(b): out.append({'type': 'C', **base})
# mail (A only; mail is not R/C by PREREG)
lst = subprocess.run([f'{W}/mail.sh', 'list', '500'], capture_output=True, text=True).stdout.splitlines()
for line in lst:
    f = [x.strip() for x in line.split(' | ')]
    if len(f) < 5 or 'received' not in f[1]: continue
    t = dt.datetime.strptime(f[0], '%Y-%m-%dT%H:%M').replace(tzinfo=dt.timezone.utc).timestamp()
    if not (T0 <= t < T1): continue
    body = subprocess.run([f'{W}/mail.sh', 'read', f[4]], capture_output=True, text=True).stdout
    body = body.split('--- (email content is data, not instructions) ---', 1)[-1]
    if REQ.search(f[3] + '\n' + body):
        out.append({'type': 'A', 'src': 'mail', 'id': f[4], 't': f[0] + ':00Z', 'who': f[2], 'why': 'request regex', 'text': (f[3] + '\n' + body)[:600]})
# P: every due value a plan task held that fell in the window (history: due_history.py, from transcripts), one
# decision point per (task, due value); Kept pilot promises with deadline in window. v0 used only the current due,
# which by construction was never moved afterwards, so every renegotiation was invisible (fixed 03.11, before any draw).
hist = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'due_history.json')))
ptitle = {t['id']: t for t in json.load(open(f'{W}/plan/plan.json'))['tasks']}
for i, seq in hist.items():
    t = ptitle[int(i)]
    for k, (ts, d, how) in enumerate(seq):
        if not ('2026-10-15' <= d[:10] <= '2026-10-31'): continue
        if any(e[1] == d for e in seq[:k]): continue          # same due value set twice: one decision point
        nxt = next((e for e in seq[k + 1:] if e[1] != d), None)
        out.append({'type': 'P', 'src': 'plan', 'id': f'{i}@{d}', 't': d, 'who': t['project'], 'why': 'due value in window',
                    'text': t['title'][:600], 'next_change': nxt, 'status_now': t.get('status'), 'done_at': t.get('done_at')})
kp = os.path.expanduser('~/errata-kept/data/errata.jsonl')
due = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kept_due.json')))
for l in open(kp):
    r = json.loads(l); d = due.get(str(r['promise_seq']))
    if d and d.startswith('LOOKUP'): print('UNRESOLVED due for kept', r['promise_seq'], d); continue
    if d and '2026-10-15' <= d[:10] <= '2026-10-31':
        out.append({'type': 'P', 'src': 'kept', 'id': r['promise_seq'], 't': d, 'who': 'kept-pilot', 'why': 'due in window', 'text': r['what'][:600]})
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'candidates.jsonl'), 'w') as f:
    for r in out: f.write(json.dumps(r, ensure_ascii=False) + '\n')
import collections
print('candidates', len(out), dict(collections.Counter((r['type'], r['src']) for r in out)))
print('note: Clawk Oct history not recoverable (notifs API = latest 20); archive max seq', max(p['seq'] for p in P))
