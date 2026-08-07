"""machine/check_model.py — THE VALIDATOR for the governance model.

The model in `facts.lp` is a hand transcription. A hand transcription is worth
nothing unless something mechanical can catch invention, drift and wishful
paraphrase. Three INDEPENDENT checks do that:

  (a) SOURCE CHECK — every fact carries source(Fact, File, Line) and
      needle(Fact, Text). The file must exist, the line must exist, and the
      needle must actually appear at that line. Catches invention, catches a
      citation that rotted when a file moved, and catches a fact with no
      citation at all.

  (b) DIFFERENTIAL CHECK — the strongest one. cycle.py IS the governance
      machine; the model is only a description of it. So: import cycle.py,
      build synthetic cycle states, and compare the model's allow/refuse
      prediction (machine/semantics.lp) against what the real driver does
      when it is actually driven. Where the driver cannot be driven without
      a full repo (snapshot subprocesses), it is driven with `_run`
      stubbed, so the refusal conditions are still the driver's own.

  (c) KNOWN-ANSWER SET — five facts established by hand about this machine
      that the model must reproduce, listed in the task that commissioned
      the model. A model that gets these wrong is wrong.

RED-FIRST DISCIPLINE (`--self-test`, the pattern from check_rewrite.py): each
check is first shown to FAIL for its own named reason on a deliberately wrong
model — a fabricated source line, a seat mislabelled human, FLIP_BUDGET marked
`derived`, a constant that disagrees with cycle.py. A check that has never
gone red is not a check.

Usage:
    python3 machine/check_model.py
    python3 machine/check_model.py --self-test
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import re
import sys
import tempfile
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

FACTS = os.path.join(HERE, "facts.lp")
SCANNED = os.path.join(HERE, "scanned.lp")
RULES = os.path.join(HERE, "rules.lp")
SEMANTICS = os.path.join(HERE, "semantics.lp")

#: Fact predicates that are bookkeeping, not claims, so they need no source.
NO_SOURCE_NEEDED = {"source", "needle", "scan_excluded"}


# ------------------------------------------------------------- .lp parsing

def _split_facts(text: str):
    """Yield top-level fact strings (predicate applications ending in '.').

    A tiny hand parser: ASP facts here are ground, so we only need to respect
    quoted strings and parenthesis depth. Comment lines start with '%'.
    """
    buf, depth, in_str, esc = [], 0, False, False
    for line in text.splitlines():
        stripped = line.lstrip()
        if not buf and (stripped.startswith("%") or not stripped):
            continue
        if not buf and (stripped.startswith("#") or ":-" in line):
            continue
        for ch in line:
            if in_str:
                buf.append(ch)
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
                buf.append(ch)
            elif ch == "(":
                depth += 1
                buf.append(ch)
            elif ch == ")":
                depth -= 1
                buf.append(ch)
            elif ch == "." and depth == 0:
                fact = "".join(buf).strip()
                buf = []
                if fact:
                    yield fact
            else:
                buf.append(ch)
        if in_str:
            buf.append("\n")


def _predicate(fact: str) -> str:
    m = re.match(r"\s*([a-z_][A-Za-z0-9_]*)", fact)
    return m.group(1) if m else ""


def _args(fact: str):
    """Top-level argument strings of a ground fact, or [] for a 0-ary one."""
    i = fact.find("(")
    if i < 0:
        return []
    body = fact[i + 1:fact.rfind(")")]
    out, buf, depth, in_str, esc = [], [], 0, False, False
    for ch in body:
        if in_str:
            buf.append(ch)
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
            buf.append(ch)
        elif ch == "(":
            depth += 1
            buf.append(ch)
        elif ch == ")":
            depth -= 1
            buf.append(ch)
        elif ch == "," and depth == 0:
            out.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    if buf:
        out.append("".join(buf).strip())
    return out


def _unquote(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        return s[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    return s


def _canon(fact: str) -> str:
    """Whitespace-insensitive key for a fact term."""
    return re.sub(r"\s+", "", fact)


def load_model(extra: str = "") -> dict:
    text = ""
    for p in (FACTS, SCANNED):
        text += open(p, encoding="utf-8").read() + "\n"
    text += extra
    facts, sources, needles = [], {}, {}
    for fact in _split_facts(text):
        pred = _predicate(fact)
        if pred == "source":
            a = _args(fact)
            sources.setdefault(_canon(a[0]), []).append(
                (_unquote(a[1]), int(a[2])))
        elif pred == "needle":
            a = _args(fact)
            needles.setdefault(_canon(a[0]), []).append(_unquote(a[1]))
        elif pred:
            facts.append(fact)
    return {"facts": facts, "sources": sources, "needles": needles,
            "text": text}


# ----------------------------------------------------- (a) SOURCE CHECK

def _norm_text(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    for dash in "‐‑‒–—−":
        s = s.replace(dash, "-")
    return re.sub(r"\s+", " ", s).strip()


_FILE_CACHE: dict = {}


def _file_lines(rel: str):
    if rel not in _FILE_CACHE:
        path = os.path.join(REPO, rel)
        if not os.path.isfile(path):
            _FILE_CACHE[rel] = None
        else:
            _FILE_CACHE[rel] = open(
                path, encoding="utf-8", errors="replace").read().splitlines()
    return _FILE_CACHE[rel]


def source_check(model: dict):
    """Every fact cites a real file:line whose text contains its needle."""
    fails = []
    seen = set()
    for fact in model["facts"]:
        pred = _predicate(fact)
        if pred in NO_SOURCE_NEEDED:
            continue
        key = _canon(fact)
        seen.add(key)
        srcs = model["sources"].get(key)
        nds = model["needles"].get(key)
        if not srcs:
            fails.append(f"unsourced fact (no source/3 companion): {fact[:90]}")
            continue
        if not nds:
            fails.append(f"no needle/2 companion: {fact[:90]}")
            continue
        for rel, line in srcs:
            lines = _file_lines(rel)
            if lines is None:
                fails.append(f"source file does not exist: {rel} "
                             f"(cited by {fact[:60]})")
                continue
            if not (1 <= line <= len(lines)):
                fails.append(
                    f"fabricated source line: {rel}:{line} is past end of "
                    f"file ({len(lines)} lines) (cited by {fact[:60]})")
                continue
            hay = _norm_text(lines[line - 1])
            for nd in nds:
                if _norm_text(nd) not in hay:
                    fails.append(
                        f"needle not found at {rel}:{line}: expected "
                        f"{nd[:60]!r} in {lines[line - 1].strip()[:70]!r}")
    orphans = [k for k in model["sources"] if k not in seen]
    for k in sorted(orphans):
        fails.append(f"source/3 for a fact that does not exist: {k[:80]}")
    return fails


# ------------------------------------------------ (b) DIFFERENTIAL CHECK

def _import_cycle():
    if REPO not in sys.path:
        sys.path.insert(0, REPO)
    import cycle
    return cycle


def _solve(files, extra: str, shows=("refuse", "halt", "override_allowed",
                                     "measure_proceeds", "decide_accepts",
                                     "demotes_to_exploratory")):
    """Ground+solve; return the set of shown atom strings."""
    import clingo
    ctl = clingo.Control(["--warn=none"])
    for f in files:
        ctl.load(f)
    ctl.add("base", [], extra)
    ctl.ground([("base", [])])
    out = set()

    def on_model(m):
        out.clear()
        for sym in m.symbols(shown=True):
            out.add(str(sym))
    ctl.solve(on_model=on_model)
    return out


def _model_predicts(state_lp: str, model_extra: str = ""):
    with tempfile.TemporaryDirectory() as td:
        fpath = os.path.join(td, "extra.lp")
        open(fpath, "w").write(model_extra)
        atoms = _solve([FACTS, SEMANTICS, fpath], state_lp)
    refusals = {a for a in atoms if a.startswith("refuse(")
                or a.startswith("halt(")}
    return atoms, refusals


def _driver_override(cycle, phase: str, override: str, reason):
    """Actually call cycle.py's _override and report refuse/allow."""
    with tempfile.TemporaryDirectory() as td:
        c = cycle.Cycle("t", root=td)
        os.makedirs(c.dir, exist_ok=True)
        phases = cycle.PHASES_BY_SHAPE["checkpoint"]
        completed = list(phases[:phases.index(phase)])
        state = {"cycle": "t", "completed": completed, "overrides": [],
                 "skipped": {}, "closed": False}
        try:
            c._override(state, phase, override, reason)
            return True, ""
        except cycle.CycleError as e:
            return False, str(e)


