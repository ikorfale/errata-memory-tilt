"""placebo_pool.txt (PREREG r11 "Situation text and arms", PLACEBO): `python3 -m pydoc` for re, json, csv, datetime,
textwrap, string, in that order (no os), concatenated; the FILE section (header and its indented lines) removed and any
line holding an absolute filesystem path removed. Generated once; it should have been committed in step 1 and was not
(stated in README-step2.md). Usage: python3 make_placebo.py > placebo_pool.txt"""
import re, subprocess, sys
PATH = re.compile(r'(?<![\w:/])/(usr|home|lib|lib64|opt|etc|root|tmp|var)\b|~/')
out = []
for m in ['re', 'json', 'csv', 'datetime', 'textwrap', 'string']:
    txt = subprocess.run([sys.executable, '-m', 'pydoc', m], capture_output=True, text=True, env={'PAGER': 'cat', 'TERM': 'dumb'}).stdout
    skip = False
    for line in txt.splitlines():
        if line.strip() == 'FILE':
            skip = True; continue
        if skip:
            if line.startswith(' ') or not line.strip():
                if not line.strip(): skip = False
                continue
            skip = False
        if PATH.search(line): continue
        out.append(line)
sys.stdout.write('\n'.join(out) + '\n')
