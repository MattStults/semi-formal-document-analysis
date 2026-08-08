"""What a model must return when asked to translate one clause into logic.

A model is given one clause of a specification and returns one object matching
these types. The object is the record; the `.lp` logic file is rendered from it.

THE FOUR RELATIONS.  Every clause in the corpus is written in the same small
vocabulary, so that clauses translated independently can still be linked and
queried together. A translator does not invent relation names:

    asserts(ClauseId, Status, Act)   this clause attaches a deontic status to
                                     an act. Status is one of exactly four:
                                     forbid, permit, oblige, prefer
    beats(Sayer, Winner, Loser)      this clause says one clause outranks
                                     another, and records WHICH CLAUSE SAYS SO
    defines(ClauseId, Kind, Term)    this clause fixes what a class covers
    an `ontology` block              non-deontic classification, e.g.
                                     restricted(x) — the clause's own subject
                                     matter, where names ARE invented

`prefer` is for comparatives — "minimize side effects", "favour reversible
approaches". They attach a preference, not a prohibition: no situation violates
them, so recording one as `forbid` invents a violation condition the document
does not have.

ACTS ARE ACTS, NOT THINGS.  `asserts` relates a status to `produce(M)`, never to
`restricted_content`. Downstream queries join on acts; a thing in an act's place
joins nothing, derives no conflict, and reports no error.

WHAT VALIDATION HERE DOES AND DOES NOT MEAN.  A provider can guarantee the SHAPE
of a returned object — that the fields exist and have the right types. It cannot
express conditional rules like "a citation is required when the licence is
textual", so those live in the validators below and they RAISE rather than warn.

⚠️ That is format integrity only. Nothing here checks whether the module says
what the clause says: no rule is compared to the text, and a well-formed module
can be entirely wrong. That comparison is a later stage and needs a reader.
"""

import dataclasses
import re
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

LICENCES = ("textual", "assumed", "world")
STATUSES = ("forbid", "permit", "oblige", "prefer")

#: The four relations above, plus the names the solver's own rules use. A module
#: may not redefine any of them as its own subject matter.
RESERVED = {"asserts", "beats", "defines", "closure", "silent", "because",
            "status", "violation", "fulfils", "live", "passage", "deontic",
            "opposite", "beats_tc", "a", "b"}
#: The document is encoded in one namespace and the BEHAVIOUR being judged
#: against it in another (`b_asserts`), deliberately kept apart. A single fact
#: that crosses them can make a real conflict disappear — satisfiably, with no
#: error — because it relates a clause to a behaviour as though they were two
#: clauses. A clause translation must never reach into the behaviour side.
BEHAVIOUR_NS = {"b_asserts", "b_beats", "seed"}

_PRED = re.compile(r"^[a-z][A-Za-z0-9_]*/\d+$")
#: A term: a lowercase functor with optional simple arguments — `produce(M)`,
#: `say_cannot_answer`. Narrow on purpose: a permissive pattern here accepts a
#: whole rule in a slot meant for a single term, which then bypasses every
#: check that applies to rules.
_TERM = re.compile(r"^[a-z][A-Za-z0-9_]*(\([A-Za-z0-9_, ()]*\))?$")
_ANON = re.compile(r"(?<![A-Za-z0-9_])_(?![A-Za-z0-9_])")
_CLAUSE_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
#: An ASP variable: an upper-case-initial token inside a term.
_VAR = re.compile(r"(?<![A-Za-z0-9_])[A-Z][A-Za-z0-9_]*")


def _check_term(term, where, allow_vars=True):
    """Validate and normalise a term: an act, an ontology atom, a defines slot.

    `allow_vars` is false where the term stands alone as a fact. A variable with
    nothing to bind it makes the solver reject the entire file, so one bad term
    takes every other clause in the link set down with it.
    """
    term = (term or "").strip()
    # `foo()` and `foo` are the SAME atom to the solver — it reads the first
    # back as the second — but two different strings to us. Anything comparing
    # act terms as text would then see one concept as two. Normalise here so
    # the two forms can never diverge downstream.
    if term.endswith("()"):
        term = term[:-2]
    if not _TERM.match(term):
        raise ValueError(
            f"{where}: {term!r} is not a term. It must be a functor like "
            f"produce(M) or say_cannot_answer — not a rule, not a sentence")
    if _ANON.search(term):
        raise ValueError(
            f"{where}: {term!r} contains an anonymous variable `_`. It is "
            f"ordinary ASP, but the tool that renders a rule back into English "
            f"cannot process it — and this slot is used both in the rule and "
            f"in the English annotation above it, so it breaks twice")
    if not allow_vars and _VAR.search(term):
        raise ValueError(
            f"{where}: {term!r} carries the variable "
            f"{_VAR.search(term).group()!r} and there are no conditions to bind "
            f"it. The solver refuses the WHOLE FILE for an unsafe variable, so "
            f"this would take every linked clause down with it — give it a "
            f"body, or write a term with no variables")
    return term
#: Characters that would break the quoted English annotation a rule carries, or
#: the line structure of the generated file. Rejected rather than escaped,
#: because these are prose fields and none of these characters belongs in a
#: sentence.
_BAD_IN_TEXT = re.compile(r'[\n\r"\\{}]')


