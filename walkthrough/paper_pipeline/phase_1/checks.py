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
every one looks fine"*). That is attack A in `resources/03_pipeline.md`, "the repair guard is
TYPED, not sized". A
loop driven by notes does not fail to terminate; it terminates by teaching the
model to make every translation look fine. So: notes stay in `findings`, stay
countable in the run report, and never set `repair_needed`.
"""

import dataclasses
import os
import re
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


# ==========================================================================
#  THE ARITY-AWARE HALF OF THE DECLARATION CHECK  (DC-5)
# ==========================================================================
#
# ⭐ WHAT IS MISSING UPSTREAM. `schema.py`'s D4b declaration check matches by
# NAME ONLY: `declared = {f.atom.split("(")[0] ...}` and `known = declared |
# {p.split("/")[0] for p in requires + inputs}`. So a module that declares
# `inputs: ['conflict/2']` and writes `conflict(P1, P2, C)` in a body passes
# the module-level check with ZERO breaches — measured, on the stored module
# for `l1_170_n047`. The mismatch surfaces one stage later as
#
#     `conflict/3` is used in a body, defined nowhere in this link scope, and
#     declared neither in `%% inputs:` nor in `%% requires:` ...
#
# which reads like a MISSING UPSTREAM MODULE. It is not: the declaration is
# right there in the module being repaired, at the wrong arity. The model
# spends its repair rounds looking for someone else's export.
#
# ⚠️ AND IT IS NOT CHEAP. Exactly four instances corpus-wide (`l1_170_n047`
# conflict 2→3, `l1_170_n087` output_consumed_by 2→1, `l1_170_n088`
# sequence_of_messages 3→4, `l171_426_n024` user_request 1→2) and ALL FOUR sit
# on `unrepaired` clauses — 16% of the 19 losses of prompt generation 11, more
# than four other mechanisms combined. A tier analysis puts arity mismatch at
# 0/11 first-try and 73% unrepaired (p=0.004).
#
# ⛔ THE PERMISSIVE READING IS NOT THE CONTRACT'S INTENT, and that was checked
# before tightening rather than assumed. The contract says the opposite in
# three places: the `requires`/`inputs` format guard refuses an entry that is
# not `name/arity` because *"two predicates sharing a name but taking
# different numbers of arguments are different predicates; without the arity
# they link to each other silently"*; D4b's own message tells the model
# "`{name}/N` must ALSO appear in one of those three"; and `link._atom_id`
# exists precisely so a body atom can be compared to a header entry BY
# IDENTITY, name and arity together. Name-only matching is an implementation
# slip in one expression, not a designed tolerance.
#
# ⛔ IT DOES NOT MASK `undeclared-body-name`. It fires only when the name IS
# declared somewhere in this module and no declaration carries the arity the
# body uses. A name declared nowhere stays entirely with D4b — one act, one
# message, and the model is never told two different things about one name.
#
# ⭐ WHY HERE AND NOT IN `schema.py`. This needs nothing but the module's own
# declaration blocks and its bodies, so it runs identically from stage 2's
# single entry point; `schema.py` is guard-watched and its D4b expression is
# located by phrase by `mutate_schema.py`. Every gating path — `translate.py`'s
# repair loop, `test_prompt_examples.py`'s check of the worked examples — goes
# through `run_checks`, so nothing that decides an outcome escapes it. The one
# residual is a DIRECT `schema.validate` caller (`seats.py`, some test
# fixtures), which sees the module as clean; that is recorded, with the exact
# one-line diff that would close it, in `_debug_gen11/PROPOSED_schema_arity.md`
# — proposed, not applied.
#
# The finding is emitted with `origin="schema"` and the shared
# `schema-breach` id ON PURPOSE. It is a module-level contract breach of
# exactly D4b's species, and the two origins `translate.py` will disclose to a
# repair prompt are fixed (`DISCLOSABLE_ORIGINS`) — a third origin invented
# here would be WITHHELD from the very prompt this check exists to inform.

#: The phrase that identifies this guard in a findings list. `schema.py`'s
#: guards carry no per-guard id and are located by a distinctive PHRASE
#: (`SCHEMA_CHECK_ID` above); this one is emitted under the same id, so it is
#: located the same way, and anything keying off it keys off this constant
#: rather than retyping the sentence.
ARITY_MESSAGE_MARK = "but a body uses it at"


def _arity_of(argstr):
    """`'(P1, P2, C)'` -> 3, `''` -> 0. `link`'s own depth-aware splitter, so
    `p(f(a,b), C)` counts 2 and not 3."""
    inner = argstr.strip()[1:-1] if argstr.strip() else ""
    return 0 if not inner.strip() else len(link._split_top(inner, ","))


def _blocks(module):
    """`(ontology_atoms, borrowed, bodies)` from a `schema.Module` OR the raw
    module dict.

    ⚠️ THE DICT PATH IS NOT A CONVENIENCE. The four real instances are stored
    live-run modules, and one of them (`l1_170_n088`) no longer CONSTRUCTS
    under today's contract — it trips D4b on a different, undeclared name. A
    pin that could only run through `schema.Module` could not use it, and it
    is the instance that proves the two checks coexist. Bodies are read from
    `asserts`, `beats` and `ontology`: exactly D4b's population, so this check
    can never see a name D4b does not.
    """
    def field(name):
        return (module.get(name) or []) if isinstance(module, dict) \
            else (getattr(module, name, None) or [])

    def attr(item, name):
        return item.get(name) if isinstance(item, dict) \
            else getattr(item, name, None)

    atoms = [attr(f, "atom") or "" for f in field("ontology")]
    borrowed = [p for p in list(field("requires")) + list(field("inputs"))
                if isinstance(p, str)]
    bodies = []
    for block in ("asserts", "beats", "ontology"):
        for i, item in enumerate(field(block)):
            bodies.append((f"{block}[{i}]", attr(item, "body") or ""))
    return atoms, borrowed, bodies


def declared_arities(module):
    """`{name: {arity, ...}}` over the THREE declaration sites, with arity.

    An `ontology` head declares at the arity it is written with; a `requires`
    or `inputs` entry at the arity it names. A malformed borrow (no `/`, or a
    non-integer arity) contributes the NAME with no arity — `schema.py`
    already breaches on it, and swallowing it here would turn one defect into
    two messages about the same line.
    """
    atoms, borrowed, _ = _blocks(module)
    out = {}
    for atom in atoms:
        head = atom.strip()
        name = head.split("(")[0].strip()
        if not name:
            continue
        out.setdefault(name, set()).add(
            _arity_of(head[len(name):]) if "(" in head else 0)
    for p in borrowed:
        name, _, ar = p.partition("/")
        name = name.strip()
        if not name:
            continue
        slot = out.setdefault(name, set())
        if ar.strip().isdigit():
            slot.add(int(ar.strip()))
    return out


def body_uses(body):
    """`[(name, arity), ...]` for every predicate a body applies to arguments.

    The name regex is D4b's, character for character, so the two checks range
    over one population; the arity comes from matching the opening paren at
    depth 0.
    """
    out = []
    for hit in re.finditer(r"(?<![A-Za-z0-9_])([a-z][A-Za-z0-9_]*)\s*\(", body):
        depth, start = 0, hit.end() - 1
        for j in range(start, len(body)):
            if body[j] == "(":
                depth += 1
            elif body[j] == ")":
                depth -= 1
                if depth == 0:
                    out.append((hit.group(1), _arity_of(body[start:j + 1])))
                    break
        else:
            continue          # unbalanced — `schema.py`'s parser owns that
    return out


def arity_mismatches(module):
    """`[(where, name, sorted_declared_arities, used_arity), ...]`.

    Pure, deterministic, and takes a `schema.Module` or the raw dict. Empty
    for a module that declares every name it uses at the arity it uses it —
    including one that declares the same name at two arities deliberately,
    which is legal and is why membership is tested against the SET.
    """
    declared = declared_arities(module)
    _, _, bodies = _blocks(module)
    out = []
    for where, body in bodies:
        for name, arity in body_uses(body):
            if name in schema.RESERVED:
                continue
            known = declared.get(name)
            # not declared at all -> `undeclared-body-name` owns it, alone
            if not known or arity in known:
                continue
            out.append((where, name, sorted(known), arity))
    return out


def arity_findings(module):
    """`arity_mismatches`, rendered as stage-2 Findings. No fix in the text —
    it names what is the case (declared at X, used at Y) and stops, under the
    same denial as every other `Finding`."""
    out = []
    for where, name, known, arity in arity_mismatches(module):
        shown = ", ".join(f"`{name}/{a}`" for a in known)
        out.append(Finding(
            SCHEMA_CHECK_ID, "error", where,
            f"`{name}` is declared at {shown} {ARITY_MESSAGE_MARK} "
            f"`{name}/{arity}`. A predicate's identity is its name AND its "
            f"argument count, so those are two different predicates and only "
            f"one of them is declared. Either the declaration in "
            f"`ontology`/`requires`/`inputs` or the body atom has the wrong "
            f"number of arguments — this is INSIDE this module, not a missing "
            f"upstream clause",
            "schema"))
    return out


#: A read-back that says the act is DISFAVOURED while `status` says `prefer`.
#: Both halves come from the same entry, so this is a self-contradiction inside
#: one object — the stage-2 property exactly (`03_pipeline.md:497`): derived
#: from the module alone, no expected verdict anywhere near it.
POLARITY_CHECK_ID = "prefer-polarity"
POLARITY_MESSAGE_MARK = "but its own read-back calls it"

#: ⚠️ WIDENED 2026-08-16 after the Opus reference set measured this pattern's
#: RECALL AT 4 OF 5 real inversions. It carried `should be avoided` and missed
#: `l4252_4482_n016`, whose read-backs say "is to be avoided" / "is to be
#: minimized" -- one alternation short. That clause is the worst instance in
#: the corpus: ALL THREE of its asserts are inverted, so the compiled module
#: PREFERS including redundant phrases from a span saying to minimize them.
#: A near-miss regex reads as a working check, which is why its recall was
#: measured against a set with a known answer rather than assumed.
#: Words a read-back uses when it means the act is to be AVOIDED. Deliberately
#: narrow: this fires only when the read-back SAYS SO, never on a guess about
#: what the clause meant. A wider net here would be a semantic judgement, and
#: semantic judgement is stage 4's job, not stage 2's.
_DISFAVOURED = re.compile(
    r"\b(dispreferred|disprefer|not preferred|discouraged|"
    r"(?:should|is to|are to) be (?:avoided|minimi[sz]ed|reduced|limited)|"
    r"is worse|undesirable)\b", re.I)


def polarity_mismatches(module):
    """Yield (where, act, phrase) for every `prefer` assert whose own
    read-back says the act is disfavoured.

    ⛔ WHY THIS EXISTS AND WHY NOTHING ELSE CATCHES IT (2026-08-15 stage-4
    read). `Status` has NO NEGATIVE POLE — there is no `disprefer` — so for a
    clause that says "avoid X" or marks X as a BAD example there is no correct
    single-act encoding, and the model reliably picks the one that INVERTS the
    meaning: `prefer` attached to the act the document tells it to avoid. The
    compiled ASP then asserts the opposite of the specification. Measured
    instance, `l1974_2125_n019.lp:57`, from a BAD-marked example of escalating
    emotional closeness with a lonely user:

        asserts(l1974_2125_n019, prefer, respond_with(R))
            :- escalates_emotional_closeness(R).

    ⛔ EVERY OTHER CHECK PASSES IT, INCLUDING ALL FOUR STAGE-4 SEATS. The
    read-back prose is CORRECT ("responding with % is dispreferred"); only
    `status` is wrong. Seats 4a-4d all judge the English RENDERING — 4b is
    explicitly not shown the program at all — so a defect living in the gap
    between a correct rendering and the field it was rendered from is
    structurally invisible to them. That is why this is mechanical and here.
    """
    out = []
    for i, a in enumerate(getattr(module, "asserts", None) or []):
        if getattr(a, "status", None) != "prefer":
            continue
        m = _DISFAVOURED.search(str(getattr(a, "read_back", "") or ""))
        if m:
            out.append((f"asserts[{i}]", getattr(a, "act", "?"), m.group(0)))
    return out


def polarity_findings(module):
    """`polarity_mismatches` as Findings — NAMING WHAT IS THE CASE, NO FIX.

    ⛔ ORIGIN IS `stage4-detector`, WHICH IS *NOT* DISCLOSABLE, AND THAT IS A
    DELIBERATE RULING, NOT AN OVERSIGHT (2026-08-15). Every instinct says a
    self-contradiction inside one entry is stage-2-shaped and should reach the
    repair loop. It must not, YET, and the reason is defect-trading: because
    `status` has no negative pole, a model told "these two disagree" CANNOT
    resolve it correctly. Its two available moves are to drop the entry —
    deleting the specification's guidance — or to REWRITE THE READ-BACK to say
    "preferred", which silences the only surviving evidence of the inversion
    and leaves a module that is semantically backwards AND internally
    consistent. That is strictly worse than what we have now, and it is the
    exact shape of the defect-trading this project has been bitten by before.

    ⭐ THE PRECONDITION FOR PROMOTING THIS TO A DISCLOSABLE STAGE-2 CHECK is a
    negative pole in `status` (a `disprefer`, or a two-act comparative form) —
    an owner ruling on `schema.py`, which is guard-watched. Once a correct
    encoding EXISTS, this becomes an ordinary stage-2 finding and the origin
    should change to "schema" in the same commit that adds the pole. Until
    then it detects and reports and does not touch the loop.
    """
    return [Finding(
        POLARITY_CHECK_ID, "error", where,
        f"`{act}` is asserted with status `prefer` {POLARITY_MESSAGE_MARK} "
        f"'{phrase}'. The compiled rule therefore states a PREFERENCE FOR an "
        f"act this module's own rendering describes as one to avoid, and the "
        f"two cannot both be what the clause says",
        "stage4-detector") for where, act, phrase in polarity_mismatches(module)]


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

    # ⭐ The arity half of the declaration check, which `schema.py` matches by
    # name only (DC-5; see the block at the top of this file). Deliberately
    # AFTER the abstention return: an abstention is forced empty on every
    # content field, so it has no bodies to check, and adding findings before
    # that return could only ever turn a terminal outcome into a repair round.
    findings += arity_findings(mod)
    # ⭐ The prefer-polarity detector. Same placement rationale as the arity
    # check above (after the abstention return — an abstention has no asserts).
    # Its origin is NOT disclosable, so it can never turn a terminal outcome
    # into a repair round; it is reported and counted, and nothing more. See
    # `polarity_findings` for why that restraint is the whole point.
    findings += polarity_findings(mod)

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
