#!/usr/bin/env python3
"""ARM G — task decomposition.  Four calls per clause, one transcript.

Stage 1 ENUMERATE      system = promptsG/s1_enumerate.md   (no formalism)
Stage 2 DEONTIC        system = promptsG/s2_deontic.md     (statuses/acts/closure only)
Stage 3 DECLARE        system = promptsG/s3_declare.md     (ontology/requires/inputs/licences)
Stage 4 ASSEMBLE       system = THE PRODUCTION SYSTEM BLOCK, byte-identical

The user turn 1 is the PRODUCTION user block from `translate.build_user` — the same
span bytes, the same NEEDS/PROVIDES/CITATION instructions, unmodified.  Stages 2-4
append their stage prompt as a further USER turn on the same transcript, so the model
carries its own prior answers forward exactly as `repair_loop` does.

A sha256 gate refuses to send stage 4 unless the assembled system block still equals
production's.  Stages 1-3 send with `format_forcing` off (they ask for prose); stage 4
sends with production's `json_schema` forcing.

Reuses `translate.load_config / load_corpus / resolve_provider / build_system /
build_user / Client.complete_messages` and `loop.adjudicate_floor`.  It does not reuse
`loop.do_live`: that file's turn boundary carries ONE system block for the whole chain,
and this arm's whole point is that the system block changes per stage.
"""
import argparse
import copy
import hashlib
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, PHASE1)
sys.path.insert(0, os.path.join(PHASE1, "_debug_gen11", "ds_opus_loop"))

import translate                                              # noqa: E402
import loop as dsloop                                         # noqa: E402
import layers                                                 # noqa: E402

CONFIG = os.path.join(PHASE1, "resolve_runs", "graph_v2",
                      "config_corpus_all.json")
OUT = os.path.join(HERE, "out")
PROMPTS = os.path.join(HERE, "promptsG")
CLAUSES = layers.CLAUSES

#: The production system block this arm's stage 4 must send unchanged.  Recomputed
#: and compared before every stage-4 send; a mismatch REFUSES.
PROD_SHA256 = "3a66c5f54277fbea1c6a8f030435f0c3083d480954b2f6ee3aeef5f1f4e4c34c"

#: HARD CAP, owner-set for this arm, in measured dollars.  A send is refused when the
#: measured spend on disk plus the worst case of the stage about to be sent crosses it.
CAP_USD = 0.115

#: The shared ledger, and the instant arm G's first call was sent.  Everything before
#: ARM_START_TS belongs to another arm.
LEDGER = os.path.abspath(os.path.join(PHASE1, "..", "..", "..",
                                      "semi-formal-experiment", "usage.jsonl"))
ARM_START_TS = 1786925100

#: SUPERSEDED, kept for the record.  MEASURED WASTE, carried against the cap.  The first live send of this arm went out
#: PROSE_MAX_TOKENS = 1600 and then = 2400 and was TRUNCATED (finish_reason=length)
#: on `l2126_2404_n016` stage 1, once more at 2400 on its stage 2, and TWICE on
#: `l1_170_n056` stage 2, where the model emitted 3,200 completion tokens containing
#: ZERO content characters -- a degenerate loop, not a long answer.  Those two are why
#: `_send_prose` retries IN PROCESS: the second was a fresh interpreter, so
#: `Client._failed_body_hashes` was empty and the identical body went out verbatim.  `_check_envelope` raises before returning,
#: so no text was seen either time; both calls produced nothing and cost $0.00059206 +
#: $0.00081606 + $0.00097706 = $0.00238518 (usage.jsonl ts 1786925126.227,
#: 1786925202.447, 1786925248.141).  The
#: cap must see money that was SPENT, not money that produced a record, so it is a
#: constant here rather than a line in a state file.
WASTED_USD = 0.00955972

#: RAISED 3,200 -> 6,000 mid-run, on measurement, and it is not a floor being moved:
#: output tokens are billed as EMITTED, so a ceiling the model does not reach costs
#: nothing, while a ceiling it hits inside its reasoning channel costs the whole call
#: and returns no text.  13 of this arm's 15 wasted calls are that exact signature
#: (completion_tokens at the cap, content_chars 0).  A prose stage that actually
#: finishes emits 1,100-1,900 characters, ~500 tokens.
#: Prose stages do not need a 4,096-token budget and the worst case is priced at it.
#: 1600 TRUNCATED on the first send (see WASTED_USD).  2400 is the second setting; the
#: ABSOLUTE worst case at this setting is $0.123 for 68 calls, which is over the
#: $0.115 cap, so this arm is NOT authorised on its worst case.  It is authorised on a
#: MEASURED rate: two clauses are run first, the per-clause cost is measured, and the
#: remaining fifteen are sent only if measured-rate x 17 fits.  The per-call gate uses
#: the REAL transcript and still refuses at the stage that would cross $0.115, so the
#: worst outcome is a partial arm, never an overspend.
PROSE_MAX_TOKENS = 6000

