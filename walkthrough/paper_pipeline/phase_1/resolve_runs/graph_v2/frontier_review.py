#!/usr/bin/env python3
"""Frontier review stage (Matt's ruling, EXPERIMENTS.md 2026-08-14:
"frontier review moves INTO the pipeline").

The K3 pass is a pipeline stage, not driver-orchestrated calls -- the same
doctrine as post_build_checks ("detection built into the pipeline, no
separate step"). Input is <run>/risk_queue.json (emitted by every build);
output is <run>/frontier_verdicts.json plus one summary line appended to
<run>/health.jsonl. Items the frontier REJECTS become the fix queue.

Stage order:
  1. PARITY SAMPLE -- `parity_n` items judged by BOTH the frontier model
     and the flash seat, rename_seat.judge-style (bounded transient
     retries, fail-closed parse handling, CostGateError and terminal
     transport propagate). A divergence rate above `divergence_stop`
     STOPS the stage loudly: the seat-defect doctrine (working rules) says
     divergence from a frontier model on the same brief is a seat defect,
     and reviewing 150 items with a defective pair of judges is noise.
  2. THE CURATED SLICE -- top `slice` items by risk, batched through
     dispatch_core.CurlTransport with a manifest-style record file
     (<run>/frontier_inflight.json) for lossless recovery: a killed
     process resumes the SAME submitted job, never pays it twice.
     Worst-case cost gate at submit (full input rate, full max_tokens
     out, no cache credit -- the ledger doctrine).
  3. Verdicts land on <run>/frontier_verdicts.json; a disposition summary
     is appended to the run's health.jsonl.

NOT auto-run inside post_build_checks: it spends real money, so it needs
its own explicit invocation with --yes, per the repo rule that
consequential spends prompt. Everything else is push-button:

    python frontier_review.py runs/ds7 --yes
"""
import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (PHASE1, HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import translate as T          # noqa: E402  (Provider, CostGateError)
import dispatch_core as dc     # noqa: E402  (CurlTransport)
import rename_seat as RS       # noqa: E402  (BRIEF reuse; judge shape)
import recurse_driver as R     # noqa: E402  (GraphClient, write_json)


#: config defaults; driver_config.json's `frontier_review` block overrides
DEFAULTS = {
    "model": "moonshotai/Kimi-K3",
    "batch": True,
    "slice": 150,
    "max_cost_usd": 3.0,
    "parity_n": 10,
    "divergence_stop": 0.4,
    #: frontier price [$in, $out] per Mtok for the worst-case gate. NO
    #: DEFAULT (adversarial review item 1a): a stale hardcoded price under-
    #: gated the real slice; the stage REFUSES to run without an explicitly
    #: configured price rather than gate on a guess.
    "price_per_mtok": None,
    "max_tokens": 1024,
    "base_url": "https://api.together.xyz/v1",
    "api_key_env": "TOGETHER_API_KEY",
}


def require_price(fcfg):
    """The configured frontier price, or a refusal (review item 1a): the
    worst-case gate is only as honest as its price, so an absent or
    malformed price stops the stage before ANY spend."""
    price = fcfg.get("price_per_mtok")
    if (not isinstance(price, (list, tuple)) or len(price) != 2
            or not all(isinstance(x, (int, float)) for x in price)):
        raise T.ConfigError(
            "frontier_review.price_per_mtok is not configured (need "
            "[$in, $out] per Mtok for the worst-case gate). Refusing to "
            "gate real spend on a guessed price -- set it in "
            "driver_config.json's frontier_review block.")
    return price

#: risk-queue kinds whose items are identification proposals -- these are
#: judged under rename_seat.BRIEF (the adopted, swept seat brief), with its
#: same_concept/different_concept vocabulary mapped to uphold/reject
RENAME_KINDS = ("seat_accepted_rename", "dangling_near_miss")

#: short per-kind briefs for the non-rename kinds (recorded design: written
#: in this file). Same contract as rename_seat.BRIEF: judge on MEANING,
#: default to the conservative side, one JSON object only.
_TAIL = """

Reply with ONE JSON object and nothing else:
{"verdict": "uphold" | "reject", "grounds": "<one or two sentences citing
the decisive wording>"}
`uphold` means the recorded decision is correct as it stands; `reject`
means it needs human review (it becomes a fix-queue item)."""

KIND_BRIEFS = {
    "low_sim_edge": """You review ONE surviving dependency edge in a concept
graph built from a policy document. A passage RELIES ON a named concept;
the edge links it to the passage recorded as ESTABLISHING that concept.
The edge was flagged only because the two descriptions share almost no
wording -- which is common for a correct edge written by independent
annotators. Judge on MEANING: does the relying passage genuinely depend on
the concept the establishing description denotes? When uncertain, reject:
a wrong edge corrupts silently, a rejected edge gets human review."""
    + _TAIL,
    "dropped_merge": """You review ONE dropped merge: two graph nodes were
proposed as redundant restatements of each other, and the merge was NOT
applied. Judge whether dropping it lost anything: if the two nodes carry
meaningfully distinct content (different scope, different obligation,
different mechanism), dropping the merge was correct -- uphold. If they
are genuine restatements whose separation will duplicate or split edges,
reject. When uncertain, uphold: an unmerged pair is honest redundancy,
a wrong merge loses content."""
    + _TAIL,
    "modal_drift": """You review ONE modal-drift flag: a graph node's
recorded claim may have shifted the FORCE of the source text (must vs
should vs may; permission vs obligation vs prohibition). Judge against the
quoted material: if the node's claim preserves the document's modal force,
uphold; if the force drifted, reject. When uncertain, reject: a drifted
modal silently rewrites policy strength."""
    + _TAIL,
    "broken_promise": """You review ONE broken promise: a division dispatch
promised that a named cross-link concept would be delivered by a child
span, and no child delivered it. Judge from the recorded context whether
the name denotes real document content that is now missing from the graph
(reject: it needs review) or a naming artifact / concept legitimately
absorbed elsewhere (uphold). When uncertain, reject: a silently vanished
concept is the worst outcome this queue exists to catch."""
    + _TAIL,
}

#: fallback brief for any future risk_queue kind this file has not met
GENERIC_BRIEF = """You review ONE recorded judgment-bearing decision from
an automated concept-graph build over a policy document. Judge on MEANING
against the recorded context whether the decision is correct. When
uncertain, reject: rejected items get human review."""

SCHEMA = ("frontier_verdict", {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": ["uphold", "reject"]},
        "grounds": {"type": "string"}},
    "required": ["verdict", "grounds"]})


