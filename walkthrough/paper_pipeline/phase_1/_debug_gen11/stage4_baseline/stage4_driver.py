#!/usr/bin/env python3
"""stage-4 driver over a GRAPH-NODE translation run.

⭐ WHAT DID NOT EXIST BEFORE THIS FILE. `seats.py` has the whole stage-4
machinery — `plan_clause` builds the four seat prompts, `run_clause` runs
4a–4d then the 4v validate/cross-check/report step — and `seats.judge`
deliberately raises without an explicit `client_factory` ("stage 4 is not
authorised to spend and must be driven through the seam"). What was missing is
the thing that walks a run directory, builds each module's readback from the
blessed node plumbing, and calls them. This is that, and nothing more: it adds
no judgement of its own and rewrites no verdict.

⛔ IT CANNOT SPEND WITHOUT `--live`. Without it there is no client factory at
all, so `judge` raises by construction rather than by a flag check. The
estimate is printed first, every time, and a worst case over `--budget`
REFUSES rather than truncating the run.

⛔ READ-ONLY on the corpus. Nothing here writes to `runs/`,
`translation_sample/runs/` or `repair_graveyard/`; the only writes are under
`--out`.

Usage
-----
    # free: plan every module, price the run, run the free detectors
    PY _debug_gen11/stage4_baseline/stage4_driver.py --dry

    # the same plan, then the seats, gated on the printed worst case
    PY .../stage4_driver.py --live --budget 0.60

    # free: rebuild the baseline from the stored per-clause reports
    PY .../stage4_driver.py --report

Re-runnable: a clause whose report is already on disk is skipped unless
`--force`, so an interrupted live run resumes without re-paying.
"""

import argparse
import dataclasses
import glob
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.abspath(os.path.join(HERE, "..", ".."))
GRAPH_V2 = os.path.join(PHASE1, "resolve_runs", "graph_v2")
WALK = os.path.abspath(os.path.join(PHASE1, "..", ".."))
REPO = os.path.abspath(os.path.join(WALK, ".."))
SFE = os.path.join(REPO, "semi-formal-experiment")

# ⛔ ORDER MATTERS AND IT BIT THE FIRST SMOKE LOUDLY (READBACK_SMOKE.md,
# synthesis 4): `semi-formal-experiment/translate.py` SHADOWS phase_1's. The
# experiment dir goes LAST.
for _p in (PHASE1, GRAPH_V2, WALK):
    if _p not in sys.path:
        sys.path.insert(0, _p)
if SFE not in sys.path:
    sys.path.append(SFE)

import checks                      # noqa: E402
import readback                    # noqa: E402
import schema                      # noqa: E402
import seats                       # noqa: E402
import translate                   # noqa: E402
import link_nodes                  # noqa: E402

DEFAULT_RUN = os.path.join(
    GRAPH_V2, "translation_sample", "runs",
    "20260815-130831-together-deepseek-v4-flash")
DEFAULT_CORPUS = os.path.join(GRAPH_V2, "node_corpus_all.json")
DEFAULT_CONFIG = os.path.join(GRAPH_V2, "config_corpus_all.json")

#: the four verdicts that mean the seat found something wrong
DEFECT_VERDICTS = ("unfaithful", "unlicensed", "not-conveyed", "not-as-meant")

#: severity order for the defect table — most severe first
SEVERITY = {"unlicensed": 0, "unfaithful": 1, "not-as-meant": 2,
            "not-conveyed": 3}


# ==========================================================================
#  gathering — the run directory, matched by ID SHAPE
# ==========================================================================

#: ⛔ `m*.json` was silently blind to the entire graph corpus (seats.survey,
#: fixed 2026-08-15): clause ids are `m0217`, graph node ids are
#: `l1_170_n056`. The same two patterns, and the same sidecar exclusion —
#: `.version.json` and `.transcript.json` are not modules and counting them as
#: invalid inflates the "never reaches a seat" figure this driver reports.
MODULE_GLOBS = ("m*.json", "l*_n*.json")
_SIDECARS = (".version.json", ".transcript.json")


