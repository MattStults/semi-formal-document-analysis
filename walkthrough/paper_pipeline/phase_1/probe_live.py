"""Stage 3's LABELLED half — [L] — driven against a real provider.

    .venv/bin/python probe_live.py --clauses probe_live_clauses.json --dry-run
    .venv/bin/python probe_live.py --clauses probe_live_clauses.json --live \\
        --repeats 3 --budget 0.50

`probe.label_situations` RAISES without an explicit `client_factory`, on
purpose: the build that made it was not authorised to spend. This module is
that seam's only live driver. It exists to produce the two measurements
`STEP_stage3.md` §9 names, and nothing about a coverage number from stage 3 is
believable until they exist:

  ⭐ THE `silent`-RATE, WITH ITS DENOMINATOR. `must-be-silent` asks a seat to
     distinguish "the clause permits this" from "the clause does not speak to
     this". §9: a rate near zero on a corpus where most clauses govern one act
     is a SEAT DEFECT, investigated as one — per the standing ruling that seat
     divergence defaults to a brief defect — BEFORE any conclusion is drawn
     about the translations. `--dry-run` prints the denominator too, so the
     rate is never printed alone (DEBUGGING_TIPS #2).

  ⭐ THE `k` HISTOGRAM. `probe.max_signature = 10` comes from a cost model and
     nobody has measured the real distribution. `--histogram` computes it over
     every translated module on disk, free, with no model call. It REPORTS;
     it does not re-set the cap. Re-setting the cap is a design change.

⛔ RAW FIRST, ALWAYS. `eval.py` made 36 paid calls and kept only finding
strings; that defect is recorded in this repo. Every provider payload is
written to disk INSIDE the client wrapper, before `response_envelope` runs and
therefore before any truncation or emptiness guard can raise. A call that is
billed and then refused still leaves its bytes behind.

⛔ THE FENCE IS THE POINT OF THE EXERCISE. `probe.build_seat_prompt` refuses a
prompt carrying the module, a coined predicate signature, the claims list, the
derived status or the closure. This driver adds nothing to the prompt that
`build_seat_prompt` does not check, and `--print-prompt` exists so a human can
audit one by eye before any money is spent.

⚠️ TWO PLACES `STEP_stage3.md` §5 CANNOT BE EXECUTED AS WRITTEN, both recorded
rather than papered over:

  1. §5 shows the seat "the act, as an English phrase (`produce this
     material`)". NOTHING ON DISK CARRIES ONE. A module declares `produce(M)`;
     the concept table glosses concepts, not acts; the module's `read_back`
     strings are the translator's own reading and are exactly what a seat is
     denied. So the act phrase is SUPPLIED, per clause, in the clause-spec
     file, and a missing one is a refusal. Falling back to the act term would
     put a coined name in front of the seat, which is the one thing §5's third
     row forbids.
  2. §5 and §3c speak of "the act", singular. `m0150` declares four and
     `m0134` four. One labelling call per clause per ACT is what this driver
     sends, and `probe.derived_status` is CLAUSE-scoped, not act-scoped, so
     adjudication of a multi-act module conflates the acts. Recorded as a
     limitation of the comparison, not worked around here — changing what
     `compare` projects is a design change.
"""

import argparse
import dataclasses
import datetime
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WALKTHROUGH = os.path.dirname(os.path.dirname(HERE))
for _p in (HERE, WALKTHROUGH):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import link                                                    # noqa: E402
import probe                                                   # noqa: E402
import translate                                               # noqa: E402


class LiveProbeError(RuntimeError):
    """The driver refused. Never a verdict, and never a silent skip."""


class BudgetExceeded(LiveProbeError):
    pass


#: ⚠️ A RECORDED DEPARTURE. `config.json` sets `format_forcing:
#: "json_schema"`, and that schema is `schema.response_format()` — the STAGE 1
#: MODULE schema. Sending it here would force the seat's answer into the shape
#: of a translated module, which is not what a labelling reply is. The seat
#: call therefore drops to `json_object`; the reply shape is checked afterwards
#: by `probe.adjudicate`, which is a refusal, not a repair.
SEAT_FORMAT_FORCING = "json_object"

