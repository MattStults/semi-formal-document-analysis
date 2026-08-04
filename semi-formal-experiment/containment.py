"""Containment overlay — licensed subsumption over the atom matcher (Unit 4).

WHY THIS EXISTS. The exact-name atom channel cannot see that
`targeted_political_manipulation` is a kind of manipulation: a query carrying
`psychological_manipulation` scores zero against a clause carrying its
sibling, although both attest the same parent concept. English compounds are
mostly right-headed (head_induction_probe.py measures how far that one
convention goes on this vocabulary), so a small set of REVIEWED `child ⊑
parent` edges lets the matcher generalize one hop — without re-annotating
anything, so Unit 1 diffs measure the effect of the edges and nothing else.

VALIDATION IS THE LICENSE. `load_edges` rejects, loudly and by name, any edge
whose child is not a genuine specialization of its parent:

  * a polarity-prefixed child (`mustnot_x`) — a deontic flip, not a subset;
  * a principal in the modifier or in a principal chain — changes WHO is
    involved, not WHAT KIND of thing it is;
  * a negation modifier (`no_`/`not_`/`non_`) — the complement, not a subset;
  * a child that is not `<modifier>_<parent>` — v0 licenses ONLY right-headed
    compounds, which keeps every accepted edge mechanically checkable;
  * a cycle — a subsumer may never be its own descendant;
  * a file without (or over) its REQUIRED `budget` {max_edges, max_families}
    — an overlay that does not declare its own ceiling can grow edge by edge
    without any single change ever reading as growth;
  * given a vocabulary, a family with fewer than 2 children PRESENT in it —
    a one-child family prices the latent parent at the child's own df, an
    alias wearing a generalization's name.

`grammar.parse_name` strips polarity and principal chains first; the residual
modifier tokens are then checked against the polarity stems, the principals,
and the negations, so a mid-name `user` or `not` is caught too.

PRICING. An exact name match scores EXACTLY what the base class scores — the
overlay adds matches, it never re-prices existing ones. A subsumption match's
credit is

    min(idf(subsumer), idf(clause_atom)) * kind_factor

with the best-priced (rarest surviving) shared subsumer chosen when several
are shared. The base term is the SUBSUMER's idf — the matcher pays for the
concept it actually established, not the one it wished for — CAPPED at the
matched clause atom's own exact price, so a subsumption match can never
outprice the exact match on the same evidence (2026-08-03 adversarial
review, finding 3: a real subsumer atom rarer than its child would otherwise
outbid the exact hit). A latent parent (a subsumer that is not itself a
vocabulary atom) has no df of its own, so its df is DEFINED as

    df(parent) = |union over licensed children c of {clauses carrying c}|

— the set of clauses on which the parent concept is attested at all, shared
clauses counted once — and its idf by the base formula
log(1 + N / (1 + df)), stopword-floored at the same cutoff the base index
uses. A parent that IS a vocabulary atom keeps the base index's price for it.

The kind_factor mirrors the base channel's exact-match rule when the
subsumer is a real vocabulary atom with recorded kinds: full credit iff the
query kind is empty or among the subsumer's kinds, the mismatch discount
otherwise. A latent parent has no kinds of its own — but as of pricing v1.1
(UNANIMOUS-CHILD KIND INHERITANCE) it may inherit one: when EVERY licensed
child of the family is attested in the loaded clause vocabulary under
exactly one non-empty kind and all children agree on the same one, the
latent parent inherits that kind, and kind agreement is then checked against
it exactly as for a real-vocabulary subsumer. The inference is mechanical
and document-side — it reads only the clause annotations already loaded,
never a panel or label — and its license is unanimity itself: a family whose
every member the annotators filed under one kind attests the parent concept
in that kind and no other, so agreement IS checkable there. It lifts the
discount exactly where that unanimity licenses it, nowhere else: a child
with conflicting kinds, a child recorded kindless, or a child absent from
the clause vocabulary leaves the family's kind unattested, inheritance does
NOT fire, and kind agreement stays unverifiable — priced as DISAGREEMENT:
the mismatch discount applies, conservatively, because the alternative (full
credit exactly where verification is impossible) would let every
unverifiable match outprice a verified-but-mismatched exact one. Real
vocabulary subsumers never inherit — their own recorded kinds stand.
Inherited-kind full credit is still capped at min(idf(subsumer),
idf(clause_atom)); a latent parent's union df is >= each child's df, so an
inherited-kind match can never outprice the exact match on the same
evidence.

Credit is a MATCHING, not a product: each query atom is credited at most
once (its best match), and each CLAUSE atom is credited at most once per
clause — query atoms claim clause atoms greedily in sorted order — so a
clause-side atom is never paid once per query sibling.

WHAT THIS MODULE MUST NEVER DO.
  * DEFAULT ON. The constructor takes its edges explicitly and defaults to
    none; nothing here — or anywhere — silently loads containment.json. The
    overlay is opt-in forever, so every number can name whether it was on.
  * JUSTIFY AN EDGE BY PANEL OUTCOMES. ITERATION_LOOP.md's policy fork,
    stance (a): keep/revert decisions cite document-side evidence only —
    glosses, adjudicated dossiers, the grammar checks above. An edge added
    because it moved a panel number is a fitted label wearing an ontology's
    clothes, and it makes the label-free headline claim false.
  * TOUCH THE EVALUATION PANEL. Query-adjacent module, panel-blind, scanned
    forever by test_no_reference_leak.py like every other query module.
"""
from __future__ import annotations