def module_paths(run_dir):
    out = []
    for pat in MODULE_GLOBS:
        for p in glob.glob(os.path.join(run_dir, pat)):
            if p.endswith(_SIDECARS):
                continue
            if os.path.basename(p) in ("run.json", "concepts.json"):
                continue
            out.append(p)
    return sorted(set(out))


def selected_in(run_dir):
    """`link_nodes.gather()`, fenced to ONE run.

    ⭐ WHY NOT `link_nodes.gather()`. It is newest-run-wins across every run
    under `translation_sample/runs/`, so the gloss table and the provider
    spans a seat is shown would come from a MIXTURE of runs. This measurement
    is of one run, and a seat judging run A's module against run B's glosses
    is measuring neither. Fenced here; the cost is that a `requires` whose
    provider node was only ever translated in another run dangles, which the
    Q-22 path already reports honestly as `requires-unsatisfied`.
    """
    selected = {}
    for path in module_paths(run_dir):
        obj = json.load(open(path, encoding="utf-8"))
        if obj.get("outcome") != "translated":
            continue
        lp = path[: -len(".json")] + ".lp"
        if not os.path.isfile(lp):
            continue
        selected[link_nodes.norm_id(obj["clause_id"])] = (lp, obj, run_dir)
    return selected


# ==========================================================================
#  planning — the free half, and everything the live half needs
# ==========================================================================

@dataclasses.dataclass
class Planned:
    clause_id: str
    module: object
    readback: object
    plan: object
    estimate: dict
    polarity: list


@dataclasses.dataclass
class Skipped:
    clause_id: str
    stage: str
    why: str


def build_plans(run_dir, corpus_path, price_per_mtok, chars_per_token=4.0):
    """Every module in `run_dir`, through the blessed node plumbing.

    Returns `(planned, skipped, context)`. NO MODEL CALL happens here.
    """
    selected = selected_in(run_dir)
    texts = link_nodes.node_clause_texts(corpus_path)
    gloss = link_nodes.merged_gloss(selected)
    resolution = link_nodes.requires_resolution(selected)

    planned, skipped = [], []
    for path in module_paths(run_dir):
        obj = json.load(open(path, encoding="utf-8"))
        cid = obj.get("clause_id") or os.path.basename(path)[:-5]
        nid = link_nodes.norm_id(cid)
        if obj.get("outcome") != "translated":
            skipped.append(Skipped(cid, "stage-1",
                                   f"outcome={obj.get('outcome')!r}"))
            continue
        try:
            mod = schema.validate(obj)
        except Exception as exc:                              # noqa: BLE001
            skipped.append(Skipped(cid, "stage-2-invalid", str(exc)[:160]))
            continue
        quote = texts.get(nid)
        if not quote:
            skipped.append(Skipped(cid, "no-clause-text",
                                   f"{nid} is not in {os.path.basename(corpus_path)}"))
            continue
        rb = readback.render_module(mod, extra_gloss=gloss, clause_quote=quote)
        if not seats.proceeds_to_a_seat(rb):
            why = "; ".join(sorted({f.check_id for f in rb.findings
                                    if f.severity == "error"})) or "—"
            skipped.append(Skipped(cid, f"readback:{rb.outcome}", why))
            continue
        xrefs = link_nodes.provider_texts(nid, selected, texts, resolution)
        try:
            plan = seats.plan_clause(
                mod, rb, clause_text=quote, corpus_texts=texts,
                cross_reference_texts=xrefs,
                # node modules cite the SOURCE SPAN, not a `m****` corpus id;
                # `survey()` uses the same relaxation for exactly this reason.
                allow_missing_citations=True)
        except seats.SeatRefused as exc:
            skipped.append(Skipped(cid, "plan-refused", str(exc)[:160]))
            continue
        est = seats.estimate_clause_usd(plan, price_per_mtok, chars_per_token,
                                        seats.SEAT_MAX_TOKENS)
        planned.append(Planned(
            clause_id=cid, module=mod, readback=rb, plan=plan, estimate=est,
            polarity=[dataclasses.asdict(f)
                      for f in checks.polarity_findings(mod)]))
    context = {"run_dir": run_dir, "corpus": corpus_path,
               "modules_on_disk": len(module_paths(run_dir)),
               "translated": len(selected),
               "gloss_names": len(gloss),
               "requires_resolution": {
                   k: v for k, v in resolution.items() if k != "per_module"}}
    return planned, skipped, context


