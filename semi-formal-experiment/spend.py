"""Running API spend, from measured usage.

hard budget for this autonomous session: $7.50 total. Every live path must
append to usage.jsonl via providers.complete_envelope(usage_log=...) or its
own equivalent; anything that does not is invisible here and will make this
number an undercount, so `audit()` reports which artifacts look unlogged.

  .venv/bin/python spend.py                # report
  .venv/bin/python spend.py --check 5.00   # exit 1 if over budget
  .venv/bin/python spend.py --would-cost luna --batches 26   # pre-flight
"""
from __future__ import annotations

import argparse, glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
USAGE = os.path.join(HERE, "usage.jsonl")
BUDGET = 7.50


def prices(path=os.path.join(HERE, "providers.json")):
    """model/provider name -> {in, out, cached_in, write_mult} in $/Mtok.

    `cached_in` is None when the provider's cached-input rate is not known.
    That is a real state, not a zero: `cost_of` then bills cached tokens at
    the FULL input rate and `total()` counts the assumption, because a budget
    that silently assumes a discount is how a hard cap gets passed.
    """
    out = {}
    for p in json.load(open(path)):
        if p.get("price_per_mtok"):
            pin, pout = p["price_per_mtok"]
            rate = {"in": pin, "out": pout,
                    "cached_in": p.get("cached_input_per_mtok"),
                    "write_mult": p.get("cache_write_multiplier", 1.25)}
            out[p["model"]] = rate
            out[p["name"]] = dict(rate)
    return out


def _rate(p):
    """Accept the (in, out) tuple older callers pass, or the full dict."""
    if isinstance(p, dict):
        return {"in": p["in"], "out": p["out"],
                "cached_in": p.get("cached_in"),
                "write_mult": p.get("write_mult", 1.25)}
    return {"in": p[0], "out": p[1], "cached_in": None, "write_mult": 1.25}


def rows(path=USAGE):
    if not os.path.exists(path):
        return []
    out = []
    for line in open(path):
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out


def cost_of(r, px):
    """Cost of one logged call, in dollars.

    Input splits three ways once prompt caching is on, and the three are
    billed at three different rates:

      cached_input_tokens   served from cache   — cheap (typically 0.1x)
      cache_write_tokens    written to cache    — a PREMIUM over input (1.25x)
      the remainder                             — full input rate

    `prompt_tokens` is the TOTAL of all three (providers.py normalizes both
    families to that convention), so this subtracts and never adds.
    """
    p = px.get(r.get("model")) or px.get(r.get("provider"))
    if not p:
        return None
    rate = _rate(p)
    prompt = r.get("prompt_tokens") or 0
    cached = r.get("cached_input_tokens") or 0
    write = r.get("cache_write_tokens") or 0
    uncached = max(prompt - cached - write, 0)
    cached_rate = rate["cached_in"]
    if cached_rate is None:            # unknown => full price, never a guess
        cached_rate = rate["in"]
    return (uncached / 1e6 * rate["in"]
            + cached / 1e6 * cached_rate
            + write / 1e6 * rate["in"] * rate["write_mult"]
            + (r.get("completion_tokens") or 0) / 1e6 * rate["out"])


def total(path=USAGE, px=None):
    px = prices() if px is None else px
    by_model, unpriced, assumed, n = {}, 0, 0, 0
    for r in rows(path):
        c = cost_of(r, px)
        n += 1
        if c is None:
            unpriced += 1
            continue
        cached = r.get("cached_input_tokens") or 0
        p = px.get(r.get("model")) or px.get(r.get("provider"))
        if cached and _rate(p)["cached_in"] is None:
            assumed += 1
        m = r.get("model", "?")
        d = by_model.setdefault(m, {"calls": 0, "in": 0, "out": 0, "cost": 0.0,
                                    "cached_in": 0, "cache_write": 0})
        d["calls"] += 1
        d["in"] += r.get("prompt_tokens") or 0
        d["out"] += r.get("completion_tokens") or 0
        d["cached_in"] += cached
        d["cache_write"] += r.get("cache_write_tokens") or 0
        d["cost"] += c
    return {"by_model": by_model, "calls": n, "unpriced": unpriced,
            "cache_price_assumed": assumed,
            "total": sum(d["cost"] for d in by_model.values())}