def _driver_measure(cycle, n_flips: int, plan):
    """Drive _measure with subprocesses stubbed; report halt/proceed."""
    with tempfile.TemporaryDirectory() as td:
        repo = os.path.join(td, "repo")
        snaps = os.path.join(repo, "snapshots")
        os.makedirs(snaps)
        old = (cycle.REPO, cycle.SNAPSHOT_DIR, cycle._run)
        cycle.REPO, cycle.SNAPSHOT_DIR = repo, snaps
        try:
            c = cycle.Cycle("t", root=os.path.join(repo, "cycles"))
            os.makedirs(c.dir)
            manifest = {"cycle_name": "t", "date": "2026-08-06", "shape": "code",
                        "census_scope": "dev", "fix_description": "x",
                        "document_side_rationale": "x", "files_to_change": [],
                        "gate_tests": [], "review_required": False,
                        "baseline_snapshot_tag": "base",
                        "compatibility": {"version_key": "v", "statement": "s"},
                        "config": {"annotations": "a.json", "atoms": "b.json",
                                   "overlay": None, "thresholds": None}}
            cycle._write_json(c._p("manifest.json"), manifest)
            cycle._write_json(os.path.join(snaps, "base.json"), {"tag": "base"})
            flips = {"behaviours": {"beh": {
                "newly_predicted": [{"clause_id": "m%04d" % i}
                                    for i in range(n_flips)],
                "no_longer_predicted": []}}}
            if plan is not None:
                cycle._write_json(c._p("flip_budget_plan.json"), plan)

            def fake_run(argv, cwd=None):
                argv = [str(a) for a in argv]
                if "snapshot" in argv and "--dir" in argv:
                    d = argv[argv.index("--dir") + 1]
                    cycle._write_json(os.path.join(d, "t.json"), {"tag": "t"})
                elif "diff" in argv:
                    cycle._write_json(argv[argv.index("--json") + 1], flips)
                elif "dossiers" in argv:
                    d = argv[argv.index("--out-dir") + 1]
                    os.makedirs(d, exist_ok=True)
                    cycle._write_json(os.path.join(d, "index.jsonl"), [])
                return None
            cycle._run = fake_run
            state = c._state()
            try:
                done, msg = c._measure(state)
                return ("proceed" if done else "halt"), msg
            except cycle.CycleError as e:
                return "refuse", str(e)
        finally:
            cycle.REPO, cycle.SNAPSHOT_DIR, cycle._run = old


