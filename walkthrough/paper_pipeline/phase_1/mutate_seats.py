"""Mutation sweep over `seats.py` — break each guard on purpose, confirm a
test dies. Also the ENGINE `mutate_readback_r3.py` runs on.

    ../../../semi-formal-experiment/.venv/bin/python mutate_seats.py

⭐ A GUARD NO MUTATION KILLS IS UNPINNED, and this repo treats an unpinned
guard as not shipped (`STEP_stage4.md` §8: *"stage 4 ships with its own
mutation run at 0 survivors or it does not ship"*). The first run of this
sweep found 16 of 71 guards surviving with all 103 tests green; every one of
them now has a named test, and the sweep is at 0.

⛔ THE FAILURE MODE THIS FILE IS DESIGNED AGAINST — and the one the first
version of it SHIPPED. Rewritten 2026-08-08 after an adversarial review
demonstrated it reporting **`83 mutants applied, 0 survivor(s)`, exit 0,
against a RED test suite**. The instrument that certifies everything else
could not tell *killed* from *never ran*. The whole kill rule was
`killed = r.returncode != 0`, which meant:

  * a suite that was already failing made **every** mutant look killed;
  * a mutant that broke the import gave pytest `rc=2` — a COLLECTION ERROR —
    and was reported KILLED;
  * nothing recorded WHICH test died, so a mutant killed by an unrelated flake
    was indistinguishable from one killed by its named guard.

`mutate_schema.py`, the sibling in this directory, guarded all three and said
so in its docstring. This file now does the same, in the same words, and adds
the fourth thing that review found:

  * a green baseline **through the same isolation path** before any mutation;
  * return-code triage — `rc in (2,3,4,5)` is ERROR, never `killed`;
  * a collected-count comparison — a run that did not collect the baseline's
    number of tests is ERROR, never `survivor`;
  * an `error` status at all. There was none; every failure folded into
    `killed`, which is the flattering direction.

⛔ AND IT NO LONGER REWRITES THE SOURCE IN PLACE. The old version edited
`seats.py` and restored it in a `finally`; an interrupted run left the working
tree mutated. Each mutant is now written into a MIRROR directory — every entry
of `phase_1/` symlinked (directories) or copied (files), with the one mutated
module written over the copy. The real file's digest is asserted unchanged.

⚠️ THE MIRROR'S LOCATION IS LOAD-BEARING, not a temp-dir detail. `seats.py`
computes `WALKTHROUGH` as `dirname(dirname(HERE))` and `link.py` resolves the
clause corpus relative to the repo root above that, so a mirror under `/tmp`
makes `survey()` raise `FileNotFoundError` and every mutant "die" for a reason
that has nothing to do with its guard. The mirror is therefore created inside
`paper_pipeline/`, dot-prefixed so pytest never collects it, and removed in a
`finally`.

⚠️ ONE TRAP, found inside the first version and kept because it is still real.
Python invalidates a `.pyc` on (mtime SECONDS, size). Two mutants written
inside the same second with the same resulting file size make the SECOND one
silently not take effect — and a mutant that never ran reports SURVIVED. The
mirror carries no `__pycache__` and `PYTHONDONTWRITEBYTECODE=1` is set, so no
`.pyc` is written at all and the window cannot open.
"""
import argparse
import ast
import hashlib
import os
import shutil
import sys
import tempfile
from collections import Counter

# ⭐ REUSED, not restated. The output parsing and the `Run` shape are
# `mutate_schema.py`'s, verified by `DEBUGGING_TIPS` §8a's sweep. Two copies
# would drift and the one that drifts is always the copy.
import mutate_schema
from mutate_schema import MutationError, Run

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "seats.py")
TESTS = os.path.join(HERE, "test_seats.py")
PY = os.environ.get("SEATS_PY") or sys.executable