# ==========================================================================
#  cost — printed FIRST, always, and it gates
# ==========================================================================

def cost_summary(planned, price_per_mtok, per_judgement_tokens=40):
    worst = sum(p.estimate["usd"] for p in planned)
    in_tok = sum(p.estimate["input_tokens"] for p in planned)
    judg = sum(sum(len(v) for v in p.plan.ids.values()) for p in planned)
    likely = ((in_tok / 1e6) * price_per_mtok[0]
              + (judg * per_judgement_tokens / 1e6) * price_per_mtok[1])
    return {"clauses": len(planned), "calls": 4 * len(planned),
            "judgements": judg, "input_tokens": in_tok,
            "usd_worst": worst, "usd_likely": likely,
            "price_per_mtok": list(price_per_mtok)}


def render_cost(cs, budget):
    return "\n".join([
        "COST ESTIMATE (printed before anything is sent)",
        f"  clauses reaching a seat : {cs['clauses']}",
        f"  seat calls              : {cs['calls']}  (4 per clause)",
        f"  judgements requested    : {cs['judgements']}",
        f"  input tokens            : {cs['input_tokens']:,}",
        f"  price $/Mtok            : {cs['price_per_mtok']}",
        f"  WORST  (every reply at the {seats.SEAT_MAX_TOKENS}-tok cap)"
        f" : ${cs['usd_worst']:.4f}   <- the number the gate reads",
        f"  likely (40 out-tok/judgement, AN ASSUMPTION)   : "
        f"${cs['usd_likely']:.4f}",
        f"  budget ceiling for this task                   : ${budget:.4f}",
    ])


# ==========================================================================
#  the seam — the client factory READBACK_SMOKE.md gap 2 says nobody owns
# ==========================================================================

class SeatClient:
    """`translate.Client`, adapted to what `seats.judge` calls.

    Three deliberate departures from the stage-1 client, each recorded:
      1. `format_forcing: json_schema -> json_object`. The config's json_schema
         is the stage-1 MODULE schema; forcing it on a seat reply would mangle
         the reply into a module.
      2. `max_tokens -> seats.SEAT_MAX_TOKENS` (4096). A judgement reply is a
         short JSON array, not a module.
      3. `complete_messages` returns an ENVELOPE dict; `judge` wants raw text.
    The measured `usage.cost_usd` is accumulated here so the run can say what
    it actually spent rather than what it estimated.
    """

    def __init__(self, cfg_path, budget_usd, raw_dir=None):
        cfg = translate.load_config(cfg_path)
        cfg = json.loads(json.dumps(cfg))          # a copy; the file is not ours
        cfg["model"]["format_forcing"] = "json_object"
        cfg["model"]["max_tokens"] = seats.SEAT_MAX_TOKENS
        args = argparse.Namespace(provider=None, model=None, max_tokens=None)
        prov = translate.resolve_provider(cfg, args)
        self.prov = prov
        self.client = translate.Client(prov, cfg)
        self.budget = budget_usd
        self.spent = 0.0
        self.calls = 0
        #: ⭐ EVERY REPLY IS KEPT, INCLUDING THE ONES THAT FAIL ADJUDICATION.
        #: `judge` raises inside `validate_judgements`, so a refused reply is
        #: otherwise destroyed by the exception — and a refusal rate is only
        #: readable if the refused replies survive to be read.
        self.raw_dir = raw_dir
        self.tag = None
        if raw_dir:
            os.makedirs(raw_dir, exist_ok=True)

    def complete_messages(self, system, messages):
        if self.spent > self.budget:
            raise seats.SeatRefused(
                f"measured spend ${self.spent:.4f} is over the ${self.budget:.4f} "
                f"ceiling; nothing further is sent")
        env = self.client.complete_messages(system, messages)
        self.calls += 1
        # ⛔ `_check_envelope` REDUCES the envelope to {text, in, out, cost_usd}
        # — `usage` does not survive it. Reading `env["usage"]["cost_usd"]`
        # here silently reported $0.000000 over four real, billed calls on the
        # first smoke. `Client.spent_usd` is the accumulator the client itself
        # bills against, so it is the authority, not a re-derivation.
        self.spent = float(self.client.spent_usd)
        if self.raw_dir and self.tag:
            json.dump({"tag": self.tag,
                       "in": env.get("in"), "out": env.get("out"),
                       "cost_usd": env.get("cost_usd"),
                       "prompt": messages[-1]["content"],
                       "text": env.get("text") or ""},
                      open(os.path.join(self.raw_dir, f"{self.tag}.json"), "w",
                           encoding="utf-8"), indent=1, ensure_ascii=False)
        return env.get("text") or ""


