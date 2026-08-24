#!/usr/bin/env python3
"""Build the seat-facing dispatch file for the defensibility batch.

Deterministic; reads defensibility_batch.json (already shuffled under the
registered seed), writes defensibility_dispatch.txt containing ONLY what the
seat may see: a row number and the packet's prompt string. No node ids, no
behaviour/delta routing, no seed.

PANEL SELECTION (registered in DEFENSIBILITY_BATCH_PROTOCOL.md, 2026-08-24,
BEFORE dispatch): the protocol's "seeded 20% three-instance panels" is
operationalized exactly like graveyard.should_keep's deterministic sampler —
row i (1-based, the shuffled order) is PANELED iff
int(sha256(f"panel:{BATCH_SEED}:{i}").hexdigest()[:8], 16) / 0xFFFFFFFF < 0.2,
with BATCH_SEED = 20260829 (the registered base 20260823 + 6, this batch's
already-registered shuffle seed — no new constant). Panel rows get THREE
independent fresh-session rulings on the identical prompt; majority
supersedes the single ruling. The paneled row numbers are printed to stdout
(campaign material, NOT part of the dispatch file — the seat never learns
which rows are paneled; the extra instances are fresh sessions that see one
prompt each, like any other row).
"""

import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
BATCH_SEED = 20260829  # = registered base 20260823 + 6 (protocol R2 section)
RATE = 0.2


def paneled(i):
    h = hashlib.sha256(f"panel:{BATCH_SEED}:{i}".encode()).hexdigest()[:8]
    return int(h, 16) / 0xFFFFFFFF < RATE


def main():
    batch = json.load(open(os.path.join(HERE, "defensibility_batch.json")))
    rows = batch["packets"]
    out = []
    panels = []
    for i, p in enumerate(rows, 1):
        out.append(f"=== RULING {i} of {len(rows)} ===\n\n{p['prompt']}\n")
        if paneled(i):
            panels.append(i)
    path = os.path.join(HERE, "defensibility_dispatch.txt")
    with open(path, "w") as f:
        f.write("\n".join(out))
    print(f"wrote {path}: {len(rows)} prompts")
    print(f"PANELED rows (campaign material, seed {BATCH_SEED}, rate {RATE}): "
          f"{panels}")


if __name__ == "__main__":
    main()