def _strip_strings(asp):
    """Blank out quoted constants so a `_` inside one is not read as a variable."""
    return re.sub(r'"[^"]*"', '""', asp)


def _check_body(body, where):
    """Validate the conditions half of a rule — everything after `:-`."""
    if body is None:
        return
    if not body.strip():
        raise ValueError(f"{where}: body is present but empty — use null for "
                         f"an unconditional assertion")
    # Newlines only. Braces are legal here — aggregates like `#count{...}`,
    # pooling, choice bodies — and rejecting them would refuse correct ASP. They
    # ARE rejected in the English annotation (see `_BAD_IN_TEXT`), which is a
    # quoted string where a brace really does break the syntax.
    if "\n" in body or "\r" in body:
        raise ValueError(f"{where}: body contains a newline; it must be a "
                         f"single-line ASP conjunction")
    if body.strip().endswith("."):
        raise ValueError(f"{where}: body carries a trailing full stop; the "
                         f"renderer adds one")
    if _ANON.search(_strip_strings(body)):
        raise ValueError(
            f"{where}: anonymous variable `_`. It is ordinary ASP, but the "
            f"tool that renders a rule back into English cannot process it")
    for name in re.findall(r"(?<![A-Za-z0-9_])([a-z][A-Za-z0-9_]*)\s*\(", body):
        if name in BEHAVIOUR_NS:
            raise ValueError(
                f"{where}: uses `{name}`, which belongs to the encoding of the "
                f"BEHAVIOUR being judged, not of the document. A clause "
                f"translation is never shown a behaviour, and one fact that "
                f"crosses the two namespaces can silently erase a real conflict")


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Licensed(Strict):
    """Every fact records where it came from and how far it is licensed.

    A faithful translation often needs a fact the clause does not literally
    state. That is allowed; leaving it unmarked is not. Three licences:

        textual   the cited clause says this          -> `cites` required
        assumed   an inference the document supports  -> `inference` required
        world     knowledge from outside the document -> `toggleable` required

    ⚠️ The point is marking, not banning. Rejecting non-textual facts outright
    pushes an author to cite a plausible-looking clause instead, which creates
    an invented entity BEHIND a check that passed — strictly worse than an
    honest `assumed`.

    `world` facts are toggleable so a conclusion that depends on outside
    knowledge can be switched off and seen to disappear. A result that survives
    only because of one is a different claim from one the document supports.
    """

    licence: Literal["textual", "assumed", "world"]
    cites: Optional[str] = Field(
        description="clause id — REQUIRED and non-empty when textual")
    inference: Optional[str] = Field(
        description="the step named in one sentence — REQUIRED when assumed")
    toggleable: bool = Field(
        description="MUST be true when licence is world, else false")

    @model_validator(mode="after")
    def _licence_obligations(self):
        w = f"{type(self).__name__}"
        if self.licence == "textual" and not (self.cites or "").strip():
            raise ValueError(
                f"{w}: licence `textual` with no citation. Either cite the "
                f"clause that says it, or mark it `assumed` and name the "
                f"inference. A manufactured citation creates an invented "
                f"entity BEHIND a passed check")
        if self.licence == "assumed" and not (self.inference or "").strip():
            raise ValueError(
                f"{w}: licence `assumed` with no named inference — an unnamed "
                f"inference is an unmarked invention")
        if self.licence == "world" and not self.toggleable:
            raise ValueError(
                f"{w}: licence `world` but not toggleable. A result resting "
                f"on world knowledge is a different claim and must be "
                f"switchable off")
        if self.licence != "world" and self.toggleable:
            raise ValueError(f"{w}: toggleable is for `world` facts only")
        return self


class ReadBack(Strict):
    """The English sentence a reviewer reads INSTEAD of the rule.

    Review compares this sentence against the clause. If it is missing, the rule
    can only be checked by someone who reads ASP; if it is wrong, a correct rule
    is rejected and an incorrect one is approved. `%` marks where each variable
    is substituted when the sentence is rendered for a concrete case.
    """

    read_back: str = Field(
        description="one English sentence, with % where each argument is "
                    "substituted. No quotes, braces, backslashes or newlines")
    read_back_slots: list[str] = Field(
        description="ONE ENTRY PER `%` IN read_back, in order — the variable "
                    "each `%` is replaced by. EMPTY when read_back contains no "
                    "`%`. This is not the list of the rule's variables: a "
                    "read-back with no substitution point is a good read-back "
                    "and takes an empty list")

    @model_validator(mode="after")
    def _readback_ok(self):
        if not self.read_back.strip():
            raise ValueError(
                "no read-back annotation. The read-back is what a reviewer "
                "sees INSTEAD of the formal item; without it the item cannot "
                "be checked against the clause at all")
        if _BAD_IN_TEXT.search(self.read_back):
            raise ValueError(
                f"read_back {self.read_back!r} contains a newline, quote, "
                f"backslash or brace. It is interpolated into "
                f'%!trace_rule {{"..."}} and any of these produces a file '
                f"clingo cannot parse")
        if self.read_back.count("%") != len(self.read_back_slots):
            raise ValueError(
                f"read_back has {self.read_back.count('%')} `%` slot(s) but "
                f"{len(self.read_back_slots)} slot entr(ies) — the rendered "
                f"sentence would silently be wrong. A literal percent sign "
                f"cannot be written; say 'per cent'")
        return self


