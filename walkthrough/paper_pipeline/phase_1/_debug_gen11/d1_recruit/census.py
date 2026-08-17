"""Can D1 be re-recruited from draws already on disk?  Pure re-analysis, ZERO API spend.

    ../../../../semi-formal-experiment/.venv/bin/python _debug_gen11/d1_recruit/census.py

Run from phase_1/.  Writes _debug_gen11/d1_recruit/census.json and prints the report.

WHAT COUNTS AS AN INDEPENDENT DRAW
  One draw = one clause, translated once, by one model call chain.
  * A run directory contributes AT MOST ONE draw per clause: the FINAL module
    `<clause>.json`.  Repair attempts inside a chain share a transcript, so the
    later attempts see the earlier one and are NOT independent.  We count the
    chain once and record its attempt count.
  * prompt_ab/draws/*.json contributes one draw per record.  ONLY arm A is used:
    arm B is the D1-modified system prompt, so a B draw is a different instrument
    and cannot serve as a stock re-draw.  (As it happens no arm-B draw exists.)

INSTRUMENT KEY.  Two draws are comparable only if the same system prompt and the
same user prompt produced them: key = (system_sha, user_sha).  run.json records
both; the prompt_ab draw records carry both directly.  Draws with the same clause
but a different instrument key are counted separately and reported separately —
they are re-draws of a DIFFERENT question.

The polarity detector is imported from `checks.polarity_mismatches` (10911de) and
never reimplemented; a duck-typed shim carries .asserts/.status/.read_back/.act so
that drafts that would fail full schema validation are still measured.
"""
import os, sys, json, glob, re, math, collections

HERE = os.path.dirname(os.path.abspath(__file__))
P1 = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, P1)
import checks                                                   # noqa: E402

RUNS_GLOB = os.path.join(P1, "resolve_runs/graph_v2/translation_sample/runs/*/")
AB_GLOB = os.path.join(P1, "_debug_gen11/prompt_ab/draws/*.json")
AB_MANIFEST = os.path.join(P1, "_debug_gen11/prompt_ab/manifest.json")
LEGACY_GLOB = os.path.join(P1, "runs/*/")

HARD = {"forbid", "permit", "oblige"}
SOFT = {"prefer"}


# --- shims ------------------------------------------------------------------
class _A:
    def __init__(self, d):
        self.status = d.get("status")
        self.act = d.get("act")
        self.read_back = d.get("read_back")


class _M:
    def __init__(self, obj):
        self.asserts = [_A(a) for a in (obj.get("asserts") or [])
                        if isinstance(a, dict)]


def parse_text(text):
    """The model's raw reply -> dict, same peeling prompt_ab/score.py uses."""
    if not text:
        return None
    c = re.sub(r"```$", "", re.sub(r"^```(?:json)?", "", text.strip()).strip()).strip()
    s, e = c.find("{"), c.rfind("}")
    if s < 0 or e < s:
        return None
    try:
        return json.loads(c[s:e + 1])
    except Exception:
        return None


# --- collection -------------------------------------------------------------
def collect_runs(glob_pat, tag):
    draws = []
    for rd in sorted(glob.glob(glob_pat)):
        run = os.path.basename(rd.rstrip("/"))
        rj = os.path.join(rd, "run.json")
        sys_sha, user_shas = None, {}
        if os.path.exists(rj):
            j = json.load(open(rj))
            sys_sha = j.get("system_sha")
            us = j.get("user_sha")
            if isinstance(us, dict):
                user_shas = us
        for f in sorted(glob.glob(os.path.join(rd, "*.json"))):
            b = os.path.basename(f)
            if b in ("run.json", "concepts.json") or b.endswith(
                    (".transcript.json", ".version.json")):
                continue
            cid = b[:-5]
            try:
                obj = json.load(open(f))
            except Exception:
                continue
            if not isinstance(obj, dict) or "outcome" not in obj:
                continue
            tr = os.path.join(rd, cid + ".transcript.json")
            att = 1
            if os.path.exists(tr):
                try:
                    msgs = json.load(open(tr))
                    att = sum(1 for m in msgs
                              if isinstance(m, dict) and m.get("role") == "assistant")
                except Exception:
                    pass
            draws.append(dict(source=tag, run=run, clause=cid, obj=obj,
                              attempts=max(att, 1),
                              system_sha=sys_sha,
                              user_sha=user_shas.get(cid)))
    return draws


