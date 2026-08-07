"""Run each relevance encoding and score it against the frozen judge panel.

    semi-formal-experiment/.venv/bin/python walkthrough/deontic_probe/run.py

No model call. Reads the panel through `panel_universe.load_universe`, which is
the reconstruction of the full 589-passage universe the judges actually saw.
"""
import os, re, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
MVP = os.path.abspath(os.path.join(HERE, "..", "..", "semi-formal-experiment"))
sys.path.insert(0, MVP)
import clingo  # the repo venv ships the module, not the binary

# ---- the 24 hand-encoded passages, joined to their panel locators ---------
# atom  ->  locator suffix.  The panel score is looked up, never hardcoded.
PASSAGE_LOCATOR = {
    "p_overview4":    "#overview > ¶4",
    "p_redline2":     "#red_line_principles > ¶2",
    "p_prohibited1":  "#prohibited_content > ¶1",
    "p_prohibited2":  "#prohibited_content > ¶2",
    "p_disallowed1":  "#disallowed_content > ¶1",
    "p_restricted1":  "#restricted_content > ¶1",
    "p_transf1":      "#transformation_exception > ¶1",
    "p_transf2":      "#transformation_exception > ¶2",
    "p_transf5":      "#transformation_exception > ¶5",
    "p_sidefx13":     "#control_side_effects > ¶13",
    "p_sidefx10":     "#control_side_effects > ¶10",
    "p_risk4":        "#risk_taxonomy > ¶4",
    "p_authority1":   "#levels_of_authority > ¶1",
    "p_stayinbounds1":"#stay_in_bounds > ¶1",
    "p_abi14":        "#assume_best_intentions > ¶14",
    "p_abi13":        "#assume_best_intentions > ¶13",
    "p_abuse3":       "#avoid_abuse > ¶3",
    "p_priv4":        "#protect_privileged_information > ¶4",
    "p_imminent5":    "#prevent_imminent_harm > ¶5",
    "p_unc29":        "#express_uncertainty > ¶29",
    "p_prof4":        "#be_professional > ¶4",
    "p_fmt3":         "#formatting > ¶3",
    "p_voice4":       "#adapt_length_in_voice_mode > ¶4",
    "p_overstep4":    "#avoid_overstepping > ¶4",
}
# p_abuse_head is scaffolding for p_abuse3's example link, not a sampled passage.
SCAFFOLD = {"p_abuse_head"}

BEH_KEY = {"harm3p": "harm-avoidance-to-third-parties",
           "help": "helpfulness",
           "caution": "avoiding-over-and-under-caution"}


def panel_scores(beh):
    import panel_universe as pu
    u = pu.load_universe(spec_keys=("openai",))
    ps = u[BEH_KEY[beh]]["coverage"]["openai"]["passages"]
    out = {}
    for atom, suf in PASSAGE_LOCATOR.items():
        hit = [p for p in ps if p["locator"].endswith(suf)]
        if len(hit) != 1:
            raise SystemExit(f"locator join failed for {atom}: {len(hit)} matches")
        out[atom] = (hit[0]["score"], hit[0]["verdicts"])
    return out


def solve(files, consts):
    args = [f"-c{k}={v}" for k, v in consts.items()] + ["--warn=none"]
    ctl = clingo.Control(args)
    for f in files:
        ctl.load(os.path.join(HERE, f))
    ctl.ground([("base", [])])
    atoms = set()
    found = []
    with ctl.solve(yield_=True) as h:
        for m in h:
            found.append(True)
            atoms |= {str(s) for s in m.symbols(shown=True)}
    if not found:
        raise SystemExit(f"UNSATISFIABLE: {files} {consts}")
    return atoms


BASE = ["kernel.lp", "passages.lp", "behaviours.lp"]


