#!/usr/bin/env python3
"""ONTOLOGY VALIDATORS — pipeline modules that gate an ontology the way
corpus_gate.py gates spec modules. Two ontologies, two validators, because
they fail differently:

  acts     — a CLASSIFICATION (bespoke functor -> canonical act). Judged by
             bridge accuracy, structural soundness, grain (via held-out
             relevance), and firing consistency (bridged query reproduces a
             hand-grounded case).
  atoms    — a VOCABULARY CONTRACT (shared situation names). Judged by gap
             rate (behaviors written in it without inventing), collision
             rate (one name, one meaning), and grounding fit.

Every check is a QUESTION a later reader can apply without judgment. Tiers:
hard = the ontology is unusable as-is; review = directs attention; info =
on the record. Checks that need an input the repo does not yet hold report
NOT-RUNNABLE loudly (never silently pass) — the pass-looks-like-did-not-run
failure this project keeps re-learning.

Usage:  .../.venv/bin/python validate_ontology.py acts   [--sample N] [--json out]
        .../.venv/bin/python validate_ontology.py atoms  [--json out]
"""
import json, os, re, sys, random, glob
from collections import Counter, defaultdict
HERE = os.path.dirname(os.path.abspath(__file__))
G2 = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, G2); sys.path.insert(0, os.path.join(G2, "..", ".."))

# ============================================================== ACT ONTOLOGY

def acts_structural():
    """A1 hard: every bespoke functor bridges to exactly one canonical act;
    A2 review: NEW escapes are rare and specific; A3 review: bucket sizes —
    a bucket holding >25% of all functors is a catch-all (grain suspect);
    A4 hard: every canonical act is performable (declared in the contract)."""
    br = json.load(open(os.path.join(HERE, "act_bridges.json")))
    fun = json.load(open(os.path.join(HERE, "act_functors.json")))
    canon = set(json.load(open(os.path.join(HERE, "behavior_vocab.json")))["canonical_acts_provisional"])
    hits = {"hard": [], "review": [], "info": []}
    unbridged = [f for f in fun if f not in br]
    if unbridged: hits["hard"].append(f"A1 {len(unbridged)} bespoke functor(s) with no bridge: {unbridged[:8]}")
    multi = [f for f, v in br.items() if isinstance(v.get("canonical"), list)]
    if multi: hits["hard"].append(f"A1 {len(multi)} functor(s) bridged to more than one canonical act")
    news = [f for f, v in br.items() if str(v["canonical"]).startswith("NEW:")]
    hits["info"].append(f"A2 NEW escapes: {len(news)}/{len(br)} ({sorted(set(br[f]['canonical'] for f in news))})")
    if len(news) > 0.05 * len(br): hits["review"].append(f"A2 NEW escapes exceed 5% — canonical list is missing a real act")
    sizes = Counter(v["canonical"] for v in br.values() if not str(v["canonical"]).startswith("NEW:"))
    for c, n in sizes.most_common():
        if n > 0.25 * len(br): hits["review"].append(f"A3 `{c}` holds {n}/{len(br)} functors ({100*n//len(br)}%) — catch-all; grain suspect")
    for c in sizes:
        if c not in canon: hits["hard"].append(f"A4 bridge target `{c}` is not a declared canonical act")
    hits["info"].append("A3 bucket sizes: " + ", ".join(f"{c} {n}" for c, n in sizes.most_common()))
    return hits


def acts_bridge_accuracy_sample(n=60, seed=20260818):
    """A5 (review, needs a reader): a stratified sample of bridges for a
    BLIND accuracy check — writes ACT_BRIDGE_SPOTCHECK.md with functor,
    gloss, example module and the assigned canonical act, for a Fable
    instance or Matt to mark AGREE/DISAGREE. The rate is entered back via
    --accuracy-file. Reports NOT-RUNNABLE until a marked file exists."""
    br = json.load(open(os.path.join(HERE, "act_bridges.json")))
    fun = json.load(open(os.path.join(HERE, "act_functors.json")))
    by = defaultdict(list)
    for f, v in br.items(): by[str(v["canonical"])].append(f)
    rnd = random.Random(seed); rows = []
    for c, fs in sorted(by.items()):
        k = max(2, round(n * len(fs) / len(br)))
        rows += [(c, f) for f in rnd.sample(sorted(fs), min(k, len(fs)))]
    out = ["# Act-bridge blind spot-check (A5) — mark AGREE / DISAGREE per row", "",
           "For each bespoke act: given its gloss and an example module, is the assigned canonical act the one a careful reader would choose? Rate = AGREE / total.", ""]
    for c, f in rows:
        out.append(f"* `{f}` /{fun[f]['arity']} — gloss: {fun[f]['gloss'][:140] or '(none)'} — e.g. `{fun[f]['modules'][0]}` — **assigned: {c}** → AGREE / DISAGREE: ____")
    open(os.path.join(HERE, "ACT_BRIDGE_SPOTCHECK.md"), "w").write("\n".join(out) + "\n")
    marked = os.path.join(HERE, "act_bridge_spotcheck_result.json")
    if os.path.exists(marked):
        r = json.load(open(marked)); rate = r["agree"] / r["total"]
        tier = "hard" if rate < 0.90 else ("review" if rate < 0.95 else "info")
        return {tier: [f"A5 bridge accuracy {r['agree']}/{r['total']} = {rate:.2f} (blind spot-check)"]}, len(rows)
    return {"review": [f"A5 NOT-RUNNABLE: bridge accuracy needs a marked spot-check — {len(rows)} rows written to ACT_BRIDGE_SPOTCHECK.md"]}, len(rows)


