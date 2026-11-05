# SeedGrow: minimal research continuation

Work is paused. The project retains only textual documentation and the current
standalone codec's source excerpt. No Hutter-qualifying candidate exists.
All measurements below are historical summaries as of 4 November 2026; the raw
experimental artifacts have been intentionally deleted.

## Objective and exactness contract

Investigate compact recursively generated neural/context models with exact
corrections. Optimize the total stored description: program, seed/model,
metadata and repairs. Intermediate generated values may be approximate. The
decoder's final complete corpus must be exact.

A probability above 50% does not guarantee the correct next bit or byte. Exact
recovery requires an entropy-coded stream, bounded-error corrections with a
verified distance bound, or explicit fallback data. Error count alone is not
description length. Every model choice, precision, framing byte and fallback
must be charged. Decoder state must depend only on its available archive and
already reconstructed prefix.

## Current implementation and measured progress

The retained source is an original standalone C++17 online context mixer. It
builds byte, word, character-class and markup contexts, long-match experts and
adaptive mixing state causally from the reconstructed prefix. Arithmetic coding
provides exact recovery. It needs no pretrained model, shipped dictionary or
external compressor at runtime. This implementation does not itself establish
a useful recursive neural-weight generator.

The best completed independent full-corpus result before cleanup was
**192,436,984 counted bytes** for the canonical 1,000,000,000-byte corpus, with
exact reconstruction verified. Its archive alone was 192,402,073 bytes; the
preferred total included the source-package alternative under the scoring
formula. That historical implementation is superseded by the retained version.

The retained improved version reduced a controlled 16 MiB prefix archive from
3,842,273 to **3,642,140 bytes**, a **5.2087%** reduction. The prefix decoded
exactly; 33 arbitrary-data round trips and a byte-identical source rebuild were
also reported. Estimated owned memory was 1,283,814,016 bytes, excluding runtime
and allocator overhead. These are prefix measurements: **there is no full
1 GB result for the retained version**. Do not extrapolate a submission score.

At the last rules check, the accepted record was 100,424,672 bytes and the
conservative working successor target was 94,954,909 bytes after allowing for
pending submissions. These are historical thresholds. The current independent
result needs roughly another halving; recheck the live rules and queue elsewhere.

## Lessons from removed experiments

- **Recursive generation is functional, but recursion creates no information.**
  A seed of 800 parameters generated 2,112 then 6,272 generator parameters and
  finally 1,024 bit logits. Exact repair worked. The best small serialized case
  occupied 525 bytes for 128 input bytes, before program/runtime costs. Preserve
  the mechanism as a hypothesis, not a demonstrated compression advantage.
- **Functional scaling is not capable modeling.** A full 1 GB test using a
  repeated tiny-prefix predictor reconstructed exactly but expanded to about
  1.032 GB, with almost everything in raw fallback. It did not rank correction
  schemes on a model trained to predict the complete corpus.
- **Residual correlations can help weak predictors without demonstrating an
  ECC advantage.** Count-conditioned entropy coding improved three weak block
  prediction samples by 9.66% in aggregate and beat the tested syndrome coding.
  With the stronger autoregressive predictor, the transferred count adjustment
  instead enlarged three disjoint sample archives by 5.44%, 6.22% and 9.68%.
  Compare correction methods using identical base predictions and full costs.
- **Smaller weights are not a smaller complete description.** Scalar/vector
  quantization saved stored model bytes but damaged predictions too much. In a
  later real-PPM-prior screen, scale-aware quantization-aware training saved
  about 1.19 MB across two model copies, while adding 0.3349 heldout bits/token.
  Its optimistic allowance after paying for a 1% improvement was only about
  0.0034 bits/token. Better layer-response MSE did not close the coding gap.
- **Standalone improvement need not complement a stronger mixture.** Adding
  the retained context expert through a tested causal residual mixer worsened
  sample coding loss by 0.02092%. Gain/bias and lagged-expert controls also
  lost; an exploratory Bayesian mixture learned to discard the added expert.
  This failed use of the expert does not invalidate its standalone prefix gain.
- **Proxy priors are screening tools.** Cheap order-1 priors do not represent
  native PPM or a full mixer. Evaluate serialized, reloaded candidates with real
  priors, then the actual final mixture on fresh disjoint main-text samples.
  Report whether match, prompt, grammar and pretraining channels are present.
- **Tiny smoke tests can miss the important execution path.** A successful
  small reconstruction can finish before the model activates or a global
  metadata boundary is reached. Verify active-row counters, complete framing,
  hidden sidecar dependencies and source-removed decoding before interpreting
  an integration test as model evidence.
- **Floating-point artifact identity is insufficient.** Require a newly
  completed paired encode/decode on the selected host; do not inherit numerical
  correctness or resource compliance from a published archive or source build.
- **Resident memory and virtual reservation differ.** Monitor process-tree RSS
  separately from address-space caps. A large sparse reservation can fail an
  overly strict virtual limit while resident usage is small. Formal timing also
  needs measured calibration, confinement, cache controls and complete runs.

Failed implementations, fitted parameters, outputs, binaries, logs and source
variants were removed. Only these lessons remain; they are not reproducible
experimental evidence on their own.

## Continuation in a clean environment

Review ORIGINAL_SOURCE.md, extract the single C++ source elsewhere, and compile
with a standard C++17 compiler. An example build is:

```sh
g++ -O3 -DNDEBUG -std=c++17 neural_fsm_v2.cpp -o codec
```

The historical selected prefix configuration used table bits 25 and history
bits 24. The source's command-line interface is `codec c INPUT ARCHIVE 25 24`
and `codec d ARCHIVE OUTPUT`. The archive stores its configuration. Keep encoder
and decoder build settings consistent. These commands are documentation, not
instructions to execute anything in this cleaned project.

Rebuild and behaviorally validate from scratch: empty input, all byte values,
repetitive and random data, corruption handling, source-absent decoding and
causality. Then use preselected disjoint authentic main-text samples. Prioritize
a materially stronger reusable context or jointly trained representation rather
than revisiting the documented failures or merely repackaging existing tools.

Canonical corpus: exactly 1,000,000,000 bytes, SHA-256:

```text
159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc
```

Authoritative starting points for a fresh rules/data review:
[contest rules](https://hutter1.net/prize/hrules.htm) and
[benchmark](https://mattmahoney.net/dc/text.html).

Before any success claim, require complete canonical reconstruction; full
program/model/assets/options accounting under the chosen scoring route;
source/license and package review; offline single-CPU execution without a GPU
or external model/corpus resources; at most 10 GiB process-tree RSS and 100 GB
temporary storage under the applicable rules; and each program within the
measured Geekbench5 allowance of less than 70,000/T hours. All current rules and
judge requirements must be verified anew. No formal qualification is preserved
or implied by this text-only handoff.
