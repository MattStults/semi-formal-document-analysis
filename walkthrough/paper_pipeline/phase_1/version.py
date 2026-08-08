"""Artifact versioning: what a stored module was made from, and when it re-runs.

    ../../../semi-formal-experiment/.venv/bin/python version.py            # census
    ../../../semi-formal-experiment/.venv/bin/python version.py --json     # machine
    ../../../semi-formal-experiment/.venv/bin/python version.py --rows     # per module

⛔ WHY THIS FILE EXISTS. `graveyard.contract_hash` and `graveyard.provenance_hash`
were written when the graveyard landed and were called in exactly ONE place: as
metadata on a FAILURE record. `[RAN]` zero occurrences across every
`runs/*/run.json` and every `runs/*/m*.json`. Nothing compared a stored hash to
a current one and nothing selected a clause for re-translation, so "artifacts
have a version which determines when they run again" was two hash functions and
a docstring. This module is the missing half.

THE TWO HASHES, AND WHY THEY STAY SEPARATE (ruling, Matt, 2026-08-08)

    contract_hash    clause text + the schema source.
                     Moved => the artifact MAY NO LONGER VALIDATE.  Re-run.
    provenance_hash  prompt + model + request params.
                     Moved => it is not reproducible from today's inputs.
                     ⭐ Re-run as well, by ruling — but it is a DIFFERENT fact.

⚠️ Both now trigger a re-run, and that is precisely why they must not be
collapsed into one hash. A module whose `provenance_hash` moved is still VALID:
it compiles, it links, it may be cited as a translation of its clause. It simply
cannot be cited as evidence about the CURRENT prompt. A module whose
`contract_hash` moved may be none of those things. One hash cannot say which,
and — see `graveyard.py`'s docstring — one hash marks the whole corpus stale on
every prompt edit, which is the state that makes iteration unaffordable.

FIVE STATES, and two of them are the interesting ones

    current              both hashes match. Nothing to do.
    provenance-stale     only the provenance hash moved.  Re-run; WAIVABLE.
    contract-stale       the contract hash moved (whatever else did).
                         Re-run; ⛔ NEVER waivable.
    unstamped            the artifact makes no claim about its inputs.
                         Treated as stale: "no claim" is not "current", and
                         every module in `runs/` as of 2026-08-08 is one of
                         these. A survey that called them `current` would be
                         asserting a provenance nobody ever recorded.
    no-longer-in-corpus  the clause is gone. It cannot be re-run — there is
                         nothing to send — so it is reported apart from the
                         work list rather than swelling it.

⚠️ PRECEDENCE. When both hashes moved the state is `contract-stale`, not
`provenance-stale`, and both differing hashes are named in the row. Reporting
the softer state would make the artifact eligible for a waiver, and a contract
change is the one thing a waiver may never excuse.

⚠️ ACROSS RUNS, THE BEST STATE WINS. A re-run writes a NEW directory and the
older, staler copy stays on disk forever. Taking the worst state per clause
would make anything ever translated under an older prompt permanently stale, so
`--only-stale` would select the whole corpus every time and the feature would be
pointless.

DETERMINISM IS THE WHOLE POINT. A hash that moves between two runs over
identical inputs turns every downstream decision into noise. So: sha256 only,
never Python's salted `hash()`; every dict serialised with `sort_keys=True`;
every directory listing sorted. `test_version.py` pins this across process
restarts with three different `PYTHONHASHSEED` values.
"""

import argparse
import json
import os
import sys

import graveyard as gy

HERE = os.path.dirname(os.path.abspath(__file__))

CURRENT = "current"
CONTRACT_STALE = "contract-stale"
PROVENANCE_STALE = "provenance-stale"
UNSTAMPED = "unstamped"
OFF_CORPUS = "no-longer-in-corpus"

#: The states `--only-stale` selects for re-translation.
STALE = (CONTRACT_STALE, PROVENANCE_STALE, UNSTAMPED)

#: Lower is better. `best_per_clause` minimises over this.
SEVERITY = {CURRENT: 0, PROVENANCE_STALE: 1, CONTRACT_STALE: 2,
            UNSTAMPED: 3, OFF_CORPUS: 4}

