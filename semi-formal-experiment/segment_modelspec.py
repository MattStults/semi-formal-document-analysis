"""Full-document segmentation of the OpenAI Model Spec into addressable clauses.

Why this exists
---------------
The 259 `[^xxxx]` focus-area markers OpenAI ships reach only ~19% of the
document's characters and appear *nowhere* inside the 183 `~~~xml` example
blocks. The benchmark panel, however, puts 38% of its high-consensus Model Spec
judgments on example blocks. A relevance tool driven by focus areas therefore
cannot reach a third of what it is graded on. This module segments the whole
file structurally instead, so focus areas become a privileged *subset*
(`focus_ids`) rather than the addressing scheme. The same parser runs on
Anthropic's constitution, which carries no markers at all.

Unit model (one clause per unit)
--------------------------------
* paragraph            - a blank-line-delimited run of body text
* list item            - each bullet / numbered item, at any nesting depth,
                         plus any lazy (unblanked) continuation lines
* example block        - the `**Example**: <caption>` line through the closing
                         `~~~`, kept as ONE clause (see below)
* commentary paragraph - each paragraph inside a `!!! meta "Commentary"` block

`¶` numbering restarts at each heading and counts units in document order.
This reproduces the panel's own numbering (validated in `validate_panel()`).

Example blocks: one clause, not one per turn
--------------------------------------------
All 313 example-block passages in the panel set quote the *caption line* only
("Example: ambiguous message from user, ..."), never a turn body, and the panel
numbered each block as a single `¶`. Splitting per turn would put the caption in
a clause of its own and scatter the conversation across ~6 more, none of which
any panel passage could ever hit; a GOOD/BAD `<comparison>` is also only
meaningful whole. So: caption + fence = one clause, `kind="example"`.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC_MD = os.path.join(HERE, "external", "model_spec", "model_spec.md")
OUT_JSON = os.path.join(HERE, "modelspec_clauses.json")
SPEC_VERSION = "model_spec@2025-12-18"

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
ATTR_RE = re.compile(r"\{#([A-Za-z0-9_\-]+)([^}]*)\}\s*$")
BULLET_RE = re.compile(r"^(\s*)(?:[-*+]|\d+[.)])\s+")
FOCUS_RE = re.compile(r"\[\^([a-z0-9]+)\]")
ADMONITION_RE = re.compile(r'^!!!\s+\w+(\s+".*")?\s*$')
CAPTION_RE = re.compile(r"^\*\*Example[^*]*\*\*")


class Unit:
    __slots__ = ("start", "end", "text", "utype", "section", "line")

    def __init__(self, start, end, text, utype, section, line):
        self.start, self.end = start, end          # line indices [start, end)
        self.text = text                            # verbatim quote
        self.utype = utype                          # paragraph|list_item|example|commentary
        self.section = section                      # (path tuple, anchor)
        self.line = line                            # 1-based first line


def read_spec(path: str = SPEC_MD) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def parse_heading(line: str):
    """-> (level, title, anchor) or None."""
    m = HEADING_RE.match(line)
    if not m:
        return None
    level, rest = len(m.group(1)), m.group(2)
    anchor = None
    a = ATTR_RE.search(rest)
    if a:
        anchor = a.group(1)
        rest = rest[: a.start()].rstrip()
    return level, rest, anchor


def segment(text: str):
    """Structural walk -> list[Unit] covering every non-structural line."""
    lines = text.split("\n")
    units: list[Unit] = []
    stack: list[tuple[int, str, str | None]] = []   # (level, title, anchor)
    i, n = 0, len(lines)

    def section():
        return (tuple(t for _, t, _ in stack), stack[-1][2] if stack else None)

    def emit(start, end, utype, quote=None):
        raw = "\n".join(lines[start:end])
        q = raw if quote is None else quote
        units.append(Unit(start, end, q, utype, section(), start + 1))

    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
            continue

        h = parse_heading(line)
        if h:
            level, title, anchor = h
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, title, anchor))
            i += 1
            continue

        # --- example block: optional caption line, then ~~~xml ... ~~~
        if line.strip() == "~~~xml":
            j = i + 1
            while j < n and lines[j].strip() != "~~~":
                j += 1
            j += 1                                   # past closing fence
            start = i
            # absorb a caption immediately above (blank line between allowed)
            k = i - 1
            while k >= 0 and not lines[k].strip():
                k -= 1
            if k >= 0 and CAPTION_RE.match(lines[k].strip()) and units and units[-1].start == k:
                units.pop()
                start = k
            emit(start, j, "example")
            i = j
            continue

        # --- commentary admonition: marker line + 4-space indented body.
        # Kept as ONE unit (marker line included) because the panel numbers and
        # quotes it that way, e.g. '#refusal_style > ¶4' == '!!! meta
        # "Commentary" We have updated our models ...'.
        if ADMONITION_RE.match(line.strip()) and line.startswith("!!!"):
            j, last = i + 1, i + 1
            while j < n:
                if not lines[j].strip():
                    j += 1
                    continue
                if not lines[j].startswith("    "):
                    break
                j += 1
                last = j
            emit(i, last, "commentary")
            i = last
            continue

        i = _emit_body(lines, i, n, emit, "paragraph")

    return units


def _strip_marker(s: str) -> str:
    """Drop the bullet/number marker and indentation; still a source substring."""
    m = BULLET_RE.match(s)
    return s[m.end():] if m else s.strip()


def _emit_body(lines, i, n, emit, kind_default):
    """Emit one body unit starting at line i; return the next index."""
    if BULLET_RE.match(lines[i]):
        j = i + 1
        while j < n and lines[j].strip() and not BULLET_RE.match(lines[j]) \
                and lines[j].strip() != "~~~xml" and not parse_heading(lines[j]):
            j += 1
        raw = "\n".join(lines[i:j])
        emit(i, j, "list_item", quote=_strip_marker(lines[i]) if j == i + 1
             else raw[len(lines[i]) - len(_strip_marker(lines[i])):])
        return j
    j = i + 1
    while j < n and lines[j].strip() and not BULLET_RE.match(lines[j]) \
            and lines[j].strip() != "~~~xml" and not parse_heading(lines[j]) \
            and not lines[j].strip().startswith("!!!"):
        j += 1
    raw = "\n".join(lines[i:j])
    quote = lines[i].strip() if j == i + 1 else raw[len(lines[i]) - len(lines[i].lstrip()):].rstrip()
    emit(i, j, kind_default, quote=quote)
    return j


def build(text: str, kinds: dict[str, str] | None = None):
    units = segment(text)
    kinds = kinds or {}
    clauses = []
    para_no: Counter = Counter()
    for idx, u in enumerate(units, 1):
        path, anchor = u.section
        para_no[path] += 1
        cid = "m%04d" % idx
        locator = "%s > %s > ¶%d" % (SPEC_VERSION, " > ".join(path), para_no[path])
        clauses.append({
            "id": cid,
            "locator": locator,
            "section_path": list(path),
            "section_id": anchor,
            "quote": u.text,
            "kind": kinds.get(cid, "example" if u.utype == "example" else None),
            "in_example_block": u.utype == "example",
            "focus_ids": ["fa_" + m for m in FOCUS_RE.findall(u.text)],
            "line": u.line,
        })
    return clauses


# ----------------------------------------------------------------- validation

def verify(clauses, text):
    bad = [c["id"] for c in clauses if c["quote"] not in text]
    locs = Counter(c["locator"] for c in clauses)
    dupes = {k: v for k, v in locs.items() if v > 1}
    all_markers = set(FOCUS_RE.findall(text))
    covered = {f[3:] for c in clauses for f in c["focus_ids"]}
    return {
        "clauses": len(clauses),
        "verbatim_pass": len(clauses) - len(bad),
        "verbatim_fail": bad[:10],
        "duplicate_locators": dict(list(dupes.items())[:10]),
        "n_duplicate_locators": len(dupes),
        "markers_in_source": len(all_markers),
        "markers_covered": len(covered & all_markers),
        "markers_missing": sorted(all_markers - covered)[:10],
        "quote_chars": sum(len(c["quote"]) for c in clauses),
        "source_chars": len(text),
    }


def accounting(text):
    """Char-level accounting of what is *not* inside a clause quote.

    Every character of the source is either inside a clause quote, or is one of
    a small set of structural tokens (heading lines, blank lines, list bullet
    markers, block indentation). Nothing is silently dropped.
    """
    lines = text.split("\n")
    units = segment(text)
    inside = [False] * len(lines)
    lost = Counter()
    for u in units:
        for i in range(u.start, u.end):
            inside[i] = True
        raw = "\n".join(lines[u.start:u.end])
        k = raw.find(u.text)
        assert k >= 0, u.line
        pre, suf = raw[:k], raw[k + len(u.text):]
        if pre:
            lost["bullet marker / indentation" if pre.strip() else "indentation"] += len(pre)
        if suf:
            lost["trailing"] += len(suf)
    for i, ln in enumerate(lines):
        if inside[i]:
            continue
        if not ln.strip():
            lost["blank line"] += len(ln) + 1
        elif parse_heading(ln):
            lost["heading line (preserved in section_path/section_id)"] += len(ln) + 1
        else:
            lost["UNACCOUNTED: " + repr(ln[:60])] += len(ln) + 1
    lost["line separators between/around units"] = (
        len(text) - sum(len(u.text) for u in units) - sum(lost.values()))
    return dict(lost)


def main():
    text = read_spec()
    kinds = {}
    kp = os.path.join(HERE, "modelspec_kinds.json")
    if os.path.exists(kp):
        kinds = json.load(open(kp))
    clauses = build(text, kinds)
    rep = verify(clauses, text)
    rep["char_coverage_pct"] = round(100 * rep["quote_chars"] / rep["source_chars"], 2)
    rep["kinds"] = dict(Counter(c["kind"] for c in clauses))
    rep["clauses_with_focus_ids"] = sum(1 for c in clauses if c["focus_ids"])
    rep["uncovered_chars"] = accounting(text)
    print(json.dumps(rep, indent=1, ensure_ascii=False))
    assert not rep["verbatim_fail"], "verbatim guarantee violated"
    assert rep["n_duplicate_locators"] == 0, "duplicate locators"
    assert rep["markers_covered"] == 259, "focus-marker cross-check failed"
    assert None not in rep["kinds"], "some clauses have no hand-assigned kind"
    assert not [k for k in rep["uncovered_chars"] if k.startswith("UNACCOUNTED")]
    out = {
        "spec": SPEC_VERSION,
        "source_sha256": hashlib.sha256(open(SPEC_MD, "rb").read()).hexdigest(),
        "clauses": clauses,
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("wrote", OUT_JSON)


if __name__ == "__main__":
    main()
