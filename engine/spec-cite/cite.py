#!/usr/bin/env python3
"""spec-cite: resolve and verify precise citations into the mirrored specs.

Locator grammar (canonical form, see specs/CITATION.md):

    <spec>@<version> > <section-ref> > ¶<n>[ s<a>[-<b>]]
    <spec>@<version> > <section-ref> > ¶<n> s<a> - ¶<m> s<b>

  spec         constitution | model-spec
  section-ref  #anchor (model-spec) or heading path "Chapter > Section" (constitution)
  ¶<n>         block number within the section's direct span ("p<n>" also accepted)
  s<a>[-<b>]   sentence (range) within the block; omit for the whole block

  ">" and "›" are interchangeable path separators.

Commands:
    cite.py outline <spec>[@<version>]
    cite.py show    "<spec>[@<version>] > <section-ref>"
    cite.py resolve "<locator>"
    cite.py find    <spec>[@<version>] "<text>"
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

SPECS = {
    ("constitution", "2026-01-20"): "specs/claude-constitution/20260120-constitution.md",
    ("model-spec", "2025-12-18"): "specs/openai-model-spec/model_spec.md",
}
DEFAULT_VERSION = {"constitution": "2026-01-20", "model-spec": "2025-12-18"}

HEADING_RE = re.compile(
    r"^(#{1,6})\s+(.*?)\s*(?:\{#([A-Za-z0-9_-]+)(?:\s+authority=\S+)?\})?\s*$"
)
FENCE_RE = re.compile(r"^(```|~~~)")
LIST_ITEM_RE = re.compile(r"^([-*+]|\d+[.)])\s+")
FOOTNOTE_RE = re.compile(r"\[\^[^\]]+\]")
XREF_RE = re.compile(r"\[\?\]\((#[A-Za-z0-9_-]+)\)")
LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")

# Tokens that end with "." but do not terminate a sentence.
ABBREVIATIONS = {
    "e.g", "i.e", "etc", "vs", "cf", "al", "approx", "no", "vol",
    "dr", "mr", "mrs", "ms", "st", "jr", "sr", "u.s", "u.k",
}


def normalize(text):
    """Mechanical normalization applied to excerpt text (see CITATION.md)."""
    text = FOOTNOTE_RE.sub("", text)
    text = XREF_RE.sub(r"\1", text)
    text = LINK_RE.sub(r"\1", text)
    text = LIST_ITEM_RE.sub("", text)  # leading bullet/number is syntax, not content
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def match_normalize(text):
    """Extra folding used only for `find` matching, never for output."""
    text = normalize(text)
    for a, b in [("‘", "'"), ("’", "'"), ("“", '"'), ("”", '"'),
                 ("—", "---"), ("–", "--"), ("…", "...")]:
        text = text.replace(a, b)
    text = re.sub(r"-{2,}", "-", text)
    text = re.sub(r"\s+", " ", text)
    return text


class Section:
    def __init__(self, level, title, anchor, path, start):
        self.level = level
        self.title = title
        self.anchor = anchor
        self.path = path  # tuple of ancestor titles, self included
        self.start = start  # first line after the heading
        self.end = None  # line of the next heading (any level) or EOF
        self.blocks = None

    @property
    def path_str(self):
        return " > ".join(self.path)


def parse_sections(lines):
    sections = []
    stack = []  # (level, title)
    in_fence = None
    for i, line in enumerate(lines):
        fence = FENCE_RE.match(line)
        if fence:
            if in_fence is None:
                in_fence = fence.group(1)
            elif line.startswith(in_fence):
                in_fence = None
            continue
        if in_fence:
            continue
        m = HEADING_RE.match(line)
        if m and not line.startswith("#!"):
            level = len(m.group(1))
            title = re.sub(r"\s+", " ", m.group(2)).strip()
            for s in sections:
                if s.end is None:
                    s.end = i
            stack = [(lv, t) for lv, t in stack if lv < level]
            stack.append((level, title))
            sections.append(
                Section(level, title, m.group(3), tuple(t for _, t in stack), i + 1)
            )
    for s in sections:
        if s.end is None:
            s.end = len(lines)
    return sections


def segment_blocks(lines, start, end):
    """Blocks in a section's direct span. Returns list of raw-text strings."""
    blocks = []
    cur = []
    in_fence = None

    def flush():
        nonlocal cur
        if cur:
            blocks.append("\n".join(cur))
            cur = []

    i = start
    while i < end:
        line = lines[i]
        fence = FENCE_RE.match(line)
        if fence and in_fence is None:
            # A fenced block: attach to a preceding **Example**: caption block.
            flush()
            fence_lines = [line]
            marker = fence.group(1)
            i += 1
            while i < end:
                fence_lines.append(lines[i])
                if lines[i].startswith(marker):
                    break
                i += 1
            fenced = "\n".join(fence_lines)
            if blocks and re.match(r"^\*\*Example\*\*", blocks[-1]):
                blocks[-1] = blocks[-1] + "\n\n" + fenced
            else:
                blocks.append(fenced)
            i += 1
            continue
        if not line.strip():
            flush()
        elif LIST_ITEM_RE.match(line):
            flush()  # each top-level list item starts a block
            cur.append(line)
        elif line[:1].isspace() or cur:
            cur.append(line)  # continuation (incl. nested list content)
        else:
            cur.append(line)
        i += 1
    flush()
    return blocks