#: Printed in this order, always, so two censuses can be read side by side.
ORDER = (CURRENT, PROVENANCE_STALE, CONTRACT_STALE, UNSTAMPED, OFF_CORPUS)

#: The stamp sidecar. See `write_stamp` for why it is a sidecar.
STAMP_SUFFIX = ".version.json"

#: `.json` files in a run directory that are not modules.
NOT_A_MODULE = ("run.json", "concepts.json")


class VersionError(RuntimeError):
    """The survey cannot answer, and must not answer approximately."""


class WaiverError(VersionError):
    """An intention flag that does not meet its own bar."""


# ==========================================================================
#  1.  The stamp
# ==========================================================================

def stamp(clause_text, schema_source, system, model, temperature,
          params=None):
    """What a translated artifact was made from, as two hashes.

    Deterministic in every argument and in nothing else. `params` is
    canonicalised by `graveyard.provenance_hash`; an empty one hashes exactly
    as the old two-argument call did, so adding the argument did not restamp
    the world.
    """
    return {
        "contract_hash": gy.contract_hash(clause_text, schema_source),
        "provenance_hash": gy.provenance_hash(system, model, temperature,
                                              params=params),
        "stamp_version": 1,
    }


def write_stamp(outdir, clause_id, st):
    """Beside the module, as `<clause_id>.version.json`.

    ⭐ WHY A SIDECAR AND NOT A FIELD OF THE MODULE. `translate.py` says it
    plainly: *"the object is the record; the .lp is a rendering of it"* — so a
    version that lived only in the `.lp` would be lost the moment the object
    was re-rendered, and the `.lp` is therefore not where it goes. But the
    object itself is a CONTRACT THE MODEL MUST SATISFY, validated by
    `schema.py` with `extra="forbid"`. Putting the hashes inside it would make
    them something the MODEL emits — forgeable, and wrong in kind: provenance
    is a fact about the run, not a claim the translation makes about itself.
    So the stamp sits beside the object, is written by the harness, and is
    keyed to the module by filename. The same two hashes also go into
    `run.json`'s per-clause record, which is the run-level index; the sidecar
    is what survives a module being copied out of its run directory.

    The `.lp` gets the hashes too, as a plain `%` comment — for a human
    reading the rendering on its own. `%%` is the module header and `link.py`
    parses it, so a version line there would be a header field nothing
    declares. The comment is never read back: it is a courtesy, not the record.
    """
    path = os.path.join(outdir, f"{clause_id}{STAMP_SUFFIX}")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(st, fh, indent=1, sort_keys=True)
    return path


def lp_comment(st):
    """The version line appended to a rendered `.lp`. A comment, not a header."""
    return (f"% version: contract={st['contract_hash']} "
            f"provenance={st['provenance_hash']}   "
            f"(the record is {STAMP_SUFFIX}; this line is a courtesy)")


def read_stamp(rundir, clause_id, run_json=None):
    """The sidecar, else `run.json`'s record for that clause, else None.

    Two places, deliberately: the sidecar travels with the module, and
    `run.json` survives the sidecar being deleted. Neither is invented — a
    module with no stamp anywhere reads `unstamped`, which is stale.
    """
    p = os.path.join(rundir, f"{clause_id}{STAMP_SUFFIX}")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as fh:
            st = json.load(fh)
        if st.get("contract_hash") and st.get("provenance_hash"):
            return st
    if run_json is None:
        rj = os.path.join(rundir, "run.json")
        if not os.path.exists(rj):
            return None
        try:
            with open(rj, encoding="utf-8") as fh:
                run_json = json.load(fh)
        except (ValueError, OSError):
            return None
    for r in (run_json.get("results") or []):
        if r.get("clause_id") == clause_id and r.get("contract_hash"):
            return {"contract_hash": r["contract_hash"],
                    "provenance_hash": r.get("provenance_hash"),
                    "stamp_version": r.get("stamp_version", 1)}
    return None


# ==========================================================================
#  2.  Classification
# ==========================================================================

def classify(stored, current):
    """(state, [names of the hashes that differ]).

    `stored` is what the artifact claims; `current` is what today's inputs
    would produce. Either may be None and each None means something different:
    no stored stamp is `unstamped`; no current stamp is a clause that has left
    the corpus.
    """
    if current is None:
        return OFF_CORPUS, []
    if not stored:
        return UNSTAMPED, ["contract_hash", "provenance_hash"]
    differing = [k for k in ("contract_hash", "provenance_hash")
                 if stored.get(k) != current.get(k)]
    if "contract_hash" in differing:
        return CONTRACT_STALE, differing
    if differing:
        return PROVENANCE_STALE, differing
    return CURRENT, []


