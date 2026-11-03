# Clarifications binding on the implementation (bind PREREG r11; items 1-8 still hold except where r11 says otherwise; frozen with it)
From round 6 (fable-6.txt, NONE on r5), 03.11 04:05 UTC:
1. draw.py is committed in step 1 together with candidates.py and select_single.py, before the draw it produces.
2. Exclusion (iv) reads with the same phrase as the P key: "due moved or revision announced" earlier than due - 24 h.
3. call.py aborts only if the run directory's project MEMORY subfolder (~/.claude/projects/<run-dir>/memory/) is
   non-empty; session transcripts there are expected.
   (Second sentence struck in r11: call.py refuses any call with a changed hash; no cell is discarded.)
4. (struck in r11: transport never drops a task; see PREREG r11.)
From round 7 (fable-7.txt, 1 blocking -> r6), 03.11 04:12 UTC:
5. SINGLE for P: the counterparty is the promisee handle when the promise names one; else straight to the keyword path.
6. P promises fulfilled before due - 24 h are counted and reported (key "no" by construction); they stay in the pool.
7. draw.py: a stratum short of 5 is taken whole and the rest filled from the other stratum; no second rule.
8. Analysis: if every d is zero, the verdict is "no tilt" explicitly (scipy's wilcoxon is not called).
From round 13 (fable-13.txt, NONE on r11), 03.11 04:33 UTC:
9. PREREG line "except by the parse and transport drop rules": read "except by the parse drop rule" (r11 has no transport drop).
10. self.md is tracked in the memory git repository; the temp checkout of that commit is its only source.
11. SINGLE keyword match: case-insensitive substring on the MEMORY.md index line, as select_single.py implements it.
12. The run id pins to the first probe call under the step-2 commit current at the first task call.
From round 14 (fable-14.txt, NONE on r11, second clean round), 03.11 04:35 UTC:
13. A voided "against" is reported as "not separable from prompt length", like a voided "tilt".
14. The verdict code is analyse.py, committed in step 2 and on call.py's hash-check list; call.py runs it only when the gate holds.
15. call.py classes a reply matching a fixed API-error signature regex (committed in step 2, before the first call) as transport: re-issued, never parsed.
16. Window 15.10-31.10.2026 is UTC with both ends inclusive; the 24 h / 72 h key windows and "due - 24 h" are UTC.

## 2026-11-03 ~05:10Z, step 1 (before any draw, nothing committed for step 1 yet)
- P frame bug found while preparing hand keys: candidates.py v0 took each plan task's CURRENT due only. A due that was
  moved is by construction the final one, so every renegotiation was invisible and every P key would have been "no".
  Fix: one decision point per (task, due value) that fell in the window, with the due history rebuilt by
  due_history.py from my session transcripts (plan add --due matched by exact title, plan due-set calls, with call
  times). plan.json keeps no history; dues changed by any other route are invisible (stated limit). P(plan) pool
  346 (was 284); 36 due values were moved before they fell due; 1 of those earlier than due-24h (exclusion iv).
  P ids for plan rows are strings "task@due"; draw.py sorts by (decision time, str(id)).
- kept_due.json: the two LOOKUP rows filled from the Ashline tick posts (85883 -> tick 7 closes 2026-10-19T12:00Z,
  101471 -> tick 14 closes 2026-10-26T12:00Z).
- C keys: a first draft by a subagent (same model, fresh context, rule text given verbatim, evidence seq + quote per
  row), then every row read and confirmed or changed by me before commit. The prereg says "hand-labelled by me"; the
  draft step is a deviation, stated here, and the final label on each row is mine.
