"""Generate publication-friendly figures from recorded summaries only."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path('results/performance')
rows = json.loads((ROOT/'summary.json').read_text())
workloads = list(dict.fromkeys(x['workload'] for x in rows))
fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), constrained_layout=True)
markers = ['o', 's', '^', 'D']
for name, marker in zip(workloads, markers):
    data = {x['configuration']: x for x in rows if x['workload']==name}
    x = [1,2,4,8]
    base = data['full-1']['median_edge_stage_seconds']
    axes[0].plot(x, [base/data[f'full-{w}']['median_edge_stage_seconds'] for w in x], marker=marker, label=name)
    for mode, style in [('full','-'), ('windowed','--')]:
        axes[1].plot(x, [data[f'{mode}-{w}']['speedup_vs_native'] for w in x], style, marker=marker, label=f'{name} {mode}')
axes[0].set_title('Adjacent-edge stage scaling (includes scheduling)')
axes[0].set_ylabel('Speedup relative to full-1 edge stage')
axes[1].set_title('End-to-end speedup versus native Git')
axes[1].set_ylabel('Native median / prototype median (higher is better)')
axes[1].set_yscale('log')
for ax in axes:
    ax.set_xticks([1,2,4,8]); ax.set_xlabel('Bounded Git workers')
    ax.axhline(1, color='gray', linewidth=1, linestyle=':')
    ax.grid(alpha=.2); ax.legend(fontsize=7)
fig.savefig(ROOT/'performance.png', dpi=180)
fig.savefig(ROOT/'performance.svg')

fig, axes = plt.subplots(1,len(workloads), figsize=(13,4), constrained_layout=True)
for name, ax in zip(workloads, axes):
    data = {x['configuration']: x for x in rows if x['workload']==name}
    labels = ['native','sequential','full-8','windowed-8']
    vals = [data[k]['median_seconds'] for k in labels]
    bars = ax.bar(labels, vals)
    for bar,value in zip(bars,vals):
        ax.text(bar.get_x()+bar.get_width()/2,value, f'{value:.3f}',ha='center',va='bottom',fontsize=8)
    ax.set_title(name); ax.set_ylabel('Median wall time (seconds)')
    ax.tick_params(axis='x',rotation=35); ax.margins(y=.2)
fig.savefig(ROOT/'wall-times.png', dpi=180)
fig.savefig(ROOT/'wall-times.svg')
