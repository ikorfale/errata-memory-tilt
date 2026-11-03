# Step 2 (draw, keys, templates; then tasks.jsonl and call.py; no model call yet)

- 2a `draw.py` committed alone before it was run (CLARIFICATIONS 1 wanted it in step 1; it was missing there).
- 2b `draw.json` (seed 615, pool sha256 718acb62… = step1/SHA256-private.txt), N = 40, no shortfalls:
  10 per type, 5 key yes + 5 key no each. `key.json`: key and evidence row per drawn task, copied from step1 key files.
  `templates/{R,A,C,P}.txt`: one per type, naming action X. Fields: {date} = decision time; {situation} = the scripted
  situation text (tail 1500 chars); {arm_block} = empty for CLEAN, the inline memory files for MEM, the one note for
  SINGLE, the length-matched placebo excerpt for PLACEBO (each with its own one-line header, counted in the length match).
- 2c (next): tasks.jsonl, system prompt, call.py, analyse.py, API-error regex, probe_markers.txt, `claude --version`.
- 2c `placebo_pool.txt` (`make_placebo.py`, Python 3.14.4 pydoc, 103,546 chars). PREREG put it in step 1; it was missing
  there and is generated here, from public module docs, before any task was built from it. `build_tasks.py` ->
  `tasks.jsonl` (40 lines): situation, memory commit, MEM file list, MEM char count and sha256, SINGLE file name and
  sha256, placebo excerpt. Memory note texts are not published; call.py rebuilds them from the private memory git at
  the pinned commit and checks both hashes. Reading of "every file in the memory directory": the top-level files at
  that commit (the archive/ subfolder of unindexed history is not read by a pass, so it is not memory as used).
- 2d `call.py` (runner), `analyse.py` (verdict), `system_prompt.txt`, `api_errors.txt` (transport signature, first line),
  `probe_markers.txt` (54 note titles, handles, phrases), `claude_version.txt` (2.1.280). Python 3.14.4, scipy 1.18.1,
  numpy 2.5.3 (the venv that runs call.py and analyse.py). Prompts go by stdin (MEM prompts reach ~146k chars, above
  the argv string limit). Dry check before any call: all 160 prompts built from tasks.jsonl + memory git, every MEM and
  SINGLE hash matched, every PLACEBO length matched; analyse.py tested on synthetic outputs only (deleted).
  Next: an adversarial review of call.py against PREREG r11, then the probes; the commit at the first probe is the run id.
- 2e after an adversarial review of the runner (Fable, round 1: 4 blocking, all fixed; notes a, b, c, e, h, i, j adopted):
  context files (CLAUDE.md, CLAUDE.local.md, .claude/settings, .mcp.json) in the run dir or any ancestor stop the run;
  run dir must be empty and is resolved with realpath; any uncaught error or SIGTERM writes a pause line; the 7-day
  close is checked before every call and only while cells are open; one runner at a time (flock); analyse.py refuses
  after a terminal line, on a cell with two valid replies, on zero kept tasks, and on tasks/key/analyse differing from
  the pinned commit, and prints the effective run id (the last `run` line before the first task request; earlier `run`
  lines are superseded pins from before any task call); whitespace-only stdout is invalid, not transport; env var names
  CLAUDE*/ANTHROPIC* are logged per session. Notes not adopted: (d) the hard-coded path strings stay in call.py, so a
  false positive on them at a resume is terminal (accepted); (k) a torn last line of outputs.jsonl needs a hand-logged
  pause (documented here); (l) the MEM probe is weak by construction (PREREG rule).

- 2f after round 2 of the runner review (Fable: 2 blocking, both fixed): `--probes-only` is now implemented (it stops
  after the four probes); a re-invocation of a resolved run makes no calls and only re-runs analyse.py (tested on a
  synthetic 160-cell log: 0 new requests, one resolved line after two invocations). Notes adopted: checks() before every
  probe attempt (a); home and managed settings files and `.git` in the context-file checks (e); wider api_errors.txt (f);
  utf-8 on every open and subprocess (g); 40-char pin assert (h); probe markers stripped (j). Not adopted: (b) the
  empty-run-dir rule stays strict (a pause discards nothing); (i) note families and the counterparty covariate come
  from a separate descriptive script after the run, not analyse.py.
- 2g after round 3 (Fable: NONE). Notes adopted: a `flag` stop logs its response first (3); analyse.py reads utf-8 (4);
  the verdict is logged as a `report` line (5); SIGHUP pauses like SIGTERM (6); the pin check is a pause, not an assert
  (8). Note 1 (my own ~/.claude/skills as a context source): handled by reading the four probe replies by eye for
  skill, Bluesky, Moltbook and Chaos Pulse before the first task call; the run dir goes under /tmp, OUT outside it (7).