import json
import math
from collections import defaultdict

import grammar
import relevance

#: The pricing regime this module implements (module docstring, PRICING).
#: Recorded in every overlay-active snapshot's config identity, so a
#: scoring-rule change under identical inputs produces a diff that can name
#: its own cause. "1.1" = unanimous-child kind inheritance.
PRICING_VERSION = "1.1"

#: The one licensing regime v0 accepts. A new license string is a new review
#: discipline and must arrive with its own validator, not slip past this one.
LICENSE = "shared_head"

#: Negation tokens. `no_` could not be a reserved grammar prefix
#: (`no_authority_content` exists), so it is checked HERE, on the modifier.
NEGATIONS = ("no", "not", "non")

#: The polarity prefixes as bare tokens, for the mid-name check.
POLARITY_STEMS = tuple(p.rstrip("_") for p in grammar.POLARITY_PREFIXES)


# ---------------------------------------------------------------- licensing

def _reject(child, parent, why):
    raise ValueError(
        f"unlicensed containment edge {child!r} -> {parent!r}: {why}")


def _find_cycle(pairs):
    """First cycle in the child->parent graph, as a node list, else None."""
    graph = defaultdict(set)
    for c, p in pairs:
        graph[c].add(p)
    color = {}
    stack = []

    def dfs(n):
        color[n] = 1
        stack.append(n)
        for m in sorted(graph.get(n, ())):
            if color.get(m) == 1:
                return stack[stack.index(m):] + [m]
            if color.get(m) is None:
                got = dfs(m)
                if got:
                    return got
        color[n] = 2
        stack.pop()
        return None

    for n in sorted(graph):
        if color.get(n) is None:
            got = dfs(n)
            if got:
                return got
    return None


def _license_edge(child, parent, license_str):
    """Raise unless this single edge is mechanically licensable."""
    if license_str != LICENSE:
        _reject(child, parent,
                f"license {license_str!r} is not the v0 regime {LICENSE!r}")
    for name, side in ((child, "child"), (parent, "parent")):
        p = grammar.parse_name(name)
        if p["error"]:
            _reject(child, parent, f"{side} does not parse: {p['error']}")
        if p["polarity"]:
            _reject(child, parent,
                    f"{side} {name!r} carries the polarity prefix "
                    f"{p['polarity']!r} — a deontic flip is not a specializer")
        if p["principals"]:
            _reject(child, parent,
                    f"{side} {name!r} carries a principal chain "
                    f"({', '.join(p['principals'])}) — principals change who, "
                    "not what kind")
    stem = grammar.parse_name(child)["stem"]
    if not (stem.endswith("_" + parent) and len(stem) > len(parent) + 1):
        _reject(child, parent,
                "not right-headed: v0 licenses only child == "
                f"'<modifier>_{parent}'")
    modifier = stem[: -(len(parent) + 1)]
    for tok in modifier.split("_"):
        if not tok:
            _reject(child, parent, "empty modifier token")
        if tok in POLARITY_STEMS:
            _reject(child, parent,
                    f"modifier token {tok!r} is a polarity stem — a deontic "
                    "flip is not a specializer")
        if tok in grammar.PRINCIPALS:
            _reject(child, parent,
                    f"modifier token {tok!r} is a principal — it changes who, "
                    "not what kind")
        if tok in NEGATIONS:
            _reject(child, parent,
                    f"modifier token {tok!r} is a negation — the complement "
                    "of the parent, not a subset of it")


