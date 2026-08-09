"""Stage 3 — build test cases for a translated clause, and run them.

    import probe
    rep = probe.probe_clause("m0217.lp", link_paths, concepts)   # [D], free
    labels = probe.label_situations(rep, clause_text, xrefs, act,
                                    concepts, client_factory=...)  # [L], paid

Specification: `STEP_stage3.md` revision 3. Build rulings on the six things it
left open: `DECISION_stage3_build.md`. Read that file before changing this one —
four of its eight rulings exist because the obvious alternative was tried, and two (R7,
R8) correct the plan.

⭐ TWO HALVES, AND EACH HAS ITS OWN VACUOUS-PASS HOLE. Neither patches the
other's.

  [D] enumerate · mutate · report.   No model call, no label anywhere near it.
      Its hole: a module with NO RULES scores `0 uncovered of 0` and passes.
      That is 1 of the 4 clauses in the only run we have. Refused as
      `no-testable-content`, keyed on `|R| = 0`.
  [L] a seat labels the covering set; one batched call per clause.
      Its hole: comparing against the CLOSURE-RESOLVED verdict scores an
      EMPTIED `m0217` at 8 of 8 — `produce = cepa`, silence permits, every
      situation still resolves to `permit`. So the comparison is on the DERIVED
      ATOM and the labels are THREE-VALUED. `compare()` refuses any other
      projection at construction.

⛔ THE LEAK PERIMETER. Stage 1 is denied the expected verdicts, and stage 3's
labels ARE expected verdicts. Two origins, and the difference is not cosmetic:

  probe-structural   derived from the module and the solver alone. No label is
                     reachable from one. Disclosable — registered in
                     `translate.DISCLOSABLE_ORIGINS`.
  probe-verdict      a situation whose derived status disagrees with its label.
                     NEVER disclosed, NEVER appended to the transcript. A
                     `probe-verdict` mismatch DISCARDS the transcript and
                     re-runs stage 1 from a clean prompt.
                     `append_findings_to_transcript` raises on one.

⚠️ A FINDING ABOUT THE SIGNATURE RULE, produced by running it.
`STEP_stage3.md` §2 derives the signature rule — `inputs ∪ head-less predicates
declared in the concept table` — from `m0217` as the committed run emitted it:
`inputs: []`, the three body predicates declared only as concepts. **Today's
schema REFUSES that module.**

    >>> schema.validate(political_module(inputs=[], requires=[]))
    <root>: body references `political_content` but nothing declares it

So the concept-table branch is reachable only for the already-committed run
outputs, and every module translated from now on is m0255-shaped (signature ==
inputs). Both branches are implemented, because the committed run is the only
corpus that exists — but the branch §2 calls "a scope row that changed because
it was run" is, as of the current schema, a legacy branch. Recorded rather than
quietly dropped.
"""

import dataclasses
import itertools
import json
import os
import re
import sys

import clingo   # the venv has it; an ImportError here must BLOCK, never skip

HERE = os.path.dirname(os.path.abspath(__file__))
WALKTHROUGH = os.path.dirname(os.path.dirname(HERE))
for _p in (HERE, WALKTHROUGH):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import checks                                                  # noqa: E402
import link                                                    # noqa: E402


class ProbeError(RuntimeError):
    """Stage 3 refused to answer. Never a verdict."""


class NotAdjudicated(ProbeError):
    """A labelling that cannot be adjudicated. Not a mismatch — a refusal."""


class DisclosureRefused(ProbeError):
    """Something carrying an expected answer tried to reach a prompt."""


# ==========================================================================
#  Constants — printed, never implicit
# ==========================================================================

#: ⚠️ NOT added to `config.json`. That file has arm variants used by an eval
#: harness, and a key added to one side of an arm pair is a diff nobody asked
#: for. `cfg["probe"]` overrides any of these when a caller supplies one.
#: `max_signature` bounds the GROUND ATOM count, not the predicate count — see
#: `DECISION_stage3_build.md` R1; on `m0217` they coincide and the conflation
#: is invisible.
PROBE_DEFAULTS = {
    "max_signature": 10,          # 2^10 = 1,024 candidates ≈ 0.8 s per pass
    "max_suppression_rate": 0.75,
    "placeholder": "x",
}

#: ⛔ FOUR VALUES, THREE OF WHICH ARE NOT VERDICTS. Only the first two may enter
#: any aggregate: a pipeline reporting "3 of 4 clauses passed stage 3" over the
#: cited run is reporting that three clauses had nothing to test.
OUTCOMES = ("passed", "failed", "no-testable-content", "signature-too-large")
AGGREGATING_OUTCOMES = ("passed", "failed")

LABELS = ("must-forbid", "must-permit", "must-be-silent", "impossible")
#: `impossible` is the one label that is NOT a verdict, which is exactly why it
#: is the one that may be disclosed.
VERDICT_LABELS = ("must-forbid", "must-permit", "must-be-silent")

#: The only projection stage 3 compares on. See `compare`.
PROJECTIONS = ("derived-atom",)

STRUCTURAL_ORIGIN = "probe-structural"
VERDICT_ORIGIN = "probe-verdict"

_STATUS_FOR_LABEL = {"must-forbid": "forbid", "must-permit": "permit"}


def probe_config(cfg=None):
    out = dict(PROBE_DEFAULTS)
    out.update((cfg or {}).get("probe", {}))
    return out


# ==========================================================================
#  Reading a module — on link.py's own regexes, never a second copy of them
# ==========================================================================
#
# `link.header` takes a PATH and stage 3 works in text (a mutant has no file).
# This reads the same compiled patterns rather than restating the parsing, so
# an edit to `HDR` / `CLOSURE_HDR` / `SIG` reaches both.

def header_of(text):
    out = {"inputs": set(), "requires": set(), "acts": set(),
           "concepts": set(), "closure": {}, "forbid_body": [], "clause": None}
    m = link.CLAUSE_HDR.search(text)
    if m:
        out["clause"] = m.group(1)
    for key, val in link.HDR.findall(text):
        if key in ("inputs", "requires"):
            out[key] = {t.strip() for t in val.split(",") if t.strip()}
        elif key == "concepts":
            out["concepts"] = set(link.SIG.findall(val))
        elif key == "acts":
            out["acts"] = set(link._split_top_level(val))
    for act_class, closure in link.CLOSURE_HDR.findall(text):
        out["closure"][act_class] = closure
    out["forbid_body"] = link.FORBID.findall(text)
    return out


