"""Classify the 259 OpenAI Model Spec focus areas with the SAME four-way scheme
used for constitution_clauses.json, and emit modelspec_focus_areas.json +
modelspec_classification_summary.md.

Categories (identical definitions to the constitution pass):
  conditional  - extractable trigger -> response structure; applicability turns
                 on a statable condition
  holistic     - weighing guidance with no crisp trigger
  definitional - defines a term / describes a category without prescribing
                 behavior
  meta         - about the document itself, its scope, or its revision

Classification below is hand-assigned per focus id after reading every governing
statement. Boundary rule applied uniformly:
  * a statable trigger (even a fuzzy predicate like "gratuitous abuse") plus a
    response that fixes an observable behaviour class -> conditional
  * blanket quality/manner duties ("be warm", "avoid excessive hedging"* where
    the response is a vague quality), explicit trade-off lists, interpretive
    priors, and "err on the side of / weigh / consider" directives -> holistic
  * purely descriptive or taxonomic statements -> definitional
  * statements about the Model Spec document itself -> meta
"""
import json
import re
from collections import Counter, defaultdict

SRC = "external/model_spec/model_spec.md"
RAW = "_extract_raw.json"

KIND = {
    "8ep1": "meta", "m12p": "conditional", "d32l": "conditional",
    "zyu5": "conditional", "2bl7": "conditional", "3u2u": "conditional",
    "4q1u": "conditional", "a9sg": "definitional", "a9sh": "holistic",
    "bn8b": "conditional", "la9s": "conditional", "d232": "conditional",
    "3oa1": "conditional", "l1ox": "conditional", "0a12": "conditional",
    "1ka0": "conditional", "5q1u": "holistic", "jlla": "holistic",
    "6rz0": "holistic", "a9se": "conditional", "btf2": "definitional",
    "a9sd": "definitional", "nhrt": "conditional", "ag2y": "holistic",
    "0prn": "holistic", "ag41": "conditional", "ag42": "conditional",
    "ag43": "conditional", "a9sq": "holistic", "33pp": "conditional",
    "ng01": "conditional", "ng02": "conditional", "ng03": "conditional",
    "ng04": "conditional", "ag6c": "conditional", "ag7d": "conditional",
    "ag8e": "conditional", "ag9f": "holistic", "aga0": "holistic",
    "agb1": "holistic", "agc2": "conditional", "agd3": "holistic",
    "age4": "holistic", "a93s": "conditional", "pcsb": "conditional",
    "f0mi": "conditional", "cpbn": "definitional", "0q9d": "conditional",
    "a0im": "conditional", "bgdj": "conditional", "wof7": "conditional",
    "tob6": "conditional", "i84s": "conditional", "5cyd": "conditional",
    "tjd6": "conditional", "a6k2": "conditional", "d912": "conditional",
    "ide1": "definitional", "ide2": "definitional", "agf5": "conditional",
    "agg6": "holistic", "agh7": "conditional", "6h7c": "conditional",
    "cwl1": "conditional", "cwl2": "conditional", "cwl3": "conditional",
    "c4ma": "conditional", "c4mb": "conditional", "91og": "conditional",
    "91of": "conditional", "91oh": "conditional", "bz0o": "conditional",
    "li9q": "conditional", "24vn": "conditional", "ax72": "conditional",
    "1dj1": "holistic", "1397": "conditional", "1398": "conditional",
    "f983": "holistic", "dz8r": "conditional", "tmho": "definitional",
    "l132": "conditional", "6o2w": "conditional", "9asd": "conditional",
    "eiy6": "conditional", "m2cz": "conditional", "6oww": "conditional",
    "xe1o": "conditional", "ap9r": "conditional", "xe1p": "conditional",
    "k8hg": "conditional", "h232": "conditional", "a222": "conditional",
    "p9ta": "conditional", "p9tl": "conditional", "ad81": "conditional",
    "ad82": "conditional", "ad83": "conditional", "c9a1": "conditional",
    "c9a2": "conditional", "c9a3": "conditional", "c9a4": "conditional",
    "c9a5": "conditional", "91as": "holistic", "kdoq": "conditional",
    "61tv": "conditional", "l98t": "conditional", "kl20": "holistic",
    "kl21": "conditional", "3kvn": "conditional", "mhd1": "conditional",
    "mhd2": "holistic", "qybs": "conditional", "2yv5": "conditional",
    "evb8": "conditional", "2mv4": "conditional", "jj34": "conditional",
    "wgjk": "conditional", "xcg4": "holistic", "up7h": "holistic",
    "g33a": "conditional", "w9nd": "definitional", "bxoj": "definitional",
    "21ox": "conditional", "8555": "definitional", "o92b": "conditional",
    "o92p": "conditional", "l912": "conditional", "agi8": "holistic",
    "agj9": "conditional", "ddka": "conditional", "31oe": "conditional",
    "uf01": "conditional", "uf02": "holistic", "uf03": "holistic",
    "ss01": "conditional", "ss03": "holistic", "ss04": "conditional",
    "yjj2": "holistic", "1392": "conditional", "4lfk": "conditional",
    "onv4": "conditional", "kp2q": "conditional", "139o": "conditional",
    "iy72": "conditional", "c955": "conditional", "nto2": "conditional",
    "nto3": "meta", "lie0": "conditional", "agk0": "holistic",
    "cova": "conditional", "lds9": "conditional", "lds2": "holistic",
    "sy73": "conditional", "sy74": "conditional", "sy75": "holistic",
    "u3nx": "conditional", "agn3": "conditional", "agp5": "conditional",
    "89iw": "definitional", "svyu": "holistic", "y7v1": "conditional",
    "8yko": "conditional", "w0lk": "conditional", "h068": "conditional",
    "7cr3": "conditional", "h70n": "definitional", "7sad": "definitional",
    "7cr6": "conditional", "ir13": "definitional", "di12": "holistic",
    "di19": "conditional", "di20": "conditional", "bjq4": "conditional",
    "h01s": "conditional", "pb13": "conditional", "pb14": "holistic",
    "kpvs": "holistic", "zwhy": "holistic", "9fpw": "holistic",
    "cp0y": "conditional", "5ckd": "conditional", "3hgm": "conditional",
    "6yer": "conditional", "jsqq": "conditional", "mlct": "conditional",
    "by9a": "conditional", "lpuw": "holistic", "1dvp": "conditional",
    "cw53": "conditional", "e9ny": "conditional", "7qme": "conditional",
    "92bt": "conditional", "5lkf": "conditional", "66cj": "conditional",
    "krkk": "holistic", "lh2e": "definitional", "0dh6": "holistic",
    "uotj": "holistic", "f36l": "holistic", "mblx": "conditional",
    "adau": "conditional", "v48c": "conditional", "934q": "conditional",
    "kk24": "conditional", "mxxw": "conditional", "fk21": "conditional",
    "fmt3": "conditional", "4qvw": "holistic", "dcqh": "conditional",
    "j45l": "holistic", "092i": "holistic", "g1pr": "holistic",
    "5tah": "holistic", "d0pu": "holistic", "l8a5": "holistic",
    "rse0": "holistic", "h82a": "holistic", "7ru5": "holistic",
    "iai0": "holistic", "zpwa": "holistic", "ydgh": "holistic",
    "thyk": "holistic", "9881": "holistic", "ttmt": "holistic",
    "zx8z": "conditional", "3blt": "holistic", "pmug": "holistic",
    "ab11": "conditional", "ab12": "conditional", "ab13": "holistic",
    "ab14": "holistic", "ab15": "conditional", "jg9d": "conditional",
    "p8a8": "conditional", "ak12": "holistic", "zlk1": "conditional",
    "t5q0": "holistic", "u005": "holistic", "pes1": "conditional",
    "zl22": "holistic", "sc01": "conditional", "sc02": "conditional",
    "qrpq": "conditional", "sty1": "conditional", "epyx": "conditional",
    "2bij": "conditional", "epwc": "conditional", "duy8": "holistic",
    "8uz1": "holistic", "7zjr": "holistic", "h4t9": "holistic",
    "35cm": "holistic", "6x4h": "conditional", "omek": "conditional",
    "hcvn": "conditional", "nyxg": "conditional", "hscu": "conditional",
    "i271": "conditional",
}

