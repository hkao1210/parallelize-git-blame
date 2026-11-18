"""Derive conclusions and bootstrap intervals from raw measurements."""
import json
from pathlib import Path
import random
import statistics

ROOT = Path('results/performance')
rows = [json.loads(line) for line in (ROOT/'raw.jsonl').read_text().splitlines()]
summary = json.loads((ROOT/'summary.json').read_text())
workloads = list(dict.fromkeys(r['workload'] for r in rows))
rng = random.Random(811)

def interval(a,b):
    ratios = sorted(statistics.median(rng.choices(a,k=len(a)))/statistics.median(rng.choices(b,k=len(b))) for _ in range(5000))
    return [ratios[124], ratios[4874]]

scaling = []
for name in workloads:
    base = [r['edge_stage_seconds'] for r in rows if r['workload']==name and r['configuration']=='full-1']
    for workers in (1,2,4,8):
        vals = [r['edge_stage_seconds'] for r in rows if r['workload']==name and r['configuration']==f'full-{workers}']
        scaling.append({'workload':name, 'workers':workers,
                        'median_speedup':statistics.median(base)/statistics.median(vals),
                        'bootstrap_95_percent_interval': interval(base,vals) if workers!=1 else [1,1]})
best = []
for name in workloads:
    winner = min((r for r in summary if r['workload']==name and r['configuration']!='native'), key=lambda r:r['median_seconds'])
    best.append({'workload': name, 'configuration':winner['configuration'],
                 'speedup_vs_native':winner['speedup_vs_native']})
correct = all(r['correct'] for r in rows)
real_names = [w['name'] for w in json.loads((ROOT/'workloads.json').read_text()) if w['kind']=='real']
stage_signal = any(r['workload'] in real_names and r['workers']>1 and r['bootstrap_95_percent_interval'][0]>1 for r in scaling)
e2e_signal = any(r['workload'] in real_names and r['speedup_vs_native']>=1.2 for r in best)
decision = {'measured_runs':len(rows), 'all_correct':correct, 'stage_scaling_real_signal':stage_signal,
            'real_end_to_end_at_least_1_2x':e2e_signal, 'decision':'GO' if correct and stage_signal and e2e_signal else 'PIVOT',
            'edge_scaling':scaling, 'best_custom_by_workload':best,
            'bootstrap_note':'5000 independent resamples of 10 measurements; descriptive, no multiple-comparison correction'}
(ROOT/'decision.json').write_text(json.dumps(decision,indent=2)+'\n')
lines = ['# Performance verification and architecture decision', '', '**'+decision['decision']+' for the current implementation.**', '',
         f'All {len(rows)} measured runs matched the native oracle. Ten measurements per configuration/workload; warmed caches only.', '',
         '| Workload | Native median (s) | Best custom | Custom median (s) | Native/custom |',
         '|---|---:|---|---:|---:|']
for bestrow in best:
    name=bestrow['workload']
    native=next(r for r in summary if r['workload']==name and r['configuration']=='native')
    custom=next(r for r in summary if r['workload']==name and r['configuration']==bestrow['configuration'])
    lines.append(f'| {name} | {native["median_seconds"]:.4f} | {custom["configuration"]} | {custom["median_seconds"]:.4f} | {custom["speedup_vs_native"]:.3f}x |')
lines += ['', 'A ratio below 1 means the prototype is slower. Best-of-configurations is descriptive, not an unbiased estimate of future performance.', '',
          '| Workload | 8-worker edge-stage speedup | Bootstrap 95% interval |', '|---|---:|---:|']
for r in scaling:
    if r['workers']==8:
        lo,hi=r['bootstrap_95_percent_interval']
        lines.append(f'| {r["workload"]} | {r["median_speedup"]:.2f}x | {lo:.2f}–{hi:.2f} |')
lines += ['', '## Gates and hypotheses', '',
          '- Gate A: scoped empirical correctness passed; see regression logs and raw comparisons.',
          f'- Gate B / H1: real-workload edge-stage scaling signal: **{stage_signal}**. This stage includes Git process startup, object reopening, hunk extraction, dense mapping, and dispatch; it is not an isolated xdiff CPU benchmark.',
          '- H2: dense summaries remain correct on tested inputs. See composition times and memory in summary.csv. Compact intervals and CPU-parallel composition remain unimplemented; algorithmic novelty/efficiency is not established.',
          f'- Gate C / H3: real-workload end-to-end ≥1.2x signal: **{e2e_signal}**. No general performance advantage can be inferred from stage speedup.', '',
          '## Interpretation and next decision', '',
          'The prototype validates the scheduling experiment, not a production speedup. Eager history validation and object loading remain serial; spawning Git separately for tree reads, blob reads and diffs incurs overhead. Windows only save diff work. Native Git already avoids irrelevant history and emits richer output than this prototype.', '',
          'Pivot away from claiming that a Python subprocess scan is a faster blame replacement. A further bounded experiment should first batch object access/history validation and use a native in-process diff interface, then rerun the same benchmarks. This is a proposed follow-up, not an implemented or measured speedup. Do not add merges or complex attribution options before obtaining a real end-to-end signal.', '',
          'The broad parallel-blame idea has documented prior art (2019). Novelty of the narrow speculative-summary combination remains unestablished; see novelty-review.md. A negative-results systems study is currently more defensible than a new-algorithm claim.', '',
          'Coverage is two files from one historical real repository plus two generated controls, one machine, no controlled cold cache. This is not the requested eventual 3–5-large-repository study, and cannot rule out wins on other workloads. Bootstrap intervals are descriptive and uncorrected for multiple comparisons.', '',
          'Raw data and reproducibility metadata: results/performance/raw.jsonl, summary.csv, metadata.json, workloads.json. Charts: performance.png and wall-times.png. Method: docs/benchmark-method.md.', '']
Path('docs/day3_decision.md').write_text('\n'.join(lines))
print(json.dumps({k:v for k,v in decision.items() if k not in ('edge_scaling',)},indent=2))