def _check_budget(path, doc, n_edges, n_families):
    """The REQUIRED self-declared ceiling (2026-08-03 review, finding 3): an
    overlay that does not state its own maximum size can grow edge by edge
    without any single change ever reading as growth. The budget lives in the
    file, so it participates in the overlay sha every snapshot records —
    raising it is a visible, named config change."""
    b = doc.get("budget")
    if not isinstance(b, dict):
        raise ValueError(
            f"{path}: missing or malformed REQUIRED 'budget' — an overlay "
            "must declare {'max_edges': int, 'max_families': int}")
    limits = {}
    for key in ("max_edges", "max_families"):
        v = b.get(key)
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            raise ValueError(f"{path}: budget[{key!r}] must be a "
                             f"non-negative integer, got {v!r}")
        limits[key] = v
    if n_edges > limits["max_edges"]:
        raise ValueError(
            f"{path}: edge list exceeds its own declared budget — "
            f"{n_edges} edges > max_edges {limits['max_edges']}")
    if n_families > limits["max_families"]:
        raise ValueError(
            f"{path}: family count exceeds its own declared budget — "
            f"{n_families} families > max_families {limits['max_families']}")


def _check_family_support(path, pairs, vocabulary):
    """Every family needs >= 2 children PRESENT in the given vocabulary. With
    a single attested child, the latent parent's df equals that child's df,
    so the 'family' match just re-prices the child under another name — a
    one-child family is an alias, not a generalization (2026-08-03 review,
    finding 3). Presence, not edge count, is what matters: two children on
    paper with one in the vocabulary is the same alias in every df that will
    ever be computed."""
    vocab = set(vocabulary)
    kids = defaultdict(set)
    for c, p in set(pairs):
        kids[p].add(c)
    for parent in sorted(kids):
        present = sorted(kids[parent] & vocab)
        if len(present) < 2:
            raise ValueError(
                f"{path}: containment family {parent!r} has "
                f"{len(present)} child(ren) present in the loaded vocabulary "
                f"({', '.join(present) or 'none'}) — a one-child family is "
                "an alias, not a generalization; every family needs at "
                "least 2 children present")


def load_edges(path, vocabulary=None):
    """The validated edge set from a containment.json-shaped file.

    Returns a sorted, deduplicated tuple of (child, parent) pairs. Raises
    ValueError — naming the edge and the reason — on the first unlicensable
    edge, so a bad overlay never half-loads. Cycles are checked over the WHOLE
    set before per-edge licensing, because a cycle is a property of the set.

    The file's REQUIRED `budget` ({max_edges, max_families}) is always
    enforced against its own edge list (`_check_budget`). When `vocabulary`
    (an iterable of atom names) is given, every family must additionally have
    >= 2 children present in it (`_check_family_support`). snapshot.py and
    dossier.py reconstruct RECORDED, sha-verified overlays without a
    vocabulary in hand, so the family check runs where a vocabulary is
    supplied — artifact review and the v0 pins in test_containment.py, which
    validate containment.json against the real b8 names.
    """
    with open(path) as f:
        doc = json.load(f)
    raw = doc.get("edges") if isinstance(doc, dict) else None
    if not isinstance(raw, list):
        raise ValueError(f"{path}: no 'edges' list")
    pairs, records = [], []
    for e in raw:
        if (not isinstance(e, dict) or not isinstance(e.get("child"), str)
                or not isinstance(e.get("parent"), str)):
            raise ValueError(f"{path}: malformed edge record {e!r} — "
                             "an edge needs string 'child' and 'parent'")
        pairs.append((e["child"], e["parent"]))
        records.append(e)
    _check_budget(path, doc, len(raw), len({p for _, p in pairs}))
    cyc = _find_cycle(pairs)
    if cyc:
        raise ValueError(
            "containment edges contain a cycle: " + " -> ".join(cyc)
            + " — a subsumer may never be its own descendant")
    for e in records:
        _license_edge(e["child"], e["parent"], e.get("license"))
    if vocabulary is not None:
        _check_family_support(path, pairs, vocabulary)
    return tuple(sorted(set(pairs)))


# ---------------------------------------------------------------- the index

