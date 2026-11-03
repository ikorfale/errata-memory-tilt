"""Step 2 draw (PREREG r11 "Frame and draw"; CLARIFICATIONS 7). Input: step1 pool.jsonl (private local copy, pinned by
step1/SHA256-private.txt). Each type's pool is sorted by (decision_time, str(id)); one random.Random(615) is used for the
whole draw, types in the order R, A, C, P, and within a type the 'yes' stratum first, then 'no'. Per type: 5 from each
stratum with rng.sample; a stratum short of 5 is taken whole and the shortfall is filled by rng.sample from the other
stratum's remainder; a type with fewer than 10 items is taken whole. Output draw.json: the drawn ids per type, in the
sorted pool order, with key and decision time, plus shortfalls and N.
Usage: python3 draw.py POOL.jsonl > draw.json"""
import hashlib, json, random, sys

SEED, PER, HALF = 615, 10, 5
path = sys.argv[1]
raw = open(path, 'rb').read()
pool = [json.loads(l) for l in raw.decode().splitlines() if l.strip()]
rng = random.Random(SEED)
out = {'seed': SEED, 'pool_sha256': hashlib.sha256(raw).hexdigest(), 'types': {}, 'shortfalls': []}
for t in 'RACP':
    items = sorted((p for p in pool if p['type'] == t), key=lambda p: (p['decision_time'], str(p['id'])))
    if len(items) < PER:
        pick = items
        out['shortfalls'].append(f'{t}: pool {len(items)} < {PER}, taken whole')
    else:
        yes = [p for p in items if p['key'] == 'yes']; no = [p for p in items if p['key'] == 'no']
        a = yes if len(yes) <= HALF else rng.sample(yes, HALF)
        b = no if len(no) <= HALF else rng.sample(no, HALF)
        if len(a) < HALF:
            rest = [p for p in no if p not in b]; b = b + rng.sample(rest, PER - len(a) - len(b))
            out['shortfalls'].append(f'{t}: yes stratum {len(yes)} < {HALF}, filled from no')
        elif len(b) < HALF:
            rest = [p for p in yes if p not in a]; a = a + rng.sample(rest, PER - len(a) - len(b))
            out['shortfalls'].append(f'{t}: no stratum {len(no)} < {HALF}, filled from yes')
        ids = {str(p['id']) for p in a + b}
        pick = [p for p in items if str(p['id']) in ids]
    out['types'][t] = [{'id': p['id'], 'key': p['key'], 'decision_time': p['decision_time']} for p in pick]
out['N'] = sum(len(v) for v in out['types'].values())
print(json.dumps(out, indent=1, ensure_ascii=False))
