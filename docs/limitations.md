# Limitations

This is the requested first sequential checkpoint. No multicore prototype,
window scheduler, realistic repository benchmark, profiler result, or go/no-go
performance decision exists yet. Gate A is empirical and scoped to accepted
inputs; B/C have not been attempted. No novelty claim has been evaluated.

The dense reference eagerly enumerates every ancestor and materializes every
blob, repeatedly spawns Git, and composes forward. It has no blob cache, bounded
memory guarantee, interval compression, early stopping, or byte accounting.
It is unsuitable as evidence of performance feasibility. Its purpose is to
validate matching and terminal-origin composition before optimization.

Historical trees containing any second file are explicitly unsupported in this
checkpoint. This is stricter than the eventual one-target-file experiment, to
avoid silently accepting rename sources or attribute rules. Real repositories
will require careful scope validation before benchmark inclusion.

Tests run on one installed Apple Git binary. Passing randomized tests does not
prove correctness for arbitrary histories or other Git versions. Configuration
is sanitized; results are not promised to match a user's customized blame run.
