#!/usr/bin/env python3
"""DeepSeek drafts -> Opus adjudicates -> feedback continues DeepSeek's OWN
transcript -> repeat.  One TURN per invocation, by necessity.

⚠️ WHY THIS IS NOT `translate.repair_loop`.  It was read first, and it cannot
be driven here.  `repair_loop` owns the whole chain: its `look()` calls
`checks.run_checks` INLINE between turns and it does not return until the
chain terminates.  The adjudicator in this experiment is a model in the
harness's own context, not a function — there is no callable to hand
`repair_loop` in place of `look`, and no way to suspend it mid-chain and
resume with an answer that arrives from outside the process.  So this file
reuses everything `repair_loop` sits ON — `translate.load_config`,
`load_corpus`, `build_system`, `build_user`, `resolve_provider`, `Client`,
`Client.complete_messages`, `estimate_cost`, `response_envelope` and the
`providers._append_usage` ledger — and reimplements only the ONE thing it
cannot borrow: the turn boundary.  The transcript shape is `repair_loop`'s
exactly (user / assistant / user / assistant …, prefix never rewritten, the
first turn being the REAL `prompt_user` block and never a summary of it), so
the cache economics and the freeze behaviour are the production ones.

Deliberately NOT copied from `repair_loop`: the freeze detector and the one
restart.  Five adjudicated turns is a different regime from five mechanical
re-sends of the same finding list, and discarding a chain here would discard
the thing being measured.  Repeated replies are RECORDED (`repeat_of_turn` in
the turn record) instead.

⚠️ TWO MEASURED OBSERVABILITY DEFECTS, FIXED 2026-08-16 (EXPERIMENTS.md).

(1) THE LEDGER HOLE.  A provider call that RAISES has already spent — the
money goes the instant the response is parsed, and `translate.Client._log_usage`
runs BEFORE `_check_envelope` precisely because a truncated completion is billed
exactly like a good one.  But the arm wrote its turn record only on the success
path, so a billed raise left NO record and `ledger_spent()` under-counted.
Measured three times: 36% of arm D's spend, $0.01612 of arm E's $0.08335, and
$0.09066 of arm F's $0.15999 — **57% of arm F's spend bought nothing**, across
21 billed-then-raised truncations.  The under-report is CORRELATED with the
outcome: the calls that raise are the long reasoners, i.e. the hard clauses, so
the arms that looked cheapest were the ones losing the most.  Now: every billed
call writes a record before any raise propagates (`record_billed_failure`), and
`ledger_spent()` sums it.  The turn NUMBERING is untouched — a billed failure
lands in `st["billed_failures"]`, never in `st["turns"]` — so re-running the
same turn number after a truncation still works exactly as it did.

(2) TRUNCATION IS A FIRST-CLASS OUTCOME.  Arm F lost 10 of 17 and 11 of 17
critic calls to the cap, delivering 5 and 6 modules; arm E lost 4 of 17, and
those 4 were its 4 longest reasoners.  The three clauses where the measured harm
was worst truncated in BOTH arm F cells — the most informative cells are exactly
the missing ones.  Truncations are now detected, recorded per call with the
token count at cut, and printed by `truncation_summary()` in every summary this
file emits.  ⛔ REJECTED BY NAME: silently retrying a truncated call (a resample
is a different draw and hides the loss), and silently raising `max_tokens` (an
arm's token cap is a PRE-REGISTERED variable; changing it mid-run invalidates
the comparison).  The harness's job is to make the loss visible and countable
and to let the caller decide.

USAGE
    loop.py --dry                       price every planned turn, send nothing
    loop.py --live --clause ID --turn 1 draft
    # adjudicate, write out/<ID>.feedback_1.md
    loop.py --live --clause ID --turn 2 send that feedback, get the redraft
"""
import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, PHASE1)

import translate                                              # noqa: E402
import schema                                                 # noqa: E402
import checks                                                 # noqa: E402

CONFIG = os.path.join(PHASE1, "resolve_runs", "graph_v2",
                      "config_corpus_all.json")
OUT = os.path.join(HERE, "out")
CLAUSES = ["l1_170_n056", "l3147_3238_n003"]
MAX_TURNS = 5

#: LEDGER ATTRIBUTION.  Stamped into `priced_by` on every row this arm prices,
#: so `usage.jsonl` says which arm bought a row instead of leaving a
#: reconciliation to join on timestamps (arms E and F both had to).  An arm
#: that reuses this module overrides it — see `setup(run_tag=...)`.
RUN_TAG = "ds_opus_loop"

