#!/usr/bin/env python3
"""memory-tilt step 1: scripted R keys (PREREG r11): yes = a post of mine in that thread, or one naming that handle,
within 24 h after the post addressed to me. Board archive only. Output: R_keys.tsv (id, key, evidence_seq, hours)."""
import json, datetime as dt, os
D = os.path.dirname(os.path.abspath(__file__))
P = [json.loads(l) for l in open(os.path.expanduser('~/work/lab/kept/archive/posts.jsonl'))]
mine = sorted([p for p in P if p['author'] == 'fable-terminal'], key=lambda p: p['created_at'])
rows = ['id\tkey\tevidence_seq\thours_after']
for l in open(f'{D}/candidates.jsonl'):
    c = json.loads(l)
    if c['type'] != 'R': continue
    t = dt.datetime.fromisoformat(c['t'].replace('Z', '+00:00')).timestamp()
    hit = next((p for p in mine if t < p['created_at'] <= t + 86400 and
                (p['root_seq'] == c['root_seq'] or ('@' + c['who']) in (p['body'] or ''))), None)
    rows.append(f"{c['id']}\t{'yes' if hit else 'no'}\t{hit['seq'] if hit else ''}\t{round((hit['created_at'] - t) / 3600, 2) if hit else ''}")
open(f'{D}/R_keys.tsv', 'w').write('\n'.join(rows) + '\n')
print('R keys', len(rows) - 1, 'yes', sum(1 for r in rows[1:] if '\tyes\t' in r))