# (name, old, new) — each one deletes or inverts exactly one guard.
MUTANTS = [
    ("4c-denominator-may-drop-concepts",
     'if "concepts" not in kinds:', 'if False:'),
    ("4c-denominator-accepts-an-unknown-kind",
     'if unknown:\n        raise SeatRefused(f"{unknown} is not a licensed item kind")',
     'if False:\n        raise SeatRefused(f"{unknown} is not a licensed item kind")'),
    ("4c-admits-a-world-item",
     '    world = [it.item for it in items if it.licence == "world"]',
     '    world = []'),
    ("4c-accepts-a-missing-citation",
     'if not allow_missing_citations and not it.cited_text.strip():',
     'if False:'),
    ("4c-accepts-a-rendering-in-the-item-text",
     '        _refuse(it.text, f"{it.item}\'s presentation", _RENDERING_PATTERNS)',
     '        pass'),
    ("4c-accepts-a-behaviour-in-the-cited-text",
     '        _refuse(it.cited_text, f"{it.item}\'s cited clause text",\n'
     '                _UNIVERSAL_PATTERNS)',
     '        pass'),
    ("4c-accepts-an-empty-denominator",
     'if not items:\n        raise SeatRefused("4c with an empty denominator is a vacuous pass")',
     'if False:\n        raise SeatRefused("4c with an empty denominator is a vacuous pass")'),
    ("4b-sees-the-logic",
     '        _refuse(text, where, _MODULE_PATTERNS)\n    if not renderings:\n'
     '        raise SeatRefused("4b with no rendering to judge is a vacuous pass")',
     '    if not renderings:\n'
     '        raise SeatRefused("4b with no rendering to judge is a vacuous pass")'),
    ("module-fence-loses-the-json-pattern",
     "    (re.compile(r'\"(outcome|clause_id|claims|acts|concepts|ontology|asserts|'\n"
     "                r'beats|defines|closure|requires|inputs|forbid_body)\"\\s*:'),\n"
     "     \"the module as JSON\"),",
     ""),
    ("universal-fence-loses-the-behaviour-namespace",
     '    (re.compile(r"(?<![A-Za-z0-9_])(" + "|".join(sorted(schema.BEHAVIOUR_NS))\n'
     '                + r")(?![A-Za-z0-9_])"),\n'
     '     "a name from the BEHAVIOUR namespace"),',
     ""),
    ("universal-fence-loses-the-panel-label",
     '    (re.compile(r"\\bpanel\\b", re.I), "a panel label"),', ""),
    ("universal-fence-loses-the-stage3-verdicts",
     '    (re.compile(r"(?<![A-Za-z0-9_])(" + "|".join(probe.LABELS)\n'
     '                + r")(?![A-Za-z0-9_])"),\n'
     '     "a stage-3 expected verdict"),', ""),
    ("universal-fence-loses-the-behaviour-header",
     '    (re.compile(r"\\bbehaviou?rs?\\b\\s*:", re.I), "a behaviour"),', ""),
    ("4d-accepts-the-claims-as-the-material",
     '    overlap = sorted(set(renderings) & set(claims))', '    overlap = []'),
    ("4d-accepts-zero-renderings",
     '    if not renderings:\n        raise SeatRefused(\n'
     '            "4d with no rendering to read is refused:',
     '    if False:\n        raise SeatRefused(\n'
     '            "4d with no rendering to read is refused:'),
    ("4d-accepts-an-empty-claims-list",
     'if not claims:\n        raise SeatRefused("4d with no claims has no denominator")',
     'if False:\n        raise SeatRefused("4d with no claims has no denominator")'),
    ("4d-does-not-fence-its-renderings",
     '        _refuse(text, where, _MODULE_PATTERNS)\n    for c in claims:',
     '    for c in claims:'),
    ("claim-denominator-double-counts-a-forbid-body-claim",
     '        overlap = set(self.ids) & set(self.excluded_forbid_body)',
     '        overlap = set()'),
    ("4d-denominator-guesses-a-missing-forbid-body-mapping",
     'if mod.forbid_body and not excluded:', 'if False:'),
    ("4d-denominator-accepts-a-name-that-excludes-nothing",
     'if unknown:\n        raise SeatRefused(\n'
     '            f"{unknown} named as forbid_body claim(s)',
     'if False:\n        raise SeatRefused(\n'
     '            f"{unknown} named as forbid_body claim(s)'),
    ("validator-accepts-an-empty-denominator",
     'if not ids:\n        raise NotAdjudicated(', 'if False:\n        raise NotAdjudicated('),
    ("validator-accepts-a-skipped-item",
     '    missing = [i for i in ids if i not in got]', '    missing = []'),
    ("validator-accepts-a-hallucinated-item",
     '    extra = [i for i in got if i not in ids]', '    extra = []'),
    ("validator-accepts-a-duplicate",
     'if len(set(got)) != len(got):', 'if False:'),
    ("validator-accepts-an-open-verdict",
     'if j.verdict not in VERDICTS[seat]:', 'if False:'),
    ("validator-accepts-an-empty-reason",
     'if not str(j.reason or "").strip():\n            raise NotAdjudicated(\n'
     '                f"{seat}: {j.item} carries no reason',
     'if False:\n            raise NotAdjudicated(\n'
     '                f"{seat}: {j.item} carries no reason'),
    ("rb4-never-stamps",
     '    if rb.non_evidential:\n        out.append("non-evidential")',
     '    if False:\n        out.append("non-evidential")'),
    ("rb4-stamps-everything",
     'if seat not in ECHO_STAMPED:', 'if seat not in SEATS:'),
    ("rb4-stamp-drops-the-verdict",
     '        return tuple(judgements)\n    return tuple(dataclasses.replace(j, evidential=False,',
     '        return tuple(judgements)\n    return tuple(dataclasses.replace(j, verdict=UNCLEAR, evidential=False,'),
    ("4c-is-stamped-by-an-echo-it-never-saw",
     'ECHO_STAMPED = ("4b", "4d")', 'ECHO_STAMPED = ("4b", "4c", "4d")'),
    ("cross-check-treats-a-missing-number-as-zero",
     '        n = None if discrimination is None else discrimination.get(j.item)',
     '        n = 0 if discrimination is None else discrimination.get(j.item, 0)'),
    ("cross-check-never-reports-inert",
     '        if n == 0:', '        if False:'),
    ("cross-check-judges-a-not-conveyed-verdict",
     'if j.verdict != "covered":', 'if False:'),
    ("divergence-fires-on-an-abstention",
     '    frozenset({"faithful", "unfaithful"}),',
     '    frozenset({"faithful", "unfaithful"}), frozenset({"faithful", "unclear"}),'),
    ("divergence-rewrites-4as-own-verdict",
     '            if (j.item in diverged and seat != "4a") else j',
     '            if j.item in diverged else j'),
    ("divergence-lets-4a-force-a-verdict",
     '    considered = {s: js for s, js in judgements_by_seat.items() if s != "4a"}',
     '    considered = dict(judgements_by_seat)'),
    ("divergence-does-not-resolve-to-unclear",
     '        diverged.add(item)', '        pass'),
    ("divergence-record-drops-the-brief-shas",
     '            brief_shas={s: brief_shas[s] for s in per_seat\n'
     '                        if s in (brief_shas or {})},',
     '            brief_shas={},'),
    ("promotion-needs-no-triage",
     'if triage is None:\n        raise SeatRefused(', 'if False:\n        raise SeatRefused('),
    ("promotion-accepts-a-non-triage",
     'if not isinstance(triage, Triage):', 'if False:'),
    ("triage-needs-no-grounds",
     'if not str(self.grounds or "").strip():', 'if False:'),
    ("report-drops-the-pass-rate-refusal",
     '        probe.refuse_pass_rate(mapping)', '        pass'),
    ("report-accepts-a-missing-required-key",
     '    missing = [k for k in REQUIRED_REPORT_KEYS if k not in d]',
     '    missing = []'),
    ("report-accepts-an-unclear-rate-with-no-denominator",
     '    for key in ("rate", "denominator"):', '    for key in ():'),
    ("report-accepts-a-rate-with-no-pooled-entry",
     'if not isinstance(rate, dict) or "pooled" not in rate:', 'if False:'),
    ("report-lets-4a-into-the-evidential-seats",
     'if "4a" in d["seats"]:', 'if False:'),
    ("report-line-reads-4a",
     '    for seat in ("4b", "4c", "4d"):',
     '    for seat in ("4b", "4c", "4d"):\n'
     '        if seat == "4b":\n'
     '            bits.append(str(d["advisory"]))'),
    ("report-line-drops-the-unclear-rate",
     '    bits.append(render_unclear_rate(d["unclear_rate"]["pooled"]))', '    pass'),
    ("report-line-drops-the-layer1-fraction",
     '    bits.append(f"layer 1: {d[\'layer1_fraction\']:.2f} of renderings")', '    pass'),
    ("report-line-hides-the-excluded-forbid-body-claims",
     '    if d["forbid_body_claims_excluded"]:', '    if False:'),
    ("layer1-fraction-is-not-computed",
     '    layer1 = ([r.layer for r in rb.renderings] or [])', '    layer1 = []'),
    ("route-does-not-re-translate-on-a-seat-finding",
     '    if driving:', '    if False:'),
    ("route-re-translates-for-ever",
     'if retranslations_used < max_retranslations:', 'if True:'),
    ("route-carries-the-transcript-across-a-re-translation",
     'return probe.Routing("re-translate", (), None)',
     'return probe.Routing("re-translate", tuple(findings), None)'),
    ("route-lets-4a-drive-repair",
     '                               SEAT_ORIGIN["4d"], INERT_ORIGIN)]',
     '                               SEAT_ORIGIN["4d"], INERT_ORIGIN,\n'
     '                               SEAT_ORIGIN["4a"])]'),
    ("route-repairs-on-a-note",
     'if any(f.origin == READBACK_STRUCTURAL and f.severity == "error"',
     'if any(f.origin == READBACK_STRUCTURAL and f.severity != "zzz"'),
    ("transcript-fence-admits-a-seat-finding",
     '    bad = [f for f in findings if f.origin not in DISCLOSABLE_ORIGINS]',
     '    bad = []'),
    ("disclosable-origins-admits-the-seats",
     'DISCLOSABLE_ORIGINS = tuple(translate.DISCLOSABLE_ORIGINS) + (READBACK_STRUCTURAL,)',
     'DISCLOSABLE_ORIGINS = tuple(translate.DISCLOSABLE_ORIGINS) + (\n'
     '    READBACK_STRUCTURAL, "seat-4b", "seat-4c", "seat-4d", INERT_ORIGIN)'),
    ("disclosable-origins-drops-readback-structural",
     'DISCLOSABLE_ORIGINS = tuple(translate.DISCLOSABLE_ORIGINS) + (READBACK_STRUCTURAL,)',
     'DISCLOSABLE_ORIGINS = tuple(translate.DISCLOSABLE_ORIGINS)'),
    ("local-log-hides-the-withheld-hole",
     '        if withheld:', '        if False:'),
    ("seat-runs-without-an-explicit-client-factory",
     'if client_factory is None:\n        raise SeatError(',
     'if False:\n        raise SeatError('),
    ("a-clause-that-renders-nothing-reaches-a-seat",
     '    return rb.outcome == "rendered"', '    return True'),
    ("plan-does-not-gate-on-the-readback",
     'if not proceeds_to_a_seat(rb):', 'if False:'),
    ("estimate-treats-an-unpriced-provider-as-free",
     'if not price_per_mtok:', 'if False:'),
    ("estimate-ignores-the-output-cap",
     '    out_tok = max_tokens * len(plan.prompts)', '    out_tok = 0'),
    ("estimate-ignores-the-brief",
     '    in_chars = sum(len(BRIEFS[s]) + len(p) for s, p in plan.prompts.items())',
     '    in_chars = sum(len(p) for p in plan.prompts.values())'),
    ("brief-sha-is-not-per-seat",
     '    return hashlib.sha256(BRIEFS[seat].encode("utf-8")).hexdigest()',
     '    return hashlib.sha256(b"constant").hexdigest()'),
    ("unclear-rate-loses-its-denominator",
     '    return {"unclear": u, "denominator": n,',
     '    return {"unclear": u, "denominator": 0,'),
    ("unclear-rate-is-not-split-by-length",
     '        lb = _bucket(len(r.text), _LENGTH_BUCKETS, ">320")\n',
     '        lb = None\n'),
    ("seat-finding-accepts-any-seat-name",
     'if seat not in SEATS:\n        raise SeatRefused(f"{seat!r} is not one of {SEATS}")\n'
     '    return checks.Finding(f"readback-{seat}"',
     'if False:\n        raise SeatRefused(f"{seat!r} is not one of {SEATS}")\n'
     '    return checks.Finding(f"readback-{seat}"'),

    ("survey-drops-the-worst-case",
     '"usd_worst_flash": flash["usd"],', '"usd_worst_flash": 0.0,'),
    ("survey-report-drops-the-total",
     'out.append(f"  {\'TOTAL\':<20} {len(rows)}   "\n'
     '               f"({len(planned)} reach a seat)")',
     'pass'),
    ("survey-report-drops-the-assumption-label",
     '        out.append("⚠️ WORST is the number a budget decision uses: every reply "\n'
     '                   "at its 4096-token cap. `likely` assumes 40 output tokens "\n'
     '                   "per judgement and is an ASSUMPTION — nothing has been run, "\n'
     '                   "so no reply length has been measured.")',
     '        pass'),
    ("survey-bills-the-frontier-at-flash-rates",
     '            front = estimate_clause_usd(plan, frontier, chars_per_token,\n'
     '                                        max_tokens)',
     '            front = flash'),
    ("survey-plans-a-clause-that-reaches-no-seat",
     '        if proceeds_to_a_seat(rb):', '        if True:'),
    ("echo-that-never-ran-reads-as-a-pass",
     '    if rb.clause_echo is None:\n        out.append("echo-not-measured")',
     '    if False:\n        out.append("echo-not-measured")'),
    ("a-failed-rb1-rb2-rb3-does-not-stamp",
     '    if not all(rb.checks[k] for k in ("RB1", "RB2", "RB3", "RB5")):',
     '    if False:'),
    ("the-report-hides-why-a-verdict-was-stamped",
     '        "readback_stamps": list(readback_stamps(rb)),',
     '        "readback_stamps": [],'),
    ("report-line-hides-the-readback-stamps",
     '    if d["readback_stamps"]:', '    if False:'),
    ("a-stamped-negative-verdict-is-dropped",
     "            if j.verdict in (\"unfaithful\", \"unlicensed\", \"not-conveyed\",",
     "            if j.evidential and j.verdict in (\"unfaithful\", \"unlicensed\", \"not-conveyed\","),
    ("a-seat-finding-loses-its-stamps",
     '                mark = f" [{\', \'.join(j.stamps)}]" if j.stamps else ""',
     '                mark = ""'),
    ("readback-stamps-is-not-a-required-report-key",
     '                        "readback_stamps")', '                        )'),
    # --- the guards this cycle added, each with its own mutant ------------
    ("report-accepts-a-consensus-field-ONE-LEVEL-DOWN",
     '    bad = sorted({where for where, text in _refused_strings(mapping)\n'
     '                  if _REFUSED_KEY.search(text)})',
     '    bad = sorted(k for k in mapping if _REFUSED_KEY.search(str(k)))'),
    ("refuse-aggregate-does-not-read-values",
     '    elif isinstance(node, str) and scan_values:\n        yield path, node',
     '    elif False:\n        yield path, node'),
    ("refuse-aggregate-exempts-every-value",
     '                scan_values and str(k) not in _VERBATIM_VALUE_KEYS)',
     '                False)'),
    ("pooled-unclear-rate-includes-4a",
     '    pooled = [j for s, js in judgements.items() if s != "4a" for j in js]',
     '    pooled = [j for s, js in judgements.items() for j in js]'),
    ("discrimination-that-joins-nothing-is-accepted",
     '    if ids and len(unmatched) == len(discrimination):',
     '    if False:'),
    ("discrimination-misses-are-not-counted",
     '    unmatched = tuple(sorted(k for k in discrimination if k not in ids))',
     '    unmatched = ()'),
    ("report-line-hides-the-unmatched-discrimination-keys",
     '    elif d.get("stage3_discrimination_keys_unmatched"):',
     '    elif False:'),
    ("the-report-drops-the-unmatched-discrimination-keys",
     '        "stage3_discrimination_keys_unmatched": list(unmatched),',
     '        "stage3_discrimination_keys_unmatched": [],'),
    ("the-frontier-price-is-a-literal-again",
     '    return max(priced, key=lambda nv: (nv[1][1], nv[1][0]))',
     '    return "sol", (5.0, 30.0)'),
    ("an-unpriced-table-is-not-refused",
     '    if not priced:', '    if False:'),
    ("the-survey-does-not-read-the-price-table",
     '        frontier_name, frontier = most_expensive_provider()',
     '        frontier_name, frontier = "sol", (5.0, 30.0)'),
    ("4c-item-text-drops-an-asserts-rule-body",
     '        base = f"clause {clause_id} {item.status}s the act {item.act}"\n'
     '        return base + (f", when {item.body}" if item.body else "")',
     '        return f"clause {clause_id} {item.status}s the act {item.act}"'),
    ("4c-item-text-drops-an-ontology-rule-body",
     '        base = f"{item.atom} — {item.gloss}"\n'
     '        return base + (f", when {item.body}" if item.body else "")',
     '        return f"{item.atom} — {item.gloss}"'),
    ("4c-item-text-drops-a-beats-rule-body",
     '        base = (f"clause {item.sayer} says clause {item.winner} outranks "\n'
     '                f"clause {item.loser}")\n'
     '        return base + (f", when {item.body}" if item.body else "")',
     '        return (f"clause {item.sayer} says clause {item.winner} outranks "\n'
     '                f"clause {item.loser}")'),
    ("licensed-kinds-drops-defines",
     'LICENSED_KINDS = ("concepts", "ontology", "asserts", "beats", "defines")',
     'LICENSED_KINDS = ("concepts", "ontology", "asserts", "beats")'),
    ("source-items-ignores-judgeable-only",
     '    ids = denominator.judgeable if judgeable_only else denominator.ids',
     '    ids = denominator.ids'),
    ("rendering-sha-ignores-the-rendering",
     '    blob = "\\n".join(f"{r.item}\\t{r.layer}\\t{r.text}" for r in rb.renderings)',
     '    blob = ""'),
    ("unclear-split-length-bucket-is-a-constant",
     '        lb = _bucket(len(r.text), _LENGTH_BUCKETS, ">320")',
     '        lb = "<=80"'),
]


