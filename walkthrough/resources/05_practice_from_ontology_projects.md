# Practice from ontology projects — what people actually did, and what it cost them

Evidence gathered 2026-08-07. **Primary source is working code**, not write-ups: repositories, commit
histories, fork trees, issue trackers, and — where an artifact shipped data — measurements computed
directly off that data. Papers are cited only where code was unavailable.

Every claim below is tagged with its strength:

| tag | meaning |
|---|---|
| ⓘ **verified** | I ran the check or read the file. Command or file path given. |
| ⚠️ **one instance** | one project did this. Not a norm. |
| ⛔ **unverified** | reported but I could not confirm. Say so out loud. |

---

## 1 ⭐ Who has actually used LKIF-Core, and what happened

### 1.1 The fork tree is a graveyard

ⓘ **verified** — `gh api repos/RinkeHoekstra/lkif-core/forks?per_page=100`, 2026-08-07.

48 forks. I pulled the commit list for every one of them.

| | count |
|---|---|
| forks with **zero** commits of their own | **39 / 48** |
| forks whose only commits are upstream's (forked a PR branch) | 3 |
| forks with **exactly one** own commit | 5 |
| forks with two own commits | 1 |
| forks with a **sustained** line of work (≥3 commits, >1 day) | **0** |

⭐ **Nobody has ever specialised LKIF-Core on GitHub and kept going.** The longest-lived fork is
`hennkar/lkif-core` at two commits, two days apart, then silence.

And of the six forks with their own work, **three of them made the same commit**:

