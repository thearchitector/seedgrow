# Autonomous compression research

Work in `/home/elias/Codespace/seedgrow`. Implement, evaluate and refine ten
cross-domain approaches to exact compression of the enwik9 Wikipedia corpus.
The success target is a complete counted result at least 1% smaller than the
actual current official Hutter Prize winner, using reproducible measurements.
Carry the investigation through to a comparative report without routine
confirmation requests. Do not stop at a plan or literature review.

## Objective and scope

Optimize total counted bytes: encoded data, programs, models, dictionaries,
structure, reconstruction choices and exact repairs. Exact reconstruction is
mandatory. Lossy intermediate representations are permitted when the archive
contains everything needed to recover the original bytes.

Explore every approach below. Distinguish a working implementation, a promising
incomplete lead, and a fully verified result meeting the official winner target.
They are different conclusions. Do not claim scientific novelty without checking
prior art, or infer corpus performance from an analogy or synthetic example.

There are no artificial campaign, stage, per-idea, elapsed-time or CPU-time
budgets. Measure time as a resource cost, but do not terminate useful work merely
because a clock allowance has expired. Define finite experimental questions,
record decisions and stop configurations on evidence. This does not require
exhausting every possible algorithm or running unproductive searches indefinitely.

## Available project and data

- `tools/resource_guard.py`: serialized process-tree resource monitor.
- `references/enwiki9`: canonical corpus, exactly 1,000,000,000 bytes, SHA-256
  `159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc`.
- `LICENSE`: project licensing material.

Read `AGENTS.md`. Implement candidate compressors as actual source files in the
worktree; there is no required project compressor to reproduce or improve.
The bibliography in `docs/COMPRESSION_LANDSCAPE.md` is optional supporting
literature. The research contracts below define the task without requiring a
conversation or additional project context.

Verify corpus size/hash by streaming. If the local corpus is unavailable, obtain
and verify it from `https://mattmahoney.net/dc/enwik9.zip`.

## Official performance target

Verify the current winner and scoring rules at startup and before declaring a
result. Use `https://www.hutter1.net/prize/` and
`https://www.hutter1.net/prize/hrules.htm`. Mahoney's general compression ranking
is not the official prize record.

Let L be the actual current official counted record. The qualifying integer
budget is `T=(99*L)//100`. The official record currently shown is 100,424,672
bytes, giving T=99,420,425 bytes; refresh L instead of treating this number as
permanent. Use the applicable complete scoring formula, including compressor,
decoder, archive, required assets and command options. Under the separate-codec
relaxation this is `C.zip + 2*D.zip + archive + options`; when C and D are the
same program it is `2*shared.zip + archive + options`.

A percentage gain over a weaker project compressor does not meet the objective.
Discard inferior project compressors as performance references; do not spend
work reproducing or incrementally improving them. Synthetic controls and
mechanism-specific ablations can establish correctness or explain an effect,
but are not the competitive target.

For screening, price nonpayload overhead P and compute remaining payload budget
`B=T-P`. If B is nonpositive, that package cannot qualify. Representative sample
rates and source-stratum coverage may guide research toward B, with uncertainty
and fixed costs explicitly accounted for. They are screening evidence only:
samples do not establish the winner's own sample performance or a full-corpus
score. Require a concrete mechanism capable of closing the measured gap, not
just a small gain over an inferior predictor. A useful component must have a
credible place in a complete pipeline meeting T; a small component saving alone
is not success.

The target is the fixed 2006 dump. Do not assume current Wikipedia syntax or
factual consistency. Any inferred semantic or physical relationship must hold
for the actual bytes or have explicitly coded exceptions.

## Environment and resource safety

WSL2 is configured with these limits in effect:

```ini
[wsl2]
memory=14GB
swap=16GB
autoMemoryReclaim=gradual
sparseVhd=true
```

Check current available memory and effective process/container limits before
launching work. Capacity is not the same as currently available memory. Keep
these experiment controls:

