# Hutter technology audit and ten cross-domain experiment designs

Research date: 10 November 2026. Status: literature and design audit, **not new
compression measurements**. No competitor executable/source package, model, or
hardware was downloaded. Author documentation and research papers were read.
Success requires at least 1% below the current official full-corpus counted
record. Method ablations diagnose mechanisms; inferior project compressors are
not the competitive target. Research has no artificial time budgets.
The index page reports a 14 October 2026 update; retrieved HTML SHA-256 is
`14e052254b2f65837074d0dd05194ff544753c354c1f5b2313751d3872d1193a`.

## Scope, evidence and main finding

The [Large Text Compression Benchmark][ltcb] is broader than the Hutter Prize.
Its ranking is not the prize scoring table. This audit covers the publicly named
prize-related submissions/builds in its 14 October 2026 descriptions/history
snapshot, cross-checked
against the [official prize record][hutter], including unsuccessful, withdrawn,
pending and ineligible entries. Ordinary benchmark programs are classified by
technology below; they are not silently counted as prize submissions. Unpublished
submissions and details absent from documentation cannot be audited. Grouped
versions share a documented mechanism; grouping does not assert identical code.

Evidence labels: **D** = mechanism documented by author; **I** = lineage-based
inference, not independently verified internals; **U** = unresolved. Pending and
ineligible statuses below reflect the cited public records, not a new committee
decision; those classifications may be stale on the research date. No
implementation audit or independent reproduction of competitors
was performed.

The target is the fixed 2006 Wikipedia XML dump, not today's Wikipedia syntax or
facts. Text can contain errors and inconsistent assertions. Physical conservation
laws do not automatically constrain prose: every inferred relation must either
hold exactly for the coded data or have paid exceptions. [Corpus index][ltcb]

The main pattern is architectural convergence: most successful prize entries
combine reversible corpus transforms, several classical statistical experts,
neural probability mixing, and increasingly strong learned predictors. Packaging,
memory layout and decoder/model description length are consequential, but are
not additional information sources. The ten proposals later in this file seek
different source representations or tractable joint models. None is a proven
improvement, and **none is certified globally novel**. The proposed enwik9
instantiations and their closest prior art are stated explicitly.

## 1. Prize-related submission coverage

### Historical records and intermediate builds

| Public names covered | Public role/status | Underlying technology; evidence and limits |
| --- | --- | --- |
| `paq8f` | enwik8 baseline | Bitwise context experts, adaptive neural mixing, arithmetic coding; D. [PAQ history][paq] |
| `durilca 0.5(Hutter)` | Rejected for memory use | Byte-context/PPM lineage; historical internals are not fully documented here; I/U. [Official submissions][hutter] |
| `raq8g` | Sub-1% improvement and other eligibility issues | PAQ-derived mixer with bracket/parenthesis nesting contexts; D. [PAQ history][paq], [official submissions][hutter] |
| `paq8hkcc` | Received submission, superseded by hp1 | PAQ-family modeling and text preprocessing; I for mechanisms not separately described. [PAQ history][paq], [official submissions][hutter] |
| `paq8hp1`, `hp2`, `hp3`, `hp4` | Early/superseded builds | PAQ-derived context mixing plus corpus-specific word/text transformation. No new coding principle established for each revision; D/I. [PAQ history][paq] |
| `paq8hp5`, `hp6` | hp5 award; hp6 intermediate | Same broad model/transform family; D. [PAQ history][paq], [official history][hutter] |
| `paq8hp7`, `hp7a` | Intermediate; hp7a withdrawn | Same family; public withdrawal is not an algorithmic refutation. Details of each change remain U. [Index history][ltcb] |
| `paq8hp8`, `hp9`, `hp10`, `hp11` | Intermediate builds | Same family; hp8 had a corrected release. Individual undocumented internals remain U. [PAQ history][paq] |
| `paq8hp12` | Award | Corpus-specialized PAQ mixture and reversible text/dictionary processing; D. [PAQ history][paq] |
| `HKCC-2` (2007 builds) | Added, updated, then withdrawn in index history | Formal submission status, authorship/technology details unresolved; **U**, not assigned a guessed algorithm. [Index history][ltcb] |
| `decomp8`, `decomp8b`, `decmprs8` (2009) | Successive enwik8 records; final award | Decoder/archive-only historical material does not establish all model internals. PAQ/lpaq proximity is lineage context, not proof of architecture; I/U. Official and benchmark naming/date conventions differ. [Official history][hutter], [index][ltcb] |
| HP-2017 original; public `phda9` 1.0, 1.2–1.8 | Original enwik8 award; public follow-up builds; v1.8 enwik9 baseline | Specialized frontend reuse is documented by STARLIT; D applies to that frontend. Original closed-decoder model internals remain U. Distinguish original and public variants; not eight awards. [STARLIT][starlit] |
| STARLIT May 10/31, 2021 | Awarded lineage | HP-2017 frontend plus cmix; article embedding/order optimization; D. [Author documentation][starlit] |
| `cmix-hp` v1, v2, v3 | Submitted; not an additional award in official table | STARLIT derivative; enlarged disk-backed PPM and model/frontend revisions; D. [Author documentation][cmixhp] |
| `fast-cmix` | Award | Speed/resource refinements in cmix-hp/STARLIT lineage; not a fundamentally different representation; D/I. [Submission announcement][fastcmix] |
| `fx-cmix` | Award | FXCM expert replaces the earlier PAQ8HP expert; richer parsed structural contexts; D. [Author documentation][fxcmix] |
| `fx2-cmix` | Award | Word/stemming streams, revised frontend and dictionary handling, embedding-derived article order; D. [Author documentation][fx2] |
| `fx3-cmix` | Hutter-formatted, ineligible in index | Further article order/model refinements in the FXCM lineage; I where unpublished changes are not specified. This is not `cmix-lex`. [cmix-lex author clarification][lex] |

