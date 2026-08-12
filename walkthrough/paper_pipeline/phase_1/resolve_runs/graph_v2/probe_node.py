#!/usr/bin/env python3
"""Replay ONE stored graph-build dispatch against DeepSeek, N times, and
compare the answers to the Haiku tree's stored answer (Matt's probe design,
2026-08-10).

The Haiku tree under recurse/ is a fixture library: every directory is a
dispatch whose INPUT is reconstructible (span from the parent's
division.json; inherited seeds = the parent's seed_vocabulary, exactly as
Driver.build threads them) and whose EXPECTED output is the stored
division.json / graph.json. This harness rebuilds the byte-identical
dispatch text via Driver.dispatch_block and samples the model N times,
single-shot (NO repair loop -- a distribution probe wants first-attempt
behavior; an invalid reply is an outcome, not a retry).

Verification is NAME-FREE (GRAPH_EQUIVALENCE.md): invented predicate names
showed ~0% convergence even Haiku-vs-Haiku, so exact match would measure
naming luck. Compared instead:
  Phase D: decision; number of children; CUT POINTS (interior span
           boundaries) vs Haiku's, matched within --tol lines; seed count.
  Phase L: node count; line-coverage agreement (which lines some node owns);
           node-start boundary agreement (+-1); needs/provides totals.
Deviation on a probe is a REPORT, not a verdict: the follow-up (per the
design) is sampling the same dispatch on Haiku a few times to see whether
DeepSeek sits inside Haiku's own run-to-run distribution.

Usage:
  python3 probe_node.py --node root --phase D --n 3 --yes
  python3 probe_node.py --node c1 --phase L --n 3 --yes   # leaf dirs only
Artifacts: probes/<node>_<phase>/sample_*.json + report.json. Free dry run
without --yes prints the reconstruction + cost estimate and stops.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
# translate._resolve_key falls back to semi-formal-experiment/providers.py's
# rc-file parser; make that import resolvable here as translate.py's own
# entry point does
sys.path.append(os.path.abspath(os.path.join(
    HERE, "..", "..", "..", "..", "..", "semi-formal-experiment")))

import recurse_driver as R  # noqa: E402

RECURSE = os.path.join(HERE, "recurse")


def parent_of(node):
    """Flat layout: recurse/c212 is child 2 of c21; c1's parent is root."""
    if node == "root":
        return None, None
    stem, ch = node[:-1], node[-1]
    idx = int(ch) if ch.isdigit() else ord(ch.lower()) - ord("a") + 1
    return (stem if stem not in ("c", "") else "root"), idx


def reconstruct(node):
    """(lo, hi, seeds, lines) exactly as Driver.build threads them."""
    cfg = json.load(open(os.path.join(HERE, "driver_config.json")))
    lines = R.load_doc(os.path.join(
        HERE, "..", "..", "..", "..", "..", "specs", "openai-model-spec",
        "model_spec.md"))
    if node == "root":
        return 1, len(lines), cfg.get("root_seeds", []), lines
    parent, idx = parent_of(node)
    d = json.load(open(os.path.join(RECURSE, parent, "division.json")))
    lo, hi = d["children"][idx - 1]["span"]
    return lo, hi, d.get("seed_vocabulary", []), lines


def cuts_of(division):
    return sorted(c["span"][1] for c in division.get("children", [])[:-1])


def compare_D(sample, expected, tol):
    got, want = cuts_of(sample), cuts_of(expected)
    matched = []
    missed = list(want)
    for w in want:
        hit = [g for g in got if abs(g - w) <= tol]
        if hit:
            matched.append({"expected_cut": w, "got": hit[0]})
            missed.remove(w)
    extra = [g for g in got
             if not any(abs(g - w) <= tol for w in want)]
    return {"decision": sample.get("decision"),
            "n_children": len(sample.get("children", [])),
            "n_children_expected": len(expected.get("children", [])),
            "cuts": got, "cuts_expected": want,
            "cuts_matched": matched, "cuts_missed": missed,
            "cuts_extra": extra,
            "n_seeds": len(sample.get("seed_vocabulary", [])),
            "n_seeds_expected": len(expected.get("seed_vocabulary", []))}


def _owned(graph, lo, hi):
    s = set()
    for n in graph.get("nodes", []):
        for sp in n.get("spans", []):
            s.update(range(sp["lines"][0], sp["lines"][1] + 1))
    return s & set(range(lo, hi + 1))