def module_ids(rundir):
    """The clause ids a run directory holds artifacts for. Sorted, always.

    ⛔ THE RULE IS "THE STEM CARRIES NO SECOND SUFFIX", and it is not fussiness.
    The first version excluded `run.json`, `concepts.json` and `*.version.json`
    by name — and the first census over the real `runs/` reported **21
    `no-longer-in-corpus` modules**, every one of them a
    `<clause>.transcript.json`. The number looked like a finding about the
    corpus (clauses that had been removed) and was an artefact of the glob.

    A run directory holds `<id>.json`, `<id>.version.json`,
    `<id>.transcript.json` and whatever the next stage adds. Enumerating the
    non-modules cannot keep up with that; enumerating the MODULE's shape can.
    A clause id carries no dot, so a stem with one is a sidecar of some kind.
    """
    if not os.path.isdir(rundir):
        return []
    out = []
    for name in sorted(os.listdir(rundir)):
        if not name.endswith(".json") or name in NOT_A_MODULE:
            continue
        stem = name[:-len(".json")]
        if "." in stem:
            continue
        out.append(stem)
    return out


def survey(runs_root, current):
    """One row per (run, module). `current` maps clause_id -> stamp.

    Sorted by run then clause so the output does not inherit the filesystem's
    directory order.
    """
    rows = []
    if not os.path.isdir(runs_root):
        return rows
    for run in sorted(os.listdir(runs_root)):
        rundir = os.path.join(runs_root, run)
        if not os.path.isdir(rundir):
            continue
        for cid in module_ids(rundir):
            stored = read_stamp(rundir, cid)
            state, differing = classify(stored, current.get(cid))
            rows.append({"run": run, "clause_id": cid, "state": state,
                         "differing": differing, "stored": stored,
                         "current": current.get(cid)})
    return rows


def best_per_clause(rows):
    """The most current row each clause has anywhere. See the module docstring."""
    best = {}
    for r in rows:
        cur = best.get(r["clause_id"])
        if cur is None or SEVERITY[r["state"]] < SEVERITY[cur["state"]]:
            best[r["clause_id"]] = r
    return best


def census(rows):
    """{state: count}, in `ORDER`, omitting states with no members."""
    counts = {}
    for r in rows:
        counts[r["state"]] = counts.get(r["state"], 0) + 1
    return {k: counts[k] for k in ORDER if k in counts}


def format_census(counts, total=None, label="modules"):
    """⛔ Every rate needs its denominator. So does every count.

    A staleness line that says "12 stale" without saying "of what" is the
    number that turns into a 593-clause spend by accident.
    """
    n = total if total is not None else sum(counts.values())
    body = ", ".join(f"{counts.get(k, 0)} {k}" for k in ORDER
                     if counts.get(k)) or "nothing"
    return f"staleness   : {body}   (of {n} {label})"


# ==========================================================================
#  3.  Current inputs
# ==========================================================================

def schema_source():
    """The text `contract_hash` covers. A function so a test can move it."""
    with open(os.path.join(HERE, "schema.py"), encoding="utf-8") as fh:
        return fh.read()


def run_params(cfg, prov=None):
    """The request-shaping knobs that go into `provenance_hash`.

    Each one changes the artifact the model produces, and none of them is the
    prompt or the model id:

      max_tokens       a truncated completion is a different artifact
      format_forcing   json_schema / json_object / none is a different task
      max_attempts     a module repaired over three turns is not the module a
                       single turn produced

    ⚠️ Kept deliberately SHORT. Every key added here marks the whole corpus
    provenance-stale the next time it changes, and each such change now costs a
    re-run — so a knob belongs here only if it changes the answer.
    """
    m = cfg.get("model") or {}
    return {
        "max_tokens": (prov.max_tokens if prov is not None
                       else m.get("max_tokens")),
        "format_forcing": m.get("format_forcing", "json_schema"),
        "max_attempts": int((cfg.get("repair") or {}).get("max_attempts", 1)),
    }