def collect_ab():
    draws = []
    for f in sorted(glob.glob(AB_GLOB)):
        r = json.load(open(f))
        if r.get("arm") != "A":          # arm B is a different system prompt
            continue
        obj = parse_text(r.get("text")) if r.get("ok") else None
        if obj is None:
            draws.append(dict(source="ab", run="prompt_ab", clause=r["clause"],
                              obj=None, attempts=1,
                              system_sha=(r.get("system_sha") or "")[:16],
                              user_sha=r.get("user_sha"),
                              tag=f"{r['exp']}/{r['task_id']}/d{r['draw']}"))
            continue
        draws.append(dict(source="ab", run="prompt_ab", clause=r["clause"],
                          obj=obj, attempts=1,
                          system_sha=(r.get("system_sha") or "")[:16],
                          user_sha=r.get("user_sha"),
                          tag=f"{r['exp']}/{r['task_id']}/d{r['draw']}"))
    return draws


# --- measurement ------------------------------------------------------------
def measure(d):
    obj = d["obj"]
    if obj is None:
        d.update(unparsed=True, trips=None, statuses=None)
        return d
    m = _M(obj)
    hits = checks.polarity_mismatches(m)             # the committed detector
    d["unparsed"] = False
    d["trips"] = len(hits)
    d["hits"] = [{"where": w, "act": a, "phrase": p} for w, a, p in hits]
    d["statuses"] = sorted(collections.Counter(
        a.status for a in m.asserts).items())
    d["status_multiset"] = tuple(sorted(a.status for a in m.asserts if a.status))
    d["act_status"] = {}
    for a in m.asserts:
        if a.act:
            d["act_status"].setdefault(str(a.act), set()).add(a.status)
    d["n_prefer"] = sum(1 for a in m.asserts if a.status in SOFT)
    d["n_hard"] = sum(1 for a in m.asserts if a.status in HARD)
    d["abstained"] = obj.get("outcome") == "abstained"
    return d


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (p, max(0.0, c - h), min(1.0, c + h))


def n_for_power(p1, p0, power=0.80, alpha=0.05):
    """Two-proportion, two-sided, per arm.  Normal approximation."""
    if p1 == p0:
        return None
    z_a, z_b = 1.959963985, 0.8416212336
    pbar = (p1 + p0) / 2
    num = (z_a * math.sqrt(2 * pbar * (1 - pbar))
           + z_b * math.sqrt(p1 * (1 - p1) + p0 * (1 - p0))) ** 2
    return math.ceil(num / (p1 - p0) ** 2)


