<img src="assets/icon.svg" width="64" height="64" alt="">

# Speculative Parallel Git Blame

Correctness-first feasibility experiment. Contains a dense sequential reference,
bounded parallel Git diff workers, and disjoint geometric backward windows.
No novelty or speedup is presumed. See [prior-art review](docs/novelty-review.md)
and [benchmark method](docs/benchmark-method.md). Initial correctness checkpoint:
111 histories, 731 revision comparisons, zero mismatches.

Python 3.10+ and Git required. Tested Git: `2.54.0 (Apple Git-157)`.

```sh
python3 -m unittest tests.test_correctness -v
python3 -m tests.report
python3 -m src /path/to/repo HEAD file.txt
python3 -m bench.worker /path/to/repo HEAD file.txt --mode windowed --workers 8
```

Attribution triples are `[origin_commit, original_line, final_line]`, one-based.
All commands ignore global/system Git config and global attributes. Native oracle:
`git -c core.attributesFile=/dev/null -C REPO blame --line-porcelain SHA -- PATH`.

Accepted histories must be genuinely linear and complete, without merges,
ignored revisions, rename ancestry, binary NUL content, attributes, or custom
diff/blame config. The selected regular file must exist at every nonempty
historical tree; other files are allowed. Empty commits before creation are
supported. Unsupported inputs explicitly fail. See [semantics](docs/semantics.md).

Reproduce the performance experiment (macOS, ten runs per configuration):

```sh
python3 -m venv .venv
.venv/bin/pip install -r bench/requirements.txt
git clone https://github.com/madler/zlib.git /tmp/parallel-blame-zlib
python3 -m bench.prepare --zlib /tmp/parallel-blame-zlib
.venv/bin/python -m bench.run --repeats 10
.venv/bin/python -m bench.plot
```

The preparer refuses to overwrite generated repositories; use a fresh `--output`
directory when regenerating. The exact measured source revision is in
`results/performance/workloads.json`. A later zlib default branch may change;
use that manifest to reproduce the recorded query rather than assuming HEAD.
Raw measurements, source hashes, dependency versions, and charts live in
`results/performance/`. No controlled cold-cache measurements are claimed.

## Measured result

**PIVOT for the current architecture:** 400/400 benchmark outputs matched native
Git, but the fastest custom configuration was 15–92× slower end to end across
these four workloads. Eight-worker edge-stage speedups were 2.68–3.75×.
This is two files from one real repository plus two generated controls, not a
large-repository generality result. The broad parallel-blame idea has prior art;
novelty of the narrow approach remains unestablished.

See [decision and measurements](docs/day3_decision.md),
[profile observations](docs/profiling-observations.md), and
[raw summary](results/performance/summary.csv). Regenerate reports and figures:

```sh
.venv/bin/python -m bench.analyze
.venv/bin/python -m bench.profile
.venv/bin/python -m bench.plot
.venv/bin/python -m bench.presentation
```
