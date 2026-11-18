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

## Performance and prior-art verification — 2026-11-18

Re-ran the original suite: 5 methods passed in 175.153 s. Committed a checkpoint
at `eb8ff39` before changing discovery and scheduling. Expanded scope to allow
other files while requiring target presence in every nonempty tree; added
rename-source rejection and historical-attribute rejection. Added per-invocation
blob caching, identity-edge skipping, backward sequential resolution, bounded
parallel diff workers, disjoint geometric windows, work counters and stage timers.

The expanded regression suite passed all 8 methods in 276.654 s, including the
original 100 randomized histories and new full/windowed checks on 111 histories.
The benchmark then ran alone: 4 workloads × 10 configurations × 10 repetitions
= 400 exact oracle matches. No failed runs or slow configurations were discarded.
Results are warmed-cache measurements, not controlled cold-cache measurements.

The experiment failed the end-to-end speedup hypothesis on every selected case,
despite reproducible edge-stage scaling. Profiling was run after measurements,
not alongside them. See `docs/day3_decision.md` and `docs/profiling-observations.md`.
The broad parallel-blame idea has explicit 2019 prior art; novelty of a narrow
summary/window contribution remains unestablished. See `docs/novelty-review.md`.

Commands: `.venv/bin/python -m bench.run --repeats 10`, `-m bench.analyze`,
`-m bench.profile`, `-m bench.plot`, and `-m bench.presentation`.
No compiled extension, merge support, or unmeasured performance claim was added.
