"""Seeded cases and synthetic reports; evidence never includes benchmark labels."""
import copy
import random
from .common import digest, write

VARIANTS = {
 'metric_reporting': ['accuracy','precision_recall','macro_f1'],
 'evaluation_selection': ['validation_winner','validation_search','test_threshold'],
 'evidence_sufficiency': ['all_runs','mean_improvement','subgroup_minimum'],
}

def metric(cm, name):
    tn, fp, fn, tp = cm
    div = lambda a,b: a/b if b else 0.0
    return {'accuracy':div(tp+tn,sum(cm)), 'precision':div(tp,tp+fp),
            'recall':div(tp,tp+fn), 'macro_f1':(div(2*tp,2*tp+fp+fn)+div(2*tn,2*tn+fp+fn))/2}[name]

def make_case(family, variant, seed, case_id, split):
    rng = random.Random(seed)
    records=[]
    def add(field, **value):
        records.append(dict(source=f'r{len(records):03}', field=field, **value))
    raw={}
    if family == 'metric_reporting':
        chosen_metric = rng.choice(['precision','recall']) if variant=='precision_recall' else variant
        cms={}
        # Both models evaluate the same labels; vary error patterns, not the target population.
        n=rng.choice([64,96,128]); positives=rng.randint(8,n-8)
        labels=[1]*positives+[0]*(n-positives); rng.shuffle(labels)
        for model in ['A','B']:
            predictions=[int(rng.random() < (rng.uniform(.55,.95) if y else rng.uniform(.05,.45))) for y in labels]
            tn=sum(y==0 and z==0 for y,z in zip(labels,predictions)); fp=sum(y==0 and z==1 for y,z in zip(labels,predictions))
            fn=sum(y==1 and z==0 for y,z in zip(labels,predictions)); tp=sum(y==1 and z==1 for y,z in zip(labels,predictions))
            cms[model]=[tn,fp,fn,tp]; raw[model]={'labels':labels,'predictions':predictions}
        # Chronological per-batch ledger, not an adversarial shuffle. Sum batch counts per model.
        for start in range(0,n,16):
            for model in ['A','B']:
                ys=labels[start:start+16]; ps=raw[model]['predictions'][start:start+16]
                counts=[sum(y==a and z==b for y,z in zip(ys,ps)) for a,b in [(0,0),(0,1),(1,0),(1,1)]]
                add(model, batch=start//16, tn=counts[0],fp=counts[1],fn=counts[2],tp=counts[3])
        vals={k:metric(v,chosen_metric) for k,v in cms.items()}
        winner='A' if vals['A']>vals['B']+1e-9 else 'B' if vals['B']>vals['A']+1e-9 else 'tie'
        gold={'score_A':round(vals['A'],4),'score_B':round(vals['B'],4),'winner':winner}
        formula={'accuracy':'(TP+TN)/(TP+TN+FP+FN)','precision':'TP/(TP+FP)','recall':'TP/(TP+FN)','macro_f1':'(2*TP/(2*TP+FP+FN) + 2*TN/(2*TN+FP+FN))/2'}[chosen_metric]
        contract=f'Sum all batch confusion counts per model. Report {chosen_metric}: {formula}. A zero denominator contributes 0. Winner is the larger unrounded metric, or tie if equal. Report scores in [0,1] rounded to four decimals.'
        spec={'metric':chosen_metric}
        corrupt=copy.deepcopy(gold)
        field=rng.choice(['score_A','score_B']); corrupt[field]=round(gold[field]+(-.15 if gold[field]>.5 else .15),4)
        subtype='incorrect_metric'
        order=['A','B']
    elif family == 'evaluation_selection':
        count=rng.randint(3,6); candidates=[f'C{i}' for i in range(count)]
        validation={x:round(rng.uniform(.55,.9),4) for x in candidates}
        test={x:round(rng.uniform(.55,.9),4) for x in candidates}
        split_used=rng.choice(['validation','test'])
        selected=max(candidates,key=lambda x:((validation if split_used=='validation' else test)[x],-int(x[1:])))
        for x in candidates:
            add('validation',candidate=x,score=validation[x])
            add('test',candidate=x,score=test[x])
            if variant=='validation_search':
                add('search',candidate=x,source_split='validation',action='inspect')
        add('selection',candidate=selected,source_split=split_used,kind='threshold' if variant=='test_threshold' else 'model')
        gold={'selected':selected,'policy_compliant':split_used=='validation'}
        corrupt=copy.deepcopy(gold); corrupt['policy_compliant']=not gold['policy_compliant']
        contract='Report the selected candidate and whether its selection event complies with policy. Selection must use validation scores only and choose the highest validation score (ties: lowest candidate ID). Inspecting test scores is allowed for final reporting, but using them for selection is prohibited. Report truthfully even when selection violates policy.'
        spec={}; subtype='misreported_selection_policy'; order=['selection','validation','search','test']
    else:
        required=list(range(1,rng.randint(4,7))); threshold=.02
        observed=[]
        missing=rng.choice(required) if rng.random()<.5 else None
        for run in required:
            add('required',run=run)
            if run==missing:continue
            delta=round(rng.uniform(-.04,.10),4)
            add('observed',run=run,group='g1',improvement=delta); observed.append(delta)
            if variant=='subgroup_minimum':
                add('observed',run=run,group='g2',improvement=round(rng.uniform(-.04,.10),4))
        complete=missing is None
        if variant=='all_runs': supported=complete
        elif variant=='mean_improvement':supported=complete and sum(observed)/len(observed)>=threshold
        else:
            bygroup={g:[x['improvement'] for x in records if x['field']=='observed' and x['group']==g] for g in ['g1','g2']}
            supported=complete and all(sum(v)/len(v)>=threshold for v in bygroup.values())
        gold={'complete':complete,'claim_supported':supported}; corrupt=copy.deepcopy(gold);corrupt['claim_supported']=not supported
        rule={'all_runs':'all required runs are present','mean_improvement':'all required runs are present AND mean improvement across required runs is at least 0.02','subgroup_minimum':'all required runs are present for both g1 and g2 AND each group has mean improvement at least 0.02'}[variant]
        contract='Report completeness and claim support. Completeness means every required run has all required group records. The claim is supported exactly when '+rule+'. Missing measurements never count as a successful run.'
        spec={'rule':variant,'threshold':threshold,'groups':['g1','g2'] if variant=='subgroup_minimum' else ['g1']}
        subtype='unsupported_claim';order=['required','observed']
    fields={k:('boolean' if type(v) is bool else 'number' if type(v) in (int,float) else 'string') for k,v in gold.items()}
    return {'id':case_id,'family':family,'variant':variant,'split':split,'seed':seed,'contract':contract,
            'spec':spec,'schema':fields,'records':records,'field_order':order,'raw':raw,
            'gold':gold,'corrupt':corrupt,'corruption_subtype':subtype}

def public(case):
    return {k:case[k] for k in ['contract','spec','schema','records','field_order']}

def evidence(case, condition):
    records=case['records']
    if condition=='claim_organized_evidence':
        order={key:i for i,key in enumerate(case['field_order'])}
        records=sorted(records,key=lambda x:(order[x['field']],x['source']))
    import json
    return '\n'.join(json.dumps(r,sort_keys=True,separators=(',',':')) for r in records)

def build(cfg, destination):
    cases=[]
    for fi,family in enumerate(cfg['families']):
        variants=VARIANTS[family]
        layout=[('development',cfg['development_per_family']),('new_instance',cfg['test_strata_per_family']['new_instance']),('held_out_variant',cfg['test_strata_per_family']['held_out_variant'])]
        i=0
        for split,n in layout:
            for j in range(n):
                variant=variants[2] if split=='held_out_variant' else variants[j%2]
                cases.append(make_case(family,variant,cfg['case_seed']+fi*10000+i,f'{fi}-{i:03}',split));i+=1
    payload={'config_hash':digest(cfg),'cases':cases}
    write(destination,payload)
    return payload