def main():
    draws = [measure(d) for d in
             collect_runs(RUNS_GLOB, "graph_v2") + collect_ab()]
    legacy = [measure(d) for d in collect_runs(LEGACY_GLOB, "legacy")]

    man = json.load(open(AB_MANIFEST))
    D1 = man["cohorts"]["D1"]

    out = {}
    P = print

    P("=" * 78)
    P("1. MULTI-DRAW CENSUS  (graph_v2 corpus; legacy runs/ reported apart)")
    P("=" * 78)
    by_clause = collections.defaultdict(list)
    for d in draws:
        by_clause[d["clause"]].append(d)
    dist = collections.Counter(len(v) for v in by_clause.values())
    P(f"  draws total                 : {len(draws)}")
    P(f"  distinct clauses            : {len(by_clause)}")
    P("  draws-per-clause distribution (any instrument):")
    for k in sorted(dist):
        P(f"      {k} draw(s): {dist[k]:4d} clauses")
    multi = {c: v for c, v in by_clause.items() if len(v) >= 2}
    P(f"  clauses with >= 2 draws     : {len(multi)}")

    # instrument-identical subsets
    by_inst = collections.defaultdict(list)
    for d in draws:
        by_inst[(d["clause"], d["system_sha"], d["user_sha"])].append(d)
    inst_multi = {k: v for k, v in by_inst.items() if len(v) >= 2 and k[1] and k[2]}
    idist = collections.Counter(len(v) for v in inst_multi.values())
    P(f"  clause x instrument cells with >= 2 draws (same system_sha AND")
    P(f"  same user_sha, i.e. a true re-draw of the same question): {len(inst_multi)}")
    for k in sorted(idist):
        P(f"      {k} draw(s): {idist[k]:4d} cells")

    nmulti_att = sum(1 for d in draws if d["attempts"] > 1)
    P(f"  chains with >1 model attempt (repair): {nmulti_att} of {len(draws)}"
      f" -- counted ONCE each, at the final module")
    P(f"  unparsed draws              : {sum(1 for d in draws if d['unparsed'])}")
    P(f"  legacy runs/ (m-id corpus, disjoint ids): {len(legacy)} draws,"
      f" {len(set(d['clause'] for d in legacy))} clauses,"
      f" {sum(1 for c, v in collections.Counter(d['clause'] for d in legacy).items() if v >= 2)}"
      f" with >=2")

    out["census"] = dict(
        draws=len(draws), clauses=len(by_clause),
        dist={str(k): v for k, v in sorted(dist.items())},
        multi_draw_clauses=len(multi),
        instrument_identical_cells_ge2=len(inst_multi),
        repair_chains=nmulti_att, unparsed=sum(1 for d in draws if d["unparsed"]),
        legacy_draws=len(legacy))

    P("")
    P("=" * 78)
    P("2. POLARITY DETECTOR OVER EVERY DRAW  (checks.polarity_mismatches)")
    P("=" * 78)
    ok = [d for d in draws if not d["unparsed"]]
    tripped = [d for d in ok if d["trips"]]
    P(f"  draws measured              : {len(ok)}")
    P(f"  draws tripping polarity     : {len(tripped)}"
      f"  ({100*len(tripped)/max(len(ok),1):.1f}%)")
    p, lo, hi = wilson(len(tripped), len(ok))
    P(f"  corpus-wide per-draw rate   : {p*100:.2f}%  95% CI [{lo*100:.2f},{hi*100:.2f}]")
    trip_clauses = sorted(set(d["clause"] for d in tripped))
    P(f"  distinct clauses ever tripping: {len(trip_clauses)}")
    out["detector"] = dict(draws_measured=len(ok), draws_tripping=len(tripped),
                           rate=p, ci=[lo, hi],
                           clauses_ever_tripping=trip_clauses)

    P("")
    P("  per-clause trips/draws, every clause that ever tripped:")
    P(f"    {'clause':22s} {'trips/draws':>12s}   runs")
    for c in trip_clauses:
        v = by_clause[c]
        k = sum(1 for d in v if d["trips"])
        rs = ",".join(sorted(set(d.get("tag") or d["run"][:13] for d in v if d["trips"])))
        P(f"    {c:22s} {k:5d}/{len(v):<6d}   {rs}")

    P("")
    P("  the 7 D1 cohort clauses, over ALL draws on disk:")
    d1rows = []
    for c in D1:
        v = by_clause.get(c, [])
        k = sum(1 for d in v if d["trips"])
        d1rows.append((c, k, len(v)))
        P(f"    {c:22s} {k:5d}/{len(v):<6d}")
    out["d1_rows"] = d1rows

    P("")
    P("=" * 78)
    P("3. THE DOUBLE-DRAW RULE:  keep clauses tripping in >= 2 INDEPENDENT draws")
    P("=" * 78)
    cohort = sorted(c for c in by_clause
                    if sum(1 for d in by_clause[c] if d["trips"]) >= 2)
    P(f"  clauses tripping >= 2 times : {len(cohort)}")
    for c in cohort:
        v = by_clause[c]
        P(f"      {c}  {sum(1 for d in v if d['trips'])}/{len(v)}")
    once = [c for c in by_clause if sum(1 for d in by_clause[c] if d["trips"]) == 1]
    P(f"  clauses tripping exactly once: {len(once)}")
    # of the ever-tripping clauses, how many even HAD a second draw?
    had2 = [c for c in trip_clauses if len(by_clause[c]) >= 2]
    P(f"  of the {len(trip_clauses)} ever-tripping clauses, {len(had2)} have >=2 draws"
      f" at all, so {len(had2)} were eligible to be confirmed")
    P("")
    P("  3b. STRICTER FORM OF THE SAME RULE: both trips must come from draws")
    P("      under the SAME instrument (same system_sha and same user_sha), so")
    P("      that 'twice' cannot be an artefact of a prompt edit between runs.")
    strict = sorted(k for k, v in by_inst.items()
                    if sum(1 for d in v if d["trips"]) >= 2)
    for k in strict:
        v = by_inst[k]
        P(f"      {k[0]:22s} sys={k[1]} user={k[2]}"
          f"  {sum(1 for d in v if d['trips'])}/{len(v)}")
    P(f"      strict cohort size: {len(strict)}"
      f"  (clauses: {sorted(set(k[0] for k in strict))})")
    out["cohort"] = cohort
    out["cohort_strict"] = [list(k) for k in strict]
    out["ever_tripping_with_2plus_draws"] = had2

    P("")
    P("=" * 78)
    P("4. CORPUS-LEVEL DESIGN  (power against the MEASURED base rate)")
    P("=" * 78)
    # base rate on draws that contain at least one assert (a clause with no
    # asserts cannot trip, so it is a structural zero and dilutes the rate)
    withasserts = [d for d in ok if d["status_multiset"]]
    ka = sum(1 for d in withasserts if d["trips"])
    pa, la, ha = wilson(ka, len(withasserts))
    P(f"  base rate, all draws                  : {len(tripped)}/{len(ok)} = {p*100:.2f}%")
    P(f"  base rate, draws with >=1 assert      : {ka}/{len(withasserts)} = {pa*100:.2f}%"
      f"  CI [{la*100:.2f},{ha*100:.2f}]")
    withprefer = [d for d in ok if d["n_prefer"]]
    kp, np_ = sum(1 for d in withprefer if d["trips"]), len(withprefer)
    pp, lp, hp = wilson(kp, np_)
    P(f"  base rate, draws emitting >=1 `prefer`: {kp}/{np_} = {pp*100:.2f}%"
      f"  CI [{lp*100:.2f},{hp*100:.2f}]")
    P("")
    P("  N per arm for 80% power, two-sided alpha=.05, against each base rate,")
    P("  for a fix that removes the given FRACTION of the defect:")
    for label, base in (("all draws", p), ("draws with asserts", pa),
                        ("draws with a `prefer`", pp)):
        row = []
        for frac in (1.0, 0.75, 0.5):
            n = n_for_power(base * (1 - frac), base)
            row.append(f"{int(frac*100)}%->N={n}")
        P(f"    {label:24s} p0={base*100:5.2f}%   " + "   ".join(row))
    out["power"] = dict(base_all=p, base_asserts=pa, base_prefer=pp,
                        n_all=[n_for_power(p * (1 - f), p) for f in (1.0, .75, .5)],
                        n_asserts=[n_for_power(pa * (1 - f), pa) for f in (1.0, .75, .5)],
                        n_prefer=[n_for_power(pp * (1 - f), pp) for f in (1.0, .75, .5)])

    P("")
    P("  4b. DOCUMENT-SIDE ENRICHMENT (the only legitimate way to raise the base")
    P("      rate: selecting on the CLAUSE TEXT is arm-independent; selecting on")
    P("      whether the draw emitted a `prefer` is NOT -- arm B changes that.)")
    corpus = json.load(open(os.path.join(P1, "resolve_runs/graph_v2/node_corpus_all.json")))
    recs = corpus["clauses"] if isinstance(corpus, dict) else corpus
    text = {r["id"]: r.get("quote", "") for r in recs}
    AVOID = ("avoid", "rather than", "instead of", "should not", "shouldn't",
             "must not", "refrain", "discourag", "better to", "prefer",
             "bad example", "not ideal", "unnecessar", "excessiv", "overly",
             "too much", "err on the side")

    def enriched(cid):
        t = text.get(cid, "").lower()
        return any(k in t for k in AVOID)

    n_en = sum(1 for r in recs if enriched(r["id"]))
    P(f"      corpus clauses matching the avoidance/comparative filter:"
      f" {n_en}/{len(recs)} = {100*n_en/len(recs):.1f}%")
    dr_en = [d for d in ok if enriched(d["clause"])]
    dr_no = [d for d in ok if not enriched(d["clause"])]
    ke, kn = sum(1 for d in dr_en if d["trips"]), sum(1 for d in dr_no if d["trips"])
    pe, le, he = wilson(ke, len(dr_en))
    pn, ln_, hn = wilson(kn, len(dr_no))
    P(f"      trip rate INSIDE  filter: {ke}/{len(dr_en)} = {pe*100:5.2f}%"
      f"  CI [{le*100:.2f},{he*100:.2f}]")
    P(f"      trip rate OUTSIDE filter: {kn}/{len(dr_no)} = {pn*100:5.2f}%"
      f"  CI [{ln_*100:.2f},{hn*100:.2f}]")
    hit8 = [c for c in trip_clauses if enriched(c)]
    P(f"      of the {len(trip_clauses)} ever-tripping clauses the filter catches"
      f" {len(hit8)}")
    if pe:
        P("      N per arm at the enriched rate: "
          + "   ".join(f"{int(f*100)}%->N={n_for_power(pe*(1-f), pe)}"
                       for f in (1.0, 0.75, 0.5)))
    out["enrichment"] = dict(filter_hits=n_en, corpus=len(recs),
                             inside=[ke, len(dr_en)], outside=[kn, len(dr_no)],
                             rate_inside=pe, rate_outside=pn,
                             ever_tripping_caught=len(hit8))

    P("")
    P("  4c. THE 4-CLAUSE RE-RECRUITED COHORT AS AN A/B (its own base rate)")
    cv = [d for d in ok if d["clause"] in cohort]
    kc = sum(1 for d in cv if d["trips"])
    pc, lc, hc = wilson(kc, len(cv))
    P(f"      pooled arm-A rate on the 4 cohort clauses: {kc}/{len(cv)}"
      f" = {pc*100:.1f}%  CI [{lc*100:.1f},{hc*100:.1f}]")
    P("      ⚠ INFLATED BY SELECTION: these four were chosen BECAUSE they tripped"
      " twice.")
    P("        Treat as an upper bound; the honest planning figure is the lower CI.")
    for label, base in (("point est.", pc), ("lower 95% CI", lc)):
        P(f"      N draws per arm, {label} p0={base*100:.1f}%: "
          + "   ".join(f"{int(f*100)}%->N={n_for_power(base*(1-f), base)}"
                       for f in (1.0, 0.75, 0.5)))
    out["cohort4"] = dict(trips=kc, draws=len(cv), rate=pc, ci=[lc, hc])

    P("")
    P("=" * 78)
    P("5. STATUS-SELECTION INSTABILITY on the multi-draw population")
    P("=" * 78)

    def instability(cells, name):
        n_cells = 0
        n_unstable_multiset = 0
        n_act_pairs = 0
        n_act_disagree = 0
        n_hardsoft = 0
        examples = []
        for key, v in cells.items():
            v = [d for d in v if not d["unparsed"]]
            if len(v) < 2:
                continue
            n_cells += 1
            ms = set(d["status_multiset"] for d in v)
            if len(ms) > 1:
                n_unstable_multiset += 1
            # hard vs soft vs none, per draw
            def shape(d):
                if d["n_hard"] and d["n_prefer"]:
                    return "mixed"
                if d["n_hard"]:
                    return "hard"
                if d["n_prefer"]:
                    return "prefer"
                return "none"
            if len(set(shape(d) for d in v)) > 1:
                n_hardsoft += 1
            # same act string, different status
            acts = collections.defaultdict(set)
            for d in v:
                for a, ss in d["act_status"].items():
                    acts[a] |= ss
            for a, ss in acts.items():
                seen = sum(1 for d in v if a in d["act_status"])
                if seen < 2:
                    continue
                n_act_pairs += 1
                if len(ss) > 1:
                    n_act_disagree += 1
                    if len(examples) < 12:
                        examples.append((key[0] if isinstance(key, tuple) else key,
                                         a, sorted(ss)))
        P(f"  -- {name}: {n_cells} cells with >=2 parsed draws")
        if n_cells:
            for k, lab in ((n_unstable_multiset, "status MULTISET differs across draws"),
                           (n_hardsoft, "deontic SHAPE differs (hard / prefer / none)")):
                q, l2, h2 = wilson(k, n_cells)
                P(f"     {lab:44s} {k:4d}/{n_cells:<4d} = {q*100:5.1f}%"
                  f" CI [{l2*100:4.1f},{h2*100:5.1f}]")
        if n_act_pairs:
            q, l2, h2 = wilson(n_act_disagree, n_act_pairs)
            P(f"     {'SAME act name, different status':44s}"
              f" {n_act_disagree:4d}/{n_act_pairs:<4d} = {q*100:5.1f}%"
              f" CI [{l2*100:4.1f},{h2*100:5.1f}]")
        else:
            P("     SAME act name, different status: no act name recurs across draws")
        for e in examples:
            P(f"       e.g. {e[0]}  act={e[1]}  statuses={e[2]}")
        return dict(cells=n_cells, multiset_unstable=n_unstable_multiset,
                    shape_unstable=n_hardsoft, act_pairs=n_act_pairs,
                    act_disagree=n_act_disagree)

    out["instability_any"] = instability(
        {c: v for c, v in by_clause.items() if len(v) >= 2},
        "any two draws of the same clause (instrument may differ)")
    P("")
    out["instability_same_instrument"] = instability(
        inst_multi, "instrument-identical re-draws only (same system+user sha)")

    P("")
    P("  act-name recurrence is the weak link above; the shape measure does not")
    P("  depend on act naming and is the one to quote.")

    json.dump(out, open(os.path.join(HERE, "census.json"), "w"),
              indent=1, default=str)
    P("")
    P(f"  wrote {os.path.join(HERE, 'census.json')}")


if __name__ == "__main__":
    main()
