"""Common, mechanical, cross-arm measures. Re-run:
   ../../../semi-formal-experiment/.venv/bin/python _debug_gen11/arms_review/measures.py
Reads only; writes only _debug_gen11/arms_review/measures.json."""
import sys, os, json, glob, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import floor
G = floor.G11

def sets():
    a1 = {os.path.basename(p).split('.')[0]: json.load(open(p))
          for p in glob.glob(G + '/ds_opus_loop/out/*.turn1.raw.json')}
    s = {'armA_turn1': a1, 'armA_CONVERGED(gold)': floor.modules_for('ds_opus_loop')}
    for a in ('list_in_prompt', 'list_in_prompt_insample', 'examples_arm',
              'retrieval_arm', 'forced_verdict_arm', 'selfreview_arm',
              'bucketed_arm', 'decompose_arm'):
        s[a] = floor.modules_for(a)
    return s

def selfcited(m, cid):
    con = {f"{c['name']}/{c['arity']}": c for c in (m.get('concepts') or [])}
    return [p for p in (m.get('requires') or [])
            if (e := con.get(p)) and e.get('licence') == 'textual' and e.get('cites') == cid]

def closures(m):
    return [e.get('closure') for e in (m.get('closure') or [])]

if __name__ == '__main__':
    out = {}
    for name, ms in sets().items():
        rec = {'n': len(ms), 'floor_clean': 0, 'selfcited_glosses': 0,
               'requires_names': 0, 'clauses_with_selfcite': 0,
               'closure': collections.Counter(), 'per_clause': {}}
        for cid, m in ms.items():
            try:
                f = floor.floor(m, cid)
                clean = f['outcome'] == 'translated' and not f['breaches'] and not f['errors']
            except Exception as e:                                   # noqa: BLE001
                f, clean = {'outcome': f'EXC {e!r}'}, False
            sc = selfcited(m, cid)
            rec['floor_clean'] += clean
            rec['selfcited_glosses'] += len(sc)
            rec['clauses_with_selfcite'] += bool(sc)
            rec['requires_names'] += len(m.get('requires') or [])
            rec['closure'].update(closures(m))
            rec['per_clause'][cid] = {'floor_clean': clean, 'selfcited': len(sc),
                                      'closure': closures(m)}
        rec['closure'] = dict(rec['closure'])
        out[name] = rec
        print(f"{name:24s} n={rec['n']:3d} floor_clean={rec['floor_clean']:3d} "
              f"selfcited={rec['selfcited_glosses']:3d}/{rec['requires_names']:3d} "
              f"closure={rec['closure']}")
    json.dump(out, open(os.path.join(HERE, 'measures.json'), 'w'), indent=1)
