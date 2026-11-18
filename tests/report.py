"""Persist reproducible inputs and exact oracle/prototype discrepancies."""
import json
import tempfile
from pathlib import Path
from src.oracle import blame
from src.schedulers import sequential
from .fixtures import CASES, create, random_versions

def main():
    records = []
    cases = list(CASES.items()) + [(f'random_{seed}', random_versions(seed)) for seed in range(100)]
    for name, versions in cases:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            commits = create(repo, versions)
            checks = []
            for commit, content in zip(commits, versions):
                if content is None:
                    continue
                actual, expected = sequential(repo, commit, 'file.txt'), blame(repo, commit, 'file.txt')
                checks.append({'commit': commit, 'match': actual == expected,
                               'actual': actual, 'expected': expected})
            records.append({'name': name, 'versions_hex': [v.hex() if v is not None else None for v in versions],
                            'commits': commits, 'checks': checks})
    output = {'histories': len(records), 'comparisons': sum(len(x['checks']) for x in records),
              'mismatches': sum(not c['match'] for x in records for c in x['checks']), 'records': records}
    Path('results/correctness.json').write_text(json.dumps(output, indent=2) + '\n')
    print(json.dumps({k:v for k,v in output.items() if k != 'records'}))
    return bool(output['mismatches'])

if __name__ == '__main__':
    raise SystemExit(main())
