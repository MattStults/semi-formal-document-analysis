"""The TRUE judged universe — every passage the panel actually graded.

WHY THIS MODULE EXISTS
----------------------
The panel did not score a candidate list. `engine/panel/whole_doc.py` put the
ENTIRE spec into ONE prompt as numbered passages and demanded a verdict for
every one:

    ps = h.passages(spec)                       # 589 for the model spec
    body = "\\n".join(f"[{i+1}] (§ {sec}) {t}" for ...)
    ... "Output {len(ps)} verdict lines."

Every judge therefore emitted 589 verdicts per behaviour. Then
`engine/panel/build_site_data.py` published only the survivors of

    def keeps_citation(score, n_votes, panel_size):
        return score >= 1 and n_votes >= min(2, panel_size)

so every passage whose SUMMED score was 0 — i.e. every passage all three
judges called irrelevant — was deleted before the file was written. The
published model-spec lists hold 377 / 333 / 153 passages; 212 / 256 / 436
true negatives are missing.

Those deletions are not neutral:

  * they are gold-NEGATIVE by construction (no judge scored them), and
  * they are CORRECTLY PREDICTED NEGATIVE by every judge.

So the deletion removes true-negative credit the judges earned, and it does so
asymmetrically: the tool never earned that credit either, but the tool's
false positives on those passages were invisible as well. Measured on the real
data, restoring the universe moves the judges' mean MCC +0.394 -> +0.555 and
the tool's only +0.274 -> +0.320.

It also invalidates the standard defence of MCC on this project ("MCC is
sensitive to true negatives, so it is robust here"): the true negatives had
been deleted upstream, so MCC was being computed on a universe with almost no
true negatives left to be sensitive to.

WHAT IT RECONSTRUCTS
--------------------
For each (behaviour, spec) it rebuilds the full passage list the judges saw,
with per-judge verdicts, where a passage absent from the published
`behaviours.json` carries verdict 0 from EVERY judge. The passage list comes
from the same function the panel used — `harness.passages(spec)`, imported by
path exactly as `whole_doc.py` imports it — so the reconstruction cannot drift
from what was prompted.

The output is site-shaped: `benchmark.passages/judges/pair_targets/...` read it
unchanged. Passage ids are re-keyed to LOCATORS (the published ids are
positional — `openai-helpfulness-panel-7` — and only exist for surviving rows,
so they cannot name a recovered passage).

Spec-swappable by construction: `spec_keys` is a parameter and the constitution
side (`anthropic` / 374 passages) loads through the identical code path.

Nothing here calls a model.
"""
from __future__ import annotations

import importlib.util
import os

MVP = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
PANEL_DIR = os.path.join(MVP, "engine", "panel")

#: site coverage key -> the spec key `harness.passages` takes.
SPEC_OF_KEY = {"openai": "model-spec", "anthropic": "constitution"}

#: What the panel prompt contained. Asserted, not trusted: if `cite.py` or the
#: spec markdown changes under us, the reconstruction is no longer the universe
#: the judges saw and every number below it is wrong. Fail loudly instead.
EXPECTED_SIZE = {"model-spec": 589, "constitution": 374}


class UnjoinablePassage(Exception):
    """A published passage that matches no passage in the reconstructed
    universe. This is a hard error: silently dropping it would delete a real
    judged verdict, which is the very defect this module exists to fix."""


# ------------------------------------------------------ the mvp panel code