#: What one seat reply is allowed to cost in output tokens. The stage-1 value
#: (16,384) prices a whole module; a labelling reply is a short JSON array, and
#: the cost gate multiplies this by every call it is about to make.
SEAT_MAX_TOKENS = 4096


# ==========================================================================
#  Raw first
# ==========================================================================

def _write(path, text):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


class RawFirstSeatClient:
    """`complete_messages` -> the completion TEXT, with the payload on disk.

    ⛔ The payload is written from inside `translate.response_envelope`, which
    `Client._send` calls on the parsed HTTP body BEFORE `_check_envelope` runs.
    A truncated or empty completion raises there — and it is billed exactly
    like a good one — so writing after the call returns would lose precisely
    the responses worth keeping.

    `probe.label_situations` accepts a `str` or a mapping; `translate.Client`
    returns an envelope. Handing the envelope straight through would make
    `data["labels"]` a KeyError on a paid call, so the text is unwrapped here.
    """

    def __init__(self, client, prefix):
        self.client = client
        self.prefix = prefix
        self.raw_paths = []
        self.envelopes = []

    def complete_messages(self, system, messages):
        n = len(self.envelopes)
        raw_path = f"{self.prefix}.r{n}.raw.json"
        # ⭐ THE WIRE REQUEST, saved before the call. `<tag>.prompt.txt` is what
        # the driver BUILT; this is what was SENT, and the disclosure fence can
        # only be audited against the second one.
        _write(f"{self.prefix}.r{n}.request.json",
               json.dumps({"system": system, "messages": list(messages)},
                          indent=1, ensure_ascii=False))
        original = translate.response_envelope

        def spy(prov, data):
            _write(raw_path, json.dumps(data, indent=1, ensure_ascii=False))
            self.raw_paths.append(raw_path)
            return original(prov, data)

        translate.response_envelope = spy
        try:
            env = self.client.complete_messages(system, messages)
        finally:
            translate.response_envelope = original
        self.envelopes.append(env)
        _write(f"{self.prefix}.r{n}.envelope.json",
               json.dumps({k: v for k, v in env.items()}, indent=1,
                          ensure_ascii=False, default=str))
        return env.get("text", "")

    @property
    def spent_usd(self):
        """⛔ `cost_usd` is TOP-LEVEL on what `Client._send` returns.

        It rides inside `usage` on the envelope `response_envelope` builds,
        but `_check_envelope` rebuilds the dict as `{text, in, out}` and
        `_send` then sets `cost_usd` beside them. Reading only the nested key
        made this property return 0.0 on seven real, billed calls and print
        `measured spend: $0.0000` — a total that reads "free" when it measured
        nothing. Both keys are read, and a call carrying NEITHER raises rather
        than counting as free: an unpriced call is over budget, never free.
        """
        total = 0.0
        for e in self.envelopes:
            c = e.get("cost_usd")
            if c is None:
                c = (e.get("usage") or {}).get("cost_usd")
            if c is None:
                raise BudgetExceeded(
                    "a completed call carries no cost_usd; an unpriced call "
                    "counts as OVER budget, never as free")
            total += c
        return total


# ==========================================================================
#  Clause specs — the act phrase is SUPPLIED, never derived from the module
# ==========================================================================

@dataclasses.dataclass(frozen=True)
class ClauseSpec:
    clause_id: str
    module: str
    act_phrase: str
    links: tuple = ()
    clause_text: str = ""
    cross_reference_texts: tuple = ()
    note: str = ""
    #: Filenames and result rows key on this, never on `clause_id` alone: a
    #: multi-act module is one call PER ACT (§5 speaks of "the act", singular,
    #: and `m0150` declares four), and two rows keyed on the clause id would
    #: overwrite each other's raw.
    tag: str = ""

    def __post_init__(self):
        if not str(self.act_phrase or "").strip():
            raise LiveProbeError(
                f"{self.clause_id}: no `act_phrase`. §5 shows the seat the act "
                f"as an ENGLISH PHRASE and nothing on disk carries one; "
                f"falling back to the declared act term would put a coined "
                f"name in front of the seat, which §5 forbids")
        if not str(self.clause_text or "").strip():
            raise LiveProbeError(
                f"{self.clause_id}: no clause text. The seat is shown the "
                f"clause verbatim; there is nothing to label without it")