class ParityStopError(T.Phase1Error):
    """Frontier/flash divergence above the configured band: seat-defect
    doctrine, the stage stops loudly instead of reviewing with a judge
    pair known to disagree."""


def brief_for(kind):
    if kind in RENAME_KINDS:
        return RS.BRIEF
    return KIND_BRIEFS.get(kind, GENERIC_BRIEF + _TAIL)


def vocab_for(kind):
    """(uphold-meaning, reject-meaning) verdict strings for this kind.

    `uphold` always means "the RECORDED decision stands". Review item 2:
    for dangling_near_miss the recorded decision is the NON-rename, so the
    mapping INVERTS -- `different_concept` upholds the honest dangling,
    while `same_concept` means the rename SHOULD have happened (reject:
    the item becomes a proposed-new-rename on the fix queue, never an
    auto-applied write)."""
    if kind == "dangling_near_miss":
        return ("different_concept", "same_concept")
    if kind in RENAME_KINDS:
        return ("same_concept", "different_concept")
    return ("uphold", "reject")


def item_prompt(item):
    """The one-shot user prompt: the item's own recorded evidence, JSON-
    rendered -- deterministic, and blind to nothing the queue recorded."""
    body = {k: item.get(k) for k in ("kind", "detail", "grounds", "where")
            if item.get(k) is not None}
    head = ("PROPOSED IDENTIFICATION UNDER REVIEW (recorded evidence):"
            if item.get("kind") in RENAME_KINDS
            else "RECORDED DECISION UNDER REVIEW:")
    return (f"{head}\n{json.dumps(body, indent=1)}\n\n"
            "Judge it per your brief. Reply with the JSON object only.")


