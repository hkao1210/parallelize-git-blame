# Correctness checkpoint

- Installed Git: 2.54.0 (Apple Git-157).
- Histories: 111 (11 deterministic, 100 seeded randomized).
- Revision comparisons: 731.
- Exact mismatches: 0.
- Compared fields: origin commit SHA, original line number, final line number.
- Algebra: 1,000 random compatible summary triples; associativity, identity,
  and terminal propagation checks passed.

Raw inputs and every expected/actual triple: `results/correctness.json`.
Unit-test output: `results/tests.txt` and `results/scope-tests.txt`.

Gate A passes for the current conservative scope. This supports the feasibility
of composing fixed adjacent-revision mappings, without proving all histories.
No discrepancy counterexample was found. Gates B/C remain untested; there is no
speedup, novelty, or overall GO claim. Before parallel implementation, broaden
scope validation and profile realistic accepted inputs.
