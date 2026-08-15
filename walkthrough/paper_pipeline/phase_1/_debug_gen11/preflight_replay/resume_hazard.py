"""CHECK 3b — is there a resumption hazard when a run dies MID-RESTART?

ZERO API SPEND: every "model" here is a local stub. Nothing under `runs/`,
`translation_sample/runs/` or `repair_graveyard/` is read or written; all
output goes to a temp directory that is deleted on exit.

The hazard being tested: the new policy makes a clause consume TWO chains.
If the process dies between them — or during the second one — a `--only-stale`
resume must NOT believe the clause is done. `--only-stale` decides from
`version.stamp`s, and `run()` writes the stamp on the success path only, so
the claim is that the hazard cannot exist. This constructs the case and
checks it rather than reasoning about it.

Three constructions:
  A. provider raises DURING the post-restart call (a caught `Phase1Error`)
  B. process is killed mid-restart (nothing returns; simulated by killing the
     run with a non-Phase1Error and letting it propagate)
  C. the restart RECOVERS — the ordinary happy path, to show the resume then
     correctly skips
"""
import copy
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE1 = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, PHASE1)

import translate as T  # noqa: E402
import version as V  # noqa: E402

CLAUSE = "m0091"

GOOD = None  # filled in below: a module that passes every check


def _good_module():
    """A reply the loop ACCEPTS and that is contract-stable.

    An abstention is used deliberately: `run()` treats `abstained` as a
    success path (it writes `<cid>.json`, the `.lp` and the version stamp),
    and it is the one legal reply whose validity does not depend on which
    predicates today's checks happen to want. The question here is the
    RESUMPTION bookkeeping, not module quality.
    """
    import schema
    obj = {k: [] for k in schema.json_schema()["properties"]}
    obj.update(outcome="abstained", clause_id=CLAUSE,
               abstain_reason="stub reply for the resumption test")
    return obj


def _bad(clause_id):
    """A module that FAILS a check, so the loop repairs. Undeclared body name."""
    import schema
    obj = {k: [] for k in schema.json_schema()["properties"]}
    obj.update(outcome="translated", clause_id=clause_id, abstain_reason=None,
               claims=["C1 a claim"], acts=["do_thing(X)"])
    return obj


class _Stub:
    """Replies from a script. `script` is a list of (text | Exception)."""

    def __init__(self, prov, cfg, script=None):
        self.script = list(script or [])
        self.n = 0

    def complete_messages(self, system, messages):
        self.n += 1
        if not self.script:
            raise AssertionError("stub ran out of scripted replies")
        item = self.script.pop(0)
        if isinstance(item, BaseException):
            raise item
        return {"text": item, "in": 10, "out": 10, "cost_usd": 0.0,
                "finish_reason": "stop"}

    # translate.run() calls this shape
    def complete(self, system, user):
        return self.complete_messages(system, [{"role": "user",
                                                "content": user}])


def _cfg(tmp, run_name, max_attempts=3):
    cfg = copy.deepcopy(T.load_config(os.path.join(PHASE1, "config.json")))
    cfg["select"] = {"clause_ids": [CLAUSE], "section_id": None,
                     "kinds": [], "limit": None}
    cfg["output"] = {"dir": tmp, "run_name": run_name}
    cfg["graveyard"] = {"dir": os.path.join(tmp, "gy"), "cap": 1000, "seed": 0,
                        "rates": {"repaired": 0.0, "first_try": 0.0}}
    cfg.setdefault("repair", {})["max_attempts"] = max_attempts
    return cfg


def _args(**over):
    class A:
        clause = section = kinds = limit = provider = model = max_tokens = None
        live = True
        show_prompt = 0
        only_stale = False
        waivers = None
    a = A()
    for k, v in over.items():
        setattr(a, k, v)
    return a


def _factory(script):
    return lambda prov, cfg: _Stub(prov, cfg, script)


