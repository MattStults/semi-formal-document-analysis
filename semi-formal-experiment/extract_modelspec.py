"""Extract the 259 inline focus-area markers [^xxxx] from the OpenAI Model Spec.

Structure finding: the markers are INLINE only. There are zero footnote-definition
lines (`[^id]:`) anywhere in the file. Each marker is a focus-area anchor attached
to the text immediately preceding it (the rendered site turns them into per-focus
permalinks). So the governing statement for a marker is the sentence it terminates
or sits inside.
"""
import json
import re
import sys

SRC = "external/model_spec/model_spec.md"
MARKER = re.compile(r"\[\^([A-Za-z0-9]+)\]")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*\{#([^}\s]+)((?:\s+[^}]*)?)\}\s*$")

MODALITIES = [
    ("must not", r"\bmust not\b|\bmust never\b"),
    ("should not", r"\bshould not\b|\bshouldn't\b|\bshould never\b"),
    ("may not", r"\bmay not\b"),
    ("must", r"\bmust\b"),
    ("should", r"\bshould\b"),
    ("may", r"\bmay\b|\bmay only\b"),
]
DEFEATERS = ["unless", "by default", "overrid", "except"]


def load():
    with open(SRC, encoding="utf-8") as f:
        return f.read()


def build_sections(text):
    """Return list of (line_idx, level, title, sec_id, attrs)."""
    heads = []
    for i, line in enumerate(text.split("\n")):
        m = HEADING.match(line)
        if m:
            heads.append((i, len(m.group(1)), m.group(2), m.group(3), m.group(4).strip()))
    return heads


def section_chain_for_line(heads, line_idx):
    stack = []
    for (i, lvl, title, sid, attrs) in heads:
        if i > line_idx:
            break
        while stack and stack[-1][1] >= lvl:
            stack.pop()
        stack.append((i, lvl, title, sid, attrs))
    return stack


SENT_END = re.compile(r"(?<=[.!?])\s")


def split_sentences(line):
    """Return list of (start, end) sentence spans within the line."""
    spans = []
    start = 0
    for m in SENT_END.finditer(line):
        # avoid splitting on abbreviations like e.g. / i.e. / U.S.
        prefix = line[max(0, m.start() - 8):m.start()]
        if re.search(r"(e\.g\.|i\.e\.|etc\.|vs\.|Dr\.|Mr\.|U\.S\.)$", prefix):
            continue
        spans.append((start, m.start() + 1))
        start = m.end()
    if start < len(line):
        spans.append((start, len(line)))
    return spans


def main():
    text = load()
    lines = text.split("\n")
    heads = build_sections(text)

    # detect fenced example blocks (~~~ ... ~~~) so we can report if markers land inside
    fenced = set()
    inside = False
    for i, line in enumerate(lines):
        if line.strip().startswith("~~~"):
            inside = not inside
            fenced.add(i)
            continue
        if inside:
            fenced.add(i)

    # Build "units": a unit is either a single bullet/numbered line, or a run of
    # consecutive hard-wrapped prose lines within one paragraph block. Units are
    # joined with "\n" so every unit (and every sentence slice of it) remains a
    # verbatim substring of the source file.
    units = []  # (first_line_idx, text)
    buf, buf_start = [], None
    def flush():
        nonlocal buf, buf_start
        if buf:
            units.append((buf_start, "\n".join(buf)))
        buf, buf_start = [], None
    for i, line in enumerate(lines):
        if not line.strip() or HEADING.match(line) or re.match(r"^\s*([-*+]|\d+\.)\s", line):
            flush()
            if line.strip() and not HEADING.match(line):
                units.append((i, line))
            continue
        if buf_start is None:
            buf_start = i
        buf.append(line)
    flush()

    records = []
    for li, line in units:
        ms = list(MARKER.finditer(line))
        if not ms:
            continue
        spans = split_sentences(line)
        chain = section_chain_for_line(heads, li)
        # authority from nearest heading attrs that declares one
        authority = None
        for (_, _, _, _, attrs) in reversed(chain):
            am = re.search(r"authority=(\w+)", attrs or "")
            if am:
                authority = am.group(1)
                break
        section_path = [h[2] for h in chain]
        section_id = chain[-1][3] if chain else None
        top_level = chain[0][2] if chain else None
        # lead-in: for bullet/numbered lines, the nearest preceding non-empty
        # non-bullet paragraph line
        is_bullet = bool(re.match(r"^\s*([-*+]|\d+\.)\s", line))
        lead_in = None
        if is_bullet:
            for j in range(li - 1, max(-1, li - 25), -1):
                s = lines[j].strip()
                if not s:
                    continue
                if re.match(r"^\s*([-*+]|\d+\.)\s", lines[j]):
                    continue
                if HEADING.match(lines[j]):
                    break
                lead_in = s
                break

        prev_end = None
        for k, m in enumerate(ms):
            # containing sentence
            sent = None
            for (a, b) in spans:
                if a <= m.start() < b:
                    sent = (a, b)
                    break
            if sent is None:
                sent = (0, len(line))
            sent_text = line[sent[0]:sent[1]].strip()
            # marked span: from max(sentence start, previous marker end) to marker start
            lo = sent[0]
            if prev_end is not None and prev_end > lo:
                lo = prev_end
            span_text = line[lo:m.start()].strip()
            prev_end = m.end()

            hay = ((lead_in or "") + " " + sent_text).lower()
            mods = [name for name, pat in MODALITIES if re.search(pat, hay)]
            # collapse: "must not" subsumes "must", etc.
            if "must not" in mods and "must" in mods and not re.search(r"\bmust\b(?! not)(?! never)", hay):
                mods.remove("must")
            if "should not" in mods and "should" in mods and not re.search(r"\bshould\b(?! not)(?! never)", hay):
                mods.remove("should")
            defs_found = sorted({d.strip() for d in DEFEATERS if d in hay})
            records.append({
                "focus_id": m.group(1),
                "line": li + 1 + line[:m.start()].count("\n"),
                "in_example_block": li in fenced,
                "section_path": section_path,
                "section_id": section_id,
                "top_level_section": top_level,
                "text": sent_text,
                "marked_span": span_text,
                "lead_in": lead_in,
                "modality": mods,
                "has_defeater": bool(defs_found),
                "defeater_markers": defs_found,
                "authority_level_or_null": authority,
            })
    print(f"markers extracted: {len(records)}  unique: {len({r['focus_id'] for r in records})}")
    print(f"in example blocks: {sum(r['in_example_block'] for r in records)}")
    with open("_extract_raw.json", "w", encoding="utf-8") as f:
        json.dump(records, f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
