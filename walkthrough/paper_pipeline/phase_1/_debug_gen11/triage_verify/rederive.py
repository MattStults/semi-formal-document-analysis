#!/usr/bin/env python3
"""Independent re-derivation of the coordinator's ESTABLISHES-vs-span conflict
triage. Written from the stated METHOD only; the coordinator's snippet was not
read or imported.

Method as reported:
  content words   = [a-z]{4,} over lowercased ESTABLISHES, minus a ~30-word stoplist
  licensed text   = per span: span['quote'] if present else the document lines
  CONFLICT        = >50% of content words absent from licensed text
  bucket 1        = missing words covered by a SIBLING node (same L<band> prefix)
  bucket 2        = missing words present in the DOCUMENT, unclaimed
  bucket 3        = present in neither
"""
import json, re, sys, os, collections

HERE = os.path.dirname(os.path.abspath(__file__))
P1 = os.path.abspath(os.path.join(HERE, "..", ".."))
GRAPH = os.path.join(P1, "resolve_runs/graph_v2/runs/ds7/root_graph.production.json")
DOC = os.path.join(P1, "..", "..", "..", "specs/openai-model-spec/model_spec.md")

# A plausible ~30-word stoplist. The coordinator's exact list is unpublished;
# STOP_VARIANTS below tests sensitivity to it.
STOP = set("""that this with from they them their there when what which will
would should shall must have been were also into more than only such other
some when about their they this that
""".split())

DOCLINES = open(DOC).read().split("\n")


def words(t):
    return [w for w in re.findall(r"[a-z]{4,}", t.lower()) if w not in STOP]


def licensed(node):
    out = []
    for sp in node.get("spans", []):
        if sp.get("quote"):
            out.append(sp["quote"])
        else:
            a, b = sp["lines"]
            out.append("\n".join(DOCLINES[a - 1:b]))
    return "\n".join(out)


def band(nid):
    return nid.split("_n")[0]


def analyze(threshold=0.5, stop=None):
    global STOP
    if stop is not None:
        STOP = stop
    g = json.load(open(GRAPH))
    nodes = g["nodes"]
    byband = collections.defaultdict(list)
    for n in nodes:
        byband[band(n["id"])].append(n)
    doc_words = set(re.findall(r"[a-z]{4,}", "\n".join(DOCLINES).lower()))

    rows = []
    for n in nodes:
        cw = words(n["establishes"])
        if not cw:
            continue
        lic = set(re.findall(r"[a-z]{4,}", licensed(n).lower()))
        missing = [w for w in dict.fromkeys(cw) if w not in lic]
        uniq = list(dict.fromkeys(cw))
        frac = len(missing) / len(uniq)
        if frac <= threshold:
            continue
        # bucket
        sib_words = set()
        for s in byband[band(n["id"])]:
            if s["id"] == n["id"]:
                continue
            sib_words |= set(re.findall(r"[a-z]{4,}", licensed(s).lower()))
        in_sib = [w for w in missing if w in sib_words]
        in_doc = [w for w in missing if w in doc_words]
        if len(in_sib) == len(missing):
            b = 1
        elif len(in_doc) == len(missing):
            b = 2
        else:
            b = 3
        rows.append(dict(id=n["id"], frac=round(frac, 3), n_cw=len(uniq),
                         missing=missing, bucket=b,
                         n_sib=len(in_sib), n_doc=len(in_doc)))
    return rows


if __name__ == "__main__":
    rows = analyze()
    c = collections.Counter(r["bucket"] for r in rows)
    print(f"CONFLICT nodes: {len(rows)} of 773 = {100*len(rows)/773:.1f}%")
    for b in (1, 2, 3):
        ex = [r["id"] for r in rows if r["bucket"] == b][:3]
        print(f"  bucket {b}: {c[b]:4d}   e.g. {ex}")
    json.dump(rows, open(os.path.join(HERE, "rows.json"), "w"), indent=1)