def _load_by_path(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_HARNESS = None


def harness():
    """`engine/panel/harness.py`, imported by path — the same way whole_doc.py
    does it. Cached: it reads the spec markdown off disk on import."""
    global _HARNESS
    if _HARNESS is None:
        _HARNESS = _load_by_path("panel_harness",
                                 os.path.join(PANEL_DIR, "harness.py"))
    return _HARNESS


def _mvp_build_site_data():
    """The publisher, for fidelity checks only. Not used at runtime — this
    module carries its own copy of the quote rule (see `citation_quote`) so a
    missing mvp checkout degrades to an import error in ONE place."""
    return _load_by_path("panel_build_site_data",
                         os.path.join(PANEL_DIR, "build_site_data.py"))


_PASSAGES: dict = {}


def spec_passages(spec: str) -> list:
    """`[(locator, section, text)]` for the whole spec — THE UNIVERSE.

    Asserts the expected size for known specs so a silent re-segmentation of
    the source document cannot slip a different universe through.
    """
    if spec not in _PASSAGES:
        ps = harness().passages(spec)
        want = EXPECTED_SIZE.get(spec)
        if want is not None and len(ps) != want:
            raise AssertionError(
                f"{spec}: reconstructed universe is {len(ps)} passages, "
                f"expected {want}. The panel prompt contained {want}; a "
                f"different number means the spec or cite.segment_blocks "
                f"changed and this is no longer the judged universe.")
        _PASSAGES[spec] = ps
    return _PASSAGES[spec]


def spec_for_key(spec_key: str) -> str:
    """Coverage key -> spec name. Raises for an unknown key: a passthrough
    would quietly leave that side on the published (broken) universe."""
    return SPEC_OF_KEY[spec_key]


# ------------------------------------------------------------ the quote rule

def clean_quote(text: str) -> str:
    """Verbatim copy of `build_site_data.clean_quote`."""
    return text.replace("**", "")


def citation_quote(text: str):
    """Verbatim copy of `build_site_data.citation_quote` — `(quote, is_example)`.

    Fenced example blocks render as code the anchor matcher cannot see, so the
    quote is the caption line before the fence and a flag extends the highlight.
    `test_local_citation_quote_matches_the_mvp_builder_on_every_passage` pins
    this copy against the original on all 589 passages.
    """
    if "~~~" in text:
        caption = clean_quote(text.split("~~~")[0].strip())
        if caption:
            return caption, True
    return clean_quote(text), False


# ---------------------------------------------------------- reconstruction

SYM = {2: "✓", 1: "~", 0: "✗"}
WORD = {2: "core", 1: "related", 0: "not relevant"}


def _role_text(verdicts, labels, n_judges) -> str:
    """The `role` free text, in the publisher's format. Recovered rows need one
    because `benchmark.panel_judge_names` / `verify_role_parse` read judges out
    of it as a cross-check on the structured `verdicts` field; a row with no
    role would make that cross-check silently weaker."""
    lines = "\n".join(f"{SYM[v]} {labels.get(m, m)} — {WORD[v]}"
                      for m, v in sorted(verdicts.items(), key=lambda x: -x[1]))
    score = sum(verdicts.values())
    return f"Model determined relevance (score {score}/{2 * n_judges}):\n{lines}"


def _judge_labels(published) -> dict:
    """`{verdicts key: display name}`, read off the published rows' role text.

    Read, never hardcoded: THE PANEL DIFFERS PER BEHAVIOUR (helpfulness uses
    Claude Fable 5, harm-avoidance Claude Opus 4.8, over/under-caution
    Kimi-K2.6).
    """
    import benchmark  # local import: benchmark imports nothing from here
    out = {}
    for p in published:
        names = []
        for line in (p.get("role") or "").split("\n")[1:]:
            m = benchmark.JUDGE_LINE.match(line.strip())
            if m:
                names.append(m.group(1).strip())
        for key in (p.get("verdicts") or {}):
            for n in names:
                if key.lower() in n.lower():
                    out.setdefault(key, n)
    return out


def recover_behaviour(behaviour: dict, spec_key: str) -> tuple:
    """`(behaviour with the FULL universe on `spec_key`, provenance)`.

    The input behaviour is not mutated. Published rows are carried through
    untouched apart from the id re-key (`published_id` keeps the original);
    absent rows are synthesised with verdict 0 from every judge.
    """
    spec = spec_for_key(spec_key)
    cov = ((behaviour.get("coverage") or {}).get(spec_key) or {})
    published = list(cov.get("passages") or [])
    universe = spec_passages(spec)
    locs = {loc for loc, _, _ in universe}

    # DUPLICATE LOCATORS. `by_loc` below is last-wins, so two published rows
    # sharing a locator silently discard one — a JUDGED VERDICT, exactly what
    # UnjoinablePassage exists to prevent. Demonstrated: duplicating one
    # locator with opposite verdicts turned a unanimous-core gold passage
    # gold-negative while provenance still reported a perfect join.
    # Multiplicity drops a verdict as thoroughly as non-membership does.
    from collections import Counter
    dupes = sorted(l for l, n in Counter(
        p.get("locator") for p in published).items() if n > 1)
    if dupes:
        raise UnjoinablePassage(
            f"{behaviour.get('slug')}/{spec_key}: {len(dupes)} locator(s) "
            f"appear on more than one published passage, so a judged verdict "
            f"would be silently overwritten. First: {dupes[:3]}")

    # ROW count, not distinct-locator count. Dividing a distinct-locator
    # numerator by a row denominator under-reports breakage by the duplication
    # factor: 50 rows sharing one bad locator reported join_rate 0.997 when the
    # truth was 0.868.
    unjoined_rows = [p for p in published if p.get("locator") not in locs]
    unjoined = sorted({p.get("locator") for p in unjoined_rows})
    if unjoined:
        raise UnjoinablePassage(
            f"{behaviour.get('slug')}/{spec_key}: {len(unjoined)} of "
            f"{len(published)} published passages join to no passage in the "
            f"{spec} universe ({len(universe)}). First: {unjoined[:3]}. "
            f"Refusing to reconstruct — an unjoined published passage is a "
            f"judged verdict about to be dropped.")

    by_loc = {p["locator"]: p for p in published}
    judge_keys = sorted({k for p in published
                         for k in (p.get("verdicts") or {})})
    labels = _judge_labels(published)

    rows = []
    for loc, _section, text in universe:
        pub = by_loc.get(loc)
        if pub is not None:
            row = dict(pub)
            row["published_id"] = pub.get("id")
            row["id"] = loc
            row["recovered"] = False
        else:
            quote, is_example = citation_quote(text)
            verdicts = {k: 0 for k in judge_keys}
            row = {
                "id": loc, "published_id": None, "locator": loc,
                "quote": quote, "exampleBlock": is_example,
                "verdicts": verdicts, "score": 0, "adjacent": True,
                "role": _role_text(verdicts, labels, len(judge_keys)),
                "recovered": True,
            }
        rows.append(row)

    out = dict(behaviour)
    out["coverage"] = {k: dict(v) for k, v in (behaviour.get("coverage") or {}).items()}
    out["coverage"].setdefault(spec_key, {})
    out["coverage"][spec_key] = dict(out["coverage"][spec_key])
    out["coverage"][spec_key]["passages"] = rows
    out["coverage"][spec_key]["universe"] = "true"

    prov = {
        "slug": behaviour.get("slug"), "spec_key": spec_key, "spec": spec,
        "universe": len(universe), "published": len(published),
        "recovered_zero": max(0, len(universe) - len(published)),
        "join_rate": (len(published) - len(unjoined_rows)) / len(published)
                     if published else 1.0,
        "unjoined": unjoined, "judges": judge_keys,
    }
    return out, prov


def load_universe(path=None, spec_keys=("openai", "anthropic"),
                  with_provenance: bool = False):
    """`{slug: behaviour}` on the TRUE universe, for every requested spec key.

    A spec key not listed is left exactly as published — so a caller can hold
    one side fixed for a like-for-like comparison — but the DEFAULT is both
    sides recovered, because the published universe is the broken one.
    """
    import benchmark
    panel = benchmark.load_panel(path or benchmark.PANEL)
    out, prov = {}, {}
    for slug, b in panel.items():
        for key in spec_keys:
            if key not in (b.get("coverage") or {}):
                continue
            b, p = recover_behaviour(b, key)
            prov[(slug, key)] = p
        out[slug] = b
    return (out, prov) if with_provenance else out


# ------------------------------------------------------------- provenance

def provenance_block(prov: dict) -> str:
    """Markdown. Every number a reader needs to check the reconstruction."""
    lines = [
        "## Judged universe — reconstruction provenance",
        "",
        "The panel graded EVERY passage of the spec in one prompt; "
        "`build_site_data.keeps_citation` then dropped every passage whose "
        "summed score was 0 before publishing. Those rows are gold-negative "
        "AND unanimously predicted negative, so restoring them restores "
        "true-negative credit rather than inventing any. Recovered rows carry "
        "verdict 0 from every judge.",
        "",
        "| behaviour | spec | universe | published | recovered as 0 | join rate |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for (slug, key), p in sorted(prov.items()):
        lines.append(
            f"| {slug} | {p['spec']} ({key}) | {p['universe']} | "
            f"{p['published']} | {p['recovered_zero']} "
            f"({p['recovered_zero'] / p['universe']:.0%}) | "
            f"{p['join_rate']:.3f} |")
    bad = {k: p["unjoined"] for k, p in prov.items() if p["unjoined"]}
    lines.append("")
    lines.append(f"unjoined published passages: **{sum(len(v) for v in bad.values())}**"
                 + (f" — {bad}" if bad else " (every published passage joins)"))
    lines.append("")
    return "\n".join(lines)
