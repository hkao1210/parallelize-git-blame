# Current limitations (2026-11-18)

The performance prototype has bounded independent Git diff workers and disjoint
backward windows. Dense composition is sequential; no parallel composition tree
or compact interval representation has been implemented. Python blob caching is
per invocation, eager, and unbounded with history size. Speculative windows save
diff work, not the full-history validation or initial object reads. Whole-tree
inspection and per-blob subprocess startup can dominate the cost.

Only complete linear histories with a regular target present in every nonempty
tree are accepted. This excludes many real files created later in a project's
life. No merges, rename ancestry, attributes, ignored revisions, -M/-C, or binary
NUL content. Global/system configuration is sanitized. Empirical correctness is
not a proof for all histories or all Git builds; upstream source inspection is
not verification of Apple's patches.

The benchmark uses two files from one real historical repository and two
synthetic histories, on one machine. Warmed cache runs only; no controlled cold
cache, affinity, or frequency isolation. Process-tree memory is sampled, and
byte counts are logical payloads rather than measured physical disk I/O. Native
work counters and custom stage profiling do not constitute a detailed native
CPU hotspot profile. Broad performance generality remains unverified.

Novelty is not established. The broad parallel-blame idea predates this project;
see `docs/novelty-review.md`. Any conclusion about the current architecture must
not be generalized into a proof that every parallel blame algorithm is slow.
