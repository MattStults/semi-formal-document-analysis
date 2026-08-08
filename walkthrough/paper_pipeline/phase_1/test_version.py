"""Artifact versioning: what a stored module claims, and when it must be re-run.

⛔ WHY THIS FILE EXISTS. `contract_hash` and `provenance_hash` existed for weeks
and were called in exactly one place — as metadata on a graveyard FAILURE
record. Zero occurrences across every `runs/*/run.json` and every `runs/*/m*.json`.
Nothing compared a stored hash to a current one; nothing selected a clause for
re-translation. The versioning strategy was a pair of functions and a docstring.

Every test below pins one half of the ruling of 2026-08-08: **both hashes
trigger a re-run, and they stay separate.**
"""

import copy
import json
import os
import pathlib
import subprocess
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import fixtures                                            # noqa: E402
import graveyard as G                                      # noqa: E402
import translate as T                                      # noqa: E402
import version as V                                        # noqa: E402

PY = sys.executable


# ==========================================================================
#  1.  Determinism — the whole point. A hash that moves is not a version.
# ==========================================================================

def test_the_same_inputs_give_the_same_stamp_ACROSS_PROCESS_RESTARTS():
    """⛔ Determinism is load-bearing, and `hash()` is salted per process.

    Nothing here may reach a Python `hash()`, a `set` iteration order or a
    `dict` repr. Two interpreters started with different `PYTHONHASHSEED`
    values must agree, or every staleness verdict downstream is noise.
    """
    script = (
        f"import sys; sys.path.insert(0, {str(HERE)!r})\n"
        "import json, version\n"
        "print(json.dumps(version.stamp('clause text', 'schema source',\n"
        "      'system prompt', 'a-model', 0.2,\n"
        "      params={'top_p': 1, 'seed': 7, 'stop': ['a', 'b']}),\n"
        "      sort_keys=True))\n")
    outs = []
    for seed in ("0", "1", "12345"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        r = subprocess.run([PY, "-c", script], capture_output=True, text=True,
                           env=env)
        assert r.returncode == 0, r.stderr
        assert r.stdout.strip(), "the subprocess printed nothing — a stamp " \
                                 "that did not run is not a stamp that agreed"
        outs.append(r.stdout.strip())
    assert len(set(outs)) == 1, outs


def test_dict_key_INSERTION_ORDER_does_not_move_the_provenance_hash():
    """`params` is a dict, and a dict built two ways is the same params.

    Serialising it without `sort_keys` makes the version of an artifact depend
    on the order somebody happened to write a config file in.
    """
    a = {"top_p": 1, "seed": 7, "stop": ["a", "b"]}
    b = {}
    for k in ("stop", "top_p", "seed"):
        b[k] = a[k]
    assert list(a) != list(b)
    assert (G.provenance_hash("p", "m", 0.2, params=a)
            == G.provenance_hash("p", "m", 0.2, params=b))


def test_an_EMPTY_params_hashes_exactly_as_the_two_argument_form_did():
    """The new argument must not silently restamp every artifact ever written.

    `params=None` and `params={}` mean "nothing beyond model and temperature",
    which is what the previous signature meant. If they differed, adding the
    argument would mark the whole corpus provenance-stale for no reason — the
    exact failure the two-hash split exists to prevent, arriving from the side.
    """
    base = G.provenance_hash("p", "m", 0.2)
    assert G.provenance_hash("p", "m", 0.2, params=None) == base
    assert G.provenance_hash("p", "m", 0.2, params={}) == base
    assert G.provenance_hash("p", "m", 0.2, params={"top_p": 1}) != base


def test_the_order_run_DIRECTORIES_are_created_in_does_not_move_the_census(
        tmp_path):
    """A survey that reads `os.listdir` inherits the filesystem's order.

    Two trees with identical content, written in opposite order, must produce
    the same rows and the same counts.
    """
    cur = {"m1": _st("c1", "p1"), "m2": _st("c2", "p2")}
    names = ["run-a", "run-b", "run-c"]
    a, b = tmp_path / "A", tmp_path / "B"
    for root, order in ((a, names), (b, list(reversed(names)))):
        for n in order:
            _fake_run(root / n, {"m1": _st("c1", "p1"),
                                 "m2": _st("cX", "p2")})
    ra, rb = V.survey(str(a), cur), V.survey(str(b), cur)
    strip = lambda rows: [(r["clause_id"], r["state"]) for r in rows]  # noqa
    assert strip(ra) == strip(rb)
    assert V.census(ra) == V.census(rb)


# ==========================================================================
#  2.  Classification — four states, and `unstamped` is not `current`
# ==========================================================================

def _st(c, p):
    return {"contract_hash": c, "provenance_hash": p}


def _fake_run(d, stamps, unstamped=()):
    """A run directory holding module `.json` files and their stamps."""
    d = pathlib.Path(d)
    d.mkdir(parents=True, exist_ok=True)
    (d / "run.json").write_text(json.dumps({"results": []}))
    (d / "concepts.json").write_text("[]")
    for cid, st in stamps.items():
        (d / f"{cid}.json").write_text(json.dumps({"clause_id": cid}))
        (d / f"{cid}{V.STAMP_SUFFIX}").write_text(json.dumps(st))
    for cid in unstamped:
        (d / f"{cid}.json").write_text(json.dumps({"clause_id": cid}))
    return d


def test_an_identical_pair_of_hashes_is_CURRENT():
    state, differing = V.classify(_st("c", "p"), _st("c", "p"))
    assert state == V.CURRENT
    assert differing == []


def test_a_moved_CONTRACT_hash_is_contract_stale():
    state, differing = V.classify(_st("c", "p"), _st("c2", "p"))
    assert state == V.CONTRACT_STALE
    assert differing == ["contract_hash"]


def test_a_moved_PROVENANCE_hash_is_provenance_stale_and_STILL_RE_RUNS():
    """⭐ Matt, 2026-08-08: a provenance change triggers a re-run too.

    The rejected alternative — *"a provenance change only relabels, never
    re-runs"* — is what this test forbids: `provenance-stale` must be inside
    the set `--only-stale` selects.
    """
    state, differing = V.classify(_st("c", "p"), _st("c", "p2"))
    assert state == V.PROVENANCE_STALE
    assert differing == ["provenance_hash"]
    assert state in V.STALE


def test_when_BOTH_moved_the_state_is_CONTRACT_stale_and_both_are_reported():
    """Precedence goes to the non-waivable one.

    Reporting it as `provenance-stale` would make it eligible for a waiver,
    which is the one thing a contract change may never be.
    """
    state, differing = V.classify(_st("c", "p"), _st("c2", "p2"))
    assert state == V.CONTRACT_STALE
    assert differing == ["contract_hash", "provenance_hash"]


def test_a_module_with_NO_STAMP_is_not_current():
    """Every module in `runs/` today is unstamped, and none of them is current.

    Treating "no claim" as "current" is the pass-indistinguishable-from-did-
    not-run failure in versioning form: the artifacts that predate the stamp
    are exactly the ones nobody can vouch for.
    """
    state, differing = V.classify(None, _st("c", "p"))
    assert state == V.UNSTAMPED
    assert state in V.STALE
    assert state != V.CURRENT


def test_a_clause_that_LEFT_THE_CORPUS_is_not_reported_as_stale():
    """It cannot be re-run — there is nothing to send. It gets its own state."""
    state, _ = V.classify(_st("c", "p"), None)
    assert state == V.OFF_CORPUS
    assert state not in V.STALE


def test_a_clause_CURRENT_in_ANY_run_is_current_overall(tmp_path):
    """A re-run writes a NEW directory; the old stale copy stays on disk.

    Taking the worst state across runs would make a clause permanently stale
    the moment it was ever translated under an older prompt — so the corpus
    could never become current and `--only-stale` would select everything,
    every time.
    """
    cur = {"m1": _st("c", "p")}
    _fake_run(tmp_path / "old", {"m1": _st("c", "pOLD")})
    _fake_run(tmp_path / "new", {"m1": _st("c", "p")})
    best = V.best_per_clause(V.survey(str(tmp_path), cur))
    assert best["m1"]["state"] == V.CURRENT


def test_run_json_and_the_concept_table_are_not_mistaken_for_modules(tmp_path):
    _fake_run(tmp_path / "r", {"m1": _st("c", "p")})
    assert V.module_ids(str(tmp_path / "r")) == ["m1"]


def test_the_STAMP_SIDECAR_is_not_itself_read_as_a_module(tmp_path):
    """`m1.version.json` matches `*.json`. It is the stamp, not the artifact."""
    _fake_run(tmp_path / "r", {"m1": _st("c", "p")})
    ids = V.module_ids(str(tmp_path / "r"))
    assert not any(i.endswith(".version") for i in ids), ids


def test_NO_SIDECAR_OF_ANY_KIND_is_read_as_a_module(tmp_path):
    """⛔ Found by running the census on the real `runs/`, not by reasoning.

    Excluding the non-modules BY NAME reported 21 `no-longer-in-corpus`
    modules — every one a `<clause>.transcript.json`. That reads as a finding
    about the corpus (clauses that were removed) and was an artefact of the
    glob. A run directory grows sidecars as stages are added, so the rule is
    the module's own shape: a clause id carries no dot.
    """
    d = _fake_run(tmp_path / "r", {"m1": _st("c", "p")})
    for extra in ("m1.transcript.json", "m1.findings.json",
                  "m1.some.future.stage.json"):
        (d / extra).write_text("{}")
    assert V.module_ids(str(d)) == ["m1"]


# ==========================================================================
#  3.  The stamp reaches disk, and it is RECOMPUTABLE
# ==========================================================================

GOOD = {c: fixtures.module_json(clause_id=c) for c in ("m0091", "m0014")}


class _Good:
    """Returns the canonical module for whichever clause it was asked about."""

    def __init__(self, *a, **k):
        pass

    def complete(self, system, user):
        cid = [c for c in GOOD if c in user][0]
        return {"text": GOOD[cid], "in": 1, "out": 1, "finish_reason": "stop"}

    def complete_messages(self, system, messages):
        raise AssertionError("repair must not be needed for a valid module")


class _NeverCalled:
    """A client factory that fails the test if a run tries to spend."""

    def __init__(self, *a, **k):
        raise AssertionError("a client was constructed — this run would spend")


def _cfg(tmp_path, clauses, run_name="t", **over):
    cfg = copy.deepcopy(T.load_config(str(HERE / "config.json")))
    cfg["select"] = {"clause_ids": list(clauses), "section_id": None,
                     "kinds": [], "limit": None}
    cfg["output"] = {"dir": str(tmp_path), "run_name": run_name}
    cfg["graveyard"] = {"dir": str(tmp_path / "gy"), "cap": 1000, "seed": 0,
                        "rates": {"repaired": 0.0, "first_try": 0.0}}
    cfg.update(over)
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


def _run(cfg, args=None, factory=_Good):
    return T.run(cfg, args or _args(), client_factory=factory)


def _unstamp(rundir, clause_id):
    """Make a stored module carry no version claim at all.

    ⚠️ BOTH PLACES. Deleting the sidecar is not enough: `run.json` carries the
    same two hashes per clause and `read_stamp` falls back to it on purpose,
    so a module whose sidecar was lost is still stamped. A test that deleted
    only the sidecar and asserted `unstamped` would be testing the fallback
    away.
    """
    rundir = pathlib.Path(rundir)
    (rundir / f"{clause_id}{V.STAMP_SUFFIX}").unlink()
    rec = json.loads((rundir / "run.json").read_text())
    for r in rec["results"]:
        if r.get("clause_id") == clause_id:
            r.pop("contract_hash", None)
            r.pop("provenance_hash", None)
    (rundir / "run.json").write_text(json.dumps(rec))


#: Lines a run prints that echo a PATH. See `_report`.
_PATHY = ("writing to ", "Raw responses kept in ")


def _report(capsys):
    """The run's own report, with every line that echoes a PATH removed.

    ⛔ FOUND BY THE MUTATION SWEEP, AND IT IS THE §8 SHAPE AGAIN. `pytest`'s
    `tmp_path` embeds the TEST'S OWN NAME:

        …/pytest-5697/test_an_UNUSED_waiver_is_reported_and_not_silent0/one

    and `run()` prints that path twice. So `assert "unused" in out` was
    satisfied by the directory name, and `assert "of 2 selected" in out` by
    `translating 2 of 2 selected clause(s)`. Both tests passed against a build
    where the line they were written to check had been deleted — four of the
    eight survivors in the first sweep were this, in tests that read as
    thorough.

    ⇒ A test that greps the whole captured stream is asserting against its own
    name. Drop the path lines, then assert on the report.
    """
    out = capsys.readouterr().out
    return "\n".join(ln for ln in out.splitlines()
                     if not any(p in ln for p in _PATHY))


def _now_provenance(cfg):
    """The provenance hash TODAY's inputs produce — params and all."""
    model, temp, params = V.model_params(cfg)
    return G.provenance_hash(T.build_system(cfg), model, temp, params=params)


def test_a_translated_module_gets_a_STAMP_SIDECAR_beside_it(tmp_path):
    """⭐ The artifact carries its own provenance, or the run is the only record.

    A module `.json` that has been copied, committed or handed to a later stage
    has to be able to answer "what was I made from" on its own.
    """
    _run(_cfg(tmp_path, ["m0091"]))
    st = json.loads((tmp_path / "t" / f"m0091{V.STAMP_SUFFIX}").read_text())
    assert st["contract_hash"] and st["provenance_hash"]
    assert st["contract_hash"] != st["provenance_hash"]


def test_the_stamp_on_disk_is_RECOMPUTABLE_from_the_inputs(tmp_path):
    """A stamp nobody can reproduce is a serial number, not a version.

    If the stored value cannot be re-derived from the clause, the schema
    source, the prompt and the model, then no comparison against a current
    value means anything — which is the state the pipeline was in.
    """
    cfg = _cfg(tmp_path, ["m0091"])
    _run(cfg)
    stored = json.loads(
        (tmp_path / "t" / f"m0091{V.STAMP_SUFFIX}").read_text())

    rows = T.load_corpus(cfg)
    row = [r for r in rows if r["id"] == "m0091"][0]
    model, temp, params = V.model_params(cfg)
    want = V.stamp(row["quote"], V.schema_source(), T.build_system(cfg),
                   model, temp, params)
    assert stored["contract_hash"] == want["contract_hash"]
    assert stored["provenance_hash"] == want["provenance_hash"]


def test_run_json_carries_the_two_hashes_PER_CLAUSE_and_at_RUN_LEVEL(tmp_path):
    _run(_cfg(tmp_path, ["m0091"]))
    rec = json.loads((tmp_path / "t" / "run.json").read_text())
    assert rec["provenance_hash"], "run.json has no run-level provenance hash"
    assert rec["schema_sha"], "run.json does not say which schema it validated against"
    r0 = rec["results"][0]
    assert r0["contract_hash"] and r0["provenance_hash"]


def test_the_LP_carries_the_version_as_a_COMMENT_not_a_directive(tmp_path):
    """The `.lp` is a rendering; the `.json` is the record.

    The version is written into the `.lp` so a human reading the rendering on
    its own can see it — but as a plain `%` comment. `%%` lines are the module
    HEADER and `link.py` parses them; a version line that looked like a
    directive would be a new header field nothing declares.
    """
    _run(_cfg(tmp_path, ["m0091"]))
    lp = (tmp_path / "t" / "m0091.lp").read_text()
    line = [ln for ln in lp.splitlines() if "contract=" in ln]
    assert line, "the .lp does not carry its version"
    assert not line[0].startswith("%%"), line[0]
    assert line[0].lstrip().startswith("%"), line[0]


def test_a_FAILED_clause_is_not_stamped(tmp_path):
    """A stamp says "this artifact was built from these inputs".

    There is no artifact on the failure path, and a stamp beside nothing would
    make the next `--only-stale` run skip a clause that was never translated.
    """
    class _Broken(_Good):
        def complete(self, system, user):
            return {"text": "{not json", "in": 1, "out": 1,
                    "finish_reason": "stop"}

        def complete_messages(self, system, messages):
            return self.complete(system, messages)

    _run(_cfg(tmp_path, ["m0091"], repair={"max_attempts": 1}),
         factory=_Broken)
    # The premise: the run really ran and really failed. Without this the test
    # passes when the run dies before writing anything at all.
    assert (tmp_path / "t" / "m0091.raw.txt").exists()
    assert not (tmp_path / "t" / "m0091.json").exists()
    assert not (tmp_path / "t" / f"m0091{V.STAMP_SUFFIX}").exists()


# ==========================================================================
#  4.  Selection — the thing that makes 593 clauses affordable to iterate on
# ==========================================================================

def test_ONLY_STALE_IS_OFF_BY_DEFAULT(tmp_path, capsys):
    """⛔ Changing what a bare `translate.py` translates is a spend change.

    A second identical run must still translate the clause, because nobody
    asked it not to.
    """
    _run(_cfg(tmp_path, ["m0091"], run_name="one"))
    _run(_cfg(tmp_path, ["m0091"], run_name="two"))
    assert (tmp_path / "two" / "m0091.json").exists()


def test_only_stale_SKIPS_a_module_whose_inputs_have_not_moved(tmp_path):
    _run(_cfg(tmp_path, ["m0091"], run_name="one"))
    code = _run(_cfg(tmp_path, ["m0091"], run_name="two"),
                _args(only_stale=True), factory=_NeverCalled)
    assert code == 0
    assert not (tmp_path / "two").exists() or \
        not (tmp_path / "two" / "m0091.json").exists()


def test_only_stale_RE_TRANSLATES_when_the_SCHEMA_moved(
        tmp_path, monkeypatch, capsys):
    """A contract change is not optional and not waivable.

    ⚠️ The `.json` assertion alone passes vacuously while `--only-stale` is
    unimplemented — a flag nothing reads translates everything, which looks
    exactly like a correct re-run. The CENSUS line is what tells the two
    apart, so it is asserted too.
    """
    _run(_cfg(tmp_path, ["m0091"], run_name="one"))
    capsys.readouterr()
    monkeypatch.setattr(V, "schema_source", lambda: "SCHEMA MOVED")
    code = _run(_cfg(tmp_path, ["m0091"], run_name="two"),
                _args(only_stale=True))
    out = _report(capsys)
    assert code == 0
    assert "1 contract-stale" in out, out
    assert (tmp_path / "two" / "m0091.json").exists()


def test_only_stale_RE_TRANSLATES_when_the_PROMPT_moved(
        tmp_path, monkeypatch, capsys):
    """⭐ The ruling. A prompt edit re-runs; it does not merely relabel.

    The rejected alternative — *"a provenance change only relabels"* — would
    show up here as `1 provenance-stale` printed and the clause NOT re-sent.
    """
    _run(_cfg(tmp_path, ["m0091"], run_name="one"))
    capsys.readouterr()
    real = T.build_system
    monkeypatch.setattr(T, "build_system", lambda cfg: real(cfg) + "\nMOVED")
    code = _run(_cfg(tmp_path, ["m0091"], run_name="two"),
                _args(only_stale=True))
    out = _report(capsys)
    assert "1 provenance-stale" in out, out
    assert "translating 1 of 1" in out, out
    assert (tmp_path / "two" / "m0091.json").exists()


def test_only_stale_PRINTS_THE_CENSUS_BEFORE_ANYTHING_IS_SENT(
        tmp_path, monkeypatch, capsys):
    """⛔ A staleness tool that silently re-runs 593 clauses is a spend incident.

    The counts, by class, with their denominator, must be on screen BEFORE the
    cost line and the gate — and the line must distinguish the two kinds of
    staleness, because they are different facts about the artifact.
    """
    _run(_cfg(tmp_path, ["m0091", "m0014"], run_name="one"))
    # m0091 keeps its stamp and the prompt moves -> provenance-stale.
    # m0014 loses its stamp entirely                -> unstamped.
    _unstamp(tmp_path / "one", "m0014")
    capsys.readouterr()
    real = T.build_system
    monkeypatch.setattr(T, "build_system", lambda c: real(c) + "\nMOVED")
    _run(_cfg(tmp_path, ["m0091", "m0014"], run_name="two"),
         _args(only_stale=True))
    out = _report(capsys)
    assert "staleness" in out, out
    assert "1 provenance-stale" in out, out
    assert "1 unstamped" in out, out
    assert "(of 2 selected)" in out, \
        "the census line carries no denominator"
    assert out.index("staleness") < out.index("cost (worst)"), out


def test_only_stale_narrows_the_COST_ESTIMATE_and_not_only_the_loop(
        tmp_path, capsys):
    """The gate must price what will actually be sent.

    Filtering inside the loop while estimating over the whole selection makes
    the printed worst case describe calls that were never going to be made —
    and, worse, leaves the cost GATE refusing runs over clauses nobody was
    going to send.
    """
    _run(_cfg(tmp_path, ["m0091", "m0014"], run_name="one"))
    # Only m0014 is stale: it carries no version claim anywhere.
    _unstamp(tmp_path / "one", "m0014")
    capsys.readouterr()
    _run(_cfg(tmp_path, ["m0091", "m0014"], run_name="two"),
         _args(only_stale=True))
    out = _report(capsys)
    assert "clauses      : 1  [m0014]" in out, out


# ==========================================================================
#  5.  The intention flag — hard to use carelessly, and it leaves a record
# ==========================================================================

def _waiver(tmp_path, **over):
    w = {"clause_ids": ["m0091"],
         "stored_provenance_hash": "",
         "current_provenance_hash": "",
         "who": "matt", "date": "2026-08-08",
         "why": "the prompt edit was a typo fix in a comment"}
    w.update(over)
    p = tmp_path / "waivers.json"
    p.write_text(json.dumps({"waivers": [w]}))
    return str(p)


def test_a_waiver_may_NEVER_excuse_a_CONTRACT_change(tmp_path, monkeypatch):
    """⛔ The one thing the intention flag may not do.

    A contract change means the artifact may no longer VALIDATE. A waiver that
    could cover it would let one word keep an invalid module in the corpus.
    """
    _run(_cfg(tmp_path, ["m0091"], run_name="one"))
    stored = json.loads(
        (tmp_path / "one" / f"m0091{V.STAMP_SUFFIX}").read_text())
    monkeypatch.setattr(V, "schema_source", lambda: "SCHEMA MOVED")
    path = _waiver(tmp_path,
                   stored_provenance_hash=stored["provenance_hash"],
                   current_provenance_hash=stored["provenance_hash"])
    with pytest.raises(V.WaiverError) as exc:
        _run(_cfg(tmp_path, ["m0091"], run_name="two"),
             _args(only_stale=True, waivers=path), factory=_NeverCalled)
    assert "contract" in str(exc.value).lower()


def test_a_waiver_covering_a_PROVENANCE_change_skips_the_clause(
        tmp_path, capsys):
    _run(_cfg(tmp_path, ["m0091"], run_name="one"))
    stored = json.loads(
        (tmp_path / "one" / f"m0091{V.STAMP_SUFFIX}").read_text())
    real = T.build_system
    T.build_system = lambda c: real(c) + "\nMOVED"
    try:
        cfg = _cfg(tmp_path, ["m0091"], run_name="two")
        now = _now_provenance(cfg)
        path = _waiver(tmp_path,
                       stored_provenance_hash=stored["provenance_hash"],
                       current_provenance_hash=now)
        code = _run(cfg, _args(only_stale=True, waivers=path),
                    factory=_NeverCalled)
    finally:
        T.build_system = real
    assert code == 0
    out = _report(capsys)
    assert "waiver honoured" in out, out
    assert "— matt, 2026-08-08:" in out, \
        "the record of WHO waived it and WHEN is not reported"
    assert "typo fix" in out, "the record of WHY is not reported"


def test_a_waiver_EXPIRES_when_the_prompt_moves_again(tmp_path):
    """⭐ This is what stops one word making 593 modules permanently current.

    The waiver names the exact transition — from this stored hash to this
    current hash. The next prompt edit changes the current hash and every
    waiver written against the previous one stops applying, by construction.
    """
    _run(_cfg(tmp_path, ["m0091"], run_name="one"))
    stored = json.loads(
        (tmp_path / "one" / f"m0091{V.STAMP_SUFFIX}").read_text())
    path = _waiver(tmp_path,
                   stored_provenance_hash=stored["provenance_hash"],
                   current_provenance_hash="a-hash-that-is-no-longer-current")
    real = T.build_system
    T.build_system = lambda c: real(c) + "\nMOVED AGAIN"
    try:
        code = _run(_cfg(tmp_path, ["m0091"], run_name="two"),
                    _args(only_stale=True, waivers=path))
    finally:
        T.build_system = real
    assert code == 0
    assert (tmp_path / "two" / "m0091.json").exists(), \
        "an expired waiver still excused the clause"


def test_an_UNUSED_waiver_is_reported_and_not_silent(tmp_path, capsys):
    """A waiver that matches nothing is either a typo or a stale file.

    Silence there is the same defect as a check that cannot run: the operator
    believes something was honoured and nothing was.
    """
    _run(_cfg(tmp_path, ["m0091"], run_name="one"))
    path = _waiver(tmp_path, clause_ids=["m0014"],
                   stored_provenance_hash="x", current_provenance_hash="y")
    _run(_cfg(tmp_path, ["m0091"], run_name="two"),
         _args(only_stale=True, waivers=path), factory=_NeverCalled)
    out = _report(capsys)
    assert "waiver UNUSED" in out, out
    assert "matched nothing" in out, out


@pytest.mark.parametrize("bad,why", [
    ({"clause_ids": ["*"]}, "a wildcard"),
    ({"clause_ids": ["all"]}, "the word all"),
    ({"clause_ids": []}, "an empty list"),
    ({"who": ""}, "no author"),
    ({"why": ""}, "no reason"),
    ({"date": ""}, "no date"),
    ({"current_provenance_hash": None}, "no transition named"),
])
def test_a_careless_waiver_is_REFUSED(tmp_path, bad, why):
    """⛔ It must be hard to use carelessly. Each of these is a refusal.

    `clause_ids` has to be an explicit enumeration: a wildcard is exactly the
    one-word mechanism this flag is designed not to offer. Enumerating 593 ids
    is mechanical, and the file that holds them IS the record.
    """
    w = {"clause_ids": ["m0091"], "stored_provenance_hash": "a",
         "current_provenance_hash": "b", "who": "matt", "why": "r",
         "date": "2026-08-08"}
    w.update(bad)
    p = tmp_path / "w.json"
    p.write_text(json.dumps({"waivers": [w]}))
    with pytest.raises(V.WaiverError):
        V.load_waivers(str(p))


def test_honoured_waivers_are_recorded_in_run_json(tmp_path):
    """A run that skipped work on somebody's say-so must say so, on disk."""
    _run(_cfg(tmp_path, ["m0091", "m0014"], run_name="one"))
    stored = json.loads(
        (tmp_path / "one" / f"m0091{V.STAMP_SUFFIX}").read_text())
    real = T.build_system
    T.build_system = lambda c: real(c) + "\nMOVED"
    try:
        cfg = _cfg(tmp_path, ["m0091", "m0014"], run_name="two")
        now = _now_provenance(cfg)
        path = _waiver(tmp_path,
                       stored_provenance_hash=stored["provenance_hash"],
                       current_provenance_hash=now)
        _run(cfg, _args(only_stale=True, waivers=path))
    finally:
        T.build_system = real
    rec = json.loads((tmp_path / "two" / "run.json").read_text())
    assert rec["waivers_honoured"], rec.get("waivers_honoured")
    assert rec["waivers_honoured"][0]["who"] == "matt"


def test_a_waiver_file_is_IGNORED_unless_only_stale_was_asked_for(tmp_path):
    """⛔ A waiver is a statement about a re-run, not a licence to skip work.

    Without `--only-stale` nothing is being skipped, so a waiver file must not
    quietly change what a run translates.
    """
    _run(_cfg(tmp_path, ["m0091"], run_name="one"))
    path = _waiver(tmp_path, stored_provenance_hash="a",
                   current_provenance_hash="b")
    _run(_cfg(tmp_path, ["m0091"], run_name="two"), _args(waivers=path))
    assert (tmp_path / "two" / "m0091.json").exists()


# ==========================================================================
#  6.  Over the runs that are actually on disk
# ==========================================================================

def test_the_survey_runs_over_the_STORED_runs_directory():
    """It must work on `runs/*/` as they exist, not only on fixtures.

    Every module there predates the stamp, so the honest answer is
    `unstamped` — and a survey that reported them `current` would be claiming
    a provenance that was never recorded.
    """
    root = HERE / "runs"
    if not root.is_dir():
        pytest.skip("no stored runs")
    cfg = T.load_config(str(HERE / "config.json"))
    rows = V.survey(str(root), V.current_map(cfg, T.build_system(cfg),
                                             *V.model_params(cfg)))
    assert rows, "the survey found no modules in runs/"
    assert set(V.census(rows)) <= {V.CURRENT, V.CONTRACT_STALE,
                                   V.PROVENANCE_STALE, V.UNSTAMPED,
                                   V.OFF_CORPUS}
    assert V.census(rows).get(V.UNSTAMPED, 0) > 0, V.census(rows)


def test_the_version_cli_reports_the_census_and_exits_zero():
    r = subprocess.run([PY, str(HERE / "version.py"), "--json"],
                       capture_output=True, text=True, cwd=str(HERE))
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip(), "the CLI printed nothing"
    payload = json.loads(r.stdout)
    assert "census" in payload and "rows" in payload


# ==========================================================================
#  7.  The survivors of the first mutation sweep
# ==========================================================================
#
# Eight guards were pinned by nothing. Four of them were pinned by tests that
# READ AS THOROUGH and were satisfied by `pytest`'s tmp_path echoing the test's
# own name — see `_report`. The other four had no test at all. Both halves are
# below.

def test_the_MODULE_listing_is_SORTED_whatever_the_filesystem_says(
        tmp_path, monkeypatch):
    """⛔ Two trees written in opposite orders is NOT a test of this.

    The first attempt built directories in reverse and compared — and APFS
    handed both back in the same order, so `sorted()` could be deleted and
    nothing died. The filesystem's order is not ours to arrange, so the only
    honest test replaces `listdir` outright.
    """
    d = _fake_run(tmp_path / "r", {"m1": _st("c", "p"), "m2": _st("c", "p"),
                                   "m3": _st("c", "p")})
    real = os.listdir
    monkeypatch.setattr(V.os, "listdir",
                        lambda p: list(reversed(sorted(real(p)))))
    assert V.module_ids(str(d)) == ["m1", "m2", "m3"]


def test_the_RUN_listing_is_SORTED_whatever_the_filesystem_says(
        tmp_path, monkeypatch):
    """The rows are the report. A report whose order is the inode order is not
    diffable against yesterday's, which is most of what a census is for."""
    cur = {"m1": _st("c", "p")}
    for n in ("run-a", "run-b", "run-c"):
        _fake_run(tmp_path / n, {"m1": _st("c", "p")})
    real = os.listdir
    monkeypatch.setattr(V.os, "listdir",
                        lambda p: list(reversed(sorted(real(p)))))
    rows = V.survey(str(tmp_path), cur)
    assert [r["run"] for r in rows] == ["run-a", "run-b", "run-c"]


def test_run_json_IS_the_fallback_when_the_sidecar_is_gone(tmp_path):
    """A module whose sidecar was deleted is not thereby unstamped.

    Two records of the same two hashes is deliberate: the sidecar travels with
    the module, `run.json` survives the sidecar. Dropping the fallback would
    mark a whole run stale the first time somebody tidied a directory — and it
    would re-translate every clause in it, at cost.
    """
    _run(_cfg(tmp_path, ["m0091"], run_name="one"))
    (tmp_path / "one" / f"m0091{V.STAMP_SUFFIX}").unlink()
    st = V.read_stamp(str(tmp_path / "one"), "m0091")
    assert st and st["contract_hash"] and st["provenance_hash"]


def test_an_UNSTAMPED_clause_CANNOT_be_waived(tmp_path):
    """⛔ A waiver excuses a KNOWN provenance transition, nothing else.

    `unstamped` means the artifact never recorded what it was made from, so
    there is no transition to vouch for — and a waiver that covered it would
    be the one-word amnesty for every artifact predating the stamp, which is
    all of them.
    """
    _run(_cfg(tmp_path, ["m0091"], run_name="one"))
    _unstamp(tmp_path / "one", "m0091")
    path = _waiver(tmp_path, stored_provenance_hash="x",
                   current_provenance_hash=_now_provenance(
                       _cfg(tmp_path, ["m0091"], run_name="two")))
    _run(_cfg(tmp_path, ["m0091"], run_name="two"),
         _args(only_stale=True, waivers=path))
    assert (tmp_path / "two" / "m0091.json").exists(), \
        "a waiver excused a clause that never recorded a provenance at all"


def test_an_EMPTY_waiver_file_is_REFUSED(tmp_path):
    """It is either a mistake or a no-op, and both are worth saying aloud.

    Reading it as "nothing to excuse" makes an empty file indistinguishable
    from a file whose waivers all expired — and the second is a situation the
    operator has to know about.
    """
    p = tmp_path / "w.json"
    p.write_text(json.dumps({"waivers": []}))
    with pytest.raises(V.WaiverError):
        V.load_waivers(str(p))


def test_a_MISSING_waiver_file_is_REFUSED(tmp_path):
    """⛔ `--waivers typo.json` must not run as though nothing was waived.

    That is the check-that-cannot-run failure: the operator asked for a
    partial re-run under a signed exception, and got a full one with no
    exception and no complaint. Whether that costs more or less money than
    intended, it is not what was asked for.
    """
    with pytest.raises(V.WaiverError):
        V.load_waivers(str(tmp_path / "nope.json"))


def test_a_waiver_over_a_CURRENT_clause_is_UNUSED_not_HONOURED(tmp_path,
                                                               capsys):
    """⛔ A waiver may only be honoured where it actually excused work.

    A CURRENT clause is not being re-translated anyway, so counting it as
    honoured makes the report say a signed exception did something. An
    operator reading `waiver honoured: 400 clause(s)` would believe 400
    re-translations were skipped on their authority when the answer is zero —
    and the same misreport hides an expired waiver, because the honoured line
    would be there either way.
    """
    cfg_one = _cfg(tmp_path, ["m0091"], run_name="one")
    _run(cfg_one)
    now = _now_provenance(cfg_one)
    path = _waiver(tmp_path, stored_provenance_hash=now,
                   current_provenance_hash=now)
    _run(_cfg(tmp_path, ["m0091"], run_name="two"),
         _args(only_stale=True, waivers=path), factory=_NeverCalled)
    out = _report(capsys)
    assert "waiver UNUSED" in out, out
    assert "waiver honoured" not in out, out
