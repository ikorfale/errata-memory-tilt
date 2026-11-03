#!/usr/bin/env python3
"""memory-tilt step 1: due-date history of plan tasks. plan.json keeps only the current due, so the history is rebuilt
from my session transcripts (~/.claude/projects/-home-board-work/*.jsonl): every `tools/plan add ... --due X` (matched
to its task by exact title) and every `tools/plan due-set ID X`, with the transcript timestamp of the call. Limits,
stated: a due changed by any other route (direct edit, a script) is invisible; an add whose title was later edited does
not match (task then starts from its first due-set or its current due). Output: due_history.json
{task_id: [[time_set_utc, due_utc, how], ...]} in time order, ending with the current plan.json due."""
import json, glob, re, datetime as dt, os
UTC = dt.timezone.utc
def norm(s):
    s = s.strip().strip('"\';').rstrip('Z')
    try: t = dt.datetime.fromisoformat(s if 'T' in s else s + 'T23:59')
    except ValueError: return None
    return (t if t.tzinfo else t.replace(tzinfo=UTC)).astimezone(UTC).strftime('%Y-%m-%dT%H:%MZ')
plan = {t['id']: t for t in json.load(open(os.path.expanduser('~/work/plan/plan.json')))['tasks']}
bytitle = {t['title'].strip(): i for i, t in plan.items()}
ev = {}
for f in sorted(glob.glob(os.path.expanduser('~/.claude/projects/-home-board-work/*.jsonl'))):
    for l in open(f, errors='ignore'):
        if 'plan add' not in l and 'due-set' not in l: continue
        try: d = json.loads(l)
        except ValueError: continue
        c = d.get('message', {}).get('content')
        if d.get('type') != 'assistant' or not isinstance(c, list): continue
        ts = (d.get('timestamp') or '')[:16] + 'Z'
        for u in c:
            if u.get('type') != 'tool_use': continue
            cmd = u.get('input', {}).get('command', '') or ''
            for m in re.finditer(r'plan due-set (\d+) (\S+)', cmd):
                du = norm(m.group(2))
                if du: ev.setdefault(int(m.group(1)), set()).add((ts, du, 'due-set'))
            for m in re.finditer(r'plan add \S+ ("(?:[^"\\]|\\.)*"|\'[^\']*\')([^\n;&|]*)', cmd):
                i = bytitle.get(m.group(1)[1:-1].strip()); du = re.search(r'--due[ =](\S+)', m.group(2))
                if i and du and norm(du.group(1)): ev.setdefault(i, set()).add((ts, norm(du.group(1)), 'add'))
out = {}
for i, t in plan.items():
    seq = sorted(ev.get(i, set()))
    # keep the first add only (a re-run of the same add command does not create a second task)
    adds = [e for e in seq if e[2] == 'add']
    seq = [e for e in seq if e[2] != 'add' or e == (adds[0] if adds else None)]
    if t.get('due') and (not seq or seq[-1][1] != t['due']): seq.append(['current', t['due'], 'plan.json'])
    out[str(i)] = [list(e) for e in seq]
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'due_history.json'), 'w'), indent=0)
n = sum(1 for v in out.values() if len({e[1] for e in v}) > 1)
print('tasks', len(out), 'with >1 due value', n)