def _driver_decide(cycle, decision, signed, justification, exploratory,
                   pred_fail, overridden):
    with tempfile.TemporaryDirectory() as td:
        c = cycle.Cycle("t", root=td)
        os.makedirs(c.dir)
        cycle._write_json(c._p("manifest.json"),
                          {"date": "2026-08-06", "fix_description": "x"})
        cycle._write_json(c._p("decision.json"),
                          {"decision": decision, "signed_by": signed,
                           "justification": justification})
        if pred_fail:
            cycle._write_json(c._p("prediction_check.json"),
                              {"checks": [{"kind": "flip_count",
                                           "result": "FAIL"}],
                               "pass_rate": [0, 1]})
        state = {"cycle": "t", "completed": [], "overrides":
                 ([{"phase": "IMPLEMENT", "reason": "r"}] if overridden else []),
                 "skipped": {}, "closed": False,
                 "exploratory": bool(exploratory)}
        c._save(state)
        try:
            done, msg = c._decide(state)
            return ("accept" if done else "halt"), msg
        except cycle.CycleError as e:
            return "refuse", str(e)


def differential_check(model_extra: str = ""):
    """Compare the model's allow/refuse against cycle.py's own logic."""
    fails, compared = [], 0
    cycle = _import_cycle()

    # ---- 1. constants must equal the driver's, exactly ------------------
    model = load_model(model_extra)
    facts = set(_canon(f) for f in model["facts"])

    def has(f):
        return _canon(f) in facts

    def valueset(pred, arg0=None):
        """Every value the model asserts for a closed-vocabulary predicate."""
        vals = set()
        for f in model["facts"]:
            if _predicate(f) != pred:
                continue
            a = _args(f)
            if arg0 is not None and a[0] != arg0:
                continue
            vals.add(_unquote(a[-1]))
        return vals

    budgets = valueset("constant_int", "flip_budget")
    if budgets != {str(cycle.FLIP_BUDGET)}:
        fails.append(
            f"constant mismatch: cycle.FLIP_BUDGET == {cycle.FLIP_BUDGET} but "
            f"the model asserts constant_int(flip_budget, ...) = "
            f"{sorted(budgets) or 'nothing'}")
    compared += 1

    # Closed vocabularies must match the driver's EXACTLY — an extra member
    # is as wrong as a missing one (it would widen a gate's accepted set).
    for pred, driver_vals, label in (
            ("decision_value", set(cycle.DECISION_VALUES), "DECISION_VALUES"),
            ("direction_value", set(cycle.DIRECTIONS), "DIRECTIONS"),
            ("dev_cell", set(cycle.DEV_CENSUS_CELLS), "DEV_CENSUS_CELLS"),
            ("closure_default", set(cycle.CLOSURE_DEFAULTS),
             "CLOSURE_DEFAULTS")):
        model_vals = valueset(pred)
        if model_vals != driver_vals:
            fails.append(
                f"constant mismatch: {label} is {sorted(driver_vals)} in "
                f"cycle.py; the model asserts {sorted(model_vals)}")
        compared += 1
    for phase in cycle.OVERRIDABLE:
        if not has("overridable(%s)" % phase.lower()):
            fails.append(f"overridability mismatch: cycle.OVERRIDABLE names "
                         f"{phase} but the model does not mark it overridable")
        compared += 1
    model_overridable = {_args(f)[0] for f in model["facts"]
                         if _predicate(f) == "overridable"}
    driver_overridable = {p.lower() for p in cycle.OVERRIDABLE}
    for extra in sorted(model_overridable - driver_overridable):
        fails.append(f"overridability mismatch: the model marks {extra} "
                     f"overridable; cycle.OVERRIDABLE does not")
        compared += 1
    for shape, phases in cycle.PHASES_BY_SHAPE.items():
        for i, p in enumerate(phases, 1):
            if not has("phase_order(%s,%s,%d)" % (shape, p.lower(), i)):
                fails.append(f"phase order mismatch: PHASES_BY_SHAPE[{shape}] "
                             f"has {p} at position {i}; the model does not")
            compared += 1

    # ---- 2. the override matrix, driven for real ------------------------
    phases = cycle.PHASES_BY_SHAPE["checkpoint"]
    for phase in phases:
        for target in phases:
            for reason in ("because", ""):
                allowed, why = _driver_override(cycle, phase, target, reason)
                st = (f"st_phase({phase.lower()}). "
                      f"st_override({target.lower()}). "
                      + ("st_reason. " if reason else ""))
                atoms, refusals = _model_predicts(st, model_extra)
                predicted = "override_allowed" in atoms
                compared += 1
                if predicted != allowed:
                    fails.append(
                        f"override({phase}, --override {target}, reason="
                        f"{reason!r}): driver says "
                        f"{'ALLOW' if allowed else 'REFUSE'}, model says "
                        f"{'ALLOW' if predicted else 'REFUSE'} "
                        f"{sorted(refusals)} / driver: {why[:60]}")

    # ---- 3. the flip budget, driven for real ----------------------------
    plans = [None,
             {"resolution": "stratified_sample", "rationale": "strata"},
             {"resolution": "split", "rationale": "split it"},
             {"resolution": "stratified_sample", "rationale": ""},
             {"resolution": "sample_a_bit", "rationale": "nope"}]
    for n in (0, 1, 29, 30, 31, 34, 60):
        for plan in plans:
            outcome, msg = _driver_measure(cycle, n, plan)
            st = f"st_flips({n}). "
            if plan is not None:
                st += f"st_plan({plan['resolution']}). "
                if plan["rationale"]:
                    st += "st_plan_rationale. "
            atoms, refusals = _model_predicts(st, model_extra)
            predicted = ("proceed" if "measure_proceeds" in atoms
                         else ("refuse" if any(a.startswith("refuse(")
                                               for a in atoms) else "halt"))
            compared += 1
            if predicted != outcome:
                fails.append(
                    f"MEASURE(flips={n}, plan={plan}): driver says {outcome}, "
                    f"model says {predicted} {sorted(refusals)} / driver: "
                    f"{msg.splitlines()[0][:70] if msg else ''}")

    # ---- 4. the DECIDE gates, driven for real ---------------------------
    scen = []
    for decision in ("keep", "revert", "maybe"):
        for signed in ("Matt", ""):
            for just in ("grounds", ""):
                for expl in (False, True):
                    for pf in (False, True):
                        for ov in (False, True):
                            scen.append((decision, signed, just, expl, pf, ov))
    for decision, signed, just, expl, pf, ov in scen:
        outcome, msg = _driver_decide(cycle, decision, signed, just, expl,
                                      pf, ov)
        st = f"st_decision({decision}). "
        st += "st_signed. " if signed else ""
        st += "st_justified. " if just else ""
        st += "st_exploratory. " if expl else ""
        st += "st_pred_fail. " if pf else ""
        st += "st_overridden. " if ov else ""
        atoms, refusals = _model_predicts(st, model_extra)
        predicted = "accept" if "decide_accepts" in atoms else "refuse"
        driver = "accept" if outcome == "accept" else "refuse"
        compared += 1
        if predicted != driver:
            fails.append(
                f"DECIDE(decision={decision!r}, signed={bool(signed)}, "
                f"just={bool(just)}, exploratory={expl}, pred_fail={pf}, "
                f"overridden={ov}): driver says {driver}, model says "
                f"{predicted} {sorted(refusals)} / driver: {msg[:60]}")

    return fails, compared