# ==========================================================================
#  the engine — shared with `mutate_readback_r3.py`
# ==========================================================================

#: ⛔ pytest's own exit codes. 2 = interrupted (a collection error looks like
#: this), 3 = internal error, 4 = usage error, 5 = NO TESTS COLLECTED. Every
#: one of them is "the suite did not run", and the first version of this file
#: counted all of them as a kill because they are non-zero.
NOT_A_RESULT = (2, 3, 4, 5)


def _mirror(workdir, skip):
    """Populate `workdir` with `phase_1`: directories symlinked, files copied.

    Files are COPIED rather than symlinked so pytest's import machinery never
    has to resolve a symlink to decide a module's identity. Directories are
    symlinked because `runs/` and `probe_runs/` are the bulk of the tree and
    nothing writes to them.
    """
    for name in sorted(os.listdir(HERE)):
        if name == "__pycache__" or name in skip or name.startswith(".mutate."):
            continue
        src, dst = os.path.join(HERE, name), os.path.join(workdir, name)
        if os.path.isdir(src):
            os.symlink(src, dst)
        else:
            shutil.copy2(src, dst)


def _pytest(src, module_path, test_path, workdir):
    """Write `src` as the module under test and run the suite against it."""
    target = os.path.join(workdir, os.path.basename(module_path))
    with open(target, "w", encoding="utf-8") as fh:
        fh.write(src)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    import subprocess
    r = subprocess.run(
        [PY, "-m", "pytest", os.path.join(workdir,
                                          os.path.basename(test_path)),
         "-q", "--tb=no", "-rfE", "--no-header", "-p", "no:cacheprovider"],
        cwd=workdir, capture_output=True, text=True, env=env)
    out = r.stdout + r.stderr
    counts = {kind: int(n) for n, kind in mutate_schema._COUNT.findall(out)}
    if "errors" in counts:
        counts["error"] = counts.pop("errors")
    dead = []
    for line in out.splitlines():
        m = mutate_schema._SUMMARY.match(line.strip())
        if m:
            nodeid = m.group(2).split(" ")[0]
            dead.append(nodeid.split("::", 1)[-1] if "::" in nodeid else nodeid)
    return Run(r.returncode, counts, sorted(set(dead)), out)


