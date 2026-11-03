"""Step 2c: tasks.jsonl, one line per drawn task (PREREG r11 "Per-task pinning"). Inputs: draw.json; the private step-1
pool (decision time, memory commit, SINGLE note, candidate text); the board archive (posts since 01.10, full text);
the memory git repository; placebo_pool.txt.
Situation: R/A/C (all 30 drawn are board posts) = the thread of the candidate post (root and replies with created_at <=
the candidate's created_at, in seq order, each as "[author, YYYY-MM-DD HH:MM UTC]" + body), cut to its last 1500
chars. P = the plan task text and its due time ("Your promise (plan task in project <p>): <text>. Due: <due>.").
Memory at the pinned commit (git show of each blob, no working-tree read): MEM block = MEMORY.md, then every other
top-level file of the memory directory in name order (the archive/ subdirectory is not a memory file: unindexed history),
self.md included among them; each as "=== <file name> ===" + content. SINGLE block = the one step-1 note. PLACEBO block
= placebo_pool.txt from offset 0, repeated, cut to the MEM block's character count. mem_sha256 = sha256 over the
MEM block text and single_sha256 over the SINGLE block
(call.py rebuilds both from the commit and compares; note texts are not published here). Usage: build_tasks.py POOL ARCHIVE MEMREPO > tasks.jsonl"""
import hashlib, json, subprocess, sys, datetime as dt
pool_path, arch_path, memrepo = sys.argv[1:4]
D = json.load(open('draw.json'))
POOL = {(p['type'], str(p['id'])): p for p in map(json.loads, open(pool_path))}
ARCH = {}
for l in open(arch_path):
    a = json.loads(l); ARCH[a['seq']] = a
PLACEBO = open('placebo_pool.txt').read()
HDR = {'MEM': 'Your notes, as they stood on that date (your memory files):\n',
       'SINGLE': 'One of your notes, as it stood on that date:\n',
       'PLACEBO': 'Reference text:\n'}

def git(*a):
    return subprocess.run(['git', '-C', memrepo, *a], capture_output=True, text=True, check=True).stdout

def mem_files(commit):
    names = [l.split('\t')[1] for l in git('ls-tree', commit).split('\n') if l and l.split()[1] == 'blob']
    names = ['MEMORY.md'] + sorted(n for n in names if n != 'MEMORY.md')
    return [(n, git('show', f'{commit}:{n}')) for n in names]

def fmt(a):
    t = dt.datetime.fromtimestamp(a['created_at'], dt.timezone.utc).strftime('%Y-%m-%d %H:%M')
    return f"[{a['author']}, {t} UTC]\n{a['body']}\n"

for t in 'RACP':
    for x in D['types'][t]:
        p = POOL[(t, str(x['id']))]
        if t == 'P':
            sit = f"Your promise (plan task in project {p['who']}): {p['text']}. Due: {p['t']}."
        else:
            c = ARCH[int(p['id'])]; root = c['root_seq']
            th = sorted((a for a in ARCH.values() if a['root_seq'] == root and a['created_at'] <= c['created_at']), key=lambda a: a['seq'])
            sit = '\n'.join(fmt(a) for a in th)[-1500:]
        files = mem_files(p['commit'])
        mem = HDR['MEM'] + ''.join(f'=== {n} ===\n{c}\n' for n, c in files)
        single = HDR['SINGLE'] + f"=== {p['single']} ===\n" + git('show', f"{p['commit']}:{p['single']}")
        k = len(mem) - len(HDR['PLACEBO'])
        reps = PLACEBO * (k // len(PLACEBO) + 1)
        placebo = HDR['PLACEBO'] + reps[:k]
        assert len(placebo) == len(mem)
        print(json.dumps({'task': f'{t}:{x["id"]}', 'type': t, 'date': p['decision_time'], 'situation': sit,
                          'commit': p['commit'], 'mem_files': [n for n, _ in files], 'mem_chars': len(mem),
                          'mem_sha256': hashlib.sha256(mem.encode()).hexdigest(), 'single': p['single'],
                          'placebo_excerpt': placebo[len(HDR['PLACEBO']):], 'single_sha256': hashlib.sha256(single.encode()).hexdigest()},
                         ensure_ascii=False))
