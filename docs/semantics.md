# Sequential semantics checkpoint

## Pinned implementation and evidence

Execution uses Git 2.54.0 (Apple Git-157). Source inspection used upstream
[v2.54.0 blame.c](https://github.com/git/git/blob/v2.54.0/blame.c)
(`diff_hunks`, `pass_blame_to_parent`) and
[builtin/blame.c](https://github.com/git/git/blob/v2.54.0/builtin/blame.c)
(`git_blame_config`, initialization of `sb.xdl_opts`). Download hashes and URLs
are recorded in `results/environment.json`. Upstream is not proof that Apple's
patched binary has identical internals; differential tests validate that binary.

`pass_blame_to_parent` loads the full parent/child blobs, calls xdiff, and passes
unchanged ranges to the parent. Remaining lines terminate at the child commit.
The default algorithm is Myers, with the configured indent heuristic inherited
by blame. Thus fixed, full-blob per-edge hunks appear suitable for composition
on this restricted single-parent history. This is a feasibility argument, not a
proof for all Git behavior or versions.

The [blame documentation](https://github.com/git/git/blob/v2.54.0/Documentation/git-blame.adoc)
notes automatic whole-file rename following. Consequently merely passing
`--no-renames` to diff would not establish scope correctness. We conservatively
reject any other historical file and whole-file disappearance after creation.
The [diff documentation](https://github.com/git/git/blob/v2.54.0/Documentation/diff-options.adoc)
describes the indent heuristic and hunk generation options.

## Boundary algebra

For boundaries A (older), B, C (newer), summary S[A,B] has one entry for each
line in B. An entry is either a zero-based surviving index into A, or a terminal
`Origin(commit, original_line)` inside (A,B]. Root lines terminate at the root;
creation from an absent file terminates at its creation commit. Original origin
line numbers are one-based. The final output preserves final line order.

`compose(older, newer)` implements S[A,B] composed with S[B,C]: replace each
surviving index in newer by older[index]; leave newer terminal origins untouched.
Identity is the index vector of a boundary. Associativity follows entrywise:
terminal entries remain terminal; surviving entries perform the same successive
lookups in either parenthesization. Composition requires compatible boundaries;
the plain tuple representation relies on the caller for this invariant.
Executable tests cover 1,000 random compatible triples, identities, and terminal
absorption. These tests verify the algebra, not Git matching correctness.

Changed child ranges receive terminal origins immediately. Reintroduced text
never searches for earlier equal text, so deletion followed by reinsertion does
not reconnect an old origin. Adjacent matching uses Git diff with Myers,
indent heuristic enabled, zero context, zero inter-hunk context, and no external
diff/textconv/rename processing. Unchanged ranges become index mappings. Hunk
coordinates with zero-length ranges have special insertion/deletion semantics.
Lines split on LF only; missing final newline is left to Git's diff semantics.

## Scope and unresolved questions

Only complete linear ancestry, committed regular file content, no NUL bytes,
and default attribution. All ancestors are inspected, including untouched
commits, before mapping. Empty trees before creation are supported. Other
historical paths, merges, shallow repositories, replace refs, grafts, local
attributes, custom diff/blame/include configuration and whole-file disappearance
are rejected. Global/system configuration is excluded for reproducibility.
CLI accepts no -M/-C/-w/ignore-rev/reverse/range options. Ignored revisions cannot
enter through local blame config. Target content may become empty and refill.

Unresolved: broader real repository scope validation, Apple source differences,
large-file xdiff limits, unusual repository extensions/configuration, and whether
adversarial ambiguous hunks reveal a discrepancy. Full-blob matching is crucial;
computing diffs on unresolved slices instead could change alignment. No claim
about merges, rename tracking, copied/moved lines, or ignored commits is made.

Global attributes are disabled with `-c core.attributesFile=/dev/null` on every Git invocation; working-tree `.gitattributes` along the target path are rejected.