def model_params(cfg, prov=None):
    """(model, temperature, params) for the CURRENT configuration."""
    if prov is None:
        import translate                                       # lazy: no cycle
        prov = translate.resolve_provider(cfg, _NoOverrides())
    return prov.model, prov.temperature, run_params(cfg, prov)


class _NoOverrides:
    provider = model = max_tokens = None


def current_map(cfg, system, model, temperature, params=None,
                schema_src=None):
    """clause_id -> the stamp today's inputs WOULD produce, for every clause."""
    import translate                                           # lazy: no cycle
    src = schema_source() if schema_src is None else schema_src
    c = cfg["corpus"]
    return {r[c["id_key"]]: stamp(r.get(c["text_key"], ""), src, system,
                                  model, temperature, params)
            for r in translate.load_corpus(cfg)}


# ==========================================================================
#  4.  The intention flag
# ==========================================================================
#
# ⭐ WHAT THIS IS FOR, and what it is designed AGAINST. A provenance change
# re-runs by ruling. But some prompt edits genuinely do not change the answer —
# a typo in a comment, a reflowed paragraph — and re-translating 593 clauses to
# find that out costs real money. The waiver is how someone says "I looked, and
# this particular move of the prompt does not oblige a re-run."
#
# It is also the mechanism by which one word could make 593 stale modules
# not-stale, so every property below exists to make that hard:
#
#   * IT NAMES THE EXACT TRANSITION. A waiver carries the stored hash it
#     excuses AND the current hash it excuses it against. The next prompt edit
#     moves the current hash and every waiver written against the old one stops
#     applying, automatically. A waiver is a statement about one move, not a
#     standing exemption.
#   * IT ENUMERATES CLAUSES. No wildcard, no "all", no empty list — those are
#     refused by name. Listing 593 ids is mechanical; the file that holds them
#     IS the record of what was waived.
#   * IT CANNOT TOUCH A CONTRACT CHANGE. A waiver naming a contract-stale
#     clause does not silently fail to apply — it REFUSES THE RUN. Silence
#     there would leave the operator believing something was covered.
#   * IT IS ATTACHED TO A FILE, NOT A FLAG. `--waivers path` points at a
#     reviewable, diffable, committable artifact carrying who, when and why.
#     A bare `--force` would leave its record only in a shell history.
#   * IT IS INERT WITHOUT `--only-stale`. Nothing is being skipped otherwise,
#     so a waiver file must not quietly change what a run translates.
#   * THE RUN SAYS WHAT IT HONOURED — on screen, with who and why, and in
#     `run.json`. A waiver that matched nothing is reported as UNUSED, because
#     a stale or mistyped waiver file that is silently ignored is the
#     pass-indistinguishable-from-did-not-run failure wearing a bureaucratic hat.

REQUIRED_WAIVER_KEYS = ("clause_ids", "stored_provenance_hash",
                        "current_provenance_hash", "who", "why", "date")

#: Refused outright as clause ids. Each is a way of saying "everything".
FORBIDDEN_IDS = ("*", "all", "ALL", "any", "-", "")


def load_waivers(path):
    """Read and VALIDATE. Every failure here is a refusal, never a warning."""
    if not os.path.exists(path):
        raise WaiverError(f"no waiver file at {path}")
    try:
        with open(path, encoding="utf-8") as fh:
            blob = json.load(fh)
    except ValueError as exc:
        raise WaiverError(f"{path} is not readable JSON: {exc}") from exc
    items = blob.get("waivers") if isinstance(blob, dict) else blob
    if not items:
        raise WaiverError(
            f"{path} carries no waivers. An empty waiver file is either a "
            f"mistake or a no-op, and both should be said out loud rather "
            f"than read as 'nothing to excuse'")
    out = []
    for i, w in enumerate(items):
        where = f"{path}[{i}]"
        for k in REQUIRED_WAIVER_KEYS:
            if not w.get(k):
                raise WaiverError(
                    f"{where}: `{k}` is missing or empty. A waiver is a signed "
                    f"statement that a re-run is not owed; every field of "
                    f"{', '.join(REQUIRED_WAIVER_KEYS)} is part of the "
                    f"signature, and one without them is not reviewable")
        ids = w["clause_ids"]
        if not isinstance(ids, list):
            raise WaiverError(f"{where}: `clause_ids` must be a list")
        bad = [c for c in ids if str(c).strip() in FORBIDDEN_IDS]
        if bad:
            raise WaiverError(
                f"{where}: clause_ids contains {bad!r}. There is deliberately "
                f"no wildcard: a waiver has to ENUMERATE the clauses it "
                f"excuses, because the whole risk of this flag is one word "
                f"making the entire corpus not-stale. Listing the ids is "
                f"mechanical, and the list is the record of what was waived")
        out.append(dict(w))
    return out


