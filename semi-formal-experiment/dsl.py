"""Data model for the semi-formal spec representation.

Three object kinds, all JSON-serializable:
  Atom    — typed primitive; exists iff a clause conditions on it (quote spans)
  Axiom   — static composability rule with a license label
  Rule    — defeasible norm from a conditional clause
plus DerivedPredicate (a behavior definition composed from atoms) and the
Vocabulary container that the checker validates against.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict

ATOM_KINDS = ("context", "act")
DIMENSIONS = ("principal", "act", "epistemic", "situation", "deontic")
AXIOM_LICENSES = ("logical", "textual", "assumed")
AXIOM_KINDS = ("incompat", "excludes", "requires", "at_most_one")
MODALITIES = ("oblige", "forbid", "permit")
STATUSES = ("validated", "draft")


@dataclass
class Atom:
    name: str
    kind: str                      # context | act
    dimension: str                 # principal | act | epistemic | situation | deontic
    gloss: str = ""
    quote_spans: list = field(default_factory=list)   # [{"locator":..., "quote":...}]
    status: str = "draft"

    def validate(self):
        errs = []
        if self.kind not in ATOM_KINDS:
            errs.append(f"atom {self.name}: bad kind {self.kind!r}")
        if self.dimension not in DIMENSIONS:
            errs.append(f"atom {self.name}: bad dimension {self.dimension!r}")
        if self.status not in STATUSES:
            errs.append(f"atom {self.name}: bad status {self.status!r}")
        return errs


@dataclass
class Axiom:
    kind: str                      # incompat | excludes | requires | at_most_one
    atoms: list                    # atom names involved
    license: str                   # logical | textual | assumed
    source: str = ""               # locator/quote for textual; rationale otherwise
    status: str = "draft"

    def validate(self, atom_names):
        errs = []
        if self.kind not in AXIOM_KINDS:
            errs.append(f"axiom {self.kind}({self.atoms}): bad kind")
        if self.license not in AXIOM_LICENSES:
            errs.append(f"axiom {self.kind}({self.atoms}): bad license {self.license!r}")
        if self.license == "textual" and not self.source:
            errs.append(f"axiom {self.kind}({self.atoms}): textual license requires source")
        for a in self.atoms:
            if a not in atom_names:
                errs.append(f"axiom {self.kind}({self.atoms}): unknown atom {a!r}")
        if self.kind in ("incompat", "requires") and len(self.atoms) != 2:
            errs.append(f"axiom {self.kind}({self.atoms}): needs exactly 2 atoms")
        return errs


@dataclass
class Rule:
    id: str
    modality: str                  # oblige | forbid | permit
    act: str                       # act atom name
    conditions: list               # context atom names (conjunctive trigger)
    defeaters: list = field(default_factory=list)  # [{"conditions":[...], "source": ...}]
    tier: int = 4
    locator: str = ""
    quote: str = ""
    status: str = "draft"

    def validate(self, vocab: "Vocabulary"):
        errs = []
        if self.modality not in MODALITIES:
            errs.append(f"rule {self.id}: bad modality {self.modality!r}")
        act = vocab.atom(self.act)
        if act is None:
            errs.append(f"rule {self.id}: unknown act {self.act!r}")
        elif act.kind != "act":
            errs.append(f"rule {self.id}: {self.act!r} is not an act atom")
        for c in self.conditions:
            ca = vocab.atom(c)
            if ca is None:
                errs.append(f"rule {self.id}: unknown condition atom {c!r}")
            elif ca.kind != "context":
                errs.append(f"rule {self.id}: condition {c!r} is not a context atom")
        for d in self.defeaters:
            for c in d.get("conditions", []):
                if vocab.atom(c) is None:
                    errs.append(f"rule {self.id}: unknown defeater atom {c!r}")
        if not self.quote or not self.locator:
            errs.append(f"rule {self.id}: missing provenance (locator+quote required)")
        return errs


@dataclass
class DerivedPredicate:
    """A behavior definition: an expression over atom names.

    Expression grammar (JSON): atom name (str), or {"all": [expr...]},
    {"any": [expr...]}, {"not": expr}.
    """
    name: str
    expr: object
    concept_map: dict = field(default_factory=dict)  # concept -> atom name or None (unmapped)
    status: str = "draft"

    def atoms_used(self):
        out = []
        def walk(e):
            if isinstance(e, str):
                out.append(e)
            elif isinstance(e, dict):
                for k, v in e.items():
                    if k in ("all", "any"):
                        for x in v:
                            walk(x)
                    elif k == "not":
                        walk(v)
        walk(self.expr)
        return out


class Vocabulary:
    def __init__(self, atoms=None, axioms=None, spec="unspecified"):
        self.spec = spec
        self.atoms = {a.name: a for a in (atoms or [])}
        self.axioms = list(axioms or [])

    def atom(self, name):
        return self.atoms.get(name)

    def validate(self):
        errs = []
        for a in self.atoms.values():
            errs.extend(a.validate())
        for ax in self.axioms:
            errs.extend(ax.validate(set(self.atoms)))
        return errs

    # ---- serialization ----
    def to_dict(self):
        return {
            "spec": self.spec,
            "atoms": [asdict(a) for a in self.atoms.values()],
            "axioms": [asdict(ax) for ax in self.axioms],
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            atoms=[Atom(**a) for a in d.get("atoms", [])],
            axioms=[Axiom(**ax) for ax in d.get("axioms", [])],
            spec=d.get("spec", "unspecified"),
        )

    def save(self, path):
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=1)

    @classmethod
    def load(cls, path):
        with open(path) as f:
            return cls.from_dict(json.load(f))
