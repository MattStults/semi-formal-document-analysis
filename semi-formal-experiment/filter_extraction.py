"""Drop items an `extraction.json` cannot legally emit, and say which and why.

`emit_asp.py` is fail-fast by design: one invalid rule aborts emission. Real
extractions from weak models always contain a few bad rules (the gpt-oss-20b run
uses a *context* atom as a rule's act), so the whole chain stalls on the first
defect and no table can be produced.

This module is an **independent** re-implementation of the structural checks, so
that the filtered extraction is guaranteed to pass `emit_asp.validate()` in its
default fail-fast mode. Being independent is the point: `cross_check()` compares
this module's rejection set against `emit_asp.validate(..., skip_invalid=True)`
and reports disagreements, which is a real test of both.

    python filter_extraction.py extraction.json --out filtered.json \\
        --report rejections.json

Semantics (matching `emit_asp`):
  * an item that fails a check is dropped and recorded with a reason class;
  * items that referenced a dropped item are dropped as *cascade* drops, so the
    emitted program never mentions something that was removed;
  * an atom no surviving rule uses is a cascade drop (it would otherwise get a
    free choice rule and widen the scenario space for nothing);
  * `at_most_one` exclusions are projected onto the surviving atoms; a
    projection with fewer than 2 atoms left cannot bite and is dropped.
"""
from __future__ import annotations

import argparse
import json
import re

ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")
MODALITIES = ("oblige", "forbid", "permit")
LICENSES = ("logical", "textual", "assumed")
EXCLUSION_KINDS = ("at_most_one", "excludes")
TIER = 1


class Reject(Exception):
    def __init__(self, message, reason_class):
        super().__init__(message)
        self.reason_class = reason_class


def _const(name, what, where=""):
    if not isinstance(name, str) or not ID_RE.match(name):
        raise Reject(f"{where}{what} {name!r} is not a legal ASP constant "
                     f"(must match ^[a-z][a-z0-9_]*$)",
                     f"{what} is not a legal ASP constant")


# ------------------------------------------------------------------ checks ---

def check_atom(a, seen):
    if not isinstance(a, dict) or "name" not in a:
        raise Reject(f"atom {a!r} has no name", "atom has no name")
    _const(a["name"], "atom name")
    if a.get("kind") not in ("context", "act"):
        raise Reject(f"atom {a['name']}: bad kind {a.get('kind')!r}",
                     "atom has a bad kind")
    if a["name"] in seen:
        raise Reject(f"duplicate atom {a['name']!r}", "duplicate atom")


def check_rule(r, atoms, seen):
    if not isinstance(r, dict) or "id" not in r:
        raise Reject(f"rule {r!r} has no id", "rule has no id")
    rid = r["id"]
    _const(rid, "rule id")
    if rid in seen:
        raise Reject(f"duplicate rule id {rid!r}", "duplicate rule id")
    where = f"rule {rid}: "

    def need(name, kind):
        _const(name, f"{kind} atom", where)
        if name not in atoms:
            raise Reject(f"{where}undeclared atom {name!r}",
                         "rule references an undeclared atom")
        if atoms[name].get("kind") != kind:
            raise Reject(
                f"{where}{name!r} is a {atoms[name].get('kind')!r} atom, "
                f"expected {kind!r}",
                f"rule uses a non-{kind} atom where an {kind} atom is required")

    if r.get("modality") not in MODALITIES:
        raise Reject(f"{where}bad modality {r.get('modality')!r}",
                     "rule has a bad modality")
    if "act" not in r:
        raise Reject(f"{where}missing act", "rule has no act")
    need(r["act"], "act")
    for c in r.get("conditions") or []:
        need(c, "context")
    for d in r.get("defeaters") or []:
        if not isinstance(d, dict):
            raise Reject(f"{where}defeater {d!r} is not an object",
                         "malformed defeater")
        conds = d.get("conditions") or []
        if not conds:
            raise Reject(f"{where}defeater with no conditions",
                         "defeater with no conditions")
        for c in conds:
            need(c, "context")
    if r.get("tier", TIER) != TIER:
        raise Reject(f"{where}tier must be {TIER} (section is uniformly root "
                     f"authority), got {r.get('tier')!r}",
                     "rule has a non-root tier")


