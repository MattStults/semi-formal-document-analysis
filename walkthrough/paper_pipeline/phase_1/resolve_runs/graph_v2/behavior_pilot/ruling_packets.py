"""Ruling packet generator for the generalization runs + defensibility batch.

Produces BLIND packets for Fable adjudication (Matt's venue, post-reset):
each packet carries the passage span + the behaviour definition + the ruling
question, and NOTHING ELSE — no instrument prediction, no draw side
(engaged/not), no prior truth, no panel verdict. Packets are input to the
round-4-lineage ruling protocol: single blind rulings + seeded 20%
three-instance panels.

Outputs:
  ruling_packets/generalization_<slug>.json   (40 packets per behaviour)
  ruling_packets/defensibility_batch.json     (28 nodes, delta-behaviour keyed)

Span source: ctx_chunk1-8 + ctx_ext1-3 packets, trimmed to SOURCE TEXT.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CONV = os.path.join(HERE, "panel_run1", "convergence")
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", "..", ".."))
DEFS = os.path.join(REPO, "data", "panel-v5", "behaviour-definitions-v5.json")

V5_SLUG_MAP = {
    "harmlessness-to-user": "harmlessness-to-user",
    "objectivity-on-contested-questions": "objectivity",
    "how-to-approach-tradeoffs": "tradeoffs",
    "user-autonomy": "user-autonomy",
    "proportionate-risk-mitigation": "proportionate-risk",
    "general-welfare": "general-welfare",
}

RULING_PROMPT = (
    "You are a blind adjudication seat. QUESTION: does the PASSAGE below bear "
    "on the BEHAVIOUR defined below — would a careful reader of the document "
    "say this passage is among the ones someone consulting the document about "
    "this behaviour should be pointed at? Answer RELEVANT or NOT_RELEVANT, "
    "then one sentence of grounds citing the passage. Judge the passage "
    "against the definition only; you have no other information and need "
    "none.\n\nBEHAVIOUR: {label}\nDEFINITION: {query}\nBOUNDARY: {boundary}\n\n"
    "PASSAGE ({node}):\n{span}"
)


def load_spans():
    import glob
    out = {}
    paths = sorted(glob.glob(os.path.join(CONV, "ctx_chunk*.json"))) + \
            sorted(glob.glob(os.path.join(CONV, "ctx_ext[0-9].json")))
    for p in paths:
        for nid, pkt in json.load(open(p)).items():
            span = pkt.get("span", "")
            i = span.find("SOURCE TEXT")
            out[nid] = span[i:] if i >= 0 else span
    return out


def main():
    spans = load_spans()
    defs = json.load(open(DEFS))
    os.makedirs(os.path.join(HERE, "ruling_packets"), exist_ok=True)

    # generalization packets
    import glob
    for draw_file in sorted(glob.glob(os.path.join(HERE, "generalization_builds", "draw_*_seed*.json"))):
        d = json.load(open(draw_file))
        slug = d["slug"]
        v5 = V5_SLUG_MAP[slug]
        dfn = defs[v5]
        packets = []
        for n in d["draw_engaged"] + d["draw_not_engaged"]:
            packets.append({
                "node": n,
                "prompt": RULING_PROMPT.format(
                    label=dfn.get("label", v5),
                    query=dfn.get("query", ""),
                    boundary=dfn.get("boundary", ""),
                    node=n, span=spans.get(n, "SPAN MISSING")),
            })
        dest = os.path.join(HERE, "ruling_packets", f"generalization_{slug}.json")
        json.dump({"_": "BLIND adjudication packets (no instrument prediction, no draw side, no truth). Protocol: single rulings + seeded 20% three-instance panels (round-4 lineage). Seed for panel selection registered at ruling time.",
                   "slug": slug, "n": len(packets), "packets": packets},
                  open(dest, "w"), indent=1)
        print(f"wrote {os.path.basename(dest)}: {len(packets)} packets")

    # defensibility batch packets
    proto = json.load(open(os.path.join(HERE, "DEFENSIBILITY_BATCH_PROTOCOL.md".replace(".md", ".md")))) if False else None
    batch = {
        "helpfulness|empowerment": ["l3596_3876_n039", "l427_460_n003", "l797_830_n004"],
        "helpfulness|trust": ["l1707_1973_n025", "l2474_2554_n002", "l2821_3040_n005",
                              "l2821_3040_n019", "l2821_3040_n020", "l2821_3040_n027",
                              "l3505_3595_n003", "l3954_4251_n003", "l4572_4692_n009"],
        "helpfulness|predictability-and-reliability": ["l1707_1973_n034", "l171_426_n035",
                              "l1974_2125_n007", "l1_170_n083", "l3383_3501_n003",
                              "l3383_3501_n014", "l3954_4251_n027", "l3954_4251_n029",
                              "l426_610_n029", "l461_608_n007", "l461_608_n018", "l461_608_n021"],
        "avoiding-over-and-under-caution|harm-prevention": ["l1707_1973_n029"],
        "avoiding-over-and-under-caution|epistemic-autonomy": ["l2126_2404_n001",
                              "l2126_2404_n003", "l2126_2404_n010", "l797_830_n004"],
    }
    v18 = json.load(open(os.path.join(HERE, "modules_contract_v18.json")))["modules"]
    packets = []
    for key, nodes in batch.items():
        slug = key.split("|")[0]
        delta = key.split("|")[1]
        dfn = v18[slug].get("module", {}).get("definition") or v18[slug].get("definition", "")
        for n in nodes:
            packets.append({
                "node": n, "behaviour": slug, "delta": delta,
                "prompt": RULING_PROMPT.format(
                    label=slug, query=dfn if isinstance(dfn, str) else json.dumps(dfn),
                    boundary="(see definition)", node=n, span=spans.get(n, "SPAN MISSING")),
            })
    dest = os.path.join(HERE, "ruling_packets", "defensibility_batch.json")
    json.dump({"_": "BLIND defensibility-adjudication packets (DEFENSIBILITY_BATCH_PROTOCOL.md): the 9b arithmetic's new false positives, one pass, no iteration. Question per node: does this passage bear on the delta's behaviour? Charter recomputed on rescued counts after rulings.",
               "n": len(packets), "packets": packets},
              open(dest, "w"), indent=1)
    print(f"wrote defensibility_batch.json: {len(packets)} packets")


if __name__ == "__main__":
    main()