def load_corpus_texts():
    """`{id: row}` from the corpus of record — `link.load_clauses` already
    keys it, and re-deriving it here would be a second segmentation."""
    return link.load_clauses()


def load_specs(path, cfg=None):
    """Clause specs, with the cross-reference set derived the way stage 1
    derived it.

    §5: the seat sees "the texts of cross-referenced clauses at link scope
    (same closure stage 1 got)". `translate.cross_references` IS that closure,
    so it is called rather than restated; a spec may name an explicit list
    instead, and then the list wins and is recorded as a departure.
    """
    raw = json.load(open(path, encoding="utf-8"))
    corpus = load_corpus_texts()
    rows_list = list(corpus.values())
    out = []
    for row in raw["clauses"]:
        cid = row["clause_id"]
        crow = corpus.get(cid)
        if crow is None:
            raise LiveProbeError(f"{cid} is not in the corpus of record")
        if "cross_references" in row:
            names = row["cross_references"]
        elif cfg is not None:
            found, _unres = translate.cross_references(crow, rows_list, cfg)
            names = [r["id"] for r in found]
        else:
            names = []
        xrefs = []
        for x in names:
            xr = corpus.get(x)
            if xr is None:
                raise LiveProbeError(f"{cid} cross-references {x}, which is "
                                     f"not in the corpus of record")
            xrefs.append(xr["quote"])
        out.append(ClauseSpec(
            clause_id=cid,
            module=os.path.join(HERE, row["module"]),
            links=tuple(os.path.join(HERE, p) for p in row.get("links", [])),
            act_phrase=row["act_phrase"],
            clause_text=crow["quote"],
            cross_reference_texts=tuple(xrefs),
            note=row.get("note", ""),
            tag=row.get("tag") or cid))
    return tuple(out)


# ==========================================================================
#  Building one seat prompt — free, and the fence runs here
# ==========================================================================

def build(spec):
    """`(report, concepts, rendered situations, prompt)`. No model call."""
    rows, _loaded, _missing = link.discover_concept_table(
        [spec.module] + list(spec.links))
    rep = probe.probe_clause(spec.module, list(spec.links), rows or [])
    if not rep.covering:
        raise LiveProbeError(
            f"{spec.clause_id}: the covering set is empty, so there is nothing "
            f"for a seat to label. Outcome {rep.outcome!r}, limits "
            f"{list(rep.reasons)}. Sending this would buy a labelling of "
            f"nothing and report it as a run")
    rendered = tuple(probe.render_situation(s, rep.enumeration.atoms, rows)
                     for s in rep.covering)
    prompt = probe.build_seat_prompt(spec.clause_text,
                                     list(spec.cross_reference_texts),
                                     spec.act_phrase, rendered)
    return rep, rows, rendered, prompt


# ==========================================================================
#  Cost — printed before every batch, and enforced while it runs
# ==========================================================================

def estimate_usd(prompts, prov, cfg, repeats=1):
    """Worst case: every input token at the full rate, every reply at its cap.

    `config.json` declines to claim together.ai's cached input rate and this
    keeps that choice. Overstating an estimate is survivable under a hard
    ledger cap; understating it is not.
    """
    if not prov.price_per_mtok:
        raise BudgetExceeded(
            f"provider {prov.name} has no price_per_mtok. An unpriced provider "
            f"counts as OVER budget, never as free")
    cpt = float(cfg["cost"]["chars_per_token"])
    pin, pout = prov.price_per_mtok
    in_tok = sum((len(probe.SEAT_BRIEF) * 2 + len(p)) / cpt for p in prompts)
    in_tok *= repeats
    out_tok = SEAT_MAX_TOKENS * len(prompts) * repeats
    return (in_tok / 1e6) * pin + (out_tok / 1e6) * pout, int(in_tok), \
        int(out_tok)


