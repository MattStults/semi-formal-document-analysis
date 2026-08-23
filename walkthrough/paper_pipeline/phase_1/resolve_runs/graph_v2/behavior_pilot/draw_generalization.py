"""Seeded stratified draws for the generalization runs (frozen prereg
GENERALIZATION_PREREG_DRAFT.md, signed 2026-08-21).

Protocol (frozen): n=40 per behaviour — 20 ENGAGED + 20 NOT-engaged at the
frozen instrument's states; if a side has fewer nodes, take that side whole
and top up the other. Within each side, 50/50 between the two pre-declared
v5-panel strata where population allows:
  panel-agree: all three full seats (sol, fable, deepseek) on the same side
               of the >=2-relevant cut at the node's LEVEL OF GRANULARITY
  panel-split: anything else
GRANULARITY OPERATIONALIZATION (addendum to the frozen prereg, 2026-08-22):
strata are computed at ANCHOR granularity (the document's {#anchor} principle
sections), not paragraph granularity. A node inherits its anchor region by
line containment (deterministic from the document); the seat verdict for an
anchor is the MAX of that seat's paragraph verdicts under the anchor; a node
is panel-agree iff all three seats land on the same side of the >=2 cut on
those anchor maxima. Chosen because paragraph-level indexing could not be
reproduced across generators (validated at 12/40 against the independent
clause corpus — mis-stratification risk), while anchor attribution is exact
and covers every node (no unmapped pool). v5 is COMPARISON LAYER ONLY — it
informs strata, never truth.

Determinism: seeded random.Random(seed); same seed + same inputs ->
byte-identical draw artifact (tested). Seed + input shas recorded in the
artifact.

Usage: python3 draw_generalization.py <modules_file> <slug> <v5_slug> <seed>
"""
import hashlib
import json
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", "..", ".."))
DOC = os.path.join(REPO, "specs", "openai-model-spec", "model_spec.md")
CLAUSES = os.path.join(REPO, "semi-formal-experiment", "modelspec_clauses.json")
V5 = os.path.join(REPO, "data", "panel-v5", "runlog-v5.jsonl")
GRAPH = os.path.join(HERE, "..", "recurse", "root", "graph.json")
FULL_SEATS = ("sol", "fable", "deepseek")
V5_SLUG_MAP = {
    "harmlessness-to-user": "harmlessness-to-user",
    "objectivity-on-contested-questions": "objectivity",
    "how-to-approach-tradeoffs": "tradeoffs",
    "user-autonomy": "user-autonomy",
    "proportionate-risk-mitigation": "proportionate-risk",
    "general-welfare": "general-welfare",
}


