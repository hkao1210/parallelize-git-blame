"""Deterministic workload selection; no rewriting of external repository history."""
import argparse
import json
from pathlib import Path
from src.history import git
from tests.fixtures import create

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--zlib', required=True)
    parser.add_argument('--output', default='.bench-workloads')
    args = parser.parse_args()
    root = Path(args.output).resolve()
    root.mkdir(exist_ok=True)
    real = Path(args.zlib).resolve()
    rows = git(real, 'rev-list', '--first-parent', '--reverse', '--parents', 'HEAD').decode().splitlines()
    prefix = []
    for row in rows:
        fields = row.split()
        if len(fields) > 2:
            break
        prefix.append(fields[0])
    # Preselected by history depth, before any timings. Do not select fastest cases.
    commit = prefix[min(127, len(prefix)-1)]
    workloads = [{'name': 'zlib_' + path[:-2], 'kind': 'real', 'repo': str(real),
                  'revision': commit, 'path': path, 'source': 'https://github.com/madler/zlib.git',
                  'selection': '128th commit of initial linear prefix (or last if shorter)',
                  'available_linear_prefix': len(prefix)} for path in ('deflate.c', 'inflate.c')]
    for locality in ('persistent', 'recent_rewrite'):
        repo = root / locality
        if repo.exists():
            raise RuntimeError(f'refusing to overwrite {repo}; choose a fresh output directory')
        content = [f'line {i:05d} original\n'.encode() for i in range(12000)]
        versions = [b''.join(content)]
        for revision in range(1, 48):
            for offset in range(64):
                pos = (revision * 131 + offset) % len(content)
                content[pos] = f'line {pos:05d} edit {revision}\n'.encode()
            if locality == 'recent_rewrite' and revision == 44:
                content = [f'rewritten {i:05d} revision 44\n'.encode() for i in range(len(content))]
            versions.append(b''.join(content))
        commits = create(repo, versions)
        git(repo, 'repack', '-adq')
        workloads.append({'name': locality, 'kind': 'generated', 'repo': str(repo),
                          'revision': commits[-1], 'path': 'file.txt', 'source': 'bench/prepare.py',
                          'commits': commits, 'selection': '48 revisions, 12000 lines, 64 local replacements/edge; optional rewrite at 44'})
    for w in workloads:
        blob = git(w['repo'], 'show', w['revision'] + ':' + w['path'])
        w['head_lines'] = len(blob.splitlines())
        w['head_bytes'] = len(blob)
        w['history_commits'] = git(w['repo'], 'rev-list', '--reverse', w['revision']).decode().splitlines()
        w['packed_objects'] = git(w['repo'], 'count-objects', '-v').decode()
    Path('results/performance/workloads.json').write_text(json.dumps(workloads, indent=2)+'\n')
    print(json.dumps(workloads, indent=2))

if __name__ == '__main__':
    main()
