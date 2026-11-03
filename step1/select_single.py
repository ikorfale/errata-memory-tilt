#!/usr/bin/env python3
"""memory-tilt step 1 (PREREG r11): per candidate, the memory-git commit at its decision time and the SINGLE note.
Decision time: R/A/C = time of the post or message; P = due - 24 h. Commit = last memory-git commit at or before it.
SINGLE = the note file of the first MEMORY.md index line (file order, at that commit) that mentions the counterparty
handle; else the first index line matching the type keyword (R: thread|reply|silence, A: help|request|take work,
C: correct|errata, P: promise|claim|due); else self.md. Output: single.jsonl."""
import json, re, subprocess, datetime as dt, os, bisect
D = os.path.dirname(os.path.abspath(__file__))
M = os.path.expanduser('~/.claude/projects/-home-board-work/memory')
KW = {'R': r'thread|reply|silence', 'A': r'help|request|take work', 'C': r'correct|errata', 'P': r'promise|claim|due'}
log = subprocess.run(['git', '-C', M, 'log', '--format=%H %cI', '--reverse'], capture_output=True, text=True).stdout.split('\n')
commits = [(dt.datetime.fromisoformat(l.split()[1]).timestamp(), l.split()[0]) for l in log if l.strip()]
times = [c[0] for c in commits]
cache = {}
def index(h):
    if h not in cache:
        txt = subprocess.run(['git', '-C', M, 'show', f'{h}:MEMORY.md'], capture_output=True, text=True).stdout
        cache[h] = [(l, m.group(1)) for l in txt.splitlines() for m in [re.search(r'\]\(([^)]+\.md)\)', l)] if m]
    return cache[h]
def ts(s):
    s = s.replace('Z', '+00:00')
    return dt.datetime.fromisoformat(s if 'T' in s and len(s) > 16 else s).timestamp()
out = []
for l in open(f'{D}/candidates.jsonl'):
    c = json.loads(l)
    t = dt.datetime.strptime(c['t'][:16], '%Y-%m-%dT%H:%M').replace(tzinfo=dt.timezone.utc).timestamp()
    if c['type'] == 'P': t -= 86400
    k = bisect.bisect_right(times, t) - 1
    h = commits[k][1]
    idx = index(h)
    who = (c.get('who') or '').strip()
    pick, rule = None, None
    if who and c['type'] != 'P':
        pick = next((f for line, f in idx if who.lower() in line.lower()), None); rule = 'handle' if pick else None
    if not pick:
        pick = next((f for line, f in idx if re.search(KW[c['type']], line, re.I)), None); rule = 'keyword' if pick else None
    if not pick: pick, rule = 'self.md', 'fallback'
    out.append({'type': c['type'], 'id': c['id'], 'decision_time': dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime('%Y-%m-%dT%H:%MZ'),
                'commit': h, 'single': pick, 'rule': rule})
with open(f'{D}/single.jsonl', 'w') as f:
    for r in out: f.write(json.dumps(r) + '\n')
import collections
print(len(out), collections.Counter((r['type'], r['rule']) for r in out))
