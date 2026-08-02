"""`extraction.json` -> ASP (`.lp`) + conflict enumeration -> `conflicts.json`.

The emitted program reproduces the structure of `rules.lp` (which
`run_conflicts.py` reads unmodified):

  * a choice rule `{ ctx(A) }.` per unconstrained context atom, and, for each
    `at_most_one` exclusion, a bounded choice group `{ ctx(a); ctx(b) } 1.`
    covering its atoms instead; `excludes` becomes `:- ctx(a), ctx(b).`
    Without these the scenario space admits impossible situations and
    witnesses become ARTIFACTs (contract §3).
  * `active(Id, Modality, Act, 1) :- ctx(...), not defeated(Id).`
    Tier is always 1 — the chain-of-command section is uniformly root
    authority, so every conflict it produces is same-tier.
  * `defeated(Id) :- ctx(...).` per defeater
  * `incompat/2` facts from the extraction's `incompat` list
  * the conflict-detection scaffolding, the `has_conflict` constraint and the
    `#show` directives, verbatim in shape from `rules.lp`
  * `source/2` and `locator/4` provenance facts, which appear in NO rule body
    or head and therefore cannot affect derivation (asserted in
    `test_emit_asp.py::test_provenance_is_inert`).

CLI:  python emit_asp.py extraction.json --lp out.lp --out conflicts.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
from collections import defaultdict

import clingo

HERE = os.path.dirname(os.path.abspath(__file__))

ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")
MODALITIES = ("oblige", "forbid", "permit")
AXIOM_LICENSES = ("logical", "textual", "assumed")
EXCLUSION_KINDS = ("at_most_one", "excludes")
TIER = 1  # uniformly root authority; see contract §2

PROVENANCE_PREDICATES = ("source", "locator")

# An extraction with no incompat facts (or no defeaters) leaves those atoms
# undefined, which clingo reports as an info message. Validation already
# rejects undeclared atoms, so the diagnostic is pure noise here.
_NO_UNDEF = "--warn=no-atom-undefined"


class EmitError(ValueError):
    """Malformed extraction — raised instead of emitting broken ASP.

    Carries `reason_class`: a normalized, id-free label used to aggregate
    `rejection_reasons` counts. `str(err)` keeps the full specific message.
    """

    def __init__(self, message, reason_class=None):
        super().__init__(message)
        self.reason_class = reason_class or "other"


# ---------------------------------------------------------------- helpers ---

def _qstr(s: str) -> str:
    """An ASP double-quoted string constant."""
    s = "" if s is None else str(s)
    s = s.replace("\\", "\\\\").replace('"', '\\"')
    s = s.replace("\n", " ").replace("\r", " ")
    return '"' + s + '"'


def _check_const(name, what, rule_id=None):
    where = f"rule {rule_id}: " if rule_id else ""
    if not isinstance(name, str) or not ID_RE.match(name):
        raise EmitError(
            f"{where}{what} {name!r} is not a legal ASP constant "
            f"(must match ^[a-z][a-z0-9_]*$)",
            f"{what} is not a legal ASP constant",
        )


def _section_of(locator: str) -> str:
    """Human-readable source section, mirroring rules.lp's `source/2`:
    the locator minus the spec-version prefix and the ` > L<line>` suffix."""
    if not locator:
        return ""
    s = locator.split(" > ", 1)[-1] if " > " in locator else locator
    # drop the trailing "> L<line>" and inventory's unique "[fa_xxxx]" suffix
    return re.sub(r" > L\d+(?: \[[^\]]+\])?$", "", s)


def _clause_id(rule_id: str) -> str:
    return rule_id[3:] if rule_id.startswith("fa_") else rule_id


# ------------------------------------------------------------- validation ---
# Each item is validated independently and raises on its own defect, so the
# caller can either abort (default, fail-fast) or skip-and-record
# (`skip_invalid=True`) without any change to the messages produced.

def _validate_atom(a, seen):
    if not isinstance(a, dict) or "name" not in a:
        raise EmitError(f"atom {a!r} has no name", "atom has no name")
    _check_const(a["name"], "atom name")
    if a.get("kind") not in ("context", "act"):
        raise EmitError(
            f"atom {a['name']}: bad kind {a.get('kind')!r}", "atom has a bad kind"
        )
    if a["name"] in seen:
        raise EmitError(f"duplicate atom {a['name']!r}", "duplicate atom")


def _validate_rule(r, atoms, seen):
    if not isinstance(r, dict) or "id" not in r:
        raise EmitError(f"rule {r!r} has no id", "rule has no id")
    rid = r["id"]
    _check_const(rid, "rule id")
    if rid in seen:
        raise EmitError(f"duplicate rule id {rid!r}", "duplicate rule id")

    def need(name, kind):
        _check_const(name, f"{kind} atom", rid)
        if name not in atoms:
            raise EmitError(
                f"rule {rid}: undeclared atom {name!r}", "rule references an undeclared atom"
            )
        if atoms[name].get("kind") != kind:
            raise EmitError(
                f"rule {rid}: {name!r} is a {atoms[name].get('kind')!r} atom, "
                f"expected {kind!r}",
                f"rule uses a non-{kind} atom where "
                f"{'an' if kind[0] in 'aeiou' else 'a'} {kind} atom is required",
            )

    if r.get("modality") not in MODALITIES:
        raise EmitError(
            f"rule {rid}: bad modality {r.get('modality')!r}", "rule has a bad modality"
        )
    if "act" not in r:
        raise EmitError(f"rule {rid}: missing act", "rule has no act")
    need(r["act"], "act")
    for c in r.get("conditions") or []:
        need(c, "context")
    for d in r.get("defeaters") or []:
        if not isinstance(d, dict):
            raise EmitError(
                f"rule {rid}: defeater {d!r} is not an object", "malformed defeater"
            )
        conds = d.get("conditions") or []
        if not conds:
            raise EmitError(
                f"rule {rid}: defeater with no conditions", "defeater with no conditions"
            )
        for c in conds:
            need(c, "context")
    tier = r.get("tier", TIER)
    if tier != TIER:
        raise EmitError(
            f"rule {rid}: tier must be {TIER} (section is uniformly root "
            f"authority), got {tier!r}",
            "rule has a non-root tier",
        )


def _validate_incompat(ax, atoms):
    acts = ax.get("acts") if isinstance(ax, dict) else None
    if not isinstance(acts, list) or len(acts) != 2:
        raise EmitError(f"incompat {ax!r}: needs exactly 2 acts", "incompat arity")
    for a in acts:
        _check_const(a, "incompat act")
        if a not in atoms:
            raise EmitError(
                f"incompat {acts}: undeclared atom {a!r}",
                "incompat references an undeclared atom",
            )
        if atoms[a].get("kind") != "act":
            raise EmitError(
                f"incompat {acts}: {a!r} is not an act atom",
                "incompat names a non-act atom",
            )
    if ax.get("license") not in AXIOM_LICENSES:
        raise EmitError(
            f"incompat {acts}: bad license {ax.get('license')!r}", "incompat bad license"
        )
    if ax["license"] == "textual" and not ax.get("source"):
        raise EmitError(
            f"incompat {acts}: textual license requires a source",
            "textual license without a source",
        )


def _validate_exclusion(ex, atoms, group_of, all_exclusions):
    names = ex.get("atoms") if isinstance(ex, dict) else None
    kind = ex.get("kind") if isinstance(ex, dict) else None
    if kind not in EXCLUSION_KINDS:
        raise EmitError(f"exclusion {ex!r}: bad kind {kind!r}", "exclusion bad kind")
    if not isinstance(names, list):
        raise EmitError(f"exclusion {ex!r}: atoms must be a list", "exclusion malformed")
    if kind == "excludes" and len(names) != 2:
        raise EmitError(
            f"exclusion {names}: 'excludes' needs exactly 2 atoms, got {len(names)}",
            "exclusion arity",
        )
    if kind == "at_most_one" and len(names) < 2:
        raise EmitError(
            f"exclusion {names}: 'at_most_one' needs at least 2 atoms, got {len(names)}",
            "exclusion arity",
        )
    if len(set(names)) != len(names):
        raise EmitError(f"exclusion {names}: repeats an atom", "exclusion repeats an atom")
    for n in names:
        _check_const(n, "exclusion atom")
        if n not in atoms:
            raise EmitError(
                f"exclusion {names}: undeclared atom {n!r}",
                "exclusion references an undeclared atom",
            )
        if atoms[n].get("kind") != "context":
            raise EmitError(
                f"exclusion {names}: {n!r} is not a context atom "
                f"(exclusions constrain context atoms; use incompat for acts)",
                "exclusion names a non-context atom",
            )
    if ex.get("license") not in AXIOM_LICENSES:
        raise EmitError(
            f"exclusion {names}: bad license {ex.get('license')!r}", "exclusion bad license"
        )
    if ex["license"] == "textual" and not ex.get("source"):
        raise EmitError(
            f"exclusion {names}: textual license requires a source",
            "textual license without a source",
        )
    if kind == "at_most_one":
        for n in names:
            if n in group_of:
                raise EmitError(
                    f"exclusion {names}: atom {n!r} already belongs to another "
                    f"at_most_one group {all_exclusions[group_of[n]]['atoms']}",
                    "atom in more than one at_most_one group",
                )


def validate(extraction: dict, skip_invalid: bool = False) -> dict:
    """Structural + identifier validation; returns an index of the extraction.

    Default is fail-fast: the first defect raises `EmitError`. With
    `skip_invalid=True` a defective item is excluded and recorded in
    `idx["rejected"]` instead, and items that depended on it are cascaded out
    (counted separately) so the emitted program never references something that
    was removed. Counts land in `idx["provenance"]`.
    """
    rejected = []

    def reject(kind, ident, err, cascade=False):
        rejected.append({
            "kind": kind,
            "id": ident,
            "reason": str(err),
            "reason_class": (
                err.reason_class if isinstance(err, EmitError) else str(err)
            ),
            "cascade": cascade,
        })

    def guard(kind, ident, fn):
        """Run a validator; return True if the item survives."""
        try:
            fn()
            return True
        except EmitError as e:
            if not skip_invalid:
                raise
            reject(kind, ident, e)
            return False

    # These are whole-document defects: there is nothing left to skip *to*, so
    # they abort in both modes.
    if not isinstance(extraction, dict):
        raise EmitError("extraction must be a JSON object", "extraction malformed")
    for key in ("atoms", "rules"):
        if not isinstance(extraction.get(key), list):
            raise EmitError(f"extraction.{key} must be a list", "extraction malformed")
    # `exclusions` is mandatory: silently defaulting a missing field to []
    # reproduces exactly the scenario-space bug the field was added to close
    # (witnesses that describe impossible situations).
    if "exclusions" not in extraction:
        raise EmitError(
            "extraction.exclusions is mandatory (may be an empty list); "
            "without it every context atom gets an independent choice rule "
            "and witnesses may describe impossible situations",
            "extraction malformed",
        )
    if not isinstance(extraction["exclusions"], list):
        raise EmitError("extraction.exclusions must be a list", "extraction malformed")

    # ---- atoms ----
    atoms = {}
    for a in extraction["atoms"]:
        ident = a.get("name") if isinstance(a, dict) else repr(a)
        if guard("atom", ident, lambda a=a: _validate_atom(a, atoms)):
            atoms[a["name"]] = a

    # ---- rules ----
    rules = {}
    for r in extraction["rules"]:
        ident = r.get("id") if isinstance(r, dict) else repr(r)
        if guard("rule", ident, lambda r=r: _validate_rule(r, atoms, rules)):
            rules[r["id"]] = r

    # ---- cascade: atoms orphaned *by a dropped rule* ----
    # An atom that no surviving rule uses cannot affect derivation. Only atoms
    # that a rejected rule referenced are cascaded out, so the flag is a strict
    # no-op on a clean extraction: an atom that was already unused before any
    # rejection is pre-existing extraction noise, is equally inert, and is left
    # alone rather than being silently re-scoped by an unrelated flag.
    def _atoms_of(r):
        got = set()
        if not isinstance(r, dict):
            return got
        if isinstance(r.get("act"), str):
            got.add(r["act"])
        got.update(c for c in (r.get("conditions") or []) if isinstance(c, str))
        for d in r.get("defeaters") or []:
            if isinstance(d, dict):
                got.update(c for c in (d.get("conditions") or []) if isinstance(c, str))
        return got

    used = set().union(*(_atoms_of(r) for r in rules.values())) if rules else set()
    dropped_rule_ids = {r["id"] for r in rejected if r["kind"] == "rule"}
    touched_by_dropped = set().union(
        *(_atoms_of(r) for r in extraction["rules"]
          if isinstance(r, dict) and r.get("id") in dropped_rule_ids)
    ) if dropped_rule_ids else set()

    # Axioms are validated against the atoms as *declared*, so an axiom over an
    # orphaned atom is reported as a cascade drop rather than as "undeclared".
    declared = dict(atoms)
    if skip_invalid:
        for name in [n for n in atoms if n not in used and n in touched_by_dropped]:
            reject(
                "atom", name,
                EmitError(
                    f"atom {name!r}: orphaned — used only by rejected rule(s), "
                    f"no surviving rule references it",
                    "atom orphaned by a dropped rule",
                ),
                cascade=True,
            )
            del atoms[name]

    # ---- incompat ----
    incompat = []
    for ax in extraction.get("incompat") or []:
        ident = ax.get("acts") if isinstance(ax, dict) else repr(ax)
        if not guard("incompat", ident, lambda ax=ax: _validate_incompat(ax, declared)):
            continue
        # An incompat naming an act that cascaded out can never fire, so
        # dropping it is inert — but it must go, or the .lp would reference an
        # atom that is no longer part of the program.
        orphan = [a for a in ax["acts"] if a not in atoms]
        if orphan and skip_invalid:
            reject(
                "incompat", ident,
                EmitError(
                    f"incompat {ax['acts']}: act(s) {orphan!r} were orphaned by a "
                    f"dropped rule — the axiom can never fire",
                    "incompat orphaned by a dropped rule",
                ),
                cascade=True,
            )
            continue
        incompat.append(ax)

    # ---- exclusions ----
    exclusions = []
    group_of = {}  # context atom -> index into `exclusions` of its at_most_one group
    for ex in extraction["exclusions"]:
        ident = ex.get("atoms") if isinstance(ex, dict) else repr(ex)
        if not guard(
            "exclusion", ident,
            lambda ex=ex: _validate_exclusion(ex, declared, group_of, exclusions),
        ):
            continue
        if skip_invalid:
            # Restrict the exclusion to atoms still in the program. For
            # at_most_one this is a sound projection (a dropped atom can never
            # be true, so the constraint over the survivors is equivalent);
            # for `excludes` a missing side makes it unable to fire.
            kept = [n for n in ex["atoms"] if n in atoms]
            if len(kept) < 2:
                reject(
                    "exclusion", ident,
                    EmitError(
                        f"exclusion {ex['atoms']}: fewer than 2 of its atoms survive "
                        f"({kept!r}) — the constraint can never bite",
                        "exclusion orphaned by a dropped rule",
                    ),
                    cascade=True,
                )
                continue
            if kept != list(ex["atoms"]):
                ex = dict(ex, atoms=kept)
        if ex["kind"] == "at_most_one":
            for n in ex["atoms"]:
                group_of[n] = len(exclusions)
        exclusions.append(ex)

    counts = defaultdict(int)
    for r in rejected:
        counts[r["reason_class"]] += 1
    provenance = {
        "atoms_in": len(extraction["atoms"]),
        "atoms_emitted": len(atoms),
        "atoms_rejected": sum(1 for r in rejected if r["kind"] == "atom"),
        "rules_in": len(extraction["rules"]),
        "rules_emitted": len(rules),
        "rules_rejected": sum(1 for r in rejected if r["kind"] == "rule"),
        "incompat_in": len(extraction.get("incompat") or []),
        "incompat_emitted": len(incompat),
        "exclusions_in": len(extraction["exclusions"]),
        "exclusions_emitted": len(exclusions),
        "cascade_drops": sum(1 for r in rejected if r["cascade"]),
        "rejection_reasons": dict(sorted(counts.items())),
        "skip_invalid": bool(skip_invalid),
    }

    return {
        "atoms": atoms,
        "rules": rules,
        "incompat": incompat,
        "exclusions": exclusions,
        "grouped": set(group_of),
        "rejected": rejected,
        "provenance": provenance,
    }


# ----------------------------------------------------------------- emitter ---

_TAIL = """
% ---------- conflict detection (shape copied from rules.lp) ----------
% direct: same act obliged and forbidden
conflict(N1, N2, A, T1, T2) :-
    active(N1, oblige, A, T1), active(N2, forbid, A, T2), N1 != N2.