def compare_L(sample, expected, lo, hi):
    g_own, e_own = _owned(sample, lo, hi), _owned(expected, lo, hi)
    starts = lambda g: {n["spans"][0]["lines"][0]                  # noqa: E731
                        for n in g.get("nodes", []) if n.get("spans")}
    gs, es = starts(sample), starts(expected)
    near = sum(1 for s in es if s in gs or s + 1 in gs or s - 1 in gs)
    deg = lambda g, k: sum(len(n.get(k, [])) for n in g.get("nodes", []))  # noqa: E731
    return {"n_nodes": len(sample.get("nodes", [])),
            "n_nodes_expected": len(expected.get("nodes", [])),
            "coverage_jaccard": round(
                len(g_own & e_own) / max(len(g_own | e_own), 1), 3),
            "boundary_agreement": f"{near}/{len(es)} expected node starts "
                                  f"have a start within +-1 line",
            "needs": deg(sample, "needs"),
            "needs_expected": deg(expected, "needs"),
            "provides": deg(sample, "provides"),
            "provides_expected": deg(expected, "provides")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--node", required=True,
                    help="tree path under recurse/root (e.g. root, c1, c2/c21)")
    ap.add_argument("--phase", choices=["D", "L"], required=True)
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--tol", type=int, default=5)
    ap.add_argument("--max-tokens", type=int, default=None,
                    help="override model.max_tokens for this probe (root "
                         "Phase D burns >16K in hidden reasoning)")
    ap.add_argument("--yes", action="store_true")
    args = ap.parse_args()

    lo, hi, seeds, lines = reconstruct(args.node)
    tdir = os.path.join(RECURSE, args.node)
    art = "division.json" if args.phase == "D" else "graph.json"
    expected = json.load(open(os.path.join(tdir, art)))

    cfg = json.load(open(os.path.join(HERE, "driver_config.json")))
    if args.max_tokens:
        cfg["model"]["max_tokens"] = args.max_tokens
    drv_cfg = {"leaf_max_lines": cfg.get("leaf_max_lines", 200),
               "model": cfg["model"]}
    out = os.path.join(HERE, "probes", f"{args.node.replace('/', '_')}_"
                                       f"{args.phase}")
    os.makedirs(out, exist_ok=True)

    # the dispatch, byte-identical to the driver's (same code path)
    dummy = R.Driver(drv_cfg, R.MockClient([]), lines, out)
    if args.phase == "D":
        extra = ("Reply with the Phase D division.json object "
                 "(decision/children/seed_vocabulary/expected_cross_links/"
                 "judgment_calls). Declaring {\"decision\": \"leaf\"} is "
                 "allowed when the whole span is one cohesive unit.")
        schema = ("division", R.DIVISION_SCHEMA)
        validate = lambda o: R.validate_division(o, lo, hi, seeds)  # noqa: E731
        compare = lambda o: compare_D(o, expected, args.tol)        # noqa: E731
    else:
        extra = ("Reply with the Phase L graph.json object "
                 "(nodes/uncovered/judgment_calls). Node ids are prefixed "
                 f"L{lo}-{hi}_.")
        schema = ("leaf_graph", R.LEAF_SCHEMA)
        validate = lambda o: R.validate_leaf(o, lo, hi, lines)      # noqa: E731
        compare = lambda o: compare_L(o, expected, lo, hi)          # noqa: E731
    user = dummy.dispatch_block(args.phase, lo, hi, seeds, extra)

    est = args.n * (len(dummy.brief) + len(user)) / 4 / 1e6 * \
        cfg["price_per_mtok"][0] + \
        args.n * cfg["model"].get("max_tokens", 16384) / 1e6 * \
        cfg["price_per_mtok"][1]
    print(f"probe {args.node} phase {args.phase}: span {lo}-{hi}, "
          f"{len(seeds)} inherited seeds, expected={art}")
    print(f"worst-case cost for n={args.n}: ${est:.3f} "
          f"(realistic ~10-20% of that)")
    if not args.yes:
        print("dry run (no --yes): dispatch written, nothing sent")
        open(os.path.join(out, "dispatch.txt"), "w").write(user)
        return

    prov = R.T.Provider(
        name="graph-probe", kind="openai-compatible",
        model=cfg["model"]["model"], base_url=cfg["model"]["base_url"],
        api_key_env=cfg["model"]["api_key_env"],
        temperature=cfg["model"].get("temperature", 0.0),
        max_tokens=cfg["model"].get("max_tokens", 16384),
        price_per_mtok=cfg["price_per_mtok"])
    client = R.GraphClient(prov, {"model": dict(
        cfg["model"], format_forcing="json_object",
        usage_log=cfg["model"].get("usage_log", "DEFAULT"))})
    client.max_cost_usd = cfg.get("cost", {}).get("max_cost_usd", 1.0)
    open(os.path.join(out, "dispatch.txt"), "w").write(user)

    report = []
    for i in range(args.n):
        client.reply_schema = schema
        try:
            env = client.complete(dummy.brief, user)
        except R.T.ProviderError as exc:
            # truncation, timeout, transient 5xx: all are OUTCOMES of the
            # probe, not reasons to lose the samples already taken
            report.append({"sample": i, "valid": False,
                           "validation_errors": [f"provider: {exc}"[:200]]})
            print(f"  sample {i}: PROVIDER ERROR -- {str(exc)[:120]}")
            continue
        raw = env["text"]
        open(os.path.join(out, f"sample_{i}.raw.txt"), "w").write(raw)
        try:
            obj = R.parse_json_reply(raw)
            errs = validate(obj)
        except Exception as exc:            # noqa: BLE001
            obj, errs = None, [f"parse failure: {exc!r:.120}"]
        row = {"sample": i, "valid": not errs,
               "validation_errors": [str(e) for e in errs][:8]}
        if obj is not None:
            R.write_json(os.path.join(out, f"sample_{i}.json"), obj)
            row["comparison"] = compare(obj)
        report.append(row)
        print(f"  sample {i}: {'valid' if not errs else 'INVALID'}"
              + (f" -- {json.dumps(row.get('comparison'))[:180]}"
                 if obj else ""))
    R.write_json(os.path.join(out, "report.json"),
                 {"node": args.node, "phase": args.phase, "span": [lo, hi],
                  "n": args.n, "tol": args.tol,
                  "spent_usd": round(getattr(client, "spent_usd", 0.0), 4),
                  "samples": report})
    print(f"spent ${getattr(client, 'spent_usd', 0.0):.4f}; "
          f"report -> {out}/report.json")


if __name__ == "__main__":
    main()
