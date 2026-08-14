#!/usr/bin/env python3
"""Promise-repair stage (item A, Matt 2026-08-14): targeted regeneration
of a run's frontier-confirmed broken promises.

Input: <run>/fixup_queue.json (the broken_promise items the frontier
REJECTED -- fixup.py routes them here as needing regeneration), the run's
root_graph.json, and its cached division/leaf artifacts. For each broken
promise:

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

DEFAULT_BUDGET = 0.25


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
    wdir = unwind_dir
    while True:
        seeds = d.get("seed_vocabulary", [])
        idx = None
        for i, c in enumerate(d.get("children", []), 1):
            sp = c.get("span") if isinstance(c, dict) else None
            if (isinstance(sp, (list, tuple)) and len(sp) == 2
                    and sp[0] <= ea[0] <= sp[1]):
                idx, (clo, chi) = i, sp
                break
        if idx is None:
            return None, (f"no child span covers established_around "
                          f"{list(ea[:2])} under {wdir}")
        cdir = os.path.join(wdir, f"c{idx}")
        sub = os.path.join(cdir, "division.json")
        if os.path.exists(sub):
            d2 = json.load(open(sub))
            if d2.get("decision") == "divide":
                wdir, d = cdir, d2
                continue
        return (seed, clo, chi, cdir, seeds), None


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


def splice(g, seed, redraw, unwind_art, scratch_wdir):
    """The mechanical merge: ONLY the new provides entry (and any new
    needs the validator accepted on the providing node) reach the graph
    copy. Everything judgmental already happened -- in the redraw."""
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
        reason = next((j for j in redraw.get("judgment_calls", [])
                       if isinstance(j, str) and name in j),
                      "(declined without a judgment_calls reason -- "
                      "validator accepted the reply, treat as decline)")
        return "declined", reason
    if not any(isinstance(sp, dict)
               and (sp.get("lines") or [0, 0])[0] <= ea[0]
               <= (sp.get("lines") or [0, -1])[1]
               for sp in prov_node.get("spans", [])):
        return "failed", (f"redraw provides '{name}' but not at the "
                          f"establishment lines {list(ea[:2])}")
    target = next((n for n in g.get("nodes", [])
                   if any(isinstance(sp, dict)
                          and (sp.get("lines") or [0, 0])[0] <= ea[0]
                          <= (sp.get("lines") or [0, -1])[1]
                          for sp in n.get("spans", []))), None)
    if target is None:
        return "failed", (f"no root-graph node covers the establishment "
                          f"lines {list(ea[:2])}")
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
    # -- deterministic prep first: locate every leaf, THEN gate, THEN spend
    plans, report_items = [], []
    for it in items:
        det = it.get("detail") or {}
        name = det.get("name")
        udir = _unwind_dir(run_dir, det.get("unwind"))
        if udir is None:
            report_items.append({"name": name, "unwind": det.get("unwind"),
                                 "status": "failed",
                                 "why": "unwind artifact dir not found"})
            continue
        located, why = locate_leaf(udir, name)
        if located is None:
            report_items.append({"name": name, "unwind": det.get("unwind"),
                                 "status": "failed", "why": why})
            continue
        seed, lo, hi, leaf_wdir, seeds = located
        plans.append({"seed": seed, "lo": lo, "hi": hi, "seeds": seeds,
                      "unwind": det.get("unwind"),
                      "scratch": os.path.join(scratch_root,
                                              _safe(name))})
    # -- budget gate BEFORE any call (worst case: full prompt in at the
    # configured rate, the leaf phase cap out; no cache credit)
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
    for p in plans:
        seed = p["seed"]
        try:
            redraw = redraw_leaf(drv, seed, p["lo"], p["hi"], p["seeds"],
                                 p["scratch"])
        except T.Phase1Error as exc:
            report_items.append({"name": seed["name"],
                                 "unwind": p["unwind"], "status": "failed",
                                 "why": f"redraw failed: {exc}"})
            continue
        status, detail = splice(g, seed, redraw, p["unwind"], p["scratch"])
        n_rep += status == "repaired"
        n_dec += status == "declined"
        report_items.append({"name": seed["name"], "unwind": p["unwind"],
                             "span": [p["lo"], p["hi"]], "status": status,
                             ("target" if status == "repaired"
                              else "why"): detail})
    after = danglings(g)
    resolved = len(before - after)
    n_fail = sum(1 for r in report_items if r["status"] == "failed")
    R.write_json(os.path.join(run_dir, "root_graph.repaired.json"), g)
    report = {"run": run_dir, "items": report_items,
              "repaired": n_rep, "declined_honestly": n_dec,
              "failed": n_fail,
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
                            "needers_resolved": resolved}) + "\n")
    print(f"promise repair: {n_rep} repaired, {n_dec} honestly "
          f"undeliverable, {n_fail} failed; danglings "
          f"{len(before)} -> {len(after)} ({resolved} needer(s) "
          f"resolved) -> root_graph.repaired.json")
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