def _inventory(rundir):
    if not os.path.isdir(rundir):
        return {"run dir": "ABSENT"}
    files = sorted(os.listdir(rundir))
    inv = {"files": files}
    rj = os.path.join(rundir, "run.json")
    if os.path.exists(rj):
        d = json.load(open(rj, encoding="utf-8"))
        inv["results"] = [{k: r.get(k) for k in
                           ("clause_id", "status", "attempts", "restarted",
                            "contract_hash", "provenance_hash")}
                          for r in d.get("results", [])]
    return inv


def _resume_state(tmp, cfg):
    """What a `--only-stale` resume would decide for CLAUSE."""
    prov = T.resolve_provider(cfg, _args())
    system = T.build_system(cfg)
    rows = T.load_corpus(cfg)
    row = [r for r in rows if r[cfg["corpus"]["id_key"]] == CLAUSE][0]
    model, temperature, params = V.model_params(cfg, prov)
    cur = V.stamp(row.get(cfg["corpus"]["text_key"], ""), V.schema_source(),
                  system, model, temperature, params)
    surveyed = V.survey(tmp, {CLAUSE: cur})
    best = V.best_per_clause(surveyed)
    st = best.get(CLAUSE)
    state = st["state"] if st else V.UNSTAMPED
    return state, state in V.STALE


def main():
    good = json.dumps(_good_module())
    tmp = tempfile.mkdtemp(prefix="resume_hazard_")
    print("=" * 78)
    print("CHECK 3b — interrupted-mid-restart resumption")
    print("=" * 78)
    print(f"(scratch dir {tmp}; deleted at the end; no repo path is written)")
    try:
        bad = json.dumps(_bad(CLAUSE))

        # ---- C: restart RECOVERS (baseline: the policy actually fires) ----
        cfg = _cfg(tmp, "C_recovered")
        # attempt1 bad, attempt2 SAME bytes -> fire -> redraw -> good
        code = T.run(cfg, _args(),
                     client_factory=_factory([bad, bad, good]))
        print("\n--- C. restart recovered ---")
        print("exit", code, json.dumps(_inventory(os.path.join(tmp, "C_recovered")),
                                       indent=1)[:900])
        st, stale = _resume_state(tmp, cfg)
        print(f"resume state for {CLAUSE}: {st}   would re-translate: {stale}")
        shutil.rmtree(os.path.join(tmp, "C_recovered"), ignore_errors=True)

        # ---- A: provider error DURING the post-restart call ----
        cfg = _cfg(tmp, "A_error_mid_restart")
        err = T.ProviderError("connection reset (simulated interruption)")
        code = T.run(cfg, _args(),
                     client_factory=_factory([bad, bad, err]))
        print("\n--- A. provider error during the post-restart call ---")
        print("exit", code, json.dumps(
            _inventory(os.path.join(tmp, "A_error_mid_restart")), indent=1)[:900])
        st, stale = _resume_state(tmp, cfg)
        print(f"resume state for {CLAUSE}: {st}   would re-translate: {stale}")
        shutil.rmtree(os.path.join(tmp, "A_error_mid_restart"),
                      ignore_errors=True)

        # ---- B: hard kill mid-restart ----
        cfg = _cfg(tmp, "B_killed_mid_restart")
        class _Killed(BaseException):
            pass
        try:
            T.run(cfg, _args(),
                  client_factory=_factory([bad, bad, _Killed("SIGKILL")]))
            print("\n--- B. hard kill mid-restart --- (did not raise!)")
        except BaseException as exc:      # noqa: BLE001
            print(f"\n--- B. hard kill mid-restart (raised {type(exc).__name__}) ---")
        print(json.dumps(_inventory(os.path.join(tmp, "B_killed_mid_restart")),
                         indent=1)[:900])
        st, stale = _resume_state(tmp, cfg)
        print(f"resume state for {CLAUSE}: {st}   would re-translate: {stale}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