class Assertion(Licensed, ReadBack):
    """One deontic status attached to one act: `asserts(Clause, Status, Act)`.

    `body` holds the conditions under which it applies, or null if it always
    does. Where a clause gives distinct grounds for the same conclusion, each
    gets its own assertion with its own positive condition — deriving a verdict
    from the mere ABSENCE of something produces a right answer with a reason the
    program cannot support.
    """

    status: Literal["forbid", "permit", "oblige", "prefer"]
    act: str = Field(
        description="the ACT TERM, e.g. produce(M) or interject(user). Acts "
                    "are indexed: an act, never a material")
    body: Optional[str] = Field(
        description="the ASP conditions under which this assertion holds, one "
                    "line — or null when it holds unconditionally. Null, never "
                    "an empty string: an empty string is rejected")

    @model_validator(mode="after")
    def _assertion_ok(self):
        where = f"assertion {self.status}/{self.act!r}"
        self.act = _check_term(self.act, where, allow_vars=bool(self.body))
        _check_body(self.body, where)
        return self


class Superiority(Licensed, ReadBack):
    """One clause outranks another: `beats(Sayer, Winner, Loser)`.

    ⭐ It records WHO SAYS SO. A clause that states an override is itself the
    source of that override, and without the sayer there is no way to trace the
    ranking back to the text that established it.

    This is also what lets an exception live in its own file. Encoding one as a
    negated condition inside the general rule means every new exception edits
    the general clause's module — merging clauses instead of linking them.

    `body` is for a clause that ranks a whole CLASS of other clauses without
    naming its members; it binds `winner` or `loser` as a variable.
    """

    sayer: str = Field(
        description="the clause id asserting this superiority — normally this "
                    "module's own clause_id")
    winner: str = Field(description="clause id, or a variable bound by body")
    loser: str = Field(description="clause id, or a variable bound by body")
    body: Optional[str] = Field(
        description="conditions, when the clause ranks a whole CLASS of other "
                    "clauses without naming its members; else null")

    @model_validator(mode="after")
    def _sup_ok(self):
        where = f"beats({self.sayer}, {self.winner}, {self.loser})"
        for slot, val in (("sayer", self.sayer), ("winner", self.winner),
                          ("loser", self.loser)):
            if not _CLAUSE_ID.match(val.strip()):
                raise ValueError(f"{where}: `{slot}` is not a clause id or a "
                                 f"variable name")
        if self.winner == self.loser:
            raise ValueError(
                f"{where}: a clause cannot beat itself — the acyclicity guard "
                f"would reject the whole program")
        _check_body(self.body, where)
        return self


class Definition(Licensed):
    """What a class covers: `defines(Clause, Kind, Term)`.

    A definitional clause attaches no status. It fixes the extension that other
    clauses quantify over — "only sexual content involving minors is considered
    prohibited" defines what `prohibited` reaches, and some other clause is what
    forbids producing it.
    """

    kind: str = Field(description="the class being defined, e.g. prohibited")
    term: str = Field(description="the term brought under it, e.g. csam")

    @model_validator(mode="after")
    def _def_ok(self):
        self.kind = _check_term(self.kind, "defines `kind`", allow_vars=False)
        self.term = _check_term(self.term, "defines `term`", allow_vars=False)
        return self


class OntologyFact(Licensed):
    """A classification fact — this thing is of that kind. No deontic content.

    `restricted(new_bioweapon_step)`: it says what something IS, never what may
    or must be done about it.

    ⚠️ Kept in its own block, and switchable as a group, because measurement has
    shown the downstream results rest almost entirely on this layer rather than
    on the deontic one. Separating it is what makes that testable — mixing a
    status in here would make the two indistinguishable.

    Use this for an INSTANCE. To introduce a predicate and say what it means,
    use `Concept`, which asserts nothing.
    """

    atom: str = Field(
        description="e.g. restricted(new_bioweapon_step). NON-deontic")
    gloss: str = Field(
        description="one sentence saying what this PREDICATE means — not what "
                    "this particular instance of it asserts. For "
                    "`prohibited(csam)`, gloss `prohibited/1`, not the fact "
                    "about csam")
    body: Optional[str] = Field(
        description="ASP conditions, or null for a ground fact")

    @model_validator(mode="after")
    def _onto_ok(self):
        atom = self.atom = _check_term(self.atom, "ontology atom",
                           allow_vars=bool(self.body))
        if not self.gloss.strip():
            raise ValueError(
                f"ontology atom {atom!r} has no gloss. A symbol must resolve "
                f"to a concept with a WRITTEN MEANING, because review renders "
                f"the meaning rather than the name — otherwise a clause "
                f"pointing at the wrong concept produces a paraphrase that "
                f"reads perfectly well and nothing catches it")
        if _BAD_IN_TEXT.search(self.gloss):
            raise ValueError(f"ontology gloss for {atom!r} contains a quote, "
                             f"brace, backslash or newline")
        name = atom.split("(")[0]
        if name in RESERVED:
            raise ValueError(
                f"ontology atom {atom!r} uses `{name}`, which belongs to the "
                f"relation schema. This block holds classification only; a "
                f"deontic relation in it makes the two layers impossible to "
                f"tell apart, which is the whole reason they are separate")
        if name in BEHAVIOUR_NS:
            raise ValueError(
                f"ontology atom {atom!r} is in the behaviour namespace — it "
                f"names part of the BEHAVIOUR being judged, not part of the "
                f"document, and the two are kept apart on purpose")
        _check_body(self.body, f"ontology {atom!r}")
        return self