`hp9any`, `hp10any`, `hp11any`, `hp12any` compatibility builds, ordinary PAQ/cmix releases, and public phda9
maintenance versions are context, not extra official submissions or awards.
The official eleven award slots are hp5, hp12, the 2009 winner, HP-2017,
STARLIT, fast-cmix, fx-cmix, fx2-cmix, cmix-lex, cmix-obias and fx2-cmix-T.
[Official award record][hutter]

### Modern branches and benchmark-only neighbors

| Entry/builds covered | Record classification | Documented change and implication |
| --- | --- | --- |
| `cmix-lex` | Award | Reversible structured-tail reordering, compact restoration information including Lehmer ranks, stronger FXCM integration. Structural simplification and permutation coding are already used. D. [README][lex] |
| `cmix-obias`, AMD/Intel builds | Awarded entry with platform builds | Online byte-LSTM, small correction model, PPMd prior, inference optimization. A paid offline correction model is already used. D. [Author model card][obias] |
| `fx2-cmix-transformer`, original/fixed builds (`fx2-cmix-T`) | Award | Replaces a recurrent predictor with a small pretrained, quantized transformer while retaining classical experts and PPM input. Learned weights and CPU inference are part of the package. D. [Author writeup][fx2t] |
| `zmix 1.0` | Pending in index | Model-bank/mixer rewrite, retraining, weight-storage optimization. Author distinguishes the unsubmitted 1.0.1 from 1.0. D. [README][zmix], [writeup][zmixwrite] |
| `cmix-lex-transformer lexth11c` | Pending in index | Transformer training/quantization and memory/mixer redistribution within the same hybrid architecture. D. [README][lexth] |
| `cmix-neif` pre/pre2/pre3/pre3f, 1.0 | Preliminary builds; 1.0 pending in index | Combines transformer, small recurrent correction, classical experts, dictionary-label and structural models; frontend and model training coupled to its stream. D. [Author lineage and architecture][neif] |
| `forge-cmix`, v2 | Ineligible/formatted entry | FXCM pruning, match expertise and recurrent-model resource balancing. D. [Author description][forge] |
| `fx-deepmix` | Ineligible/formatted entry | Index reports grammar/metadata changes plus a two-layer, 200-cell online LSTM and inference/training revisions. No independent author architecture was established; I/U. [Index][ltcb] |
| `fractal-zip` | Ineligible/formatted entry | Compressed-memory PPM heap is a central change; the name does not establish fractal source encoding. D. [Author submission description][fractal] |
| `fx2-cmix-T-ft8` | Ineligible/formatted entry | Additional model training/quantization in the existing transformer branch. D. [Author documentation][ft8] |
| `makimono` | Ineligible/formatted entry | Transformer/quantization/model-bank refinements in a zmix-derived branch. D. [Author documentation][makimono] |
| `ex-girlfriend` | Ineligible/formatted entry | Adds an online auxiliary predictor of sparse intermediate transformer features, retaining the original transformer. D. [Author documentation][exgirlfriend] |
| RATA-CMIX; named upstream `fx4-cmix-transformer` | RATA explicitly not a Hutter candidate; upstream formal status unestablished | Transformer plus additional recurrent/classical specialists. Included to delimit scope, not counted as formal prize submissions. D/U. [Author README][rata] |
| `altxs`; `tufazip` v1/v2 | LTCB GPU entries; formal Hutter submission unestablished | Large neural compression experiments outside the ordinary prize resource setup. D/U for formal status. [altxs][altxs], [tufazip][tufazip] |

The later benchmark leaders are not automatically later official prize winners.
Author totals and committee totals can differ. This report therefore does not
merge their scores into a new official ranking. [Official record][hutter]

On the research date the official record is 100,424,672 bytes; at least 1%
improvement requires an integer total no larger than 99,420,425 bytes. Under
the separate-codec relaxation the score is `C.zip + 2 D.zip + archive + options`;
when C and D are identical it becomes `2 shared.zip + archive + options`.
All required models/inverse data must be included, rather than assumed installed
side information. [Official record][hutter], [scoring rules][rules]

### What these programs actually encode

