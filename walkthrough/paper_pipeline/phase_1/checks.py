"""Stage 2's entry point: what is wrong with this attempt, COMPLETELY.

    from checks import run_checks
    result = run_checks(obj, clause, corpus_ids)

One call, one attempt, one answer. `run_checks` merges the two halves of stage
2 — the contract breaches `schema.validate_all` collects, and the deterministic
link checks `link.collect` returns — into a single findings list, and decides
the attempt's outcome from it.

⭐ WHY ONE ENTRY POINT, AND WHY IT RETURNS EVERYTHING.
`schema.validate` raises on the first breach; `link.collect` returns many;
neither knows about the other. A repair loop built on those directly repairs one
defect per PAID MODEL CALL, and a module with three read-back breaches and an
undeclared name costs four round-trips for a set of defects a model could fix in
one. The complete finding set is this module's whole reason to exist.

⛔ WHAT IT DOES NOT DO. It does not judge the translation. Whether the module
for clause m0091 says what clause m0091 says is stage 4 and needs a reader.
Passing every check here must never be reported as "correct": `03_pipeline.md`
Part 7 — correctness is not local, and any per-clause pass rate reported before
stage 9 overstates the result.

THE THREE OUTCOMES

    translated   the module constructed and no ERROR-severity finding stands.
                 Notes may be present; see the severity ruling below.
    abstained    ⭐ TERMINAL. Not a findings list — see `run_checks`.
    invalid      the module could not be constructed, or an error stands.

⭐ THE SEVERITY RULING: ONLY `error` DRIVES A REPAIR. `note` is reported,
counted and inert.

`link.py` emits two severities, and two of its checks are `note` deliberately:

  requires-unprovided  at single-module scope a `%% requires:` predicate is
                       head-less BY DESIGN. It fires on every CORRECT module
                       this pipeline emits.
  concept-declared     the counterpart of `situation-input`: a name that stops
                       being an error must stay visible rather than vanish.
  concept-multi-gloss  one name, two definitions — measured at 46 of 228 reused
                       names (20%), which is the ORDINARY rate for this task.

⚠️ THE CONSEQUENCE, STATED RATHER THAN DISCOVERED LATER. If notes drove repair,
a single-module run would not terminate on `requires-unprovided`: the finding is
true of a correct module, so no faithful repair clears it. The only CONVERGENT
repair is to move the predicate from `requires` into `inputs` — which clears the
finding, returns zero findings, and destroys the distinction `03_pipeline.md`
calls load-bearing (*"without it, 'a name nothing defines' cannot be told apart
from 'a name supplied at query time', and every translation looks broken or
every one looks fine"*). That is attack A in `STEP_stage2_and_repair.md` §4. A
loop driven by notes does not fail to terminate; it terminates by teaching the
model to make every translation look fine. So: notes stay in `findings`, stay
countable in the run report, and never set `repair_needed`.
"""

import dataclasses
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
WALKTHROUGH = os.path.dirname(os.path.dirname(HERE))
for _p in (HERE, WALKTHROUGH):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import link                                                    # noqa: E402
import schema                                                  # noqa: E402

#: The only two severities. A third invented here would silently escape the
#: ruling above — `repair_needed` is defined as "any error", so a `warning`
#: level would drive nothing and an `error`-but-not-really level would drive
#: everything, with no test noticing which.
SEVERITIES = ("error", "note")

#: `schema.py` guards carry no stable per-guard identifiers — they are located
#: by a distinctive PHRASE from their message (`mutate_schema.py`), and giving
#: each one an id would mean editing every raise site and breaking that
#: coupling. So every contract breach shares one check id and the MESSAGE is
#: the discriminator. ⚠️ Consequence for anyone keying off this: assert the
#: message fragment as well, never `check_id` alone.
SCHEMA_CHECK_ID = "schema-breach"