def audit():
    """Reconcile live artifacts on disk against usage.jsonl.

    This used to glob paths, never read them, and print "verify their calls
    were logged" — a manual to-do, not a check. That is precisely why
    `extract_section.InstrumentedClient` silently failed to log for six live
    runs: the safety net could not see the hole it existed to catch.

    Now it reads each artifact, extracts the model it ran against, and reports
    any model that produced artifacts but has NO rows in the usage log. That
    is the signature of an unlogged transport path.
    """
    logged = rows()
    logged_models = {r.get("model") for r in logged if r.get("model")}
    seen = {}
    for pat in ("*/extraction_*.json", "*/conflicts_baseline_*.json",
                "extraction_*.json", "annotations*.json", "*_atoms.json"):
        for f in glob.glob(os.path.join(HERE, pat)):
            rel = os.path.relpath(f, HERE)
            try:
                with open(f) as fh:
                    d = json.load(fh)
            except (OSError, json.JSONDecodeError):
                seen.setdefault("<unreadable>", []).append(rel)
                continue
            prov = d.get("provenance") if isinstance(d, dict) else None
            model = (prov or {}).get("model") if isinstance(prov, dict) else None
            model = model or (d.get("model") if isinstance(d, dict) else None)
            seen.setdefault(model or "<unknown>", []).append(rel)

    unlogged = {m: sorted(fs) for m, fs in seen.items()
                if m not in logged_models and not m.startswith("<")}
    return {"usage_rows": len(logged),
            "models_in_log": sorted(logged_models),
            "artifacts_by_model": {m: sorted(fs) for m, fs in sorted(seen.items())},
            "UNLOGGED_MODELS": unlogged}


def would_cost(model, batches, in_tok=6000, out_tok=7000, cached_tok=0):
    """Pre-flight projection. `cached_tok` is the share of `in_tok` that is a
    repeated constant prefix and would be served from cache on every call
    after the first — the single biggest lever on this repo's frontier runs."""
    px = prices()
    p = px.get(model)
    if not p:
        return None
    row = {"model": model, "prompt_tokens": in_tok, "completion_tokens": out_tok,
           "cached_input_tokens": min(cached_tok, in_tok)}
    return batches * cost_of(row, px)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", type=float, default=None)
    ap.add_argument("--would-cost", default=None)
    ap.add_argument("--batches", type=int, default=1)
    ap.add_argument("--in-tok", type=int, default=6000)
    ap.add_argument("--out-tok", type=int, default=7000)
    ap.add_argument("--cached-tok", type=int, default=0,
                    help="how much of --in-tok is a repeated constant prefix")
    a = ap.parse_args()

    if a.would_cost:
        c = would_cost(a.would_cost, a.batches, a.in_tok, a.out_tok,
                       a.cached_tok)
        t = total()["total"]
        if c is None:
            print(f"no price for {a.would_cost!r}"); sys.exit(2)
        print(f"projected: {a.batches} batches on {a.would_cost} = ${c:.3f}")
        print(f"spent so far ${t:.3f} -> after ${t + c:.3f} of ${BUDGET:.2f} "
              f"({100*(t+c)/BUDGET:.0f}%)")
        sys.exit(1 if t + c > BUDGET else 0)

    t = total()
    print(f"{'model':34s} {'calls':>5s} {'in':>9s} {'cached':>9s} "
          f"{'out':>9s} {'cost':>8s}")
    for m, d in sorted(t["by_model"].items(), key=lambda kv: -kv[1]["cost"]):
        print(f"{m:34s} {d['calls']:5d} {d['in']:9d} "
              f"{d.get('cached_in', 0):9d} {d['out']:9d} ${d['cost']:7.3f}")
    print(f"{'TOTAL':34s} {t['calls']:5d} {'':9s} {'':9s} {'':9s} "
          f"${t['total']:7.3f}"
          f"   of ${BUDGET:.2f}  ({100*t['total']/BUDGET:.0f}%)")
    if t["unpriced"]:
        print(f"  !! {t['unpriced']} logged calls had no price entry")
    if t.get("cache_price_assumed"):
        print(f"  !! {t['cache_price_assumed']} calls had cached input but no "
              "cached rate in providers.json — billed at the FULL input rate, "
              "so this total is an OVERSTATEMENT for those rows")
    au = audit()
    print(f"\nusage.jsonl rows: {au['usage_rows']}")
    if au["UNLOGGED_MODELS"]:
        print("\n!! UNLOGGED SPEND — these models produced artifacts but have no "
              "usage rows.\n   Their calls were billed and are NOT in the total above:")
        for m, fs in sorted(au["UNLOGGED_MODELS"].items()):
            print(f"   {m}: {len(fs)} artifact(s) — e.g. {fs[0]}")
    else:
        print("audit: every artifact's model appears in the usage log")
    if a.check is not None and t["total"] > a.check:
        print(f"\nOVER BUDGET: ${t['total']:.3f} > ${a.check:.2f}")
        sys.exit(1)


if __name__ == "__main__":
    main()
