"""Mutation sweep over `readback_r3.py` — break each guard, confirm a test dies.

    ../../../semi-formal-experiment/.venv/bin/python mutate_readback_r3.py

⛔ WHY THIS FILE EXISTS. `21813f2` claimed *"mutation sweep 21/21 killed, 0
survivors"* for R3 and **committed no harness**, so the number was reproducible
by nobody but its author and re-runnable by nobody at all. `STEP_stage4.md` §8's
bar — *"stage 4 ships with its own mutation run at 0 survivors or it does not
ship"* — was met for the seats and unmet for R3. A mutation number that cannot
be re-run is a claim, not a measurement.

⭐ IT IS THE SAME ENGINE `mutate_seats.py` RUNS, imported rather than copied:
green baseline through the same isolation path, return-code triage, a
collected-count comparison, and a third `error` status that is never folded
into "no tests died". See that file's docstring for what each guard is for and
which review found it missing. Only the mutant table below is R3's own.

⚠️ R3 SHELLS OUT TO xclingo, so this sweep is slower than the seats one and it
is worth knowing why a mutant might die for the wrong reason: an R3 mutation
that makes the program unparseable takes the whole tree down, and every test
over live derivations dies with it. Those show up in the ENTANGLEMENT table at
the bottom, not as clean 1:1 pins.
"""
import os
import sys

# ⭐ The engine, imported rather than copied. `mutate_seats.HERE` anchors the
# mirror on `phase_1/` and is the same directory this file lives in.
import mutate_seats

SRC = os.path.join(mutate_seats.HERE, "readback_r3.py")
TESTS = os.path.join(mutate_seats.HERE, "test_readback_r3.py")

