"""Readable single-panel figure for the research result, from recorded summaries."""
import base64
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

root=Path('results/performance')
rows=json.loads((root/'summary.json').read_text())
names=list(dict.fromkeys(r['workload'] for r in rows))
fig,ax=plt.subplots(figsize=(7.2,4.8),constrained_layout=True)
for i,name in enumerate(names):
    native=next(r for r in rows if r['workload']==name and r['configuration']=='native')
    best=min((r for r in rows if r['workload']==name and r['configuration']!='native'),key=lambda r:r['median_seconds'])
    ax.barh(i-.17,native['median_seconds'],height=.28,color='#2676a8',label='Native Git' if i==0 else None)
    ax.barh(i+.17,best['median_seconds'],height=.28,color='#cf7832',label='Fastest custom configuration' if i==0 else None)
    for y,r in ((i-.17,native),(i+.17,best)):
        ax.text(r['median_seconds']+.03,y,f'{r["median_seconds"]:.3f} s',va='center',fontsize=10)
ax.set_yticks(range(len(names)),[n.replace('_',' ') for n in names],fontsize=11)
ax.invert_yaxis()
ax.set_xlabel('Median end-to-end wall time (seconds); lower is better',fontsize=11)
ax.set_title('Parallel blame prototype vs native Git',fontsize=14,pad=16)
ax.legend(loc='lower right',fontsize=10)
ax.set_xlim(0, max(r['median_seconds'] for r in rows)*1.15)
ax.grid(axis='x',alpha=.2); ax.set_axisbelow(True)
fig.savefig(root/'comparison.png',dpi=180)
fig.savefig(root/'comparison.svg')
encoded=base64.b64encode((root/'comparison.png').read_bytes()).decode()
html='<!doctype html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{margin:0;font-family:var(--font-sans);color:var(--foreground)}img{width:100%;height:450px;object-fit:contain}p{font-size:13px;color:var(--muted-foreground);margin:8px 0}</style></head><body><img alt="Native Git has lower median end-to-end latency than every custom configuration on all four measured workloads." src="data:image/png;base64,'+encoded+'"><p>10 runs per configuration · warmed caches · two zlib files and two generated controls · best custom selected after measurement</p></body></html>'
(root/'comparison.html').write_text(html)