- One experiment process tree globally, including across subagents.
- Use all available CPU cores and threads; no additional affinity, thread-count
  or niceness restrictions. Clear inherited artificial thread caps if present.
- Require 3 GiB available RAM before launch. During work, keep a 2 GiB combined
  available-RAM/free-swap reserve and a 512 MiB emergency available-RAM floor.
- No fixed per-tree RSS cap. Temporary growth into swap is allowed. Record RSS,
  swap usage and available headroom. Reduce working sets if sustained swapping
  prevents useful progress; do not reject a trial merely because it uses swap.
- Stream batches and unload models between stages when necessary. Include every
  descendant, predictor and helper in the process-tree memory measurement.

Use the guard for compilation, training, symbolic searches, functional tests
and benchmarks. Keep its shared lock, descendant monitoring and RAM/swap
headroom checks. The runner must not impose CPU or thread limits. Do not nest
guards or bypass their lock. These are monitored safeguards, not a kernel-enforced
memory quota.

```bash
python3 tools/resource_guard.py \
  --log .research/NAME.guard.json \
  --wall-seconds 0 \
  -- COMMAND ARGUMENTS
```

Disable research runtime deadlines in inner helpers too; an unlimited outer
monitor does not disable a subprocess timeout. Keep counted-size stops, ordinary
I/O error handling and diagnosis of actual deadlocks or nonprogressing programs.

On temporary low headroom, wait with interruptible backoff. Do not kill unrelated
processes or alter WSL/host settings. Reduce working sets on memory pressure. A
resource-blocked or unfinished experiment is not an algorithmic refutation.

No GPU, rented hardware, external decoding services, publication, submission,
remote messages or commits. Do not download existing compressors or their source
for comparative benchmarking. Use published benchmark results and primary
papers/author documentation. Do not modify repository metadata or unrelated work.

## The ten research contracts

### 1. Evolutionary variation graphs

Represent related article families as paths through a shared byte-labelled
variation graph. Test correlated choices across distant branches, including
consistent entity substitutions. The archive must include graph labels/edges,
family membership, paths, edits, original page order and decoder.

Compare correlated branch coding with independent branch coding on the same
graph and reference-plus-edits to isolate the mechanism. A gain from sorting similar pages
or renaming substring pointers alone does not establish the proposed mechanism.
Check whether graph and path costs erase the benefit.

### 2. Causal reconstruction programs

Infer typed primitive facts and small acyclic programs that generate multiple
outputs: dates can determine ages or weekdays; counts can determine totals and
percentages. Store primitive values, programs, entity links, renderer, layout
choices and byte-exact exceptions/repairs.

Compare computed reuse against opaque-slot templates using the same extracted
fields. Hold out field values. Test actual arithmetic reuse across separated
outputs, not simply phrase replacement. Meaning alone does not recover wording,
capitalization, punctuation or inconsistent assertions.

### 3. Signed Born tensor networks

Model short symbol blocks using a normalized joint distribution proportional to
`|l^T A[x1] A[x2] ... A[xn] r|^2`. Obtain valid conditional probabilities by
contracting unobserved variables and entropy-code the original discrete symbols.
Store quantized tensors, boundaries, shapes, numerical rules and fallback support.

Compare signed and nonnegative Born models with identical parameterization;
separately compare a parameter-matched HMM. Verify parity/copy synthetic controls.
A nonnegative squared-amplitude model is not automatically a same-bond HMM.
No quantum device, free amplitudes or embedding inverse is assumed.

### 4. Exact integer flows

Learn invertible discrete coupling/lifting transforms that simplify joint text
or typed-field dependencies. A layer may use `yA=xA` and
`yB=(xB+f(xA)) mod 256`. Store every latent coordinate and the full transform/model.