#: HARD CAP for this experiment, in measured dollars, owner-set.  Not a
#: config knob: the run refuses to send when the ledger below plus the
#: worst case of the turn about to be sent would cross it.
CAP_USD = 0.15


class _Args:
    """`resolve_provider` reads attributes off argparse's namespace."""
    provider = None
    model = None
    max_tokens = None


def setup(run_tag=None):
    translate.set_run_tag(run_tag or RUN_TAG)
    cfg = translate.load_config(CONFIG)
    rows = translate.load_corpus(cfg)
    prov = translate.resolve_provider(cfg, _Args())
    system = translate.build_system(cfg)
    return cfg, rows, prov, system


def clause_row(rows, cfg, cid):
    idk = cfg["corpus"]["id_key"]
    for r in rows:
        if r[idk] == cid:
            return r
    raise SystemExit(f"no such clause id: {cid}")


def state_path(cid):
    return os.path.join(OUT, f"{cid}.transcript.json")


def load_state(cid):
    p = state_path(cid)
    if os.path.exists(p):
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)
    return {"clause_id": cid, "transcript": [], "turns": [],
            "billed_failures": []}


def save_state(st):
    st.setdefault("billed_failures", [])
    with open(state_path(st["clause_id"]), "w", encoding="utf-8") as fh:
        json.dump(st, fh, indent=1)


def billed_records(cid=None):
    """Every record of a call this arm was BILLED for: the turns that returned
    AND the ones that spent and then raised. The second list is the one that
    did not exist, and it is where 36–57% of an arm's money lived."""
    out = []
    for c in ([cid] if cid else CLAUSES):
        st = load_state(c)
        out += [dict(t, clause_id=c, kind="turn") for t in st.get("turns", [])]
        out += [dict(t, clause_id=c, kind="billed_failure")
                for t in st.get("billed_failures", [])]
    return out


def unpriced_calls():
    """Records of calls that raised with NO envelope — transport or HTTP
    failures. They may or may not have spent and there are no token counts to
    say. Reported as a count, never silently totalled as $0."""
    return [r for r in billed_records()
            if r.get("kind") == "billed_failure" and not r.get("billed")]


def ledger_spent():
    """Measured dollars this experiment has already spent, from the records on
    disk — never from a counter held in memory, which a crashed invocation
    would lose while the money stayed spent.

    ⚠️ THIS NOW INCLUDES BILLED FAILURES (2026-08-16).  It used to read
    `st["turns"]` alone, and a truncated call — billed, then raised, no turn
    record — was invisible to it. The cap below was therefore computed against
    an under-count that grew fastest on the hardest clauses.
    """
    return sum(float(r.get("cost_usd") or 0.0) for r in billed_records())


def truncations(cid=None):
    """Every call cut off at the token cap, with the count at cut."""
    return [r for r in billed_records(cid) if r.get("truncated")]


def summarize_truncation(recs, run_tag=None):
    """⚠️ Truncation is a FIRST-CLASS OUTCOME here, not an error to swallow.

    Printed by every summary this file emits, and by the arms that import it:
    an arm that quietly delivered 5 modules out of 17 must not be able to look
    like an arm that delivered 17. `recs` is any list of call records carrying
    `cost_usd` / `truncated` / `completion_tokens_at_cut`.
    """
    # A record written BEFORE the fix has no `truncated` field, only the
    # error string. Read those too: the arms whose loss this summary exists to
    # show are on disk in exactly that shape.
    cut = [r for r in recs
           if r.get("truncated")
           or (r.get("truncated") is None
               and "TRUNCATED" in str(r.get("error") or r.get("raised") or ""))]
    lines = [f"CALLS BILLED {len(recs)}   TRUNCATED AT THE CAP {len(cut)}"
             + (f"  ({100.0 * len(cut) / len(recs):.0f}% of billed calls)"
                if recs else "")]
    lost = sum(float(r.get("cost_usd") or 0.0) for r in cut)
    total = sum(float(r.get("cost_usd") or 0.0) for r in recs)
    if cut:
        lines.append(f"  ${lost:.5f} of ${total:.5f} bought a cut-off "
                     f"completion"
                     + (f" ({100.0 * lost / total:.0f}% of spend)"
                        if total else ""))
        legacy = [r for r in cut if r.get("billed") is None]
        if legacy:
            lines.append(
                f"  ⚠️ {len(legacy)} of these records PREDATE the fix and carry "
                f"no cost — the money for them is in usage.jsonl only, so the "
                f"share above is a FLOOR, not the loss")
        for r in cut:
            at = r.get("completion_tokens_at_cut")
            lines.append(
                f"   CUT {r.get('clause_id')} "
                f"{r.get('kind') or r.get('phase')} "
                + (f"n={r['n']} " if r.get("n") is not None else "")
                + (f"at {at} completion tokens "
                   f"(cap {r.get('requested_max_tokens')}), "
                   f"${float(r.get('cost_usd') or 0.0):.5f}"
                   if at is not None else "[pre-fix record: cost and cut "
                                          "point not recorded]"))
        lines.append("  ⛔ NOT retried and the cap is NOT raised: the cap is a "
                     "pre-registered variable. Decide, then re-run "
                     "deliberately.")
    unp = [r for r in recs if r.get("raised") and not r.get("billed")]
    if unp:
        lines.append(f"  ⚠️ {len(unp)} call(s) raised with no envelope — spend "
                     f"UNKNOWN, not zero; check usage.jsonl for run tag "
                     f"{run_tag or RUN_TAG!r}")
    return "\n".join(lines)