| fork | date | its entire contribution |
|---|---|---|
| [tourtiere](https://github.com/tourtiere/lkif-core) | 2023-04-05 | `replace http://www.estrellaproject.org -> github.com` |
| [hennkar](https://github.com/hennkar/lkif-core) | 2025-05-07 | `Add valid ontology` |
| [wadie999](https://github.com/wadie999/lkif-core) | 2026-01-24 | `Fix broken import links` |
| [palomena](https://github.com/palomena/lkif-core) | 2025-09-04 | `Merged ontologies into single file under new IRI` |
| [alibama](https://github.com/alibama/lkif-core) | 2025-06-27 | `Changes to be committed:` (sic) |
| [emersonbanez/philippine-legal-ontology](https://github.com/emersonbanez/philippine-legal-ontology) | 2018-06-05 | `Initial Checkin` |

### 1.2 ⛔⭐ LKIF-Core does not load. This is the single most practical finding.

ⓘ **verified** — `curl http://www.estrellaproject.org/lkif-core/lkif-core.owl` → **404**.

Every `owl:imports` in every one of the 15 modules points at `http://www.estrellaproject.org/`,
which is dead. So does every namespace prefix, and so does the `xml:base` of every file. The
ontology as published **cannot be loaded by any tool that resolves imports**.

This is not a footnote; it is what the fork tree is *made of*. Five of the six people who ever
touched a fork were fixing this, independently, over three years, without finding each other's fix:

* `wadie999` rewrote all 15 files, 512 changed lines, pointing every IRI at
  `raw.githubusercontent.com/wadie999/lkif-core/master/…`
* `tourtiere` did **the identical rewrite** two years earlier, pointing at their own fork
* `palomena` gave up on modules entirely — *"Merged ontologies into single file under new IRI"*
* `emersonbanez` took the third route: added a `catalog-v001.xml`
  ([file](https://github.com/emersonbanez/philippine-legal-ontology/blob/master/catalog-v001.xml)),
  the Protégé XML-catalog workaround that redirects each dead IRI to a local file

Upstream knows. Both issues are **open and unanswered**:

* [#5 "links are broken in owl files"](https://github.com/RinkeHoekstra/lkif-core/issues/5) — opened
  2025-06-27, 1 comment
* [#9](https://github.com/RinkeHoekstra/lkif-core/issues/9) — opened 2026-03-16, **0 comments**:
  *"Bunch of Errors during `relative-places.owl` conversion to functional owl syntax with robot
  tool: Could not load imported ontology: `http://www.estrellaproject.org/lkif-core/mereology.owl`"*

⇒ ⚠️ **Note what the three fixes cost.** Each rewrites the IRI of every class in the ontology. That
means `tourtiere`'s `Action` and `wadie999`'s `Action` are, to a reasoner, **different classes**.
The workaround for the dead host forks the identity of the vocabulary. `emersonbanez`'s XML catalog
is the only one of the three that does not — it keeps the IRIs and redirects resolution.

### 1.3 ⓘ The 2026 refresh was a licence change, and nothing else

ⓘ **verified** — `gh api repos/RinkeHoekstra/lkif-core/commits/master`.

The "last updated 23 February 2026" in `SCRATCH_concept_phase.md` is real but should be read
correctly. Master's HEAD is a merge of
[PR #7](https://github.com/RinkeHoekstra/lkif-core/pull/7), and the five commits that day are, in
full: *"Updated all files with a CC-BY 4.0 license instead of LGPL. Generated Turtle versions."* /
*"Added license file"* / *"Included CC BY legal code"* / *"Updated readme"* / merge.

**Before that, the previous commit was 2013-01-21.** The CC BY 4.0 claim is confirmed (LICENSE file
present, 18,656 bytes) and the `.ttl` files are new. The *ontology content* is unchanged since 2008.

### 1.4 ⭐ There is no validation of any kind, and never has been

ⓘ **verified** — full repo listing, `gh api repos/RinkeHoekstra/lkif-core/contents`.

The repo contains: 15 `.owl` + 15 `.ttl` files, `README.md`, `LICENSE`, `pyproject.toml`,
`poetry.lock`, and a directory `perf-tests/` containing exactly one file —
`performance-lkif-core-v102-20080208.xls`, a **2008 spreadsheet of reasoner timings**.

* no test suite
* no SHACL shapes
* no competency questions
* **no `.github/workflows` at all** (404)
* `pyproject.toml`'s entire dependency list is `rdflib` — it exists to regenerate the Turtle files

⇒ The field's canonical legal core ontology, 19 years old, 167 stars, has **never had an executable
check**. Whatever "established practice" means in legal ontology engineering, it does not include
testing the ontology.

### 1.5 ⓘ Adoption in code: essentially zero outside benchmarks

ⓘ **verified** — `gh search code "estrellaproject.org/lkif-core" --limit 40`.

Every hit across public GitHub falls into three buckets:

1. the LKIF-Core repo itself
2. **reasoner benchmark fixtures** — `stardog-union/pellet` and `Galigator/openllet` both list
   LKIF-Core in `profiler/src/main/resources/etc/dataset.txt`. It is a performance test case.
3. `SPARQL-Anything/sparql.anything`, which has vendored Apache Any23's generated vocabulary
   constant classes (`LKIFCoreAction.java`, `LKIFCoreRole.java`, …) — machine-generated Java
   constants nobody wrote by hand

⚠️ **Caveat, stated plainly:** GitHub code search does not index every repository, and it misses
private and non-indexed code. But the shape of the result is informative: LKIF-Core is used as a
**test fixture for OWL reasoners**, not as a modelling substrate.

### 1.6 ⓘ Verified: the `norm` module axiom our scratch doc flagged

ⓘ **verified** — `lkif/norm.ttl:285-297`, cloned at HEAD.

```turtle
:Prohibition a owl:Class ;
    rdfs:subClassOf :Permission ;
    owl:equivalentClass [ … owl:allValuesFrom :Obliged ; owl:onProperty :allows … ] .
```

`SCRATCH_concept_phase.md` is correct: `Prohibition rdfs:subClassOf Permission`, with a full
equivalent-class definition in deontic operators. Module sizes, for scoping the "take the names,
refuse the axioms" decision:

| module | classes | object properties |
|---|---|---|
| norm | **67** | 13 |
| expression | 51 | 36 |
| time-modification | 48 | 11 |
| legal-action | 26 | 0 |
| role | 23 | 8 |
| action | 20 | 9 |
| process | 12 | 12 |
| mereology | 6 | 14 |
| legal-role | **3** | 0 |
| lkif-top | 7 | 0 |

⚠️ `legal-role` — one of the three legal modules — contains **three classes**. Do not budget for it
as a tier.

---

## 2 ⭐ The one live, published LKIF-Core specialisation: DAOnt

[`oeg-upm/DAOnt`](https://github.com/oeg-upm/DAOnt) — EU Data Act (Reg. 2023/2854), by the
Ontology Engineering Group at UPM (Poveda-Villalón, Rodríguez-Doncel), arXiv 2604.16386. This is the
best-resourced current example of exactly the move we are making, so I read it closely.

ⓘ Repo health: last push **2025-11-18**, 2 stars, 1 fork, 3 open issues (two of which are
bot-generated metadata-quality reports, unanswered).

### 2.1 ⭐ They took four terms and copied them. They did not import.

ⓘ **verified** — `grep -c lkif DAOnt.ttl` → 13 lines; `grep imports DAOnt.ttl` → **nothing**.

DAOnt has **no `owl:imports` of LKIF-Core at all**. It reuses exactly four LKIF terms, re-declaring
each locally inside `DAOnt.ttl`:

* `expression.owl#Legal_Document`
* `expression.owl#qualifies`
* `role.owl#plays`
* `norm.owl#Right`

That is 4 terms out of ~283 classes. And note *which* four: they took **`norm:Right` as a bare
class**, with none of the norm module's deontic axiomatisation.

⇒ ⭐ **The strongest independent corroboration available for our "take the vocabulary, refuse the
axioms" resolution** — the one professional team doing this in 2026 arrived at the same place, and
went further than we planned: they did not import at all, they MIREOT'd four terms.

⇒ ⭐ **And the reason they could not import is §1.2.** You cannot `owl:imports` a 404.

### 2.2 The concept record, field by field — this part is worth stealing

ⓘ **verified** — property census over `DAOnt.ttl`:

| property | count | over ~40 concepts |
|---|---|---|
| `rdfs:label` | 179 | — |
| `rdfs:comment` | 121 | — |
| `skos:prefLabel` | 40 | ~100% |
| `skos:definition` | 39 | ~98% |
| `skos:scopeNote` | 36 | ~90% |
| `skos:example` | 36 | ~90% |
| `skos:altLabel` | 2 | 5% |

The **SKOS quartet — prefLabel / definition / scopeNote / example — at ~90–100% coverage** is a
concrete, adoptable concept-record schema. A real record (`daont:DataHolder`):

```turtle
skos:prefLabel  "Data Holder"@en , "Titular de Datos"@es ;
skos:definition "A legal or natural person with the right or obligation to control access to data.
                 MANDATORY OBLIGATIONS: (1) Provide data to users upon request (Article 4) via
                 performsLegalAction→DataProvision, (2) Share with data recipients under FRAND
                 terms (Article 8), (3) Justify refusals with trade secrets (Article 8(6))."@en ;
skos:scopeNote  "Defined in Article 2(13). COMPLIANCE ENFORCEMENT: Violations detected when
                 (a) User requests data but holder has no DataProvision action…"@en ;
skos:example    "watchManufacturer (data holder) MUST provide charlieHealthData when Charlie
                 requests it…"@en .
```

⚠️ Note the disease as well as the cure: `skos:definition` here is not a definition. It is a
definition *plus a procedural rule list plus enforcement instructions*, in one string. The record
field has been used as a scratchpad. That is worth avoiding by construction.

### 2.3 ⛔⭐ Clause citations live in English prose. Nothing links to a clause.

ⓘ **verified** — no `dct:source`, no `rdfs:isDefinedBy`, no `prov:` anywhere in `DAOnt.ttl`.

Every reference to the source regulation is a substring of a comment:

```turtle
rdfs:comment "Article 2(13) - Data holder has rights to control access to data" ;
rdfs:comment "Article 5 and Article 8 - Data provision to recipients" ;
rdfs:comment "Data intermediation service as defined in Article 2, point (11), of Regulation
              (EU) 2022/868. Article 2(10) of Regulation (EU) 2023/2854.
              EUR-Lex: https://eur-lex.europa.eu/eli/reg/2023/2854/oj" ;
```

There are 60+ `Article N(M)` strings in the file and **not one of them is machine-readable**. You
cannot ask "which classes derive from Article 5" without regexing English. The one ELI URI present
points at the *whole regulation*, not the article.

⇒ ⚠️ **Independently replicated.** The LLM-generated Chinese contract extension (§3) does the same
thing — `《民法典》第595条` inside `rdfs:comment`. Two unrelated 2026 artifacts, same failure.

⇒ ⭐ Worse, in DAOnt the citation coverage is uneven in an informative way: the classes lifted from
the Data Act's *definitions* article (Art. 2) all carry citations; classes further from the text
carry fewer. Same gradient as our problem #1.

⇒ ⛔ **But do not generalise this into "nobody does it properly." DPV does — see §5.1, which is a
direct correction to an earlier draft of this section.** The practice bifurcates sharply: the
academic-artifact tier (DAOnt, the LLM extension, LKIF itself) puts citations in prose; the one
sustained community-maintained vocabulary puts them in `dct:source` with a resolvable clause-level
URI. The difference tracks maintenance, not competence.

### 2.4 ⛔⭐ The shipped queries do not query the shipped ontology

ⓘ **verified** — three different namespaces for one ontology, in one repo:

| artifact | namespace |
|---|---|
| `DAOnt.ttl` / `DAOnt.owl` (the published ontology, w3id-minted, cited in the paper) | `https://w3id.org/def/daont#` |
| `compliance-checks/queries/*.sparql` (`PREFIX daont:`) | `http://www.semanticweb.org/daont#` |
| `compliance-checks/contracts/*.owl` (`xml:base`) | `http://www.semanticweb.org/daont` |
| `compliance-checks/compliance_checker.py:16` (`DATAACT = Namespace(...)`) | `http://www.semanticweb.org/dataact#` |

`http://www.semanticweb.org/...` is **Protégé's default placeholder namespace**. So the compliance
demo runs against an unreleased Protégé working copy that is not in the repo, while the artifact of
record uses a different IRI. And the checker script's constant doesn't match *either*.

ⓘ There is **no test suite and no CI** in the repo (`gh api .../contents/.github` → 404; the only
`.py` files are `compliance_checker.py`, `run_compliance_check.py`, `dashboard.py`).

⇒ ⭐ **This is our problem #8 — different names for the same thing — occurring at the namespace
level in a peer-reviewed artifact, and surviving publication because nothing executes.** A single
CI job that loaded the published ontology and ran the published queries would have caught it in
seconds. This is the strongest argument in this entire document for executable checks.

### 2.5 The query side, as actually implemented

ⓘ `compliance-checks/queries/query-19.2.a.sparql` — hand-written, one file per article, verdict
strings **hardcoded into the SELECT clause**:

```sparql
SELECT DISTINCT ?b2gSharing ?publicBody ?holder ?action
    ("COMPETITIVE_PRODUCT_DEVELOPMENT" AS ?violationType)
    ("Article 19(2)(a) VIOLATED: Public body used data to develop competing product" AS ?details)
WHERE { ?b2gSharing a daont:B2GDataSharing ; daont:governedBy ?contract .
        ?contract dpv:hasRecipient ?publicBody .
        ?publicBody a daont:PublicSectorBody , daont:DataRecipient .
        ?publicBody daont:performsAction ?action .
        ?action a daont:UseDataToDevelopCompetingProduct . }
```

Three queries exist, for Articles 4(1), 8(6) and 19(2)(a). Each has its expected output pasted into
the file as a comment, and a `Screenshot_*.png` beside it.

⭐ **The honest reading of the query side, from the only implementation available:** there is no
mechanism. A human wrote one SPARQL query per article by hand, hardcoded the English verdict, ran it
once, and screenshotted the result. Three articles out of a regulation with 50. Nothing generalises,
nothing is generated from the ontology, nothing is tested.

⚠️ And note the class `daont:UseDataToDevelopCompetingProduct` — the query only fires if someone has
already asserted the exact violation as a typed instance. That is our problem #5, hollow stubs: the
whole judgement is in the instance data, the query just reports it back.

---

## 3 ⭐ An LLM specialising LKIF-Core, in the wild, July 2026

[`rockgarden/lkif-core-cn`](https://github.com/rockgarden/lkif-core-cn), branch
`中国合同本体扩展-79893` ("Chinese contract ontology extension"). One commit, 2026-07-09, author
`qwen.ai[bot]`, produced by an OpenHands agent. 493 lines of Turtle, 28 classes, 5 properties. PR #1
open, never merged, branch untouched since.

⭐ **This is the closest thing available to a dry run of our own step 3 (minting), performed by a
model, left in public.** Every failure mode in our Part-1 table is visible in it.

ⓘ **verified** by reading the file and mechanically checking every LKIF reference against a fresh
clone of upstream:

| what the file does | our problem |
|---|---|
| `# 注意：由于LKIF-Core中没有预定义的has-identifier属性` — *"since LKIF-Core has no predefined has-identifier property"* — then **invents** `:has-identifier`, `rdfs:domain owl:Thing`, no citation | **#1 made-up things.** The model noticed the gap and filled it rather than stopping. |
| the usage example uses `laction:name`. ⓘ I grepped all 15 upstream modules: **`name` does not exist in LKIF-Core.** (The other 8 referenced terms — `Contract`, `Obligation`, `Legal_Person`, `Agent`, `Proposition`, `qualified_by`, `towards`, `bears` — all resolve.) | **#1**, and it is in the *example*, the part a reviewer would read to check the rest |
| local names in three conventions in one file: `:Chinese_Contract` (PascalCase_underscore), `:has-identifier` / `:obliged-actor` (kebab), `:买卖合同` / `:统一社会信用代码` (Chinese) | **#8/#10.** Convergence failure inside a *single generation*, not across runs. |
| the 11 contract-type classes each cite `（《民法典》第595条）` in `rdfs:comment`; the obligation classes at the tail (`:协助义务`, `:损害赔偿义务`) cite **nothing** | **#1 again**, with the same degradation gradient as DAOnt |
| `dct:created "2025-01-01"^^xsd:date` on a file committed 2026-07-09; `dct:creator "OpenHands AI Assistant"` as a bare string | hallucinated provenance |
| the usage example — the only thing resembling a test — is **inside a `#` comment block**, unexecutable | nothing checks any of the above |
| `owl:imports <http://www.estrellaproject.org/lkif-core/norm.owl>` | the file cannot load (§1.2) |

⇒ ⭐ The model **correctly performed the parts our design says are easy** — it subclassed everything
under `norm:Contract`, used `rdfs:subClassOf`/`rdfs:subPropertyOf` to extend without editing LKIF,
and wrote a clear rationale in the ontology header. It then **failed at exactly the step our design
identifies as the dangerous one**: minting without a licence. The header even announces the correct
principle — *"使用rdfs:subClassOf和rdfs:subPropertyOf扩展而不修改原始LKIF-Core类"* — while the body
violates it.

⚠️ n=1 artifact, and produced by an unknown agent scaffold with no review step. Do not read it as a
measurement of what models do under our pipeline. Read it as an existence proof of the failure shape.

---

## 4 ⭐⭐ The number nobody published: human concept-annotation agreement

This is the most important measurement in this document and I computed it myself, because the
project that produced the data never reported it.

**Source:** [`PLN-FaMAF/legal-ontology-population`](https://github.com/PLN-FaMAF/legal-ontology-population)
— *"Resources for legal ontology population from the MIREL Project."* MIREL was an EU H2020 MSCA-RISE
project on exactly our problem.

ⓘ Repo health first, because it is itself a finding. The complete contents:

* `README.md` — **111 bytes**, restating the repo description
* `mapping_LKIF_YAGO_v1.owl` — 17 KB of hand-written `owl:equivalentClass` links from LKIF classes
  to WordNet/YAGO synsets (`lkif:Code_of_Conduct ≡ yago:wordnet_code_of_conduct_105668095`)
* `ECHR_annotated/annotator{1,2,3,4}/` — CoNLL files, ECHR judgments

Last push **2017-05-15**. 7 stars. No code, no evaluation script, no agreement report.

⚠️ Note what `mapping_LKIF_YAGO_v1.owl` is: it is arm C of our Invariant 1 — resolve concepts via a
general knowledge graph — attempted by the EU project set up to do it, and abandoned at 17 KB.
`SCRATCH`'s judgement that general KGs will not supply this is supported by the only attempt.

### 4.1 The annotation scheme, which is directly adoptable

Each token carries `B-<instance-URI>##<type-URI>`:

```
B-https://en.wikipedia.org/wiki/European_Court_of_Human_Rights##wordnet_trial_court_108336490   Court
B-##wordnet_rape_100773402                                                                      rape
B-##NOT_IN_WIKIPEDIA_assessment                                                                 assessment
```

⭐ Three things worth taking:

1. **Two slots, independently fillable** — an *instance* and a *type*. Either may be empty (`##`).
   A term can be typed without being individuated.
2. **`NOT_IN_WIKIPEDIA_<surface_form>` is an explicit, first-class value.** A term the vocabulary
   does not cover is recorded *as unresolvable, carrying its surface form*, rather than being
   omitted or invented. This is a direct answer to our open question *"what does it do with a term
   the document never defines"* — mark it, keep the word, do not mint.
3. The escape hatch is **countable**, so "how much of this document is off-vocabulary" is a number.

### 4.2 ⭐⭐ The agreement numbers

Three documents were annotated by two annotators each. ⓘ I downloaded all six files and computed
agreement directly (`scratchpad/agree2.py`; token streams are positionally identical for PERUŠ,
5,421 lines each).

| pair | document | tokens | both annotated same token | **same concept** | **different concept** | concept-vocabulary **Jaccard** |
|---|---|---:|---:|---:|---:|---:|
| a2 / a3 | PERUŠ v. Slovenia | 5,123 | 424 | 346 (81.6%) | **78 (18.4%)** | **0.30** |
| a3 / a4 | B.S. v. Spain | 7,098 | 789 | 94 (11.9%) | 695 (88.1%) | **0.24** |
| a1 / a4 | Eğitim v. Turkey | 2,504 | 540 | 281 (52.0%) | 259 (48.0%) | **0.29** |

Exact agreement over all tokens either annotator marked: **39.3% / 5.7% / 33.5%**.

⚠️ **Read the caveats before using these.**

* Only the PERUŠ pair is exactly line-aligned (5,421 = 5,421). The other two differ slightly
  (7,470 vs 7,446; 2,595 vs 2,598), so positional comparison can drift onto coincidentally-identical
  tokens and **inflate the per-token disagreement**. The B.S. figure of 88.1% is very likely an
  artifact and should not be quoted.
* The **Jaccard column is drift-immune** — it compares the *set* of distinct concept labels each
  annotator used anywhere in the file, which has no positional component.
* n=3 pairs, one document each, one corpus (ECHR), 2017.

⭐ **The robust finding, and it is stark: concept-vocabulary Jaccard is 0.30, 0.24, 0.29 — an
extraordinarily stable ~0.27 across three independent annotator pairs.** Two trained human
annotators, given the same ontology, the same guidelines, and the same document, converge on
roughly **a quarter** of the concept vocabulary they produce. On the cleanest pair, where both
independently decided a token was worth annotating, they disagreed on *which concept* **18.4%** of
the time.

Annotator 2 used `NOT_IN_WIKIPEDIA` **0 times**; annotator 3 used it **12 times** on the same
document. Even the "I can't resolve this" behaviour does not converge.

⇒ ⭐⭐ **This is the empirical ceiling on free-form concept assignment, measured on humans.** Our
repo's measured 20% of reused names carrying more than one definition (problem #9) is not a symptom
of using a model. It is the ordinary rate for this task. Any design that requires a *name* to be the
identity of a concept is trying to beat a number that trained humans do not beat.

⇒ ⭐ And it is the strongest available support for `SCRATCH`'s central move — replacing open naming
with **closed classification**. It does not prove closed classification will agree; it proves the
thing it replaces does not.

---

## 5 ⭐⭐ The one project that has actually solved most of this: DPV

[`w3c-cg/dpv`](https://github.com/w3c-cg/dpv) — the Data Privacy Vocabulary, W3C Community Group
(Pandit et al., ADAPT/TCD). ⓘ **verified**: last push **2026-08-06**, 80 stars, 34 forks, **115 open
issues**, versioned release directories `1.0/ 2.0/ 2.1/ 2.2/ 2.3/` checked into the repo.

⭐ This is the outlier in every dimension. It is the only artifact in this survey that is alive, and
— not coincidentally — the only one that answers our questions with running code rather than prose.
Its GDPR extension (`2.1/legal/eu/gdpr/`) is the closest existing analogue to what we are building.

⚠️ **Lineage matters here, and it is a negative result in its own right.** The same group's earlier,
paper-shaped artifacts are dead: ⓘ `coolharsh55/GDPRtEXT` last push **2020-03-31**,
`coolharsh55/GConsent` last push **2019-02-12**. DPV is what survived, and what survived is the one
with a release process.

### 5.1 ⭐⭐ Machine-readable, clause-level citation. This corrects §2.3.

ⓘ **verified** — `2.1/legal/eu/gdpr/eu-gdpr.ttl`, a real concept record in full:

```turtle
eu-gdpr:A6-1-a a rdfs:Class, skos:Concept, dpv:LegalBasis ;
    dct:source [ a schema:WebPage ;
            schema:name "GDPR Art.6-1a" ;
            schema:url "https://eur-lex.europa.eu/eli/reg/2016/679/art_6/par_1/pnt_a/oj" ] ;
    dct:created  "2022-09-07"^^xsd:date ;
    dct:modified "2024-12-17"^^xsd:date ;
    sw:term_status "modified"@en ;
    rdfs:isDefinedBy eu-gdpr: ;
    skos:prefLabel "Art.6(1-a) consent"@en ;
    skos:definition "Legal basis based on data subject's given consent to the processing of his or
                     her personal data for one or more specific purposes"@en ;
    skos:scopeNote "Consent can be explicit or non-explicit…"@en ;
    skos:broader dpv:ExpressedConsent, eu-gdpr:Consent .
```

Four things here that nothing else in this survey has:

1. ⭐ **The citation is a resolvable URI at clause granularity** — `…/art_6/par_1/pnt_a/oj`, an ELI
   URI addressing *Article 6(1)(a)*, not the regulation. ⓘ I counted: **77 clause-level ELI URIs
   (`art_N/…`) and zero whole-regulation-only URIs.** Contrast DAOnt's single `…/2854/oj`.
2. ⭐ **The concept id is the clause id.** `A6-1-a`, `A13`, `A13-Denied`. Isomorphism (our Invariant
   3) enforced by naming convention rather than by documentation.
3. ⭐ **Per-concept versioning**: `dct:created` + `dct:modified` + `sw:term_status`
   (SemWeb vocab-status: ⓘ 216 `accepted`, 7 `modified` across the GDPR extension). A concept
   records its own drift.
4. **A published CSV serialisation beside every RDF format** — `eu-gdpr.csv`, columns
   `term,type,iri,label,definition,dpvtype,subclassof,hasbroader,scopenote,created,modified,vocab,namespace`.
   The concept dictionary is a git-diffable table, and the RDF is generated from it.

ⓘ Coverage over the 223 concepts in the GDPR extension:

| field | coverage |
|---|---|
| `skos:prefLabel`, `skos:definition`, `dct:created`, `sw:term_status`, `rdfs:isDefinedBy` | **100%** |
| `dct:source` (the citation) | **79%** (176/223) |
| `dct:modified` | 21% |
| `skos:scopeNote` | 17% |

⚠️ Note the honest shape of that: even the best-run project in the field cites only **79%** of its
concepts back to the text. 47 concepts have no source. Do not budget for 100%.

### 5.2 ⭐ Amendment handling: a generated, per-concept changelog with named removals

ⓘ **verified** — `2.1/changelog.html`. Every release ships one. From 2.1:

> *"In total, DPV 2.1 and all its extensions contain **9167 concepts**, and compared to 2.0 — **6553
> concepts have been added and 133 concepts removed**."*

And crucially it is not a summary. It enumerates:

* **every removed concept by name, with the reason**: *"Removed concepts include `License` which has
  been renamed to `LicenseAgreement`… The other removed concepts are financial purposes, which have
  been moved to the newly created SECTOR-FINANCE extension. 1: CreditChecking 2: Licence 3: …"*
* **an explicit breaking-change assessment written for downstream consumers**: *"This is potentially
  a minor breaking change if the code relies on instances of data subjects, as these are not present
  by default in the graph but can be inferred…"*
* a section literally titled *"Do I need to update or change something?"*

⭐ That is the discipline our Invariant 3 is supposed to buy us, made concrete: when the vocabulary
moves, **every deletion is named and every rename is traced**, so a downstream consumer can compute
what broke.

⚠️ **What DPV does *not* solve, and it is our question.** Its release cadence tracks *the
vocabulary's* evolution, not the source law's. ⓘ The live instance of source-document amendment in
the tracker is issue *"GDNG: Add hint about new law and pause of development based on old GDNG
2024"* (opened 2026-07-06) — Germany's health-data law changed, and the response was to **flag the
extension stale and pause**, not to migrate it. ⭐ So even here, the answer to "the document was
amended" is *stop, mark it, and tell people* — which is at least a designed failure rather than a
silent one.

⚠️ **Caveat on §5.1–5.2 sourcing:** the DPV facts above are ⓘ mine (I fetched and counted the
`.ttl`, `.csv` and changelog). The GDPRtEXT/GConsent abandonment dates are ⓘ verified via `gh api`.
The characterisation of DPV's internal build pipeline (`290_validate_SHACL.py`, OOPS!/FOOPS! runs at
release) came from a parallel agent and ⛔ **I could not verify it** — there is no `.github/workflows`
directory in the DPV repo and I could not locate the build scripts. Treat "DPV runs SHACL in CI" as
unconfirmed.

### 5.3 FOLIO: a typed diff for concurrent editing

[`alea-institute/FOLIO`](https://github.com/alea-institute/FOLIO) — Federated Open Legal Information
Ontology. ⓘ 44 stars, 7 forks, last push 2026-05-27. An 18 MB single `FOLIO.owl`. **No tests, no
releases, no SHACL** — but it has one thing nobody else does: a merge pipeline.

ⓘ `.github/workflows/webprotege-merge.yml` + `scripts/generate_webprotege_merge.py` (28 KB). It
reconciles a **GUI-authored copy (WebProtégé) against the git-tracked OWL**, on every push that
touches `FOLIO.owl`. The design is worth reading:

* **rdflib for the semantic diff, text operations to apply it** — so the GUI export's formatting
  survives and the diff is not a line diff
* a **typed diff**, not a blob: `new_classes`, `new_alt_labels`, `label_normalizations`,
  `definition_updates`, `new_restrictions`, `new_other_triples`, `removed_labels`, `removals`
* ⭐ **`removals` are logged and never applied** — the code comment says so explicitly
  (`# (s, p, o) triples removed in GH (logged, not applied)`). Deletion is not automated.
* ⭐ **an explicit allowlist of what is safe to delete**, with the reasoning in the source:

  > *"SKOS label predicates whose removals are safe to propagate. These are multi-valued,
  > non-structural labels: dropping one never leaves a concept without a name. Deliberately excludes
  > `skos:prefLabel` (every concept needs one; a 'removed' prefLabel is almost always a rename
  > handled elsewhere) and `skos:definition` (handled as a 1:1 update)."*

⚠️ One project, and it solves *concurrent editing*, not *source-document amendment*. But the shape —
**typed diff, per-category policy, deletions logged not applied, allowlist with written reasons** —
is the mechanism DPV's changelog (§5.2) reports the *output* of. FOLIO shows how to compute it;
DPV shows how to publish it. Together they are the only running answer in this survey.

### 5.4 Everything else has no amendment mechanism at all

⛔ ⓘ DAOnt: no versioning tooling, no diff, no changelog — `owl:versionIRI <…/2.0>` is bumped by
hand. LKIF-Core: 18 years, none. MIREL: dead 2017. AIRO
([`DelaramGlp/airo`](https://github.com/DelaramGlp/airo)): last push 2025-08-01, reads as a finished
paper artifact. ⛔ FinRegOnt (finregont.com) — the other project that explicitly builds on LKIF-Core,
aligning it with FIBO for Dodd-Frank/MiFID II — has, per its own published tutorial, **no validation
against the regulatory text and no versioning discussion**; its validation is "does it open in
Protégé and is it consistent." (Reported by a parallel agent from the tutorial pages; ⛔ I did not
verify this myself.)

---

## 6 Standards worth knowing — briefly

Researched by a parallel agent; ⛔ **I did not independently verify these** and have marked the one
correction that matters.

* **Akoma Ntoso / LegalDocML (OASIS).** `eId` is a stable, *structurally derived* clause identifier
  (`sec_2__list_1__point_4`), not a UUID. `wId` ("was-ID") appears only on renumbering, recording the
  previous `eId` so identity survives. Amendments use dedicated elements referencing `eId`s, not a
  generic diff. Cost: it is a full XML document model; borrowing the ID convention without the markup
  is not really supported.
  [naming convention](https://docs.oasis-open.org/legaldocml/akn-nc/v1.0/csprd01/akn-nc-v1.0-csprd01.html) ·
  [repo](https://github.com/oasis-open/legaldocml-akomantoso) (last push 2022-06-02)
* **ELI.** URI templating + RDF metadata for legislation, widely deployed (EUR-Lex). ⚠️ Operates at
  *document/expression* granularity, **not clause granularity** — it does not solve stable clause
  IDs. [EU Vocabularies](https://op.europa.eu/en/web/eu-vocabularies/eli)
* **⛔ ELTEC is a false lead.** ELTeC is the European Literary Text Collection — a corpus-encoding
  effort for *novels*. There is no ELTEC in the legal-ontology space. Do not carry this forward.
* **DAOnt** — see §2. ⚠️ Correction to the brief's framing: DAOnt is a **compliance-checking**
  artifact (it ships `compliance_checker.py` and per-article violation queries). It is a precedent
  for *LKIF reuse pattern*, not for retrieval.
* **LegalRuleML (OASIS)** vs LKIF: LKIF gives the nouns (OWL-DL concept vocabulary), LegalRuleML the
  norm-logic layer (defeasible deontic rules, exceptions, temporal). Complementary. For
  contradiction-finding without rule execution, LegalRuleML's machinery is more than needed.
* **Point-in-time law.** No cross-jurisdiction standard; `legislation.gov.uk` is the reference
  implementation: a stable `IdURI` per section across all time, plus a dated `DocumentURI`
  (`…/section/38/2020-01-01`) resolving to the text as it stood, with a per-date `Status`.
  [formats](https://legislation.gov.uk/developer/formats/xml)

---

## 7 Ontology-mediated retrieval, as distinct from compliance

⭐ **The brief's suspicion is correct: this is under-served, and I could not find a single
head-to-head number.**

* ⛔ No paper found reports "ontology-guided retrieval beat dense retrieval, with numbers, on a legal
  corpus, for the *provision-relevance* task." Stated as a gap, not smoothed over.
* **SAT-Graph RAG** ([arXiv:2505.00039](https://arxiv.org/abs/2505.00039) /
  [2510.06002](https://arxiv.org/html/2510.06002v1), JURIX 2025) is the closest match: an
  ontology-driven Graph RAG over legal norms that explicitly separates *which provisions relate to X*
  from *is X permitted*, and reifies amendment events as queryable nodes. ⚠️ **One paper, case study
  only (Brazilian Constitution), no benchmark.**
* ⚠️ Do **not** cite LegalGraphRAG ([arXiv:2605.28120](https://arxiv.org/html/2605.28120)) as
  retrieval evidence despite its good numbers (6.3–19.1% over baselines) — its task is legal
  *judgment prediction*, a different thing.
* Every legal-ontology artifact I read in code (DAOnt, the Chinese extension, LKIF's own framework
  modules) is built for the permission question. Retrieval is not what this field builds.

## 8 LLM-assisted ontology population, 2025–26 — reported numbers

⛔ Papers, not code; I verified the repo health of the SLR only.

* **Ontology Population using LLMs** ([arXiv:2411.01612](https://arxiv.org/abs/2411.01612)) — ~90%
  triple-extraction coverage *with modular-ontology prompt guidance*, but GPT-4 82–88%, Llama-3 71%,
  and **some modules at zero coverage** on one schema. Coverage measured by fuzzy string similarity,
  not exact match. The authors call their own evaluation *"comparatively shallow"* and say they
  cannot distinguish missing source text from model error. ⚠️ Read as a weak positive at best.
* **⛔ No paper found reports inter-run or inter-annotator agreement for LLM ontology population.**
  This metric does not appear to exist in the literature yet. ⭐ Which makes §4.2 — human agreement
  on the same task — the only anchor available, and makes `SCRATCH`'s V1 (inter-run κ over a closed
  set) a contribution rather than a routine check.
* [`oeg-upm/llm4oe-slr`](https://github.com/oeg-upm/llm4oe-slr) — systematic literature review, 34
  papers 2018–2025, with extracted-data spreadsheets checked in. Last push 2026-03-04. The best
  entry point for a non-anecdotal view; ⛔ I did not open the spreadsheets.
* Legal-domain hallucination baseline: independent audits of legal AI tools found fabricated
  citations in **17–33%** of responses. ⛔ Second-hand.
* ⛔ Could not find any paper stating "human review cost more than manual modelling" for legal
  ontology population. Closest non-legal analogue: ~40 person-minutes per component for manual review
  ([arXiv:2603.20094](https://arxiv.org/pdf/2603.20094)).

---

## 9 ⭐ Repo health across the field, in one table

ⓘ All figures via `gh api`, 2026-08-07. This is the survey's blunt summary.

| repo | what it is | last push | tests / CI | citation to clause |
|---|---|---|---|---|
| [`w3c-cg/dpv`](https://github.com/w3c-cg/dpv) | Data Privacy Vocabulary, GDPR ext. | **2026-08-06** | ⛔ no `.github/workflows`; build scripts not located | ⭐ `dct:source` → clause-level ELI, 79% |
| [`alea-institute/FOLIO`](https://github.com/alea-institute/FOLIO) | general legal ontology | 2026-05-27 | 1 workflow (merge pipeline), **no tests** | n/a |
| [`oeg-upm/DAOnt`](https://github.com/oeg-upm/DAOnt) | EU Data Act | 2025-11-18 | ⛔ none | ⛔ prose only |
| [`RinkeHoekstra/lkif-core`](https://github.com/RinkeHoekstra/lkif-core) | LKIF-Core | 2026-02-23 (licence only; **content 2008**) | ⛔ none, ever | n/a |
| [`DelaramGlp/airo`](https://github.com/DelaramGlp/airo) | AI risk ontology | 2025-08-01 | ⛔ not checked | ⛔ not checked |
| [`coolharsh55/GDPRtEXT`](https://github.com/coolharsh55/GDPRtEXT) | GDPR as linked data | **2020-03-31** | dead | — |
| [`coolharsh55/GConsent`](https://github.com/coolharsh55/GConsent) | GDPR consent | **2019-02-12** | dead | — |
| [`PLN-FaMAF/legal-ontology-population`](https://github.com/PLN-FaMAF/legal-ontology-population) | MIREL (EU H2020) | **2017-05-15** | 111-byte README | — |
| [`rockgarden/lkif-core-cn`](https://github.com/rockgarden/lkif-core-cn) | LLM LKIF extension | 2026-07-09, PR unmerged | ⛔ example is a comment | ⛔ prose only |

⭐ **One of nine is alive. One of nine cites machine-readably. Zero have a test suite.**

## 10 Leads worth following that I could not open

Both are PDFs that the fetch tool could not extract, and both bear directly on the weakest part of
our design. Flagging rather than smoothing:

* ⛔ **MIREL Deliverable D2.4**, `mirelproject.eu/publications/D2.4.pdf` — *"connecting legal text to
  ontology concepts and instances."* This is the report behind the annotation data I measured in
  §4.2, and it is the single most on-topic document found: it is explicitly about text-span→concept
  linking (our citable derivation), not compliance. **Someone should open this locally.**
* ⛔ **Ming Shi, "The Reuse of a Financial Ontology Driven by Competency Questions"** (U Toronto
  thesis) — the only source found that is *about* the CQ-to-query transition rather than assuming it.
* ⛔ [`oeg-upm/llm4oe-slr`](https://github.com/oeg-upm/llm4oe-slr) — systematic review of 34 papers on
  LLMs for ontology engineering, with the extracted-data spreadsheets checked into the repo (last
  push 2026-03-04). The headline numbers are in the `.xlsx` files; nobody has read them yet.

---

# ⭐ Verdict

## Three things to adopt

### 1. A single CI job that loads the published artifact and runs the published queries

This is not generic advice; it is the specific defect that shipped in the one funded, peer-reviewed,
2026 LKIF-Core specialisation. DAOnt's queries address `http://www.semanticweb.org/daont#`, its
ontology is `https://w3id.org/def/daont#`, and its Python checker uses a third string — **§2.4**.
LKIF-Core itself imports a host that has 404'd for years and nobody upstream has noticed in three
open issues — **§1.2, §1.4**. Neither repo has a workflows directory.

Our equivalent is cheap and immediate: a check that every concept id referenced by any rule resolves
in the dictionary, that every clause id cited exists in the 593, and that the artifact we publish is
the artifact the queries run against.

⚠️ **Nine repos, zero test suites (§9).** DPV is the only one with a plausible internal validation
step, and ⛔ I could not find it — no workflows directory, build scripts not located. Whatever the
norm is in this field, it is not this. Doing it is cheap and would put us ahead of every artifact
surveyed.

### 2. ⭐ DPV's concept record, wholesale — plus MIREL's unresolvable marker

**§5.1.** This is the highest-value transfer in the document, because it is a *format*, it is proven
over 9,167 concepts, and copying it costs a schema decision rather than a project. Per concept:

| field | why |
|---|---|
| id **= the clause id** (`A6-1-a`) | Invariant 3 enforced by naming, not by documentation |
| `dct:source` → a **resolvable clause-level URI** | the citable derivation, machine-readable. Not prose. |
| `skos:prefLabel` / `skos:definition` / `skos:scopeNote` | the read-back renders the *definition*, per Invariant 1 |
| `dct:created` / `dct:modified` / `term_status` | the concept records its own drift |
| a **CSV as the source of record**, RDF generated from it | the dictionary is git-diffable and reviewable by a human |

Add MIREL's `NOT_IN_<vocab>_<surface_form>` as a first-class value (**§4.1**) — our open question
about terms the document never defines has a published answer: mark it unresolvable, keep the
surface word, make it countable, do not mint.

⛔ **And note the realistic target: DPV cites 79% of its concepts, not 100%.** Set the floor there,
not at perfection, and make the uncited 21% *visible* rather than absent — which is what our
licence-class scheme (textual / assumed / world) already does better than DPV does.

### 3. A named-removal changelog per revision, computed from a typed diff

**§5.2 + §5.3.** When the spec is amended, DPV's release note enumerates **every removed concept by
name with its reason**, states renames explicitly, and carries a breaking-change assessment written
for downstream consumers. FOLIO shows the mechanism that produces such a thing: a diff typed by
change category, an allowlist of what may be auto-removed **with the reasoning written into the
source**, and — the part worth stealing outright — **removals logged and never auto-applied**.

Our Invariant 3 (one clause, one module) is what makes this computable for us. Neither project got
there by accident; both wrote the deletion policy down before automating it.

---

## ⛔ The one thing we are doing that this evidence says will fail

**Competency questions written first (pipeline step 0) will not survive contact, and the query side
will not be a mechanism — it will be one hand-written query per question, and the count will be
small.**

Stated plainly, because the brief asked for it plainly.

The pipeline in `03_pipeline.md` opens with *"0. COMPETENCY QUESTIONS — the questions this body of
knowledge must answer — written FIRST"*, and it is the one box with no arrow describing how a
question becomes an executable thing. The brief already flags it as the least-written-down part of
the design. Here is what the code says about that gap:

* **Nobody has an executable competency question.** Not LKIF-Core (no tests, no CI, ever — **§1.4**).
  Not DAOnt (no tests, no CI — **§2.4**). Not FOLIO (no tests — **§5**). Not MIREL (no code at all —
  **§4**). Across every artifact I opened, the count of competency questions expressed as running
  code is **zero**.
* **The one implementation of the query side that exists is three hand-written SPARQL files with the
  English verdict hardcoded in the SELECT clause and the expected output pasted underneath as a
  comment** — for a regulation with ~50 articles (**§2.5**). That is what "the query side" looks like
  when a funded ontology-engineering group ships it in 2026.
* And it degenerates: `?action a daont:UseDataToDevelopCompetingProduct` only fires if a human
  already asserted the violation as a typed instance. The query reports a judgement it did not make.
  That is our problem #5 arriving through the query layer, which is not where we are watching for it.
* ⛔ **The one project that got everything else right did not build a query side at all.** DPV
  (**§5**) — 9,167 concepts, clause-level citations, a real release process — is oriented at
  *metadata annotation* (tag a dataset with `dpv:hasLegalBasis`), not at answering open questions.
  There is no CQ→SPARQL framework in it. The project with the resources to build the query side
  chose a different shape of problem.
* ⛔ **And where CQs were taken seriously, the unanswerable ones were quietly dropped.** The
  GConsent/GDPRov line explicitly reports that some compliance questions *could not be expressed in
  SPARQL and were removed as "out of scope"* — **without reporting how many**. (Reported by a
  parallel agent from the project write-ups; ⛔ I did not verify the primary text.) That is the exact
  failure mode to expect: the questions that survive to the paper are the ones the ontology happened
  to answer, and the attrition rate is never published.

⚠️ **Be precise about the claim.** I am not saying competency questions are worthless — they scope
the ontology, and that is real. I am saying the design currently treats step 0 as *generating* the
query side, and there is no instance in this literature of that transition being made. The evidence
says CQs function as **scoping prose that is never executed**, and that the query side gets built
later, by hand, one question at a time, in numbers far below what the document has clauses.

⇒ The concrete risk for us: we write competency questions, build 593 clause modules, and then
discover that turning *"which passages bear on this behaviour"* into something the modules answer is
an unbudgeted second project. `SCRATCH`'s Test 1 and Test 2 both validate the *concept* layer. **No
test in either document validates that a question can be answered at all.** That is the hole, and
this literature has not filled it for anyone else either.