class Result:
    def __init__(self, name, status, killed=(), detail=""):
        self.name, self.status = name, status
        self.killed, self.detail = list(killed), detail


def _sha(p):
    with open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def run_all(mutants, module_path=None, test_path=None, only=None):
    """Apply each mutant to a MIRROR of `phase_1` and record which tests die.

    `module_path` is READ ONLY; its digest is asserted before and after.
    """
    module_path = module_path or SRC
    test_path = test_path or TESTS
    with open(module_path, encoding="utf-8") as fh:
        original = fh.read()
    before = _sha(module_path)
    if only:
        mutants = [m for m in mutants if only in m[0] or only in m[1]]
        if not mutants:
            raise MutationError(f"--only {only!r} matched no mutant")

    workdir = tempfile.mkdtemp(prefix=".mutate.", dir=os.path.dirname(HERE))
    try:
        _mirror(workdir, skip={os.path.basename(module_path)})
        # ⚠️ The test file may live OUTSIDE `phase_1` — this harness's own
        # tests drive it with a fake module/test pair in a tmp dir, which is
        # the only way to check that a SURVIVOR is reported as one without
        # waiting on the real suite.
        if not os.path.exists(os.path.join(workdir,
                                           os.path.basename(test_path))):
            shutil.copy2(test_path, workdir)
        # ⛔ THE BASELINE, THROUGH THE SAME ISOLATION PATH. Without it a RED
        # suite makes every mutant look killed — which is exactly what this
        # file shipped, and it reported `0 survivor(s)` while doing it.
        base = _pytest(original, module_path, test_path, workdir)
        if base.returncode != 0 or base.counts.get("passed", 0) == 0:
            raise MutationError(
                f"baseline is NOT GREEN through the isolation path, so every "
                f"mutation result below would be meaningless — a red suite "
                f"kills every mutant and the sweep reports 0 survivors.\n"
                f"rc={base.returncode} counts={base.counts}\n"
                f"{base.output[-2500:]}")
        baseline_n = base.total

        results = []
        for name, old, new in mutants:
            n = original.count(old)
            if n != 1:
                results.append(Result(
                    name, "error", [],
                    f"the anchor matches {n} times, not once — the guard moved "
                    f"or was reworded and the mutation was NOT applied. This "
                    f"run proves nothing about it"))
                continue
            mutated = original.replace(old, new, 1)
            if mutated == original:
                results.append(Result(name, "error", [],
                                      "the mutation changed nothing"))
                continue
            try:
                ast.parse(mutated)
            except SyntaxError as exc:
                results.append(Result(
                    name, "error", [],
                    f"mutated source does not parse ({exc}) — a mutant that "
                    f"cannot be imported tests the importer, not the guard"))
                continue
            run = _pytest(mutated, module_path, test_path, workdir)
            if run.returncode in NOT_A_RESULT or run.total != baseline_n:
                results.append(Result(
                    name, "error", [],
                    f"the suite did not run comparably (rc={run.returncode}, "
                    f"collected {run.total} vs baseline {baseline_n}) — this "
                    f"is NOT evidence the guard is pinned\n"
                    f"{run.output[-1200:]}"))
                continue
            # ⛔ KILLED means a NAMED TEST DIED, not "the process was unhappy".
            results.append(Result(name, "killed" if run.dead else "survivor",
                                  run.dead))
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    if _sha(module_path) != before:
        raise MutationError(
            f"{module_path} was MODIFIED IN PLACE. Every result in this run is "
            f"untrustworthy and the working tree needs restoring")
    return results, baseline_n


