"""Adapter: `modelspec_focus_areas.json` -> flat inventory rows.

One row per focus area, no collapsing or grouping. Rows carry both the raw
`focus_id` (`source_id`, the join key back to the OpenAI rubric prompts) and a
uniformly prefixed, ASP-legal `id`.

Row shape:
    {id, source_id, locator, quote, marked_span, kind, modality, has_defeater}

`locator` format (Agent C must match this exactly):
    "model_spec@2025-12-18 > <section_path joined by ' > '> > L<line> [fa_<id>]"

The trailing `[fa_<id>]` is load-bearing: line-level locators are NOT unique.
The 62 chain-of-command provisions share only 34 distinct line locators, and 7
of those collisions span genuinely different clause text — so a bare locator
cannot identify a provision. The focus id is unique by the document's own
construction and stable under re-segmentation, unlike a derived ordinal
(`L203#2`), which would silently renumber whenever the provision set changed.
"""
from __future__ import annotations

import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
FOCUS_AREAS = os.path.join(HERE, "modelspec_focus_areas.json")
# Canonical spec lives outside this experiment so both it and the constitution
# come from one place; verified byte-identical (sha256 8c95f020...) to the
# former local clone at external/model_spec/, which is retained as a fallback
# only so the module still imports if the specs tree moves.
SPEC_MD = os.path.abspath(os.path.join(
    HERE, "..", "specs", "openai-model-spec", "model_spec.md"))
if not os.path.exists(SPEC_MD):
    SPEC_MD = os.path.join(HERE, "external", "model_spec", "model_spec.md")

SPEC_VERSION = "model_spec@2025-12-18"
DEFAULT_SECTION = "The chain of command"

ID_PREFIX = "fa_"
ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def asp_id(focus_id: str) -> str:
    """Prefix uniformly. 13 of the 62 focus ids in the chain-of-command
    section are digit-initial and illegal as ASP constants; prefixing every
    id keeps this a single rule rather than a special case."""
    return ID_PREFIX + focus_id


def make_locator(section_path, line, focus_id=None) -> str:
    """Unique provision locator. `focus_id` is optional only so that older call
    sites that never had one keep working; inventory rows always pass it, and
    without it the result is NOT unique (see module docstring)."""
    base = f"{SPEC_VERSION} > {' > '.join(section_path)} > L{line}"
    return base if focus_id is None else f"{base} [{asp_id(focus_id)}]"


def locator_is_unique(rows) -> bool:
    """Assert no two rows share a locator. Raises AssertionError listing the
    colliding locators; returns True on success."""
    from collections import Counter

    dupes = {loc: n for loc, n in Counter(r["locator"] for r in rows).items() if n > 1}
    assert not dupes, (
        f"{len(dupes)} locator(s) shared by more than one provision: "
        f"{sorted(dupes)[:5]}"
    )
    return True


# ---- quote-containment join (panel comparison) ----

FOOTNOTE_MARKER = re.compile(r"\[\^[a-z0-9]+\]")


_LINK = re.compile(r"\[([^\]]*)\]\(([^)]*)\)")
_EMPH = re.compile(r"\*\*|\*|`")


def _norm(s: str) -> str:
    """Normalize away source-encoding noise before comparing text.

    All artifacts of how the Model Spec is stored or re-rendered, not
    differences in what is being said:
      * whitespace — the source hard-wraps, so a multi-line clause never
        compares equal byte-strictly against a reflowed panel passage;
      * footnote markers — every focus-area quote carries an inline `[^xxxx]`
        marker (25 mid-sentence) that the panel's quotes lack;
      * markdown emphasis — every example caption is `**Example**:` in source
        and `Example:` in the panel, so *no* example-block passage can match
        without this (313 of 863 passages);
      * links — reduced to their text; see `_variants` for the target form.
    """
    s = FOOTNOTE_MARKER.sub("", s or "")
    s = _LINK.sub(lambda m: m.group(1), s)
    return " ".join(_EMPH.sub("", s).split())