def body_atoms(body):
    """(name, args) for every atom a rule body depends on, `not` stripped."""
    out = []
    for conj in link._split_top(body, ","):
        c = conj.strip()
        while c.startswith("not "):
            c = c[4:].strip()
        name, args = link._parse_atom(c)
        if name:
            out.append((name, args))
    return out


def module_rules(text):
    """`(statement_index, statement)` for every rule with a HEAD and a BODY.

    ⭐ THE DENOMINATOR OF DISCRIMINATION COVERAGE. Integrity constraints
    (`:- body.`) and unconditional facts are counted separately and are NOT
    mutated: deleting a fact is a situation change, and deleting a constraint
    changes the coherent set rather than a derived status. Neither is what this
    criterion measures, and folding them in would let `|R| = 0` hide.
    """
    out = []
    for i, st in enumerate(link.statements(text)):
        if st.startswith("#"):
            continue
        parts = link._split_top(st, ":-")
        if len(parts) < 2 or not parts[0].strip():
            continue
        name, _args = link._parse_atom(parts[0])
        if name:
            out.append((i, st))
    return tuple(out)


def module_facts(text):
    return tuple(link.facts(text))


def module_constraints(text):
    out = []
    for i, st in enumerate(link.statements(text)):
        parts = link._split_top(st, ":-")
        if len(parts) > 1 and not parts[0].strip():
            out.append((i, st))
    return tuple(out)


_VAR = re.compile(r"^[A-Z][A-Za-z0-9_]*$")
_CONST = re.compile(r"^([a-z_][A-Za-z0-9_]*|\d+|\"[^\"]*\")$")


def _is_var(t):
    return bool(_VAR.match(t.strip()))


def _is_const(t):
    return bool(_CONST.match(t.strip()))


# ==========================================================================
#  3a — the situation signature, and its ground atoms
# ==========================================================================

def situation_signature(target_text, link_texts, concepts):
    """Every predicate a situation must be free to set, from four sources.

    `inputs` ∪ (head-less ∧ declared-in-concepts) ∪ UNSATISFIED `requires`
    ∪ the LINKED modules' own `inputs`.

    ⛔ NOT `inputs` alone. On the committed `m0217` that gives the EMPTY SET,
    stage 3 enumerates ONE situation, finds nothing, and reports green — and
    the guard revision 2 wrote for this (`|enumeration| == 0`) never fires,
    because 2^0 is one, not zero. `signature_findings` fires on the empty
    SIGNATURE instead.

    ⛔ AND NOT THAT EITHER — Q-22, found 2026-08-09. The first two terms miss
    `requires` completely, because a borrowed predicate is head-less and the
    concept table covers only names a clause INTRODUCES. `[RAN]` 6 of 19
    stored modules carried one. On `m0079` the dropped predicate sat under a
    negation, so `not higher_authority_conflict(I)` was permanently true and
    the module collapsed to "every instruction is applicable" — the clause's
    entire content inert, and the probe GREEN because no enumerated situation
    could reach the dead branch.

    ⭐ WHY THE FIX IS NOT "ADD `requires`", and this is the whole subtlety.
    `requires` means *another clause defines it*. When a linked module DOES
    define it, the predicate is DERIVED, and putting a derived predicate in
    the signature lets a situation assert it independently of the rule that
    produces it — asserting a conclusion its own premises deny. That is a
    worse bug than the one being fixed. So an unsatisfied `requires` joins the
    signature and a satisfied one does not, which is what
    `test_q22_control_a_requires_THE_LINK_DEFINES_stays_out` pins.

    ⚠️ THE FOURTH TERM IS THE SAME DEFECT ONE LEVEL DOWN. `[RAN]` linking a
    provider in moved the required predicate out of the signature (correctly)
    while the provider's OWN `inputs` never entered it — so the defining rule
    could not fire either, and linking made the module MORE inert, not less.
    A linked module's inputs are facts about the same case and belong here.

    ⚠️ This grows signatures, and `max_signature` bounds ground atoms at 10.
    That is intended: the cap already refuses loudly with `signature-too-large`
    rather than sampling, so growth surfaces as a refusal to measure and never
    as a quiet partial enumeration.
    """
    texts = [target_text] + list(link_texts)
    declared = {str(r.get("concept") or "").strip() for r in (concepts or [])}
    defined = set()
    for t in texts:
        defined |= link.defined_predicates(t)
    sig = set(header_of(target_text)["inputs"])
    for t in link_texts:
        sig |= header_of(t)["inputs"]
    sig |= unsatisfied_requires(target_text, link_texts)
    for name, args in _referenced(texts):
        s = f"{name}/{len(args)}"
        if s not in defined and s in declared:
            sig.add(s)
    return tuple(sorted(sig))


def unsatisfied_requires(target_text, link_texts):
    """`requires` entries that NOTHING in scope defines — the unkept promises.

    ⭐ Reported as well as enumerated. Widening the signature makes the module
    testable, which is necessary and not sufficient: `requires` asserts that
    another clause defines the predicate, and at `[RAN]` 13 of 593 clauses
    translated that assertion is usually false. Repairing it silently would
    leave "nothing in the corpus defines this" indistinguishable from "linked
    fine", which is the class of failure this repo exists to make impossible.
    """
    defined = set()
    for t in [target_text] + list(link_texts):
        defined |= link.defined_predicates(t)
    return {s for s in header_of(target_text)["requires"] if s not in defined}


def _referenced(texts):
    out = []
    for t in texts:
        for _h, _a, body in link.rules(t):
            out.extend(body_atoms(body))
    return out


