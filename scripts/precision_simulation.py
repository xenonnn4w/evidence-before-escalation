"""Illustrative interval-width check. Hypothetical scores, not model performance."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import numpy as np
from auditbench.analysis import queue,interval,cluster_indices
from auditbench.common import write

rng=np.random.default_rng(20261027)
reports=[dict(case_id=str(i),family=str(i%3),split='new_instance' if i<90 else 'held_out_variant') for i in range(150) for _ in range(2)]
y=np.tile([0.,1.],150);ties=np.arange(300);rows=[]
for shift in [0,.25,.5]:
    widths=[];effects=[]
    for trial in range(30):
        shared=rng.normal(size=300);u=shared+.5*y;s=shared+.5*y+shift*y+rng.normal(0,.3,size=300)
        effect=queue(y,s,.2,ties)['recall']-queue(y,u,.2,ties)['recall'];bs=[]
        for _ in range(200):
            idx=cluster_indices(reports,rng);bs.append(queue(y[idx],s[idx],.2,ties[idx])['recall']-queue(y[idx],u[idx],.2,ties[idx])['recall'])
        lo,hi,_=interval(bs);effects.append(effect);widths.append(hi-lo)
    rows.append(dict(hypothetical_score_shift=shift,median_observed_effect=float(np.median(effects)),median_95_interval_width=float(np.median(widths)),trials=30,bootstrap_per_trial=200))
write('outputs/precision_simulation.json',{'warning':'HYPOTHETICAL SCORES ONLY. Not model results or a power guarantee. Arbitrary score correlation/noise assumptions.','seed':20261027,'scenarios':rows})
print(rows)
