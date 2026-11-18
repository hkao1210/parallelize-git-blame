# Performance verification and architecture decision

**PIVOT for the current implementation.**

All 400 measured runs matched the native oracle. Ten measurements per configuration/workload; warmed caches only.

| Workload | Native median (s) | Best custom | Custom median (s) | Native/custom |
|---|---:|---|---:|---:|
| zlib_deflate | 0.0295 | windowed-8 | 2.3401 | 0.013x |
| zlib_inflate | 0.0245 | full-4 | 2.2562 | 0.011x |
| persistent | 0.0781 | windowed-8 | 1.3209 | 0.059x |
| recent_rewrite | 0.0833 | sequential | 1.2846 | 0.065x |

A ratio below 1 means the prototype is slower. Best-of-configurations is descriptive, not an unbiased estimate of future performance.

| Workload | 8-worker edge-stage speedup | Bootstrap 95% interval |
|---|---:|---:|
| zlib_deflate | 2.87x | 2.79–2.94 |
| zlib_inflate | 2.68x | 2.09–2.99 |
| persistent | 3.75x | 3.51–4.01 |
| recent_rewrite | 2.88x | 2.58–3.48 |

## Gates and hypotheses

- Gate A: scoped empirical correctness passed; see regression logs and raw comparisons.
- Gate B / H1: real-workload edge-stage scaling signal: **True**. This stage includes Git process startup, object reopening, hunk extraction, dense mapping, and dispatch; it is not an isolated xdiff CPU benchmark.
- H2: dense summaries remain correct on tested inputs. See composition times and memory in summary.csv. Compact intervals and CPU-parallel composition remain unimplemented; algorithmic novelty/efficiency is not established.
- Gate C / H3: real-workload end-to-end ≥1.2x signal: **False**. No general performance advantage can be inferred from stage speedup.

## Interpretation and next decision

The prototype validates the scheduling experiment, not a production speedup. Eager history validation and object loading remain serial; spawning Git separately for tree reads, blob reads and diffs incurs overhead. Windows only save diff work. Native Git already avoids irrelevant history and emits richer output than this prototype.

Pivot away from claiming that a Python subprocess scan is a faster blame replacement. A further bounded experiment should first batch object access/history validation and use a native in-process diff interface, then rerun the same benchmarks. This is a proposed follow-up, not an implemented or measured speedup. Do not add merges or complex attribution options before obtaining a real end-to-end signal.

The broad parallel-blame idea has documented prior art (2019). Novelty of the narrow speculative-summary combination remains unestablished; see novelty-review.md. A negative-results systems study is currently more defensible than a new-algorithm claim.

Coverage is two files from one historical real repository plus two generated controls, one machine, no controlled cold cache. This is not the requested eventual 3–5-large-repository study, and cannot rule out wins on other workloads. Bootstrap intervals are descriptive and uncorrected for multiple comparisons.

Raw data and reproducibility metadata: results/performance/raw.jsonl, summary.csv, metadata.json, workloads.json. Charts: performance.png and wall-times.png. Method: docs/benchmark-method.md.