| Mechanism | Information represented | Examples/primary evidence | Opportunity already occupied |
| --- | --- | --- | --- |
| Classical context mixtures | Probabilities of the next bit from byte/word/match/structure contexts | [PAQ][paq], [cmix-neif architecture][neif] | Adding contexts or another mixer is incremental, not a new source representation. |
| PPM/context trees/DMC | Conditional symbol/bit distributions backed off or adapted over history/state | [CTW][ctw], [DMC][dmc], [cmix-hp][cmixhp] | Longer context and adaptive state construction are established. |
| Dictionary/LZ/grammar | Reused phrases, offsets, nonterminal expansions | [LZ77][lz77]; benchmark families include LZMA, Brotli, GLZA and BPE | New token names alone do not change description length after dictionary cost. |
| BWT/sort/symbol-rank transforms | Reversible context grouping and rank histories | [Original BWT report][bwt]; bzip2/bsc/M03 families in index | Reordering into an easier stream is an old, powerful principle. |
| Corpus structure transforms | XML restoration, metadata, word coding, morphology, article permutation | [fx2][fx2], [cmix-lex][lex], [STARLIT][starlit] | Simplification, semantic ordering and compact restoration are not unoccupied categories. |
| Recurrent/attention predictors | Learned distributions, online state, shipped pretrained parameters | [cmix-obias][obias], [fx2 transformer][fx2t], [NNCP][nncp] | Embeddings, neural states, pretraining and quantization are already present. |
| Arithmetic/range/ANS | A near-probability-length serialization of modeled choices | [ANS][ans] | A new numeral base or coder alone cannot recover redundancy the model does not expose. |
| Resource engineering | More useful prediction within CPU/RAM/model-byte limits | [fractal-zip][fractal], [zmix][zmixwrite], [forge][forge] | Compressed heaps and model pruning improve feasibility, not the intrinsic data description. |

This taxonomy also accounts for ordinary non-prize LTCB families; it is not a
claim to have reverse-engineered every proprietary archiver on the page.

## 2. What a physical bridge must accomplish

A physical analogy is useful if it gives a shorter **finite, reconstructible
description** or a better tractable joint probability model. It need not use
physical hardware. Our candidates are CPU simulations/algorithms inspired by
those mechanisms; physical storage density is a different objective.

For an exact invertible representation `z=T(x)`, entropy is unchanged under the
same source distribution. This does not forbid useful transforms: `z` can make
regularity accessible to a much cheaper model. Nor does an average entropy bound
for a source prove that a particular fixed corpus cannot have a short program.
The relevant test is its **complete description length**. [Shannon][shannon]

For a model/scaffold `m`, a useful accounting identity is:

`L_total = program/package + model + structure + choices + exact residual + framing`.

These terms must not be double-counted when a single joint code replaces several
channels. Encoder-only training/search need not run at decode; its implementation
and dependencies belong in the compressor package. Decoder inference and the
selected model, mappings and choices it actually needs belong in the decoder
package/data. A training seed is unnecessary when the final parameters suffice;
a generation seed matters if reconstruction uses it. A transformed intermediate byte
count, embedding dimension or scientific model-fit score is not a codelength.

Four attractive-looking shortcuts need special care:

- **Analog amplitudes, chaotic seeds, optical holograms:** finite precision,
  noise, phase and ambiguity carry information. Replacing many bits by a real
  number does not make its required precision free. [Shannon][shannon],
  [finite-alphabet phase retrieval][phase]
- **Quantum amplitudes:** a state vector's exponentially many coordinates are
  not freely readable classical storage. Schumacher compression concerns quantum
  source states; Holevo bounds accessible classical information. Tensor-network
  algorithms can still be useful on an ordinary CPU. [Schumacher][schumacher],
  [Holevo][holevo]
- **Astrophysical “lossless” summaries:** MOPED preserves parameter-estimation
  Fisher information under assumptions, rather than every original observation.
  Applying its summaries to text would still require exact residual information.
  This is a domain-specific meaning of lossless, not a loophole. [MOPED][moped]
- **DNA, fingerprints and invariants:** a small alphabet, high physical density
  or stable identity feature does not specify the full original sequence. Genome
  assembly literature explicitly studies ambiguities caused by repeats. Missing
  paths/orderings must be supplied. [Assembly limits][assembly]

Likewise, biological assembly indices count construction complexity; the scalar
index is not an injective description of an object. A full reusable construction
graph belongs to program/grammar coding. Hyperdimensional binding/bundling is
useful for noisy associative retrieval, but exact text still needs collision
and cleanup information. These are useful research connections, not additional
free encodings. [Assembly theory][assemblytheory], [Kanerva][kanerva]

## 3. Ten distinct proposed architectures

These are **ten operationally different experiments**, not ten new information
theorems. Established ingredients are credited; “proposed addition” means a
design hypothesis for this project, not a world-first claim. The mathematical
classes overlap: every exact codec is ultimately a program and can induce a
probability distribution. Distinctness here concerns the stored object,
reconstruction algorithm, and testable source of savings.

### 1. Evolutionary variation graphs for article families

