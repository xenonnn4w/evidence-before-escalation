"""Reproduce seven figures from persisted records. Never fabricates missing model data."""
import csv
import math
from pathlib import Path
import numpy as np
from .common import read,lines,write,digest

U='original_order_evidence';S='claim_organized_evidence';R='report_only'
COLORS={R:'#89939c',U:'#386cb0',S:'#e67e22'}

def queue(y,s,budget,ties,policy='risk'):
    y=np.asarray(y,dtype=float);s=np.asarray(s);k=int(math.floor(len(y)*budget))
    rankscore=1-np.abs(2*s-1) if policy=='uncertainty' else s
    order=np.lexsort((ties,-rankscore));selected=order[:k]
    e=float(y.sum());caught=float(y[selected].sum());n=len(y)
    return {'n':n,'errors':e,'k':k,'caught':caught,'recall':caught/e if e else float('nan'),
            'precision':caught/k if k else float('nan'),'missed_rate':(e-caught)/n if n else float('nan'),
            'false_escalation':(k-caught)/(n-e) if n>e else float('nan')}

def auroc(y,s):
    positives=np.asarray(s)[np.asarray(y)==1];negatives=np.asarray(s)[np.asarray(y)==0]
    if not len(positives) or not len(negatives):return float('nan')
    differences=positives[:,None]-negatives[None,:]
    return float(np.mean((differences>0)+.5*(differences==0)))

def interval(values):
    values=np.asarray(values);values=values[np.isfinite(values)]
    return (float(np.quantile(values,.025)),float(np.quantile(values,.975)),len(values)) if len(values) else (float('nan'),float('nan'),0)

def cluster_indices(reports,rng):
    strata={};members={}
    for i,r in enumerate(reports):
        members.setdefault(r['case_id'],[]).append(i)
        strata.setdefault((r['family'],r['split']),set()).add(r['case_id'])
    ids=[]
    for key in sorted(strata):
        clusters=sorted(strata[key])
        for c in rng.choice(clusters,len(clusters),replace=True):ids.extend(members[c])
    return np.array(ids,dtype=int)

