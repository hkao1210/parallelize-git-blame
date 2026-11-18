# Performance verification method

## Inputs and scope

Four preselected workloads: actual zlib `deflate.c` and `inflate.c` at the 128th
commit of the initial genuinely linear history, plus two deterministic generated
48-commit histories with 12,000 lines. Generated histories replace 64 lines per
edge; one fully rewrites the file at revision 44. The persistent case retains
many root origins; the rewrite case lets windows terminate early. They are
controlled workloads, not real-repository wins. Workloads were selected before
performance measurements. No slow cases are removed based on results.

`results/performance/workloads.json` stores repository URLs, exact commit IDs,
paths, and generation rules. The external zlib clone is read-only during tests.
No first-parent approximation, history rewriting, or merge acceptance is used.
A full root-to-input ancestry check rejects merges. Other files are now permitted
when the target exists at every nonempty tree, and historical attributes remain
unsupported. Git's `find_origin` checks the same path before attempting rename
tracking, which justifies this narrower expansion of scope. Creation after empty
initial commits is still allowed. A target absent from any nonempty tree is
rejected, so creation in many real repositories remains unsupported.

## Configurations

Native `git -c core.attributesFile=/dev/null -C REPO blame --line-porcelain SHA -- PATH`;
custom demand-driven sequential; full edge processing with 1/2/4/8 workers;
and disjoint backward windows starting at 8 revisions with 1/2/4/8 workers.
Workers are Python coordinator threads launching independent CPU-running Git
processes. Python dense summary construction and composition are sequential/GIL
bound; this is **not** a parallel composition-tree implementation.

The full mode computes all differing-blob edge diffs, even if origins could be
resolved sooner. Identical blob IDs skip diff work in every custom mode. Windows
are disjoint, double in size after each unresolved boundary, and never recompute
an edge. They complete a window before testing termination, including speculative
unneeded edges. Only terminal origins permit early stopping; surviving indices
must continue or reach the root. `duplicate_diffs` is zero by construction and
covered by tests. Discovery and blob retrieval remain eager for every mode;
windowing does not claim to stop those stages. Blob payloads are cached by OID
within one invocation only; no persistent preprocessing is hidden.

## Timing and correctness

Ten measured repetitions per configuration and workload, one configuration at a
time; order shuffled reproducibly within each repetition. One unmeasured warm-up
per configuration. Caches are not flushed: results are warmed OS-cache runs, not
controlled cold-cache results. Input commits are resolved and all object reads,
validation, process startup, scheduling, composition, and output happen inside
each timed command. Setup/generation/clone and oracle computation are outside
query timing for all configurations. Native Git produces richer porcelain output
than custom JSON triples; this favors the prototype's output cost. No native
output parsing is included in its timed command. Custom JSON serialization is
included. Both outputs are completely captured before stopping timing, then
compared exactly by commit/original/final line triples outside the timer.

`/usr/bin/time -l` wraps each command on macOS. Parent wall timing includes its
small startup cost and stdout capture. A 5ms psutil sampler records the process
tree RSS; this is a sampled peak, may miss short peaks, and sums shared memory
more than once. `time -l` also reports maximum process RSS, not simultaneous
whole-tree peak. CPU time is the RUSAGE_CHILDREN user+system delta. Sampling
introduces overhead; native commands are especially short, so microsecond-scale
interpretation is inappropriate. No CPU affinity or frequency isolation is used.

The JSONL retains every measurement, command, output hash, correctness result,
and stage/work counters. Summary CSV/JSON reports median, nearest-rank p95
(with n=10 this is the maximum), sample variance, CPU and memory. Blob bytes are
logical unique payloads read into Python, not physical disk reads. Diff bytes
count both blob inputs per executed diff and can repeat; native disk-byte counts
are unknown. Task diff/summary seconds are summed worker elapsed times, **not**
parallel wall times or CPU times. `edge_stage_seconds` is measured wall time
including diff extraction, mapping, and dispatch. Git internally reopens objects
for each diff; those payloads are accounted logically but disk caching is opaque.

## Interpretation limits

Two files from one modest historical real repository cannot establish generality
across 3–5 large modern repositories. This is a feasibility test, not a completed
large-repository performance study. Stage scaling can support H1 for this workload
but does not imply end-to-end improvement. Low composition time at these sizes
supports practicality only; it does not prove a novel compact summary algorithm.
The recorded profile of the Python implementation includes subprocess waits.
Native work counters can show work avoided but do not identify native CPU
hotspots such as decompression versus xdiff. Those remain a follow-up question
if this architecture becomes competitive.