Compare identity, ordinary numeric deltas and fixed linear lifting. Test exact
inverse behavior for arbitrary byte values and finite-width overflow. Chemical
conservation coordinates qualify only when enough kernel coordinates/residues
are preserved for reconstruction. A bijection exposes regularity; it does not
remove intrinsic information or make model parameters free.

### 5. Constraints and exact configuration ranks

Store compact constraints `c=C(x)` and the exact rank of the original in
`Omega(c)={y:C(y)=c}`. Begin with tractable transition-count/end-point constraints;
consider structural constraints only when exact completion counting is feasible.
Pay `L(c)+ceil(log2|Omega(c)|)` plus program/framing for a uniform configuration code.

First price the complete admissible set; implement and exhaustively validate
rank/unrank on a tiny alphabet when the bound is promising. Compare ordinary
conditional coding. Fingerprints alone cannot choose among collisions. If
symmetries are used, original labels/order require restoration when part of the
source; a truly unordered object has no original order to restore.

### 6. Noncausal progressive revelation

Encode a deterministic hierarchy of anchors/coarse choices, then fill gaps using
already decoded context on both sides. Every information increment needs a valid
normalized conditional code. Store model, token/shape data and nonderivable
schedule choices, as well as every refinement.

Compare matched-model left-to-right coding, progressive coding and shuffled
anchors. Prefix-only probabilities cannot be reused across unresolved gaps.
Coarse classes followed by fine symbols require class-conditioned normalization.
Measure whether added context repays anchors, model size and inference passes.

### 7. Cross-page coset coding

Pay for reference pages, align related target blocks, and encode them using
sparse parity syndromes with a decoder-side correlation model. Store references,
alignment, code specification/seed, syndromes, rate extensions, model and fallbacks.

Compare reference-plus-edits and conditional arithmetic coding with identical
references. Encoder must simulate deterministic decoding and transmit fallback
when reconstruction differs. A checksum alone is not proof of uniqueness.
Slepian-Wolf coding provides no theorem promising an advantage over a joint
encoder that already knows both sources; the specific mechanism must earn it.

### 8. Cooperative self-assembly

Represent blocks as grids or graphs forced by a small cooperative tile/rule set
and sparse anchors. Store rules/glue labels, layout, anchors, defects and a rank
among distinct valid completions. Use deterministic propagation and finite,
explicitly defined search.

Require two-sided/noncausal cooperation beyond a one-sided context predictor or
phrase dictionary. Compare the same layouts against those controls. Encoder
simulates bounded decoding and explicitly transmits a fallback mode/payload when
completion is unsuitable. A decoder cannot invent unsent fallback data on timeout.
Test a tile-generated positive control and shuffled real text.

### 9. Determinant-coded occupation sets

Encode word-presence sets under a DPP, for example
`P(S)=det(L[S])/det(I+L)`, with `L=D+B B^T` and positive diagonal `D`.
Then encode multiplicities, order, exact spellings and nonword bytes. Include
kernel/model costs and deterministic finite-precision probability handling.

Compare independent Bernoulli presence probabilities and a fully paid set-plus-
ordered-completion control. DPPs model repulsion, not arbitrary positive topic
co-occurrence. A positive diagonal makes L full rank even when B has few columns;
a truly low-rank kernel excludes larger sets. Small set-likelihood improvements
are insufficient unless they repay the complete scaffold and ordering cost.

### 10. Address-to-byte logic circuits

Treat a block as the truth table of a function from position bits to output byte
bits. Store a shared reduced decision/circuit graph, output roots, variable order,
address mapping, lengths, padding rules and exceptions. Decode by evaluating all
valid original addresses.

Compare fixed position order and a deterministic role/offset order, a trie or
substring DAG to isolate the mechanism. Test noncontiguous subfunction sharing rather
than a disguised phrase dictionary. Count node pointers and variable mapping;
universality theorems for binary ROBDDs do not establish this circuit's finite-
corpus performance.

## Autonomous investigation procedure

