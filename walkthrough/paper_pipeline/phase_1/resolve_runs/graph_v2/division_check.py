#!/usr/bin/env python3
"""Mechanical checks on a division.json. Usage: division_check.py <division.json> <span_lo> <span_hi>"""
import json, sys

def main(path, lo, hi):
    lo, hi = int(lo), int(hi)
    d = json.load(open(path))
    print('decision:', d.get('decision'))
    ch = d.get('children', [])
    print('children:', len(ch), [tuple(c['span']) for c in ch])
    if not 2 <= len(ch) <= 3:
        print('!! child count out of 2-3')
    # contiguity + coverage
    spans = [tuple(c['span']) for c in ch]
    if spans:
        if spans[0][0] != lo: print(f'!! first child starts {spans[0][0]}, span starts {lo}')
        if spans[-1][1] != hi: print(f'!! last child ends {spans[-1][1]}, span ends {hi}')
        for (a1, b1), (a2, b2) in zip(spans, spans[1:]):
            if a2 != b1 + 1: print(f'!! gap/overlap between {b1} and {a2}')
    seeds = d.get('seed_vocabulary', [])
    bad = [s for s in seeds if not (isinstance(s, dict) and s.get('name') and s.get('prose'))]
    print('seeds:', len(seeds), 'malformed:', len(bad))
    xl = d.get('expected_cross_links', [])
    seednames = {s['name'] for s in seeds if isinstance(s, dict) and s.get('name')}
    unseeded = [x.get('name') for x in xl if x.get('name') not in seednames]
    print('expected_cross_links:', len(xl), 'naming a non-seeded concept:', unseeded)
    print('judgment_calls:', len(d.get('judgment_calls', [])))
    for j in d.get('judgment_calls', [])[:6]:
        print('  -', str(j)[:110])

if __name__ == '__main__':
    main(*sys.argv[1:])