class Concept(Strict):
    """Introducing a predicate and saying what it means. Asserts nothing.

    *"The predicate `restricted/1` exists and means: the material falls under
    the restricted-content policy."* Distinct from `OntologyFact`, which asserts
    that some particular thing IS restricted.

    The distinction is not bookkeeping. A declaration written as a fact —
    `restricted(M)` with nothing to bind `M` — is one the solver refuses
    outright, so without this type the only expressible form is a broken one.

    ⚠️ These do NOT go into the logic file. Together they form the concept
    dictionary, emitted as its own table (see `concept_rows`). Burying
    definitions in comments inside logic files forces every later consumer — the
    English rendering, the vocabulary review, any cross-clause comparison — to
    parse ASP to recover them. Published legal ontologies have done exactly
    that, and the result is that you cannot ask which concepts derive from a
    given article without regex over prose.
    """

    name: str = Field(description="the predicate name, e.g. restricted")
    arity: int = Field(description="how many arguments it takes")
    gloss: str = Field(
        description="one sentence saying what the PREDICATE means — not what "
                    "any instance of it asserts. This sentence is the written "
                    "definition the concept table carries")

    @model_validator(mode="after")
    def _concept_ok(self):
        if not re.match(r"^[a-z][A-Za-z0-9_]*$", self.name or ""):
            raise ValueError(f"concept name {self.name!r} is not a predicate "
                             f"name")
        if self.name in RESERVED or self.name in BEHAVIOUR_NS:
            raise ValueError(
                f"concept {self.name!r} belongs to the relation schema or the "
                f"behaviour namespace and may not be redeclared")
        if not (self.gloss or "").strip():
            raise ValueError(
                f"concept {self.name!r} has no gloss. A symbol must resolve "
                f"to a concept with a WRITTEN MEANING, because review reads "
                f"that meaning rather than the name")
        if _BAD_IN_TEXT.search(self.gloss):
            raise ValueError(f"concept {self.name!r}: gloss contains a quote, "
                             f"brace, backslash or newline")
        if self.arity < 0:
            raise ValueError(f"concept {self.name!r}: negative arity")
        return self

    @property
    def sig(self):
        return f"{self.name}/{self.arity}"


class Concepts(Licensed, Concept):
    """A concept declaration, carrying its licence and citation like any fact."""


class Closure(Strict):
    """What the document's SILENCE about an act means. Required, not optional.

    If a clause says nothing about some act, does that permit it or forbid it?
    Written in plain logic the question never gets asked: the absence of a rule
    reads as "permitted", and nothing anywhere records that a choice was made.

        cepa      silence permits  — whatever is not forbidden is allowed
        cnpa      silence prohibits — whatever is not allowed is forbidden
        unclear   this clause does not settle it

    ⚠️ Required for EVERY act class a module governs, because measurement shows
    the downstream verdict flips depending on the answer, while the "no
    declaration" and "silence permits" cases are byte-identical in the output.
    An optional declaration is therefore the same as no declaration.

    Per act class rather than global: a document can be permissive about one
    kind of act and restrictive about another.
    """

    act_class: str = Field(
        description="the act functor this covers, e.g. produce or interject")
    closure: Literal["cepa", "cnpa", "unclear"] = Field(
        description="cepa = the document's silence PERMITS this act; "
                    "cnpa = its silence PROHIBITS it; "
                    "unclear = the clause does not settle it")
    reason: str = Field(
        description="one sentence, from the clause, for this reading")

    @model_validator(mode="after")
    def _closure_ok(self):
        self.act_class = _check_term(self.act_class, "closure act_class",
                                     allow_vars=False)
        if not self.reason.strip():
            raise ValueError(
                f"closure for {self.act_class!r} has no reason — an unreasoned "
                f"closure is the silent default this declaration exists to "
                f"replace")
        return self


class ForbidBody(Strict):
    """A claim about the RULES THEMSELVES, which no test case can exhibit.

    "Purpose never creates an exemption" is not about any situation — it says no
    rule of a certain shape may exist. There is nothing to test, because the
    claim is that a derivation never happens.

    Written instead as a constraint over facts nothing produces, such a rule is
    dead: it can never fire, the solver says so on every run, and it looks like
    an enforced claim while enforcing nothing. Declared here, it is checked by
    inspecting the program rather than by running it.
    """

    head: str = Field(description="the derived relation, e.g. permit")
    banned: str = Field(description="what may not appear in its body")

    @model_validator(mode="after")
    def _fb_ok(self):
        for slot, val in (("head", self.head), ("banned", self.banned)):
            if not re.match(r"^[a-z][A-Za-z0-9_]*$", (val or "").strip()):
                raise ValueError(f"forbid_body `{slot}` {val!r} is not a bare "
                                 f"predicate name")
        return self