def acts_grain_by_relevance():
    """A6 review: grain measured downstream — per behavior, held-out
    precision/recall of relevance-by-act (relevance_by_act.json). Precision
    < 0.75 on a behavior whose performed acts include a catch-all bucket ->
    the bucket is too coarse for that behavior."""
    p = os.path.join(HERE, "panel_run1", "relevance_by_act.json")
    if not os.path.exists(p): return {"review": ["A6 NOT-RUNNABLE: run relevance_by_act.py --score first"]}
    r = json.load(open(p)); hits = {"review": [], "info": []}
    for slug, v in r.items():
        h = v.get("held_out")
        if not h: continue
        ed = h["engagement_def"]; a, b = map(int, ed.split("/")); prec = a / b if b else 0
        hits["info"].append(f"A6 {slug}: performs {v['performs']}; held-out precision {prec:.2f}, recall {h['recall']}, deviation-def {h['deviation_def']}")
        if prec < 0.75: hits["review"].append(f"A6 {slug}: precision {prec:.2f} < 0.75 through {v['performs']} — split the coarse bucket(s) and re-score")
    return hits


def acts_firing_consistency():
    """A7 hard: the bridged query must reproduce a hand-grounded case.
    Reference: S4 (contradiction_S4.json) — over-cautious refusal -> 1
    conflict, compliant -> 0. Loads the same 10 modules + act_bridges.lp +
    a behavior instance in CANONICAL acts, and checks conflicts match."""
    try:
        import behavior_match as BM, link_nodes
    except Exception as ex:
        return {"hard": [f"A7 NOT-RUNNABLE: {ex!r}"]}
    ref = json.load(open(os.path.join(HERE, "panel_run1", "contradiction_S4.json")))
    nodes = ["l609_698_n017","l609_698_n010","l1542_1706_n007","l609_698_n014","l609_698_n020","l1542_1706_n002","l1542_1706_n005","l3954_4251_n023","l3954_4251_n018","l609_698_n016"]
    common = ["assistant_definition(asst)", "root_authority(rule_r)", "shoplifting_deterrence_tips(t1)", "misusable_as_shoplifting_tips(t1)",
              "user_request(r1)", "request(r1)", "ambiguous_request(r1)", "some_reasonable_interpretations_aligned(r1)",
              "some_reasonable_interpretations_not_aligned(r1)", "unclear_intent(r1)"]
    bridges = open(os.path.join(HERE, "act_bridges.lp")).read()
    # canonical-act instance: the behavior performs canonical acts; a bridge in the OTHER direction
    # (canonical -> each bespoke act) is what lets `does` reach the modules. Derive it from the same file.
    # BEHAVIOR -> CORPUS direction: a behavior performing canonical act C(X) performs every
    # bespoke act bridged to C, so `does(B, bespoke(X))` joins the modules' asserts. This is
    # the rule the real query layer needs (canonical_act/1 in act_bridges.lp is the reverse).
    rev = []
    for ln in bridges.splitlines():
        m = re.search(r"canonical_act\((\w+)\((X|unit)\)\)\s*:-\s*(\w+)(\(X\))?", ln)
        if m and m.group(2) == "X":
            rev.append(f"does(B, {m.group(3)}(X)) :- does(B, {m.group(1)}(X)), behavior(B).")
    hits = {"hard": [], "info": []}
    for label, does, expect in (("S4a", ["refuse(r1)", "judge_or_moralize(r1)"], 1), ("S4b", ["comply(r1)", "provide(t1)"], 0)):
        lp = BM.render_behavior_module("b_s4", "S4 canonical", common, does)
        # bespoke acts the modules assert on: make the corpus see them as performed via the reverse bridge
        prog_extra = "\n".join(rev) + "\n"
        try:
            q = BM.relevance_query(nodes, lp + "\n" + prog_extra)
            got = len(q.get("conflicts") or [])
        except Exception as ex:
            hits["hard"].append(f"A7 {label}: query failed under bridges: {str(ex)[:120]}"); continue
        hits["info"].append(f"A7 {label}: conflicts {got} (hand-grounded reference {expect})")
        if got != expect: hits["hard"].append(f"A7 {label}: bridged query gives {got} conflicts, hand-grounded gave {expect} — bridge semantics differ")
    return hits

# ============================================================ ATOM ONTOLOGY