# ==========================================================================
#  The two measurements
# ==========================================================================

def silent_rate(labellings):
    """⭐ THE RATE **AND** ITS DENOMINATOR, never the rate alone.

    DEBUGGING_TIPS #2: a metric can read 0.0000 when it measured NOTHING, and
    that is indistinguishable from "no difference" unless the population size
    is printed beside it.
    """
    d = probe.label_distribution(labellings)
    n = sum(d.values())
    return {"silent": d["must-be-silent"],
            "denominator": n,
            "rate": (None if n == 0 else d["must-be-silent"] / n),
            "distribution": d}


def render_silent_rate(sr):
    if sr["denominator"] == 0:
        return "silent-rate: NOT MEASURED — 0 labellings"
    return (f"silent-rate: {sr['silent']}/{sr['denominator']} = "
            f"{sr['rate']:.3f}   ("
            + " · ".join(f"{sr['distribution'][k]} {k}" for k in probe.LABELS)
            + ")")


def k_histogram(module_paths, link_map=None):
    """⭐ The distribution of SIGNATURE SIZE over every module on disk.

    Free: the deterministic half only. `k` is the GROUND ATOM count, which is
    what `probe.max_signature` bounds (`DECISION_stage3_build.md` R1) — the
    predicate count is reported beside it because on `m0217` the two coincide
    and the conflation is invisible.

    ⛔ This REPORTS. It does not re-set `probe.max_signature`. §9 says the cap
    must be re-set from the histogram rather than defended, and doing that is a
    design change with an owner.
    """
    link_map = link_map or {}
    rows = []
    for p in module_paths:
        links = list(link_map.get(p, ()))
        try:
            table, _l, _m = link.discover_concept_table([p] + links)
            rep = probe.probe_clause(p, links, table or [])
            # ⛔ `|R| = 0` returns BEFORE the signature is built, so
            # `ground_atoms` is empty because it was never computed — not
            # because the signature is empty. Counting that as a `k = 0` bar
            # is the pass-looks-like-did-not-run shape in histogram form: it
            # would put every rule-less module in the smallest bucket and make
            # the distribution look comfortably under the cap.
            computed = "zero-rules" not in rep.reasons
            rows.append({"module": p, "clause_id": rep.clause_id,
                         "outcome": rep.outcome,
                         "predicates": len(rep.signature) if computed else None,
                         "k": len(rep.ground_atoms) if computed else None,
                         "covering": len(rep.covering),
                         "rules_mutated": (None if rep.coverage is None
                                           else rep.coverage.rules_mutated)})
        except Exception as exc:                              # noqa: BLE001
            rows.append({"module": p, "clause_id": None,
                         "outcome": f"ERROR {type(exc).__name__}: {exc}",
                         "predicates": None, "k": None, "covering": None,
                         "rules_mutated": None})
    hist = {}
    for r in rows:
        if r["k"] is not None:
            hist[r["k"]] = hist.get(r["k"], 0) + 1
    return rows, dict(sorted(hist.items()))


def render_k_histogram(rows, hist, cap=None):
    cap = probe.PROBE_DEFAULTS["max_signature"] if cap is None else cap
    n = sum(hist.values())
    out = [f"k histogram (ground atoms) over {n} module(s) that produced a "
           f"signature; cap 2^{cap}"]
    for k in sorted(hist):
        out.append(f"  k = {k:2d} : {'#' * hist[k]} ({hist[k]})")
    over = sum(v for k, v in hist.items() if k > cap)
    out.append(f"  over the cap (k > {cap}): {over} of {n}")
    out.append("  ⚠️ REPORTED, NOT ACTED ON — re-setting the cap is a design "
               "change (STEP_stage3.md §9)")
    return "\n".join(out)


# ==========================================================================
#  One clause, one act, one repeat
# ==========================================================================