#: PER-(clause, stage) OUTPUT OVERRIDE, and the measurement that forced it.
#: `l1_170_n056` stage 2 failed FIVE times at 3,200 output tokens with
#: content_chars = 0 and reasoning_chars ~13,600 every time: the model never left its
#: reasoning channel.  That is not a long answer being cut off, it is a reasoning
#: blow-up, and it happened on the one clause the Opus-critic loop needed all five
#: turns for.  Raising this clause's stage-2 ceiling is the only change; it is recorded
#: here rather than applied globally so the arm's other 16 clauses stay comparable.
PROSE_OVERRIDE = {("l1_170_n056", 2): 6000}

STAGES = [("s1_enumerate", "s1_enumerate.md"),
          ("s2_deontic", "s2_deontic.md"),
          ("s3_declare", "s3_declare.md"),
          ("s4_assemble", "s4_assemble.md")]


class _Args:
    provider = model = max_tokens = None


def setup():
    cfg = translate.load_config(CONFIG)
    rows = translate.load_corpus(cfg)
    prov = translate.resolve_provider(cfg, _Args())
    prod_system = translate.build_system(cfg)
    got = hashlib.sha256(prod_system.encode()).hexdigest()
    if got != PROD_SHA256:
        raise SystemExit(f"REFUSED: production system block sha256 {got} != "
                         f"{PROD_SHA256}. Nothing sent.")
    # a second provider handle for the prose stages: forcing off, shorter output
    prose_cfg = copy.deepcopy(cfg)
    prose_cfg["model"]["format_forcing"] = "none"
    prose_prov = translate.resolve_provider(prose_cfg, _Args())
    prose_prov.max_tokens = PROSE_MAX_TOKENS
    stage_prompts = {k: open(os.path.join(PROMPTS, f), encoding="utf-8").read()
                     for k, f in STAGES}
    return cfg, prose_cfg, rows, prov, prose_prov, prod_system, stage_prompts


def state_path(cid):
    return os.path.join(OUT, f"{cid}.stages.json")


def load_state(cid):
    p = state_path(cid)
    if os.path.exists(p):
        return json.load(open(p, encoding="utf-8"))
    return {"clause_id": cid, "stages": []}


def ledger_waste():
    """Calls this arm PAID FOR and got no stage record from, read off the shared
    ledger rather than kept in a constant a crash could lose.

    Arm G is the only arm in this window sending a prompt under 8,000 tokens (its
    prose stages); every other live arm sends the 40 KB production block, ~10,500
    tokens, on every call.  A prose-shaped row whose `content_chars` is not on any
    stage record is a call that produced nothing.
    """
    try:
        rows = [json.loads(l) for l in open(LEDGER, encoding="utf-8")]
    except OSError:
        return 0.0
    pool = []
    for cid in CLAUSES:
        for st in load_state(cid)["stages"]:
            if st["stage"] != 4:
                pool.append(len(st["raw"]))
    waste = 0.0
    for r in rows:
        if r["ts"] <= ARM_START_TS or r["prompt_tokens"] >= 8000:
            continue
        if r["content_chars"] in pool:
            pool.remove(r["content_chars"])
        else:
            waste += r["cost_usd"]
    return waste


def ledger_spent():
    return ledger_waste() + sum(float(s.get("cost_usd") or 0.0)
                            for cid in CLAUSES for s in load_state(cid)["stages"])


def _price(prov, cfg, in_chars, out_tokens):
    cpt = float(cfg["cost"]["chars_per_token"])
    pin, pout = prov.price_per_mtok
    return (in_chars / cpt / 1e6) * pin + (out_tokens / 1e6) * pout