def ground_atoms(signature, texts, placeholder=None):
    """Ground the free predicates over the domains the program itself supplies.

    Per argument position: the constants observed there, plus the constants of
    any variable that position is bound to by a predicate with ground facts at
    link scope (`forbids(P,M)` with `policy_class(P,K)` in the same body ⇒
    `P ∈ {restricted_content, sensitive_content, prohibited_content}`). A
    variable with no such binding takes ONE placeholder constant.

    ⚠️ THE LIMIT, STATED HERE RATHER THAN DISCOVERED LATER: one placeholder
    individual per unbound position, so the enumeration cannot see a situation
    that needs TWO distinct materials. Every clause in the run we have governs
    one. A clause that needs two is an under-reach of the SIGNATURE, not a
    mismatch, and `DECISION_stage3_build.md` R2 records it.

    ⚠️ A declared predicate that occurs in NO rule body yields NO atoms. It
    cannot change any derived status, and giving it one would double the
    candidate count for nothing and then report it as an undiscriminated input.
    """
    placeholder = placeholder or PROBE_DEFAULTS["placeholder"]
    if not signature:
        return ()
    facts_by_sig = {}
    for t in texts:
        for name, args in link.facts(t):
            if all(_is_const(a) for a in args):
                facts_by_sig.setdefault(f"{name}/{len(args)}", []) \
                    .append(tuple(a.strip() for a in args))

    arity = {s: int(s.rsplit("/", 1)[1]) for s in signature}
    dom = {s: [set() for _ in range(arity[s])] for s in signature}
    seen = set()
    for t in texts:
        for _h, _a, body in link.rules(t):
            atoms = body_atoms(body)
            var_dom = {}
            for name, args in atoms:
                rows = facts_by_sig.get(f"{name}/{len(args)}")
                if not rows:
                    continue
                for i, a in enumerate(args):
                    if _is_var(a):
                        var_dom.setdefault(a.strip(), set()).update(
                            r[i] for r in rows)
            for name, args in atoms:
                s = f"{name}/{len(args)}"
                if s not in dom:
                    continue
                seen.add(s)
                for i, a in enumerate(args):
                    a = a.strip()
                    if _is_const(a):
                        dom[s][i].add(a)
                    elif a in var_dom:
                        dom[s][i] |= var_dom[a]

    out = []
    for s in signature:
        if s not in seen:
            continue                      # declared, never referenced
        name = s.rsplit("/", 1)[0]
        if arity[s] == 0:
            out.append(name)
            continue
        positions = [sorted(dom[s][i]) or [placeholder] for i in range(arity[s])]
        for combo in itertools.product(*positions):
            out.append(f"{name}({','.join(combo)})")
    return tuple(sorted(set(out)))


# ==========================================================================
#  3a — enumeration. CHOICE RULES, one solve. Not a ground-and-solve loop.
# ==========================================================================

@dataclasses.dataclass(frozen=True)
class Situation:
    id: str
    index: int
    true_atoms: frozenset
    derived: frozenset

    def asserts_of(self, clause_id):
        return derived_status(self, clause_id)


@dataclasses.dataclass(frozen=True)
class Enumeration:
    atoms: tuple
    candidates: int
    situations: tuple
    suppressed: int

    def by_id(self):
        return {s.id: s for s in self.situations}


def _program(text, link_texts, drop=()):
    """Comment-free, statement-per-line. Mutants drop by statement index."""
    parts = []
    kept = [st for i, st in enumerate(link.statements(text)) if i not in drop]
    for group in [kept] + [link.statements(t) for t in link_texts]:
        if group:
            parts.append(".\n".join(group) + ".\n")
    return "".join(parts)


def _solve(program):
    models = []
    ctl = clingo.Control(["0"], logger=lambda code, msg: None,
                         message_limit=0)
    ctl.add("base", [], program)
    ctl.ground([("base", [])])
    ctl.solve(on_model=lambda m: models.append(
        frozenset(str(s) for s in m.symbols(atoms=True))))
    return models


def _sid(true_atoms, atoms):
    idx = sum(1 << i for i, a in enumerate(atoms) if a in true_atoms)
    return f"S{idx}", idx


def enumerate_situations(target_text, link_texts, atoms, drop=()):
    """Every situation the module's own program admits, in ONE solve.

    ⭐ SITUATIONS ARE ANSWER SETS OF THE MODULE, never hand-written. A
    candidate the module's integrity constraints reject produces no answer set
    and never becomes a test case, so there is no second well-formedness
    language to keep in sync with the logic — which is where failure mode #11
    came from (`m0255_case_d` asserted material was both brand new AND a
    transformation of user content, and the program answered confidently).

    ⛔ `suppressed` is a FIRST-CLASS OUTPUT. A situation dropped for UNSAT is
    byte-identical in the output to one the enumerator never proposed.
    """
    atoms = tuple(atoms)
    prog = _program(target_text, link_texts, drop)
    choices = "\n".join("{ %s }." % a for a in atoms)
    universe = set(atoms)
    situations = {}
    for m in _solve(prog + "\n" + choices + "\n"):
        true = frozenset(m & universe)
        # ⚠️ NOT `m - universe - base_facts`. A rule whose only effect is on a
        # fact derivable with every input false would be invisible under a base
        # subtraction, so nothing is subtracted but the situation itself. The
        # linked clauses' facts are constant across every situation and so
        # cancel in every comparison.
        derived = frozenset(m - universe)
        sid, idx = _sid(true, atoms)
        prev = situations.get(sid)
        if prev is not None and prev.derived != derived:
            raise ProbeError(
                f"situation {sid} has two answer sets with different derived "
                f"atoms: the module is non-deterministic and stage 3 cannot "
                f"project it to a single derived status")
        situations[sid] = Situation(sid, idx, true, derived)
    ordered = tuple(sorted(situations.values(), key=lambda s: s.index))
    candidates = 1 << len(atoms)
    return Enumeration(atoms, candidates, ordered, candidates - len(ordered))


# ==========================================================================
#  3b — discrimination coverage, the covering set, and the criterion that
#       does NOT work
# ==========================================================================

_INCOHERENT = object()


@dataclasses.dataclass(frozen=True)
class ClaimCoverage:
    covered: tuple
    uncovered: tuple
    #: ⛔ #14: claims no test case can demonstrate. `forbid_body` claims are
    #: checked by `link.py` at stage 2 by inspecting the PROGRAM. Counted here,
    #: and excluded from the denominator — a clause whose only unenforced claim
    #: is a `forbid_body` claim must not report full coverage.
    forbid_body_claims: tuple = ()

    def __post_init__(self):
        overlap = set(self.forbid_body_claims) & (set(self.covered)
                                                  | set(self.uncovered))
        if overlap:
            raise ValueError(
                f"{sorted(overlap)} counted BOTH as forbid_body claims and in "
                f"the coverage denominator; a forbid_body claim is not "
                f"demonstrable by any test case and must be excluded from it")

    @property
    def denominator(self):
        return len(self.covered) + len(self.uncovered)