def truncation_summary(cid=None):
    return summarize_truncation(billed_records(cid))


def record_billed_failure(st, exc, turn, feedback=None):
    """THE CONTRACT: a call that spends writes a record BEFORE the raise
    propagates. Never appended to `st["turns"]` — a failed turn did not
    produce an assistant message, and putting it there would renumber the
    transcript and refuse the re-send of the same turn."""
    rec = translate.billed_record(exc, n=turn, feedback_sent=feedback)
    st.setdefault("billed_failures", []).append(rec)
    save_state(st)
    return rec


def worst_case(system, user, prov, cfg, n_prior_completions):
    """One turn's worst case: system + user + every prior completion resent as
    input, and a full `max_tokens` of output.  Same arithmetic as
    `translate.estimate_cost`, restricted to a SINGLE turn because that is what
    this file sends."""
    cpt = float(cfg["cost"]["chars_per_token"])
    in_tok = (len(system) + len(user)) / cpt + prov.max_tokens * n_prior_completions
    out_tok = prov.max_tokens
    pin, pout = prov.price_per_mtok
    return (in_tok / 1e6) * pin + (out_tok / 1e6) * pout


def adjudicate_floor(raw, row, cfg, rows):
    """The MANDATORY floor, run on every draft before any human-side reading:
    `schema.validate_all` then `checks.run_checks`.  The Opus adjudication is
    ON TOP of this, never instead of it."""
    out = {"parsed": False, "breaches": [], "checks": [], "outcome": None}
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError as exc:
        out["breaches"] = [f"not-json: {exc}"]
        return out, None
    out["parsed"] = True
    idk = cfg["corpus"]["id_key"]
    ids = {r[idk] for r in rows}
    mod, breaches = schema.validate_all(obj, row[idk], ids)
    out["breaches"] = [str(b) for b in breaches]
    try:
        res = checks.run_checks(obj, row, ids)
        out["outcome"] = res.outcome
        out["repair_needed"] = bool(res.repair_needed)
        out["checks"] = [f"[{f.severity}/{f.origin}] {f.check_id} @ {f.where}: "
                         f"{f.message}" for f in res.findings]
    except Exception as exc:                                  # noqa: BLE001
        out["checks"] = [f"run_checks raised: {exc!r}"]
    return out, mod


def do_dry(cfg, rows, prov, system):
    print(f"provider {prov.name}  model {prov.model}  "
          f"max_tokens {prov.max_tokens}  price {prov.price_per_mtok} $/Mtok")
    grand = 0.0
    for cid in CLAUSES:
        row = clause_row(rows, cfg, cid)
        user, _, _ = translate.build_user(row, rows, cfg)
        sub = sum(worst_case(system, user, prov, cfg, k)
                  for k in range(MAX_TURNS))
        # the feedback turns' own user blocks ride on the same surplus
        # `estimate_cost` documents: a finding list is far smaller than the
        # `max_tokens` completion already priced beside it.
        print(f"  {cid}: system {len(system)}c + user {len(user)}c, "
              f"{MAX_TURNS} turns worst case ${sub:.4f}")
        grand += sub
    print(f"WORST CASE, both clauses, {MAX_TURNS} turns each: ${grand:.4f}")
    print(f"already spent (measured, from turn records): ${ledger_spent():.4f}")
    print(f"cap ${CAP_USD:.2f}  -> "
          f"{'WITHIN' if grand + ledger_spent() <= CAP_USD else 'OVER — a live run will refuse at the turn that would cross it'}")
    print(truncation_summary())
    print("nothing sent.")