# ------------------------------------------------ (c) KNOWN-ANSWER SET

def known_answer_check(model_extra: str = ""):
    """Five hand-established answers the model MUST reproduce."""
    model = load_model(model_extra)
    facts = set(_canon(f) for f in model["facts"])

    def has(f):
        return _canon(f) in facts

    fails = []

    # 1. the flip adjudicator is a MODEL seat (haiku-operable), not human.
    if not has("seat_tier(flip_adjudicator,haiku)"):
        fails.append("known-answer 1: the flip adjudicator must be recorded "
                     "haiku-operable")
    if has("seat_tier(flip_adjudicator,human)"):
        fails.append("known-answer 1: the flip adjudicator is a MODEL seat, "
                     "not human — the model labels it human")

    # 2. change_reviewer and decision_signer are per-CYCLE, not per-flip.
    for seat in ("change_reviewer", "decision_signer"):
        if not has(f"seat_scaling_unit({seat},per_cycle)"):
            fails.append(f"known-answer 2: {seat} must scale per_cycle")
        if has(f"seat_scaling_unit({seat},per_flip)"):
            fails.append(f"known-answer 2: {seat} is per-CYCLE, not per-flip "
                         f"— the model says per_flip")

    # 3. FLIP_BUDGET provenance is `chosen`, not `derived`.
    if not has("provenance(flip_budget,chosen)"):
        fails.append("known-answer 3: FLIP_BUDGET provenance must be `chosen`")
    if has("provenance(flip_budget,derived)"):
        fails.append("known-answer 3: FLIP_BUDGET is `chosen` (searched: no "
                     "derivation exists) — the model says `derived`")

    # 4. PREDICT-freeze, ADJUDICATE-validation, DECIDE-signature are
    #    NON-overridable. (PREDICT the PHASE is overridable, but the freeze
    #    gate is not waivable: overriding it demotes the cycle instead.)
    if not has("override_demotes(predict,exploratory)"):
        fails.append("known-answer 4: overriding PREDICT must DEMOTE the "
                     "cycle to exploratory (the freeze is not waivable)")
    if not has("exploratory_refuses_keep"):
        fails.append("known-answer 4: an exploratory cycle must be unable to "
                     "record keep")
    for phase in ("adjudicate", "decide"):
        if has(f"overridable({phase})"):
            fails.append(f"known-answer 4: {phase} must be NON-overridable")

    # 5. the stratified_sample escape validates only a resolution string and
    #    a non-empty rationale; no code draws or verifies the sample.
    if not any(_predicate(f) == "escape_path"
               and _args(f)[0] == "g_flip_budget" for f in model["facts"]):
        fails.append("known-answer 5: the flip-budget gate has a documented "
                     "stratified_sample escape path; the model omits it")
    validated = {_unquote(_args(f)[1]) for f in model["facts"]
                 if _predicate(f) == "escape_validates_only"
                 and _args(f)[0] == "g_flip_budget"}
    if not any("resolution" in v for v in validated):
        fails.append("known-answer 5: the escape validates the resolution "
                     "string; the model does not say so")
    if not any("rationale" in v for v in validated):
        fails.append("known-answer 5: the escape validates a non-empty "
                     "rationale; the model does not say so")
    if not any(_predicate(f) == "escape_unverified"
               and _args(f)[0] == "g_flip_budget" for f in model["facts"]):
        fails.append("known-answer 5: no code draws or verifies the sample — "
                     "the model must record that as unverified")
    return fails


