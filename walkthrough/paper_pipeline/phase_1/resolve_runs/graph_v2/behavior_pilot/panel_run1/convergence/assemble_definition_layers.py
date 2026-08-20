#!/usr/bin/env python3
"""Assemble def_cal_ann_*.json (Opus annotation seats) into the three definition_*
layer files + definition_acts.json, then evaluate against the pre-registered
calibration expectations (definitional_lane_prereg.md). Deterministic, $0."""
import json, os, sys, glob
HERE = os.path.dirname(os.path.abspath(__file__))
BP = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, BP); sys.path.insert(0, os.path.dirname(BP))

def assemble(write=True):
    ann = {}
    for p in sorted(glob.glob(os.path.join(HERE, 'def_cal_ann_*.json'))):
        ann.update(json.load(open(p)))
    acts, sig, prot, pa = {}, {}, {}, {}
    for nid, claims in ann.items():
        alist = sorted({a for c in claims for a in c.get('acts', [])})
        if alist: acts[nid] = alist
        for i, c in enumerate(claims):
            k = f"{nid}|c{i}"
            # EMPTY-GOVERNS FAIL-OPEN (calibration r1 finding, 2026-08-20): a
            # definitional claim with governs=[] carries NO quality information —
            # the assert-lane analogue is "unannotated", which fails OPEN. Writing
            # governs=[] made signature_ok fail CLOSED (empty set never intersects
            # governs_concern), blocking 4 Set-A nodes on a semantics mismatch.
            # So: omit the sig record when there is no information (non-document
            # actor + empty governs); keep document-actor records so the
            # authority_plumbing exclusion still sees them.
            # (document-actor exclusion is carried by actor_ok over pa — writing
            # plumbing-only sig records made MIXED nodes all-plumbing and excluded
            # them; so sig records exist only where there is quality information)
            # (contexts-only records are also no-information: contexts matter
            # only paired with a governs value in gov_cond — so: governs or nothing)
            if c.get('governs'):
                sig[k] = {"governs": c.get('governs', []), "contexts": c.get('contexts', []),
                          "authority_plumbing": c.get('actor') == 'document'}
            # ROLE-PURITY MAPPING (contract 9a): the brief offered 'minor' but the
            # assert lane is role-pure (minor = third_party + attribute; zero 'minor'
            # values in assert_protects.json). Map to keep one schema.
            prot[k] = [('third_party' if v == 'minor' else v) for v in (c.get('protects') or ['unspecified'])]
            pa[k] = {"actor": c.get('actor', 'document'), "purpose": c.get('purpose', [])}
    if write:
        json.dump({"_": "definitional lane (prereg definitional_lane_prereg.md)", "acts": acts},
                  open(os.path.join(BP, 'definition_acts.json'), 'w'), indent=1)
        json.dump(sig, open(os.path.join(BP, 'definition_signature.json'), 'w'), indent=1)
        json.dump(prot, open(os.path.join(BP, 'definition_protects.json'), 'w'), indent=1)
        json.dump(pa, open(os.path.join(BP, 'definition_purpose_actor.json'), 'w'), indent=1)
    return ann, acts

def evaluate():
    import relevance_by_act as RBA
    import satisfiability_census as sc
    cal = json.load(open(os.path.join(HERE, 'definitional_calibration_sets.json')))
    mods = json.load(open(os.path.join(BP, 'modules_contract_v18.json')))['modules']
    br = RBA.bridges(); corpus = RBA.corpus_acts()
    A = set(cal['set_A_census_FNs']); Bb = cal['set_B_by_behavior']
    a_hit = a_miss = b_ok = b_bad = 0
    rows = []
    for slug, mod in mods.items():
        if 'module' not in mod: continue
        _, rel = RBA.relevance(mod, br, corpus)
        truth = sc.truth_all(slug)
        for n in sorted(A):
            if truth.get(n) == 'relevant':
                hit = n in rel
                a_hit += hit; a_miss += (not hit)
                rows.append(f"A {slug[:8]} {n} {'ENGAGED' if hit else 'still-FN'}")
        for n in Bb.get(slug, []):
            if n in A and truth.get(n) == 'relevant': continue  # counted in A for its own behavior
            bad = n in rel
            b_bad += bad; b_ok += (not bad)
            rows.append(f"B {slug[:8]} {n} {'ENGAGED(bad)' if bad else 'declined-ok'}")
    print('\n'.join(rows))
    print(f"\nSET A: engaged {a_hit}/{a_hit+a_miss} (prereg bar >=80%)")
    print(f"SET B: wrongly engaged {b_bad}/{b_bad+b_ok} (prereg bar <=2)")
    return a_hit, a_miss, b_bad

if __name__ == '__main__':
    ann, acts = assemble(write='--dry' not in sys.argv)
    print(f"assembled {len(ann)} nodes; {len(acts)} with described acts")
    if '--eval' in sys.argv: evaluate()
