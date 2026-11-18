import argparse
import json
from .history import Unsupported
from .schedulers import sequential

parser = argparse.ArgumentParser(description='Sequential single-file linear blame feasibility prototype')
parser.add_argument('repo')
parser.add_argument('revision')
parser.add_argument('path')
args = parser.parse_args()
try:
    print(json.dumps(sequential(args.repo, args.revision, args.path)))
except Unsupported as error:
    parser.exit(2, f'Unsupported: {error}\n')