@dataclasses.dataclass(frozen=True)
class CoverageReport:
    criterion: str
    rules_mutated: object            # ⭐ |R|. None is REFUSED, not defaulted.
    per_rule: dict                   # rule index -> discriminating situations
    uncovered_rules: tuple
    claim_coverage: object = None

    def __post_init__(self):
        if self.rules_mutated is None:
            raise ValueError(
                "a coverage report rendered without |R| is refused: "
                "`0/0 covered` and `11/11 covered` must never render the same "
                "way, and only |R| separates them")

    def render(self):
        n = self.rules_mutated
        cov = n - len(self.uncovered_rules)
        out = [f"|R| = {n} rule(s) mutated · coverage: {self.criterion} = "
               f"{cov}/{n} covered"]
        for i in sorted(self.per_rule):
            mark = "uncovered" if i in self.uncovered_rules else "covered"
            out.append(f"  rule {i}: {mark} — {self.per_rule[i]} "
                       f"discriminating situation(s)")
        cc = self.claim_coverage
        if cc is not None:
            for c in cc.uncovered:
                out.append(f"  {c}: uncovered — 0 discriminating situation(s)")
            for c in cc.covered:
                out.append(f"  {c}: covered")
            if cc.forbid_body_claims:
                out.append(f"  forbid_body claims (NOT TESTABLE HERE, excluded "
                           f"from the denominator): "
                           f"{', '.join(cc.forbid_body_claims)}")
        return "\n".join(out)


def _projection(enum):
    return {s.id: s.derived for s in enum.situations}


def discrimination_coverage(target_text, link_texts, atoms, base_enum,
                            claims_map=None):
    """⭐ A rule is covered iff SOME situation's derived status CHANGES when it
    is removed.

    ⛔ Rule coverage — "the rule fires somewhere" — is INSUFFICIENT, and this
    was measured, not argued. `m0255`'s two C3 rules fire; deleting them
    changes 0 of its situations and leaves all five hand-written probe cases
    bit-identical. Rule coverage passes them. This criterion names C3.

    ⛔ And it CANNOT see a rule that is live and WRONG: on `m0217`, deleting
    the rule and INVERTING it (`permit` → `forbid`) each change one situation,
    and this report renders byte-identically for both. That is the reason the
    labelled half exists.
    """
    orig = _projection(base_enum)
    per_rule, changed_union = {}, set()
    for i, _st in module_rules(target_text):
        mut = _projection(enumerate_situations(target_text, link_texts, atoms,
                                               drop={i}))
        changed = {sid for sid in set(orig) | set(mut)
                   if orig.get(sid, _INCOHERENT) != mut.get(sid, _INCOHERENT)}
        per_rule[i] = len(changed)
        changed_union |= changed
    uncovered = tuple(sorted(i for i, n in per_rule.items() if n == 0))

    claim_cov = None
    if claims_map:
        by_claim = {}
        for i, c in claims_map.items():
            by_claim.setdefault(c, []).append(i)
        cov = tuple(sorted(c for c, idx in by_claim.items()
                           if any(per_rule.get(i, 0) > 0 for i in idx)))
        unc = tuple(sorted(c for c in by_claim if c not in cov))
        claim_cov = ClaimCoverage(cov, unc)
    return CoverageReport("discrimination", len(per_rule), per_rule, uncovered,
                          claim_cov), changed_union


def rule_coverage(target_text, link_texts, atoms):
    """The criterion that does NOT work, kept executable as the control.

    A check that fires on everything is pinned by nothing: this is what makes
    `test_6` mean something. It returns `{rule index: fired anywhere}`.
    """
    rules = module_rules(target_text)
    markers = []
    for i, st in rules:
        body = ":-".join(link._split_top(st, ":-")[1:]).strip()
        markers.append(f"probe_fired_{i} :- {body}.")
    prog = (_program(target_text, link_texts) + "\n" + "\n".join(markers)
            + "\n" + "\n".join("{ %s }." % a for a in atoms) + "\n")
    models = _solve(prog)
    return {i: any(f"probe_fired_{i}" in m for m in models) for i, _ in rules}


def discriminating_pairs(enum):
    """(a, b, atom) for every pair differing in ONE atom with different status."""
    by_atoms = {s.true_atoms: s for s in enum.situations}
    out = []
    for s in enum.situations:
        for a in enum.atoms:
            other = frozenset(s.true_atoms ^ {a})
            o = by_atoms.get(other)
            if o is None or o.index <= s.index:
                continue
            if o.derived != s.derived:
                out.append((s, o, a))
    return tuple(out)


def covering_set(enum):
    """MC/DC-style: ONE discriminating pair per input, not every pair.

    On `m0217` that is the one firing situation and its three single-flip
    neighbours — 4 of 8, exactly as `STEP_stage3.md` §2 reports.

    ⚠️ "Every situation taking part in some discriminating pair" is NOT a
    reduction and was the first thing built here. On `m0255` it returned 180 of
    180 coherent situations — the whole enumeration, renamed. The covering set
    is what the LABELLING SEAT is shown and what the [L] half is priced on, so a
    reduction that reduces nothing turns one cheap call into a 180-situation
    table and reports it as a covering set. Bounded by 2k, k = |atoms|.
    """
    seen, taken = {}, set()
    for a, b, atom in discriminating_pairs(enum):
        if atom in taken:
            continue
        taken.add(atom)
        seen[a.index], seen[b.index] = a, b
    return tuple(v for _k, v in sorted(seen.items()))


def input_discrimination(enum):
    counts = {a: 0 for a in enum.atoms}
    for _a, _b, atom in discriminating_pairs(enum):
        counts[atom] += 1
    return counts


# ==========================================================================
#  3c / 3d — labels, and the comparison the whole document is about
# ==========================================================================

_ASSERTS = re.compile(r"^asserts\(([^,]+),([^,]+),")


def derived_status(situation, clause_id):
    """The statuses THIS clause derives in this situation. Empty means silent.

    ⛔ Read off the DERIVED ATOM, never off a closure-resolved verdict.
    """
    out = set()
    for atom in situation.derived:
        m = _ASSERTS.match(atom.replace(" ", ""))
        if m and m.group(1) == clause_id:
            out.add(m.group(2))
    return frozenset(out)