**Bridge:** pangenomics and evolutionary reconstruction. Store related pages as
paths through a shared, byte-labelled variation graph, rather than independently
encoded strings. Variable entity values form typed branches. Correlated branch
choices across distant locations are modeled jointly, so one family genotype
can explain several separated textual changes.

**Exact archive:** graph labels/edges, family membership, page paths or correlated
branch choices, literal edits, original page order, framing and graph decoder.
Path spelling followed by exact patches reproduces every byte. Unsupported
pages use the ordinary codec. The graph itself is never free corpus knowledge.

**Closest work and proposed addition:** GBWT already stores haplotypes as graph
paths and inherits BWT machinery. The proposed addition is correlated, typed
Wikipedia variation paths, not the discovery of graph compression. This differs
from ordinary LZ only if it exploits distant coupled choices after the graph
has been paid. Embedding-based article ordering already occurs in STARLIT;
sorting similar pages alone does not qualify. [GBWT][gbwt], [STARLIT][starlit]

**First probe:** 128 KiB, at most 32 related page families, working target 1 GiB. Compare the *same* graph with independent branch
coding, correlated branch coding, and reference-plus-edits. Include unrelated
pages. Continue only if correlated savings repay graph, paths, repairs, order
and code. Main failure: near-duplicate strings are already captured by matches,
while graph topology/path information consumes the hoped-for gain.

### 2. Causal reconstruction programs for generated prose

**Bridge:** developmental biology, attribute grammars and inverse graphics.
Infer small typed fact programs whose execution emits XML and prose: one date
can generate an age/weekday, or counts can generate totals and percentages.
Facts feed several separated outputs through explicit causal dependencies.

**Exact archive:** primitive facts and entity links, bounded renderer/operations,
program structure, layout/style choices and byte-exact edit residuals. Decoder
executes an acyclic program, then patches spelling, punctuation and exceptions.
No external knowledge base or language model is assumed.

**Closest work and proposed addition:** L-systems, attribute grammars, inverse
rendering and compression by program synthesis are established. The proposed
addition is a paid causal fact graph shared across Wikipedia outputs, learned
for description length. It must compute relationships, not simply replace
phrases with template IDs. Computed multi-output dependencies must be isolated
from ordinary phrase substitution. [Lindenmayer][lsystem], [Knuth][attributes],
[Picture][picture], [Brevis preprint][brevis]

**First probe:** 64 KiB of qualifying real pages, at most 24 primitive operations,
working target 1 GiB. Use identical extracted fields in an
opaque-slot template control. Hold out field values and include malformed/XML
and prose exceptions. Stop unless computed reuse pays facts, syntax, renderer,
styles and repairs. Main failure: factual understanding explains meaning but
not exact wording, and most prose may not be generated by a compact renderer.

### 3. Signed Born tensor networks as a joint block code

**Bridge:** quantum many-body states and tensor-network contraction. Represent
a block distribution by `P(x) ∝ |lᵀ A[x1] A[x2] … A[xn] r|²`. Signed amplitudes
permit interference; bounded bond dimension keeps contraction manageable.
Contract all unobserved variables to form normalized conditional probabilities
for arithmetic coding. A later tree topology could connect syntax/entity roles.

**Exact archive:** quantized cores and boundary vectors, block dimensions,
normalization/rounding specification, coder bytes and fallback support. Decoder
recovers original discrete symbols directly. There is no quantum device,
embedding inverse, measurement trick or ECC recovery stage.

**Closest work and proposed addition:** Born-machine generative learning and
tree tensor networks are prior art. The proposed addition is a compact,
structurally aligned, signed joint model trained for *paid enwik9 coding cost*.
It is not merely tensor factorization of a transformer's weights. Compare a
nonnegative Born MPS with the identical bond/parameterization to isolate signs;
separately compare a parameter-matched HMM. Squaring an amplitude is not the
same model as a same-bond HMM. [Han et al.][born], [Cheng et al.][ttn]

**First probe:** nibble alphabet, 64-byte blocks, bond 4/8, serialized model ceiling 2 MiB and working target 1 GiB. Verify parity
and long-copy controls, then frozen text. Use deterministic bounded/integer
contraction and a strictly positive escape component; charge normalization
overhead. Stop if normalized integer-CDF code length plus assets cannot beat
the matched control. Main failures: insufficient correlation range, training
cost and numerical precision. Quantum terminology supplies no size advantage.

### 4. Exact integer flows and reaction-coordinate transforms

**Bridge:** reversible dynamical systems, multiscale lifting and chemical
reaction coordinates. Learn a small invertible discrete transform that turns
jointly dependent text/field blocks into easier-to-code coordinates. One layer
can use `yA=xA; yB=(xB+f(xA)) mod 256`; inversion is exact subtraction. Couple
layers at several scales and preserve XML/slot boundaries where useful.

**Exact archive:** transform parameters, all latent coordinates, shape/field
metadata, base-distribution parameters and entropy code. No coordinate is
discarded. Conservation relations fit here only when sufficient kernel
coordinates/residues are retained to make reconstruction bijective; a rectangular
invariant map alone does not. Otherwise they belong under 5. Matrices, large
coefficients, residues and exceptions are charged.