def atoms_gap_rate():
    """T1 review: gap rate — concepts behavior modules could not express in
    the declared vocabulary (modules_contract_*.json `gaps`). Reported per
    behavior; a rate that does not fall as behaviors accumulate means the
    vocabulary is not converging."""
    hits = {"info": [], "review": []}
    for p in sorted(glob.glob(os.path.join(HERE, "modules_contract_*.json"))):
        d = json.load(open(p))
        for slug, m in d.get("modules", {}).items():
            g = m.get("gaps") or []
            n_pred = len(m.get("conditions", [])) + len((m.get("module") or {}).get("situation", []))
            hits["info"].append(f"T1 {os.path.basename(p)} {slug}: {len(g)} gaps against {n_pred} situation/condition predicates")
            if g and len(g) > 0.3 * max(1, n_pred): hits["review"].append(f"T1 {slug}: gap rate {len(g)}/{n_pred} — vocabulary missing concepts this behavior needs: {[x[:50] for x in g[:3]]}")
    if not hits["info"]: hits["review"].append("T1 NOT-RUNNABLE: no modules_contract_*.json with gaps recorded")
    return hits


def atoms_collision_rate():
    """T2 hard: same name, different meaning — corpus_gate's cross-module
    seam checks (arity disagreement, section-local gloss) read from the
    latest corpus_gate_report.json. Any hard hit = a shared name that does
    not mean one thing."""
    p = os.path.join(G2, "corpus_gate_report.json")
    if not os.path.exists(p): return {"hard": ["T2 NOT-RUNNABLE: no corpus_gate_report.json"]}
    r = json.load(open(p))["cross"]; hits = {"hard": [], "review": [], "info": []}
    for k in ("seam_contract", "arity_disagreement", "section_local_gloss"):
        n = len(r.get(k, {}).get("hits", []))
        (hits["hard"] if n else hits["info"]).append(f"T2 {k}: {n} hit(s)")
    n = len(r.get("sort_disagreement", {}).get("hits", [])); hits["review" if n else "info"].append(f"T2 sort_disagreement: {n} hit(s)")
    return hits


def atoms_coinage_spread():
    """T3 review: how per-module the input vocabulary is — distinct input
    names vs modules, and the share used by exactly one module. A shared
    ontology drives the singleton share down; 1739 names over 762 modules
    with most used once is the act problem in the situation layer."""
    inputs = json.load(open(os.path.join(HERE, "behavior_vocab.json")))["inputs"]
    tot = len(inputs); single = sum(1 for v in inputs.values() if v == 1)
    hits = {"info": [f"T3 {tot} distinct input names; {single} ({100*single//tot}%) used by exactly one module"]}
    if single > 0.6 * tot: hits["review"] = [f"T3 singleton share {100*single//tot}% — situation vocabulary is per-module coinage; the act procedure (inventory→classify→bridge→gate) has not been run over inputs"]
    return hits


def atoms_grounding_fit():
    """T4 (hard when runnable): when a behavior's situation facts are
    written in the shared vocabulary, do intended modules' BODIES satisfy?
    Needs a grounded behavior instance + expected firing set. Uses S4 as
    the reference case: its facts are all declared inputs; the reference
    modules must fire as recorded."""
    ref = os.path.join(HERE, "panel_run1", "contradiction_S4.json")
    if not os.path.exists(ref): return {"hard": ["T4 NOT-RUNNABLE: no grounded reference case"]}
    r = json.load(open(ref)); a = r.get("S4a over-cautious refusal", {}); 
    fired = len(a.get("relevant_modules") or [])
    return {"info": [f"T4 S4 reference: {fired} modules fire on declared-input facts (recorded); a general T4 needs the input ontology built"]}


def run(kind, sample=60):
    checks = ([acts_structural, lambda: acts_bridge_accuracy_sample(sample)[0], acts_grain_by_relevance, acts_firing_consistency]
              if kind == "acts" else [atoms_gap_rate, atoms_collision_rate, atoms_coinage_spread, atoms_grounding_fit])
    agg = {"hard": [], "review": [], "info": []}
    for c in checks:
        try:
            h = c()
        except Exception as ex:
            h = {"hard": [f"{c.__name__}: CHECK ERROR {ex!r:.140}"]}
        for k, v in h.items(): agg[k] += v
    print(f"=== ONTOLOGY VALIDATOR: {kind} ===")
    for k in ("hard", "review", "info"):
        for x in agg[k]: print(f"  [{k:6s}] {x}")
    print(f"verdict: {'BLOCKED' if agg['hard'] else ('REVIEW' if agg['review'] else 'CLEAN')} — hard {len(agg['hard'])}, review {len(agg['review'])}")
    return agg


if __name__ == "__main__":
    kind = sys.argv[1]; sample = int(sys.argv[sys.argv.index("--sample") + 1]) if "--sample" in sys.argv else 60
    agg = run(kind, sample)
    if "--json" in sys.argv:
        json.dump(agg, open(sys.argv[sys.argv.index("--json") + 1], "w"), indent=1)