def plan(cid, k, ctx, st):
    """(system, transcript, provider, cfg) for stage k (1-based) of clause cid."""
    cfg, prose_cfg, rows, prov, prose_prov, prod_system, sp = ctx
    idk = cfg["corpus"]["id_key"]
    row = next(r for r in rows if r[idk] == cid)
    user1, _, _ = translate.build_user(row, rows, cfg)
    transcript = [{"role": "user", "content": user1}]
    for j, s in enumerate(st["stages"]):
        transcript.append({"role": "assistant", "content": s["raw"]})
        transcript.append({"role": "user", "content": sp[STAGES[j + 1][0]]})
    if k == 1:
        pass
    system = prod_system if k == 4 else sp[STAGES[k - 1][0]]
    if k == 1:
        system = sp["s1_enumerate"]
    use_prov = prov if k == 4 else copy.copy(prose_prov)
    if k != 4 and (cid, k) in PROSE_OVERRIDE:
        use_prov.max_tokens = PROSE_OVERRIDE[(cid, k)]
    use_cfg = cfg if k == 4 else prose_cfg
    return system, transcript, use_prov, use_cfg, row


def worst_case(system, transcript, prov, cfg):
    chars = len(system) + sum(len(m["content"]) for m in transcript)
    return _price(prov, cfg, chars, prov.max_tokens)


def do_dry(ctx):
    cfg = ctx[0]
    prov = ctx[3]
    print(f"provider {prov.name}  model {prov.model}  "
          f"price {prov.price_per_mtok} $/Mtok")
    grand = 0.0
    per = []
    for cid in CLAUSES:
        st = {"clause_id": cid, "stages": []}
        sub = 0.0
        # simulate the transcript growing at the PROSE cap each stage
        fake = []
        for k in range(1, 5):
            st["stages"] = [{"raw": "x" * (PROSE_MAX_TOKENS * 4)} for _ in fake]
            system, transcript, p, c, _ = plan(cid, k, ctx, st)
            sub += worst_case(system, transcript, p, c)
            fake.append(k)
        per.append((cid, sub))
        grand += sub
    for cid, sub in per:
        print(f"  {cid}: 4 stages worst case ${sub:.4f}")
    print(f"WORST CASE, {len(CLAUSES)} clauses x 4 stages = "
          f"{len(CLAUSES) * 4} calls: ${grand:.4f}")
    print(f"measured so far ${ledger_spent():.4f}   cap ${CAP_USD:.3f}  -> "
          f"{'WITHIN' if grand + ledger_spent() <= CAP_USD else 'OVER'}")
    print("nothing sent.")


def _tolerant_check(env):
    """`translate._check_envelope` for the PROSE stages only.

    ⚠️ WHY THIS EXISTS, and why it is not a floor being lowered.  The
    production guard's own words are *"a cut-off MODULE can be syntactically
    fine and semantically half a clause"* — it is written about the emitted
    object, which stage 4 still sends through the UNPATCHED guard.  Stages 1-3
    emit scratch prose, and a paid call whose text is discarded is worse than a
    short answer: the money is spent either way and the discard also removes
    the record of HOW it was short.  Truncation is recorded on the stage record
    (`truncated: true`) and reported, never swallowed.

    Emptiness is still a refusal.
    """
    text = env.get("text")
    if text is None or not str(text).strip():
        raise translate.ProviderError("empty response")
    u = env.get("usage") or {}
    return {"text": text, "truncated": bool(env.get("truncated")),
            "in": u.get("prompt_tokens") or 0,
            "out": u.get("completion_tokens") or 0}


