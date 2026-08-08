"""Mutation sweep over the artifact-versioning guards — break each, confirm a test dies.

    ../../../semi-formal-experiment/.venv/bin/python mutate_version.py

⭐ IT IS THE SAME ENGINE `mutate_seats.py` RUNS, imported rather than copied:
a green baseline through the same isolation path, return-code triage, a
collected-count comparison, and a third `error` status that is never folded
into "no tests died". See that file's docstring for why each of those exists
and which review found it missing. Only the mutant tables here are this
feature's own.

⚠️ THREE SWEEPS, because the guards live in three files. `version.py` carries
the classification, the survey and the waiver rules; `graveyard.py` carries the
two hash functions themselves; `translate.py` carries THE WIRING — and the
wiring is where this feature could have gone missing entirely, because a
correct `version.py` that nothing calls is exactly the state the two hash
functions were in for weeks: every unit test green, not one artifact stamped.

The graveyard table is deliberately SHORT — it covers only the `params`
argument added on 2026-08-08, because those are the only graveyard guards
`test_version.py` pins. `test_graveyard.py` pins the rest, and mutating them
against the wrong test file would report survivors that are really just the
wrong suite.

⚠️ THE FIRST RUN OF THIS SWEEP FOUND 8 SURVIVORS OF 25, and four of them were
guards whose tests LOOKED thorough: `pytest`'s `tmp_path` embeds the test's own
name, `run()` prints that path, and `assert "unused" in out` was therefore
satisfied by the directory name rather than by the report. See
`test_version._report`. That is the whole argument for running this: the four
tests were written by someone who believed they were checking those lines.

⛔ WHAT A SURVIVOR HERE WOULD MEAN. Every mutant below is a way for the
pipeline to under-report staleness — to call a stale artifact current, to let a
waiver excuse a contract change, or to make a version depend on something that
is not an input. Each one is silent by construction: the run looks normal, the
census looks plausible, and the corpus quietly stops being re-translated.
"""
import os
import sys

import mutate_seats

SRC = os.path.join(mutate_seats.HERE, "version.py")
GRAVEYARD = os.path.join(mutate_seats.HERE, "graveyard.py")
TRANSLATE = os.path.join(mutate_seats.HERE, "translate.py")
TESTS = os.path.join(mutate_seats.HERE, "test_version.py")

# (name, old, new) — each deletes or inverts exactly one guard.
MUTANTS = [
    # --- classification: the four states, and which of them is stale --------
    ("an-UNSTAMPED-artifact-is-treated-as-CURRENT",
     '    if not stored:\n        return UNSTAMPED, ["contract_hash", "provenance_hash"]',
     '    if not stored:\n        return CURRENT, []'),
    ("a-CONTRACT-change-loses-its-PRECEDENCE-over-a-provenance-change",
     '    if "contract_hash" in differing:\n        return CONTRACT_STALE, differing',
     '    if False:\n        return CONTRACT_STALE, differing'),
    ("a-clause-that-LEFT-THE-CORPUS-is-reported-as-work",
     '    if current is None:\n        return OFF_CORPUS, []',
     '    if current is None:\n        return UNSTAMPED, []'),
    ("the-differing-hashes-are-not-reported",
     '    differing = [k for k in ("contract_hash", "provenance_hash")\n'
     '                 if stored.get(k) != current.get(k)]',
     '    differing = []\n'
     '    differing = differing or [k for k in ("contract_hash", "provenance_hash")\n'
     '                              if stored.get(k) != current.get(k)] and []'),

    # --- ⛔ THE RULING ITSELF: what re-runs -------------------------------
    ("a-PROVENANCE-change-only-relabels-and-never-re-runs",
     'STALE = (CONTRACT_STALE, PROVENANCE_STALE, UNSTAMPED)',
     'STALE = (CONTRACT_STALE, UNSTAMPED)'),
    ("an-UNSTAMPED-artifact-is-not-work",
     'STALE = (CONTRACT_STALE, PROVENANCE_STALE, UNSTAMPED)',
     'STALE = (CONTRACT_STALE, PROVENANCE_STALE)'),

    # --- across runs, the BEST state wins ---------------------------------
    ("the-WORST-state-across-runs-wins-so-nothing-is-ever-current",
     '        if cur is None or SEVERITY[r["state"]] < SEVERITY[cur["state"]]:',
     '        if cur is None or SEVERITY[r["state"]] > SEVERITY[cur["state"]]:'),

    # --- what counts as a module on disk ----------------------------------
    ("a-SIDECAR-is-read-as-a-module",
     '        stem = name[:-len(".json")]\n        if "." in stem:\n            continue',
     '        stem = name[:-len(".json")]'),
    ("run_json-and-the-concept-table-are-read-as-modules",
     '        if not name.endswith(".json") or name in NOT_A_MODULE:',
     '        if not name.endswith(".json"):'),
    ("the-directory-listing-is-not-SORTED",
     '    for name in sorted(os.listdir(rundir)):',
     '    for name in os.listdir(rundir):'),
    ("the-RUN-directories-are-not-SORTED",
     '    for run in sorted(os.listdir(runs_root)):',
     '    for run in os.listdir(runs_root):'),

    # --- the stamp on disk ------------------------------------------------
    ("the-STAMP-SIDECAR-is-written-with-no-provenance-hash",
     '        "provenance_hash": gy.provenance_hash(system, model, temperature,\n'
     '                                              params=params),',
     '        "provenance_hash": gy.contract_hash(system, model),'),
    ("the-LP-version-line-is-written-as-a-HEADER-DIRECTIVE",
     '    return (f"% version: contract={st[\'contract_hash\']} "',
     '    return (f"%% version: contract={st[\'contract_hash\']} "'),
    ("a-run_json-record-is-never-consulted-when-the-sidecar-is-gone",
     '    for r in (run_json.get("results") or []):',
     '    for r in []:'),

    # --- the census a human reads before spending -------------------------
    ("the-census-loses-its-DENOMINATOR",
     '    return f"staleness   : {body}   (of {n} {label})"',
     '    return f"staleness   : {body}"'),

    # --- ⛔ the intention flag ---------------------------------------------
    ("a-waiver-may-excuse-a-CONTRACT-change",
     '            if row["state"] == CONTRACT_STALE:',
     '            if False:'),
    ("a-waiver-NEVER-EXPIRES-because-the-current-hash-is-not-checked",
     '            if (stored == w["stored_provenance_hash"]\n'
     '                    and current == w["current_provenance_hash"]):',
     '            if stored == w["stored_provenance_hash"]:'),
    ("a-waiver-applies-to-any-state-at-all",
     '            if row["state"] != PROVENANCE_STALE:\n                continue',
     '            if False:\n                continue'),
    ("a-WILDCARD-clause-id-is-accepted",
     'FORBIDDEN_IDS = ("*", "all", "ALL", "any", "-", "")',
     'FORBIDDEN_IDS = ()'),
    ("a-waiver-with-no-author-no-reason-and-no-date-is-accepted",
     'REQUIRED_WAIVER_KEYS = ("clause_ids", "stored_provenance_hash",\n'
     '                        "current_provenance_hash", "who", "why", "date")',
     'REQUIRED_WAIVER_KEYS = ("clause_ids", "stored_provenance_hash")'),
    ("an-UNUSED-waiver-is-silent",
     '    for w in unused:\n        lines.append(',
     '    for w in []:\n        lines.append('),
    ("an-EMPTY-waiver-file-is-read-as-nothing-to-excuse",
     '    if not items:', '    if False:'),
    ("a-missing-waiver-file-is-read-as-no-waivers",
     '    if not os.path.exists(path):', '    if False:'),

    # --- determinism ------------------------------------------------------
    ("the-schema-source-is-not-part-of-the-contract-hash",
     '        "contract_hash": gy.contract_hash(clause_text, schema_source),',
     '        "contract_hash": gy.contract_hash(clause_text, ""),'),
    ("the-PROMPT-is-not-part-of-the-provenance-hash",
     '        "provenance_hash": gy.provenance_hash(system, model, temperature,\n'
     '                                              params=params),',
     '        "provenance_hash": gy.provenance_hash("", model, temperature,\n'
     '                                              params=params),'),
]

