"""Running API spend, from measured usage.

The hard budget ceiling for this repo is `BUDGET` below — the ONE ceiling
the machine reads (G9 ruling, 2026-08-15: documents quote the constant or
its authorization history, never a second number). Every live path must
append to usage.jsonl via providers.complete_envelope(usage_log=...) or its
own equivalent; anything that does not is invisible here and will make this
number an undercount, so `audit()` reports which artifacts look unlogged.
Rows the price table cannot price are louder still: the report REFUSES its
total and `--check` fails closed, because a partial sum printed as the total
is how $9.20 of spend once read as 24% of cap (G1).

  .venv/bin/python spend.py                # report
  .venv/bin/python spend.py --check 5.00   # exit 1 if over budget OR unpriceable
  .venv/bin/python spend.py --would-cost luna --batches 26   # pre-flight
"""
from __future__ import annotations

import argparse, glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
USAGE = os.path.join(HERE, "usage.jsonl")
#: The machine-read HARD CAP (ladder.preflight() and annotate.py read this).
#: Authorization history — every raise is a recorded decision by Matt, never
#: a workaround for a run that does not fit:
#:   $7.50  original session quote
#:   $8.50  2026-08-02, to cover the grammar-extension annotation pass + its
#:          read-back evaluation after a dry-run showed the original quote
#:          ($0.55) covered only the annotation half
#:   $10.00 2026-08-12, campaign extension (resolve_runs/graph_v2/
#:          EXPERIMENTS.md:1291 "Matt extended the campaign authorization")
#:   $20.00 2026-08-14, "+$5" for the full-corpus translation (EXPERIMENTS.md
#:          "Budget raised to $20.00 (Matt +$5)", ~line 2712)
#: G9 (2026-08-13 review): this constant had fallen behind the live
#: authorization twice; the gauge printed percentages against $8.50 while
#: $9.20 had been spent with authorization to $20. A cap change updates THIS
#: constant and the documents that quote it — nothing else.
BUDGET = 20.00


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
    unpriced_models = {}
    for r in rows(path):
        c = cost_of(r, px)
        n += 1
        if c is None:
            unpriced += 1
            m = r.get("model") or r.get("provider") or "<no model field>"
            unpriced_models[m] = unpriced_models.get(m, 0) + 1
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
            "unpriced_models": unpriced_models,
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


def batch_notes(path=os.path.join(HERE, "providers.json")):
    """model/provider name -> batch-billing caveat, from providers.json DATA.

    A row that carries a `batch_billing_note` was billed through a batch API
    at some point, and its ledger rows may not be distinguishable from
    list-price live rows — the note says so wherever the model's rows appear,
    rather than letting a list-price total read as the actual bill."""
    out = {}
    for p in json.load(open(path)):
        note = p.get("batch_billing_note")
        if note:
            if p.get("model"):
                out[p["model"]] = note
            if p.get("name"):
                out[p["name"]] = note
    return out


