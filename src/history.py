"""Conservative scope validation and reproducible Git invocation."""
import os
import subprocess
from time import perf_counter
from pathlib import Path

class Unsupported(ValueError):
    pass

def git_environment(env=None):
    clean = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    clean.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
                 LC_ALL='C', GIT_NO_REPLACE_OBJECTS='1')
    clean.update(env or {})
    return clean

def git(repo, *args, env=None):
    return subprocess.check_output(['git', '-c', 'core.attributesFile=' + os.devnull, '-C', str(repo), *args], env=git_environment(env),
                                   stderr=subprocess.PIPE)

def lines(blob):
    # Git splits on LF only, not Python's broader splitlines delimiters.
    return blob.split(b'\n')[:-1] if blob.endswith(b'\n') else (blob.split(b'\n') if blob else [])

def discover(repo, revision, path, stats=None):
    started = perf_counter()
    stats = stats if stats is not None else {}
    object_seconds = 0.0
    cache = {}
    if not revision or revision.startswith('-'):
        raise Unsupported('revision must not be an option')
    if not path or path.startswith('-') or any(c in path for c in ':\n\r\0') or Path(path).is_absolute() or '..' in Path(path).parts:
        raise Unsupported('requires a simple repository-relative path')
    root = Path(git(repo, 'rev-parse', '--show-toplevel').decode().strip())
    for parent in [Path('.'), *Path(path).parents]:
        if (root / parent / '.gitattributes').exists():
            raise Unsupported('working-tree attributes')
    config = git(repo, 'config', '--local', '--list').decode().lower().splitlines()
    if any(x.startswith(('diff.', 'blame.', 'core.attributesfile', 'include.', 'includeif.')) for x in config):
        raise Unsupported('custom diff/blame/attribute/include configuration')
    if git(repo, 'rev-parse', '--is-shallow-repository').strip() != b'false':
        raise Unsupported('shallow history')
    head = git(repo, 'rev-parse', '--verify', revision + '^{commit}').decode().strip()
    if git(repo, 'for-each-ref', 'refs/replace').strip():
        raise Unsupported('replacement objects')
    grafts = Path(git(repo, 'rev-parse', '--path-format=absolute', '--git-path', 'info/grafts').decode().strip())
    attrs = Path(git(repo, 'rev-parse', '--path-format=absolute', '--git-path', 'info/attributes').decode().strip())
    if grafts.exists() or attrs.exists():
        raise Unsupported('grafts or repository attributes')
    commits = []
    for row in git(repo, 'rev-list', '--reverse', '--parents', head).decode().splitlines():
        fields = row.split()
        if len(fields) > 2:
            raise Unsupported('merge commits')
        commits.append(fields[0])
    blobs = []
    seen = False
    for commit in commits:
        entries = git(repo, 'ls-tree', '-r', '-z', commit).split(b'\0')
        found = None
        for entry in filter(None, entries):
            meta, name = entry.split(b'\t', 1)
            if name.split(b'/')[-1] == b'.gitattributes':
                raise Unsupported('historical attributes')
            if name != path.encode():
                continue
            mode, kind, oid = meta.split()
            if mode not in (b'100644', b'100755') or kind != b'blob':
                raise Unsupported('non-regular file')
            found = oid.decode()
        if found is None and any(entries):
            raise Unsupported('target absent from a nonempty tree; possible rename ancestry')
        if found is None and seen:
            raise Unsupported('whole-file deletion/recreation')
        seen |= found is not None
        before = perf_counter()
        if found and found not in cache:
            cache[found] = git(repo, 'cat-file', 'blob', found)
        blob = cache[found] if found else b''
        object_seconds += perf_counter() - before
        if b'\0' in blob:
            raise Unsupported('binary NUL content')
        blobs.append((found, blob))
    if not seen:
        raise Unsupported('target file does not exist')
    stats.update(history_seconds=perf_counter()-started-object_seconds,
                 object_seconds=object_seconds, commits=len(commits),
                 unique_blobs=len(cache), blob_bytes=sum(map(len, cache.values())))
    return commits, blobs
