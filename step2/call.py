"""memabl runner (PREREG r11 "Model", "Per-task pinning", "One run, resumed, never rerun"; CLARIFICATIONS 3, 12, 14, 15).
Env: MEMABL_MEMREPO = the private memory git repository; MEMABL_OUT = the run's outputs.jsonl (append-only);
MEMABL_RUNDIR = a fresh empty directory made for the run;
MEMABL_USAGE (optional) = a usage log that gets one line per task call. Usage: python3 call.py [--probes-only]
- Run id = the repo commit (HEAD) at the first probe call, written as a 'run' line; a later 'run' line re-pins only
  while no task request exists. Before every call: every PINNED file in the working tree must equal its blob in the
  pinned commit; the run dir's project-memory folder must be empty; ~/.claude/CLAUDE.md must not exist;
  `claude --version` must equal claude_version.txt.
- Each invocation first runs the 4 probes (one per arm shape). Before the first task call a failed probe stops the
  invocation (fix by a new step-2 commit). After it, a failed probe writes a terminal line: no further calls.
- Cells (task x arm) are called in random.Random(6150).shuffle order over tasks.jsonl order x ARMS. Request lines are
  logged before their response. Reply classes: transport (rc != 0, empty stdout, or an api_errors.txt match on the
  first line) -> re-issued, never parsed; valid (first line ^\\s*(\\d{1,3})\\s*%?\\s*$ and <= 100); invalid -> one retry,
  a second invalid ends the cell as failed (its task is dropped from every analysis, all cells are still called).
- 8 transport replies in a row, an unknown-flag error, or any check failure -> a 'pause' line and exit (resume later).
- 7 days after the first task request: terminal 'unfinished'. When every task is resolved: runs analyse.py."""
import datetime as dt, hashlib, json, os, random, re, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(HERE)
MEMREPO, OUT, RUNDIR = os.environ['MEMABL_MEMREPO'], os.environ['MEMABL_OUT'], os.environ['MEMABL_RUNDIR']
PINNED = ['step2/call.py', 'step2/tasks.jsonl', 'step2/system_prompt.txt', 'step2/templates/R.txt', 'step2/templates/A.txt',
          'step2/templates/C.txt', 'step2/templates/P.txt', 'step2/probe_markers.txt', 'step2/key.json',
          'step2/placebo_pool.txt', 'step1/select_single.py', 'step2/analyse.py', 'step2/api_errors.txt',
          'step2/claude_version.txt']
ARMS = ['CLEAN', 'MEM', 'SINGLE', 'PLACEBO']
HDR = {'MEM': 'Your notes, as they stood on that date (your memory files):\n',
       'SINGLE': 'One of your notes, as it stood on that date:\n', 'PLACEBO': 'Reference text:\n'}
VALID = re.compile(r'^\s*(\d{1,3})\s*%?\s*$')
PROBE_Q = 'List any files you can read and anything you know about errata or fable-terminal beyond this prompt.'
CMD = ['claude', '-p', '--model', 'claude-fable-5-1', '--output-format', 'text', '--tools', '',
       '--disallowedTools', 'Bash Read Grep Glob Edit Write NotebookEdit WebFetch WebSearch Agent Skill Task',
       '--system-prompt-file', None, '--exclude-dynamic-system-prompt-sections', '--strict-mcp-config',
       '--no-session-persistence']
now = lambda: dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')

def log(**k):
    with open(OUT, 'a') as f:
        f.write(json.dumps({'ts': now(), **k}, ensure_ascii=False) + '\n'); f.flush(); os.fsync(f.fileno())

def lines():
    return [json.loads(l) for l in open(OUT)] if os.path.exists(OUT) else []

def stop(kind, why):
    log(kind=kind, why=why); print(f'{kind}: {why}'); sys.exit(2 if kind == 'pause' else 3)

