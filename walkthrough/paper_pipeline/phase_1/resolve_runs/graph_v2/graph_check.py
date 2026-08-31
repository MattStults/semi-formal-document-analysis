#!/usr/bin/env python3
"""Mechanical checks on a document-graph run. Usage: graph_check.py graph.json

Reads the RAW spec for quote verification (ground truth), per the design rule that
line numbers refer to the raw file. Every rate prints its denominator (DEBUGGING_TIPS SS2).
"""
import json, re, sys, statistics
from pathlib import Path

# Resolved relative to this file so a fresh clone works from any cwd.
RAW = Path(__file__).resolve().parents[5] / 'specs/openai-model-spec/model_spec.md'

def normalise(s):
    # SS17: strip formatting the file carries, never content words.
    s = re.sub(r'\[\^[^\]]+\]', '', s)          # footnote markers
    s = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', s)  # markdown links -> anchor text
    s = s.replace('**', '').replace('*', '')     # emphasis
    s = s.replace('“', '"').replace('”', '"').replace('’', "'").replace('‘', "'")
    s = re.sub(r'\s+', ' ', s)
    return s.strip().lower()

def adapt(n):
    """Accept v1 format (lines: [[a,b]], needs/provides: [str]) and v2 native."""
    if 'spans' not in n and 'lines' in n:
        n['spans'] = [{'lines': ab} for ab in n['lines']]
    for f in ('needs', 'provides'):
        n[f] = [{'name': x, 'prose': x} if isinstance(x, str) else x for x in n.get(f, [])]
    return n

def main(path, limit=None, lo=1):
    """limit: last line of the graph's span; lo: first line (coverage is judged on [lo, limit])."""
    lines = RAW.read_text().splitlines()
    if limit:
        lines = lines[:int(limit)]
    nmax = len(lines)
    lo = int(lo)
    g = json.load(open(path))
    nodes = [adapt(n) for n in g.get('nodes', [])]
    print(f'nodes: {len(nodes)}   uncovered entries: {len(g.get("uncovered", []))}')

    # --- ids
    ids = [n.get('id') for n in nodes]
    if len(set(ids)) != len(ids):
        print('!! duplicate ids')

    # --- spans resolve
    bad_lines, bad_quotes, quotes_total = [], [], 0
    node_lineset = {}
    for n in nodes:
        covered = set()
        for sp in n.get('spans', []):
            a, b = sp['lines']
            if not (1 <= a <= b <= nmax):
                bad_lines.append((n['id'], a, b))
                continue
            covered.update(range(a, b + 1))
            if 'quote' in sp:
                quotes_total += 1
                hay = normalise(' '.join(lines[a-1:b]))
                if normalise(sp['quote']) not in hay:
                    bad_quotes.append((n['id'], sp['quote'][:60]))
        node_lineset[n['id']] = covered
    print(f'bad line ranges: {len(bad_lines)} / {sum(len(n.get("spans",[])) for n in nodes)} spans  {bad_lines[:5]}')
    print(f'bad quotes: {len(bad_quotes)} / {quotes_total}  {bad_quotes[:5]}')

    # --- size distribution
    sizes = sorted(len(s) for s in node_lineset.values())
    if sizes:
        print(f'span sizes (lines covered): min {sizes[0]}  median {statistics.median(sizes)}  max {sizes[-1]}')
        print(f'  nodes covering 0 lines: {sum(1 for s in sizes if s==0)};  >100 lines: {sum(1 for s in sizes if s>100)} of {len(sizes)}')

    # --- overlap / nesting (K5)
    idl = list(node_lineset.items())
    overlap = nest = 0
    for i in range(len(idl)):
        for j in range(i+1, len(idl)):
            a, b = idl[i][1], idl[j][1]
            if a and b and (a & b):
                overlap += 1
                if a <= b or b <= a:
                    nest += 1
    print(f'overlapping node pairs: {overlap} (of {len(idl)*(len(idl)-1)//2}); nested pairs: {nest}')

    # --- names
    provides = {}
    for n in nodes:
        for p in n.get('provides', []):
            provides.setdefault(p['name'], []).append(n['id'])
    multi = {k: v for k, v in provides.items() if len(v) > 1}
    needs_total = dangling = 0
    dang_names = []
    for n in nodes:
        for d in n.get('needs', []):
            needs_total += 1
            if d['name'] not in provides:
                dangling += 1
                dang_names.append((n['id'], d['name']))
    print(f'provided names: {len(provides)} ({len(multi)} provided by >1 node)')
    print(f'needs: {needs_total}; dangling (no provider): {dangling}')
    for nid, nm in dang_names:
        print(f'   dangling: {nid} needs {nm}')
    if multi:
        print(f'   multi-provided: {dict(list(multi.items())[:8])}')

    # --- K1: a node grounded on the L183-191 list (span intersecting it, not a whole-section
    # blob) whose provides mentions an ordering. Report exact list coverage separately.
    K1 = []
    for n in nodes:
        for sp in n.get('spans', []):
            a, b = sp['lines']
            if a <= 191 and b >= 183 and (b - a) <= 15:
                K1.append((n['id'], (a, b)))
                break
    hit = []
    for nid, span in K1:
        n = next(x for x in nodes if x['id'] == nid)
        blob = ' '.join(p['prose'] + ' ' + p['name'] for p in n.get('provides', [])).lower()
        if re.search(r'order|rank|preced|priorit|higher|outrank|hierarch', blob):
            full = span[0] <= 186 and span[1] >= 191
            hit.append((nid, span, 'covers full list' if full else 'PARTIAL list coverage'))
    print(f'K1 nodes grounded on the L183-191 list: {K1}; with ordering in provides: {hit}')

    # --- needs density and quote usage
    zero_needs = sum(1 for n in nodes if not n.get('needs'))
    print(f'nodes with zero needs: {zero_needs} / {len(nodes)}')
    print(f'spans with quotes: {quotes_total} / {sum(len(n.get("spans",[])) for n in nodes)}')

    # --- heading-authority capture: headings carrying authority= metadata
    auth_lines = [i for i in range(lo, nmax+1) if re.search(r'^#+ .*authority=', lines[i-1])]
    captured = [i for i in auth_lines if any(i in s for s in node_lineset.values())]
    print(f'authority-tagged headings captured in some node: {len(captured)} / {len(auth_lines)}')

    # --- coverage
    all_covered = set().union(*node_lineset.values()) if node_lineset else set()
    unc = set()
    for u in g.get('uncovered', []):
        a, b = u['lines']
        unc.update(range(a, b+1))
    nonblank = {i for i in range(lo, nmax+1) if lines[i-1].strip()}
    print(f'lines covered by nodes: {len(all_covered & nonblank)} / {len(nonblank)} non-blank; declared uncovered: {len(unc & nonblank)}; unaccounted: {len(nonblank - all_covered - unc)}')

if __name__ == '__main__':
    main(*sys.argv[1:])
