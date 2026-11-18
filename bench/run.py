"""Serial benchmark configurations, warmed caches, fresh process per measurement."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import random
import re
import resource
import statistics
import subprocess
import sys
import tempfile
import threading
import time
import psutil
from src.history import git, git_environment
from src.oracle import blame, parse

OUT = Path('results/performance')

def measure(argv):
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    with tempfile.NamedTemporaryFile() as timing:
        start = time.perf_counter()
        process = subprocess.Popen(['/usr/bin/time', '-l', '-o', timing.name, *argv],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   env=git_environment())
        result = {}
        done = threading.Event()
        def collect():
            result['stdout'], result['stderr'] = process.communicate()
            result['end'] = time.perf_counter()
            done.set()
        thread = threading.Thread(target=collect)
        thread.start()
        peak = 0
        parent = psutil.Process(process.pid)
        while not done.is_set():
            try:
                descendants = [parent] + parent.children(recursive=True)
            except psutil.Error:
                descendants = []
            rss = 0
            for child in descendants:
                try:
                    rss += child.memory_info().rss
                except psutil.Error:
                    pass
            peak = max(peak, rss)
            done.wait(.005)
        thread.join()
        usage = Path(timing.name).read_text()
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    if process.returncode:
        raise RuntimeError(f'{argv}: {result["stderr"].decode(errors="replace")}')
    match = re.search(r'(\d+)\s+maximum resident set size', usage)
    return result['stdout'], {
        'wall_seconds': result['end']-start,
        'cpu_seconds': after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,
        'max_process_rss_bytes': int(match[1]) if match else None,
        'sampled_tree_peak_rss_bytes': peak, 'stdout_bytes': len(result['stdout']),
        'command': argv,
    }

def summarize(rows):
    groups = {}
    for row in rows:
        groups.setdefault((row['workload'], row['configuration']), []).append(row)
    summary = []
    for (workload, config), values in groups.items():
        walls = [r['wall_seconds'] for r in values]
        item = dict(workload=workload, configuration=config, runs=len(values),
                    median_seconds=statistics.median(walls),
                    p95_seconds=sorted(walls)[math.ceil(.95*len(walls))-1],
                    variance_seconds2=statistics.variance(walls) if len(walls)>1 else 0,
                    correctness_rate=sum(r['correct'] for r in values)/len(values))
        for key in ('cpu_seconds', 'max_process_rss_bytes', 'sampled_tree_peak_rss_bytes',
                    'history_seconds', 'object_seconds', 'edge_stage_seconds',
                    'diff_task_seconds', 'summary_task_seconds', 'compose_seconds',
                    'origin_seconds', 'blob_bytes', 'diff_input_bytes', 'patch_bytes',
                    'diffs', 'identity_edges', 'unprocessed_edges'):
            field = [r[key] for r in values if key in r and r[key] is not None]
            item['median_'+key] = statistics.median(field) if field else None
        summary.append(item)
    for row in summary:
        baseline = next(r for r in summary if r['workload']==row['workload'] and r['configuration']=='native')
        row['speedup_vs_native'] = baseline['median_seconds']/row['median_seconds']
    return summary

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repeats', type=int, default=10)
    parser.add_argument('--workloads', default=str(OUT/'workloads.json'))
    args = parser.parse_args()
    workloads = json.loads(Path(args.workloads).read_text())
    configurations = [('native', 1), ('sequential', 1)] + [(mode, n) for mode in ('full', 'windowed') for n in (1,2,4,8)]
    metadata = {'git': git('.', '--version').decode().strip(), 'python': sys.version,
                'platform': platform.platform(), 'logical_cpus': os.cpu_count(),
                'cpu': subprocess.check_output(['sysctl', '-n', 'machdep.cpu.brand_string'], text=True).strip(),
                'cache_policy': 'one unmeasured warm-up per configuration; no cache flushing; OS cache uncontrolled thereafter',
                'repeats': args.repeats, 'order_seed': 20261118,
                'memory': '5ms sampled process-tree RSS (may miss short peaks; double-counts shared pages); time -l max process RSS, bytes on macOS',
                'cpu_time': 'RUSAGE_CHILDREN user+system delta, includes waited descendant processes',
                'bytes': 'blob_bytes: unique blob payloads returned to Python, not physical disk I/O; diff_input_bytes: logical pair payloads (repeats counted); native unknown',
                'source_sha256': {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ('src','bench') for p in Path(folder).glob('*.py')}}
    (OUT/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    rows = []
    with (OUT/'raw.jsonl').open('w') as raw:
        for workload in workloads:
            repo, revision, path = [workload[x] for x in ('repo','revision','path')]
            expected = [list(x) for x in blame(repo, revision, path)]
            (OUT/(workload['name']+'-oracle.json')).write_text(json.dumps(expected)+'\n')
            def command(mode, workers):
                if mode == 'native':
                    return ['git', '-c', 'core.attributesFile='+os.devnull, '-C', repo, 'blame', '--line-porcelain', revision, '--', path]
                return [sys.executable, '-m', 'bench.worker', repo, revision, path, '--mode', mode, '--workers', str(workers)]
            for mode, workers in configurations:
                output = subprocess.check_output(command(mode, workers), env=git_environment())
                actual = [list(x) for x in parse(output)] if mode=='native' else json.loads(output)['attribution']
                if actual != expected:
                    raise AssertionError(f'warmup mismatch {workload["name"]} {mode} {workers}')
            for repeat in range(args.repeats):
                order = configurations.copy()
                random.Random(20261118+repeat).shuffle(order)
                for mode, workers in order:
                    output, row = measure(command(mode, workers))
                    if mode == 'native':
                        actual = [list(x) for x in parse(output)]
                    else:
                        payload = json.loads(output)
                        actual = payload['attribution']
                        row.update(payload['stats'])
                    row.update(workload=workload['name'], configuration=mode if mode in ('native','sequential') else f'{mode}-{workers}',
                               repeat=repeat, correct=actual==expected,
                               output_sha256=hashlib.sha256(output).hexdigest())
                    raw.write(json.dumps(row)+'\n'); raw.flush()
                    rows.append(row)
                    if not row['correct']:
                        (OUT/'mismatch.json').write_text(json.dumps({'row': row,'actual': actual,'expected':expected}))
                        raise AssertionError('benchmark correctness failure')
                print(f'{workload["name"]}: repeat {repeat+1}/{args.repeats}', flush=True)
    summary = summarize(rows)
    (OUT/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    import csv
    with (OUT/'summary.csv').open('w') as file:
        writer = csv.DictWriter(file, fieldnames=list(summary[0])); writer.writeheader(); writer.writerows(summary)

if __name__ == '__main__':
    main()
