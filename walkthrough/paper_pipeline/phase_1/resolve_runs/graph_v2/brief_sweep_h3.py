import json, hashlib, os, sys
sys.path.insert(0, ".")
import brief_sweep as B
H3 = B.BRIEFS["H1H2_referent_text"] + """

EXCEPTION to the facet rule, named by the failing cases themselves: the
DEFINITION of a category (what counts as X) and a RULE commanding or
prohibiting X are named separately by this document and are DIFFERENT
concepts. Facets that remain the same concept are e.g. a rule and the
authority level that rule carries, or a mechanism and the ordering it
produces -- not a definition and a command about the defined thing."""
B.BRIEFS = {"baseline": B.BRIEFS["baseline"],
            "H1H2_referent_text": B.BRIEFS["H1H2_referent_text"],
            "H3_category_vs_rule": H3}
cache = json.load(open("brief_sweep_cache.json")) if os.path.exists("brief_sweep_cache.json") else {}
orig = B.judge
def cached(brief, prompt):
    k = hashlib.sha256((brief + "\x00" + prompt).encode()).hexdigest()[:24]
    if k not in cache:
        cache[k] = orig(brief, prompt)
        json.dump(cache, open("brief_sweep_cache.json", "w"))
    return cache[k]
B.judge = cached
B.main()