def csvwrite(path,rows):
    if not rows:return
    with Path(path).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def analyze(cfg,out,quick=False):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    out=Path(out);manifest=read(out/'manifest.json')
    if manifest['phase']!='test':raise ValueError('Main figures require test partition; development results must not enter them')
    if quick and manifest['mode']!='fixture':raise ValueError('Reduced bootstrap counts allowed only for fixture verification')
    figdir=out/'analysis';figdir.mkdir(exist_ok=True)
    reports=read(out/'reports.json');rmap={r['id']:r for r in reports};scores=lines(out/'scores.jsonl')
    models=[x['model'] for x in manifest['models']];arms=['controlled','natural'];budgets=cfg['budgets']
    B=40 if quick else cfg['bootstrap_replicates'];draws=40 if quick else cfg['prevalence_sensitivity']['queue_draws']
    groups={};metrics=[];effects=[];allci={}
    for model in models:
        for arm in arms:
            rs=sorted([r for r in reports if r['arm']==arm and r['status']!='unassessable'],key=lambda r:r['id'])
            if not rs:continue
            lookup={(s['report_id'],s['condition']):s['p_error'] for s in scores if s['model']==model}
            y=np.array([r['status']=='incorrect' for r in rs],dtype=float)
            ties=np.array([int(digest(r['id'])[:12],16) for r in rs],dtype=np.int64)
            arrays={cond:np.array([lookup[r['id'],cond] for r in rs]) for cond in cfg['conditions']}
            groups[model,arm]=(rs,y,ties,arrays)
            boot={(cond,policy,b):[] for cond in cfg['conditions'] for policy in ['risk','uncertainty'] for b in budgets}
            paired=[];rng=np.random.default_rng(cfg['bootstrap_seed'])
            for _ in range(B):
                idx=cluster_indices(rs,rng)
                for key in boot:
                    cond,policy,b=key;boot[key].append(queue(y[idx],arrays[cond][idx],b,ties[idx],policy)['recall'])
                paired.append(boot[S,'risk',.2][-1]-boot[U,'risk',.2][-1])
            for (cond,policy,b),values in boot.items():
                m=queue(y,arrays[cond],b,ties,policy);lo,hi,valid=interval(values)
                metrics.append(dict(model=model,arm=arm,condition=cond,policy=policy,budget=b,**m,auroc=auroc(y,arrays[cond]),lo=lo,hi=hi,valid_bootstrap=valid))
                allci[model,arm,cond,policy,b]=(lo,hi)
            diff=queue(y,arrays[S],.2,ties)['recall']-queue(y,arrays[U],.2,ties)['recall'];lo,hi,valid=interval(paired)
            effects.append(dict(model=model,arm=arm,difference=diff,lo=lo,hi=hi,valid_bootstrap=valid,
                extra_errors=queue(y,arrays[S],.2,ties)['caught']-queue(y,arrays[U],.2,ties)['caught'],errors=y.sum(),n=len(y)))
    csvwrite(figdir/'metrics.csv',metrics);csvwrite(figdir/'paired_effects.csv',effects)
    outcome_counts=[]
    for family in cfg['families']:
        rr=[r for r in reports if r['family']==family and r['arm']=='natural']
        bad=sum(r['status']=='incorrect' for r in rr);unknown=sum(r['status']=='unassessable' for r in rr)
        outcome_counts.append(dict(family=family,n=len(rr),incorrect=bad,unassessable=unknown,operational_failures=bad+unknown,operational_failure_rate=(bad+unknown)/len(rr) if rr else float('nan')))
    csvwrite(figdir/'natural_operational_failures.csv',outcome_counts)
    csvwrite(figdir/'checker_coverage.csv',[dict(arm=arm,n=sum(r['arm']==arm for r in reports),assessed=sum(r['arm']==arm and r['status']!='unassessable' for r in reports),abstentions=sum(r['arm']==arm and r['status']=='unassessable' for r in reports)) for arm in arms])
    notice='SYNTHETIC FIXTURE — NOT MODEL RESULTS' if manifest['mode']=='fixture' else 'Held-out model experiment'
    plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':130})
    def save(fig,name,title,table):
        fig.suptitle(title+'\n'+notice,fontsize=12)
        fig.tight_layout(rect=[0,0,1,.92]);fig.savefig(figdir/(name+'.png'));fig.savefig(figdir/(name+'.pdf'));plt.close(fig)
        csvwrite(figdir/(name+'.csv'),table)
    # Figure 1: budget curves and random-policy spread, respecting model/arm separation.
    fig,axes=plt.subplots(len(models),2,figsize=(11,4*len(models)),squeeze=False);table=[]
    for i,model in enumerate(models):
        for j,arm in enumerate(arms):
            ax=axes[i,j];g=groups.get((model,arm));ax.set_title(model.split('/')[-1]+' / '+arm)
            if not g:ax.text(.2,.5,'No assessable reports');continue
            rs,y,ties,arrays=g
            for cond,policy in [(R,'risk'),(U,'risk'),(S,'risk'),(S,'uncertainty')]:
                mm=[next(m for m in metrics if (m['model'],m['arm'],m['condition'],m['policy'],m['budget'])==(model,arm,cond,policy,b)) for b in budgets]
                label={'report_only':'Report only','original_order_evidence':'Original','claim_organized_evidence':'Organized'}[cond]+(' uncertainty' if policy=='uncertainty' else '')
                ax.plot(budgets,[m['recall'] for m in mm],marker='o',color=COLORS[cond],linestyle='--' if policy=='uncertainty' else '-',label=label)
                ax.fill_between(budgets,[m['lo'] for m in mm],[m['hi'] for m in mm],color=COLORS[cond],alpha=.08);table.extend(mm)
            oracle=[queue(y,y,b,ties)['recall'] for b in budgets]
            ax.plot(budgets,oracle,':',color='black',label='Oracle / full-coverage checker')
            rng=np.random.default_rng(cfg['bootstrap_seed']);reps=40 if quick else cfg['random_rankings'];rv=[]
            for b in budgets:
                v=[queue(y,rng.random(len(y)),b,ties)['recall'] for _ in range(reps)]
                finite=[x for x in v if math.isfinite(x)];rv.append((np.mean(finite),np.quantile(finite,.05),np.quantile(finite,.95)) if finite else (np.nan,np.nan,np.nan))
            ax.plot(budgets,[v[0] for v in rv],':',color='gray',label='Random mean');ax.fill_between(budgets,[v[1] for v in rv],[v[2] for v in rv],color='gray',alpha=.15)
            for b,o,v in zip(budgets,oracle,rv):
                table.append(dict.fromkeys(metrics[0],'' )|{'model':model,'arm':arm,'condition':'reference','policy':'random','budget':b,'recall':v[0],'lo':v[1],'hi':v[2]})
                table.append(dict.fromkeys(metrics[0],'' )|{'model':model,'arm':arm,'condition':'reference','policy':'oracle','budget':b,'recall':o})
            ax.set(xlabel='Review fraction',ylabel='Error recall',ylim=(0,1));ax.legend(fontsize=7)
            if arm=='natural' and (y.sum()<20 or len(y)-y.sum()<20):ax.text(.01,.02,'Sparse classes: descriptive only',transform=ax.transAxes,color='darkred',fontsize=8)
    save(fig,'fig01_review_budget','Errors prioritized at a fixed review budget',table)
    # Figure 2: paired differences, not differences of independent intervals.
    fig,ax=plt.subplots(figsize=(9,5))
    for i,e in enumerate(effects):
        x=e['difference'];lo=e['lo'];hi=e['hi']
        ax.hlines(i,lo,hi,color='#386cb0');ax.plot(x,i,'o',color='#386cb0');ax.text(max(x,hi)+.01,i,f"{e['extra_errors']:+.0f} errors; N={e['n']}",fontsize=8)
    ax.set_yticks(range(len(effects)),[e['model'].split('/')[-1]+' / '+e['arm'] for e in effects]);ax.axvline(0,color='gray',linestyle=':');ax.set_xlabel('Organized minus original error recall, 20% review')
    save(fig,'fig02_organization_effect','Primary contrast: 4B controlled; other contrasts exploratory',effects)
    # Figure 3: within-stratum queues; bootstrap remains grouped.
    table=[];fig,axes=plt.subplots(1,len(models),figsize=(6*len(models),4),squeeze=False)
    for i,model in enumerate(models):
        ax=axes[0,i]
        for arm in arms:
            if (model,arm) not in groups:continue
            rs,y,ties,arrays=groups[model,arm]
            for cond in [U,S]:
                ys=[];los=[];his=[]
                for split in ['new_instance','held_out_variant']:
                    ix=np.array([k for k,r in enumerate(rs) if r['split']==split],dtype=int);sub=[rs[k] for k in ix]
                    val=queue(y[ix],arrays[cond][ix],.2,ties[ix]);rng=np.random.default_rng(cfg['bootstrap_seed']);bs=[]
                    for _ in range(B):
                        ind=ix[cluster_indices(sub,rng)];bs.append(queue(y[ind],arrays[cond][ind],.2,ties[ind])['recall'])
                    lo,hi,valid=interval(bs);ys.append(val['recall']);los.append(lo);his.append(hi)
                    table.append(dict(model=model,arm=arm,condition=cond,split=split,**val,lo=lo,hi=hi))
                ax.plot([0,1],ys,marker='o',color=COLORS[cond],linestyle='-' if arm=='controlled' else '--',label=arm+' '+('original' if cond==U else 'organized'));ax.fill_between([0,1],los,his,color=COLORS[cond],alpha=.08)
        ax.set_xticks([0,1],['New instances','Held-out variants']);ax.set(title=model.split('/')[-1],ylabel='Error recall at 20% review',ylim=(0,1));ax.legend(fontsize=7)
    save(fig,'fig03_variant_transfer','Transfer within task families (separate queues per stratum)',table)
    # Figure 4: global-queue misses, grouped by actual erroneous field.
    table=[];fig,axes=plt.subplots(1,2,figsize=(13,6))
    for j,arm in enumerate(arms):
        categories=sorted({r['family']+'/'+err for r in reports if r['arm']==arm and r['status']=='incorrect' for err in r['errors']})
        columns=[(m,c) for m in models for c in [U,S]];matrix=np.full((len(categories),len(columns)),np.nan)
        for col,(model,cond) in enumerate(columns):
            if (model,arm) not in groups:continue
            rs,y,ties,arrays=groups[model,arm];chosen=set(np.lexsort((ties,-arrays[cond]))[:int(len(rs)*.2)])
            for row,cat in enumerate(categories):
                idx=[k for k,r in enumerate(rs) if r['status']=='incorrect' and any(r['family']+'/'+e==cat for e in r['errors'])];miss=sum(k not in chosen for k in idx)
                matrix[row,col]=miss/len(idx) if idx else np.nan;table.append(dict(arm=arm,category=cat,model=model,condition=cond,missed=miss,total=len(idx),fraction=matrix[row,col]))
        ax=axes[j];ax.set_title(arm+' (multi-error rows may overlap)')
        if categories:
            ax.imshow(matrix,vmin=0,vmax=1,cmap='YlOrRd',aspect='auto');ax.set_yticks(range(len(categories)),[s.replace('evaluation_selection','selection').replace('evidence_sufficiency','evidence').replace('metric_reporting','metric') for s in categories],fontsize=7)
            for row in range(len(categories)):
                for col in range(len(columns)):
                    if np.isfinite(matrix[row,col]):ax.text(col,row,f'{matrix[row,col]:.0%}',ha='center',va='center',fontsize=7)
        else:ax.text(.2,.5,'No erroneous reports')
        ax.set_xticks(range(len(columns)),[m.split('/')[-1]+'\n'+('U' if c==U else 'S') for m,c in columns],fontsize=8)
    save(fig,'fig04_residual_errors','Errors missed by the global 20% review queue',table)
    # Figure 5: counts include malformed records, whereas queue metrics exclude them.
    table=[];fig,axes=plt.subplots(1,2,figsize=(12,4));families=cfg['families'];bottom=np.zeros(len(families))
    for status,color in [('correct','#4daf4a'),('incorrect','#e41a1c'),('unassessable','#999999')]:
        counts=[sum(r['arm']=='natural' and r['family']==f and r['status']==status for r in reports) for f in families]
        axes[0].bar(range(len(families)),counts,bottom=bottom,label=status,color=color);bottom+=counts
        for f,n in zip(families,counts):table.append(dict(kind='natural_count',family=f,status=status,value=n,model='',condition='',arm='natural',metric='count'))
    axes[0].set_xticks(range(3),['Metrics','Selection','Evidence']);axes[0].set_ylabel('Natural reports');axes[0].legend(fontsize=8)
    labels=[];precision=[];recall=[]
    for model in models:
        for arm in arms:
            if (model,arm) not in groups:continue
            rs,y,ties,arr=groups[model,arm]
            for cond in [U,S]:
                m=queue(y,arr[cond],.2,ties);labels.append(model.split('/')[-1]+'\n'+arm+' '+('U' if cond==U else 'S'));precision.append(m['precision']);recall.append(m['recall'])
                for metric in ['precision','recall']:table.append(dict(kind='queue_metric',family='',status='',value=m[metric],model=model,condition=cond,arm=arm,metric=metric))
    x=np.arange(len(labels));axes[1].bar(x-.18,precision,.36,label='Precision');axes[1].bar(x+.18,recall,.36,label='Recall');axes[1].set_xticks(x,labels,rotation=65,ha='right',fontsize=6);axes[1].set_ylim(0,1);axes[1].legend(fontsize=8)
    save(fig,'fig05_natural_controlled','Natural outcomes and 20% queues; controlled arm is designed 50:50',table)
    # Figure 6: prevalence simulation; a single variant per case in each draw.
    table=[];fig,axes=plt.subplots(1,2,figsize=(11,4));summary=[]
    for model in models:
        rs,y,ties,arrays=groups[model,'controlled'];clusters={}
        for i,r in enumerate(rs):clusters.setdefault(r['case_id'],{})[int(y[i])]=i
        strata={}
        for cid,v in clusters.items():r=rs[v[0]];strata.setdefault((r['family'],r['split']),[]).append(cid)
        for rate in cfg['prevalence_sensitivity']['nominal_error_rates']:
            rng=np.random.default_rng(cfg['prevalence_sensitivity']['seed']);vals={c:{'recall':[],'precision':[]} for c in [U,S]}
            for d in range(draws):
                ix=[]
                for key in sorted(strata):
                    ids=sorted(strata[key]);chosen=set(rng.choice(ids,int(round(len(ids)*rate)),replace=False))
                    ix.extend(clusters[c][int(c in chosen)] for c in ids)
                ix=np.array(ix);actual=y[ix].mean()
                for cond in [U,S]:
                    m=queue(y[ix],arrays[cond][ix],.2,ties[ix]);ref=queue(y[ix],y[ix],.2,ties[ix])
                    table.append(dict(model=model,condition=cond,nominal_prevalence=rate,actual_prevalence=actual,draw=d,precision=m['precision'],recall=m['recall'],oracle_recall=ref['recall'],random_expected_recall=m['k']/m['n']))
                    for metric in vals[cond]:vals[cond][metric].append(m[metric])
            for cond in vals:
                for metric,v in vals[cond].items():summary.append(dict(model=model,condition=cond,metric=metric,rate=rate,median=np.median(v),lo=np.quantile(v,.05),hi=np.quantile(v,.95)))
    for j,metric in enumerate(['precision','recall']):
        ax=axes[j]
        for i,model in enumerate(models):
            for cond in [U,S]:
                a=[s for s in summary if (s['model'],s['condition'],s['metric'])==(model,cond,metric)]
                ax.plot([s['rate'] for s in a],[s['median'] for s in a],marker='o',color=COLORS[cond],linestyle='-' if i==0 else '--',label=model.split('/')[-1]+' '+('U' if cond==U else 'S'));ax.fill_between([s['rate'] for s in a],[s['lo'] for s in a],[s['hi'] for s in a],color=COLORS[cond],alpha=.1)
        rates=cfg['prevalence_sensitivity']['nominal_error_rates']
        refs=[]
        for rate in rates:
            a=[r for r in table if r['model']==models[0] and r['condition']==U and r['nominal_prevalence']==rate]
            if metric=='recall':refs.append((np.median([r['random_expected_recall'] for r in a]),np.median([r['oracle_recall'] for r in a])))
            else:
                actual=np.median([r['actual_prevalence'] for r in a]);refs.append((actual,min(1,actual/.2)))
        ax.plot(rates,[x[0] for x in refs],':',color='gray',label='Random expectation')
        ax.plot(rates,[x[1] for x in refs],':',color='black',label='Oracle')
        ax.set(xlabel='Nominal error prevalence',ylabel=metric,ylim=(0,1));ax.legend(fontsize=7)
    save(fig,'fig06_prevalence_sensitivity','Conditional queue simulations; ranges are not new-sample confidence intervals',table)
    # Figure 7: do not plot made-up performance numbers for fixtures.
    table=[];fig,axes=plt.subplots(1,3,figsize=(12,4))
    if manifest['mode']=='fixture':
        for ax in axes:ax.axis('off');ax.text(.08,.5,'No GPU measurements\nFixture validation only',transform=ax.transAxes)
        table=[dict(model='fixture',condition='none',median_seconds='',p05_seconds='',p95_seconds='',peak_gib='',checker_median_seconds='')]
    else:
        labels=[];times=[];peaks=[];p05=[];p95=[]
        for model in models:
            for cond in cfg['conditions']:
                a=[s for s in scores if s['model']==model and s['condition']==cond];v=[s['seconds'] for s in a];peak=max(s['peak_vram_bytes'] for s in a)/2**30
                labels.append(model.split('/')[-1]+' '+{R:'R',U:'U',S:'S'}[cond]);times.append(np.median(v));peaks.append(peak);p05.append(np.quantile(v,.05));p95.append(np.quantile(v,.95))
                table.append(dict(model=model,condition=cond,median_seconds=times[-1],p05_seconds=p05[-1],p95_seconds=p95[-1],peak_gib=peak,checker_median_seconds=''))
        axes[0].bar(range(len(labels)),times);axes[0].errorbar(range(len(labels)),times,yerr=[np.array(times)-p05,np.array(p95)-times],fmt='none',color='black');axes[1].bar(range(len(labels)),peaks)
        for ax in axes[:2]:ax.set_xticks(range(len(labels)),labels,rotation=60,ha='right',fontsize=7)
        axes[0].set_ylabel('Audit seconds/report (median, 5–95%)');axes[1].set_ylabel('Peak allocated VRAM (GiB)')
        ct=np.median([r['checker_seconds'] for r in reports]);axes[2].bar(['CPU checker'],[ct*1000]);axes[2].set_ylabel('Milliseconds/report')
        table.append(dict(model='CPU checker',condition='artifacts',median_seconds='',p05_seconds='',p95_seconds='',peak_gib='',checker_median_seconds=ct))
    save(fig,'fig07_compute_cost','Measured audit cost (loading and generation excluded)',table)
    write(figdir/'analysis_manifest.json',{'mode':manifest['mode'],'run_signature':manifest['signature'],'bootstrap_replicates':B,'prevalence_draws':draws,'figures':7,'warning':notice})
    return {'figures':7,'directory':str(figdir),'mode':manifest['mode']}