# ------------------------------------------------------- acceptance test

def acceptance_check(model_extra: str = "", scanned: str = SCANNED):
    """The two contradictions the model must SURFACE without being told."""
    with tempfile.TemporaryDirectory() as td:
        fpath = os.path.join(td, "extra.lp")
        open(fpath, "w").write(model_extra)
        atoms = _solve([FACTS, scanned, RULES, fpath], "",
                       shows=("contradiction",))
    fails = []
    if not any('retracted_claim_still_asserted_in_same_file' in a
               and 'section.py' in a for a in atoms):
        fails.append("acceptance 1: section.py's retracted-then-asserted "
                     "claim was not surfaced")
    n = sum(1 for a in atoms
            if a.startswith("contradiction(defensible_verdict_carries_fault_cause"))
    if n != 27:
        fails.append(f"acceptance 2: expected 27 both_defensible verdicts "
                     f"carrying fault-asserting causes, model surfaced {n}")
    return fails, sorted(atoms)


# ---------------------------------------------------------------- driver

def run_all(model_extra: str = "", quiet: bool = False):
    results = {}
    results["source"] = source_check(load_model(model_extra))
    diff_fails, compared = differential_check(model_extra)
    results["differential"] = diff_fails
    results["differential_compared"] = compared
    results["known_answer"] = known_answer_check(model_extra)
    acc_fails, atoms = acceptance_check(model_extra)
    results["acceptance"] = acc_fails
    results["contradictions"] = atoms
    return results