def judge_item(complete, item):
    """One verdict on one risk-queue item, rename_seat.judge-style: the
    `complete(system, user) -> {'text': ...}` callable is the only seam.
    Returns {"verdict": "uphold"|"reject"|"no_verdict", "grounds": ...}.

    Fail-closed direction, decided here: an unparseable reply or exhausted
    transient retries is `no_verdict` -- NOT reject (which would spray
    noise into the fix queue) and NOT uphold (which would silently pass a
    risky item). CostGateError and terminal transport (402/401/403, key
    resolution) PROPAGATE, exactly as in rename_seat.judge post-F3."""
    ok, bad = vocab_for(item.get("kind"))
    env = None
    for attempt in range(3):
        try:
            env = complete(brief_for(item.get("kind")), item_prompt(item))
            break
        except Exception as exc:                # noqa: BLE001
            if type(exc).__name__ == "CostGateError":
                raise
            if attempt == 2:
                msg = str(exc)
                if (any(m in msg for m in ("HTTP 402", "HTTP 401",
                                           "HTTP 403"))
                        or "no key for $" in msg
                        or "Refusing to build a live client" in msg):
                    raise
                return {"verdict": "no_verdict",
                        "grounds": f"(transport error after 3 attempts: "
                                   f"{exc!r:.120})"}
            time.sleep(5 * (attempt + 1))
    return parse_verdict(env.get("text", "") if isinstance(env, dict)
                         else str(env), ok, bad)


def parse_verdict(text, ok, bad):
    try:
        # N1 (re-review): fence-tolerant parse, the driver's own -- a
        # markdown-fenced frontier reply must still DECIDE, not swell the
        # no_verdict pile that fails parity open
        o = R.parse_json_reply(text)
        v = o.get("verdict")
        if v == ok:
            return {"verdict": "uphold",
                    "grounds": str(o.get("grounds", ""))[:400]}
        if v == bad:
            return {"verdict": "reject",
                    "grounds": str(o.get("grounds", ""))[:400]}
        raise ValueError(f"verdict {v!r}")
    except Exception as exc:                    # noqa: BLE001
        return {"verdict": "no_verdict",
                "grounds": f"(unparseable reply: {exc!r:.120})"}


