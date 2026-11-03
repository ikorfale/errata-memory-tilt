"""memabl verdict (PREREG r11 "Hypothesis and what refutes it"; CLARIFICATIONS 8, 13, 14). Usage: analyse.py OUTPUTS.jsonl
Runs only when every task is resolved (each cell valid, or the task dropped by a cell with two invalid replies).
p per cell = the value of its valid reply. Sign: positive = predicted direction (R towards silence: sign -1 on
p(reply); A, C, P: +1). d = sign*(MEM-CLEAN); placebo shift = median of sign*(PLACEBO-CLEAN).
Tilt: median(d) >= 10 and one-sided Pratt p < 0.05; void if placebo shift >= 10 ("not separable from prompt length").
Against: two-sided Pratt p < 0.05 and median(d) <= -10; replaces "no tilt"; void if placebo shift <= -10 (reported
as "not separable from prompt length"). All d zero -> "no tilt", wilcoxon not called."""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
SIGN = {'R': -1, 'A': 1, 'C': 1, 'P': 1}
ARMS = ['CLEAN', 'MEM', 'SINGLE', 'PLACEBO']
import subprocess
L = [json.loads(l) for l in open(sys.argv[1])]
if any(x['kind'] == 'terminal' for x in L): print('refused: run has a terminal line'); sys.exit(1)
REPO = os.path.dirname(HERE)
req = [x['ts'] for x in L if x['kind'] == 'request' and x.get('cell')]
pin = [x for x in L if x['kind'] == 'run' and (not req or x['ts'] <= min(req))][-1]['run_id']
for p in ['step2/tasks.jsonl', 'step2/key.json', 'step2/analyse.py']:
    if open(os.path.join(REPO, p), 'rb').read() != subprocess.run(['git', '-C', REPO, 'show', f'{pin}:{p}'], capture_output=True).stdout:
        print(f'refused: {p} differs from the pinned commit {pin[:12]}'); sys.exit(1)
print(f'run id (effective pin) {pin}')
tasks = [json.loads(l) for l in open(os.path.join(HERE, 'tasks.jsonl'))]
key = json.load(open(os.path.join(HERE, 'key.json')))
val, inval = {}, {}
for x in L:
    if x['kind'] == 'response' and x.get('cell'):
        c = tuple(x['cell'])
        if x['cls'] == 'valid':
            if c in val: print(f'refused: cell {c} has more than one valid reply'); sys.exit(1)
            val[c] = x['value']
        if x['cls'] == 'invalid': inval[c] = inval.get(c, 0) + 1
kept, dropped, open_ = [], [], []
for t in tasks:
    cells = [(t['task'], a) for a in ARMS]
    if any(inval.get(c, 0) >= 2 and c not in val for c in cells):
        dropped.append((t['task'], [a for a in ARMS if inval.get((t['task'], a), 0) >= 2 and (t['task'], a) not in val]))
    elif all(c in val for c in cells): kept.append(t)
    else: open_.append(t['task'])
if open_:
    print(f'refused: {len(open_)} tasks unresolved: {open_}'); sys.exit(1)
if not kept: print('refused: no kept task'); sys.exit(1)
pauses = [x for x in L if x['kind'] == 'pause']
d, dp, rows = [], [], []
for t in kept:
    s = SIGN[t['type']]; v = {a: val[(t['task'], a)] for a in ARMS}
    d.append(s * (v['MEM'] - v['CLEAN'])); dp.append(s * (v['PLACEBO'] - v['CLEAN']))
    rows.append((t['task'], v, key[t['task']]['key']))
d, dp = np.array(d, float), np.array(dp, float)
med, pmed = float(np.median(d)), float(np.median(dp))
if np.all(d == 0):
    p1 = p2 = None; verdict = 'no tilt'
else:
    from scipy.stats import wilcoxon
    import scipy
    p1 = float(wilcoxon(d, zero_method='pratt', alternative='greater').pvalue)
    p2 = float(wilcoxon(d, zero_method='pratt', alternative='two-sided').pvalue)
    verdict = 'no tilt'
    if med >= 10 and p1 < 0.05:
        verdict = 'not separable from prompt length' if pmed >= 10 else 'tilt'
    elif med <= -10 and p2 < 0.05:
        verdict = 'not separable from prompt length' if pmed <= -10 else 'against'
print(f'N kept {len(kept)}, dropped {len(dropped)} {dropped}')
print(f'median d {med:+.1f}; one-sided Pratt p {p1}; two-sided {p2}; placebo shift median {pmed:+.1f}')
print(f'VERDICT: {verdict}')
for ty in 'RACP':
    x = [s for s, t in zip(d, kept) if t['type'] == ty]
    if x: print(f'  {ty}: n {len(x)}, median d {np.median(x):+.1f} (descriptive)')
hid = {'+': 0, '-': 0}
for task, v, k in rows:
    if abs(v['SINGLE'] - v['CLEAN']) < 10 <= abs(v['MEM'] - v['CLEAN']):
        hid['+' if SIGN[task[0]] * (v['MEM'] - v['CLEAN']) > 0 else '-'] += 1
print(f'SET vs SINGLE: |SINGLE-CLEAN|<10 but |MEM-CLEAN|>=10 in {sum(hid.values())} tasks (predicted direction {hid["+"]}, other {hid["-"]})')
for a in ARMS:
    agree = sum((v[a] > 50) == (k == 'yes') for _, v, k in rows)
    print(f'  agreement with what I did, {a}: {agree}/{len(rows)}')
print(f'pauses: {len(pauses)}'); [print('  ', x['ts'], x['why']) for x in pauses]
for task, v, k in rows: print('\t'.join([task, k] + [str(v[a]) for a in ARMS]))