class Module(Strict):
    """Everything one clause translates to — or a refusal to translate it.

    One clause, one module. Modules are combined by linking, never by copying
    text between them, so that each formal item stays traceable to the clause it
    came from and an amended clause changes exactly one file.

    ⚠️ `abstained` is a real answer, not a failure. A clause that cannot be
    translated faithfully — a heading, a goal with no trigger, an example —
    should be declined with a reason rather than turned into something that
    passes the checks. The rate at which that happens is a signal worth reading:
    without it, "we translated the document" cannot be told apart from "we
    translated the easy parts of it".
    """

    outcome: Literal["translated", "abstained"] = Field(
        description="`translated` if you wrote a module for this clause; "
                    "`abstained` if you declined to")
    clause_id: str = Field(description="the clause id you were given, exactly")
    abstain_reason: Optional[str] = Field(
        description="one sentence when abstaining; null when translating")
    claims: list[str] = Field(
        description="the clause's distinct claims, one string each")
    acts: list[str] = Field(
        description="every act term this clause governs, each declared once "
                    "here, e.g. [\"produce(M)\"]")
    concepts: list[Concepts] = Field(
        description="the predicates this clause INTRODUCES: name, arity, and "
                    "what each one MEANS. Asserts nothing")
    ontology: list[OntologyFact] = Field(
        description="the clause's non-deontic classification facts — what "
                    "something IS, never what may be done about it")
    asserts: list[Assertion] = Field(
        description="the deontic assertions: one status attached to one act")
    beats: list[Superiority] = Field(
        description="the superiority claims THIS clause states")
    defines: list[Definition] = Field(
        description="the extensions this clause fixes")
    closure: list[Closure] = Field(
        description="one entry per act class this module governs")
    requires: list[str] = Field(
        description="predicates another clause must define, as name/arity")
    inputs: list[str] = Field(
        description="facts about the CASE, supplied at query time, name/arity")
    forbid_body: list[ForbidBody] = Field(
        description="claims about the rule set that no situation can exhibit")

    @model_validator(mode="after")
    def _coherent(self):
        if self.outcome == "abstained":
            if not (self.abstain_reason or "").strip():
                raise ValueError(
                    "abstained with no reason — an abstention with no reason "
                    "is a skip in disguise, and the RATE of abstention is a "
                    "signal that only means something if each one is accounted")
            for name in ("claims", "acts", "concepts", "ontology", "asserts", "beats",
                         "defines", "closure", "requires", "inputs",
                         "forbid_body"):
                if getattr(self, name):
                    raise ValueError(
                        f"abstained but `{name}` is non-empty — an abstention "
                        f"with content in it is neither an abstention nor a "
                        f"translation")
            return self

        if not (self.asserts or self.defines or self.ontology or self.beats
                or self.concepts):
            raise ValueError(
                "translated but emitted no assertion, definition, superiority "
                "or ontology fact — that is an abstention that did not say so")
        if not self.claims:
            raise ValueError(
                "translated with no `claims` — a clause making four separate "
                "claims and tested against one case looks fully covered. "
                "Listing the claims is what makes that visible")

        for field in ("requires", "inputs"):
            for p in getattr(self, field):
                if not _PRED.match(p):
                    raise ValueError(
                        f"{field} entry {p!r} is not name/arity. Two "
                        f"predicates sharing a name but taking different "
                        f"numbers of arguments are different predicates; "
                        f"without the arity they link to each other silently")
        overlap = set(self.requires) & set(self.inputs)
        if overlap:
            raise ValueError(
                f"{sorted(overlap)} appear in BOTH `requires` and `inputs`. "
                f"`requires` means another clause must define it; `inputs` "
                f"means it is supplied with the case being judged. A predicate "
                f"cannot be both, and without the distinction 'a name nothing "
                f"defines' cannot be told from 'a name supplied at query time'")

        self.acts = [_check_term(a, "acts entry", allow_vars=True)
                     for a in self.acts]
        declared = set(self.acts)
        for asn in self.asserts:
            if asn.act.strip() not in declared:
                raise ValueError(
                    f"assertion names act {asn.act!r}, which is not in `acts`. "
                    f"Every act must be declared once so the closure "
                    f"declaration can be checked against it")

        # THE FORCED CLOSURE — every act class governed must carry one
        governed = {a.split("(")[0] for a in declared}
        covered = {c.act_class.strip() for c in self.closure}
        missing = sorted(governed - covered)
        if missing:
            raise ValueError(
                f"no default-closure declaration for act class(es) {missing}. "
                f"It is FORCED, not optional: an absent declaration reads as "
                f"'whatever is not forbidden is permitted', silently. That "
                f"reading changes what the corpus concludes, and it is "
                f"indistinguishable in the output from having decided nothing")
        extra = sorted(covered - governed)
        if extra:
            raise ValueError(
                f"closure declared for act class(es) {extra} the module does "
                f"not govern — a commitment about acts this clause is not "
                f"about")
        if len({c.act_class for c in self.closure}) != len(self.closure):
            raise ValueError("two closure declarations for one act class")

        # D4b level 1: every concept a body references must be DECLARED
        # somewhere in this module — its own ontology, `requires` (another
        # clause defines it) or `inputs` (a fact about the case). Only whether
        # the declaration finds a PROVIDER corpus-wide is link scope
        # Whether it also finds a DEFINITION somewhere in the corpus is a
        # question for link time, once enough clauses exist to answer it.
        # ⛔ Concepts are NOT a declaration site. A concept says what a
        # predicate MEANS; it does not say that anything DEFINES it — no fact,
        # no rule, no other clause. A rule resting only on concept
        # declarations can never fire, and counting them here made that pass
        # with zero errors. Three sites: this module's ontology, `requires`
        # (another clause defines it) or `inputs` (supplied with the case).
        declared = {f.atom.split("(")[0] for f in self.ontology}
        known = declared | {p.split("/")[0] for p in self.requires + self.inputs}
        for item in (*self.asserts, *self.beats, *self.ontology):
            body = getattr(item, "body", None) or ""
            for name in re.findall(
                    r"(?<![A-Za-z0-9_])([a-z][A-Za-z0-9_]*)\s*\(", body):
                if name not in known and name not in RESERVED:
                    raise ValueError(
                        f"body references `{name}` but nothing declares it. "
                        f"Put it in this module's `ontology`, in `requires` "
                        f"(another clause defines it), or in `inputs` (a fact "
                        f"about the case). An undeclared name cannot be told "
                        f"apart from a typo")

        # Note there is deliberately NO check that a declared concept is used
        # somewhere in its own module. Introducing vocabulary it does not itself
        # use is exactly what a definitional clause does — "Assistant: the
        # entity the user interacts with. (The term agent is sometimes used
        # ...)" introduces two terms and defines one. Whether a concept is dead
        # is a question about the whole corpus, not about one clause.

        for b in self.beats:
            if b.sayer != self.clause_id and not b.body:
                raise ValueError(
                    f"beats sayer {b.sayer!r} is not this clause and no body "
                    f"binds it — a module may only record superiority its own "
                    f"clause states")
        return self


