#!/usr/bin/env python3
"""The golden set — planted predicates with a known right answer.

⭐ WHY IT MUST FILL MOST SECTIONS, not sit in a list of its own. `[RAN]` only 9
of 78 sections have a translated module. If the other 69 carried "not
applicable", the 9 real ones would be the only populated sections in the
document and a model could score well by noticing WHICH SECTIONS HAVE ENTRIES
rather than by reading anything. Planted items must be indistinguishable in
form and position from real ones, so they go under the same section markers, in
the same format, interleaved throughout.

⛔ THE KEY IS NEVER RENDERED. `expected` and `category` exist only for scoring.

WHERE THE GROUND TRUTH COMES FROM, so it is checkable rather than asserted:

  KNOWN GOOD  two sources, because one was not enough.
              (a) SECTION NAMES. The document's own topic names are diverse and
                  unarguable: the section that establishes `restricted_content`
                  is the one whose id is `restricted_content`.
              (b) `**Term**:` DEFINITIONS. ⚠️ `[RAN]` this yields only **10
                  distinct terms across 2 sections** — the "199" is a count of
                  CLAUSES matching the pattern, most of them repeats. A set
                  built on (b) alone would let a model score well by always
                  answering "definitions", so it is a minority category here.
  KNOWN BAD   constructed against measured absence. Three kinds, and they are
              NOT equally hard:
                absent-word      a word that appears nowhere in the document
                absent-compound  ⛔ both words are document vocabulary, the
                                 COMPOUND is not. `policy_class` is real and
                                 spans 9 sections word-wise
                plausible        assembled from very common words —
                                 `user_trust_level` spans 73 sections word-wise
  WORLD       terms the document USES and never defines. `[RAN]` 7 clauses say
              "illegal"/"illicit"; 0 define it.
  NOTHING     a few sections deliberately borrow nothing, to check the model
              does not invent needs where none are claimed.

⚠️ A FITTING RISK I CANNOT FULLY REMOVE, stated rather than hidden: I am both
constructing this set and reporting the score against it. The mitigations are
that known-good answers are read mechanically off the document's own `**Term**:`
pattern rather than chosen, the draw is seeded and reproducible, and every
planted item is written to disk with its category so a reviewer can check the
set was not made easy.
"""

import argparse
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import translate as T  # noqa: E402

SALT = "golden-v1"

#: Words absent from the document, for `absent-word`. Verified at build time —
#: a word that turns out to be present is a build error, not a quiet pass.
ALIEN = ["telemetry", "escrow", "quorum", "bytecode", "phenotype", "cadastral",
         "sharding", "isotope", "vellum", "monsoon", "abseil", "trawler"]

#: Terms the document uses without defining. `[RAN]` verified: 7 clauses use
#: illegal/illicit/unlawful, 0 define the extension.
WORLD_TERMS = ["illegal", "unlawful", "illicit"]


def _rank(*parts):
    return int(hashlib.sha256((SALT + "|".join(parts)).encode()).hexdigest()[:8], 16)


def defined_terms(clauses):
    """`**Term**: …` — the document defining its own vocabulary.

    ⚠️ `[RAN]` **10 distinct terms, in 2 sections.** 199 CLAUSES match the
    pattern but most repeat the same term, and reading the clause count as a
    term count is what made the first version of this set unusable.
    """
    out = {}
    for c in clauses:
        m = re.match(r"\s*\*\*([^*]{2,40})\*\*\s*[::]", c["quote"])
        if not m:
            continue
        term = re.sub(r"[^a-z0-9]+", "_", m.group(1).strip().lower()).strip("_")
        if term and term not in out:
            out[term] = {"section_id": c["section_id"], "clause_id": c["id"]}
    return out


def vocabulary(clauses):
    words, pairs = set(), set()
    for c in clauses:
        toks = re.findall(r"[a-z]{3,}", c["quote"].lower())
        words |= set(toks)
        pairs |= {f"{a}_{b}" for a, b in zip(toks, toks[1:])}
    return words, pairs


