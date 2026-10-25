"""Post-hoc diagnostic figures from saved test scores; no new model inference.

Run from the repository root: python analysis/supplementary.py
U/S queue membership reproduces the primary analysis's hash tie-breaking.
These descriptive diagnostics were added after inspection of the primary result.
"""
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'results/test'
OUT=RUN/'analysis'
reports=json.loads((RUN/'reports.json').read_text())
scores=[json.loads(line) for line in (RUN/'scores.jsonl').read_text().splitlines()]
models=['Qwen/Qwen3-1.7B','Qwen/Qwen3-4B']
conditions=['original_order_evidence','claim_organized_evidence']
colors=['#386cb0','#e67e22']
families=['metric_reporting','evaluation_selection','evidence_sufficiency']
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':150})

def tie(report):
 return int(hashlib.sha256(json.dumps(report['id'],sort_keys=True,allow_nan=False).encode()).hexdigest()[:12],16)

def group(model,arm):
 rs=sorted([r for r in reports if r['arm']==arm and r['status']!='unassessable'],key=lambda r:r['id'])
 lookup={(s['report_id'],s['condition']):s['p_error'] for s in scores if s['model']==model}
 queues={c:{r['id'] for r in sorted(rs,key=lambda r:(-lookup[r['id'],c],tie(r)))[:int(.2*len(rs))]} for c in conditions}
 return rs,lookup,queues

def save(fig,name,rows):
 fig.tight_layout()
 for ext in ['png','pdf']:fig.savefig(OUT/f'{name}.{ext}',bbox_inches='tight')
 plt.close(fig)
 with (OUT/f'{name}.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

# Family counts use the pooled 20% queue, not newly allocated per-family queues.
fig,axes=plt.subplots(2,2,figsize=(11,7),sharey=True);rows=[]
for i,model in enumerate(models):
 for j,arm in enumerate(['controlled','natural']):
  ax=axes[i,j];rs,lookup,q=group(model,arm)
  for ci,c in enumerate(conditions):
   vals=[]
   for fi,family in enumerate(families):
    errors=[r for r in rs if r['family']==family and r['status']=='incorrect'];caught=sum(r['id'] in q[c] for r in errors)
    value=caught/len(errors);vals.append(value)
    rows.append(dict(model=model,arm=arm,condition=c,family=family,errors=len(errors),selected_errors=caught,recall=value,queue_size=int(.2*len(rs))))
    ax.text(fi+(ci-.5)*.34,value+.025,f'{caught}/{len(errors)}',ha='center',fontsize=8)
   ax.bar(np.arange(3)+(ci-.5)*.34,vals,width=.32,color=colors[ci],label=['Original','Organized'][ci])
  ax.set(title=f'{model.split("/")[-1]} · {arm}',xticks=range(3),xticklabels=['Metrics','Selection','Evidence'],ylim=(0,1.08),ylabel='Fraction of family errors selected')
axes[0,0].legend(frameon=False)
fig.suptitle('Where the global review queue spends its capacity',y=1.02)
save(fig,'fig08_family_prioritization',rows)

# Queue churn separates retained versus gained/lost erroneous reports.
fig,axes=plt.subplots(1,2,figsize=(11,4.2));rows=[]
for ax,arm in zip(axes,['controlled','natural']):
 for mi,model in enumerate(models):
  rs,lookup,q=group(model,arm);u,s=[q[c] for c in conditions]
  err={r['id'] for r in rs if r['status']=='incorrect'}
  groups=[('Both queues',u&s),('Original only',u-s),('Organized only',s-u)]
  for gi,(name,ids) in enumerate(groups):
   x=mi*4+gi;bad=len(ids&err);good=len(ids-err)
   ax.bar(x,bad,color='#386cb0',label='Erroneous' if mi==gi==0 else None)
   ax.bar(x,good,bottom=bad,color='#b5bdc6',label='Correct' if mi==gi==0 else None)
   ax.text(x,len(ids)+.6,str(len(ids)),ha='center',fontsize=9)
   rows.append(dict(model=model,arm=arm,membership=name,reports=len(ids),errors=bad,correct=good))
 ax.set(title=arm.capitalize(),ylabel='Reports',xticks=[0,1,2,4,5,6],xticklabels=['Both','U only','S only']*2)
 ax.text(1,-.22,'Qwen3-1.7B',transform=ax.get_xaxis_transform(),ha='center')
 ax.text(5,-.22,'Qwen3-4B',transform=ax.get_xaxis_transform(),ha='center')
 ax.set_ylim(0,65 if arm=='controlled' else 35)
axes[0].legend(frameon=False);fig.suptitle('Same queue budget, different reports',y=1.03)
save(fig,'fig09_queue_overlap',rows)

# ROC thresholds operate on unique scores so ties receive a single threshold step.
fig,axes=plt.subplots(2,2,figsize=(10,7),sharex=True,sharey=True);rows=[]
for i,model in enumerate(models):
 for j,arm in enumerate(['controlled','natural']):
  ax=axes[i,j];rs,lookup,q=group(model,arm);y=np.array([r['status']=='incorrect' for r in rs]);P=int(y.sum());N=len(y)-P
  for ci,c in enumerate(conditions):
   values=np.array([lookup[r['id'],c] for r in rs]);order=np.argsort(-values,kind='stable');v=values[order];labels=y[order]
   ends=np.r_[np.where(v[1:]!=v[:-1])[0],len(v)-1];tp=np.r_[0,np.cumsum(labels)[ends]];fp=np.r_[0,np.cumsum(~labels)[ends]];tpr=tp/P;fpr=fp/N
   # Pairwise definition of AUROC matches the primary analyzer and handles ties.
   diff=values[y][:,None]-values[~y][None,:];auc=float(np.mean((diff>0)+.5*(diff==0)))
   ax.plot(fpr,tpr,color=colors[ci],label=f'{["Original","Organized"][ci]} · AUC {auc:.3f}')
   for x,z in zip(fpr,tpr):rows.append(dict(model=model,arm=arm,condition=c,false_positive_rate=float(x),true_positive_rate=float(z),auroc=auc,errors=P,correct=N))
  ax.plot([0,1],[0,1],':',color='#999');ax.set(title=f'{model.split("/")[-1]} · {arm}',xlabel='False-positive rate',ylabel='True-positive rate');ax.legend(frameon=False,fontsize=9,loc='lower right')
fig.suptitle('Whole-ranking discrimination differs from top-budget recall',y=1.02)
save(fig,'fig10_score_discrimination',rows)
print(json.dumps({'supplementary_figures':3,'directory':str(OUT),'status':'post-hoc descriptive; no new inference'}))