# ==========================================================================
#  The wire schema
# ==========================================================================

def json_schema():
    """`Module.model_json_schema()`, flattened for structured-output mode.

    pydantic emits three things providers reject or mishandle:
      * `$defs` + `$ref` — inlined; several providers do not resolve them
      * `Optional[X]` as `anyOf` — rewritten to a nullable type, keeping the
        whole surviving branch. Keeping only its `type` would silently drop
        `items` from an optional list, and collapse an optional nested object
        to a bare string
      * no `additionalProperties` — forced false at every object level, so an
        invented extra field is a rejection rather than silent noise
    """
    raw = Module.model_json_schema()
    defs = raw.pop("$defs", {})

    def inline(node, seen=()):
        if isinstance(node, list):
            return [inline(x, seen) for x in node]
        if not isinstance(node, dict):
            return node
        if "$ref" in node:
            name = node["$ref"].rsplit("/", 1)[-1]
            if name in seen:
                raise ValueError(
                    f"recursive $ref to {name!r}: a strict wire schema cannot "
                    f"express it, and inlining would not terminate")
            merged = {k: v for k, v in node.items() if k != "$ref"}
            return inline({**defs[name], **merged}, seen + (name,))

        if _nullable(node.get("anyOf")):
            base = next(x for x in node["anyOf"] if x.get("type") != "null")
            rest = {k: v for k, v in node.items() if k != "anyOf"}
            out = inline({**base, **rest}, seen)          # keep the WHOLE body
            out["type"] = [base.get("type", "string"), "null"]
        else:
            out = {k: inline(v, seen) for k, v in node.items()}

        t = out.get("type")
        if t == "object" or (isinstance(t, list) and "object" in t):
            out["additionalProperties"] = False
            if "properties" in out:
                out["required"] = list(out["properties"])
        return out

    return inline(raw)


def _nullable(any_of):
    return (isinstance(any_of, list) and len(any_of) == 2
            and any(x.get("type") == "null" for x in any_of))


def response_format(strict=True):
    """together.ai's documented shape: {type, json_schema: {name, schema}}."""
    js = {"name": "clause_module", "schema": json_schema()}
    if strict:
        js["strict"] = True
    return {"type": "json_schema", "json_schema": js}


class ModuleValidationError(RuntimeError):
    """A returned object the shape accepted and the contract does not."""


def validate(obj, clause_id=None, known_clause_ids=None):
    """dict -> Module. Raises ModuleValidationError on any breach.

    `clause_id` and `known_clause_ids`, when given, close two holes a schema
    cannot: a module that renames itself, and a citation to a clause that does
    not exist. Without the second, a fact can carry a citation that looks
    perfectly well-formed and points at nothing.
    """
    from pydantic import ValidationError
    try:
        mod = Module.model_validate(obj)
    except ValidationError as exc:
        parts = []
        for err in exc.errors():
            loc = ".".join(str(x) for x in err["loc"]) or "<root>"
            parts.append(f"{loc}: {err['msg']}")
        raise ModuleValidationError("; ".join(parts)) from exc

    if clause_id is not None and mod.clause_id != clause_id:
        raise ModuleValidationError(
            f"module says clause_id {mod.clause_id!r} but it was asked to "
            f"translate {clause_id!r}. The artifact would carry two identities")
    if known_clause_ids is not None:
        for item in (*mod.asserts, *mod.beats, *mod.defines, *mod.ontology):
            if item.licence == "textual" and item.cites not in known_clause_ids:
                raise ModuleValidationError(
                    f"cites {item.cites!r}, which is not a clause in this "
                    f"corpus. A manufactured citation creates an invented "
                    f"entity behind a passed check")
        for b in mod.beats:
            for slot in ("sayer", "winner", "loser"):
                val = getattr(b, slot)
                if not b.body and val not in known_clause_ids:
                    raise ModuleValidationError(
                        f"beats {slot} {val!r} is not a clause in this corpus "
                        f"and no body binds it as a variable")
    return mod