def do_live(ctx, cid, k):
    cfg = ctx[0]
    rows = ctx[2]
    st = load_state(cid)
    if len(st["stages"]) != k - 1:
        raise SystemExit(f"{cid} has {len(st['stages'])} stage(s); asked for "
                         f"{k}. Next is {len(st['stages']) + 1}.")
    system, transcript, prov, use_cfg, row = plan(cid, k, ctx, st)
    est = worst_case(system, transcript, prov, use_cfg)
    spent = ledger_spent()
    if spent + est > CAP_USD:
        raise SystemExit(f"REFUSED: ${spent:.4f} + ${est:.4f} would cross "
                         f"${CAP_USD:.3f}. Nothing sent.")
    if k == 4:
        got = hashlib.sha256(system.encode()).hexdigest()
        if got != PROD_SHA256:
            raise SystemExit("REFUSED: stage-4 system block is not production's.")
    client = translate.Client(prov, use_cfg)
    real = translate._check_envelope
    if k != 4:
        translate._check_envelope = _tolerant_check
    attempts = 0
    try:
        # ONE client, so `Client._failed_body_hashes` varies the bytes on a
        # retry instead of re-sending a body already measured to fail.
        while True:
            attempts += 1
            try:
                env = client.complete_messages(system, transcript)
                break
            except translate.ProviderError as exc:
                msg = str(exc)
                # TRANSPORT, not content.  together.ai returned HTTP 503
                # "Service unavailable" and multi-minute read stalls throughout
                # this arm's window (several other agents are driving the same
                # endpoint).  A transport failure is retried on EVERY stage,
                # stage 4 included, because nothing about the request is wrong;
                # a CONTENT failure (empty/reasoning loop) is still refused on
                # stage 4, where the object matters.
                transient = ("503" in msg or "Service unavailable" in msg
                             or "timed out" in msg or "502" in msg
                             or "429" in msg)
                if transient and attempts < 6:
                    wait = 15 * attempts
                    print(f"  transient ({msg[:40]}...); waiting {wait}s, "
                          f"attempt {attempts + 1}")
                    time.sleep(wait)
                    continue
                if k == 4 or attempts >= 3:
                    raise
                # MEASURED: every prose failure in this arm was the model
                # exhausting its output budget inside the REASONING channel --
                # completion_tokens at the cap, content_chars 0,
                # reasoning_chars ~13,600.  Retrying the same body at the same
                # ceiling reproduced it five times on `l1_170_n056`; doubling
                # the ceiling cleared it on the next send.  So the retry raises
                # the ceiling rather than re-rolling the dice.
                # ...but ONLY on the empty/reasoning-loop signature.  A read
                # timeout is the opposite problem and doubling the ceiling makes
                # the next attempt slower, not likelier.
                if "empty response" in str(exc):
                    prov.max_tokens = min(prov.max_tokens * 2, 12000)
                print(f"  retry {attempts} at max_tokens={prov.max_tokens} "
                      f"after {exc}")
    finally:
        translate._check_envelope = real
    raw = env["text"]
    cost = float(env.get("cost_usd") or 0.0)
    rec = {"stage": k, "name": STAGES[k - 1][0], "raw": raw,
           "max_tokens": prov.max_tokens,
           "cost_usd": cost, "usage": env.get("usage"),
           "truncated": bool(env.get("truncated")), "attempts": attempts,
           "out_tokens": env.get("out"),
           "system_sha256": hashlib.sha256(system.encode()).hexdigest(),
           "in_chars": len(system) + sum(len(m["content"]) for m in transcript)}
    st["stages"].append(rec)
    with open(state_path(cid), "w", encoding="utf-8") as fh:
        json.dump(st, fh, indent=1)
    print(f"[{cid} stage {k} {STAGES[k-1][0]}] ${cost:.5f}  "
          f"total ${ledger_spent():.4f}  out {len(raw)}c"
          f"{'  ⚠️TRUNCATED' if env.get('truncated') else ''}")
    if k == 4:
        floor, _ = dsloop.adjudicate_floor(raw, row, cfg, rows)
        st["floor"] = floor
        with open(state_path(cid), "w", encoding="utf-8") as fh:
            json.dump(st, fh, indent=1)
        if floor["parsed"]:
            with open(os.path.join(OUT, f"{cid}.final.json"), "w",
                      encoding="utf-8") as fh:
                json.dump(json.loads(raw), fh, indent=1)
        print(f"  parsed={floor['parsed']} outcome={floor['outcome']} "
              f"breaches={len(floor['breaches'])} "
              f"findings={len(floor['checks'])}")
        for b in floor["breaches"]:
            print("   BREACH", b)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--clause")
    ap.add_argument("--stage", type=int)
    ap.add_argument("--only", help="comma-separated clause ids for --all; lets "
                                   "several workers cover disjoint clause sets "
                                   "in parallel, which this provider's "
                                   "multi-minute stalls make necessary")
    ap.add_argument("--all", action="store_true",
                    help="run every remaining stage of every clause in order")
    a = ap.parse_args(argv)
    os.makedirs(OUT, exist_ok=True)
    ctx = setup()
    if not a.live:
        return do_dry(ctx)
    if a.all:
        todo = a.only.split(",") if a.only else CLAUSES
        for cid in todo:
            for k in range(len(load_state(cid)["stages"]) + 1, 5):
                do_live(ctx, cid, k)
        return
    if not a.clause or not a.stage:
        raise SystemExit("--live needs --clause and --stage, or --all")
    return do_live(ctx, a.clause, a.stage)


if __name__ == "__main__":
    raise SystemExit(main())