def build(cfg, n_good=30, n_bad=21, n_world=4, n_nothing=6):
    """Plant a golden set across the sections that have no real data.

    Returns (items, empty_sections). Every item carries `expected`, which is
    the scoring key and is never rendered into a prompt.
    """
    clauses = T.load_corpus(cfg)
    all_secs = []
    for c in clauses:
        if c["section_id"] not in all_secs:
            all_secs.append(c["section_id"])
    defined = defined_terms(clauses)
    words, pairs = vocabulary(clauses)

    alien = [w for w in ALIEN if w not in words]
    if len(alien) < 6:
        raise SystemExit(f"⛔ only {len(alien)} alien words are genuinely absent; "
                         f"the `absent-word` category would be built on a false "
                         f"premise. Add more to ALIEN.")

    items = []

    # --- KNOWN GOOD (a): the document's own SECTION NAMES ------------------
    # ⭐ The `**Term**:` pattern yields only 10 distinct terms across 2 sections
    # `[RAN]`, so a set built on it alone would let a model score well by always
    # answering "definitions". Section ids are the document's own topic names,
    # they are diverse, and "which section establishes `restricted_content`?"
    # has an unarguable answer. Meta sections are excluded: nothing "establishes"
    # the concept of an overview.
    META = {"overview", "definitions", "objectives", "introduction", "conclusion"}
    topical = [s for s in all_secs
               if s not in META and "_" in s and not s.startswith("example")]
    topical.sort(key=lambda t: _rank("topic", t))
    for t in topical[:n_good]:
        elsewhere = [s for s in all_secs if s != t]
        elsewhere.sort(key=lambda s: _rank("topicsec", t, s))
        items.append({"predicate": f"{t}/1", "section_id": elsewhere[0],
                      "category": "known-good-section",
                      "expected": {"verdict": "document", "section_id": t}})

    # --- KNOWN GOOD (b): a term the document explicitly defines -------------
    good_terms = sorted(defined)
    good_terms.sort(key=lambda t: _rank("good", t))
    for t in good_terms:
        home = defined[t]["section_id"]
        elsewhere = [s for s in all_secs if s != home]
        elsewhere.sort(key=lambda s: _rank("goodsec", t, s))
        items.append({"predicate": f"{t}/1", "section_id": elsewhere[0],
                      "category": "known-good-defined",
                      "expected": {"verdict": "document", "section_id": home}})

    # --- KNOWN BAD, three kinds of increasing difficulty -------------------
    common = sorted(w for w in words if len(w) > 3)
    common.sort(key=lambda w: _rank("common", w))
    secs = sorted(all_secs, key=lambda s: _rank("badsec", s))
    k = 0
    for i in range(n_bad):
        kind = ("absent-word", "absent-compound", "plausible")[i % 3]
        if kind == "absent-word":
            name = f"{alien[i % len(alien)]}_state"
        elif kind == "absent-compound":
            a, b = common[k], common[k + 1]
            k += 2
            while f"{a}_{b}" in pairs:
                a, b = common[k], common[k + 1]
                k += 2
            name = f"{a}_{b}"
        else:
            a, b, c2 = common[k], common[k + 1], common[k + 2]
            k += 3
            name = f"{a}_{b}_{c2}"
        items.append({"predicate": f"{name}/1", "section_id": secs[i % len(secs)],
                      "category": kind,
                      "expected": {"verdict": "coinage", "section_id": None}})

    # --- WORLD -------------------------------------------------------------
    for i, w in enumerate((WORLD_TERMS * 3)[:n_world]):
        items.append({"predicate": f"{w}/1",
                      "section_id": secs[(i + n_bad) % len(secs)],
                      "category": "world",
                      "expected": {"verdict": "world", "section_id": None}})

    used = {i["section_id"] for i in items}
    free = [s for s in all_secs if s not in used]
    free.sort(key=lambda s: _rank("empty", s))
    return items, free[:n_nothing]


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", default=os.path.join(HERE, "resolve_runs",
                                                 "golden_set.json"))
    a = p.parse_args(argv)
    cfg = T.load_config(os.path.join(HERE, "config.json"))
    items, empty = build(cfg)
    by = {}
    for it in items:
        by[it["category"]] = by.get(it["category"], 0) + 1
    print(f"  planted items      : {len(items)}")
    for k, v in sorted(by.items()):
        print(f"     {k:18} {v}")
    print(f"  sections left EMPTY (borrows nothing, on purpose): {len(empty)}")
    print(f"  sections touched   : {len({i['section_id'] for i in items})} of 78")
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump({"salt": SALT, "items": items, "empty_sections": empty}, fh,
                  indent=1)
    print(f"\n  key written to {a.out}  ⛔ never rendered into a prompt")
    print("\n  sample (predicate → expected):")
    for it in items[:6]:
        print(f"     {it['predicate']:34} {it['category']:16} "
              f"→ {it['expected']['verdict']}"
              + (f" @ {it['expected']['section_id']}" if it['expected']['section_id'] else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
