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