def report_lines(path=USAGE, px=None):
    """The gauge, as lines of text.

    ⭐ When ANY logged row has no price entry the total is REFUSED, not
    reported: the sum printed is labeled a PARTIAL subtotal and the unpriced
    models are named. A partial sum printed as the total is the G1 failure —
    the gauge read 24% while the ledger's own arithmetic said over cap.
    """
    t = total(path, px)
    lines = [f"{'model':34s} {'calls':>5s} {'in':>9s} {'cached':>9s} "
             f"{'out':>9s} {'cost':>8s}"]
    for m, d in sorted(t["by_model"].items(), key=lambda kv: -kv[1]["cost"]):
        lines.append(f"{m:34s} {d['calls']:5d} {d['in']:9d} "
                     f"{d.get('cached_in', 0):9d} {d['out']:9d} "
                     f"${d['cost']:7.3f}")
    if t["unpriced"]:
        lines.append(f"{'PRICED SUBTOTAL (PARTIAL)':34s} {t['calls']:5d} "
                     f"{'':9s} {'':9s} {'':9s} ${t['total']:7.3f}")
        lines.append("")
        lines.append(f"⛔ TOTAL REFUSED: {t['unpriced']} of {t['calls']} logged "
                     f"row(s) have no price entry,")
        lines.append("   so the number above is a PARTIAL sum and is NOT the "
                     "spend. Unpriced:")
        for m, n in sorted(t["unpriced_models"].items()):
            lines.append(f"      {m}: {n} row(s)")
        lines.append("   A partial sum printed as the total is how $9.20 of "
                     "spend read as 24% of cap")
        lines.append("   (G1, 2026-08-13 review). Add the missing price(s) to "
                     "providers.json, or")
        lines.append("   accept that this gauge cannot report a total — it "
                     "will keep refusing.")
    else:
        lines.append(f"{'TOTAL':34s} {t['calls']:5d} {'':9s} {'':9s} {'':9s} "
                     f"${t['total']:7.3f}"
                     f"   of ${BUDGET:.2f}  ({100*t['total']/BUDGET:.0f}%)")
    if t.get("cache_price_assumed"):
        lines.append(f"  !! {t['cache_price_assumed']} calls had cached input "
                     "but no cached rate in providers.json — billed at the "
                     "FULL input rate, so this total is an OVERSTATEMENT for "
                     "those rows")
    notes = batch_notes()
    for note in sorted({notes[m] for m in t["by_model"] if m in notes}):
        lines.append("")
        lines.append(f"⚠️  {note}")
    au = audit()
    lines.append("")
    lines.append(f"usage.jsonl rows: {au['usage_rows']}")
    if au["UNLOGGED_MODELS"]:
        lines.append("")
        lines.append("!! UNLOGGED SPEND — these models produced artifacts but "
                     "have no usage rows.")
        lines.append("   Their calls were billed and are NOT in the total "
                     "above:")
        for m, fs in sorted(au["UNLOGGED_MODELS"].items()):
            lines.append(f"   {m}: {len(fs)} artifact(s) — e.g. {fs[0]}")
    else:
        lines.append("audit: every artifact's model appears in the usage log")
    return lines


def run_cli(argv=None, usage_path=USAGE):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", type=float, default=None)
    ap.add_argument("--would-cost", default=None)
    ap.add_argument("--batches", type=int, default=1)
    ap.add_argument("--in-tok", type=int, default=6000)
    ap.add_argument("--out-tok", type=int, default=7000)
    ap.add_argument("--cached-tok", type=int, default=0,
                    help="how much of --in-tok is a repeated constant prefix")
    a = ap.parse_args(argv)

    if a.would_cost:
        c = would_cost(a.would_cost, a.batches, a.in_tok, a.out_tok,
                       a.cached_tok)
        t = total(usage_path)
        if c is None:
            print(f"no price for {a.would_cost!r}")
            return 2
        print(f"projected: {a.batches} batches on {a.would_cost} = ${c:.3f}")
        print(f"spent so far ${t['total']:.3f} -> after "
              f"${t['total'] + c:.3f} of ${BUDGET:.2f} "
              f"({100*(t['total']+c)/BUDGET:.0f}%)")
        if t["unpriced"]:
            print(f"  !! 'spent so far' is a PARTIAL sum: {t['unpriced']} "
                  "logged row(s) have no price entry — the projection may "
                  "understate.")
        return 1 if t["total"] + c > BUDGET else 0

    print("\n".join(report_lines(usage_path)))
    if a.check is not None:
        t = total(usage_path)
        if t["unpriced"]:
            print(f"\nCHECK REFUSED: {t['unpriced']} logged row(s) have no "
                  "price entry, so the gate cannot certify the sum. The "
                  "TOTAL REFUSED block above names them.")
            return 1
        if t["total"] > a.check:
            print(f"\nOVER BUDGET: ${t['total']:.3f} > ${a.check:.2f}")
            return 1
    return 0


def main():
    sys.exit(run_cli())


if __name__ == "__main__":
    main()