**Closest work and proposed addition:** discrete flows already model text, and
integer discrete flows already perform exact compression. The proposed addition
is a small structure-conditioned multiscale transform that exposes dependencies
our linear rotations/canonicalizations missed. Stoichiometric or Smith-normal
form encodings are included here, not counted again as a new approach. A
chemical reaction network can simply implement a neural function, so naming it
chemical adds nothing. [Discrete flows][discreteflow], [IDF][idf],
[integer-only flows][iodf], [Smith reconstruction][smith], [CRN computation][crn]

**First probe:** 128 KiB, four fixed coupling layers, at most 64 KiB serialized
parameters, working target 1 GiB. Compare identity,
ordinary numeric deltas, and a fixed linear lifting transform. Exhaustively
invert tiny alphabets; test all byte values and finite-width overflow. Continue
only on a lower complete archive after transform/model costs. Main failure:
bijectivity preserves entropy; useful latent simplification may require a model
larger than the redundancy it exposes.

### 5. Microcanonical constraints and exact configuration ranks

**Bridge:** statistical mechanics, chemical conservation and graph symmetry.
Describe a block by compact constraints, then its exact rank among every
configuration satisfying them. Begin with transition counts/endpoints rather
than a vague semantic fingerprint. A shared structural constraint library might
later express article-family relationships.

**Exact archive:** constraints `c`, lengths, endpoints, an index in
`Ω(c)={y:C(y)=c}`, and all ranking/constraint code. The basic cost is
`L(c)+ceil(log2 |Ω(c)|)`, plus program/framing. Decoder counts completions and
unranks; it does not guess which colliding fingerprint was intended.

**Closest work and proposed addition:** enumerative coding is old; microcanonical
graph models and shuffle coding are also established. The proposed addition is
a tractable set of reusable text/relational constraints with paid exact ranking.
Gauge/orbit coding is a related specialization, not an eleventh idea: original
labels/order require restoration when they belong to the source; stabilizers
change orbit size. Genuinely unordered objects and internal representation
gauges have no original sequence order to restore.
A word multiset does not identify its original ordering; the paid admissible
set must account for that ambiguity. [Cover][cover], [Peixoto][micro],
[Practical Shuffle Coding][shuffle]

**First probe:** price sparse nibble-transition constraints on frozen blocks;
implement rank/unrank only if promising. Target 512 MiB. Exhaustively check a tiny alphabet first. Stop if
even the priced admissible-set bound loses, or if exact counting is intractable.
Uniform-set bounds and nonuniform probability models are different controls;
do not call an unimplemented combinatorial count an archive.

### 6. Noncausal progressive revelation by discrete diffusion

**Bridge:** diffusion, coarse-to-fine reconstruction and missing-data inference.
Encode a deterministic hierarchy of anchors first, then fill gaps using both
left and right *already decoded* context. Reveal structural fields, entity
identity or coarse token classes before remaining lexical choices. The schedule
changes which correlations are available when a choice is coded.

**Exact archive:** normalized symbol codes at every reveal step, token/shape
metadata, model parameters and any schedule choices not derivable by decoder.
Every information increment is coded once; coarse classes followed by finer
symbols require class-conditioned normalization. There is no semantic-quality
substitute for exact recovery. No free selection oracle. Ordinary native-prefix
probabilities cannot be reused across unresolved gaps: each reveal needs a
valid conditional distribution based on the decoder's actual known state.

**Closest work and proposed addition:** ARDMs already connect order-agnostic
generation, discrete diffusion and lossless compression. The proposed addition
is a compact deterministic, syntax-aware reveal schedule for enwik9, with a
small bidirectional model. The test must isolate useful conditioning on both
sides, rather than merely deleting words into a separate stream. [ARDM][ardm]

**First probe:** 128 KiB, two fixed reveal schedules, at most 256 KiB serialized
model and working target 1 GiB. Compare left-to-right and
reveal coding at matched model/parameter budget, plus shuffled anchors. Charge
the anchor stream and every refinement. Stop if full normalized codelength or
serial inference cost loses. Main failure: additional context fails to repay
the model and multiple inference passes; parallel generation papers do not
establish single-core prize feasibility.

### 7. Cross-page coset coding with correlated side information

**Bridge:** distributed source coding, parity constraints and spin-glass decoding.
After paying for reference/anchor pages, encode aligned related blocks by a
syndrome under a fixed sparse code. Decoder combines the syndrome with a
correlation model and known reference to recover the exact target. This tests
long-range cross-page dependence, not the correction radius of a lossy model.

**Exact archive:** anchors, alignments, code seed/matrix specification, syndrome
bits, transmitted rate extensions, correlation model, fallback blocks and
program. Decoder is deterministic; encoder simulates it and uses a literal/
ordinary-code fallback whenever the result differs. A checksum alone does not
guarantee uniqueness. All acquisition cost for side information is paid.

