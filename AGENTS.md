# Local research resources

WSL2 capacity is configured as 14 GB RAM and 16 GB swap, with gradual memory
reclaim and sparse VHD enabled. Check available memory before launching work.
Run one experiment process tree at a time, including across subagents. Use all
available CPU cores and threads; impose no additional CPU affinity, thread-count
or niceness restriction. Use `tools/resource_guard.py` for memory monitoring and
serialization. It requires 3 GiB available RAM before launch and monitors a
2 GiB combined available-RAM/free-swap reserve plus a 512 MiB emergency available-
RAM floor. There is no fixed process-tree RSS cap; temporary swap growth is
allowed. Record process-tree RSS/swap and host headroom. These are monitored
safeguards, not a kernel-enforced quota. Reduce batches on sustained memory
pressure or unproductive swapping.
Research has no artificial elapsed-time or CPU-time budgets. Set
`--wall-seconds 0`; retain the shared lock and memory-pressure monitoring.
Save checkpoints and resume work without repeating completed experiments.

# Benchmarking and references

Success requires a complete counted result at least 1% below the current official
Hutter Prize winner, with exact full-corpus reconstruction. Refresh that record
from the official site. A gain over a weaker project compressor is not success;
do not retain inferior project compressors as the performance target.

Do not download existing (de)compressors or their source in order to benchmark against any POC or experiment; use their published benchmarks from <https://mattmahoney.net/dc/text.html> instead.

Monitor encoding progress and stop when committed counted bytes, or a valid
lower bound including unavoidable remaining cost, rule out the qualifying
threshold. A failed run need not process the full corpus. Forecast-based stops
are screening decisions, not proof of a full-corpus result. Never claim success
without exact complete reconstruction and full accounting.

# Cleanliness and experimentation

This repo must contain only the ACTIVE proof of concept. If building and running experiments or scripts as a scratchpad, delete and clean up their files. If the experiment is a failure, document findings and lessons in `docs/CROSS_DOMAIN_RESULTS.md`; if successful, incorporate the code into the current active proof of concept.