def check_incompat(ax, atoms):
    acts = ax.get("acts") if isinstance(ax, dict) else None
    if not isinstance(acts, list) or len(acts) != 2:
        raise Reject(f"incompat {ax!r}: needs exactly 2 acts", "incompat arity")
    for a in acts:
        _const(a, "incompat act")
        if a not in atoms:
            raise Reject(f"incompat {acts}: undeclared atom {a!r}",
                         "incompat references an undeclared atom")
        if atoms[a].get("kind") != "act":
            raise Reject(f"incompat {acts}: {a!r} is not an act atom",
                         "incompat names a non-act atom")
    if ax.get("license") not in LICENSES:
        raise Reject(f"incompat {acts}: bad license {ax.get('license')!r}",
                     "incompat bad license")
    if ax["license"] == "textual" and not ax.get("source"):
        raise Reject(f"incompat {acts}: textual license requires a source",
                     "textual license without a source")


def check_exclusion(ex, atoms, group_of, kept_exclusions):
    names = ex.get("atoms") if isinstance(ex, dict) else None
    kind = ex.get("kind") if isinstance(ex, dict) else None
    if kind not in EXCLUSION_KINDS:
        raise Reject(f"exclusion {ex!r}: bad kind {kind!r}", "exclusion bad kind")
    if not isinstance(names, list):
        raise Reject(f"exclusion {ex!r}: atoms must be a list", "exclusion malformed")
    if kind == "excludes" and len(names) != 2:
        raise Reject(f"exclusion {names}: 'excludes' needs exactly 2 atoms, "
                     f"got {len(names)}", "exclusion arity")
    if kind == "at_most_one" and len(names) < 2:
        raise Reject(f"exclusion {names}: 'at_most_one' needs at least 2 atoms, "
                     f"got {len(names)}", "exclusion arity")
    if len(set(names)) != len(names):
        raise Reject(f"exclusion {names}: repeats an atom", "exclusion repeats an atom")
    for n in names:
        _const(n, "exclusion atom")
        if n not in atoms:
            raise Reject(f"exclusion {names}: undeclared atom {n!r}",
                         "exclusion references an undeclared atom")
        if atoms[n].get("kind") != "context":
            raise Reject(
                f"exclusion {names}: {n!r} is not a context atom "
                f"(exclusions constrain context atoms; use incompat for acts)",
                "exclusion names a non-context atom")
    if ex.get("license") not in LICENSES:
        raise Reject(f"exclusion {names}: bad license {ex.get('license')!r}",
                     "exclusion bad license")
    if ex["license"] == "textual" and not ex.get("source"):
        raise Reject(f"exclusion {names}: textual license requires a source",
                     "textual license without a source")
    if kind == "at_most_one":
        for n in names:
            if n in group_of:
                raise Reject(
                    f"exclusion {names}: atom {n!r} already belongs to another "
                    f"at_most_one group {kept_exclusions[group_of[n]]['atoms']}",
                    "atom in more than one at_most_one group")


# ------------------------------------------------------------------ filter ---