@dataclasses.dataclass(frozen=True)
class Finding:
    """One thing that is wrong with an attempt, and where.

    ⛔ CARRIES NO SUGGESTED FIX AND NO EXPECTED VALUE, exactly as
    `link.Finding` does not. These feed a stage-2 repair prompt and stage 1 is
    denied the expected verdicts; a `fix=` or `expected=` field would put the
    answer into the prompt that is supposed to produce it, and every later
    measurement of whether the repair worked would be measuring the hint.

    ⭐ `origin` IS REQUIRED AND POSITIONAL, AND MUST NEVER ACQUIRE A DEFAULT.
    Stages 3 and 4 feed this same repair log, and both carry the expected
    answers a translator is explicitly denied — stage 3's probe cases with
    their must-forbid/must-permit labels, and the four review seats. The
    rendered log admits stage-2 origins only, and that rule is enforceable only
    if every producer has to SAY what it is. With a default, a future producer
    silently inherits `origin="schema"`, the log admits its findings, and the
    denial dissolves with nothing to notice it. That is why the marker goes in
    now, while there is only one origin to mark.
    """

    check_id: str          #: `link.py`'s stable ids, or `schema-breach`
    severity: str          #: "error" (drives repair) or "note" (visible, inert)
    where: str             #: a file basename, or `asserts[0]` / `<root>`
    message: str           #: one human sentence, no fix in it
    origin: str            #: "schema" or "link". REQUIRED. Never defaulted.

    def __post_init__(self):
        # An empty origin satisfies "positional, passed" and marks nothing, so
        # a producer that has not decided what it is would otherwise slip
        # through every field-set assertion.
        if not isinstance(self.origin, str) or not self.origin.strip():
            raise ValueError(
                f"Finding.origin is {self.origin!r}: every finding must name "
                f"the stage that produced it, because the repair log admits "
                f"stage-2 origins only and an unmarked finding cannot be "
                f"excluded from it")
        if self.severity not in SEVERITIES:
            raise ValueError(
                f"Finding.severity {self.severity!r} is not one of "
                f"{SEVERITIES}; only `error` drives a repair, so a third level "
                f"would be silently inert or silently binding")

    @classmethod
    def from_link(cls, finding):
        """Adapt a `link.Finding` at the boundary.

        ⚠️ `link.Finding` has no `origin`, and `link.py --self-test` asserts its
        field set by EQUALITY — so it cannot grow one. The adaptation therefore
        happens HERE and `link.py` is not touched. Built from `asdict` on
        purpose: if `link.Finding` ever gains a field, this raises a TypeError
        rather than silently dropping it on the way into the repair log.
        """
        return cls(**dataclasses.asdict(finding), origin="link")


@dataclasses.dataclass(frozen=True)
class CheckResult:
    """One attempt's complete stage-2 verdict."""

    outcome: str                     #: translated | abstained | invalid
    module: object                   #: `schema.Module`, or None if unbuildable
    findings: list                   #: every Finding, both origins, both severities
    #: ⭐ Which repair attempt produced this, or None when the caller did not
    #: say. See `run_checks` — `None` is deliberately NOT `1`.
    attempt: object = None
    abstain_reason: object = None

    @property
    def errors(self):
        return [f for f in self.findings if f.severity == "error"]

    @property
    def notes(self):
        return [f for f in self.findings if f.severity == "note"]

    @property
    def repair_needed(self):
        """Whether this attempt should be sent back. Errors only — see §ruling."""
        return self.outcome == "invalid"

    @property
    def first_attempt(self):
        """True / False / None-for-unrecorded. Three states on purpose."""
        return None if self.attempt is None else self.attempt == 1


