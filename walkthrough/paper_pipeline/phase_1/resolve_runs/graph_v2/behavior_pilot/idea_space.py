#!/usr/bin/env python3
"""A9: the differentiable-idea space, computed mechanically (see
ERROR_CALCULUS.md A9). Counts distinct feature vectors over the corpus
(the maximum number of ideas the instrument can express at inventory k),
the multi-node vector classes (provably indistinguishable twins), and how
many of those classes carry the BYTE-IDENTITY absolute-exhaustion
certificate (identical claims: no reading can separate them) vs textually
distinct (a groundable distinction exists in principle -> any exhaustion
there is SUSPENDED-OPEN, never terminal). NOTE: vectors here are the
unmasked full-feature view (load_layers already folds context atoms into
signature contexts), so this bounds the finest per-inventory granularity;
per-behavior CURRENT masking is coarser."""
import json, sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import satisfiability_census as SC
import relevance_by_act as RBA
sig, ap, pa, ctx = SC.load_layers()
br = RBA.bridges(); corpus = RBA.corpus_acts(); asorts = RBA.arg_sorts()
ref = SC.load_refinements()
vec = {n: SC.vector(n, corpus, br, sig, ap, pa, None, asorts, ref) for n in corpus}
groups = collections.defaultdict(list)
for n, v in vec.items(): groups[v].append(n)
nc = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "node_corpus_all.json")))
byid = {c["id"]: c for c in nc["clauses"]}
multi = {tuple(sorted(ns)) for v, ns in groups.items() if len(ns) > 1}
cert = [g for g in multi if len({byid[n]["quote"] if n in byid else n for n in g}) < len(g)]
out = {"corpus": len(corpus), "distinct_vectors": len(groups),
       "twin_nodes": sum(len(g) for g in multi), "multi_classes": len(multi),
       "byte_identity_certificates": len(cert),
       "textually_distinct_open_classes": len(multi) - len(cert)}
print(json.dumps(out, indent=1))