def resolve_through_closure(situation, clause_id, closure):
    """⛔ THE NAIVE COMPARISON — kept ONLY so its blindness stays executable.

    `cepa` = closed-except-permitted-above: silence permits. Under it, an
    emptied `m0217` returns `permit` in all 8 situations, exactly as the intact
    module does, and stage 3 reports "8/8 passed" on a worthless translation.
    Never call this from the report.
    """
    st = derived_status(situation, clause_id)
    if "forbid" in st:
        return "forbid"
    if "permit" in st:
        return "permit"
    return "permit" if closure == "cepa" else "forbid"


@dataclasses.dataclass(frozen=True)
class Labelling:
    situation_id: str
    label: str
    reason: str

    def __post_init__(self):
        if self.label not in LABELS:
            raise ValueError(f"label {self.label!r} is not one of {LABELS}; "
                             f"`must-be-silent` is a real answer and dropping "
                             f"it re-creates the 8/8 failure")


@dataclasses.dataclass(frozen=True)
class Mismatch:
    situation_id: str
    label: str
    derived: tuple


def adjudicate(situations, labellings):
    """⭐ THE DENOMINATOR IS COMPUTED HERE, NEVER SUPPLIED BY THE SEAT.

    Every enumerated situation carries exactly one labelling, no labelling
    names a situation that was not enumerated, and every label carries a
    non-empty reason. A run failing any of these is NOT ADJUDICATED — a seat
    that skips the hard situations otherwise returns a complete-looking set,
    and the skipped ones are the discriminating ones.
    """
    want = [s.id for s in situations]
    got = [l.situation_id for l in labellings]
    missing = [i for i in want if i not in got]
    if missing:
        raise NotAdjudicated(f"missing a labelling for {missing}; the "
                             f"denominator is the enumeration, not the reply")
    extra = [i for i in got if i not in want]
    if extra:
        raise NotAdjudicated(f"{extra} was not enumerated")
    if len(set(got)) != len(got):
        raise NotAdjudicated("a situation was labelled twice")
    for l in labellings:
        if not str(l.reason or "").strip():
            raise NotAdjudicated(f"{l.situation_id} carries no reason")
    return tuple(labellings)


def label_distribution(labellings):
    d = {k: 0 for k in LABELS}
    for l in labellings:
        d[l.label] += 1
    return d


def compare(situations, labellings, clause_id, projection="derived-atom"):
    """Compare the DERIVED ATOM to the label. Three-valued, never resolved.

    ⛔ `projection="closure-resolved"` is REFUSED AT CONSTRUCTION. Under it the
    emptied `m0217` scores 8 of 8 and stage 3 reports success on an empty
    module; `link.py` also returns "no unresolved references" on it, because
    there is nothing left to resolve.
    """
    if projection not in PROJECTIONS:
        raise ValueError(
            f"projection {projection!r} refused: stage 3 compares derived "
            f"atoms. Resolving silence through the closure declaration scores "
            f"an EMPTIED module 8 of 8, and the closure is a global semantic "
            f"commitment no probe can reach (#13). It is carried in the report "
            f"marked NOT TESTED HERE.")
    by_id = {s.id: s for s in situations}
    out = []
    for l in labellings:
        if l.label not in VERDICT_LABELS:
            continue
        s = by_id.get(l.situation_id)
        if s is None:
            continue
        st = derived_status(s, clause_id)
        want = _STATUS_FOR_LABEL.get(l.label)
        ok = (not st) if want is None else (want in st)
        if not ok:
            out.append(Mismatch(l.situation_id, l.label, tuple(sorted(st))))
    return tuple(out)


# ==========================================================================
#  Findings, and what is allowed to cross into a prompt
# ==========================================================================

def _finding(check_id, severity, where, message, origin):
    return checks.Finding(check_id, severity, where, message, origin)


def structural_finding(check_id, where, message, severity="error"):
    return _finding(check_id, severity, where, message, STRUCTURAL_ORIGIN)


def verdict_findings(mismatches, where):
    """⛔ NEVER DISCLOSED. Naming the situation IS the answer key when the
    verdict space is two-valued in practice, which it is for most rules."""
    return tuple(_finding("probe-verdict-mismatch", "error", where,
                          f"situation {m.situation_id} derived "
                          f"{'/'.join(m.derived) or 'nothing'} but is labelled "
                          f"{m.label}", VERDICT_ORIGIN)
                 for m in mismatches)


def impossible_findings(situations, labellings, clause_id):
    """⭐ The one label that is not a verdict is the one that may be disclosed.

    A module with no integrity constraints filters nothing: `m0217` admits
    `political_content ∧ broad_audience ∧ exploits_individual`, which may well
    be document-impossible, and the mechanism that protected `m0255` is simply
    absent. So `impossible` is a label the seat may return, and it produces a
    finding naming the situation AND NO VERDICT.
    """
    by_id = {s.id: s for s in situations}
    out = []
    for l in labellings:
        if l.label != "impossible":
            continue
        s = by_id.get(l.situation_id)
        where = f"{clause_id}.lp"
        out.append(structural_finding(
            "probe-impossible-situation", where,
            f"the module admits a situation the clause treats as impossible: "
            f"{l.situation_id} ({_atoms_phrase(s)})"))
    return tuple(out)


def _atoms_phrase(s):
    if s is None:
        return "unknown"
    return ", ".join(sorted(s.true_atoms)) or "nothing holds"


def append_findings_to_transcript(transcript, findings):
    """⛔ THE FENCE, IN CODE RATHER THAN IN A CONVENTION.

    The transcript is persistent per clause, so one appended label lives there
    for the rest of that clause's life — the leak `STEP_stage2_and_repair.md`
    §5 was written to stop. Rejected by name: "append the mismatch to the
    transcript"; "disclose the situation but not the label"; "pass a count of
    mismatches" (a count plus an unchanged module is hill-climbing against a
    hidden answer key).
    """
    import translate as _t
    bad = [f for f in findings if f.origin not in _t.DISCLOSABLE_ORIGINS]
    if bad:
        raise DisclosureRefused(
            f"{len(bad)} finding(s) of origin "
            f"{sorted({f.origin for f in bad})} may not enter a repair "
            f"transcript: they carry an expected verdict stage 1 is denied")
    out = list(transcript)
    out.append({"role": "user",
                "content": _t.render_error_log([("stage 3", list(findings))])})
    return out