# ---------------------------------------------------------------- stage 1
def parity_stage(items, frontier_complete, flash_complete, fcfg):
    """N items judged by BOTH judges; divergence above the band stops the
    stage loudly. Divergence is computed over pairs where both judges
    reached a real verdict; no_verdict pairs are recorded, not compared."""
    n = int(fcfg.get("parity_n", DEFAULTS["parity_n"]))
    sample = items[:n]
    rows, agree, decided = [], 0, 0
    for i, it in enumerate(sample):
        fv = judge_item(frontier_complete, it)
        sv = judge_item(flash_complete, it)
        rows.append({"idx": i, "kind": it.get("kind"),
                     "risk": it.get("risk"),
                     "frontier": fv, "flash": sv})
        if (fv["verdict"] != "no_verdict"
                and sv["verdict"] != "no_verdict"):
            decided += 1
            agree += fv["verdict"] == sv["verdict"]
    divergence = 1.0 - (agree / decided) if decided else 0.0
    band = float(fcfg.get("divergence_stop", DEFAULTS["divergence_stop"]))
    report = {"n": len(sample), "decided_pairs": decided,
              "divergence": round(divergence, 3), "band": band,
              "rows": rows}
    # N1 (re-review): the stage must not fail OPEN on an empty comparison
    # -- "0% divergence over 0 decided pairs" is a defective judge pair
    # (both judges emitting no_verdict), not agreement. The floor is
    # bounded by the sample itself: a 2-item queue can only ever decide 2.
    floor = min(len(sample), max(3, n // 2))
    if decided < floor:
        exc = ParityStopError(
            f"PARITY STOP: only {decided} decided pair(s) out of "
            f"{len(sample)} sampled (floor {floor}). A judge pair that "
            f"cannot produce verdicts is as defective as one that "
            f"diverges -- inspect the no_verdict grounds in the "
            f"exception's .report before reviewing the slice.")
        exc.report = report
        raise exc
    if divergence > band:
        exc = ParityStopError(
            f"PARITY STOP: frontier/flash divergence {divergence:.0%} over "
            f"{decided} decided pair(s) exceeds the {band:.0%} band. "
            f"Divergence from a frontier model on the same brief is a SEAT "
            f"DEFECT (working rules); fix the brief before reviewing the "
            f"slice. Parity rows are in the exception's .report.")
        exc.report = report        # review item 9: the promised attribute
        raise exc from None
    return report


# ---------------------------------------------------------------- stage 2
def _worst_case_usd(bodies, price):
    pin, pout = price
    usd = 0.0
    for b in bodies:
        usd += (len(json.dumps(b)) / 3.5 / 1e6 * pin
                + b.get("max_tokens", 0) / 1e6 * pout)
    return usd


def _record_path(run_dir):
    return os.path.join(run_dir, "frontier_inflight.json")


def _request_body(item, idx, fcfg):
    return {"model": fcfg["model"],
            "temperature": 0.0,
            "max_tokens": int(fcfg.get("max_tokens",
                                       DEFAULTS["max_tokens"])),
            "messages": [
                {"role": "system", "content": brief_for(item.get("kind"))},
                {"role": "user", "content": item_prompt(item)}],
            "response_format": {"type": "json_object"}}


def _adopt_batch_id(entry, transport, rec_path):
    """Review item 3a (dispatch_core._adopt_batch_id's doctrine): a record
    with an input_file_id but no batch_id is INDETERMINATE -- the kill may
    have landed after the provider accepted create(). Ask the provider;
    never create a second job the listing might already show."""
    fid = entry.get("input_file_id")
    try:
        jobs = transport.list_batches()
    except T.ProviderError as exc:
        raise T.ProviderError(
            f"frontier create window indeterminate for {fid} and the batch "
            f"listing is unavailable ({str(exc)[:80]}); keeping the record "
            f"-- rerun when the listing answers, never resubmit blind"
        ) from exc
    match = next((j for j in jobs if j.get("input_file_id") == fid), None)
    if match is not None:
        entry["batch_id"] = match.get("id")
        R.write_json(rec_path, entry)
        print(f"  (adopted live frontier job {entry['batch_id']} for {fid} "
              f"from the create kill window)")
        return entry["batch_id"]
    # positive listing, no job: the create never took; create from the
    # ALREADY-UPLOADED file (no second upload, no second gate-worth)
    job = transport.create(fid)
    entry["batch_id"] = job.get("id")
    R.write_json(rec_path, entry)
    return entry["batch_id"]


def batch_stage(run_dir, items, transport, fcfg, poll_s=20.0, client=None):
    """Submit the curated slice as ONE batch job through CurlTransport,
    with a manifest-style record file (F2 doctrine: the record exists from
    the moment money is committed until results are routed; a killed
    process resumes the SAME job -- including the create kill window,
    review item 3a). Returns (verdicts, deferred_gate_exc): measured batch
    spend is ledgered through `client._log_usage` when a client is given
    (review item 5), and a CostGateError it raises is DEFERRED so every
    paid row is still routed (the collect-then-raise pattern); the caller
    re-raises it after the verdicts are on disk. The record file is NOT
    cleared here -- the caller clears it after frontier_verdicts.json is
    written (review item 3b)."""
    rec_path = _record_path(run_dir)
    entry = (json.load(open(rec_path))
             if os.path.exists(rec_path) else {})
    bodies = [_request_body(it, i, fcfg) for i, it in enumerate(items)]
    if not entry.get("batch_id") and entry.get("input_file_id"):
        _adopt_batch_id(entry, transport, rec_path)
    if not entry.get("batch_id"):
        # worst-case cost gate at SUBMIT (F3 arithmetic, ledger doctrine)
        ceiling = float(fcfg.get("max_cost_usd",
                                 DEFAULTS["max_cost_usd"]))
        price = require_price(fcfg)
        worst = _worst_case_usd(bodies, price)
        if worst > ceiling:
            raise T.CostGateError(
                f"frontier batch worst case ${worst:.2f} exceeds "
                f"frontier_review.max_cost_usd ${ceiling:.2f} over "
                f"{len(bodies)} item(s). Narrow `slice` or raise the "
                f"ceiling deliberately.")
        jpath = os.path.join(run_dir, "frontier_batch_input.jsonl")
        with open(jpath, "w") as f:
            for i, b in enumerate(bodies):
                f.write(json.dumps({"custom_id": f"fr-{i}",
                                    "body": b}) + "\n")
        # record BEFORE create: a kill in the create window leaves a
        # record to reconcile, never an invisible paid job. `entry` is
        # UPDATED, not replaced -- a persisted parity report (item 3c)
        # must survive the submit.
        entry.update({"input_jsonl": jpath, "n": len(bodies),
                      "worst_usd": round(worst, 4),
                      "max_tokens": (bodies[0]["max_tokens"]
                                     if bodies else None)})
        file_id = transport.upload(jpath, "frontier_review.jsonl")
        entry["input_file_id"] = file_id
        R.write_json(rec_path, entry)
        job = transport.create(file_id)
        # batch_id reaches DISK immediately: the only remaining loss
        # window is inside the create round-trip itself, which the
        # adopt path above reconciles on resume
        entry["batch_id"] = job.get("id")
        R.write_json(rec_path, entry)
    bid = entry["batch_id"]
    no_status = 0
    while True:
        j = transport.status(bid)
        status = str(j.get("status") or "").upper()
        if not status:
            # F8's backstop, same as dispatch_core: three consecutive
            # statusless replies are a transport error, not an eternal wait
            no_status += 1
            if no_status >= 3:
                raise T.ProviderError(
                    f"frontier batch status for {bid} carried no status "
                    f"field in 3 consecutive polls: {json.dumps(j)[:200]}")
            time.sleep(max(poll_s, 0.0))
            continue
        no_status = 0
        if status == "COMPLETED":
            break
        if status in ("FAILED", "EXPIRED", "CANCELLED"):
            raise T.ProviderError(
                f"frontier batch {bid} ended {status}; the record file "
                f"{rec_path} is kept for the post-mortem")
        time.sleep(max(poll_s, 0.0))
    blob = transport.content(j.get("output_file_id"))
    by_id = {}
    for ln in blob.strip().splitlines():
        if ln.strip():
            row = json.loads(ln)
            by_id[row.get("custom_id")] = row
    # review item 5: measured batch spend reaches the ledger. The envelope
    # normalisation needs a Provider-shaped price carrier (the batch reply
    # carries tokens, not dollars).
    prov = T.Provider("frontier-review", "openai-compatible",
                      fcfg.get("model", ""), fcfg.get("base_url", ""),
                      fcfg.get("api_key_env", ""), 0.0,
                      int(fcfg.get("max_tokens", DEFAULTS["max_tokens"])),
                      require_price(fcfg))
    # N2 (re-review): the record is only cleared after run_review writes
    # the verdicts, so a kill in that window would re-run this loop on
    # resume and ledger every row TWICE. The flag reaches disk BEFORE the
    # first ledger call: a resume re-parses the verdicts for free and
    # skips the ledger. (A kill mid-loop now under-ledgers the tail
    # instead of double-ledgering the whole batch -- the survivable
    # direction for a spend record read under a hard cap... is the
    # OVERSTATING one, but a double-ledger overstates usage.jsonl itself,
    # which corrupts the measurement rather than padding an estimate.)
    do_ledger = hasattr(client, "_log_usage") and not entry.get("ledgered")
    if do_ledger:
        entry["ledgered"] = True
        R.write_json(rec_path, entry)
    gate_exc = None
    verdicts = []
    for i, it in enumerate(items):
        row = by_id.get(f"fr-{i}")
        body = ((row or {}).get("response") or {}).get("body") or {}
        if body.get("choices") and do_ledger:
            try:
                client._log_usage(T.response_envelope(prov, body))
            except T.CostGateError as exc:
                # collect-then-raise (review item 4's pattern): the paid
                # rows in hand are all routed before the ceiling stops
                # anything; the caller re-raises after verdicts persist
                if gate_exc is None:
                    gate_exc = exc
        ch = (body.get("choices") or [{}])[0]
        text = ((ch.get("message") or {}).get("content")) or ""
        ok, bad = vocab_for(it.get("kind"))
        v = (parse_verdict(text, ok, bad) if text
             else {"verdict": "no_verdict",
                   "grounds": "(no row / empty completion in batch output)"})
        verdicts.append({"idx": i, "kind": it.get("kind"),
                         "risk": it.get("risk"),
                         "detail": it.get("detail"), **v})
    return verdicts, gate_exc


def live_stage(items, frontier_complete):
    """batch=false fallback: the same slice judged live, one call each."""
    out = []
    for i, it in enumerate(items):
        v = judge_item(frontier_complete, it)
        out.append({"idx": i, "kind": it.get("kind"),
                    "risk": it.get("risk"),
                    "detail": it.get("detail"), **v})
    return out


# ------------------------------------------------------------------- run
def run_review(run_dir, fcfg, frontier_complete, flash_complete,
               transport=None, poll_s=20.0, client=None):
    """The whole stage, judges and transport injected (tests run it
    offline for $0; main() wires the live clients). Ordering per the
    adversarial review: the WHOLE worst case (parity + slice) is gated
    BEFORE the parity stage spends anything (item 1c); a passed parity
    report persists in the inflight record so a resume never re-pays it
    (item 3c); the record is cleared only AFTER frontier_verdicts.json is
    on disk (item 3b); a deferred ledger CostGateError re-raises last."""
    queue = json.load(open(os.path.join(run_dir, "risk_queue.json")))
    items = queue.get("items", [])
    if not items:
        print("risk queue is empty -- nothing to review")
        return {"run": run_dir, "parity": None, "verdicts": []}
    top = items[:int(fcfg.get("slice", DEFAULTS["slice"]))]
    rec_path = _record_path(run_dir)
    rec = json.load(open(rec_path)) if os.path.exists(rec_path) else {}
    price = require_price(fcfg)
    ceiling = float(fcfg.get("max_cost_usd", DEFAULTS["max_cost_usd"]))
    # item 1c: gate the WHOLE stage up front -- slice worst case plus the
    # parity sample's live calls (two judges per item, same body
    # arithmetic), so the run can never spend parity money and then
    # refuse at submit
    worst = _worst_case_usd([_request_body(it, i, fcfg)
                             for i, it in enumerate(top)], price)
    parity_worst = 0.0
    if not rec.get("parity"):
        n = min(int(fcfg.get("parity_n", DEFAULTS["parity_n"])),
                len(items))
        parity_worst = 2 * _worst_case_usd(
            [_request_body(it, i, fcfg) for i, it in enumerate(items[:n])],
            price)
    if worst + parity_worst > ceiling:
        raise T.CostGateError(
            f"frontier review worst case ${worst + parity_worst:.2f} "
            f"(slice ${worst:.2f} + parity ${parity_worst:.2f}) exceeds "
            f"frontier_review.max_cost_usd ${ceiling:.2f} BEFORE any "
            f"spend. Narrow `slice`/`parity_n` or raise the ceiling "
            f"deliberately.")
    if rec.get("parity"):
        parity = rec["parity"]
        print(f"parity: resumed from {os.path.basename(rec_path)} "
              f"(divergence {parity['divergence']:.0%}, already passed)")
    else:
        parity = parity_stage(items, frontier_complete, flash_complete,
                              fcfg)
        rec["parity"] = parity            # item 3c: passed parity persists
        R.write_json(rec_path, rec)
        print(f"parity: divergence {parity['divergence']:.0%} over "
              f"{parity['decided_pairs']} decided pair(s) "
              f"(band {parity['band']:.0%}) -- proceeding")
    gate_exc = None
    if fcfg.get("batch", DEFAULTS["batch"]):
        verdicts, gate_exc = batch_stage(run_dir, top, transport, fcfg,
                                         poll_s=poll_s, client=client)
    else:
        verdicts = live_stage(top, frontier_complete)
    out = {"run": run_dir, "model": fcfg.get("model"),
           "parity": parity, "slice_n": len(top),
           "counts": {}, "verdicts": verdicts}
    for v in verdicts:
        out["counts"][v["verdict"]] = out["counts"].get(v["verdict"], 0) + 1
    R.write_json(os.path.join(run_dir, "frontier_verdicts.json"), out)
    # item 3b: the committed-money record outlives everything until the
    # verdicts are ON DISK
    if os.path.exists(rec_path):
        os.remove(rec_path)
    with open(os.path.join(run_dir, "health.jsonl"), "a") as f:
        f.write(json.dumps({
            "artifact": "frontier_review", "kind": "frontier_review",
            "model": fcfg.get("model"), "n": len(top),
            "parity_divergence": parity["divergence"],
            **{k: out["counts"].get(k, 0)
               for k in ("uphold", "reject", "no_verdict")}}) + "\n")
    n_rej = out["counts"].get("reject", 0)
    print(f"{len(verdicts)} verdict(s) -> frontier_verdicts.json; "
          f"{n_rej} rejection(s) are the fix queue")
    if (fcfg.get("batch", DEFAULTS["batch"])
            and not hasattr(client, "_log_usage")):
        print("!" * 72 + "\n!! FRONTIER BATCH SPEND NOT LEDGERED: no "
              "client was passed to run_review,\n!! so these rows are in "
              "no usage.jsonl and spend.py under-counts this run.\n"
              + "!" * 72)
    if gate_exc is not None:
        raise gate_exc                    # after the verdicts persisted
    return out


def _live_client(model_cfg, price, name):
    prov = T.Provider(
        name=name, kind="openai-compatible",
        model=model_cfg["model"], base_url=model_cfg["base_url"],
        api_key_env=model_cfg["api_key_env"],
        temperature=model_cfg.get("temperature", 0.0),
        max_tokens=model_cfg.get("max_tokens", 1024),
        price_per_mtok=price)
    client = R.GraphClient(prov, {"model": dict(
        model_cfg, format_forcing="json_object",
        usage_log=model_cfg.get("usage_log", "DEFAULT"))})
    return client


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("run", help="run directory, e.g. runs/ds7")
    ap.add_argument("--config", default=os.path.join(HERE,
                                                     "driver_config.json"))
    ap.add_argument("--yes", action="store_true",
                    help="required: this stage spends real money")
    args = ap.parse_args(argv)
    if not args.yes:
        print("refusing to spend without --yes (frontier review is the one "
              "stage that is not push-button, by design)")
        return 2
    cfg = json.load(open(args.config))
    fcfg = dict(DEFAULTS, **(cfg.get("frontier_review") or {}))
    frontier = _live_client(
        {"model": fcfg["model"], "base_url": fcfg["base_url"],
         "api_key_env": fcfg["api_key_env"],
         "max_tokens": int(fcfg.get("max_tokens",
                                    DEFAULTS["max_tokens"]))},
        fcfg.get("price_per_mtok"), "frontier-review")
    frontier.max_cost_usd = float(fcfg["max_cost_usd"])
    flash = _live_client(cfg["model"], cfg.get("price_per_mtok"),
                         "flash-seat")
    flash.max_cost_usd = float(fcfg["max_cost_usd"])
    transport = dc.CurlTransport(fcfg["base_url"], frontier.key)
    try:
        run_review(args.run, fcfg, frontier.complete, flash.complete,
                   transport=transport, client=frontier)
    except T.Phase1Error as exc:
        print(f"⛔ {type(exc).__name__}: {exc}")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