def label_once(spec, rep, rows, prompt, client_factory, prefix):
    """One paid call. Returns `(labellings, error)`; the raw is already saved.

    An unadjudicable reply is a REFUSAL, recorded with its raw, never a
    mismatch and never a silent retry (§5's denominator rule).
    """
    del prompt                       # rebuilt inside `label_situations`
    try:
        labellings = probe.label_situations(
            rep, spec.clause_text, list(spec.cross_reference_texts),
            spec.act_phrase, rows, client_factory=client_factory)
        return labellings, None
    except (probe.ProbeError, ValueError, KeyError,
            json.JSONDecodeError) as exc:
        _write(f"{prefix}.refusal.txt", f"{type(exc).__name__}: {exc}\n")
        return (), f"{type(exc).__name__}: {exc}"


def run(specs, outdir, live=False, repeats=1, budget=0.50, cfg_path=None,
        client_factory=None, print_prompt=False):
    cfg = translate.load_config(cfg_path or os.path.join(HERE, "config.json"))
    args = argparse.Namespace(provider=None, model=None, max_tokens=None)
    prov = translate.resolve_provider(cfg, args)
    prov.max_tokens = SEAT_MAX_TOKENS

    built = []
    for spec in specs:
        rep, rows, rendered, prompt = build(spec)
        built.append((spec, rep, rows, rendered, prompt))

    est, in_tok, out_tok = estimate_usd([b[4] for b in built], prov, cfg,
                                        repeats)
    print(f"clauses: {len(built)} · repeats: {repeats} · calls: "
          f"{len(built) * repeats}")
    print(f"ESTIMATE (worst case): ${est:.4f}   "
          f"[{in_tok} in / {out_tok} out tok @ {prov.price_per_mtok} per Mtok]")
    print(f"BUDGET for this run: ${budget:.2f}")
    if est > budget:
        raise BudgetExceeded(
            f"estimated ${est:.4f} exceeds the ${budget:.2f} ceiling for this "
            f"run. Nothing sent.")
    if print_prompt:
        spec, _rep, _rows, _rendered, prompt = built[0]
        print("\n" + "=" * 74)
        print(f"SEAT PROMPT — {spec.clause_id}, verbatim, system block then "
              f"user block")
        print("=" * 74)
        print("---- SYSTEM ----")
        print(probe.SEAT_BRIEF)
        print("---- USER ----")
        print(prompt)
        print("=" * 74 + "\n")

    os.makedirs(outdir, exist_ok=True)
    results, all_labels, spent = [], [], 0.0
    for spec, rep, rows, rendered, prompt in built:
        _write(os.path.join(outdir, f"{spec.tag}.probe.json"),
               json.dumps(rep.to_json(), indent=1, ensure_ascii=False))
        _write(os.path.join(outdir, f"{spec.tag}.probe.txt"),
               rep.render())
        _write(os.path.join(outdir, f"{spec.tag}.prompt.txt"), prompt)
        for r in range(repeats):
            prefix = os.path.join(outdir, f"{spec.tag}.rep{r}")
            row = {"clause_id": spec.clause_id, "tag": spec.tag, "repeat": r,
                   "act_phrase": spec.act_phrase, "outcome_D": rep.outcome,
                   "covering": [s.id for s in rep.covering]}
            if not live:
                row["status"] = "dry-run — nothing sent"
                results.append(row)
                continue
            if spent >= budget:
                raise BudgetExceeded(
                    f"measured spend ${spent:.4f} reached the ${budget:.2f} "
                    f"ceiling; stopping before call "
                    f"{len(results) + 1}")
            seat = RawFirstSeatClient(client_factory(), prefix)
            labellings, err = label_once(spec, rep, rows, prompt,
                                         lambda s=seat: s, prefix)
            spent += seat.spent_usd
            row["spent_usd"] = seat.spent_usd
            row["raw"] = seat.raw_paths
            if err:
                row["status"] = "NOT ADJUDICATED"
                row["error"] = err
                results.append(row)
                continue
            mism = probe.compare(rep.covering, labellings, rep.clause_id)
            imposs = probe.impossible_findings(rep.covering, labellings,
                                               rep.clause_id)
            row["status"] = "adjudicated"
            row["labels"] = [dataclasses.asdict(l) for l in labellings]
            row["distribution"] = probe.label_distribution(labellings)
            row["silent_rate"] = silent_rate(labellings)
            row["mismatches"] = [dataclasses.asdict(m) for m in mism]
            row["impossible_findings"] = [f.message for f in imposs]
            row["derived"] = {s.id: sorted(probe.derived_status(
                s, rep.clause_id)) for s in rep.covering}
            all_labels.extend(labellings)
            _write(f"{prefix}.labels.json",
                   json.dumps(row, indent=1, ensure_ascii=False))
            results.append(row)

    summary = {
        "when": datetime.datetime.now().isoformat(timespec="seconds"),
        "live": live,
        "repeats": repeats,
        "provider": prov.name,
        "model": prov.model,
        "format_forcing": SEAT_FORMAT_FORCING,
        "estimate_usd": est,
        "measured_usd": spent,
        "budget_usd": budget,
        "spend_py_can_see_this": False,
        "why": "the provider is defined inline in phase_1/config.json; "
               "spend.py prices from providers.json and skips the row",
        "results": results,
        "pooled_silent_rate": silent_rate(all_labels),
    }
    _write(os.path.join(outdir, "run.json"),
           json.dumps(summary, indent=1, ensure_ascii=False, default=str))
    print(render_silent_rate(summary["pooled_silent_rate"]))
    print(f"measured spend: ${spent:.4f} of ${budget:.2f}  "
          f"⚠️ INVISIBLE TO spend.py (inline provider)")
    return summary