% indirect: two obligations on incompatible acts
conflict(N1, N2, A1, T1, T2) :-
    active(N1, oblige, A1, T1), active(N2, oblige, A2, T2),
    incompat(A1, A2).
conflict(N1, N2, A1, T1, T2) :-
    active(N1, oblige, A1, T1), active(N2, oblige, A2, T2),
    incompat(A2, A1).

same_tier_conflict(N1, N2)  :- conflict(N1, N2, _, T, T).
cross_tier_conflict(N1, N2) :- conflict(N1, N2, _, T1, T2), T1 != T2.

% only show scenarios containing at least one conflict
has_conflict :- conflict(_,_,_,_,_).
:- not has_conflict.

#show conflict/5.
#show ctx/1.
"""


def emit(extraction: dict, include_provenance: bool = True,
         skip_invalid: bool = False, idx: dict = None) -> str:
    """Render the `.lp`. Pass a pre-computed `idx` from `validate()` to avoid
    validating twice (and to read the rejection provenance)."""
    if idx is None:
        idx = validate(extraction, skip_invalid=skip_invalid)
    atoms, rules, incompat = idx["atoms"], idx["rules"], idx["incompat"]
    exclusions, grouped = idx["exclusions"], idx["grouped"]
    prov = idx["provenance"]

    out = []
    out.append("% " + "=" * 58)
    out.append("% Generated by emit_asp.py — do not edit by hand.")
    out.append(f"% section: {extraction.get('section', '?')}")
    out.append(f"% model:   {extraction.get('model', '?')}")
    out.append(f"% run_id:  {extraction.get('run_id', '?')}")
    out.append(
        f"% tier is constant {TIER}: the section is uniformly root authority, "
        "so every conflict is same-tier."
    )
    if idx["rejected"]:
        out.append("%")
        out.append(
            "%% !! PARTIAL PROGRAM: %d of %d rules emitted (%d rejected, "
            "%d cascade drops). Conflicts below are computed over the survivors "
            "only. See conflicts.json -> provenance."
            % (prov["rules_emitted"], prov["rules_in"], prov["rules_rejected"],
               prov["cascade_drops"])
        )
        for rj in idx["rejected"]:
            out.append(
                "%%   dropped %s %s: %s"
                % (rj["kind"], rj["id"], rj["reason"].replace("\n", " "))
            )
    out.append("% " + "=" * 58)

    # ---------- scenario space ----------
    out.append("\n% ---------- scenario space: context predicates ----------")
    for name in sorted(a["name"] for a in atoms.values() if a["kind"] == "context"):
        if name in grouped:
            continue  # emitted below as part of its at_most_one choice group
        gloss = atoms[name].get("gloss") or ""
        comment = f"   % {gloss}" if gloss else ""
        out.append("{ ctx(%s) }.%s" % (name, comment))

    # ---------- exclusions: context atoms that cannot co-occur ----------
    # `at_most_one` becomes a bounded choice group (rules.lp style), so the
    # grouped atoms have no independent choice rule above; `excludes` becomes
    # an integrity constraint over atoms that keep their own choice rules.
    amo = [e for e in exclusions if e["kind"] == "at_most_one"]
    exc = [e for e in exclusions if e["kind"] == "excludes"]
    if exclusions:
        out.append("\n% ---------- exclusions: mutually exclusive context atoms ----------")
        out.append("% Each carries a license label per the axiom taxonomy:")
        out.append("%   logical = true by the meaning of the atoms; textual = spec")
        out.append("%   asserts it (cite clause); assumed = analyst judgment, flagged.")
    for e in amo:
        src = (e.get("source") or "").replace("\n", " ").strip()
        for n in e["atoms"]:
            g = atoms[n].get("gloss") or ""
            if g:
                out.append(f"%   {n}: {g}")
        out.append(
            "{ %s } 1.      %% license: %s%s"
            % ("; ".join("ctx(%s)" % n for n in e["atoms"]),
               e["license"].upper(), f" — {src}" if src else "")
        )
    for e in exc:
        src = (e.get("source") or "").replace("\n", " ").strip()
        a, b = e["atoms"]
        out.append(
            ":- ctx(%s), ctx(%s).      %% license: %s%s"
            % (a, b, e["license"].upper(), f" — {src}" if src else "")
        )

    # ---------- provenance (output-only) ----------
    if include_provenance:
        out.append("\n% ---------- provenance (OUTPUT METADATA ONLY) ----------")
        out.append("% These facts appear in no rule body or head and cannot")
        out.append("% affect derivation. See test_emit_asp.py.")
        for rid in sorted(rules):
            out.append(
                "source(%s, %s)." % (rid, _qstr(_section_of(rules[rid].get("locator", ""))))
            )
        out.append("#show source/2.")
        for rid in sorted(rules):
            r = rules[rid]
            out.append(
                "locator(%s, %s, %s, %s)."
                % (rid, _qstr(r.get("locator", "")), _qstr(_clause_id(rid)),
                   _qstr(r.get("kind", "conditional")))
            )
        out.append("#show locator/4.")

    # ---------- norms ----------
    out.append("\n% ---------- norms ----------")
    for rid in sorted(rules):
        r = rules[rid]
        quote = (r.get("quote") or "").replace("\n", " ").strip()
        if quote:
            out.append(f"% {rid}: {quote}")
        body = ["ctx(%s)" % c for c in (r.get("conditions") or [])]
        defeaters = r.get("defeaters") or []
        if defeaters:
            body.append("not defeated(%s)" % rid)
        head = "active(%s, %s, %s, %d)" % (rid, r["modality"], r["act"], TIER)
        if body:
            out.append("%s :-\n    %s." % (head, ", ".join(body)))
        else:
            out.append("%s." % head)
        for d in defeaters:
            src = (d.get("source") or "").replace("\n", " ").strip()
            if src:
                out.append(f"%   defeater: {src}")
            out.append(
                "defeated(%s) :- %s."
                % (rid, ", ".join("ctx(%s)" % c for c in d["conditions"]))
            )

    # ---------- incompatible-act pairs ----------
    out.append("\n% ---------- incompatible-act pairs ----------")
    if not incompat:
        out.append("% (none)")
    for ax in incompat:
        a, b = ax["acts"]
        src = (ax.get("source") or "").replace("\n", " ").strip()
        out.append(
            "incompat(%s, %s).      %% license: %s%s"
            % (a, b, ax["license"].upper(), f" — {src}" if src else "")
        )

    out.append(_TAIL)
    return "\n".join(out) + "\n"


def write_lp(extraction: dict, path: str, include_provenance: bool = True,
             skip_invalid: bool = False, idx: dict = None) -> str:
    text = emit(extraction, include_provenance=include_provenance,
                skip_invalid=skip_invalid, idx=idx)
    with open(path, "w") as f:
        f.write(text)
    return text


def strip_provenance(lp_text: str) -> str:
    """Remove `source/2` and `locator/4` facts and their `#show` directives,
    selected by predicate name (not by string prefix matching)."""
    keep = []
    fact = re.compile(r"^\s*(%s)\s*\(" % "|".join(PROVENANCE_PREDICATES))
    show = re.compile(r"^\s*#show\s+(%s)/\d+\s*\.\s*$" % "|".join(PROVENANCE_PREDICATES))
    for line in lp_text.splitlines():
        if fact.match(line) or show.match(line):
            continue
        keep.append(line)
    return "\n".join(keep) + "\n"


# ------------------------------------------------------------------ solver ---
# Mirrors run_conflicts.py's brave-consequence enumeration, parameterized by
# program path (run_conflicts hardcodes rules.lp in a module constant).

def brave_conflicts(lp_path: str):
    """Union over all answer sets of the conflict/5 atoms (brave consequences)."""
    ctl = clingo.Control(["--enum-mode=brave", _NO_UNDEF])
    ctl.load(lp_path)
    ctl.ground([("base", [])])
    last = []

    def on_model(m):
        last.clear()
        last.extend(m.symbols(shown=True))

    ctl.solve(on_model=on_model)
    sources = {
        str(s.arguments[0]): str(s.arguments[1]).strip('"')
        for s in last
        if s.name == "source"
    }
    locators = {
        str(s.arguments[0]): tuple(str(a).strip('"') for a in s.arguments[1:])
        for s in last
        if s.name == "locator"
    }
    return sorted({str(s) for s in last if s.name == "conflict"}), sources, locators


def witness(lp_path: str, conflict_atom: str, minimize: bool = True):
    """One minimal-ish witness scenario for a given conflict atom."""
    ctl = clingo.Control(["--opt-mode=optN", "1", _NO_UNDEF])
    ctl.load(lp_path)
    ctl.add("goal", [], f":- not {conflict_atom}.")
    if minimize:
        ctl.add("goal", [], "#minimize { 1,X : ctx(X) }.")
    ctl.ground([("base", []), ("goal", [])])
    found = {}

    def on_model(m):
        syms = m.symbols(shown=True)
        found["ctx"] = sorted(str(s.arguments[0]) for s in syms if s.name == "ctx")

    ctl.solve(on_model=on_model)
    return found.get("ctx", [])


def _parse_conflict(atom: str):
    inner = atom[len("conflict(") : -1]
    n1, n2, act, t1, t2 = [x.strip() for x in inner.split(",")]
    return n1, n2, act, int(t1), int(t2)


def conflict_pairs(lp_path: str):
    """Deduped unordered norm pairs, each with a representative conflict atom."""
    conflicts, sources, locators = brave_conflicts(lp_path)
    seen = {}
    for c in conflicts:
        n1, n2, act, t1, t2 = _parse_conflict(c)
        key = frozenset((n1, n2))
        if key not in seen:
            seen[key] = (c, n1, n2, act, t1, t2)
    return seen, sources, locators


# ------------------------------------------------------------ prose (mech) ---

def _gloss_map(extraction: dict) -> dict:
    return {
        a["name"]: (a.get("gloss") or a["name"]).strip().rstrip(".")
        for a in extraction.get("atoms", [])
    }


def _join(items):
    items = list(items)
    if not items:
        return "no particular conditions hold"
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def witness_prose(extraction: dict, n1: str, n2: str, act: str, ctx: list) -> str:
    """Mechanically templated one-sentence description. No LLM."""
    g = _gloss_map(extraction)
    rules = {r["id"]: r for r in extraction.get("rules", [])}
    r1, r2 = rules.get(n1, {}), rules.get(n2, {})
    conds = _join([g.get(c, c) for c in ctx])
    verb = {"oblige": "requires", "forbid": "forbids", "permit": "permits"}
    a1, a2 = r1.get("act", act), r2.get("act", act)
    v1 = verb.get(r1.get("modality"), "bears on")
    v2 = verb.get(r2.get("modality"), "bears on")
    if a1 == a2:
        return (
            f"When {conds}: {n1} {v1} {g.get(a1, a1)}, while {n2} {v2} the same act."
        )
    return (
        f"When {conds}: {n1} {v1} {g.get(a1, a1)}, while {n2} {v2} "
        f"{g.get(a2, a2)}, and those acts are incompatible."
    )


def _note(extraction: dict, n1: str, n2: str, act: str) -> str:
    rules = {r["id"]: r for r in extraction.get("rules", [])}
    r1, r2 = rules.get(n1, {}), rules.get(n2, {})
    return (
        f"{n1} ({r1.get('modality', '?')} {r1.get('act', '?')}, "
        f"{r1.get('locator', 'no locator')}) collides with "
        f"{n2} ({r2.get('modality', '?')} {r2.get('act', '?')}, "
        f"{r2.get('locator', 'no locator')}) over act {act}; "
        f"same-tier (tier {TIER}, root authority) — unresolved by priority ordering."
    )


def conflicts_report(extraction: dict, lp_path: str, source: str = "tool",
                     idx: dict = None) -> dict:
    """`conflicts.json` per contract §3, plus a `provenance` block recording
    how much of the extraction the conflict set was actually computed over.
    A conflict set over 20 of 24 rules is not the same claim as one over 24."""
    seen, _sources, _locators = conflict_pairs(lp_path)
    rows = []
    for c, n1, n2, act, _t1, _t2 in seen.values():
        ctx = witness(lp_path, c)
        pair = sorted([n1, n2])
        # orient the prose along the sorted pair so output is deterministic
        p1, p2 = pair
        rows.append(
            {
                "pair": pair,
                "witness": {"ctx": ctx},
                "witness_prose": witness_prose(extraction, p1, p2, act, ctx),
                "note": _note(extraction, p1, p2, act),
            }
        )
    rows.sort(key=lambda r: (r["pair"], r["witness"]["ctx"]))
    if idx is None:
        idx = validate(extraction)
    return {
        "source": source,
        "model": extraction.get("model", ""),
        "run_id": extraction.get("run_id", ""),
        "conflicts": rows,
        "provenance": idx["provenance"],
        "rejected": idx["rejected"],
    }


def run(extraction: dict, lp_path: str, out_path: str = None, source: str = "tool",
        skip_invalid: bool = False):
    idx = validate(extraction, skip_invalid=skip_invalid)
    write_lp(extraction, lp_path, idx=idx)
    report = conflicts_report(extraction, lp_path, source=source, idx=idx)
    if out_path:
        with open(out_path, "w") as f:
            json.dump(report, f, indent=1)
    return report


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("extraction", help="path to extraction.json")
    ap.add_argument("--lp", default=os.path.join(HERE, "emitted.lp"))
    ap.add_argument("--out", default=os.path.join(HERE, "conflicts.json"))
    ap.add_argument(
        "--skip-invalid", action="store_true",
        help="skip and record items that fail validation instead of aborting; "
             "counts land in conflicts.json -> provenance. Default is fail-fast.",
    )
    args = ap.parse_args(argv)
    with open(args.extraction) as f:
        extraction = json.load(f)
    report = run(extraction, args.lp, args.out, skip_invalid=args.skip_invalid)
    p = report["provenance"]
    print(
        f"rules: {p['rules_emitted']}/{p['rules_in']} emitted, "
        f"{p['rules_rejected']} rejected, {p['cascade_drops']} cascade drops"
    )
    for reason, n in p["rejection_reasons"].items():
        print(f"    {n:3d}  {reason}")
    print(f"{len(report['conflicts'])} distinct norm-pair conflicts -> {args.out}")
    for c in report["conflicts"]:
        print(f"  {c['pair'][0]} vs {c['pair'][1]}: {c['witness_prose']}")
    return report


if __name__ == "__main__":
    main()
