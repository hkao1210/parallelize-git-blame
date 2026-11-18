"""Parse native line-porcelain without assuming UTF-8 file contents."""
import re
from .history import git

HEADER = re.compile(rb'^([0-9a-f]{40,64}) (\d+) (\d+)(?: \d+)?$')

def blame(repo, revision, path):
    raw = git(repo, 'blame', '--line-porcelain', revision, '--', path)
    result = []
    pending = None
    for row in raw.split(b'\n'):
        match = HEADER.fullmatch(row)
        if match:
            commit, original, final = match.groups()
            pending = (commit.decode(), int(original), int(final))
        elif row.startswith(b'\t'):
            if pending is None:
                raise ValueError('porcelain content without header')
            result.append(pending)
            pending = None
    return result