@dataclasses.dataclass(frozen=True)
class Routing:
    action: str          # repair | re-translate | carry | none
    transcript: tuple = ()
    status: object = None


def route(findings, retranslations_used=0, max_retranslations=1):
    """⭐ RULING (`STEP_stage3.md` §5): a `probe-verdict` mismatch DISCARDS the
    transcript and re-runs stage 1 from a clean prompt, up to
    `max_retranslations`; then the clause is carried, unrepaired, as
    `probe-mismatch` to stage 4 and to a human.

    Re-translation carries NO information from the mismatch at all. That is the
    point: it costs one stage-1 call and leaks zero bits.
    """
    if any(f.origin == VERDICT_ORIGIN for f in findings):
        if retranslations_used < max_retranslations:
            return Routing("re-translate", (), None)
        return Routing("carry", (), "probe-mismatch")
    if any(f.origin == STRUCTURAL_ORIGIN and f.severity == "error"
           for f in findings):
        return Routing("repair", (), None)
    return Routing("none", (), None)


# ==========================================================================
#  5 — the seat: what it is shown, and what it is denied
# ==========================================================================

SEAT_BRIEF = """\
You are labelling test situations for ONE clause of a written specification.

You are shown the clause, the clauses it cross-references, an act, and a list
of situations. For each situation, say what the CLAUSE requires:

  must-forbid     the clause requires that this act be refused here
  must-permit     the clause requires that this act be allowed here
  must-be-silent  the clause does not speak to this situation at all
  impossible      this situation cannot arise; the clause treats it as
                  incoherent (this is not a verdict about the act)

⭐ `must-be-silent` is a REAL ANSWER and it is the commonest one. A clause that
governs one act says nothing about most situations. Do not stretch the clause
to cover a situation it does not reach; saying so is the informative answer,
exactly as declining to translate is at stage 1.

Answer with JSON: {"labels": [{"situation": "...", "label": "...",
"reason": "..."}]} — every situation you were shown, exactly once, each with a
non-empty reason.
"""

#: Patterns that must never reach the seat. #5 (hollow stubs) arrives here in a
#: new form: the situations are expressed in the TRANSLATOR'S OWN COINED
#: PREDICATE NAMES, which echo the document's words by construction, so a seat
#: shown `political_content/1` grades the NAME. Invariant 1: the read-back
#: renders the definition, not the label.
_DISCLOSURE = (
    (re.compile(r"[a-z][A-Za-z0-9_]*/\d"), "a coined predicate signature"),
    (re.compile(r":-"), "a rule from the module"),
    (re.compile(r"\basserts\s*\("), "the module's assertions"),
    (re.compile(r"\bbeats\s*\("), "the module's superiority relation"),
    (re.compile(r"\b(cepa|cnpa)\b", re.I), "the closure declaration"),
    (re.compile(r"\bclosure\b", re.I), "the closure declaration"),
    (re.compile(r"\bderived\s*:", re.I), "the derived status"),
    (re.compile(r"\bCLAIMS?\b\s*:"), "the module's claims list — the "
                                     "translator's own reading"),
    (re.compile(r"%%|%!"), "a module header"),
)


def _refuse_disclosure(text, where):
    for pat, what in _DISCLOSURE:
        if pat.search(text):
            raise DisclosureRefused(
                f"{where} carries {what}; a stage-3 seat is shown the CLAUSE "
                f"and the situation in glosses, never the module")


def render_situation(situation, atoms, concepts):
    """One English sentence per fact, rendered from `concepts.json` GLOSSES.

    ⛔ Never the coined predicate names. A gloss that is missing is a refusal,
    not a fallback to the name.
    """
    gloss = {str(r.get("concept") or "").strip(): str(r.get("gloss") or "")
             for r in (concepts or [])}
    lines = [situation.id]
    for a in atoms:
        name, _, rest = a.partition("(")
        args = [x for x in rest.rstrip(")").split(",") if x] if rest else []
        g = gloss.get(f"{name}/{len(args)}")
        if not g:
            raise DisclosureRefused(
                f"no gloss for `{name}/{len(args)}`: a seat must never be "
                f"shown a bare predicate name (#5, hollow stubs)")
        const = [x for x in args if _is_const(x)
                 and x != PROBE_DEFAULTS["placeholder"]]
        suffix = f" (concerning: {', '.join(const)})" if const else ""
        yes = "yes" if a in situation.true_atoms else "no"
        lines.append(f"  {yes}: {g}{suffix}")
    return "\n".join(lines)


def build_seat_prompt(clause_text, cross_reference_texts, act_phrase,
                      situations):
    """Assemble the seat's user block. Every SUPPLIED part is checked first.

    ⚠️ The brief itself names the four labels, so the disclosure check runs on
    the caller's parts only — checking the assembled text would refuse the
    brief for containing `must-permit`.
    """
    parts = [("clause text", clause_text), ("act", act_phrase)]
    parts += [("a cross-reference", t) for t in cross_reference_texts]
    parts += [("a situation", t) for t in situations]
    for where, text in parts:
        _refuse_disclosure(str(text), where)
    out = [SEAT_BRIEF, "", "THE CLAUSE", "", clause_text.strip(), ""]
    if cross_reference_texts:
        out += ["CLAUSES IT CROSS-REFERENCES", ""]
        out += [t.strip() + "\n" for t in cross_reference_texts]
    out += [f"THE ACT: {act_phrase}", "", "THE SITUATIONS", ""]
    out += list(situations)
    return "\n".join(out)


def label_situations(report, clause_text, cross_reference_texts, act_phrase,
                     concepts, client_factory=None):
    """[L] — the only paid work in stage 3. ONE batched call per clause.

    ⛔ `client_factory` is REQUIRED. Omitting it raises rather than building a
    live client: nothing in this build is authorised to spend, and a default
    that quietly reaches the network is the one mistake that cannot be undone
    by a revert.
    """
    if client_factory is None:
        raise ProbeError(
            "label_situations needs an explicit `client_factory`; stage 3's "
            "labelling half is not authorised to spend and must be driven "
            "through the seam")
    atoms = report.enumeration.atoms
    rendered = tuple(render_situation(s, atoms, concepts)
                     for s in report.covering)
    prompt = build_seat_prompt(clause_text, cross_reference_texts, act_phrase,
                               rendered)
    client = client_factory()
    raw = client.complete_messages(SEAT_BRIEF,
                                   [{"role": "user", "content": prompt}])
    data = json.loads(raw) if isinstance(raw, str) else raw
    labellings = tuple(Labelling(str(r["situation"]), str(r["label"]),
                                 str(r.get("reason", "")))
                       for r in data["labels"])
    return adjudicate(report.covering, labellings)


