#!/usr/bin/env python3
"""Absorbed-content check for restatement merges.

A merge retires node R and keeps survivor S. This checks that R's distinctive content
elements appear in S's establishes+provides prose. Heuristic (proper-noun phrases,
enumerated items, quoted terms) -- a flagged element is a finding to read, not a verdict.
Per DEBUGGING_TIPS S8: proven RED on the known n028/n008 tier-loss case before trust.
"""
import re, sys

def elements(text):
    els = set()
    # enumerated items "(N) ..." up to next enum/period
    for m in re.finditer(r'\((\d)\)\s*([^;.,(]{3,60})', text):
        els.add(m.group(2).strip())
    # Capitalized multiword-ish phrases and tier names
    for m in re.finditer(r'\b([A-Z][a-z]+(?: [A-Z][a-z]+)+)\b', text):
        els.add(m.group(1))
    # quoted terms
    for m in re.finditer(r'"([^"]{3,40})"', text):
        els.add(m.group(1))
    return els

def check(survivor_text, retired_text):
    missing = []
    for el in sorted(elements(retired_text)):
        norm = el.lower()
        if norm not in survivor_text.lower():
            missing.append(el)
    return missing

if __name__ == '__main__':
    import json
    def nm(x): return x if isinstance(x, str) else x.get('prose', '')
    surv_file, surv_id, ret_file, ret_id = sys.argv[1:5]
    S = next(n for n in json.load(open(surv_file))['nodes'] if n['id'] == surv_id)
    R = next(n for n in json.load(open(ret_file))['nodes'] if n['id'] == ret_id)
    surv_blob = S['establishes'] + ' ' + ' '.join(nm(p) for p in S.get('provides', []))
    missing = check(surv_blob, R['establishes'])
    if missing:
        print(f'MERGE-LOSS: {len(missing)} element(s) of {ret_id} absent from {surv_id}:')
        for x in missing: print('  -', x)
        sys.exit(1)
    print(f'OK: all detected elements of {ret_id} present in {surv_id}')