# (name, old, new) — each one deletes or inverts exactly one guard.
MUTANTS = [
    # --- the trace-safe literal, and the three escapes it has had ---------
    ("trace-safe-neutralises-nothing",
     'TRACE_SAFE = {\'"\': "”", "\\\\": "/", "{": "(", "}": ")",\n'
     '              "\\n": " ", "\\r": " ", "%": "％"}',
     'TRACE_SAFE = {}'),
    ("trace-safe-misses-the-PERCENT",
     '              "\\n": " ", "\\r": " ", "%": "％"}',
     '              "\\n": " ", "\\r": " "}'),
    ("a-rewritten-sentence-is-not-recorded",
     '    safe, bad = trace_safe(sentence)\n    if bad:',
     '    safe, bad = trace_safe(sentence)\n    if False:'),

    # --- the annotation. An unannotated rule is INVISIBLE to xclingo ------
    ("module-program-stops-annotating-ontology",
     '            item = f"ontology[{i}]"\n'
     '            out.append(_annotation(sentence[item], notes, item))',
     '            item = f"ontology[{i}]"'),
    ("module-program-stops-annotating-defines",
     '        item = f"defines[{i}]"\n'
     '        out.append(_annotation(sentence[item], notes, item))',
     '        item = f"defines[{i}]"'),
    ("module-program-stops-annotating-asserts",
     '        item = f"asserts[{i}]"\n'
     '        out.append(_annotation(sentence[item], notes, item))',
     '        item = f"asserts[{i}]"'),
    ("module-program-uses-the-AUTHORED-read-back",
     '    sentence = {r.item: r.text for r in renderings}',
     '    sentence = {f"asserts[{i}]": a.read_back\n'
     '                for i, a in enumerate(mod.asserts)}'),

    # --- the anonymous-variable refusal (`_` kills the WHOLE link set) ----
    ("anonymous-variable-scan-reads-comments",
     '        scrubbed = _COMMENT.sub("", _STRINGS.sub(\'""\', line))',
     '        scrubbed = _STRINGS.sub(\'""\', line)'),
    ("anonymous-variable-scan-reads-string-constants",
     '        scrubbed = _COMMENT.sub("", _STRINGS.sub(\'""\', line))',
     '        scrubbed = _COMMENT.sub("", line)'),
    ("the-link-scope-is-not-scanned-at-all",
     '    _refuse_anonymous(sources)', '    sources = sources'),
    ("an-anonymous-variable-is-not-refused",
     '        hits = anonymous_variables(text)\n        if hits:',
     '        hits = anonymous_variables(text)\n        if False:'),

    # --- xclingo's THREE deliberately redundant detectors -----------------
    ("a-NONZERO-EXIT-is-ignored",
     '    if proc.returncode != 0:', '    if False:'),
    ("an-ERROR-on-stderr-that-EXITED-ZERO-is-ignored",
     '    if _ERROR_LINE.search(proc.stderr or ""):', '    if False:'),
    ("a-MISSING-COMPLETION-MARKER-is-ignored",
     '    if DONE_MARK not in proc.stdout:', '    if False:'),
    ("TWO-ANSWER-SETS-are-accepted",
     '    if answers > 1:', '    if False:'),

    # --- the parser. A dropped line is a simpler-looking explanation ------
    ("a-tree-line-that-cannot-be-placed-is-skipped",
     '            raise R3Error(\n'
     '                f"tree line {line!r} is not an xclingo ascii-tree line',
     '            continue\n'
     '            raise R3Error(\n'
     '                f"tree line {line!r} is not an xclingo ascii-tree line'),
    ("an-IMPOSSIBLE-DEPTH-invents-a-parent",
     '        if depth > len(stack) + 1:', '        if False:'),
    ("a-node-payload-is-read-as-ONE-quoted-sentence",
     '        elif ch == ";" and not in_str:', '        elif ch == ";":'),
    ("a-node-is-classified-by-how-its-payload-STARTS",
     '    kind = "rule" if said else "fact"',
     '    kind = "rule" if raw.startswith(\'"\') else "fact"'),

    # --- §2.1's substance: every leaf replaced by its R1 rendering --------
    ("a-leaf-with-NO-GLOSS-is-passed-through-as-its-predicate-name",
     '    if not written:\n'
     '        return f"{readback.UNGLOSS_MARK}{name}{readback.UNGLOSS_CLOSE}", False',
     '    if not written:\n        return name, True'),
    ("a-leafs-CONSTANT-is-dropped-from-its-rendering",
     '    shown = [a for a in _split_args(atom)\n'
     '             if _CONST.match(a) and a != placeholder]',
     '    shown = []'),
    ("the-PLACEHOLDER-is-shown-as-though-it-were-a-constant",
     '             if _CONST.match(a) and a != placeholder]',
     '             if _CONST.match(a)]'),
    ("every-node-is-stamped-LAYER-2",
     '    text, layer = node.text, layers.get(node.text, 1)',
     '    text, layer = node.text, 2'),
    ("a-MISSING-GLOSS-is-demoted-to-a-missing-TEMPLATE",
     '        layer = 2\n        if not ok:', '        layer = 1\n        if not ok:'),

    # --- ⛔ EVERY EMPTY RESULT BLOCKS -------------------------------------
    ("an-EMPTY-SITUATION-LIST-is-accepted",
     '    if not situations:', '    if False:'),
    ("a-VERDICT-WITH-NO-TREE-is-accepted",
     '            if not rooted:', '            if False:'),
    ("a-NO-DERIVATION-situation-is-DROPPED-rather-than-counted",
     '            out_situations.append(SituationR3(\n'
     '                s.id, tuple(sorted(s.true_atoms)), (), (), (), '
     '"no-derivation"))\n            continue',
     '            continue'),
    ("verdict-atoms-accepts-ANY-derived-atom",
     '                        if _VERDICT.match(a.replace(" ", ""))))',
     '                        if a))'),
    ("the-ungloss-finding-is-only-a-NOTE",
     '                "readback-ungloss", "error", s.id,',
     '                "readback-ungloss", "note", s.id,'),
    ("an-UNGLOSSED-run-still-proceeds-to-a-seat",
     '    return out.outcome == "rendered"', '    return True'),
    ("the-outcome-ignores-a-run-that-derived-nothing",
     '    elif with_derivation == 0:', '    elif False:'),

    # --- §2.3's reported numbers -----------------------------------------
    ("layer1-fraction-reads-0.0-when-it-measured-NOTHING",
     '        if not nodes:\n            return None',
     '        if not nodes:\n            return 0.0'),
    ("the-report-hides-how-many-situations-derived-nothing",
     '                f"  derivations: {self.with_derivation} of {self.covering} "',
     '                f"  derivations: {self.with_derivation} of {0} "'),
]


def main(argv=None):
    return mutate_seats.main(argv, mutants=MUTANTS, module_path=SRC,
                             test_path=TESTS)


if __name__ == "__main__":
    sys.exit(main())
