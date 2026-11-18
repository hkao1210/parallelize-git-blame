"""Sequential reference only; parallel execution awaits correctness review."""
from .history import discover, lines
from .diff_map import edge
from .provenance import Origin, compose

def sequential(repo, revision, path):
    commits, blobs = discover(repo, revision, path)
    summary = tuple(Origin(commits[0], i + 1) for i in range(len(lines(blobs[0][1]))))
    for index in range(1, len(commits)):
        mapping = edge(repo, commits[index-1], commits[index], path,
                       blobs[index-1][1], blobs[index][1])
        summary = compose(summary, mapping)
    return [(x.commit, x.line, i + 1) for i, x in enumerate(summary)]