def split_sentences(text):
    """Deterministic sentence split on normalized prose (see CITATION.md)."""
    sentences = []
    buf = ""
    i = 0
    n = len(text)
    while i < n:
        buf += text[i]
        if text[i] in ".!?":
            j = i + 1
            closers = ""
            while j < n and text[j] in "\"'’”)]":
                closers += text[j]
                j += 1
            if j >= n:
                buf += closers
                i = j
                break
            if text[j] == " " and j + 1 < n:
                nxt = text[j + 1]
                tail = re.split(r"[\s(]", buf.rstrip(".!?"))[-1]
                is_abbrev = text[i] == "." and tail.lower() in ABBREVIATIONS
                opens = nxt.isupper() or nxt.isdigit() or nxt in "\"'‘“([*#"
                if opens and not is_abbrev:
                    sentences.append((buf + closers).strip())
                    buf = ""
                    i = j  # closers and the space are consumed
        i += 1
    if buf.strip():
        sentences.append(buf.strip())
    return sentences


def load_spec(spec, version):
    version = version or DEFAULT_VERSION.get(spec)
    path = SPECS.get((spec, version))
    if not path:
        known = ", ".join(f"{s}@{v}" for s, v in SPECS)
        sys.exit(f"unknown spec '{spec}@{version}' (known: {known})")
    lines = (REPO_ROOT / path).read_text(encoding="utf-8").splitlines()
    return version, parse_sections(lines), lines


def find_section(sections, ref):
    ref = ref.strip()
    if ref.startswith("#"):
        hits = [s for s in sections if s.anchor == ref[1:]]
    else:
        parts = tuple(p.strip().lower() for p in re.split(r"\s*[>›]\s*", ref))
        hits = [
            s for s in sections
            if tuple(t.lower() for t in s.path[-len(parts):]) == parts
        ]
    if not hits:
        sys.exit(f"section not found: {ref}")
    if len(hits) > 1:
        opts = "\n  ".join(s.path_str for s in hits)
        sys.exit(f"ambiguous section '{ref}', candidates:\n  {opts}")
    return hits[0]


def section_blocks(sec, lines):
    if sec.blocks is None:
        raw = segment_blocks(lines, sec.start, sec.end)
        sec.blocks = []
        for b in raw:
            if FENCE_RE.match(b) or "\n~~~" in b or "\n```" in b:
                sec.blocks.append({"raw": b, "sentences": None})  # example/code
            else:
                sec.blocks.append({"raw": b, "sentences": split_sentences(normalize(b))})
    return sec.blocks


BLOCK_TOKEN = re.compile(r"^(?:¶|p)(\d+)$", re.IGNORECASE)


def parse_locator(text):
    """Returns (spec, version, section_ref, [(block, s_from, s_to), ...])."""
    parts = [p.strip() for p in re.split(r"\s*[>›]\s*", text.strip())]
    head = parts[0]
    m = re.match(r"^([a-z-]+)(?:@(\d{4}-\d{2}-\d{2}))?$", head)
    if not m:
        sys.exit(f"bad spec identifier: '{head}'")
    spec, version = m.group(1), m.group(2)
    pos = None
    if len(parts) > 1 and re.match(r"^(?:¶|p)\d", parts[-1], re.IGNORECASE):
        pos = parts[-1]
        parts = parts[:-1]
    section_ref = " > ".join(parts[1:]) if len(parts) > 1 else None
    span = None
    if pos:
        rng = re.match(
            r"^(?:¶|p)(\d+)(?:\s*s(\d+)(?:\s*-\s*(?:s?(\d+)|(?:¶|p)(\d+)\s*s(\d+)))?)?$",
            pos.replace(" ", ""), re.IGNORECASE,
        )
        if not rng:
            sys.exit(f"bad position: '{pos}'")
        b1 = int(rng.group(1))
        s1 = int(rng.group(2)) if rng.group(2) else None
        if rng.group(4):  # cross-block range
            span = (b1, s1, int(rng.group(4)), int(rng.group(5)))
        elif rng.group(3):
            span = (b1, s1, b1, int(rng.group(3)))
        elif s1:
            span = (b1, s1, b1, s1)
        else:
            span = (b1, None, b1, None)
    return spec, version, section_ref, span


