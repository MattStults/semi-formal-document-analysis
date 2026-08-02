"""Re-derive the ladder's cost table WITH prompt caching on.

    .venv/bin/python ladder_cost_cached.py

Derived the same way `ladder.estimate_cost` derives the uncached table, and
from the same inputs, so the two are comparable line for line:

  * the prompts are BUILT, exactly as a live run would build them, and their
    characters counted — nothing is assumed about prompt size;
  * chars/token and the completion-token profile come from
    `ladder.calibrate_chars_per_token()` and `ladder.measured_output_profile()`,
    i.e. from this repo's own logged calls;
  * dollars come from `spend.cost_of` against `providers.json`, so the number
    here and the number the budget tracker will report after the run are
    produced by ONE pricing function. A separate cost model in the projection
    is how a run comes in at a price nobody predicted.

Four corrections to `ladder.estimate_cost`'s `$ cached` column, all in the
CONSERVATIVE direction except the third:

  1. THE FIRST CALL IS A MISS. A cache has to be written before it can be
     read. ladder credits the discount to all N calls; this credits it to
     N-1 and bills call one at full input price.
  2. MINIMUM CACHEABLE PREFIX. Below ~1024 tokens a prefix silently does not
     cache at all. Checked per group, and a group that fails it gets no
     discount.
  3. THE JUDGE CALLS CACHE TOO. ladder counts a shared prefix only across
     ANNOTATION prompts; the fidelity/control batches share their system
     prompt as well. That is a real saving ladder's column omits.
  4. THE RATE IS THE CONFIGURED ONE, not a hardcoded 0.1. `providers.json`
     carries a per-model `cached_input_per_mtok`, and if a model has none,
     `spend.cost_of` bills its cached tokens at FULL price rather than
     inventing a discount.

ASSUMPTIONS, all load-bearing, none measured on this account:

  A. The cached rate itself (`cached_input_per_mtok`, currently 0.1x input).
     Every cached-column dollar scales linearly with it.
  B. Cache residency. OpenAI's prefix cache is evicted after a few minutes of
     inactivity on a prefix. This assumes the ~150 calls of a rung run close
     enough together to stay warm. A rung run in stop-start fashion, or
     interleaved with another prefix, pays extra misses. Re-running rung by
     rung back-to-back is the cheap operating discipline.
  C. Automatic caching charges no write premium (true for OpenAI-style
     prefix caching; Anthropic's 1.25x write premium IS modelled, via
     `cache_write_multiplier`, but no rung here runs on Anthropic).
  D. chars/token 4.59, inherited unchanged from ladder's own calibration.
  E. Output tokens are unaffected by caching. Caching is an INPUT-side
     discount only, so the out-token column is identical to ladder's — which
     is why the floor below is what it is.
"""
from __future__ import annotations

import ladder
import providers
import readback as rb
import spend

BUDGET_REMAINING = 5.98


def _common_prefix_len(strings):
    """Longest byte-identical leading run shared by every string."""
    if not strings:
        return 0
    a, b = min(strings), max(strings)
    i = 0
    while i < len(a) and i < len(b) and a[i] == b[i]:
        i += 1
    return i


def _group(prompts, cpt, provider):
    """Token accounting for one set of prompts that share a cache.

    Returns total input tokens, the part that will be served from cache, and
    why — including the case where the prefix exists but is too short to
    cache, which providers do silently.
    """
    n = len(prompts)
    total_chars = sum(len(p) for p in prompts)
    pre = _common_prefix_len(prompts)
    pre_tok = pre / cpt
    cacheable = n > 1 and providers.prefix_caches(provider, "x" * pre)
    # call 1 writes the cache; calls 2..N read it.
    cached_tok = pre_tok * (n - 1) if cacheable else 0.0
    return {"calls": n, "in_tokens": total_chars / cpt,
            "prefix_tokens": pre_tok, "cached_tokens": cached_tok,
            "cacheable": cacheable}