def apply_waivers(states, waivers):
    """(waived_ids, honoured, unused). `states` maps clause_id -> row.

    ⛔ A waiver naming a contract-stale clause RAISES. It does not quietly not
    apply: the operator wrote it down believing it covered that clause.
    """
    waived, honoured, unused = set(), [], []
    for w in waivers:
        hit = []
        for cid in w["clause_ids"]:
            row = states.get(cid)
            if row is None:
                continue
            if row["state"] == CONTRACT_STALE:
                raise WaiverError(
                    f"waiver by {w['who']} ({w['date']}) names {cid}, which is "
                    f"CONTRACT-stale: its clause text or the schema source "
                    f"moved, so the stored module may no longer VALIDATE. A "
                    f"contract change is never waivable — that is the whole "
                    f"reason the two hashes are kept apart. Re-translate "
                    f"{cid}, or remove it from the waiver")
            if row["state"] != PROVENANCE_STALE:
                continue
            stored = (row["stored"] or {}).get("provenance_hash")
            current = (row["current"] or {}).get("provenance_hash")
            if (stored == w["stored_provenance_hash"]
                    and current == w["current_provenance_hash"]):
                hit.append(cid)
        if hit:
            waived.update(hit)
            honoured.append({**w, "clause_ids": sorted(hit)})
        else:
            unused.append(w)
    return waived, honoured, unused


def format_waivers(honoured, unused):
    """What the run prints. Both halves; the unused half is the loud one."""
    lines = []
    for w in honoured:
        lines.append(
            f"waiver honoured: {len(w['clause_ids'])} clause(s) "
            f"[{', '.join(w['clause_ids'][:6])}"
            f"{' …' if len(w['clause_ids']) > 6 else ''}] "
            f"— {w['who']}, {w['date']}: {w['why']}")
    for w in unused:
        lines.append(
            f"⚠️ waiver UNUSED — matched nothing: {w['who']}, {w['date']} over "
            f"{len(w['clause_ids'])} clause id(s). Either the provenance hash "
            f"it names is no longer current (a waiver expires when the prompt "
            f"moves again, by design), or the ids are wrong. Nothing was "
            f"excused by it")
    return "\n".join(lines)


# ==========================================================================
#  5.  CLI
# ==========================================================================

def main(argv=None):
    import translate                                           # lazy: no cycle
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", default=os.path.join(HERE, "config.json"))
    ap.add_argument("--runs", default=None,
                    help="the runs directory (default: output.dir)")
    ap.add_argument("--json", action="store_true", dest="as_json")
    ap.add_argument("--rows", action="store_true",
                    help="one line per (run, module), not just the counts")
    a = ap.parse_args(argv)

    cfg = translate.load_config(a.config)
    system = translate.build_system(cfg)
    model, temp, params = model_params(cfg)
    cur = current_map(cfg, system, model, temp, params)
    root = a.runs or translate.rel(cfg["output"]["dir"])
    rows = survey(root, cur)
    best = best_per_clause(rows)
    best_rows = [best[k] for k in sorted(best)]

    if a.as_json:
        print(json.dumps({"runs_root": root,
                          "census": census(rows),
                          "census_per_clause": census(best_rows),
                          "rows": rows}, indent=1, sort_keys=True))
        return 0

    print(f"runs        : {root}")
    print(format_census(census(rows), label="stored modules"))
    print(format_census(census(best_rows), label="distinct clauses "
                                                 "(best state anywhere)"))
    if a.rows:
        for r in rows:
            extra = f"  [{', '.join(r['differing'])}]" if r["differing"] else ""
            print(f"  {r['run']}  {r['clause_id']:>6}  {r['state']}{extra}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