Give every idea an initial investigation before concentrating on a favorite.
Suggested order: 1, 2, 4, 6, 3, 5, 10, 7, 8, 9; measured evidence may change priority.
For each idea:

1. Define the exact transmitted object, decoder knowledge, reconstruction
   algorithm, expected source of savings and falsification criteria.
2. Check the closest primary literature and state the proposed addition. Do not
   treat a domain-specific name as proof of a different mechanism.
3. Implement a synthetic positive control and negative/shuffled control. Verify
   that the intended mechanism activates and reconstructs correctly.
4. Run a real-corpus probe or a defensible, fully priced headroom bound.
   Literature discussion alone is not experimental coverage.
5. Record the evidence-backed status: rejected by a stated bound; exact but
   losing; promising normalized screen; verified archive improvement; or
   incomplete with a specific blocker.
6. Refine when measurements identify a concrete bottleneck and a plausible way
   to address it. State what changes and what observation would justify continuing.

Do not impose an arbitrary number of refinements, but require evidence for each.
Avoid blind sweeps and unchanged retries. Revisit a rejected configuration only
when new measurements or a materially different mechanism support doing so.
Combine mechanisms only after isolated tests justify measuring their interaction;
savings cannot be added without a combined measurement.

Use subagents for source preparation, research and review where useful. Appoint
one experiment owner. Helpers must not independently compile, train, benchmark
or run numerical tests. Parallel preparation is allowed; parallel experiment
trees are not. Keep briefs and reports concise.

## Data, scoring and verification

Create frozen disjoint TRAIN, DEV and HOLDOUT cohorts from the verified corpus.
Record exact byte ranges, hashes, assembly order and initialization/reset rules.
Include prose, markup and repetitive structures. Fit and tune on TRAIN/DEV;
freeze candidate configurations before holdout evaluation and do not tune on its
results. Use additional untouched data if more validation is needed.

Selected page families can diagnose a mechanism. Final rankings must use identical
representative original bytes, with fallback explicitly counted for other content.
Do not compare selected-stratum gains against whole-corpus goals without pricing
all remaining content. Expand samples when necessary to distinguish fixed
overhead from scaling, within memory limits. Use identical representative input
bytes and reset protocols when comparing candidate pipelines.

Clearly separate theoretical/oracle bounds, normalized probability screens and
actual stored archives. Charge the applicable official formula, including all
program/model/data dependencies and required command options. Charge shared fixed
assets according to the real format, not once per page unless duplicated there.
Encoder-only search need not run during decoding: charge encoder dependencies in
the compressor and decoder dependencies in its package/data.

Record archive/component/total counted bytes, source coverage, exactness, encode/
decode and transform/search/inverse CPU and wall time, peak tree RSS, minimum
available memory and temporary storage. Tiny inputs may be dominated by fixed
program cost; measured body savings can justify a larger test with explicitly
priced overhead. Hypothetical amortization is not a full-corpus result.

Before declaring a compression success, require actual lower counted size,
exact reconstruction, deterministic rebuilding/decoding, charged dependencies,
frozen holdout validation and measured resource feasibility. Test empty input,
all byte values, random/repetitive data, EOF, truncation, checksum failures and
incompatible configurations/formats. Decode using the archive and packaged
assets without the original input or hidden sidecars. Specify reproducible
numerical behavior and version changes in predictor or format semantics.

## Progressive evaluation and early stopping

A failed idea does not need a complete corpus run. Instrument encoding to report
source bytes processed, committed final-archive bytes, known mandatory overhead,
source strata encountered, current coding rates and any certified lower bound
on unavoidable remaining cost. Keep progress machine-readable and checkpoints
resumable. Do not treat temporary files as committed archive bytes.

Let W be irreversible final archive bytes, P be mandatory counted bytes outside
the archive, and Rmin a justified lower bound on additional unavoidable bytes.
Stop when `W+P+Rmin>T`. With no useful remaining-cost bound, use Rmin=0. Exceeding
T in committed counted bytes alone proves that the current append-only attempt
cannot qualify; it need not finish encoding or perform a full decode.