# ==========================================================================
#  The report
# ==========================================================================

#: ⛔ #15: a per-clause single-number pass rate is what let `8/8` look like
#: evidence. A pass is reported as a VECTOR — `1 must-permit · 0 must-forbid ·
#: 3 must-be-silent` over a covering set of 4 — plus the discriminating count,
#: which is the number that matters.
_PASS_RATE_KEY = re.compile(r"pass[_ ]?rate|passrate|passed|pass_ratio|"
                            r"\bscore\b|percent", re.I)


def refuse_pass_rate(mapping):
    bad = [k for k in mapping if _PASS_RATE_KEY.search(str(k))]
    if bad:
        raise ValueError(
            f"{bad} is a per-clause pass rate and is refused: `8/8` on a module "
            f"with its only rule deleted is what this whole stage exists to "
            f"stop. Report the label vector and the discriminating count.")


@dataclasses.dataclass
class ProbeReport:
    clause_id: str
    outcome: str
    reasons: tuple = ()
    signature: tuple = ()
    ground_atoms: tuple = ()
    candidates: int = 0
    coherent: int = 0
    suppressed: int = 0
    covering: tuple = ()
    coverage: object = None
    discriminating: int = 0
    input_pairs: dict = dataclasses.field(default_factory=dict)
    undiscriminated_inputs: tuple = ()
    labels: object = None
    mismatches: tuple = ()
    forbid_body_claims: tuple = ()
    closure_declared: dict = dataclasses.field(default_factory=dict)
    max_signature: int = PROBE_DEFAULTS["max_signature"]
    max_suppression_rate: float = PROBE_DEFAULTS["max_suppression_rate"]
    findings: tuple = ()
    enumeration: object = dataclasses.field(default=None, repr=False)
    extra: dict = dataclasses.field(default_factory=dict)

    def __post_init__(self):
        if self.outcome not in OUTCOMES:
            raise ValueError(f"outcome {self.outcome!r} is not one of "
                             f"{OUTCOMES}")

    @property
    def ground_atom_count(self):
        return len(self.ground_atoms)

    @property
    def aggregates(self):
        return self.outcome in AGGREGATING_OUTCOMES

    def to_json(self):
        d = {
            "clause_id": self.clause_id,
            "outcome": self.outcome,
            "reasons": list(self.reasons),
            "signature": list(self.signature),
            "ground_atoms": list(self.ground_atoms),
            "candidates": self.candidates,
            "coherent": self.coherent,
            "suppressed": self.suppressed,
            "covering_set": [s.id for s in self.covering],
            "coverage": None if self.coverage is None else {
                "criterion": self.coverage.criterion,
                "rules_mutated": self.coverage.rules_mutated,
                "per_rule": {str(k): v
                             for k, v in self.coverage.per_rule.items()},
                "uncovered_rules": list(self.coverage.uncovered_rules),
            },
            "discriminating_situations": self.discriminating,
            "undiscriminated_inputs": list(self.undiscriminated_inputs),
            "labels": (None if self.labels is None
                       else label_distribution(self.labels)),
            "mismatches": [dataclasses.asdict(m) for m in self.mismatches],
            "forbid_body_claims": list(self.forbid_body_claims),
            "closure_declared": dict(self.closure_declared),
            "cap": self.max_signature,
            "max_suppression_rate": self.max_suppression_rate,
            "findings": [dataclasses.asdict(f) for f in self.findings],
            "enters_an_aggregate": self.aggregates,
        }
        d.update(self.extra)
        refuse_pass_rate(d)
        return d

    def render(self):
        k = len(self.ground_atoms)
        cap = self.max_signature
        within = "WITHIN CAP" if k <= cap else "OVER CAP"
        out = [
            f"probe report: {self.clause_id}",
            f"outcome: {self.outcome}"
            + ("" if self.aggregates
               else "   [does NOT aggregate into a pass rate]"),
            # ⚠️ On its own line, NOT appended to the outcome: `m0255` carries
            # `no-acts` and fails for two uncovered rules, and rendering
            # `failed (no-acts)` reads as though the header were the fault.
            "limits: " + (", ".join(self.reasons) or "(none)"),
            f"signature: {len(self.signature)} predicate(s) · {k} ground "
            f"atom(s) · 2^{k} candidates · cap 2^{cap} · {within}",
        ]
        if self.coverage is not None:
            out.append(self.coverage.render())
        else:
            out.append("|R| = n/a — no coverage computed")
        out.append(f"candidates {self.candidates} · coherent {self.coherent} · "
                   f"suppressed {self.suppressed} "
                   f"(error above {self.max_suppression_rate:.2f}) · "
                   f"covering set {len(self.covering)}")
        if self.labels is None:
            out.append("labels: NOT RUN — the labelled half has not been run "
                       "for this clause")
        else:
            d = label_distribution(self.labels)
            out.append("labels: " + " · ".join(f"{d[k2]} {k2}" for k2 in LABELS)
                       + f"   (covering set {len(self.covering)})")
        out.append(f"discriminating situations: {self.discriminating}")
        out.append("inputs with no discriminating pair: "
                   + (", ".join(self.undiscriminated_inputs) or "(none)"))
        out.append(f"forbid_body claims: {len(self.forbid_body_claims)}  "
                   f"(NOT TESTABLE HERE — checked by link.py, excluded from "
                   f"the denominator)")
        decl = ", ".join(f"{a} = {c}"
                         for a, c in sorted(self.closure_declared.items()))
        out.append(f"closure declared: {decl or '(none)'}      "
                   f"(NOT TESTED HERE — #13)")
        out.append(f"mismatches: {len(self.mismatches)}   "
                   f"⛔ withheld from any repair prompt")
        for f in self.findings:
            out.append(f"  - [{f.severity}] [{f.check_id}] {f.message}")
        return "\n".join(out)


# ==========================================================================
#  The entry point
# ==========================================================================