# ==========================================================================
#  The COLLECTING path — every breach in one call
# ==========================================================================
#
# ⭐ WHY THIS EXISTS AND WHY IT IS SEPARATE FROM `validate()`.
#
# `validate()` raises on the first breach. That decides the COST OF REPAIR: a
# module with three read-back breaches and a fabricated citation is four paid
# model round-trips at one-breach-per-call, and one round-trip if the whole set
# comes back together. Stage 2's repair loop needs the whole set.
#
# `validate()` is nonetheless left byte-for-byte as it was. Two reasons, both
# concrete: a lot of code calls it and expects the raise, and every one of its
# `raise` sites is a MUTATION ANCHOR located by a phrase from its own source
# (`mutate_schema.py`), so lifting a message out of a raise into a shared helper
# would break the coupling — loudly, but for no gain.
#
# ⚠️ THE CONSEQUENCE, STATED RATHER THAN HIDDEN: the corpus and identity checks
# below are a SECOND COPY of the ones inside `validate()`. Two copies of a rule
# drift. `test_schema.py::test_validate_all_and_validate_agree_on_what_is_a_breach`
# is what holds them together — anything `validate()` rejects for a named reason,
# this must report for the same named reason.


@dataclasses.dataclass(frozen=True)
class Breach:
    """One contract breach, located.

    ⛔ CARRIES NO SUGGESTED FIX AND NO EXPECTED VALUE, under the same denial as
    `link.Finding`: these feed a stage-2 repair prompt and stage 1 is denied the
    expected verdicts. A breach says WHAT IS THE CASE and WHERE.
    """

    where: str      #: `asserts[0]`, `concepts[2].gloss`, or `<root>`
    message: str    #: the guard's own sentence, no fix in it


def _where(loc):
    """A pydantic error location as a path a repair prompt can point at.

    `('asserts', 0, 'status')` -> `asserts[0].status`; `()` -> `<root>`. List
    indices are bracketed rather than dotted so `asserts.0` — which reads as a
    field named `0` — never appears in a prompt.
    """
    out = ""
    for part in loc:
        if isinstance(part, int):
            out += f"[{part}]"
        else:
            out = f"{out}.{part}" if out else str(part)
    return out or "<root>"


def _msg(err):
    """pydantic prefixes a validator's own sentence with `Value error, `."""
    m = err["msg"]
    return m[len("Value error, "):] if m.startswith("Value error, ") else m


def validate_all(obj, clause_id=None, known_clause_ids=None):
    """dict -> `(Module | None, list[Breach])`. Collects; never raises.

    The module is `None` only when the object could not be CONSTRUCTED. When it
    constructed but breached a corpus or identity rule, the module is returned
    ALONGSIDE its breaches — the caller still has to render the `.lp` to run the
    link checks, and withholding it would put stage 2 back behind stage 1.

    ⚠️ TWO PLACES WHERE BREACHES ARE STILL SERIALISED, named because a collector
    that silently under-reports is worse than one that admits its scope:

    * **Within one sub-model instance, only the first failing validator is
      reported.** `Assertion` runs `_licence_obligations`, `_readback_ok` and
      `_assertion_ok` in sequence and pydantic stops the chain at the first
      raise. Across instances there is no such limit — three bad assertions
      report three breaches, and so do a bad assertion, a bad concept and a bad
      ontology fact.
    * **`Module._coherent` runs only once every sub-model has validated.** It is
      an `after` validator on the constructed model, so there is nothing for it
      to read until then. Running its guards over half-validated values instead
      was considered and REJECTED: the values it reads are exactly the ones
      still unnormalised at that point (`produce()` has not yet become
      `produce`), so it would emit breaches that are not true of the object the
      model actually sent. A fabricated finding in a repair log is worse than a
      missing one — it spends a paid call chasing a defect that is not there.
    """
    from pydantic import ValidationError
    try:
        mod = Module.model_validate(obj)
    except ValidationError as exc:
        return None, [Breach(_where(err["loc"]), _msg(err))
                      for err in exc.errors()]

    breaches = []
    if clause_id is not None and mod.clause_id != clause_id:
        breaches.append(Breach(
            "<root>",
            f"module says clause_id {mod.clause_id!r} but it was asked to "
            f"translate {clause_id!r}. The artifact would carry two identities"))
    if known_clause_ids is not None:
        for field in ("asserts", "beats", "defines", "ontology"):
            for i, item in enumerate(getattr(mod, field)):
                if item.licence == "textual" and item.cites not in known_clause_ids:
                    breaches.append(Breach(
                        f"{field}[{i}]",
                        f"cites {item.cites!r}, which is not a clause in this "
                        f"corpus. A manufactured citation creates an invented "
                        f"entity behind a passed check"))
        for i, b in enumerate(mod.beats):
            for slot in ("sayer", "winner", "loser"):
                val = getattr(b, slot)
                if not b.body and val not in known_clause_ids:
                    breaches.append(Breach(
                        f"beats[{i}]",
                        f"beats {slot} {val!r} is not a clause in this corpus "
                        f"and no body binds it as a variable"))
    return mod, breaches