For an append-only final archive, enable the runner's size monitor:

```bash
python3 tools/resource_guard.py \
  --log .research/NAME.guard.json --wall-seconds 0 \
  --archive .research/candidate.archive \
  --counted-overhead-bytes P --counted-limit-bytes T \
  -- COMMAND ARGUMENTS
```

Replace P and T with computed integers. Monitor a fresh final archive path; this
check is invalid for scratch buffers, reserved space, shrinkable files or a file
that will later be recompressed. Encoder-specific stronger lower bounds may
justify stopping even sooner; document their derivation and assumptions.

Stratified rate forecasts, uncertainty estimates and evidence of a large
unexplained gap may also justify screening out an unpromising attempt. Label
that outcome as forecast-based screening, not a mathematically established
full-corpus failure. A slow or unfavorable prefix alone need not predict later
content or adaptation. Do not hide these uncertainties in a claimed result.

When a frozen candidate retains a credible route to T after representative
validation and all overhead is priced, run its full-corpus trial with progressive
monitoring. Continue a surviving promising trial to completion; early failure
checks save work but cannot certify an unprocessed successful remainder.

Verify all 1,000,000,000 reconstructed bytes against the canonical corpus. A
successful size result requires the complete counted total to be no larger than
T and exact reconstruction. Separately validate the official execution/resource
requirements before claiming prize eligibility. There are no artificial research
time limits; official prize runtime limits remain external eligibility criteria.
Do not claim calibrated timing compliance without a measured calibration.

## Records, cleanup and completion

Maintain compact machine-readable checkpoints under `.research/` and record
per-idea findings and lessons directly in `docs/CROSS_DOMAIN_RESULTS.md`. Save
source/configuration/data hashes, completed commands, decisions and the exact
next step. The prompt defines the task; do not create duplicate narrative plans
or separate progress journals.
Resume from checkpoints after interruption or context compaction; do not repeat
completed work without a reason. Platform or quota interruption must leave an
honest incomplete checkpoint, not a false completion report.

Files may be reorganized or deleted when unnecessary. Inspect their roles first;
preserve the corpus, licenses and anything necessary to reproduce the active
result. Keep only the active proof of concept and necessary evaluation tools. Record
failed findings, measurements and cleanup manifests before deleting rejected
scratch implementations and generated artifacts. Incorporate a successful
mechanism only after safe integration and verification; do not manufacture a
promotion merely to show a code change.

Complete when all ten ideas have evidence-backed outcomes, promising ones have
received justified refinements and comparable validation, and no identified next
experiment has demonstrated enough headroom to justify continuing that
investigation. Speculative possibilities may remain documented. Do not claim
that all conceivable algorithms have been exhausted.

Write `docs/CROSS_DOMAIN_RESULTS.md` with:

1. A ten-row table: evidence type, data/hash, best variant, actual counted bytes
   or clearly labelled screening result, distance to T, exactness, resources and
   decision. For samples report rates, fixed overhead and source coverage; do
   not subtract a sample archive size from the full-corpus target and call it
   competitive headroom. Separate full-corpus totals from sample measurements.
2. A ranking of verified actual-archive results on comparable inputs, with
   full-corpus performance against the official winner reported separately.
3. A separate list of promising incomplete or bound-only leads.
4. The most successful approach, if any, with its supporting evidence.
5. Whether any approach actually achieved at least 1% below the current official
   winner, with complete scoring and byte-exact full-corpus reconstruction.
6. Failed hypotheses, limitations, reproducible commands and the smallest
   justified next investigation.

If no approach meets T, say that none met the objective. Identify the best
measured candidate, its remaining gap to the official target and what evidence
could justify further development. Do not relabel a local improvement as success.
Keep progress updates concise and make the final report understandable on its own.