# ==========================================================================
#  the live half
# ==========================================================================

def run_one(planned, factory, discrimination=None):
    """One clause, four seats.

    ⭐ WHY THIS IS NOT A BARE CALL TO `seats.run_clause`, and the difference is
    a measurement decision rather than a convenience. `run_clause` is
    ALL-OR-NOTHING: it loops the seats and any one `NotAdjudicated` propagates,
    so a clause whose 4d reply merely dropped a claim's `C1 ` prefix loses 4a,
    4b and 4c as well — three seats that answered, paid for, and discarded.
    Measured on the very first live clause here (`l171_426_n001`).

    So the seats are driven one at a time through the SAME seam, and each
    seat's refusal is recorded as a refusal OF THAT SEAT. Everything after the
    loop — `stamp_evidential`, `cross_check_4d`, the seat findings,
    `instrument_defects`, `build_report`, `route` — is `run_clause`'s own
    sequence, called here in the same order with the same arguments, so a
    clause where all four adjudicate produces the identical report.

    ⛔ A REFUSED SEAT IS NOT A PASSED SEAT AND NOT A FAILED ONE. It is absent
    from `seats`/`advisory` (so no verdict is invented) and named in
    `_driver.seat_failures` (so the refusal rate is readable). Nothing is
    retried; a retry until the reply parses is how a refusal rate gets tuned
    to zero.
    """
    plan, rb = planned.plan, planned.readback
    t0 = time.time()
    judgements, findings, failures = {}, [], {}
    for seat in seats.SEATS:
        factory.tag = f"{planned.clause_id}.{seat}"
        try:
            js = seats.judge(seat, plan.prompts[seat], plan.ids[seat],
                             client_factory=lambda: factory)
        except Exception as exc:                              # noqa: BLE001
            failures[seat] = {"error_class": type(exc).__name__,
                              "error": str(exc)[:500]}
            continue
        js = seats.stamp_evidential(seat, js, rb)
        if seat == "4d":
            js, inert = seats.cross_check_4d(js, discrimination)
            findings.extend(inert)
        judgements[seat] = js

    for seat, js in judgements.items():
        for j in js:
            if j.verdict in DEFECT_VERDICTS:
                mark = f" [{', '.join(j.stamps)}]" if j.stamps else ""
                findings.append(seats.seat_finding(
                    seat, f"{plan.clause_id}.lp",
                    f"{seat} returned {j.verdict} on {j.item}{mark}"))
    defects = seats.instrument_defects(
        judgements, {s: seats.brief_sha(s) for s in seats.SEATS},
        seats.rendering_sha(rb))
    for d in defects:
        findings.append(seats.instrument_finding(
            d.item, f"4b returned {d.verdicts['4b']} and 4c returned "
                    f"{d.verdicts['4c']} on {d.item}. 4b reads only the "
                    f"rendering and 4c reads only the module, so the rendering "
                    f"is the only thing between them"))
    try:
        rep = seats.build_report(plan.clause_id, rb, judgements,
                                 plan.denominators,
                                 instrument_defect_records=defects,
                                 findings=findings,
                                 discrimination=discrimination)
        rep["routing"] = dataclasses.asdict(
            seats.route(findings, 0, 1))
        rep = seats.validate_report(rep)
        status = "adjudicated" if not failures else "partial"
    except Exception as exc:                                  # noqa: BLE001
        rep = {"clause_id": plan.clause_id}
        failures["report"] = {"error_class": type(exc).__name__,
                              "error": str(exc)[:500]}
        status = "report-refused"
    rep["_driver"] = {"status": status,
                      "seats_adjudicated": sorted(judgements),
                      "seat_failures": failures,
                      "seconds": round(time.time() - t0, 2)}
    return rep