def filter_extraction(extraction):
    """-> (filtered_extraction, report). The filtered dict passes
    `emit_asp.validate()` in fail-fast mode."""
    rejected = []

    def drop(kind, ident, err, cascade=False):
        rejected.append({"kind": kind, "id": ident, "reason": str(err),
                         "reason_class": (err.reason_class
                                          if isinstance(err, Reject) else str(err)),
                         "cascade": cascade})

    def guard(kind, ident, fn):
        try:
            fn()
            return True
        except Reject as e:
            drop(kind, ident, e)
            return False

    # Whole-document defects have nothing to skip *to*.
    if not isinstance(extraction, dict):
        raise Reject("extraction must be a JSON object", "extraction malformed")
    for key in ("atoms", "rules"):
        if not isinstance(extraction.get(key), list):
            raise Reject(f"extraction.{key} must be a list", "extraction malformed")
    # `exclusions` is mandatory in the contract (§3) but a *missing* key is a
    # schema gap, not a per-item defect: normalize it to [] here and record the
    # substitution, rather than aborting a whole run over it.
    exclusions_in = extraction.get("exclusions")
    exclusions_defaulted = False
    if exclusions_in is None:
        exclusions_in, exclusions_defaulted = [], True
    if not isinstance(exclusions_in, list):
        raise Reject("extraction.exclusions must be a list", "extraction malformed")

    atoms = {}
    for a in extraction["atoms"]:
        ident = a.get("name") if isinstance(a, dict) else repr(a)
        if guard("atom", ident, lambda a=a: check_atom(a, atoms)):
            atoms[a["name"]] = a

    rules = {}
    for r in extraction["rules"]:
        ident = r.get("id") if isinstance(r, dict) else repr(r)
        if guard("rule", ident, lambda r=r: check_rule(r, atoms, rules)):
            rules[r["id"]] = r

    declared = dict(atoms)              # axioms are checked against declarations
    used = set()
    for r in rules.values():
        used.add(r["act"])
        used.update(r.get("conditions") or [])
        for d in r.get("defeaters") or []:
            used.update(d.get("conditions") or [])
    for name in [n for n in atoms if n not in used]:
        drop("atom", name,
             Reject(f"atom {name!r}: orphaned — no surviving rule uses it",
                    "atom orphaned by a dropped rule"), cascade=True)
        del atoms[name]

    incompat = []
    for ax in extraction.get("incompat") or []:
        ident = ax.get("acts") if isinstance(ax, dict) else repr(ax)
        if not guard("incompat", ident, lambda ax=ax: check_incompat(ax, declared)):
            continue
        orphan = [a for a in ax["acts"] if a not in used]
        if orphan:
            drop("incompat", ident,
                 Reject(f"incompat {ax['acts']}: act(s) {orphan!r} used by no "
                        f"surviving rule — the axiom can never fire",
                        "incompat orphaned by a dropped rule"), cascade=True)
            continue
        incompat.append(ax)

    exclusions, group_of = [], {}
    for ex in exclusions_in:
        ident = ex.get("atoms") if isinstance(ex, dict) else repr(ex)
        if not guard("exclusion", ident,
                     lambda ex=ex: check_exclusion(ex, declared, group_of, exclusions)):
            continue
        kept = [n for n in ex["atoms"] if n in atoms]
        if len(kept) < 2:
            drop("exclusion", ident,
                 Reject(f"exclusion {ex['atoms']}: fewer than 2 of its atoms "
                        f"survive ({kept!r}) — the constraint can never bite",
                        "exclusion orphaned by a dropped rule"), cascade=True)
            continue
        if kept != list(ex["atoms"]):
            ex = dict(ex, atoms=kept)
        if ex["kind"] == "at_most_one":
            for n in ex["atoms"]:
                group_of[n] = len(exclusions)
        exclusions.append(ex)

    out = dict(extraction)
    out["atoms"] = [a for a in extraction["atoms"]
                    if isinstance(a, dict) and a.get("name") in atoms
                    and atoms[a["name"]] is a]
    out["rules"] = [r for r in extraction["rules"]
                    if isinstance(r, dict) and r.get("id") in rules
                    and rules[r["id"]] is r]
    out["incompat"] = incompat
    out["exclusions"] = exclusions

    counts = {}
    for r in rejected:
        counts[r["reason_class"]] = counts.get(r["reason_class"], 0) + 1
    report = {
        "atoms_in": len(extraction["atoms"]),
        "atoms_emitted": len(atoms),
        "atoms_rejected": sum(1 for r in rejected if r["kind"] == "atom"),
        "rules_in": len(extraction["rules"]),
        "rules_emitted": len(rules),
        "rules_rejected": sum(1 for r in rejected if r["kind"] == "rule"),
        "incompat_in": len(extraction.get("incompat") or []),
        "incompat_emitted": len(incompat),
        "exclusions_in": len(exclusions_in),
        "exclusions_emitted": len(exclusions),
        "exclusions_defaulted": exclusions_defaulted,
        "cascade_drops": sum(1 for r in rejected if r["cascade"]),
        "rejection_reasons": dict(sorted(counts.items())),
        "rejected": rejected,
    }
    return out, report