class ContainmentIndex(relevance.RelevanceIndex):
    """RelevanceIndex plus licensed one-hop subsumption in the atom channel.

    A query atom q matches a clause atom c EITHER by exact name — priced
    exactly as the base class prices it, bit for bit — OR when q and c share
    a licensed subsumer (q's parent == c, c's parent == q, or a shared
    parent), priced per the module docstring's PRICING rules: the subsumer's
    idf capped at the clause atom's own exact price, times the kind factor,
    at most one credit per clause atom.

    `edges` is explicit and defaults to NONE. With an empty edge set this
    class is behaviourally identical to the base class; nothing constructs it
    with edges unless a caller opted in by name.
    """

    def __init__(self, clauses, annotations=None, weights=None, *, edges=()):
        super().__init__(clauses, annotations, weights)
        self.edges = tuple(sorted({(str(c), str(p)) for c, p in edges}))
        self._up = {}      # name -> licensed parents
        self._down = {}    # parent -> licensed children
        for c, p in self.edges:
            self._up.setdefault(c, set()).add(p)
            self._down.setdefault(p, set()).add(c)

        # Price every parent once, at construction, so query time stays a
        # dict lookup. See the module docstring for the latent-parent df
        # formula; a latent parent attested on NO clause keeps the formula's
        # df=0 value but can never fire (no clause carries child or parent).
        n_docs = len(self.ids) or 1
        cutoff = self.weights.atom_stopword_frac * n_docs
        self.parent_df = {}
        self.subsumer_idf = {}
        for parent, kids in self._down.items():
            if parent in self.atom_df:
                # a real vocabulary atom keeps the base index's price
                self.parent_df[parent] = int(self.atom_df[parent])
                self.subsumer_idf[parent] = self.atom_idf.get(parent, 0.0)
                continue
            df = sum(1 for cid in self.ids if self._names[cid] & kids)
            self.parent_df[parent] = df
            self.subsumer_idf[parent] = (
                0.0 if df > cutoff else math.log(1.0 + n_docs / (1.0 + df)))

        # The kinds each subsumer is filed under across the clause vocabulary,
        # for the kind check (module docstring, PRICING). A real vocabulary
        # atom collects the union of its per-clause kinds. A latent parent is
        # in no annotation, so its own set is empty — but it may INHERIT the
        # one kind its licensed children unanimously carry (pricing v1.1,
        # `_unanimous_child_kind`); when unanimity does not license
        # inheritance the set stays empty, meaning "no kinds defined", which
        # prices at the mismatch discount, conservatively.
        self.parent_kinds = {}
        for parent in self._down:
            ks = set()
            for cid in self.ids:
                ks |= set(self._name_kinds.get(cid, {}).get(parent, ()))
            if not ks and parent not in self.atom_df:
                # v1.1 unanimous-child kind inheritance — LATENT parents
                # only; a real vocabulary atom keeps its own recorded kinds
                # (module docstring, PRICING).
                inherited = self._unanimous_child_kind(self._down[parent])
                if inherited is not None:
                    ks = {inherited}
            self.parent_kinds[parent] = frozenset(ks)

    def _unanimous_child_kind(self, children):
        """The one kind EVERY licensed child of a latent parent is recorded
        under in the loaded clause vocabulary — or None, blocking inheritance
        (pricing v1.1; module docstring, PRICING).

        Each child must be attested with EXACTLY one non-empty kind (its
        union across clauses), and all children must agree on the same one. A
        child absent from the clause vocabulary, or recorded kindless, has no
        recorded kind; a child under two kinds is unanimous about neither —
        either blocks, and the caller keeps the unconditional discount."""
        agreed = set()
        for child in sorted(children):
            ck = set()
            for cid in self.ids:
                ck |= set(self._name_kinds.get(cid, {}).get(child, ()))
            if len(ck) != 1:
                return None      # no recorded kind, or conflicting kinds
            (kind,) = ck
            if not kind:
                return None      # recorded, but kindless
            agreed.add(kind)
            if len(agreed) > 1:
                return None      # children disagree with each other
        return agreed.pop() if agreed else None

    @classmethod
    def from_files(cls, clauses_path=relevance.CLAUSES, annotations_path=None,
                   weights=None, *, edges=()):
        """Same loading path as the base class, plus an explicit edge set."""
        base = relevance.RelevanceIndex.from_files(
            clauses_path=clauses_path, annotations_path=annotations_path,
            weights=weights)
        return cls(base.clauses, base.annotations, weights, edges=edges)

    def _subsumers(self, name):
        return {name} | self._up.get(name, set())

    def _best_subsumption(self, qname, qkind, names):
        """The subsumption match the scorer PRICES for one query atom against
        the clause atom names still `names`-available: (credit, kind_factor,
        subsumer_idf, clause_atom, subsumer) for the best-PRICED shared
        subsumer, or None when nothing is shared or the best credit is zero
        (a stopword-floored parent — or clause atom — contributes nothing).

        The credit per candidate is  min(idf(subsumer), idf(clause_atom)) *
        kind_factor.  The cap enforces the invariant that a subsumption match
        never outprices the exact match on the clause atom it went through
        (a real subsumer atom can be RARER than its child; uncapped it would
        outbid the exact hit). The kind factor mirrors the base channel's
        exact-match rule when the subsumer has kinds defined — its own
        recorded kinds for a real vocabulary atom, or the kind a latent
        parent inherited from unanimous children (pricing v1.1) — full credit
        iff the query kind is empty or among them — and is the MISMATCH
        discount whenever the subsumer has no kinds defined (a latent parent
        without licensed unanimity): agreement that cannot be checked is
        priced as disagreement, conservatively.

        Iteration is sorted with a strict `>` so ties break deterministically
        toward the lexicographically smallest (clause_atom, subsumer)."""
        qsubs = self._subsumers(qname)
        d = self.weights.kind_mismatch_discount
        best = None
        for cname in sorted(names):
            for s in sorted(qsubs & self._subsumers(cname)):
                idf = self.subsumer_idf.get(s)
                if idf is None:
                    idf = self.atom_idf.get(s, 0.0)
                priced = min(idf, self.atom_idf.get(cname, idf))
                kinds = self.parent_kinds.get(s) or ()
                factor = (1.0 if (not qkind or qkind in kinds) else d) \
                    if kinds else d
                credit = priced * factor
                if credit > 0.0 and (best is None or credit > best[0]):
                    best = (credit, factor, idf, cname, s)
        return best

    def _subsumption_matches(self, query_atoms, cid):
        """One priced record per (query atom, clause atom) subsumption match
        on this clause — the explain() payload behind the credit _atom_score
        adds. Two caps make the credit a matching, not a product (2026-08-03
        adversarial review, finding 3, hole 1):

          * each query atom is credited at most once (its best match), as the
            base channel credits each query entry at most once;
          * each CLAUSE atom is credited at most once per clause — its single
            best licensed match — never summed over query siblings. Query
            atoms are taken in sorted order and each claims its best match
            among the clause atoms not yet claimed, so four query siblings
            against one clause-side family atom pay ONCE, not four times.

        Iterates (name, kind) entries exactly as the base channel credits
        them (a name listed under two kinds is credited — and reported — per
        entry), sorted for determinism."""
        out = []
        if not self.edges or not query_atoms:
            return out
        names = self._names.get(cid) or set()
        if not names:
            return out
        available = set(names)
        for qname, qkind in sorted(query_atoms):
            if qname in names:
                continue  # exact match: priced (and reported) by the base
            if not available:
                break
            best = self._best_subsumption(qname, qkind, available)
            if best is not None:
                credit, factor, idf, cname, s = best
                available.discard(cname)
                out.append({"query_atom": qname, "clause_atom": cname,
                            "subsumer": s, "subsumer_idf": idf,
                            "kind_factor": factor, "credit": credit})
        return out

    def _atom_score(self, query_atoms, cid):
        """Base score, unchanged, plus subsumption credit for query atoms
        with NO exact match on this clause. Skipping exactly the exact-matched
        names is what keeps the base contribution bit-identical. The credit
        is the sum of exactly the records _subsumption_matches reports, so
        explain() can never drift from what actually scored."""
        score = super()._atom_score(query_atoms, cid)
        matches = self._subsumption_matches(query_atoms, cid)
        if not matches:
            return score
        extra = sum(m["credit"] for m in matches)
        # same normalization as the base channel: the corpus's rarest-atom
        # weight, never the query's own mass
        return score + extra / self._atom_norm

    def explain(self, behaviour, clause_id):
        """The base payload plus `subsumption_matches`: for every subsumption
        (non-exact) match contributing to this clause's atom channel, the
        record {query_atom, clause_atom, subsumer, subsumer_idf, kind_factor,
        credit} — so a dossier can name the licensing edge (and the exact
        priced credit) behind a flip from the explain output alone
        (ITERATION_LOOP.md Unit 4.1). The records are the SAME objects
        _atom_score summed, so the report can never drift from what scored.
        Exact-name matches stay in `matched_atoms`, unchanged."""
        out = super().explain(behaviour, clause_id)
        qatoms = {(a["name"], a["kind"]) for a in behaviour.norm_atoms}
        out["subsumption_matches"] = self._subsumption_matches(
            qatoms, str(clause_id))
        return out


#: The drivable query surface, so the repo's anti-cheat spy
#: (test_no_reference_leak.py) can exercise this module like every other
#: query module — the same accommodation snapshot.py and readback.py ship.
Index = ContainmentIndex