def run_checks(obj, clause, corpus_ids, concepts=None, lp_path=None,
               *, attempt=None):
    """Every deterministic check stage 2 has, over one attempt at one clause.

    `obj`         the raw dict a translator returned.
    `clause`      the clause record — `id`, `section_id`, `kind`, `quote`. Its
                  `id` is what the module is checked to agree with.
    `corpus_ids`  every clause id in the corpus, so a citation pointing at
                  nothing is caught rather than passing as well-formed.
    `concepts`    a concept table to check against — the rows
                  `schema.concept_rows` writes. ⚠️ DEFAULTS TO THE MODULE'S OWN
                  ROWS, not to None. Running `link.collect` with no table is the
                  failure mode to avoid, not a neutral default: every declared
                  concept then reads as undeclared and the tool floods with
                  false positives indistinguishable from real findings — 7 of 7
                  on the first live run. We always hold the validated module, so
                  the table is always derivable. Pass a corpus-wide table to get
                  the cross-clause checks; pass `[]` to assert against an empty
                  one.
    `lp_path`     an already-rendered `.lp` to check. Omitted, the module is
                  rendered to a temp file and removed again.
    `attempt`     ⭐ which repair attempt this is. `None` means UNRECORDED, and
                  that is not the same as 1 — see below.

    ⭐ AN ABSTENTION IS A TERMINAL OUTCOME, NOT A FINDINGS LIST.
    A translator that cannot faithfully translate a clause should decline with a
    reason rather than emit something that passes the checks. An abstention is
    forced empty on every content field, so it passes every deterministic check
    TRIVIALLY, and both obvious defaults are harmful: pass it through and it
    enters stage 3 as a passing module with the abstention rate never computed;
    fire a check on it and the loop re-prompts a model that has already said it
    cannot translate faithfully — producing exactly what abstention exists to
    prevent, with an accumulating error log behind it. So: `outcome="abstained"`
    with `findings=[]`, and the caller stops.

    ⚠️ ... BUT AN ABSTENTION ON ATTEMPT 3 IS NOT AN ABSTENTION ON ATTEMPT 1.
    The second is a repair-pressure artifact — the model was told twice it was
    wrong and took the exit — not a first-class answer about the clause.
    Treating them alike lets a model abstain its way out of the hard clauses
    while the rate, which is the reliability signal the whole mechanism exists
    for, reads as though it had judged them. So the attempt is recorded on the
    result, and `first_attempt` is TRI-STATE: an unrecorded attempt reports
    `None`, never `True`. Defaulting it to 1 would make a loop that forgot to
    pass it report every late abstention as a first answer — the same silent
    misclassification `origin` exists to prevent, one field over.

    ⚠️ `outcome="abstained"` is read off the VALIDATED module, never off the raw
    dict. An object that says `abstained` and carries claims is neither an
    abstention nor a translation; reading the raw field would let it terminate
    the loop as a first-class answer.
    """
    clause_id = clause.get("id") if isinstance(clause, dict) else None
    mod, breaches = schema.validate_all(obj, clause_id=clause_id,
                                        known_clause_ids=corpus_ids)
    findings = [Finding(SCHEMA_CHECK_ID, "error", b.where, b.message, "schema")
                for b in breaches]

    if mod is None:
        return CheckResult("invalid", None, findings, attempt, None)

    if mod.outcome == "abstained" and not findings:
        return CheckResult("abstained", mod, [], attempt, mod.abstain_reason)

    if lp_path is None:
        tmp = tempfile.mkdtemp(prefix="stage2_checks_")
        try:
            path = os.path.join(tmp, f"{mod.clause_id}.lp")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(schema.render_lp(mod, clause))
            findings += _link_findings(path, mod, concepts)
        finally:
            for name in os.listdir(tmp):
                os.remove(os.path.join(tmp, name))
            os.rmdir(tmp)
    else:
        findings += _link_findings(lp_path, mod, concepts)

    outcome = "invalid" if any(f.severity == "error" for f in findings) \
        else "translated"
    return CheckResult(outcome, mod, findings, attempt,
                       mod.abstain_reason if mod.outcome == "abstained" else None)


def _link_findings(path, mod, concepts):
    """`link.collect`, with the concept table defaulted to the module's own."""
    rows = schema.concept_rows(mod) if concepts is None else concepts
    return [Finding.from_link(f) for f in link.collect([path], concepts=rows)]