#: Same arms `ladder.py --cost` prints, so the two tables line up row for row.
ALL_RUNGS = tuple(ladder.RUNGS) + (ladder.NULL_ARM,)


def build(rungs=ALL_RUNGS, models=("luna", "sol"), fidelity_batch=5):
    rows = rb.load_clauses()
    ids = list(ladder.sample(rows))
    vocab = ladder.load_vocabulary()
    ann = rb.load_annotations()
    cal = ladder.calibrate_chars_per_token()
    cpt = cal["chars_per_token"]
    outp = ladder.measured_output_profile()
    blocks = ladder.load_rung_blocks()
    by_id = {r["id"]: r for r in rows}

    per_clause = outp["completion_per_batch"] / outp["clauses_per_batch"]
    content_per_clause = ((outp["completion_per_batch"]
                           - outp["reasoning_per_batch"])
                          / outp["clauses_per_batch"])

    per_rung = {}
    for rung in list(rungs) + ["controls"]:
        prompts, judge = [], []
        if rung == "controls":
            for which in ("positive", "negative"):
                for b in rb._batches(ladder.control_items(ids, rows, which, ann),
                                     fidelity_batch):
                    system, user = ladder.fidelity_prompt(b)
                    judge.append(system + "\n" + user)
        else:
            spec = ladder.rung_spec(rung)
            if spec["annotates"]:
                for cid in ids:
                    system, user = ladder.annotate_prompt_for(
                        by_id[cid], rung, vocab, rows, blocks)
                    prompts.append(system + "\n" + user)
            bc = ({c: ann.get(c, []) for c in ids} if rung == "0"
                  else {c: [] for c in ids})
            for b in rb._batches(ladder.fidelity_items(ids, rows, bc, rung),
                                 fidelity_batch):
                system, user = ladder.fidelity_prompt(b)
                judge.append(system + "\n" + user)
        per_rung[rung] = {
            "prompts": prompts, "judge": judge,
            "out_low": (len(prompts) * per_clause
                        + len(judge) * ladder.JUDGE_COMPLETION_PER_BATCH),
            "out_high": (len(prompts) * (content_per_clause
                                         + outp["reasoning_per_batch"])
                         + len(judge) * ladder.JUDGE_COMPLETION_PER_BATCH),
        }

    px = spend.prices()
    out = {"_calibration": {"chars_per_token": cal, "output": outp}}
    for m in models:
        prov = ladder.provider_for(m)
        out[m] = {"_model": prov.model, "_cache_mode": prov.cache_mode(),
                  "_cached_rate": px.get(prov.model, {}).get("cached_in")}
        for rung, d in per_rung.items():
            # Annotation prompts and judge prompts are two separate caches:
            # different system prompts, so different prefixes.
            groups = [g for g in (_group(d["prompts"], cpt, prov),
                                  _group(d["judge"], cpt, prov)) if g["calls"]]
            in_tok = sum(g["in_tokens"] for g in groups)
            cached = sum(g["cached_tokens"] for g in groups)
            row = {"model": prov.model, "prompt_tokens": in_tok,
                   "cached_input_tokens": cached}
            usd_cached_hi = spend.cost_of(
                dict(row, completion_tokens=d["out_high"]), px)
            usd_cached_lo = spend.cost_of(
                dict(row, completion_tokens=d["out_low"]), px)
            usd_uncached = spend.cost_of(
                {"model": prov.model, "prompt_tokens": in_tok,
                 "completion_tokens": d["out_high"]}, px)
            out[m][rung] = {
                "calls": sum(g["calls"] for g in groups),
                "in_tokens": in_tok, "cached_tokens": cached,
                "cache_share": (cached / in_tok) if in_tok else 0.0,
                "cacheable": all(g["cacheable"] for g in groups),
                "prefix_tokens": [round(g["prefix_tokens"]) for g in groups],
                "out_high": d["out_high"], "out_low": d["out_low"],
                "usd_uncached": usd_uncached,
                "usd": usd_cached_hi, "usd_low": usd_cached_lo,
            }
        out[m]["_total"] = sum(v["usd"] for k, v in out[m].items()
                               if not k.startswith("_"))
        out[m]["_total_low"] = sum(v["usd_low"] for k, v in out[m].items()
                                   if not k.startswith("_"))
        out[m]["_total_uncached"] = sum(v["usd_uncached"] for k, v in out[m].items()
                                        if not k.startswith("_"))
    return out