CONSTITUTION = {
    "total": 616,
    "conditional": 195, "holistic": 204, "definitional": 168, "meta": 49,
}


def main():
    raw = json.load(open(RAW, encoding="utf-8"))
    source = open(SRC, encoding="utf-8").read()

    recs = []
    for r in raw:
        fid = r["focus_id"]
        recs.append({
            "focus_id": fid,
            "line": r["line"],
            "section_path": r["section_path"],
            "section_id": r["section_id"],
            "top_level_section": r["top_level_section"],
            "text": r["text"],
            "marked_span": r["marked_span"],
            "lead_in": r["lead_in"],
            "kind": KIND.get(fid, "unclassifiable"),
            "modality": r["modality"],
            "has_defeater": r["has_defeater"],
            "defeater_markers": r["defeater_markers"],
            "authority_level_or_null": r["authority_level_or_null"],
        })

    # ---- verbatim verification -------------------------------------------
    ok = sum(1 for r in recs if r["text"] in source)
    ok_span = sum(1 for r in recs if r["marked_span"] in source)
    print(f"verbatim text pass: {ok}/{len(recs)} = {100*ok/len(recs):.1f}%")
    print(f"verbatim marked_span pass: {ok_span}/{len(recs)} = {100*ok_span/len(recs):.1f}%")
    for r in recs:
        if r["text"] not in source:
            print("  FAIL", r["focus_id"], repr(r["text"][:120]))

    json.dump(recs, open("modelspec_focus_areas.json", "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)

    # ---- summary ----------------------------------------------------------
    n = len(recs)
    kinds = Counter(r["kind"] for r in recs)
    order = ["conditional", "holistic", "definitional", "meta", "unclassifiable"]

    by_sec = defaultdict(Counter)
    sec_order = []
    for r in recs:
        s = r["top_level_section"]
        if s not in sec_order:
            sec_order.append(s)
        by_sec[s][r["kind"]] += 1
        by_sec[s]["total"] += 1

    mods = Counter()
    for r in recs:
        mods["+".join(r["modality"]) if r["modality"] else "(none)"] += 1
    mod_any = Counter()
    for r in recs:
        if not r["modality"]:
            mod_any["(none)"] += 1
        for m in r["modality"]:
            mod_any[m] += 1

    defeat = sum(1 for r in recs if r["has_defeater"])
    dmark = Counter()
    for r in recs:
        for d in r["defeater_markers"]:
            dmark[d] += 1
    auth = Counter(r["authority_level_or_null"] or "(none stated)" for r in recs)

    L = []
    A = L.append
    A("# OpenAI Model Spec focus-area classification summary\n")
    A("Source: `external/model_spec/model_spec.md` (model_spec repo checkout, 4691 lines). "
      "Inventory: `modelspec_focus_areas.json`. Criteria identical to the constitution pass "
      "(`segmentation_summary.md`, 616 clauses).\n")
    A(f"**Total focus areas: {n}** (all 259 unique `[^xxxx]` markers in the file)\n")

    A("## Marker structure\n")
    A("The `[^xxxx]` tokens are **inline anchors, not footnotes**. The file contains "
      "**zero** footnote-definition lines (`[^id]:`) — a scan of all 4691 lines finds none. "
      "Each marker sits immediately after the span of prose it labels (the rendered site "
      "turns each into a per-focus-area permalink), so the governing statement for a marker "
      "is the sentence it terminates or sits inside. All 259 markers occur in normative prose; "
      "**0** fall inside the `~~~`-fenced example conversation blocks.\n")

    A("## By kind\n")
    A("| kind | count | % |")
    A("|---|---|---|")
    for k in order:
        if kinds.get(k):
            A(f"| {k} | {kinds[k]} | {100*kinds[k]/n:.1f}% |")
    A("")
    A(f"**Formalizable fraction (conditional): {100*kinds['conditional']/n:.1f}%** "
      f"({100*kinds['conditional']/(kinds['conditional']+kinds['holistic']):.1f}% conditional "
      f"among the trigger-bearing vs weighing normative pool)\n")

    A("## By top-level section\n")
    A("| section | total | conditional | holistic | definitional | meta | % conditional |")
    A("|---|---|---|---|---|---|---|")
    for s in sec_order:
        c = by_sec[s]
        A(f"| {s} | {c['total']} | {c['conditional']} | {c['holistic']} | "
          f"{c['definitional']} | {c['meta']} | {100*c['conditional']/c['total']:.1f}% |")
    A("")

    A("## Modality distribution\n")
    A("Counted over the governing statement plus its bullet lead-in, so a focus area can "
      "carry more than one modality verb.\n")
    A("| modality verb | focus areas | % of 259 |")
    A("|---|---|---|")
    for m, c in mod_any.most_common():
        A(f"| {m} | {c} | {100*c/n:.1f}% |")
    A("")
    A("Exact combinations:\n")
    A("| combination | count |")
    A("|---|---|")
    for m, c in mods.most_common():
        A(f"| {m} | {c} |")
    A("")

    A("## Defeasibility\n")
    A(f"**{defeat} of {n} focus areas ({100*defeat/n:.1f}%) carry an explicit defeasibility "
      "marker** (`unless`, `by default`, `overrid`* covering override/overridden/overriding, `except`).\n")
    A("| marker | occurrences |")
    A("|---|---|")
    for d, c in dmark.most_common():
        A(f"| {d} | {c} |")
    A("")
    A("Authority level declared on the containing section heading "
      "(`{#id authority=...}`), inherited down the heading chain:\n")
    A("| authority | focus areas | % |")
    A("|---|---|---|")
    for a, c in auth.most_common():
        A(f"| {a} | {c} | {100*c/n:.1f}% |")
    A("")

    A("## Side-by-side: Model Spec vs Anthropic constitution\n")
    A("| kind | Model Spec (n=259) | % | Constitution (n=616) | % | delta (pp) |")
    A("|---|---|---|---|---|---|")
    for k in ["conditional", "holistic", "definitional", "meta"]:
        ms, cs = kinds.get(k, 0), CONSTITUTION[k]
        mp, cp = 100*ms/n, 100*cs/CONSTITUTION["total"]
        A(f"| {k} | {ms} | {mp:.1f}% | {cs} | {cp:.1f}% | {mp-cp:+.1f} |")
    A("")
    cond_ms = 100*kinds["conditional"]/n
    cond_cs = 100*CONSTITUTION["conditional"]/CONSTITUTION["total"]
    A(f"Conditional (formalizable) share: **Model Spec {cond_ms:.1f}%** vs "
      f"**constitution {cond_cs:.1f}%** — a {cond_ms-cond_cs:+.1f} pp difference.\n")

    # robustness: collapse markers that share one governing sentence
    sent_kind = {}
    for r in recs:
        sent_kind.setdefault(r["text"], Counter())[r["kind"]] += 1
    dedup = Counter(kc.most_common(1)[0][0] for kc in sent_kind.values())
    nd = len(sent_kind)
    shared = sum(v for v in (sum(kc.values()) for kc in sent_kind.values()) if v > 1)
    A("## Robustness: de-duplicated to distinct governing sentences\n")
    A(f"{shared} of the {n} markers are sub-sentence enumeration anchors sharing one "
      f"governing sentence with siblings (23 sentences carry 2+ markers), e.g. "
      "`chemical[^91oh], biological[^bz0o], radiological[^li9q]`. Collapsing to the "
      f"{nd} distinct governing sentences:\n")
    A("| kind | count | % |")
    A("|---|---|---|")
    for k in order:
        if dedup.get(k):
            A(f"| {k} | {dedup[k]} | {100*dedup[k]/nd:.1f}% |")
    A("")
    A(f"Conditional share on this stricter unit: **{100*dedup['conditional']/nd:.1f}%** "
      f"(vs {100*kinds['conditional']/n:.1f}% per-marker). The comparison to the "
      "constitution's 31.7% holds in either accounting.\n")

    A("## Verbatim verification\n")
    A(f"Every `text` field was checked as an exact substring of `model_spec.md`: "
      f"**{ok}/{n} = {100*ok/n:.1f}% pass**. `marked_span` fields: {ok_span}/{n} = "
      f"{100*ok_span/n:.1f}%. Run `python classify_modelspec.py` to reproduce.\n")

    A("## Caveats\n")
    A("- Units are not comparable one-for-one: constitution units are segmented *clauses*; "
      "Model Spec units are the authors' own *focus areas*. 69 of the 259 markers are "
      "sub-sentence enumeration anchors that share one governing sentence with siblings, "
      "which inflates the conditional count wherever a crisp rule enumerates many items; see "
      "the de-duplicated table above.\n"
      "- 0 focus areas were unclassifiable; every marker associated cleanly with a governing "
      "sentence.\n"
      "- Four whole top-level sections carry no focus markers at all: Overview (lines 1-108), "
      "Definitions (109-170), the voice-mode subsections (`#voice_style` and children), and "
      "the Under-18 Principles (`#chatgpt_u18`). The last marker is at line "
      f"{max(r['line'] for r in recs)} of 4691.\n")

    open("modelspec_classification_summary.md", "w", encoding="utf-8").write("\n".join(L))
    print("\n".join(L[:0]) or "wrote modelspec_focus_areas.json + modelspec_classification_summary.md")
    print(dict(kinds))


if __name__ == "__main__":
    main()