def _live_client_factory(cfg_path=None):
    cfg = translate.load_config(cfg_path or os.path.join(HERE, "config.json"))
    cfg = json.loads(json.dumps(cfg))
    cfg["model"]["format_forcing"] = SEAT_FORMAT_FORCING
    args = argparse.Namespace(provider=None, model=None, max_tokens=None)
    prov = translate.resolve_provider(cfg, args)
    prov.max_tokens = SEAT_MAX_TOKENS
    client = translate.Client(prov, cfg)

    def factory():
        return client
    return factory


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--clauses", default=os.path.join(
        HERE, "probe_live_clauses.json"))
    ap.add_argument("--out", default=None)
    ap.add_argument("--repeats", type=int, default=1)
    ap.add_argument("--budget", type=float, default=0.50)
    ap.add_argument("--config", default=None)
    ap.add_argument("--live", action="store_true",
                    help="actually call the provider. Off by default: a "
                         "driver that spends unless told not to is the one "
                         "mistake a revert cannot undo")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--print-prompt", action="store_true")
    ap.add_argument("--histogram", action="store_true",
                    help="the k histogram over every module on disk. Free.")
    a = ap.parse_args(argv)

    if a.histogram:
        import glob
        mods = sorted(glob.glob(os.path.join(HERE, "runs", "*", "m*.lp")))
        m0255 = os.path.join(WALKTHROUGH, "m0255.lp")
        link_map = {m0255: sorted(glob.glob(os.path.join(
            WALKTHROUGH, "clauses", "*.lp")))}
        mods.append(m0255)
        rows, hist = k_histogram(mods, link_map)
        print(render_k_histogram(rows, hist))
        print()
        for r in rows:
            print(f"  {os.path.relpath(r['module'], HERE):68s} "
                  f"k={r['k']} pred={r['predicates']} "
                  f"|R|={r['rules_mutated']} cov={r['covering']} "
                  f"{r['outcome']}")
        return 0

    cfg = translate.load_config(a.config or os.path.join(HERE, "config.json"))
    specs = load_specs(a.clauses, cfg)
    live = a.live and not a.dry_run
    out = a.out or os.path.join(
        HERE, "probe_runs",
        datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        + ("-live" if live else "-dry"))
    run(specs, out, live=live, repeats=a.repeats, budget=a.budget,
        cfg_path=a.config,
        client_factory=_live_client_factory(a.config) if live else None,
        print_prompt=a.print_prompt)
    print(f"artifacts: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
