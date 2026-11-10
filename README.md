# SeedGrow

Research into exact compression of the canonical enwik9 Wikipedia corpus.
The target is at least 1% below the current official Hutter Prize winner,
including every counted program, model, archive and execution option.

Give [AUTONOMOUS_RESEARCH_PROMPT.md](docs/AUTONOMOUS_RESEARCH_PROMPT.md) to a
research agent. It contains the complete investigation brief, ten mechanisms,
resource policy, acceptance criteria and reporting requirements.
[COMPRESSION_LANDSCAPE.md](docs/COMPRESSION_LANDSCAPE.md) provides the literature
and submission audit. The agent stores resumable checkpoints under `.research/`
and writes findings to `docs/CROSS_DOMAIN_RESULTS.md`.

The corpus is `references/enwiki9`, exactly 1,000,000,000 bytes, SHA-256
`159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc`.
The official download is <https://mattmahoney.net/dc/enwik9.zip>.

Run builds, training and experiments through `tools/resource_guard.py` with
`--wall-seconds 0`. All available CPU cores/threads and temporary swap use are
permitted. Follow [AGENTS.md](AGENTS.md) for serial execution and RAM/swap
headroom monitoring. Research has no artificial time budgets. Candidate source belongs in
the worktree; generated artifacts belong in `.research/` and must be cleaned.

Official record: <https://www.hutter1.net/prize/>.
Scoring rules: <https://www.hutter1.net/prize/hrules.htm>.
Project license: [LICENSE](LICENSE).