# ==========================================================================
#  Rendering
# ==========================================================================

def _line(item, text):
    """A rendered line, with its licence and source in a trailing comment."""
    note = ({"textual": f"[T] {item.cites}",
             "assumed": f"[A] {item.inference}",
             "world": "[W] toggleable"})[item.licence]
    return f"{text}   % {note}"


def concept_rows(mod: Module) -> list:
    """The concept dictionary as rows. One per concept, joinable across clauses.

    This is the artifact, not the `.lp`. DPV's practice, adopted in
    A table is the source of record and everything else is generated from it,
    so the vocabulary can be diffed, reviewed and joined across clauses without
    parsing any logic.
    """
    return [dict(concept=c.sig, clause_id=mod.clause_id, gloss=c.gloss,
                 licence=c.licence, cites=c.cites, inference=c.inference)
            for c in mod.concepts]


def render_lp(mod: Module, clause: dict) -> str:
    """Render the `.lp`. Deterministic: same object, same bytes."""
    out = [f"%% clause: {mod.clause_id}   "
           f"section: {clause.get('section_id', '')}   "
           f"kind: {clause.get('kind', '')}"]

    if mod.outcome == "abstained":
        out.append(f"%% ABSTAIN: {mod.abstain_reason}")
        return "\n".join(out) + "\n"

    out.append(f"%% acts: {', '.join(mod.acts)}")
    # A POINTER, never the content — see concept_rows().
    if mod.concepts:
        out.append(f"%% concepts: {', '.join(c.sig for c in mod.concepts)}"
                   f"   (glosses in the concept table, not here)")
    out.append(f"%% requires: {', '.join(mod.requires)}")
    out.append(f"%% inputs: {', '.join(mod.inputs)}")
    for c in mod.closure:
        out.append(f"%% closure: {c.act_class} = {c.closure}   % {c.reason}")
    for fb in mod.forbid_body:
        out.append(f"%% forbid-body: {fb.head} <- {fb.banned}")

    out.append("% " + "=" * 68)
    out.append("% GENERATED by phase_1/translate.py — not hand-written.")
    for i, line in enumerate(_wrap(clause.get("quote", ""), 66)):
        out.append(f"% SOURCE: {line}" if i == 0 else f"%         {line}")
    out.append("%")
    out.append("% CLAIMS:")
    for c in mod.claims:
        for j, line in enumerate(_wrap(c, 64)):
            out.append(f"%   {line}" if j == 0 else f"%     {line}")
    out.append("% " + "=" * 68)

    # Acts are DECLARED, not asserted. `act(produce(M)).` with an unbound
    # variable is unsafe and clingo refuses the whole file — found by running
    # it. Ground act facts belong to the case (see `inputs`), not to a clause
    # module: which acts actually exist belongs to the case being judged.
    # The declaration is a header so the forced-closure check has something to
    # check against and a reviewer can see the clause's scope.

    if mod.ontology:
        out += ["",
                "% ---- ontology: NON-deontic classification ----",
                "% Guarded so the ablation in deontic_probe/FINDINGS.md §4.6",
                "% can be re-run against this corpus.",
                "#const onto = on.",
                "o :- onto = on."]
        for f in mod.ontology:
            head = f"{f.atom} :- o" if not f.body else f"{f.atom} :- o, {f.body}"
            out.append(_line(f, head + "."))

    if mod.defines:
        out += ["", "% ---- definitions ----"]
        for d in mod.defines:
            out.append(_line(d, f"defines({mod.clause_id}, {d.kind}, {d.term})."))

    if mod.asserts:
        out += ["", "% ---- deontic assertions ----"]
        for a in mod.asserts:
            args = ", ".join(a.read_back_slots)
            out.append(f'%!trace_rule {{"{a.read_back}"'
                       + (f", {args}}}." if args else "}."))
            head = f"asserts({mod.clause_id}, {a.status}, {a.act})"
            out.append(_line(a, head + (f" :- {a.body}." if a.body else ".")))

    if mod.beats:
        out += ["", "% ---- superiority ----"]
        for b in mod.beats:
            args = ", ".join(b.read_back_slots)
            out.append(f'%!trace_rule {{"{b.read_back}"'
                       + (f", {args}}}." if args else "}."))
            head = f"beats({b.sayer}, {b.winner}, {b.loser})"
            out.append(_line(b, head + (f" :- {b.body}." if b.body else ".")))

    out += ["", "%!show_trace {asserts(P,D,A)}.",
            "%!show_trace {beats(S,W,L)}."]
    return "\n".join(out).rstrip() + "\n"


def _wrap(text, width):
    words, line, lines = (text or "").split(), "", []
    for w in words:
        if line and len(line) + len(w) + 1 > width:
            lines.append(line)
            line = w
        else:
            line = f"{line} {w}".strip()
    if line:
        lines.append(line)
    return lines or [""]