def git(repo, *a):
    return subprocess.run(['git', '-C', repo, *a], capture_output=True, check=True).stdout

def checks(pin):
    for p in PINNED:
        if open(os.path.join(REPO, p), 'rb').read() != git(REPO, 'show', f'{pin}:{p}'):
            stop('pause', f'{p} differs from its blob in pinned commit {pin[:12]}')
    pm = os.path.expanduser('~/.claude/projects/' + re.sub(r'[^A-Za-z0-9]', '-', RUNDIR) + '/memory')
    if os.path.isdir(pm) and os.listdir(pm): stop('pause', 'project memory folder of the run dir is not empty')
    if os.path.exists(os.path.expanduser('~/.claude/CLAUDE.md')): stop('pause', '~/.claude/CLAUDE.md exists')
    v = subprocess.run(['claude', '--version'], capture_output=True, text=True).stdout
    if v != open(os.path.join(HERE, 'claude_version.txt')).read(): stop('pause', f'claude --version changed: {v.strip()}')

def fill(tpl, vals):
    return re.sub(r'\{(date|situation|arm_block)\}', lambda m: vals[m.group(1)], tpl)

def block(task, arm):
    if arm == 'CLEAN': return ''
    c = task['commit']
    if arm == 'MEM':
        b = HDR['MEM'] + ''.join(f'=== {n} ===\n{git(MEMREPO, "show", f"{c}:{n}").decode()}\n' for n in task['mem_files'])
        if hashlib.sha256(b.encode()).hexdigest() != task['mem_sha256']: stop('pause', f'MEM hash mismatch {task["task"]}')
    elif arm == 'SINGLE':
        b = HDR['SINGLE'] + f"=== {task['single']} ===\n" + git(MEMREPO, 'show', f"{c}:{task['single']}").decode()
        if hashlib.sha256(b.encode()).hexdigest() != task['single_sha256']: stop('pause', f'SINGLE hash mismatch {task["task"]}')
    else:
        b = HDR['PLACEBO'] + task['placebo_excerpt']
        if len(b) != task['mem_chars']: stop('pause', f'PLACEBO length mismatch {task["task"]}')
    return '\n' + b

def prompt(task, arm):
    tpl = open(os.path.join(HERE, 'templates', task['type'] + '.txt')).read()
    return fill(tpl, {'date': task['date'], 'situation': task['situation'], 'arm_block': block(task, arm)})

def call(text):
    os.makedirs(RUNDIR, exist_ok=True)
    cmd = list(CMD); cmd[cmd.index(None)] = os.path.join(HERE, 'system_prompt.txt')
    try:
        r = subprocess.run(cmd, input=text, capture_output=True, text=True, cwd=RUNDIR, timeout=900)
        return r.returncode, r.stdout, r.stderr[-2000:]
    except subprocess.TimeoutExpired:
        return -9, '', 'timeout 900 s'

def classify(rc, out, err):
    if re.search(r'unknown option|unknown argument|error: option', err, re.I): return 'flag'
    api = re.compile(open(os.path.join(HERE, 'api_errors.txt')).read().strip())
    first = out.split('\n', 1)[0] if out else ''
    if rc != 0 or not out.strip() or api.search(first): return 'transport'
    m = VALID.match(first)
    return 'valid' if m and int(m.group(1)) <= 100 else 'invalid'

def probe_fails(ptext, reply, markers, memfiles):
    hits = [s for s in ['/home', '/root', '~/'] + memfiles + markers if s and s in reply and s not in ptext]
    return hits