**Closest work and proposed addition:** Slepian–Wolf and practical syndrome
coding are established. Spin-glass/channel-code analogies are also established.
The proposed addition is a corpus dependency graph supplying real, paid side
information and rate adaptation. Aligned page data must demonstrate useful
conditional redundancy. A joint encoder already sees both pages, so Slepian–Wolf
has no theorem promising superiority to ordinary conditional coding.
[Slepian–Wolf][sw], [rateless codes][rateless], [Sourlas][sourlas]

**First probe:** 128 KiB of aligned blocks, working target 1 GiB. Compare reference-plus-edits and a conditional arithmetic model, with
identical paid anchors. Reject before building a decoder unless a favorable
syndrome/rate bound repays alignments and code/model cost. Main failures:
insertion/deletion mismatch, burst errors, iterative-decoder cost and side-info
overhead. No independent information appears through ECC.

### 8. Cooperative self-assembly as a constraint-completion codec

**Bridge:** algorithmic DNA tile assembly and cooperative local interactions.
Represent blocks as small grids/graphs whose values are forced by a compact
tile rule set and sparse anchors. Several neighboring constraints cooperate;
propagation and bounded search fill the rest. Defects are explicit.

**Exact archive:** rules and glue-label bits, graph/grid layout, anchor positions
and values, defect overrides, and rank among distinct consistent output grids.
Decoder follows a bounded deterministic propagation/enumeration procedure.
Encoder simulates that bounded decoder and explicitly transmits an ordinary-code
mode/payload on timeout or expensive ambiguous cases; the decoder cannot invent
a missing fallback payload after independently timing out.

**Closest work and proposed addition:** algorithmic tile assembly and compact
tile programs are established. The proposed addition is minimum-description
selection of text-derived anchors and defects under *two-sided* constraints.
A north/west-only tile predictor is just another causal context model; a tile
that stores a phrase is a dictionary entry. The experiment qualifies only if
cooperative, noncausal completion reduces the transmitted description.
[DNA XOR assembly][tilesxor], [tile program complexity][tilescomplex],
[shape complexity][shapes], [tile minimization][tilemin]

**First probe:** 128 KiB mapped to fixed 16×16 bit grids, at most 16 tile types
and 4,096 search branches per block; working target 1 GiB.
Use identical grids for a one-sided predictor and ordinary codec controls.
Include a synthetic tile-generated positive control and shuffled text. Stop if
rules+anchors+ambiguity+defects do not win. Main failure: text lacks the needed
local constraints; inference or seed description grows as large as the data.
Shape-assembly theorems do not establish text compressibility.

### 9. Fermionic occupation sets with determinant coding

**Bridge:** fermionic exclusion, random matrices and determinantal point
processes. Model word-presence sets by a normalized determinant distribution,
then code multiplicities and the exact ordered surface conditioned on that set.
This asks whether exclusion/diversity structure provides information missing
from independent word-presence probabilities.

**Exact archive:** a kernel such as `L=D+BBᵀ` with positive diagonal `D`, set
codes under `P(S)=det(L[S])/det(I+L)`, count/order codes, spellings, nonword bytes,
model and program. Positive diagonal ensures mathematical full support; the
finite-precision coder still needs deterministic CDFs and escape handling.

**Closest work and proposed addition:** DPP inference and summarization are
established; the source paper is not a compression demonstration. The proposed
addition is a fully paid determinant-coded scaffold integrated with exact
ordered completion. It is *not* another claim that a bag uniquely identifies
text. Ordinary DPPs model repulsion and cannot directly represent the positive
co-occurrence common in topics. [Kulesza–Taskar][dpp]

**First probe:** 64 presence features, eight columns in B, a likelihood/headroom screen,
working target 512 MiB. Compare independent Bernoulli and
a paid set-plus-ordered-completion control at matched precision. Continue only
if determinant savings repay complete set/count/order and model costs. This is
a low-priority, conditional lead, not an evidence-backed likely winner. The positive diagonal makes L full
rank; a truly rank-eight kernel would exclude subsets larger than eight.

### 10. Logic-circuit encoding of address-to-byte functions

**Bridge:** digital logic synthesis and binary decision diagrams. Treat an exact
block as the truth table of a multi-output function from position bits to byte
bits. Store a reduced decision/circuit graph. Repeated Boolean subfunctions
across positions or bitplanes can share nodes without being contiguous phrases.

**Exact archive:** circuit/ROBDD nodes, output roots, variable order, block
length/padding rules, structural address mapping and all exceptions. Decoder
enumerates valid addresses and evaluates the function to recover original bytes.
Constant terminal values and references have explicit codes.

**Closest work and proposed addition:** ROBDD lossless compression is established
and has a universality analysis for power-of-two binary strings relative to
finite-state binary sources, not our arbitrary multi-output circuits. The
proposed addition is role/offset-address
factoring and shared multi-output logic for article families or numeric columns,
optimized for actual serialized circuit size. Variable ordering is part of the
description. A disguised substring trie is not sufficient evidence of a new
gain over a grammar/match control. [Kieffer–Flajolet–Yang][bdd]

