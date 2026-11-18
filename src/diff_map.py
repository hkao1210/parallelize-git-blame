"""Extract unchanged line correspondence from zero-context Git diff hunks."""
import re
from time import perf_counter
from .history import git, lines
from .provenance import Origin

HUNK = re.compile(rb'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', re.M)

def edge(repo, parent, commit, path, old_blob, new_blob, stats=None):
    start = perf_counter()
    patch = git(repo, 'diff', '--no-ext-diff', '--no-textconv', '--no-renames',
                '--diff-algorithm=myers', '--indent-heuristic', '--no-color',
                '--unified=0', '--inter-hunk-context=0', parent, commit, '--', path)
    after_diff = perf_counter()
    mapping = []
    old_pos = new_pos = 0
    for match in HUNK.finditer(patch):
        a, ac, b, bc = match.groups()
        ac, bc = int(ac) if ac is not None else 1, int(bc) if bc is not None else 1
        a, b = int(a) - bool(ac), int(b) - bool(bc)
        assert a - old_pos == b - new_pos
        mapping.extend(range(old_pos, a))
        mapping.extend(Origin(commit, i + 1) for i in range(b, b + bc))
        old_pos, new_pos = a + ac, b + bc
    mapping.extend(range(old_pos, len(lines(old_blob))))
    assert len(mapping) == len(lines(new_blob))
    result = tuple(mapping)
    if stats is not None:
        stats.update(diff_seconds=after_diff-start, summary_seconds=perf_counter()-after_diff,
                     diff_input_bytes=len(old_blob)+len(new_blob), patch_bytes=len(patch))
    return result
