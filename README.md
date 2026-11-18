<img src="assets/icon.svg" width="64" height="64" alt="">

# Speculative Parallel Git Blame

Correctness-first feasibility experiment. This first checkpoint implements a
**sequential dense reference**, not a parallel blame implementation. Novelty and
speedup are unverified. Python 3.10+ and Git are required; no Python dependencies.
Tested Git: `2.54.0 (Apple Git-157)`; complete metadata in `results/environment.json`.

```sh
python3 -m unittest tests.test_correctness -v
python3 -m tests.report
python3 -m src /path/to/isolated/repository HEAD file.txt
```

Output records are `[origin_commit, original_line_number, final_line_number]`,
with one-based line numbers. Native oracle command:

```sh
git -c core.attributesFile=/dev/null -C <repo> blame --line-porcelain <commit> -- file.txt
```

Both paths run with global/system Git configuration disabled and Git environment
variables cleared (see `src/history.py`). They read committed content, not working
files. Unsupported inputs raise an explicit error. This initial version accepts
only linear, complete repositories whose historical trees contain **only the
selected regular file** (or are empty before creation). This conservative limit
excludes rename/copy sources and attributes; it must be relaxed with validation
before realistic repository benchmarks. No merges, whole-file deletion/recreation,
binary NULs, ignored revisions, custom diff settings, or advanced blame options.

`tests/fixtures.py` creates deterministic isolated temporary repositories with
fixed timestamps. Eleven named fixtures cover insertions, deletion/reintroduction,
repeated lines, replacement, empty content, missing terminal newline, whitespace,
alternating edits, creation, untouched commits, and CRLF. One hundred seeded
random histories exercise ambiguous matches. Every existing-file revision is
compared against native blame. `results/correctness.json` preserves contents,
commit IDs, and both output triples, including exact discrepancies if any.

See `docs/semantics.md`, `docs/limitations.md`, and `docs/experiment-log.md`.
Parallel scheduling and performance claims are deferred until this checkpoint
has been assessed. The three-day decision is not yet available.

Global attributes are disabled with `-c core.attributesFile=/dev/null` on every Git invocation; working-tree `.gitattributes` along the target path are rejected.
