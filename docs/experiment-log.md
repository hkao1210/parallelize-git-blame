# First-actions experiment log

Date: 2026-11-17. Repository initially contained only a README and icon; Git was
already initialized. No existing implementation or AGENTS.md was found.

Environment: macOS arm64, 10 logical CPUs, Python 3.10.15, Apple clang 21.0.0,
Git 2.54.0 (Apple Git-157). See `results/environment.json` for full strings and
source download hashes. `git diff -h` / `git blame -h` were inspected; help exits
129 normally. Upstream v2.54.0 blame source and documentation were downloaded
and inspected. Apple-specific implementation differences remain unresolved.

Implemented the five requested smallest cases first in the fixture catalog,
then expanded to all requested deterministic categories. Added LF-only line
counting, byte-safe porcelain parsing, zero-length hunk handling, dense terminal
summaries, sequential forward composition, and conservative history validation.
No performance optimization or parallel work has begun.

Commands and recorded outcomes:

- `python3 -m unittest tests.test_correctness -v` — four test methods passed in
  178.572 seconds (11 deterministic histories, 100 randomized histories,
  1,000 algebra trials, initial scope rejections). See `results/tests.txt`.
- Added rejection checks for merges, binary content, file disappearance and
  working-tree attributes; disabled global attributes explicitly. Re-ran the
  deterministic, algebra, and scope tests: four selected methods passed in
  7.973 seconds; see `results/scope-tests.txt`.
- `python3 -m tests.report` — independently regenerates all histories and saves
  exact commit IDs, input bytes, and origin/final-line triples. See
  `results/report-summary.txt` and `results/correctness.json`. This run began
  before the final attribute guard was added; generated fixtures contain no
  attributes, so that guard does not alter their mappings.
- `git diff --check` — no whitespace errors.

No attribution mismatch has been observed. No failed semantic experiment was
hidden or test coverage reduced. The initial review's broad skepticism about
DAG prefix scan remains valid, but it does not rule out composition on a linear
single-file history with fixed Git-compatible whole-blob matching.

Next: review raw results, broaden scope validation to realistic repositories,
profile native blame and the reference, then attempt bounded per-edge workers.
Preserve the reference and exact oracle tests. Do not interpret this correctness
checkpoint as evidence for H1/H2 efficiency or H3 end-to-end speedup. A Day-3
GO/PIVOT decision requires the still-unperformed scaling and realistic workload
experiments; no premature decision report is issued.

Raw-data run completed successfully: 111 histories, 731 revision comparisons, zero mismatches. CLI delete/reintroduce attributed the reinserted line to commit `48ab7a181c2e5857a5e093fa11f6225fe5e470af`, original/final line 2; unsupported config exited 2.