def _variants(s: str) -> set:
    """Both renderings of a link, because the panel's renderer is inconsistent
    — sometimes emitting the link text, sometimes the target, occasionally
    both inside one passage. Comparing against both recovers 849/863 rather
    than 377/863."""
    s = FOOTNOTE_MARKER.sub("", s or "")
    return {" ".join(_EMPH.sub("", _LINK.sub(lambda m: m.group(k), s)).split())
            for k in (1, 2)}


def match_passage(passage_quote: str, rows) -> list:
    """Provisions covered by a panel passage, joined on quote containment.

    Locator-to-locator cannot work: our locators are line-anchored and the
    panel's are paragraph-anchored (`... > #chain_of_command > ¶3`), and a
    paragraph holds several provisions — the relation is many-to-many on both
    sides. So match on text: a provision matches when its `quote` or
    `marked_span` sits inside the passage, or the passage sits inside its
    `quote` (the panel sometimes cites a fragment of a longer sentence).

    Returns every match, in row order. The relation is genuinely one-to-many
    and callers must see that rather than receive an arbitrary pick.
    """
    ps = {v for v in _variants(passage_quote) if v}
    if not ps:
        return []
    out = []
    for r in rows:
        qs = {v for v in _variants(r["quote"]) if v}
        spans = {v for v in _variants(r["marked_span"]) if v}
        if any(q in p for q in qs for p in ps) \
           or any(s in p for s in spans for p in ps) \
           or any(p in q for q in qs for p in ps):
            out.append(r)
    return out


# ---- join v2 (JOIN_INTEGRITY_DESIGN.md §2 + SEGMENTATION_GAPS_DESIGN.md §3/§4)

#: v1 = `match_passage`, today's behavior, kept reachable forever (the
#: PRICING_VERSION pattern; reconstruction compatibility per CYCLE_DESIGN F9).
#: v2 = locator-restricted candidates + degenerate-quote refusal + the F9
#: empty-meta skip + per-link mixed rendering variants. Per PORTFOLIO_REVIEW
#: F12: join_version belongs in CENSUS config identity, NOT snapshot identity
#: — the join is downstream of the scorer and cannot flip a clause snapshot.
JOIN_VERSION_V1 = 1
JOIN_VERSION_V2 = 2

#: 2b backstop arm: normalized quotes under this many characters are refused
#: before candidate enumeration ever runs. THE STRUCTURAL ARM ("cannot
#: discriminate among the candidates") IS THE LOAD-BEARING PREDICATE; any
#: recalibration moves this floor, never the structural arm's semantics
#: (PORTFOLIO_REVIEW F12 ruling).
#:
#: RECALIBRATED 25 -> 14 during implementation, per the design's own rule
#: ("if implementation finds a second sub-floor quote that IS
#: discriminating, the floor moves down, not the refusal semantics").
#: The design's 25 was calibrated on the PUBLISHED 863-passage set; the
#: TRUE 589-locator universe holds EIGHT sub-25 normalized quotes, of which
#: seven discriminate perfectly (one in-section clause each; 14-24 chars,
#: one of them reference-grade) and only the header-only offender
#: (`!!! meta "Commentary"`, 21 chars) does not — and no floor separates 21
#: from 21, so the offender is caught by the structural arm post-restriction
#: instead. 14 is the largest floor sparing every measured discriminating
#: quote ('Sending emails', 14 chars, is the shortest). Pinned in
#: test_join_v2.py; evidence in cycles/join-integrity-v2-2026-08-04/measure/.
DEGENERATE_QUOTE_FLOOR = 14

#: The machine-readable refusal flag `benchmark.map_reference` records as a
#: stratum, so the accounting identity "strata sum equals unmatched" holds.
DEGENERATE_QUOTE_FLAG = "degenerate_quote_refused"

#: Segmentation option 1: per-link independent renderings, bounded so the
#: join stays linear in practice — beyond this many variants (2^3 links) the
#: set falls back to the uniform pair (current behavior).
MIXED_VARIANT_CAP = 8