#: Only the `params` argument — see the docstring for why this table is short.
GRAVEYARD_MUTANTS = [
    ("params-are-serialised-WITHOUT-sort_keys",
     '        h.update(("params:" + json.dumps(params, sort_keys=True,\n'
     '                                         default=str)).encode())',
     '        h.update(("params:" + json.dumps(list(params.items()),\n'
     '                                         default=str)).encode())'),
    ("an-EMPTY-params-hashes-DIFFERENTLY-from-no-params",
     '    if params:\n        h.update(', '    if True:\n        h.update('),
    ("params-do-not-reach-the-hash-at-all",
     '    if params:\n        h.update(', '    if False:\n        h.update('),
]


#: ⭐ THE WIRING, which is where this feature could have gone missing entirely.
#: A correct `version.py` that nothing calls is precisely the state the two hash
#: functions were in for weeks — every unit test green, and not one artifact
#: stamped. These mutants delete the CALLS, not the logic.
TRANSLATE_MUTANTS = [
    ("the-only-stale-flag-is-read-and-ignored",
     '    if getattr(args, "only_stale", False):', '    if False:'),
    ("an-empty-stale-set-still-goes-on-to-spend",
     '        if not jobs:\n            print("nothing is stale',
     '        if False:\n            print("nothing is stale'),
    ("the-STAMP-SIDECAR-is-never-written",
     '            version.write_stamp(outdir, cid, _stamp)',
     '            pass'),
    ("the-per-clause-hashes-never-reach-run_json",
     '            rec.update(_stamp)', '            pass'),
    ("the-LP-is-written-without-its-version-line",
     '                fh.write(lp + version.lp_comment(_stamp) + "\\n")',
     '                fh.write(lp)'),
    ("the-RUN-LEVEL-version-block-never-reaches-run_json",
     '        **(version_block or {}),', '        **{},'),
]


def main(argv=None):
    rc = mutate_seats.main(argv, mutants=MUTANTS, module_path=SRC,
                           test_path=TESTS)
    print("\n" + "=" * 72)
    print("graveyard.py — the `params` argument only")
    print("=" * 72)
    rc2 = mutate_seats.main(argv, mutants=GRAVEYARD_MUTANTS,
                            module_path=GRAVEYARD, test_path=TESTS)
    print("\n" + "=" * 72)
    print("translate.py — the WIRING: the calls, not the logic")
    print("=" * 72)
    rc3 = mutate_seats.main(argv, mutants=TRANSLATE_MUTANTS,
                            module_path=TRANSLATE, test_path=TESTS)
    return rc or rc2 or rc3


if __name__ == "__main__":
    sys.exit(main())
