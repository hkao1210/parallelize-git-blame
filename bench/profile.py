"""Run separately from benchmarks; native work counters + custom cProfile."""
import cProfile
import json
from pathlib import Path
import pstats
import re
from src.history import git
from src.schedulers import run

OUT = Path('results/performance')
workloads = json.loads((OUT/'workloads.json').read_text())
records = []
for w in workloads:
    raw = git(w['repo'], 'blame', '--line-porcelain', '--show-stats', w['revision'], '--', w['path'])
    counters = {}
    for line in raw.split(b'\n'):
        match = re.fullmatch(rb'(num (?:read blob|get patch|commits)): (\d+)', line)
        if match:
            counters[match[1].decode()] = int(match[2])
    records.append({'workload': w['name'], 'native_work_counters': counters,
                    'raw_tail': raw.split(b'\n')[-5:][0].decode(errors='replace')})
    profiler = cProfile.Profile()
    result, stats = profiler.runcall(run, w['repo'], w['revision'], w['path'], 'sequential')
    profiler.dump_stats(str(OUT/(w['name']+'.prof')))
    with (OUT/(w['name']+'-profile.txt')).open('w') as file:
        pstats.Stats(profiler, stream=file).strip_dirs().sort_stats('cumulative').print_stats(30)
    records[-1]['custom_stats_instrumented'] = stats
(OUT/'profiles.json').write_text(json.dumps(records,indent=2)+'\n')