def format_report(results, baseline_n, module_path):
    lines, w = [], min(56, max(len(r.name) for r in results))
    lines.append(f"baseline: {baseline_n} tests, all green "
                 f"({os.path.basename(module_path)} unmodified)")
    lines.append("")
    lines.append(f"{'#':>3}  {'mutant':<{w}}  {'result':<9}  tests killed")
    lines.append(f"{'':->3}  {'':-<{w}}  {'':-<9}  {'':-<12}")
    for i, r in enumerate(results, 1):
        if r.status == "killed":
            mark, dead = "killed", ", ".join(r.killed)
            if len(r.killed) > 4:
                dead = f"{len(r.killed)} tests: " + ", ".join(r.killed[:4]) + ", …"
        elif r.status == "survivor":
            mark, dead = "SURVIVOR", "⭐ NOTHING — this guard is pinned by no test"
        else:
            mark, dead = "ERROR", "‼ " + r.detail.splitlines()[0]
        lines.append(f"{i:>3}  {r.name[:w]:<{w}}  {mark:<9}  {dead}")

    survivors = [r for r in results if r.status == "survivor"]
    errors = [r for r in results if r.status == "error"]
    killed = [r for r in results if r.status == "killed"]
    lines += ["", f"{len(killed)} killed · {len(survivors)} SURVIVORS · "
                  f"{len(errors)} errors  (of {len(results)} mutants)"]
    if survivors:
        lines += ["", "⭐ SURVIVORS — guards no test pins. These are the finding:"]
        lines += [f"   • {r.name}" for r in survivors]
    if errors:
        lines += ["", "‼ ERRORS — the mutation did not apply or the run was "
                      "not comparable. NOT evidence of anything:"]
        for r in errors:
            lines.append(f"   • {r.name}")
            lines += [f"     {ln}" for ln in r.detail.splitlines()[:3]]

    broad = [r for r in killed if len(r.killed) >= 5]
    if broad:
        lines += ["", "mutants that kill MANY tests — entangled, or "
                      "load-bearing for the fixtures rather than for one "
                      "assertion:"]
        for r in sorted(broad, key=lambda x: -len(x.killed)):
            lines.append(f"   • {len(r.killed):>2} tests — {r.name}")
    narrow = [r for r in killed if len(r.killed) < 5]
    counts = Counter(t for r in narrow for t in r.killed)
    suspect = [(t, n) for t, n in counts.most_common() if n >= 3]
    lines += ["", f"tests killed by ≥3 different NARROW mutants "
                  f"({len(narrow)} of {len(killed)} counted; the {len(broad)} "
                  f"broad one(s) excluded, being global by construction) — "
                  f"suspect: they may be failing for a reason other than the "
                  f"one they name:"]
    lines += ([f"   • {n:>2} mutants — {t}" for t, n in suspect]
              or ["   (none)"])
    one = [t for t, n in counts.items() if n == 1]
    lines += ["", f"{len(one)} of {len(counts)} tests killed by a narrow "
                  f"mutant are killed by exactly one (a clean 1:1 pin)."]
    return "\n".join(lines)


def main(argv=None, mutants=None, module_path=None, test_path=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--only", default=None,
                    help="substring: run only mutants whose name or anchor "
                         "matches")
    a = ap.parse_args(argv)
    mutants = MUTANTS if mutants is None else mutants
    module_path = module_path or SRC
    print(f"mutating {len(mutants)} guards in "
          f"{os.path.basename(module_path)}", file=sys.stderr)
    try:
        results, baseline_n = run_all(mutants, module_path, test_path, a.only)
    except MutationError as exc:
        print(f"‼ {exc}", file=sys.stderr)
        return 2
    print(format_report(results, baseline_n, module_path))
    bad = sum(r.status in ("survivor", "error") for r in results)
    print(f"\nexit {1 if bad else 0}: "
          + ("a guard nothing pins, or a mutation that did not apply."
             if bad else "every guard is pinned by at least one test."))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
