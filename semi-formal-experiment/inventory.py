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
