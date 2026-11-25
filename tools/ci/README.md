# Hosted runner ISA smoke test

Can this particular GitHub Linux VM **execute** an EVEX-encoded 256-bit `vpdpbusd` and return the expected 512 integer lane results? The two dot widths (64/192) and signed weight range (−7…7) match the codec experiment. Inputs are generated, including overflow cases that distinguish non-saturating from saturating addition. There are no weights, corpus samples, production binaries, credentials or inbound transfer services in the test.

A successful job can report either `executed-match` or `unsupported` (CPUID/XCR0 gate, exit 77). The second outcome is not an EVEX pass. A bad output, missing opcode, SIGILL, or resource refusal fails the job. Neither outcome measures the codec, bare-metal isolation, memory eligibility, speedup or contest time. Hosted runner CPUs can change between runs; do not re-run until a preferred CPU appears.

Pushing the topic branch `ci/runner-isa-smoke` with changes to the referenced test or workflow triggers **one** job. There is no PR, schedule or matrix trigger. Manual dispatch is an alternative once the dispatch-enabled workflow is on the default branch. Do not both push and dispatch the same test.

To retrieve a run, select the ID matching the pushed commit, not simply the newest run. For the first attempt (`1`), from the matching topic checkout:

```sh
repo=thearchitector/seedgrow
sha=$(git rev-parse HEAD)
gh run list -R "$repo" --branch ci/runner-isa-smoke --workflow scratchpad.yml --commit "$sha" \
    --json databaseId,headSha,status,conclusion,url
# Set id to the returned databaseId for that SHA.
gh run watch "$id" -R "$repo" --exit-status
dest=$(mktemp -d)
gh run download "$id" -R "$repo" -n "runner-isa-$id-1" -D "$dest"
python3 -IB tools/ci/runner_isa.py verify "$dest" --commit "$sha"
```

The verifier reads only JSON and raw little-endian lanes; it does not run anything from the artifact. GitHub retains the small return for seven days. The next step after an `executed-match`, if warranted, is a *different* correctness test on a cleared short release fixture, not a full-corpus run.