def _report(results) -> int:
    ok = True
    for name, label in (("source", "(a) SOURCE CHECK"),
                        ("differential", "(b) DIFFERENTIAL CHECK vs cycle.py"),
                        ("known_answer", "(c) KNOWN-ANSWER SET"),
                        ("acceptance", "(*) ACCEPTANCE TEST")):
        fails = results[name]
        extra = ""
        if name == "differential":
            extra = f" ({results['differential_compared']} comparisons)"
        if fails:
            ok = False
            print(f"FAIL {label}{extra}: {len(fails)} problem(s)")
            for f in fails[:20]:
                print("   " + f)
            if len(fails) > 20:
                print(f"   ... and {len(fails) - 20} more")
        else:
            print(f"PASS {label}{extra}")
    print(f"\n{len(results['contradictions'])} contradiction(s) reported by "
          f"rules.lp (run `python3 machine/query.py contradictions`)")
    return 0 if ok else 1


# ------------------------------------------------------------ self-test

_RED_CASES = [
    ("fabricated source line", "source",
     'seat(fabricated_seat). source(seat(fabricated_seat),"cycle.py",99999). '
     'needle(seat(fabricated_seat),"nothing").',
     "fabricated source line"),
    ("needle absent from the cited line", "source",
     'driver_runs_git. source(driver_runs_git,"CYCLE_DESIGN.md",254). '
     'needle(driver_runs_git,"The driver ALWAYS runs git").',
     "needle not found"),
    ("fact with no source companion", "source",
     "seat(undocumented_seat).",
     "unsourced fact"),
    ("seat mislabelled human", "known_answer",
     'seat_tier(flip_adjudicator,human). '
     'source(seat_tier(flip_adjudicator,human),"cycle.py",1). '
     'needle(seat_tier(flip_adjudicator,human),"The CYCLE DRIVER").',
     "MODEL seat"),
    ("FLIP_BUDGET marked derived", "known_answer",
     'provenance(flip_budget,derived). '
     'source(provenance(flip_budget,derived),"cycle.py",113). '
     'needle(provenance(flip_budget,derived),"FLIP_BUDGET"). '
     'derivation(flip_budget,"invented"). '
     'source(derivation(flip_budget,"invented"),"cycle.py",113). '
     'needle(derivation(flip_budget,"invented"),"FLIP_BUDGET").',
     "`derived`"),
    ("a per-cycle seat relabelled per-flip", "known_answer",
     'seat_scaling_unit(change_reviewer,per_flip). '
     'source(seat_scaling_unit(change_reviewer,per_flip),"cycle.py",1). '
     'needle(seat_scaling_unit(change_reviewer,per_flip),"The CYCLE DRIVER").',
     "not per-flip"),
    ("a constant that disagrees with cycle.py", "differential",
     'constant_int(flip_budget,50). '
     'source(constant_int(flip_budget,50),"cycle.py",113). '
     'needle(constant_int(flip_budget,50),"FLIP_BUDGET").',
     "constant mismatch"),
    ("a phase wrongly marked overridable", "differential",
     'overridable(decide). source(overridable(decide),"cycle.py",109). '
     'needle(overridable(decide),"OVERRIDABLE").',
     "overridability mismatch"),
]


