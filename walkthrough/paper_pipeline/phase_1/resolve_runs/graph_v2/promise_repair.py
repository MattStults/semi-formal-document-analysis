#!/usr/bin/env python3
"""Promise-repair stage (item A, Matt 2026-08-14; scope extended per the
k3_validity_report + delta_investigation): targeted regeneration of a
run's missing provides exports, in TWO classes:

  (a) PROMISE breaks -- <run>/fixup_queue.json broken_promise items the
      frontier rejected (note: the ds7 first-slice K3 "confirmations" of
      this kind were evidence-free defaults, k3_validity_report; the
      class stands on the division's own recorded promise, not on them);
  (b) UNDER-EXPORT -- the deterministic scan over the root graph's
      danglings (delta_investigation cause 3, ds7's one real defect: 92
      exported provides names vs the golden's 230): a dangling need whose
      establishing content already EXISTS as a node -- establishes-prose
      token overlap >= 0.25 with the need prose, or spans containing the
      name's seeded established_around -- becomes a repair candidate
      aimed at that node, with the SAME must-provide-or-explain redraw
      and the same decline path.

Input: <run>/fixup_queue.json, the run's root_graph.json, and its cached
division/leaf artifacts. For each item:

  1. locate the promised name's seed entry (name + prose +
     established_around) in the responsible division.json;
  2. descend the cached division tree to the LEAF whose span covers
     established_around;
  3. re-dispatch THAT LEAF ONLY (Driver.leaf semantics: the same prompt
     via leaf_dispatch/dispatch_block, the same validators including
     coverage and coinage, PLUS an appended promise instruction and the
     item-B promise-delivery enforcement with its judgment_calls escape
     hatch) into a scratch dir under <run>/promise_repair/;
  4. MERGE mechanically: if the redraw provides the promised name at the
     establishment lines, splice ONLY the new provides entry (and any new
     needs the validator accepted) onto the existing node(s) covering
     those lines in a COPY of the graph -> <run>/root_graph.repaired.json
     (never in place; a provenance note per repair rides in the artifact
     and a summary line in health.jsonl). If the redraw DECLINES (a
     judgment_calls reason naming the seed), the promise is recorded as
     honestly-undeliverable in <run>/promise_repair_report.json.

The danglings computation re-runs after all repairs and the report says
how many needers resolved. The stage is budget-gated up front
(promise_repair.max_cost_usd, default 0.25 -- ~40 leaf redraws at ~$0.002)
and requires --yes: it spends real money.

    python promise_repair.py runs/ds7 --yes
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (PHASE1, HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import translate as T          # noqa: E402
import recurse_driver as R     # noqa: E402

DEFAULT_BUDGET = 0.40    # matches config (re-review 5 + final 1c note)


def _safe(s):
    import re
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", s or "x")


def broken_promises_to_repair(run_dir):
    """The frontier-confirmed queue rows this stage owns."""
    q = json.load(open(os.path.join(run_dir, "fixup_queue.json")))
    return [it for it in q.get("items", [])
            if it.get("kind") == "broken_promise"
            and it.get("verdict") == "reject"]


def _unwind_dir(run_dir, art):
    """health.jsonl's `artifact` field as recorded at build time -- may be
    absolute, run-relative, or the run dir itself."""
    for cand in (art or "", os.path.join(run_dir, art or ""), run_dir):
        if cand and os.path.exists(os.path.join(cand, "division.json")):
            return cand
    return None


def _descend(unwind_dir, line):
    """Descend the cached division tree to the leaf whose span covers
    `line`. Returns ((lo, hi, leaf_wdir, inherited_seeds), None) or
    (None, reason). No model call."""
    d = json.load(open(os.path.join(unwind_dir, "division.json")))
    wdir = unwind_dir
    while True:
        seeds = d.get("seed_vocabulary", [])
        idx = clo = chi = None
        for i, c in enumerate(d.get("children", []), 1):
            sp = c.get("span") if isinstance(c, dict) else None
            if (isinstance(sp, (list, tuple)) and len(sp) == 2
                    and sp[0] <= line <= sp[1]):
                idx, (clo, chi) = i, sp
                break
        if idx is None:
            return None, f"no child span covers line {line} under {wdir}"
        cdir = os.path.join(wdir, f"c{idx}")
        sub = os.path.join(cdir, "division.json")
        if os.path.exists(sub):
            d2 = json.load(open(sub))
            if d2.get("decision") == "divide":
                wdir, d = cdir, d2
                continue
        return (clo, chi, cdir, seeds), None


def locate_leaf(unwind_dir, name):
    """(seed, lo, hi, leaf_wdir, inherited_seeds) for the promised name,
    or (None, reason). Descends cached divisions only -- no model call."""
    d = json.load(open(os.path.join(unwind_dir, "division.json")))
    seed = next((s for s in d.get("seed_vocabulary", [])
                 if isinstance(s, dict) and s.get("name") == name), None)
    ea = (seed or {}).get("established_around")
    if not (isinstance(ea, (list, tuple)) and len(ea) >= 2):
        return None, (f"seed '{name}' has no usable established_around in "
                      f"{unwind_dir}/division.json")
    located, why = _descend(unwind_dir, ea[0])
    if located is None:
        return None, why
    lo, hi, leaf_wdir, seeds = located
    return (seed, lo, hi, leaf_wdir, seeds), None


def _all_division_seeds(run_dir):
    """name -> seed entry, from every cached division.json under the run
    (first wins, the validator's own convention)."""
    import glob
    out = {}
    for p in sorted(glob.glob(os.path.join(run_dir, "**", "division.json"),
                              recursive=True)):
        try:
            for s in json.load(open(p)).get("seed_vocabulary", []):
                if isinstance(s, dict) and s.get("name"):
                    out.setdefault(s["name"], s)
        except Exception:               # noqa: BLE001
            pass
    return out


def _covers(sp, ea, tol=2):
    """Span-coherence test with tolerance (re-review 1c): a span counts as
    covering the establishment when it contains ANY line of [ea0, ea1] or
    sits within +-2 lines of it. Ground: the flagship
    interactive_vs_programmatic case -- seed established_around
    [3384, 3386], the establishing nodes START at 3386; exact-containment
    of ea[0] alone called that infeasible."""
    if not (isinstance(sp, (list, tuple)) and len(sp) == 2
            and isinstance(ea, (list, tuple)) and len(ea) >= 2):
        return False
    return not (sp[1] < ea[0] - tol or sp[0] > ea[1] + tol)


def _node_covers(node, ea, tol=2):
    return any(isinstance(sp, dict)
               and _covers(sp.get("lines"), ea, tol)
               for sp in (node or {}).get("spans", []))


def _select_target(nodes, ea, tol=2):
    """THE ONE splice-target selector (final re-review 1c displacement;
    both the prep feasibility check and splice's promise-class branch
    call this -- the coherence lesson: two selection rules drift).
    Ranking, NEVER graph order:
      1. EXACT-cover nodes first -- a span containing ANY line of
         [ea0, ea1], no tolerance;
      2. only if none exist, the +-2 tolerance fallback;
      3. among matches: maximum line-overlap with [ea0, ea1], then the
         narrowest span.
    Ground (ds7 flagship): ea [3384, 3386] with the adjacent worked-
    example node L3239-3382_n017 (spans to 3382, inside tolerance)
    present must select L3383-3501_n001 -- first-cover-in-graph-order
    displaced the splice onto the neighbour."""
    if not (isinstance(ea, (list, tuple)) and len(ea) >= 2):
        return None
    best_node, best_key = None, None
    for n in nodes:
        for sp in n.get("spans", []):
            ln = sp.get("lines") if isinstance(sp, dict) else None
            if not (isinstance(ln, (list, tuple)) and len(ln) == 2):
                continue
            if not _covers(ln, ea, tol):
                continue
            exact = not (ln[1] < ea[0] or ln[0] > ea[1])
            ov = max(0, min(ln[1], ea[1]) - max(ln[0], ea[0]) + 1)
            key = (1 if exact else 0, ov, -(ln[1] - ln[0]))
            if best_key is None or key > best_key:
                best_key, best_node = key, n
    return best_node


def underexport_candidates(run_dir, g):
    """The deterministic scan (item A extension; delta_investigation
    cause 3 -- ds7's one real defect: 92 exported provides names vs the
    golden's 230, with ~50 of the 64 near-miss danglings naming content
    that EXISTS as nodes with empty provides). For each dangling need:
    the best existing node whose establishes has >= 0.25 token overlap
    with the need prose, or whose spans contain the name's seed
    established_around (when any cached division seeded it). Emits one
    candidate per dangling name."""
    import risk_queue as RQ
    provides = {R.nm(p) for n in g.get("nodes", [])
                for p in n.get("provides", [])}
    seeds = _all_division_seeds(run_dir)
    cands = {}
    for n in g.get("nodes", []):
        for d in n.get("needs", []):
            name = R.nm(d)
            if name in provides or not isinstance(d, dict):
                continue
            if name in cands:
                continue
            prose = d.get("prose", "")
            ea = (seeds.get(name) or {}).get("established_around")
            best, best_sim, via = None, 0.0, None
            for cand in g.get("nodes", []):
                if cand is n:
                    continue
                s = RQ.sim(prose, cand.get("establishes", ""))
                if s >= 0.25 and s > best_sim:
                    best, best_sim, via = cand, s, "establishes-overlap"
                if (best is None and isinstance(ea, (list, tuple))
                        and len(ea) >= 2
                        and any(isinstance(sp, dict)
                                and (sp.get("lines") or [0, -1])[0]
                                <= ea[0]
                                <= (sp.get("lines") or [0, -1])[1]
                                for sp in cand.get("spans", []))):
                    best, via = cand, "established_around"
            if best is None:
                continue
            a = (best.get("spans") or [{}])[0].get("lines") or [None, None]
            if a[0] is None:
                continue
            # re-review 1b (target/ea coherence; 4/23 ds7 candidates
            # incoherent): when the target was picked by establishes
            # OVERLAP, the redraw location derives FROM THE TARGET's own
            # span and the (possibly stale) seed ea is dropped -- never
            # redraw an ea leaf to splice a distant node. Only an
            # ea-picked target (which covers ea by construction) keeps
            # the seed's established_around.
            if via == "establishes-overlap" or not (
                    isinstance(ea, (list, tuple)) and len(ea) >= 2):
                ea_out = [a[0], a[1]]
            else:
                ea_out = list(ea[:2])
            cands[name] = {
                "name": name, "prose": prose, "needer": n.get("id"),
                "target_id": best.get("id"), "via": via,
                "sim": round(best_sim, 3),
                "established_around": ea_out}
    return list(cands.values())


def promise_extra(seed):
    ea = seed["established_around"]
    return (f"\n⚠️ PROMISE REPAIR: the inherited seed '{seed['name']}' "
            f"({seed.get('prose', '')}) is established around lines "
            f"{ea[0]}-{ea[1]} inside your span; if your span genuinely "
            f"establishes it you MUST include a provides entry with "
            f"exactly this name; if it does NOT, say why in "
            f"judgment_calls.")


def redraw_leaf(drv, seed, lo, hi, seeds, scratch_wdir):
    """Driver.leaf semantics, promise-instrumented: same prompt
    construction (leaf_dispatch + dispatch_block), same validators, plus
    the appended instruction and item B's deliver-or-explain enforcement
    scoped to THIS seed."""
    extra, schema, derive = R.leaf_dispatch(lo, hi, drv.cfg)
    extra += promise_extra(seed)
    if not any(isinstance(s, dict) and s.get("name") == seed["name"]
               for s in seeds):
        seeds = list(seeds) + [seed]
    g = drv.call(drv.dispatch_block("L", lo, hi, seeds, extra),
                 lambda o: R.validate_leaf(
                     o, lo, hi, drv.lines, derive_uncovered=derive,
                     seeds=[seed], enforce_promise_delivery=True),
                 schema=schema)
    os.makedirs(scratch_wdir, exist_ok=True)
    R.write_json(os.path.join(scratch_wdir, "graph.json"), g)
    return g


def splice(g, seed, redraw, unwind_art, scratch_wdir, target_id=None):
    """The mechanical merge: ONLY the new provides entry (and any new
    needs the validator accepted on the providing node) reach the graph
    copy. Everything judgmental already happened -- in the redraw.
    `target_id` (the under-export class): the scan already named the
    node that owns the establishment lines."""
    name, ea = seed["name"], seed["established_around"]
    prov_node = prov_entry = None
    for n in redraw.get("nodes", []):
        for p in n.get("provides", []):
            if isinstance(p, dict) and p.get("name") == name:
                prov_node, prov_entry = n, p
                break
        if prov_entry:
            break
    if prov_entry is None:
        # re-review 2-note: word-boundary match, never substring -- a
        # judgment_calls entry naming support_mental_health_rule must not
        # count as a decline of support_mental_health
        reason = next((j for j in redraw.get("judgment_calls", [])
                       if isinstance(j, str)
                       and R.name_mentioned(name, j)),
                      "(declined without a judgment_calls reason -- "
                      "validator accepted the reply, treat as decline)")
        return "declined", reason
    if not _node_covers(prov_node, ea):
        return "failed", (f"redraw provides '{name}' but not at the "
                          f"establishment lines {list(ea[:2])} "
                          f"(+-2 tolerance)")
    if target_id is not None:
        target = next((n for n in g.get("nodes", [])
                       if n.get("id") == target_id), None)
    else:
        target = _select_target(g.get("nodes", []), ea)
    if target is None:
        return "failed", (f"no root-graph node covers the establishment "
                          f"lines {list(ea[:2])}"
                          if target_id is None
                          else f"scan target {target_id!r} vanished from "
                               f"the root graph")
    have_p = {R.nm(p) for p in target.get("provides", [])}
    if name not in have_p:
        target.setdefault("provides", []).append(dict(prov_entry))
    have_n = {R.nm(d) for d in target.get("needs", [])}
    new_needs = [dict(d) for d in prov_node.get("needs", [])
                 if isinstance(d, dict) and d.get("name") not in have_n]
    target.setdefault("needs", []).extend(new_needs)
    g.setdefault("promise_repairs", []).append({
        "name": name, "unwind": unwind_art, "target": target.get("id"),
        "established_around": list(ea[:2]),
        "redraw_artifact": os.path.relpath(scratch_wdir),
        "spliced_needs": [d.get("name") for d in new_needs]})
    g.setdefault("driver_autofixes", []).append(
        f"promise_repair: spliced provides '{name}' onto "
        f"{target.get('id')} from the targeted leaf redraw "
        f"(established_around {list(ea[:2])})")
    return "repaired", target.get("id")


def danglings(g):
    provides = {R.nm(p) for n in g.get("nodes", [])
                for p in n.get("provides", [])}
    return {(n.get("id"), R.nm(d)) for n in g.get("nodes", [])
            for d in n.get("needs", []) if R.nm(d) not in provides}


def run_repair(run_dir, cfg, client, lines):
    """The whole stage. `client` and `lines` are injected: pins run it
    with a MockClient for $0; main() wires the live GraphClient."""
    items = broken_promises_to_repair(run_dir)
    g = json.load(open(os.path.join(run_dir, "root_graph.json")))
    g = json.loads(json.dumps(g))              # NEVER in place
    before = danglings(g)
    scratch_root = os.path.join(run_dir, "promise_repair")
    drv = R.Driver(cfg, client, lines, scratch_root)
    #: names already provided ANYWHERE in the root graph (re-review 1a;
    #: ds7 real case: scope_of_autonomy already provided by L461-608_n002
    #: -- 3/26 queue names were stale): a redraw for these buys nothing
    provided_now = {R.nm(p) for n in g.get("nodes", [])
                    for p in n.get("provides", [])}
    # -- deterministic prep first: locate every leaf, THEN gate, THEN spend
    plans, report_items = [], []
    seen_promise = set()          # re-review 1d: one plan per name, max
    for it in items:
        det = it.get("detail") or {}
        name = det.get("name")
        if name in seen_promise:
            continue              # 1d (chain_of_command_principle x6 ->
        seen_promise.add(name)    #     one plan)
        if name in provided_now:
            report_items.append({"name": name, "unwind": det.get("unwind"),
                                 "class": "promise",
                                 "status": "skipped_already_provided",
                                 "why": "the name is already provided in "
                                        "the root graph (stale queue row)"})
            continue
        udir = _unwind_dir(run_dir, det.get("unwind"))
        if udir is None:
            report_items.append({"name": name, "unwind": det.get("unwind"),
                                 "class": "promise", "status": "failed",
                                 "why": "unwind artifact dir not found"})
            continue
        located, why = locate_leaf(udir, name)
        if located is None:
            report_items.append({"name": name, "unwind": det.get("unwind"),
                                 "class": "promise", "status": "failed",
                                 "why": why})
            continue
        seed, lo, hi, leaf_wdir, seeds = located
        plans.append({"class": "promise", "seed": seed, "lo": lo, "hi": hi,
                      "seeds": seeds, "unwind": det.get("unwind"),
                      "target_id": None,
                      "scratch": os.path.join(scratch_root,
                                              _safe(name))})
    # -- class (b), the under-export scan (item A extension,
    # delta_investigation cause 3): danglings whose establishing content
    # already EXISTS as a node with empty provides get the SAME
    # must-provide-or-explain leaf redraw, aimed at that node's span
    planned = {p["seed"]["name"] for p in plans}
    if os.path.exists(os.path.join(run_dir, "division.json")):
        for c in underexport_candidates(run_dir, g):
            if c["name"] in planned:
                continue                 # the promise class owns this name
            located, why = _descend(run_dir, c["established_around"][0])
            if located is None:
                report_items.append({"name": c["name"],
                                     "class": "underexport",
                                     "status": "failed", "why": why})
                continue
            lo, hi, leaf_wdir, seeds = located
            # a synthetic seed: the dangling's own prose is the promise
            plans.append({"class": "underexport",
                          "seed": {"name": c["name"],
                                   "prose": c["prose"],
                                   "established_around":
                                       c["established_around"]},
                          "lo": lo, "hi": hi, "seeds": seeds,
                          "unwind": f"(scan: {c['via']}, "
                                    f"target {c['target_id']})",
                          "target_id": c["target_id"],
                          "scratch": os.path.join(
                              scratch_root, "underexport_"
                              + _safe(c["name"]))})
    # -- re-review 1c: prep-time splice feasibility, BEFORE spending.
    # Redraw side: the leaf must cover the establishment lines (with the
    # +-2 tolerance) or the redraw can never provide there. Target side:
    # a root-graph node must exist at those lines (the scan's target for
    # class b; any covering node for class a). Infeasible plans become
    # report rows and cost nothing.
    feasible = []
    for p in plans:
        ea = p["seed"]["established_around"]
        if not _covers([p["lo"], p["hi"]], ea):
            report_items.append({"name": p["seed"]["name"],
                                 "class": p["class"],
                                 "unwind": p["unwind"],
                                 "status": "infeasible",
                                 "why": f"redraw leaf [{p['lo']}, "
                                        f"{p['hi']}] does not cover "
                                        f"established_around "
                                        f"{list(ea[:2])} (+-2)"})
            continue
        if p["target_id"] is not None:
            tgt = next((n for n in g.get("nodes", [])
                        if n.get("id") == p["target_id"]), None)
        else:
            tgt = _select_target(g.get("nodes", []), ea)
        if tgt is None:
            report_items.append({"name": p["seed"]["name"],
                                 "class": p["class"],
                                 "unwind": p["unwind"],
                                 "status": "infeasible",
                                 "why": f"no splice target at "
                                        f"{list(ea[:2])} (+-2)"})
            continue
        feasible.append(p)
    plans = feasible
    # -- budget gate BEFORE any call (worst case: full prompt in at the
    # configured rate, the leaf phase cap out; no cache credit).
    # Re-review 5: repair rounds are NOT multiplied into this gate --
    # documented rationale: the gate prices the expected path (one draw
    # per plan); repair-round overruns are backstopped by the MEASURED
    # ceiling main() sets (client.max_cost_usd = the stage budget), which
    # GraphClient/Client._log_usage enforces after every billed call
    # (routing-gap F2), so the stage can never spend past the budget
    # however many repair rounds the draws take.
    budget = float((cfg.get("promise_repair") or {})
                   .get("max_cost_usd", DEFAULT_BUDGET))
    price = cfg.get("price_per_mtok")
    if price and plans:
        pin, pout = price
        cap = cfg.get("phase_max_tokens",
                      R.Driver.PHASE_MAX_TOKENS).get("leaf_graph", 24576)
        worst = 0.0
        for p in plans:
            extra, _sch, _d = R.leaf_dispatch(p["lo"], p["hi"], cfg)
            prompt = drv.dispatch_block("L", p["lo"], p["hi"], p["seeds"],
                                        extra + promise_extra(p["seed"]))
            worst += ((len(drv.brief) + len(prompt)) / 3.5 / 1e6 * pin
                      + cap / 1e6 * pout)
        if worst > budget:
            raise T.CostGateError(
                f"promise repair worst case ${worst:.2f} over "
                f"{len(plans)} leaf redraw(s) exceeds "
                f"promise_repair.max_cost_usd ${budget:.2f}. Repair in "
                f"slices or raise the budget deliberately.")
    # -- spend: one targeted leaf redraw per plan
    n_rep = n_dec = 0
    repaired_names = {"promise": set(), "underexport": set()}
    for p in plans:
        seed = p["seed"]
        try:
            redraw = redraw_leaf(drv, seed, p["lo"], p["hi"], p["seeds"],
                                 p["scratch"])
        except T.Phase1Error as exc:
            report_items.append({"name": seed["name"],
                                 "class": p["class"],
                                 "unwind": p["unwind"], "status": "failed",
                                 "why": f"redraw failed: {exc}"})
            continue
        status, detail = splice(g, seed, redraw, p["unwind"], p["scratch"],
                                target_id=p.get("target_id"))
        n_rep += status == "repaired"
        n_dec += status == "declined"
        if status == "repaired":
            repaired_names[p["class"]].add(seed["name"])
        report_items.append({"name": seed["name"], "class": p["class"],
                             "unwind": p["unwind"],
                             "span": [p["lo"], p["hi"]], "status": status,
                             ("target" if status == "repaired"
                              else "why"): detail})
    after = danglings(g)
    resolved = len(before - after)
    # resolved-needer count PER CLASS (the item's own asked-for number):
    # a before-dangling resolves to a class when its name was repaired by
    # that class's redraws
    by_class = {}
    for cls in ("promise", "underexport"):
        rows = [r for r in report_items if r.get("class") == cls]
        by_class[cls] = {
            "planned": len(rows),
            "repaired": sum(1 for r in rows if r["status"] == "repaired"),
            "declined": sum(1 for r in rows if r["status"] == "declined"),
            "failed": sum(1 for r in rows if r["status"] == "failed"),
            "skipped_already_provided": sum(
                1 for r in rows
                if r["status"] == "skipped_already_provided"),
            "infeasible": sum(1 for r in rows
                              if r["status"] == "infeasible"),
            "needers_resolved": len(
                {(nid, nm) for nid, nm in (before - after)
                 if nm in repaired_names[cls]})}
    n_fail = sum(1 for r in report_items if r["status"] == "failed")
    R.write_json(os.path.join(run_dir, "root_graph.repaired.json"), g)
    report = {"run": run_dir, "items": report_items,
              "repaired": n_rep, "declined_honestly": n_dec,
              "failed": n_fail,
              "by_class": by_class,
              "danglings_before": len(before),
              "danglings_after": len(after),
              "needers_resolved": resolved,
              "spent_usd": round(getattr(client, "spent_usd", 0.0), 6)}
    R.write_json(os.path.join(run_dir, "promise_repair_report.json"),
                 report)
    with open(os.path.join(run_dir, "health.jsonl"), "a") as f:
        f.write(json.dumps({"artifact": "promise_repair",
                            "kind": "promise_repair",
                            "repaired": n_rep, "declined": n_dec,
                            "failed": n_fail,
                            "by_class": {c: by_class[c]["needers_resolved"]
                                         for c in by_class},
                            "needers_resolved": resolved}) + "\n")
    print(f"promise repair: {n_rep} repaired, {n_dec} honestly "
          f"undeliverable, {n_fail} failed; danglings "
          f"{len(before)} -> {len(after)} ({resolved} needer(s) "
          f"resolved: promise "
          f"{by_class['promise']['needers_resolved']}, underexport "
          f"{by_class['underexport']['needers_resolved']}) -> "
          f"root_graph.repaired.json")
    return report


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("run", help="run directory, e.g. runs/ds7")
    ap.add_argument("--config", default=os.path.join(HERE,
                                                     "driver_config.json"))
    ap.add_argument("--yes", action="store_true",
                    help="required: this stage spends real money")
    args = ap.parse_args(argv)
    if not args.yes:
        print("refusing to spend without --yes")
        return 2
    cfg = json.load(open(args.config))
    doc = os.path.join(PHASE1, "..", "..", "..", cfg["doc_path"])
    lines = R.load_doc(doc)
    prov = T.Provider(
        name="promise-repair", kind="openai-compatible",
        model=cfg["model"]["model"], base_url=cfg["model"]["base_url"],
        api_key_env=cfg["model"]["api_key_env"],
        temperature=cfg["model"].get("temperature", 0.0),
        max_tokens=cfg["model"].get("max_tokens", 16384),
        price_per_mtok=cfg["price_per_mtok"])
    client = R.GraphClient(prov, {"model": dict(
        cfg["model"], format_forcing="json_object",
        usage_log=cfg["model"].get("usage_log", "DEFAULT"))})
    client.max_cost_usd = float((cfg.get("promise_repair") or {})
                                .get("max_cost_usd", DEFAULT_BUDGET))
    try:
        run_repair(args.run, cfg, client, lines)
    except T.Phase1Error as exc:
        print(f"⛔ {type(exc).__name__}: {exc}")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