#: Panel locator grammar: `model-spec@2025-12-18 > #<anchor> > ¶<n>`. No
#: fuzzy matching anywhere downstream: the anchor either equals a clause
#: `section_id` string or restriction does not apply.
_PANEL_ANCHOR = re.compile(r">\s*#([A-Za-z0-9_-]+)\s*>")


def locator_anchor(locator) -> str | None:
    """Section anchor from a panel passage locator, or None."""
    m = _PANEL_ANCHOR.search(locator or "")
    return m.group(1) if m else None


def _variants_mixed(s: str, cap: int = MIXED_VARIANT_CAP) -> set:
    """Every per-link choice of rendering (text vs target), bounded.

    The panel's renderer chose PER LINK, not per passage — a passage mixing
    renderings across two links defeats both uniform `_variants` (the seven
    zero-match locators of SEGMENTATION_GAPS_DESIGN §1, all in link-dense
    paragraphs). Beyond `cap` variants the explosion is refused and the
    uniform pair is returned — the pre-option-1 behavior, disclosed by the
    bound being a named constant rather than silently truncated.
    """
    s = FOOTNOTE_MARKER.sub("", s or "")
    n = len(_LINK.findall(s))
    if n == 0 or 2 ** n > cap:
        return {" ".join(_EMPH.sub("", _LINK.sub(lambda m: m.group(k), s))
                         .split()) for k in (1, 2)}
    out = set()
    for mask in range(2 ** n):
        i = [0]

        def pick(m, mask=mask, i=i):
            k = 2 if (mask >> i[0]) & 1 else 1
            i[0] += 1
            return m.group(k)

        out.add(" ".join(_EMPH.sub("", _LINK.sub(pick, s)).split()))
    return out


def content_empty(row: dict) -> bool:
    """The F9 CODE-SIDE predicate (SEGMENTATION_GAPS_DESIGN §4, as amended
    per PORTFOLIO_REVIEW F9): a content-free pseudo-heading clause — kind
    `meta` AND heading-shaped text (a bold-wrapped heading, or a short
    trailing-colon noun phrase with no sentence punctuation). Computed here
    so `modelspec_clauses.json` is never edited (no artifact re-freeze
    mid-spine). Membership on the current artifact is pinned by test to
    exactly {m0393, m0398, m0535, m0539}.
    """
    if (row.get("kind") or "") != "meta":
        return False
    t = (row.get("quote") or "").strip()
    if re.fullmatch(r"\*\*[^*\n]+\*\*", t):
        return True
    return (t.endswith(":") and "," not in t
            and not any(c in t for c in ".!?")
            and len(t.split()) <= 4)


def match_passage_v2(passage_quote: str, rows, locator: str = "",
                     mixed_variants: bool = False) -> dict:
    """Join v2: `match_passage`'s containment rule behind two independent
    guards (JOIN_INTEGRITY_DESIGN §2) plus the F9 empty-meta skip and
    segmentation option 1's mixed variant set.

    Returns a dict, never a bare list — the refusal and the restriction
    fallback are facts the caller must see:
      clauses       matched rows, in row order (empty on refusal);
      restricted    True iff the candidate set was locator-restricted;
                    False is the DISCLOSED full-corpus fallback, never silent;
      refused       True iff the quote failed a degeneracy arm;
      flag          `degenerate_quote_refused` on refusal, else None;
      join_version  2.

    `mixed_variants=False` isolates the restriction+refusal lever over the
    uniform variant set — the two cycles (P1 join-integrity, P2 segmentation
    option 1) check their §3 predictions independently on it.

    The DEFAULT is False: the measured, pinned state (pinned by
    test_join_v2.py). True selects segmentation option 1's per-link mixed
    variant set, which has never been opened, measured, or adjudicated —
    it is OPT-IN and must be passed explicitly, never inherited silently.
    """
    var = _variants_mixed if mixed_variants else _variants
    result = {"clauses": [], "restricted": False, "refused": False,
              "flag": None, "join_version": JOIN_VERSION_V2}
    # 2b backstop arm — refuse pathological quotes before enumeration.
    if len(_norm(passage_quote)) < DEGENERATE_QUOTE_FLOOR:
        result["refused"] = True
        result["flag"] = DEGENERATE_QUOTE_FLAG
        return result
    ps = {v for v in var(passage_quote) if v}
    if not ps:
        return result
    # F9: content-empty pseudo-headings are never candidates.
    candidates = [r for r in rows if not content_empty(r)]
    # 2a: locator-restricted candidate set, exact anchor equality only.
    anchor = locator_anchor(locator)
    if anchor is not None and any(r.get("section_id") == anchor
                                  for r in candidates):
        candidates = [r for r in candidates if r.get("section_id") == anchor]
        result["restricted"] = True
    matched, proper_only = [], []
    for r in candidates:
        qs = {v for v in var(r["quote"]) if v}
        spans = {v for v in var(r.get("marked_span")) if v}
        clause_in_passage = any(q in p for q in qs for p in ps) \
            or any(s in p for s in spans for p in ps)
        passage_in_clause = any(p in q for q in qs for p in ps)
        if clause_in_passage or passage_in_clause:
            matched.append(r)
            proper_only.append(passage_in_clause and not clause_in_passage)
    # 2b structural arm (LOAD-BEARING): a quote that is a proper substring of
    # every one of several candidates cannot discriminate among them.
    if len(matched) > 1 and all(proper_only):
        result["refused"] = True
        result["flag"] = DEGENERATE_QUOTE_FLAG
        return result
    result["clauses"] = matched
    return result