def _self_test() -> int:
    print("RED — each deliberately wrong model must be REJECTED for its own "
          "named reason:")
    red_ok = True
    for name, check, extra, expect in _RED_CASES:
        if check == "source":
            fails = source_check(load_model(extra))
        elif check == "known_answer":
            fails = known_answer_check(extra)
        else:
            with contextlib.redirect_stdout(io.StringIO()):
                fails, _ = differential_check(extra)
        hit = any(expect in f for f in fails)
        red_ok &= hit
        shown = fails[0][:96] if fails else "ACCEPTED (bug!)"
        for f in fails:
            if expect in f:
                shown = f[:96]
                break
        print(f"  [{'PASS' if hit else 'FAIL'}] {name:38s} -> {shown}")

    # The acceptance test must go red when the scanned evidence is removed:
    # a test that cannot fail is not a test. Two blinded scans, each with one
    # contradiction's evidence deleted, must each be REJECTED.
    print("\nRED — the acceptance test must fail when the scanned evidence "
          "for a known contradiction is removed:")
    scanned_text = open(SCANNED, encoding="utf-8").read().splitlines()
    blinds = [
        ("section.py retraction evidence deleted",
         lambda l: "section.py" not in l or not l.lstrip().startswith(
             ("claim_retracted", "claim_asserted", "source(claim_",
              "needle(claim_")),
         "acceptance 1"),
        ("both_defensible verdict evidence deleted",
         lambda l: not l.lstrip().startswith(
             ("verdict(", "source(verdict(", "needle(verdict(")),
         "acceptance 2"),
    ]
    with tempfile.TemporaryDirectory() as td:
        for name, keep, expect in blinds:
            path = os.path.join(td, name.split()[0] + ".lp")
            open(path, "w").write(
                "\n".join(l for l in scanned_text if keep(l)) + "\n")
            fails, _ = acceptance_check("", scanned=path)
            hit = any(expect in f for f in fails)
            red_ok &= hit
            print(f"  [{'PASS' if hit else 'FAIL'}] {name:44s} -> "
                  f"{(fails[0] if fails else 'ACCEPTED (bug!)')[:70]}")

    print("\nGREEN — the real model must pass all four checks:")
    results = run_all()
    ok = _report(results)
    return 0 if (red_ok and ok == 0) else 1


def main(argv) -> int:
    if "--self-test" in argv:
        return _self_test()
    if "--json" in argv:
        r = run_all()
        r.pop("contradictions", None)
        print(json.dumps({k: v for k, v in r.items()}, indent=1))
        return 0 if not any(r[k] for k in
                            ("source", "differential", "known_answer",
                             "acceptance")) else 1
    return _report(run_all())


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