# ==========================================================================
#  the baseline report — free, off the stored per-clause reports
# ==========================================================================

def load_reports(out_dir):
    d = os.path.join(out_dir, "reports")
    return [json.load(open(p, encoding="utf-8"))
            for p in sorted(glob.glob(os.path.join(d, "*.json")))]


def clause_rows(reports):
    rows = []
    for rep in reports:
        drv = rep.get("_driver") or {}
        if drv.get("status") not in ("adjudicated", "partial"):
            rows.append({"clause_id": rep.get("clause_id"),
                         "status": drv.get("status", "unknown"),
                         "seat_failures": drv.get("seat_failures", {}),
                         "verdicts": {}, "defects": [], "unclear": None,
                         "denominator": None})
            continue
        per_seat, defects = {}, []
        seatmap = dict(rep.get("seats") or {})
        seatmap["4a"] = (rep.get("advisory") or {}).get("4a", [])
        for seat, js in seatmap.items():
            counts = {}
            for j in js:
                counts[j["verdict"]] = counts.get(j["verdict"], 0) + 1
                if j["verdict"] in DEFECT_VERDICTS:
                    defects.append({"seat": seat, "item": j["item"],
                                    "verdict": j["verdict"],
                                    "reason": j.get("reason", ""),
                                    "evidential": j.get("evidential", True),
                                    "stamps": j.get("stamps", [])})
            per_seat[seat] = counts
        pooled = rep["unclear_rate"]["pooled"]
        rows.append({
            "clause_id": rep["clause_id"],
            "status": drv.get("status"),
            "seats_adjudicated": drv.get("seats_adjudicated", []),
            "seat_failures": drv.get("seat_failures", {}),
            "readback_outcome": rep.get("readback_outcome"),
            "verdicts": per_seat,
            "defects": defects,
            "unclear": pooled["unclear"],
            "denominator": pooled["denominator"],
            "unclear_rate": pooled["rate"],
            "instrument_defects": rep.get("instrument_defects", []),
            "readback_stamps": rep.get("readback_stamps", []),
            "routing": (rep.get("routing") or {}).get("decision"),
        })
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", default=DEFAULT_RUN)
    ap.add_argument("--corpus", default=DEFAULT_CORPUS)
    ap.add_argument("--config", default=DEFAULT_CONFIG)
    ap.add_argument("--out", default=os.path.join(HERE, "out"))
    ap.add_argument("--budget", type=float, default=0.60,
                    help="hard ceiling in USD. The printed WORST case is "
                         "checked against it and a run over it REFUSES.")
    ap.add_argument("--dry", action="store_true",
                    help="plan and price only. Makes no call. The default.")
    ap.add_argument("--live", action="store_true",
                    help="⛔ SPENDS. Runs the four seats per clause.")
    ap.add_argument("--report", action="store_true",
                    help="rebuild the baseline from stored reports. Free.")
    ap.add_argument("--ids", default=None,
                    help="comma-separated clause ids, for a smaller slice")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--force", action="store_true",
                    help="re-run clauses that already have a stored report")
    a = ap.parse_args(argv)

    os.makedirs(a.out, exist_ok=True)
    os.makedirs(os.path.join(a.out, "reports"), exist_ok=True)

    cfg = translate.load_config(a.config)
    price = tuple(cfg["model"]["price_per_mtok"])

    if a.report and not a.live:
        reports = load_reports(a.out)
        rows = clause_rows(reports)
        json.dump(rows, open(os.path.join(a.out, "clause_rows.json"), "w"),
                  indent=1)
        print(json.dumps({"clauses": len(rows)}, indent=1))
        return 0

    planned, skipped, context = build_plans(a.run, a.corpus, price)
    if a.ids:
        want = {s.strip() for s in a.ids.split(",") if s.strip()}
        planned = [p for p in planned if p.clause_id in want]
    if a.limit:
        planned = planned[:a.limit]

    cs = cost_summary(planned, price)
    print(f"run     : {a.run}")
    print(f"corpus  : {a.corpus}")
    print(f"model   : {cfg['model']['model']}  "
          f"({cfg['model'].get('provider_name')})")
    print(f"modules on disk {context['modules_on_disk']}, "
          f"translated {context['translated']}, "
          f"reaching a seat {len(planned)}, "
          f"not reaching a seat {len(skipped)}")
    print()
    print(render_cost(cs, a.budget))
    print()

    json.dump({"context": context, "cost": cs,
               "skipped": [dataclasses.asdict(s) for s in skipped],
               "polarity": {p.clause_id: p.polarity
                            for p in planned if p.polarity},
               "planned": [{"clause_id": p.clause_id,
                            "readback_outcome": p.readback.outcome,
                            "renderings": len(p.readback.renderings),
                            "echo": p.readback.clause_echo,
                            "ids": {s: list(v) for s, v in p.plan.ids.items()},
                            "estimate": p.estimate}
                           for p in planned]},
              open(os.path.join(a.out, "plan.json"), "w",
                   encoding="utf-8"), indent=1, ensure_ascii=False)

    if not a.live:
        print("DRY — nothing was sent. `judge` has no client factory on this "
              "path, so a spend here is impossible by construction, not by a "
              "flag check.")
        return 0

    if cs["usd_worst"] > a.budget:
        print(f"⛔ REFUSED: the worst case ${cs['usd_worst']:.4f} is over the "
              f"${a.budget:.4f} ceiling. Nothing sent. An unpriced or "
              f"over-ceiling run counts as over budget, never as free.")
        return 2

    factory = SeatClient(a.config, a.budget,
                         raw_dir=os.path.join(a.out, "raw"))
    done = 0
    for p in planned:
        dest = os.path.join(a.out, "reports", f"{p.clause_id}.json")
        if os.path.isfile(dest) and not a.force:
            continue
        rep = run_one(p, factory)
        json.dump(rep, open(dest, "w", encoding="utf-8"), indent=1,
                  ensure_ascii=False, default=str)
        done += 1
        drv = rep.get("_driver") or {}
        status = drv.get("status")
        if status in ("adjudicated", "partial"):
            line = seats.report_line(rep)
            if drv.get("seat_failures"):
                line += ("   ·   SEATS REFUSED: " + ", ".join(
                    f"{s}={v['error_class']}"
                    for s, v in sorted(drv["seat_failures"].items())))
        else:
            line = (f"stage4 {p.clause_id}  REPORT REFUSED "
                    f"{json.dumps(drv.get('seat_failures'))[:200]}")
        print(f"[{done}] {line}")
        if factory.spent > a.budget:
            print(f"⛔ STOPPING: measured spend ${factory.spent:.4f} passed "
                  f"the ${a.budget:.4f} ceiling.")
            break

    print()
    print(f"MEASURED SPEND ${factory.spent:.6f} over {factory.calls} calls "
          f"(estimate was ${cs['usd_likely']:.4f} likely / "
          f"${cs['usd_worst']:.4f} worst)")
    json.dump({"spent_usd": factory.spent, "calls": factory.calls,
               "clauses_run": done, "budget": a.budget,
               "estimate": cs},
              open(os.path.join(a.out, "spend.json"), "w"), indent=1)

    rows = clause_rows(load_reports(a.out))
    json.dump(rows, open(os.path.join(a.out, "clause_rows.json"), "w"),
              indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