def _row(raw: dict) -> dict:
    return {
        "id": asp_id(raw["focus_id"]),
        "source_id": raw["focus_id"],
        "locator": make_locator(raw["section_path"], raw["line"], raw["focus_id"]),
        "quote": raw["text"],
        "marked_span": raw["marked_span"],
        "kind": raw["kind"],
        "modality": list(raw.get("modality") or []),
        "has_defeater": bool(raw.get("has_defeater")),
    }


def load_raw(path: str = FOCUS_AREAS) -> list:
    with open(path) as f:
        return json.load(f)


def load_section(name: str = DEFAULT_SECTION, path: str = FOCUS_AREAS) -> list:
    """All focus-area rows whose `top_level_section` is `name`, in file order."""
    return [_row(r) for r in load_raw(path) if r.get("top_level_section") == name]


def load_all(path: str = FOCUS_AREAS) -> list:
    """Every focus area in the document, not just one section — the scope
    locator uniqueness has to hold over."""
    return [_row(r) for r in load_raw(path)]


def conditional(rows) -> list:
    return [r for r in rows if r["kind"] == "conditional"]


def spec_text(path: str = SPEC_MD) -> str:
    with open(path) as f:
        return f.read()


def verify(rows, spec_path: str = SPEC_MD) -> bool:
    """Assert every quote (and every non-null marked_span) is an exact
    substring of the Model Spec source, and every id is a legal ASP constant.
    Raises AssertionError naming the first offender; returns True on success."""
    text = spec_text(spec_path)
    for r in rows:
        assert ID_RE.match(r["id"]), f"{r['id']!r} is not a legal ASP constant"
        assert r["quote"] in text, f"{r['id']}: quote not found verbatim in {spec_path}"
        if r["marked_span"] is not None:
            assert r["marked_span"] in text, (
                f"{r['id']}: marked_span not found verbatim in {spec_path}"
            )
    return True


def summarize(rows) -> dict:
    from collections import Counter

    cond = conditional(rows)
    mods = Counter(m for r in cond for m in r["modality"])
    return {
        "rows": len(rows),
        "conditional": len(cond),
        "kinds": dict(Counter(r["kind"] for r in rows)),
        "modality_on_conditional": dict(mods),
        "conditional_with_defeater": sum(1 for r in cond if r["has_defeater"]),
        "illegal_source_ids": sum(
            1 for r in rows if not ID_RE.match(r["source_id"])
        ),
    }


def main():
    rows = load_section()
    verify(rows)
    print(json.dumps(summarize(rows), indent=1))


if __name__ == "__main__":
    main()
