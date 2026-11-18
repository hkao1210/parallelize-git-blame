import argparse
import json
from src.schedulers import run

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('repo')
    parser.add_argument('revision')
    parser.add_argument('path')
    parser.add_argument('--mode', choices=['sequential', 'full', 'windowed'], required=True)
    parser.add_argument('--workers', type=int, default=1)
    parser.add_argument('--window', type=int, default=8)
    args = parser.parse_args()
    result, stats = run(args.repo, args.revision, args.path, args.mode, args.workers, args.window)
    print(json.dumps({'attribution': result, 'stats': stats}, separators=(',', ':')))