**First probe:** 128 KiB, fixed binary position order plus one deterministic
role/offset order, node ceiling 250,000; working target 1 GiB.
Compare a byte trie/grammar-style DAG and ordinary codec, with exactly the same
block boundaries. Test padding, arbitrary byte values and multi-output sharing.
Stop if node pointers/variable mapping cost more than the code saved. Main
failures: irregular prose produces a large graph; circuit optimization is hard;
theoretical universality does not imply competitive finite-corpus performance.

## 4. Why these are ten rather than relabelled variants

| ID | Stored object | Reconstruction work | Specific hypothesis |
| --- | --- | --- | --- |
| 1 | Variation graph + paths | Spell paths, apply edits | Distant variants co-vary across related pages. |
| 2 | Fact/renderer program + repairs | Evaluate typed computations | Several exact outputs share computed causes. |
| 3 | Small tensor joint model + code | Contract normalized conditionals | Signed low-rank correlations are cheap. |
| 4 | Bijection + all latent coordinates | Invert coupling/lifting layers | Dependencies simplify in exact learned coordinates. |
| 5 | Constraints + configuration rank | Count and unrank | A cheap admissible set captures joint regularity. |
| 6 | Reveal hierarchy + symbol codes | Fill in decoded-context order | Noncausal context lowers paid prediction cost. |
| 7 | Anchors + parity cosets | Correlation-aware syndrome decoding | Paid references make sparse parity codes efficient. |
| 8 | Tile rules + seeds/defects/rank | Cooperative completion | Multi-neighbor constraints force unstored values. |
| 9 | Determinant-coded set + completion | Decode set then ordered surface | Negative subset correlations repay scaffold cost. |
| 10 | Address-to-value circuit | Evaluate all original positions | Noncontiguous Boolean subfunctions share compactly. |

Potential combinations are hypotheses, not additive savings: 1 can supply
references for 7; 2 can supply constraints for 5; 3 can model branch choices in
1 or reveal choices in 6; 4 can transform typed numeric coordinates from 2;
10 can represent regular renderer outputs. First isolate each mechanism. A
second mechanism is justified only after the first pays its complete cost.

Orbit/gauge coding was merged into 5; stoichiometric coordinate coding into 4.
De Bruijn spectra without path information, free analog precision, quantum
amplitude storage, and Fisher-information-only summaries were not padded into
additional candidates. Chaotic maps or CRNs that merely implement an existing
coder/model also do not count as independent principles.

## 5. Suggested later execution order and common gates

This file proposes later experiments; **none is queued or run by this audit**.
Research has no artificial elapsed-time or CPU-time budgets. Use
`tools/resource_guard.py --wall-seconds 0`. The resource policy remains
one experiment tree with all available CPU cores/threads, 3 GiB available RAM
at launch, a 2 GiB combined available-RAM/free-swap reserve and a 512 MiB
emergency RAM floor. Temporary swapping is allowed; no fixed tree-RSS cap. Working targets above are
lower allocation goals, not new kernel-enforced quotas. Use the existing guard.

First cheap probes: **1 (variation paths)** and **2 (causal programs)**. They
have explicit source structures and small interpreters, so graph/program cost
can refute them before expensive training. This ordering is engineering judgment,
not a literature-proven ranking. Require broad enough coverage to matter: a
large saving on a tiny selected stratum is not a full-corpus opportunity.

Higher-risk, broader text directions: **4 (exact flow)**, **6 (noncausal reveal)**
and **3 (Born network)**. Start with a tiny positive control and priced model
bound; do not train a large neural system from an analogy. **5 and 10** are good
small exact-combinatorial screens. **7 and 8** require actual source correlation
or constraint density first. **9** remains last unless its headroom screen can
repay the full scaffold and original-order costs.

For any chosen probe:

1. Freeze data, candidate parameters and a matched control before scoring.
   Use representative prose, markup and repetitive pages, plus synthetic
   positive and shuffled negative controls. Fit/search on development only.
2. Price model, graph/program, maps/permutations, side information and a valid
   residual lower bound before building a complete codec. Distinguish an oracle
   bound, normalized probability screen and real stored archive.
3. Implement exact round-trip and deterministic decoding, arbitrary bytes,
   EOF/truncation/version/checksum handling and decoder asset independence.
   Float-dependent models need a specified reproducible numerical path.
4. Continue when measured headroom supports a complete pipeline at least 1%
   below the actual official full-corpus winner, after all overhead. Small gains
   over an inferior project compressor are not the goal. Method ablations are
   diagnostic only. Resource stops are incomplete, not a scientific refutation.
   Reopen failures only with a changed mechanism or new measured headroom.
5. Run full-corpus validation only for a frozen candidate with a credible path
   to the official target. Samples cannot establish success. Verify exact
   reconstruction, complete scoring and applicable resource limits, and stop
   append-only final output when its counted size cannot qualify. Corpus fitting
   is allowed, but every decoder asset is counted. Do not claim timing calibration
   or official resource compliance without measuring it.

## Sources

Links below are primary author papers/documentation except the requested
benchmark index and official prize registry. Paper performance on images,
genomes, quantum states or shapes is **not** an enwik9 performance claim.

