# Profiling observations

Measured on Apple M4 (10 logical cores), Git 2.54.0 (Apple Git-157).
The repeated uninstrumented benchmark is the performance evidence. The separate
cProfile runs are diagnostic, slower, and never substituted for benchmark times.

For zlib `deflate.c`, full-8 median history validation/enumeration is 1.371 s,
blob retrieval 0.692 s, edge processing 0.250 s, and composition 0.0085 s, against
2.359 s total. The first two stages alone sum to about 2.06 s. Even eliminating
all edge-stage cost would not approach native's 0.0295 s on this implementation.
The Python profile makes 273 Git subprocess calls and spends most cumulative
time in subprocess communication/polling. This identifies a pipeline bottleneck;
it does not distinguish child xdiff CPU from object decompression or executable
startup within each wait. Creation of the subprocess objects itself also costs
time. A native hotspot profile has not been obtained.

Native `--show-stats` reports 68 patch computations for deflate and 41 for inflate.
The full custom implementation computes exactly those counts as well. Thus the
real-file slowdown here is not explained by more diff edges: conservative
full-history tree scans, repeated process startup/object access, Python pipeline
overhead and lack of integrated native caches are the relevant differences.
A causal partition of their individual costs requires further instrumentation.

On the generated recent-rewrite history, native and custom sequential each
compute 4 patches. Full mode computes 47, whereas windowed mode computes 8 and
leaves 39 older edges unprocessed. Windows therefore avoid 39 of 47 diffs, but
still do twice the sequential demand-driven diff work and load all 48 unique
blobs. Windowed-8 has median wall time 1.387 s, versus 1.285 s custom sequential
and 0.0833 s native. Native reports 6 blob reads; custom retrieves 48 unique blob
payloads. Counter definitions differ, so do not interpret the read-count ratio
as physical disk I/O amplification.

Composition medians for full-8 range from about 0.0067 to 0.0202 s in these
workloads. This does not justify investing in CPU-parallel tree composition
before fixing retrieval/startup costs. The dense representation remains
unbounded with history/file size. Full-8 median sampled process-tree peaks span
about 49–84 MB here; this is sampled RSS with shared pages counted per process,
not a strict memory bound or precise physical footprint.

Raw evidence: `results/performance/summary.csv`, `profiles.json`, `*-profile.txt`
and `.prof` files. Run profiles only after timing: `.venv/bin/python -m bench.profile`.
