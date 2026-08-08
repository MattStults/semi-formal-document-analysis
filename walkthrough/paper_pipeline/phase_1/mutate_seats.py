"""Mutation sweep over `seats.py` — break each guard on purpose, confirm a
test dies.

    ../../../semi-formal-experiment/.venv/bin/python mutate_seats.py

⭐ A GUARD NO MUTATION KILLS IS UNPINNED, and this repo treats an unpinned
guard as not shipped (`STEP_stage4.md` §8: *"stage 4 ships with its own
mutation run at 0 survivors or it does not ship"*). The first run of this
sweep found 16 of 71 guards surviving with all 103 tests green; every one of
them now has a named test, and the sweep is at 0.

⛔ IT REWRITES `seats.py` IN PLACE and restores it byte-for-byte in a `finally`
block, asserting the restore. Do not run it concurrently with an edit to that
file.

⚠️ ONE TRAP, found inside this script and worth more than the sweep. Python
invalidates a `.pyc` on (mtime SECONDS, size). Two mutants written inside the
same second with the same resulting file size make the SECOND one silently not
take effect — and a mutant that never ran reports SURVIVED. That is this
repo's own "a pass indistinguishable from did-not-run" shape, occurring inside
the tool built to detect it, and it initially hid one real kill. `__pycache__`
is now cleared and byte-code writing disabled before every run.
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "seats.py")
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
    ("report-accepts-a-consensus-field",
     '    bad = sorted(k for k in mapping if _REFUSED_KEY.search(str(k)))',
     '    bad = []'),
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
]



def main():
    original = open(SRC, encoding="utf-8").read()
    backup = tempfile.mktemp(suffix=".seats.py")
    shutil.copy2(SRC, backup)
    survivors, unapplied = [], []
    try:
        for name, old, new in MUTANTS:
            if original.count(old) != 1:
                unapplied.append((name, original.count(old)))
                continue
            open(SRC, "w", encoding="utf-8").write(original.replace(old, new, 1))
            # ⛔ pyc invalidation is (mtime SECONDS, size). Two mutants written
            # inside one second with the same file size make the second one
            # silently not take effect — and a mutant that never ran reports
            # SURVIVED, which is this repo's own "pass indistinguishable from
            # did-not-run" shape, inside the tool built to detect it.
            shutil.rmtree(os.path.join(HERE, "__pycache__"), ignore_errors=True)
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
            r = subprocess.run(
                [PY, "-m", "pytest", "test_seats.py", "-x", "-q",
                 "--no-header", "-p", "no:cacheprovider"],
                cwd=HERE, capture_output=True, text=True, env=env)
            killed = r.returncode != 0
            print(f"{'KILLED ' if killed else 'SURVIVED'}  {name}")
            if not killed:
                survivors.append(name)
    finally:
        shutil.copy2(backup, SRC)
        assert open(SRC, encoding="utf-8").read() == original, "RESTORE FAILED"
    print(f"\n{len(MUTANTS) - len(unapplied)} mutants applied, "
          f"{len(survivors)} survivor(s)")
    for s in survivors:
        print("  SURVIVOR:", s)
    for n, c in unapplied:
        print(f"  NOT APPLIED ({c} matches):", n)
    return 1 if survivors or unapplied else 0


if __name__ == "__main__":
    sys.exit(main())