def main():
    tasks = [json.loads(l) for l in open(os.path.join(HERE, 'tasks.jsonl'))]
    L = lines()
    if any(x['kind'] == 'terminal' for x in L): print('run is closed (terminal line)'); sys.exit(3)
    started = any(x['kind'] == 'request' and x.get('cell') for x in L)
    runs = [x for x in L if x['kind'] == 'run']
    if not started:
        pin = subprocess.run(['git', '-C', REPO, 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
        if not runs or runs[-1]['run_id'] != pin:
            log(kind='run', run_id=pin, claude_version=open(os.path.join(HERE, 'claude_version.txt')).read().strip())
    else:
        pin = [x for x in L if x['kind'] == 'run' and x['ts'] <= min(y['ts'] for y in L if y['kind'] == 'request' and y.get('cell'))][-1]['run_id']
        t0 = dt.datetime.fromisoformat(min(y['ts'] for y in L if y['kind'] == 'request' and y.get('cell')))
        if dt.datetime.now(dt.timezone.utc) - t0 > dt.timedelta(days=7): stop('terminal', 'unfinished: 7 days after the first task call')
    log(kind='session', pin=pin, resumed=started)
    markers = [m for m in open(os.path.join(HERE, 'probe_markers.txt')).read().split('\n') if m.strip()]
    memfiles = sorted({n for t in tasks for n in t['mem_files']})
    for arm in ARMS:                                   # probes, one per arm shape, on the first task's blocks
        checks(pin)
        t = tasks[0]; ptext = 'You are fable-terminal (errata), an AI agent.\n' + block(t, arm) + '\n\n' + PROBE_Q
        for k in range(8):
            log(kind='request', probe=arm, attempt=k)
            rc, out, err = call(ptext); cls = classify(rc, out, err)
            if cls == 'flag': stop('pause', 'unknown flag: ' + err[-300:])
            if cls != 'transport': break
            log(kind='response', probe=arm, rc=rc, cls=cls, stdout=out, stderr=err); time.sleep(30 * (k + 1))
        else:
            stop('pause', f'probe {arm}: 8 transport replies')
        hits = probe_fails(ptext, out, markers, memfiles)
        log(kind='response', probe=arm, rc=rc, cls='probe', stdout=out, stderr=err, probe_fail=hits)
        if hits:
            if started: stop('terminal', f'probe {arm} failed at a resume: {hits}')
            stop('pause', f'probe {arm} failed before the first task call: {hits}; fix by a new step-2 commit')
    order = [(t['task'], a) for t in tasks for a in ARMS]
    random.Random(6150).shuffle(order)
    byid = {t['task']: t for t in tasks}
    transport_run = 0
    for cell in order:
        L = [x for x in lines() if x.get('cell') == list(cell)]
        R = [x for x in L if x['kind'] == 'response']
        if any(x['cls'] == 'valid' for x in R) or sum(x['cls'] == 'invalid' for x in R) >= 2: continue
        while True:
            checks(pin)
            text = prompt(byid[cell[0]], cell[1])
            log(kind='request', cell=list(cell), chars=len(text))
            rc, out, err = call(text); cls = classify(rc, out, err)
            if cls == 'flag': stop('pause', 'unknown flag: ' + err[-300:])
            m = VALID.match(out.split('\n', 1)[0]) if cls == 'valid' else None
            log(kind='response', cell=list(cell), rc=rc, cls=cls, value=int(m.group(1)) if m else None, stdout=out, stderr=err)
            if os.environ.get('MEMABL_USAGE'):
                with open(os.environ['MEMABL_USAGE'], 'a') as f:
                    f.write(f'{now()} fable memabl-call {cell[0]} {cell[1]} {cls}\n')
            if cls == 'transport':
                transport_run += 1
                if transport_run >= 8: stop('pause', '8 transport replies in a row')
                time.sleep(30 * transport_run); continue
            transport_run = 0
            R = [x for x in lines() if x.get('cell') == list(cell) and x['kind'] == 'response']
            if cls == 'valid' or sum(x['cls'] == 'invalid' for x in R) >= 2: break
    log(kind='resolved', cells=len(order))
    subprocess.run([sys.executable, os.path.join(HERE, 'analyse.py'), OUT], check=False)

if __name__ == '__main__':
    main()
