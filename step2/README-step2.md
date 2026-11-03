# Step 2 (draw, keys, templates; then tasks.jsonl and call.py; no model call yet)

- 2a `draw.py` committed alone before it was run (CLARIFICATIONS 1 wanted it in step 1; it was missing there).
- 2b `draw.json` (seed 615, pool sha256 718acb62… = step1/SHA256-private.txt), N = 40, no shortfalls:
  10 per type, 5 key yes + 5 key no each. `key.json`: key and evidence row per drawn task, copied from step1 key files.
  `templates/{R,A,C,P}.txt`: one per type, naming action X. Fields: {date} = decision time; {situation} = the scripted
  situation text (tail 1500 chars); {arm_block} = empty for CLEAN, the inline memory files for MEM, the one note for
  SINGLE, the length-matched placebo excerpt for PLACEBO (each with its own one-line header, counted in the length match).
- 2c (next): tasks.jsonl, system prompt, call.py, analyse.py, API-error regex, probe_markers.txt, `claude --version`.
