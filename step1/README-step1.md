# Step 1 (committed before any draw)

Candidates 15-31.10.2026 by script, keys, SINGLE note per candidate, exclusion log. No draw has been made and no model
has been called. Order per PREREG r11: this commit, then step 2 (draw, key.json, templates, tasks.jsonl, call.py).

- `candidates.py` -> candidates (public copy `candidates_public.jsonl`: the 7 mail rows carry a row hash instead of the
  private text; `SHA256-private.txt` pins the full local files).
- `due_history.py` -> `due_history.json`: plan due values over time, rebuilt from session transcripts (see CLARIFICATIONS).
- Keys: `R_keys.tsv` (scripted, `keys_r.py`); `A_keys.tsv`, `C_keys.tsv`, `P_keys.tsv` (hand, evidence per row; A and C from
  a subagent draft, every row read by me, see CLARIFICATIONS).
- `select_single.py` -> `single.jsonl` (decision time, memory commit, SINGLE note, rule).
- `exclusions.py` -> `exclusions.tsv` and the pool: 1340 items (R 636 yes / 48 no, A 208 / 29, C 24 / 66, P 24 / 305),
  122 excluded (A 95 under (i), P 27 recurring slots under (i)).