[ltcb]: https://mattmahoney.net/dc/text.html
[hutter]: https://www.hutter1.net/prize/
[rules]: https://www.hutter1.net/prize/hrules.htm
[paq]: https://mattmahoney.net/dc/paq.html
[starlit]: https://github.com/amargaritov/starlit
[cmixhp]: https://github.com/byronknoll/cmix-hp
[fastcmix]: https://groups.google.com/g/Hutter-Prize/c/GVAWh2t0Rsc
[fxcmix]: https://github.com/kaitz/fx-cmix
[fx2]: https://github.com/kaitz/fx2-cmix/blob/main/README.md
[lex]: https://github.com/blahem/cmix-lex
[obias]: https://huggingface.co/dfreelan/cmix-obias
[fx2t]: https://github.com/astOwOlfo/fx2-cmix-transformer-v1/blob/main/writeup.md
[zmix]: https://zmix.frostbyrne.io/v1.0/README.md
[zmixwrite]: https://zmix.frostbyrne.io/v1.0/writeup.md
[lexth]: https://github.com/Neel49/cmix-lex-transformer/blob/main/README.md
[neif]: https://github.com/marwoelk/cmix-neif-1.0
[forge]: https://github.com/dirknesner/forge-cmix/blob/main/DESCRIPTION.md
[fractal]: https://freement.cloud/fractal_zip/hutter/
[ft8]: https://github.com/mejutoco/fx2-cmix-T-ft8
[makimono]: https://github.com/krapuchino83/makimono
[exgirlfriend]: https://github.com/rlanday/ex-girlfriend
[rata]: https://github.com/Dharmesh2015/RATA-CMIX
[altxs]: https://github.com/altvectra/altxs
[tufazip]: https://github.com/Tufalabs/tufazip
[nncp]: https://bellard.org/nncp/
[ctw]: https://research.tue.nl/en/publications/the-context-tree-weighting-method-basic-properties/
[dmc]: https://academic.oup.com/comjnl/article-abstract/30/6/541/327619
[lz77]: https://ieeexplore.ieee.org/abstract/document/1055714/authors
[bwt]: https://bitsavers.org/pdf/dec/tech_reports/SRC-RR-124.pdf
[ans]: https://arxiv.org/abs/0902.0271
[shannon]: https://web.mit.edu/6.441/www/reading/shannon1948.pdf
[holevo]: https://www.mathnet.ru/php/archive.phtml?jrnid=ppi&option_lang=eng&paperid=903&wshow=paper
[schumacher]: https://journals.aps.org/pra/abstract/10.1103/PhysRevA.51.2738
[moped]: https://arxiv.org/abs/astro-ph/9911102
[phase]: https://arxiv.org/abs/2301.10647
[gbwt]: https://pmc.ncbi.nlm.nih.gov/articles/PMC7223266/
[assembly]: https://arxiv.org/abs/1301.0068
[assemblytheory]: https://www.nature.com/articles/s41586-023-06600-9
[kanerva]: https://redwood.berkeley.edu/wp-content/uploads/2020/08/kanerva09-hyperdimensional.pdf
[lsystem]: https://www.sciencedirect.com/science/article/pii/0022519368900805
[attributes]: https://www.ccs.neu.edu/home/chadwick/files/knuth.pdf
[picture]: https://www.cv-foundation.org/openaccess/content_cvpr_2015/html/Kulkarni_Picture_A_Probabilistic_2015_CVPR_paper.html
[brevis]: https://arxiv.org/abs/2608.02162
[born]: https://arxiv.org/abs/1709.01662
[ttn]: https://journals.aps.org/prb/abstract/10.1103/PhysRevB.99.155131
[discreteflow]: https://arxiv.org/abs/1905.10347
[idf]: https://arxiv.org/abs/1905.07376
[iodf]: https://proceedings.mlr.press/v162/wang22a.html
[smith]: https://arxiv.org/abs/2111.09949
[crn]: https://doi.org/10.1073/pnas.2111552119
[cover]: https://isl.stanford.edu/~cover/papers/transIT/0073cove.pdf
[micro]: https://arxiv.org/abs/1610.02703
[shuffle]: https://proceedings.neurips.cc/paper_files/paper/2024/hash/98d17a9632e1534bae96793e99dc3c2d-Abstract-Conference.html
[ardm]: https://arxiv.org/abs/2110.02037
[sw]: https://web.mit.edu/6.454/www/www_fall_2001/kusuma/slepwolf.pdf
[rateless]: https://www.comm.toronto.edu/~weiyu/eckford_sw.pdf
[sourlas]: https://www.nature.com/articles/339693a0
[tilesxor]: https://pmc.ncbi.nlm.nih.gov/articles/PMC534809/
[tilescomplex]: https://www.dna.caltech.edu/Papers/squares_STOC.pdf
[shapes]: https://arxiv.org/abs/cs/0412096
[tilemin]: https://www.dna.caltech.edu/Papers/minimal_tile_systems_ISAAC2011.pdf
[dpp]: https://proceedings.mlr.press/r9/kulesza11a.html
[bdd]: https://arxiv.org/abs/1111.1432