def do_live(cfg, rows, prov, system, cid, turn):
    row = clause_row(rows, cfg, cid)
    user, _, _ = translate.build_user(row, rows, cfg)
    st = load_state(cid)
    done = len(st["turns"])
    if turn != done + 1:
        raise SystemExit(f"{cid} has {done} turn(s) on disk; asked for turn "
                         f"{turn}. Next is {done + 1}.")
    if turn > MAX_TURNS:
        raise SystemExit(f"MAX_TURNS={MAX_TURNS} reached for {cid}.")

    if turn == 1:
        transcript = [{"role": "user", "content": user}]
        feedback = None
    else:
        fb = os.path.join(OUT, f"{cid}.feedback_{turn - 1}.md")
        if not os.path.exists(fb):
            raise SystemExit(f"turn {turn} needs the adjudication of turn "
                             f"{turn - 1} at {fb}")
        feedback = open(fb, encoding="utf-8").read().strip()
        if not feedback:
            raise SystemExit(f"{fb} is empty")
        transcript = list(st["transcript"])
        transcript.append({"role": "assistant",
                           "content": st["turns"][-1]["raw"]})
        transcript.append({"role": "user", "content": feedback})

    est = worst_case(system, "".join(m["content"] for m in transcript[:1]),
                     prov, cfg, turn - 1)
    spent = ledger_spent()
    print(f"[{cid} turn {turn}] worst case this turn ${est:.4f}; "
          f"measured so far ${spent:.4f}; cap ${CAP_USD:.2f}")
    if spent + est > CAP_USD:
        raise SystemExit(f"REFUSED: ${spent:.4f} + ${est:.4f} would cross the "
                         f"${CAP_USD:.2f} cap. Nothing sent.")

    client = translate.Client(prov, cfg)
    try:
        env = client.complete_messages(system, transcript)
    except Exception as exc:                                  # noqa: BLE001
        # ⚠️ THE LEDGER HOLE, CLOSED.  This call has ALREADY SPENT — the guard
        # that raised runs after `_log_usage`.  Write the record first, with
        # the money and the token count at cut on it, and only then let the
        # raise out. Nothing is retried and no cap is raised here.
        rec = record_billed_failure(st, exc, turn, feedback)
        print(f"  ⚠️ BILLED THEN RAISED: "
              f"${float(rec.get('cost_usd') or 0.0):.5f}"
              if rec.get("billed") else
              "  ⚠️ raised with NO envelope — spend UNKNOWN, not zero")
        if rec.get("truncated"):
            print(f"  ⚠️ TRUNCATED at {rec['completion_tokens_at_cut']} "
                  f"completion tokens (cap {rec['requested_max_tokens']}) — "
                  f"recorded, NOT retried")
        print(f"  total now ${ledger_spent():.4f}")
        print(truncation_summary())
        raise
    raw = env["text"]
    cost = float(env.get("cost_usd") or 0.0)

    floor, mod = adjudicate_floor(raw, row, cfg, rows)
    h = hashlib.sha1(raw.encode()).hexdigest()
    repeat = next((t["n"] for t in st["turns"] if t.get("sha1") == h), None)

    st["transcript"] = transcript
    st["turns"].append({"n": turn, "raw": raw, "sha1": h,
                        "repeat_of_turn": repeat, "cost_usd": cost,
                        "feedback_sent": feedback, "floor": floor,
                        "usage": env.get("usage")})
    save_state(st)

    with open(os.path.join(OUT, f"{cid}.turn{turn}.raw.json"), "w",
              encoding="utf-8") as fh:
        fh.write(raw)
    if floor["parsed"]:
        with open(os.path.join(OUT, f"{cid}.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(json.loads(raw), fh, indent=1)

    print(f"  cost ${cost:.5f}   total ${ledger_spent():.4f}")
    print(f"  parsed={floor['parsed']} outcome={floor['outcome']} "
          f"repair_needed={floor.get('repair_needed')} "
          f"breaches={len(floor['breaches'])} findings={len(floor['checks'])}")
    for b in floor["breaches"]:
        print("   BREACH", b)
    for c in floor["checks"]:
        print("   CHECK ", c)
    if repeat:
        print(f"  ⚠️ byte-identical to turn {repeat} — the reply is frozen")
    print(truncation_summary())


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--clause")
    ap.add_argument("--turn", type=int)
    a = ap.parse_args(argv)
    cfg, rows, prov, system = setup()
    if a.dry or not a.live:
        return do_dry(cfg, rows, prov, system)
    if not a.clause or not a.turn:
        raise SystemExit("--live needs --clause and --turn")
    return do_live(cfg, rows, prov, system, a.clause, a.turn)


if __name__ == "__main__":
    raise SystemExit(main())