# ------------------------------------------------------------- cross-check ---

def _sig(rejected):
    """Comparable rejection signature: (kind, id-as-text, cascade).

    Deliberately **excludes** `reason_class`. Agreement means the two
    implementations drop the same items for the same structural role, not that
    they phrase the diagnostic identically --- pinning the prose made the
    cross-check fail on an article ("a context atom" vs "an context atom")
    while both had correctly rejected the same rule. Wording differences are
    still surfaced, as `reason_class_differences`.
    """
    return {(r["kind"],
             json.dumps(r["id"], sort_keys=True) if not isinstance(r["id"], str)
             else r["id"],
             bool(r["cascade"])) for r in rejected}


def _reasons(rejected):
    out = {}
    for r in rejected:
        key = (r["kind"],
               json.dumps(r["id"], sort_keys=True) if not isinstance(r["id"], str)
               else r["id"])
        out[key] = r["reason_class"]
    return out


def cross_check(extraction):
    """Compare this filter against `emit_asp.validate(skip_invalid=True)`.

    Returns a dict with `agree` plus the symmetric difference. Used to retire
    this module once emit_asp grows a `--skip-invalid` CLI flag.
    """
    import emit_asp
    _, mine = filter_extraction(extraction)
    theirs = emit_asp.validate(extraction, skip_invalid=True)
    a, b = _sig(mine["rejected"]), _sig(theirs["rejected"])
    counts_match = all(
        mine[k] == theirs["provenance"][k]
        for k in ("atoms_emitted", "rules_emitted", "incompat_emitted",
                  "exclusions_emitted", "cascade_drops"))
    ra, rb = _reasons(mine["rejected"]), _reasons(theirs["rejected"])
    diffs = sorted((list(k), ra[k], rb[k]) for k in set(ra) & set(rb)
                   if ra[k] != rb[k])
    return {"agree": a == b and counts_match,
            "only_filter_extraction": sorted(a - b),
            "only_emit_asp": sorted(b - a),
            "counts_match": counts_match,
            "reason_class_differences": diffs,
            "mine": {k: v for k, v in mine.items() if k != "rejected"},
            "theirs": theirs["provenance"]}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("extraction")
    ap.add_argument("--out", default=None, help="write the filtered extraction")
    ap.add_argument("--report", default=None, help="write the rejection report")
    ap.add_argument("--cross-check", action="store_true",
                    help="compare against emit_asp.validate(skip_invalid=True)")
    a = ap.parse_args(argv)
    with open(a.extraction) as f:
        extraction = json.load(f)
    filtered, report = filter_extraction(extraction)
    if a.out:
        with open(a.out, "w") as f:
            json.dump(filtered, f, indent=1)
        print(f"filtered extraction -> {a.out}")
    if a.report:
        with open(a.report, "w") as f:
            json.dump(report, f, indent=1)
        print(f"rejections -> {a.report}")
    print(f"rules {report['rules_emitted']}/{report['rules_in']} kept, "
          f"atoms {report['atoms_emitted']}/{report['atoms_in']} kept, "
          f"{report['cascade_drops']} cascade drops")
    for r in report["rejected"]:
        print(f"  DROP {r['kind']} {r['id']}"
              f"{' (cascade)' if r['cascade'] else ''}: {r['reason']}")
    if a.cross_check:
        cc = cross_check(extraction)
        print(f"cross-check vs emit_asp.validate(skip_invalid=True): "
              f"{'AGREE' if cc['agree'] else 'DISAGREE'}")
        for s in cc["only_filter_extraction"]:
            print(f"  only filter_extraction: {s}")
        for s in cc["only_emit_asp"]:
            print(f"  only emit_asp:          {s}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