def predict(enc, beh, variant="a", onto="on"):
    """-> set of passage atoms the encoding calls relevant."""
    if enc in ("e3", "e3r"):
        mode = "reasoned" if enc == "e3r" else "plain"
        base = {a for a in solve(BASE + ["e3_difference.lp"],
                                 {"beh": beh, "e3": mode, "onto": onto})
                if a.startswith("surface(")}
        rel = set()
        for p in PASSAGE_LOCATOR:
            without = {a for a in solve(BASE + ["e3_difference.lp"],
                                        {"beh": beh, "e3": mode, "drop": p,
                                         "onto": onto})
                       if a.startswith("surface(")}
            if without != base:
                rel.add(p)
        return rel
    f = {"e1": "e1_engagement.lp", "e2": "e2_applicability.lp",
         "e4": "e4_defeat.lp", "e5": "e5_violation.lp"}[enc]
    consts = {"beh": beh, "onto": onto}
    if enc == "e1":
        consts["variant"] = variant
    atoms = solve(BASE + [f], consts)
    rel = set()
    for a in atoms:
        m = re.match(r"relevant\((\w+),", a)
        if m and m.group(1) not in SCAFFOLD:
            rel.add(m.group(1))
    return rel


def report(name, pred, scores, thresh=3):
    tp = fp = fn = tn = 0
    misses, falses = [], []
    for p, (s, v) in sorted(scores.items(), key=lambda kv: -kv[1][0]):
        gold = s >= thresh
        got = p in pred
        if got and gold: tp += 1
        elif got: fp += 1; falses.append((p, s, v))
        elif gold: fn += 1; misses.append((p, s, v))
        else: tn += 1
    print(f"--- {name}   TP={tp} FP={fp} FN={fn} TN={tn}"
          f"   prec={tp/max(tp+fp,1):.2f} rec={tp/max(tp+fn,1):.2f}")
    print("    PREDICTED: " + " ".join(sorted(pred)))
    if misses:
        print("    MISSED (panel-relevant, encoding says no):")
        for p, s, v in misses:
            print(f"      {p:16s} score {s}  {v}")
    if falses:
        print("    FALSE POSITIVE (panel says no, encoding says yes):")
        for p, s, v in falses:
            print(f"      {p:16s} score {s}  {v}")
    print()
    return tp, fp, fn, tn


if __name__ == "__main__":
    beh = sys.argv[1] if len(sys.argv) > 1 else "harm3p"
    scores = panel_scores(beh)
    print(f"===== behaviour: {beh} ({BEH_KEY[beh]}) =====")
    print(f"panel bands over the 24 hand-encoded passages: "
          f"{collections.Counter('core' if s >= 5 else ('mid' if s >= 1 else 'zero') for s, _ in scores.values())}\n")
    for name, enc, var in (
        ("E1a act-engagement, seeds only          ", "e1", "a"),
        ("E1b act-engagement + in_scope (ontology)", "e1", "b"),
        ("E2  norm applicability                  ", "e2", "a"),
        ("E3  deontic non-vacuity (plain surface)  ", "e3", "a"),
        ("E3r deontic non-vacuity (reasoned surface)", "e3r", "a"),
        ("E4  defeat reachability                 ", "e4", "a"),
        ("E5  violation / contrary-to-duty        ", "e5", "a"),
    ):
        report(name, predict(enc, beh, var), scores)
    # the union: best case for the deontic family as a whole
    allp = set()
    for enc, var in (("e1", "b"), ("e2", "a"), ("e3", "a"), ("e3r", "a"),
                     ("e4", "a"), ("e5", "a")):
        allp |= predict(enc, beh, var)
    report("UNION of E1b,E2,E3,E3r,E4,E5            ", allp, scores)

    # ⭐ ONTOLOGY ABLATION: same encodings, act-classification block removed.
    print("===== ontology ablated (-c onto=off): what the DEONTIC layer alone yields =====")
    for name, enc, var in (
        ("E1b act-engagement + in_scope [no ontology]", "e1", "b"),
        ("E2  norm applicability      [no ontology]", "e2", "a"),
        ("E4  defeat reachability     [no ontology]", "e4", "a"),
        ("E5  violation / CTD         [no ontology]", "e5", "a"),
    ):
        pred = predict(enc, beh, var, onto="off")
        print(f"--- {name}: {len(pred)} relevant  {sorted(pred)}")