def get_span_text(sec, lines, span):
    blocks = section_blocks(sec, lines)
    b1, s1, b2, s2 = span
    for b in (b1, b2):
        if not 1 <= b <= len(blocks):
            sys.exit(f"block ¶{b} out of range (section has {len(blocks)} blocks)")
    out = []
    for bi in range(b1, b2 + 1):
        blk = blocks[bi - 1]
        if blk["sentences"] is None:
            out.append(blk["raw"])
            continue
        sents = blk["sentences"]
        lo = s1 if (bi == b1 and s1) else 1
        hi = s2 if (bi == b2 and s2) else len(sents)
        if not (1 <= lo <= hi <= len(sents)):
            sys.exit(
                f"sentence range s{lo}-s{hi} out of range in ¶{bi} "
                f"(has {len(sents)} sentences)"
            )
        out.append(" ".join(sents[lo - 1:hi]))
    return "\n\n".join(out)


def cmd_outline(args):
    spec, _, version = args[0].partition("@")
    version, sections, _ = load_spec(spec, version or None)
    print(f"{spec}@{version}")
    for s in sections:
        anchor = f"  {{#{s.anchor}}}" if s.anchor else ""
        print(f"{'  ' * (s.level - 1)}{s.title}{anchor}")


def cmd_show(args):
    spec, version, ref, _ = parse_locator(args[0])
    version, sections, lines = load_spec(spec, version)
    if not ref:
        sys.exit("show needs a section reference")
    sec = find_section(sections, ref)
    label = f"#{sec.anchor}" if sec.anchor else sec.path_str
    print(f"{spec}@{version} > {label}")
    for i, blk in enumerate(section_blocks(sec, lines), 1):
        if blk["sentences"] is None:
            first = blk["raw"].splitlines()[0]
            print(f"\n¶{i} [example/code block] {first}")
        else:
            print(f"\n¶{i}")
            for j, s in enumerate(blk["sentences"], 1):
                print(f"  s{j}: {s}")


def cmd_resolve(args):
    spec, version, ref, span = parse_locator(args[0])
    version, sections, lines = load_spec(spec, version)
    if not ref:
        sys.exit("resolve needs a section reference")
    sec = find_section(sections, ref)
    if span is None:
        blocks = section_blocks(sec, lines)
        span = (1, None, len(blocks), None)
    print(get_span_text(sec, lines, span))


def cmd_find(args):
    spec, _, version = args[0].partition("@")
    needle = match_normalize(args[1])
    version, sections, lines = load_spec(spec, version or None)
    found = 0
    for sec in sections:
        for bi, blk in enumerate(section_blocks(sec, lines), 1):
            if blk["sentences"] is None:
                if needle in match_normalize(blk["raw"]):
                    label = f"#{sec.anchor}" if sec.anchor else sec.path_str
                    print(f"{spec}@{version} > {label} > ¶{bi}  [example/code block]")
                    found += 1
                continue
            sents = blk["sentences"]
            joined = ""
            bounds = []
            for s in sents:
                if joined:
                    joined += " "
                bounds.append((len(joined), len(joined) + len(match_normalize(s))))
                joined += match_normalize(s)
            idx = joined.find(needle)
            if idx < 0:
                continue
            end = idx + len(needle)
            lo = next(i for i, (a, b) in enumerate(bounds, 1) if idx < b)
            hi = next(i for i, (a, b) in enumerate(bounds, 1) if end <= b)
            label = f"#{sec.anchor}" if sec.anchor else sec.path_str
            srange = f"s{lo}" if lo == hi else f"s{lo}-{hi}"
            full = " s1-" + str(len(sents)) if (lo, hi) == (1, len(sents)) else f" {srange}"
            loc = f"{spec}@{version} > {label} > ¶{bi} {srange}"
            print(loc)
            print("  " + " ".join(sents[lo - 1:hi]))
            found += 1
    if not found:
        sys.exit("not found (note: matching is whitespace- and quote-style-insensitive)")


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    cmd, args = sys.argv[1], sys.argv[2:]
    dispatch = {
        "outline": cmd_outline,
        "show": cmd_show,
        "resolve": cmd_resolve,
        "find": cmd_find,
    }
    if cmd not in dispatch:
        print(__doc__)
        sys.exit(f"unknown command: {cmd}")
    dispatch[cmd](args)


if __name__ == "__main__":
    main()