def sha_file(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def anchor_map():
    """anchor -> heading line number, from the document's {#anchor} tags."""
    out = {}
    for i, line in enumerate(open(DOC).read().splitlines(), start=1):
        m = re.search(r"\{#([a-z0-9_]+)", line)
        if m and line.lstrip().startswith("#"):
            out[m.group(1)] = i
    return out


DOC_LINES = None


def doc_lines():
    global DOC_LINES
    if DOC_LINES is None:
        DOC_LINES = open(DOC).read().splitlines()
    return DOC_LINES


def anchor_regions(anchors):
    """anchor -> (start_line, end_line): heading line to the next anchored
    heading (or EOF)."""
    starts = sorted(anchors.items(), key=lambda kv: kv[1])
    regions = {}
    total = len(doc_lines())
    for i, (a, ln) in enumerate(starts):
        end = starts[i + 1][1] - 1 if i + 1 < len(starts) else total
        regions[a] = (ln, end)
    return regions


def paragraph_index(regions, line):
    """(anchor, 1-based paragraph index) for a document line: paragraphs are
    blank-line-separated blocks within the anchor region, counted AFTER the
    heading line (clause-corpus cross-check: line 3 = #overview ¶1)."""
    for a, (s, e) in regions.items():
        if s <= line <= e:
            if line == s:
                return a, 0          # the heading itself is not a paragraph
            idx, in_para = 0, False
            for off, l in enumerate(doc_lines()[s:e]):
                ln_no = s + 1 + off
                if l.strip() == "":
                    in_para = False
                else:
                    if not in_para:
                        idx += 1
                        in_para = True
                    if ln_no == line:
                        return a, idx
            return a, idx
    return None, None


def node_lines():
    """corpus node id -> list of (lo, hi) line SEGMENTS, parsed from the
    packet SOURCE-TEXT L-markers (ctx_chunk1-8 + ctx_ext1-3 cover all 762
    corpus nodes); per-segment, not envelope (draw review A2, 2026-08-22).
    NOTE (2026-08-22): recurse/root/graph.json CANNOT be used for this join —
    its segmentation generation differs from the translation corpus
    (e.g. L1108-1368 vs l1108_1367) and its ids do not match corpus ids."""
    import glob as _glob
    out = {}
    paths = sorted(_glob.glob(os.path.join(HERE, "panel_run1", "convergence", "ctx_chunk*.json"))) + \
            sorted(_glob.glob(os.path.join(HERE, "panel_run1", "convergence", "ctx_ext[0-9].json")))
    for p in paths:
        for nid, pkt in json.load(open(p)).items():
            span = pkt.get("span", "")
            i = span.find("SOURCE TEXT")
            seg = span[i:] if i >= 0 else span
            ms = re.findall(r"L(\d+)-L(\d+)", seg)
            if ms:
                # A2 fix (draw review, 2026-08-22): keep the SEGMENTS, not
                # their envelope — scattered-quote nodes (2/762) otherwise
                # map to every anchor between their extreme lines
                segs = [(int(a), int(b)) for a, b in ms]
                out.setdefault(nid, []).extend(segs)
    return out


def v5_node_strata(v5_slug):
    """corpus node_id -> 'agree' | 'split', at ANCHOR granularity (see module
    docstring operationalization). Node lines from packet L-markers; anchor
    attribution by line containment (a node spanning several anchors collects
    them all); anchor seat verdict = max over its paragraphs; agree iff all
    three full seats land on the same side of the >=2 cut."""
    anchors = anchor_map()
    regions = anchor_regions(anchors)
    # anchor -> seat -> max verdict over paragraphs
    verd = {}
    for l in open(V5):
        r = json.loads(l)
        if r["spec"] != "model-spec" or r["model"] not in FULL_SEATS:
            continue
        if r["behaviour"] != v5_slug:
            continue
        parts = r["locator"].split(" > ")
        if len(parts) < 2:
            continue
        m = re.search(r"#([a-z0-9_]+)", parts[-2] if len(parts) >= 3 else parts[-1])
        # A1 fix (draw review, 2026-08-22): re.search not re.match — v5 has a
        # trailing-tag locator form ("... {#anchor authority=...} > ¶N") that
        # re.match silently dropped (51 rows/behaviour, prioritize_teen_safety)
        if not m:
            continue
        a = m.group(1)
        verd.setdefault(a, {})
        verd[a][r["model"]] = max(verd[a].get(r["model"], 0), int(r["verdict"]))
    out = {}
    for nid, segs in node_lines().items():
        anchs = {a for (lo, hi) in segs for a, (s, e) in regions.items()
                 if not (hi < s or lo > e)}
        seat_max = {}
        for a in anchs:
            for seat, v in verd.get(a, {}).items():
                seat_max[seat] = max(seat_max.get(seat, 0), v)
        if len(seat_max) < len(FULL_SEATS):
            # no full-seat coverage for this behaviour: conservative split
            out[nid] = "split"
            continue
        sides = {v >= 2 for v in seat_max.values()}
        out[nid] = "agree" if len(sides) == 1 else "split"
    return out


def stratified_draw(engaged, not_engaged, strata, seed, n_side=20):
    rng = random.Random(seed)
    def draw_side(pool):
        agree = [n for n in pool if strata.get(n) == "agree"]
        split = [n for n in pool if strata.get(n) == "split"]
        unmap = [n for n in pool if strata.get(n) is None]
        rng.shuffle(agree); rng.shuffle(split); rng.shuffle(unmap)
        want = min(n_side, len(pool))
        half = want // 2
        picked = agree[:half] + split[half:half + (want - half)] \
            if len(split) >= want - half else agree[:half] + split
        # fill from whichever stratum has surplus, then unmapped
        picked_set = set(picked)
        surplus = [n for n in (agree + split) if n not in picked_set]
        picked += surplus[:want - len(picked)]
        picked += unmap[:want - len(picked)]
        return sorted(picked[:want])
    e_pool, ne_pool = sorted(engaged), sorted(not_engaged)
    e_draw = draw_side(e_pool)
    ne_draw = draw_side(ne_pool)
    # top-up rule: if a side is short, take it whole and top up the other
    if len(e_draw) < n_side:
        extra = draw_side([n for n in ne_pool if n not in ne_draw])
        ne_draw = sorted(ne_draw + extra[:n_side - len(e_draw)])
    if len(ne_draw) < n_side:
        extra = draw_side([n for n in e_pool if n not in e_draw])
        e_draw = sorted(e_draw + extra[:n_side - len(ne_draw)])
    return e_draw, ne_draw


def main():
    mods_file, slug, seed = sys.argv[1], sys.argv[2], int(sys.argv[3])
    v5_slug = V5_SLUG_MAP[slug]
    sys.path.insert(0, HERE)
    import relevance_by_act as RBA
    br = RBA.bridges(); corpus = RBA.corpus_acts()
    mods = json.load(open(mods_file))["modules"]
    _, rel = RBA.relevance(mods[slug], br, corpus)
    eng = set(rel)
    strata = v5_node_strata(v5_slug)
    known = set(strata)
    engaged = [n for n in eng if n in known]
    not_engaged = [n for n in known if n not in eng]
    e_draw, ne_draw = stratified_draw(engaged, not_engaged, strata, seed)
    out = {
        "_": "Generalization fresh draw (frozen prereg). v5 comparison layer "
             "informs strata ONLY — never truth. Anchor seat verdict = max "
             "over its paragraphs (per-segment node-to-anchor attribution; "
             "prereg addenda 1-3); panel-agree = all three full seats on the "
             "same side of the >=2 cut; unmapped nodes fill residual slots "
             "only and are counted below.",
        "modules_file": os.path.basename(mods_file),
        "modules_sha": sha_file(mods_file),
        "input_shas": {"runlog_v5": sha_file(V5), "model_spec": sha_file(DOC)},
        "v5_slug": v5_slug,
        "slug": slug,
        "seed": seed,
        "engaged_pool": len(engaged),
        "not_engaged_pool": len(not_engaged),
        "unmapped_in_pools": sum(1 for n in list(engaged) + not_engaged
                                 if strata.get(n) is None) if False else
                             sum(1 for n in set(engaged) | set(not_engaged)
                                 if strata.get(n) is None),
        "draw_engaged": e_draw,
        "draw_not_engaged": ne_draw,
        "strata_of_draw": {n: strata.get(n) for n in e_draw + ne_draw},
    }
    dest = os.path.join(HERE, "generalization_builds",
                        f"draw_{slug}_seed{seed}.json")
    json.dump(out, open(dest, "w"), indent=1)
    print(f"wrote {dest}: engaged {len(e_draw)} + not-engaged {len(ne_draw)}")
    print(f"pools: engaged {len(engaged)}, not-engaged {len(not_engaged)}, "
          f"unmapped in pools {out['unmapped_in_pools']}")


if __name__ == "__main__":
    main()