def probe_clause(target_path, link_paths, concepts, cfg=None, claims_map=None):
    """Stage 3's deterministic half over one module that passed stage 2.

    Returns a `ProbeReport`. The labelled half runs separately, through
    `label_situations`, and needs a `client_factory`.
    """
    pc = probe_config(cfg)
    text = open(target_path, encoding="utf-8").read()
    link_texts = [open(p, encoding="utf-8").read() for p in link_paths]
    hdr = header_of(text)
    clause_id = hdr["clause"] or os.path.basename(target_path).split(".")[0]
    where = os.path.basename(target_path)
    common = dict(clause_id=clause_id,
                  closure_declared=dict(hdr["closure"]),
                  forbid_body_claims=tuple(f"{h} <- {b}"
                                           for h, b in hdr["forbid_body"]),
                  max_signature=pc["max_signature"],
                  max_suppression_rate=pc["max_suppression_rate"])

    # ---- the two INDEPENDENT refusals. They must not collapse. ----------
    #
    # ⚠️ AND THEY GATE DIFFERENT THINGS — a correction to `STEP_stage3.md` §7,
    # forced by running it. §7 folds both into one outcome, and `m0037` (the
    # only case it had) carries BOTH, so the difference was invisible. `m0255`
    # separates them in the other direction: it has ten rules and **no `%% acts:`
    # header at all** — it was hand-written under the superseded contract, with
    # a private `lifted/binds/violation` vocabulary and no `asserts/3`. Under §7
    # as written, stage 3 refuses the very module §6 uses to justify its
    # criterion, and the dead C3 claim §6 found would never be reported.
    #
    # ⇒ `|R| = 0` stops everything: there is nothing to mutate.
    #   `no acts` stops the LABELLED half only: no act, no must-forbid /
    #   must-permit to compare. The outcome is still `no-testable-content` —
    #   non-aggregating, never a pass — but the deterministic evidence is
    #   COMPUTED AND CARRIED, because discarding a real finding on a header
    #   technicality is not a refusal, it is a loss.
    reasons = []
    if not hdr["acts"]:
        reasons.append("no-acts")
    rules = module_rules(text)
    if not rules:
        reasons.append("zero-rules")
        return ProbeReport(outcome="no-testable-content",
                           reasons=tuple(reasons), **common)

    sig = situation_signature(text, link_texts, concepts)
    atoms = ground_atoms(sig, [text] + link_texts, pc["placeholder"])
    common.update(signature=sig, ground_atoms=atoms)

    # ---- the cap. Not a sampling fallback. ------------------------------
    if len(atoms) > pc["max_signature"]:
        return ProbeReport(
            outcome="signature-too-large",
            reasons=(f"{len(atoms)} ground atoms over cap "
                     f"{pc['max_signature']}",),
            findings=(structural_finding(
                "signature-too-large", where,
                f"the situation signature grounds to {len(atoms)} atoms, over "
                f"the declared cap of {pc['max_signature']}; no enumeration "
                f"was produced and none was sampled"),),
            **common)

    findings = []
    # ⭐ Q-22. The signature now enumerates these (see `situation_signature`),
    # so the module is testable — but `requires` claimed another clause would
    # define them and nothing does. Enumerating an unkept promise is the right
    # repair AND a different statement from keeping it, so it is reported.
    unmet = unsatisfied_requires(text, link_texts)
    if unmet:
        findings.append(structural_finding(
            "requires-unsatisfied", where,
            f"{', '.join(sorted(unmet))} declared in `requires` — another "
            f"clause was supposed to define these and nothing in scope does. "
            f"They are enumerated as situation inputs so the rules resting on "
            f"them can be tested, but the link they assert does not exist",
            # ⚠️ `note`, deliberately, and NOT `error`. Only `error` drives the
            # stage-2 repair loop, and no rewrite of THIS module can conjure
            # the clause that was supposed to define the predicate — it is a
            # fact about corpus coverage. `DEBUGGING_TIPS` §7: a repair loop
            # that chases notes does not converge. It must still be SEEN,
            # which is the census's job, not the repairer's.
            severity="note"))
    if not atoms:
        # ⛔ The guard revision 2 got wrong. `|enumeration| == 0` never fires
        # here: an empty signature yields 2^0 = ONE all-false situation.
        findings.append(structural_finding(
            "signature-empty", where,
            "the situation signature is empty, so the enumeration is a single "
            "all-false situation and every check below is vacuous"))

    enum = enumerate_situations(text, link_texts, atoms)
    if enum.situations == ():
        findings.append(structural_finding(
            "coherent-set-empty", where,
            "no situation satisfies the module's own integrity constraints, so "
            "every check below ran over nothing"))
    elif enum.candidates and \
            enum.suppressed / enum.candidates > pc["max_suppression_rate"]:
        findings.append(structural_finding(
            "suppression-excessive", where,
            f"{enum.suppressed} of {enum.candidates} candidate situations are "
            f"rejected by the module's own constraints, above the declared "
            f"threshold of {pc['max_suppression_rate']:.2f}"))

    coverage, changed = discrimination_coverage(text, link_texts, atoms, enum,
                                                claims_map)
    for i in coverage.uncovered_rules:
        findings.append(structural_finding(
            "rule-not-discriminated", where,
            f"rule {i} is in no derivation that any situation distinguishes: "
            f"deleting it changes nothing"))
    pairs = input_discrimination(enum)
    undiscriminated = tuple(a for a in enum.atoms if pairs[a] == 0)

    if any(f.severity == "error" for f in findings):
        outcome = "failed"
    elif reasons:                      # rules but no acts — see the note above
        outcome = "no-testable-content"
    else:
        outcome = "passed"
    return ProbeReport(
        outcome=outcome, reasons=tuple(reasons),
        candidates=enum.candidates, coherent=len(enum.situations),
        suppressed=enum.suppressed, covering=covering_set(enum),
        coverage=coverage, discriminating=len(changed),
        input_pairs=pairs, undiscriminated_inputs=undiscriminated,
        findings=tuple(findings), enumeration=enum, **common)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    as_json = "--json" in argv
    argv = [a for a in argv if a != "--json"]
    if not argv:
        print("usage: probe.py TARGET.lp [LINK.lp ...] [--json]")
        return 2
    target, links = argv[0], argv[1:]
    rows, _loaded, _missing = link.discover_concept_table([target] + links)
    rep = probe_clause(target, links, rows or [])
    print(json.dumps(rep.to_json(), indent=1) if as_json else rep.render())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