def report(est):
    cal = est["_calibration"]
    L = ["",
         "LADDER COST WITH PROMPT CACHING ON — prompts built and counted, "
         "priced by spend.cost_of.",
         f"  chars/token {cal['chars_per_token']['chars_per_token']:.2f} "
         f"({cal['chars_per_token']['method']})",
         f"  completion/batch {cal['output']['completion_per_batch']:.0f} tok, "
         f"reasoning {cal['output']['reasoning_per_batch']:.0f}",
         "  $ uncached = today's code (no caching). $ cached = with caching, "
         "reasoning priced per CALL.",
         "  $ floor    = with caching, reasoning priced per CLAUSE (the "
         "optimistic output profile).",
         "  cache% = share of input tokens served from cache (call 1 of each "
         "group is a write, never a read).",
         ""]
    warn = set()
    for m in ("luna", "sol"):
        for rung, d in est.get(m, {}).items():
            if not rung.startswith("_") and not d["cacheable"]:
                warn.update(t for t in d["prefix_tokens"]
                            if t < providers.DEFAULT_MIN_CACHEABLE_TOKENS)
    if warn:
        L.append("  !! at least one prompt group has a shared prefix BELOW the "
                 f"{providers.DEFAULT_MIN_CACHEABLE_TOKENS}-token minimum "
                 f"({sorted(warn)} tok) and therefore does not cache at all —")
        L.append("     that is the judge/fidelity prompt. It is credited NO "
                 "discount here. Lengthening or restructuring it is the one "
                 "cheap win left.")
        L.append("")
    for m in ("luna", "sol"):
        if m not in est:
            continue
        byr = est[m]
        L.append(f"  {m} ({byr['_model']}, cache={byr['_cache_mode']}, "
                 f"cached rate ${byr['_cached_rate']}/Mtok)")
        L.append(f"  {'rung':9s}{'calls':>7s}{'in tok':>11s}{'cache%':>8s}"
                 f"{'out tok':>10s}{'$ uncached':>12s}{'$ cached':>10s}"
                 f"{'$ floor':>9s}")
        for rung, d in byr.items():
            if rung.startswith("_"):
                continue
            L.append(f"  {rung:9s}{d['calls']:>7d}{d['in_tokens']:>11.0f}"
                     f"{100*d['cache_share']:>7.0f}%{d['out_high']:>10.0f}"
                     f"{d['usd_uncached']:>12.3f}{d['usd']:>10.3f}"
                     f"{d['usd_low']:>9.3f}")
        L.append(f"  {'TOTAL':9s}{'':7s}{'':11s}{'':8s}{'':10s}"
                 f"{byr['_total_uncached']:>12.3f}{byr['_total']:>10.3f}"
                 f"{byr['_total_low']:>9.3f}")
        L.append("")
    sol = est.get("sol")
    if sol:
        L.append(f"  BUDGET REMAINING ${BUDGET_REMAINING:.2f}")
        L.append(f"  full ladder on sol, cached:  ${sol['_total']:.2f}"
                 f"  ->  {'FITS' if sol['_total'] <= BUDGET_REMAINING else 'DOES NOT FIT'}")
        r3 = sol.get("3")
        if r3:
            L.append(f"  rung 3 only on sol, cached:  ${r3['usd']:.2f}"
                     f" (floor ${r3['usd_low']:.2f})  ->  "
                     f"{'FITS' if r3['usd'] <= BUDGET_REMAINING else 'DOES NOT FIT'}")
        L.append("")
    return "\n".join(L)


if __name__ == "__main__":
    print(report(build()))
