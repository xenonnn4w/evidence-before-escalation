"""Independent artifact-derived checker. Does not access benchmark gold/corrupt fields."""
import math

def expected(case):
    r=case['records']; spec=case['spec']
    if 'metric' in spec:
        scores={}
        for model in ['A','B']:
            totals={k:sum(x[k] for x in r if x['field']==model) for k in ['tn','fp','fn','tp']}
            tn,fp,fn,tp=[totals[k] for k in ['tn','fp','fn','tp']]
            def ratio(a,b):return a/b if b else 0
            name=spec['metric']
            if name=='accuracy':v=ratio(tn+tp,tn+fp+fn+tp)
            elif name=='precision':v=ratio(tp,tp+fp)
            elif name=='recall':v=ratio(tp,tp+fn)
            elif name=='macro_f1':v=.5*(ratio(2*tp,2*tp+fp+fn)+ratio(2*tn,2*tn+fp+fn))
            else:raise ValueError(name)
            scores[model]=v
        return {'score_A':round(scores['A'],4),'score_B':round(scores['B'],4),'winner':'tie' if abs(scores['A']-scores['B'])<=1e-9 else max(scores,key=scores.get)}
    if 'rule' in spec:
        required={x['run'] for x in r if x['field']=='required'}
        observed={(x['run'],x['group']):x['improvement'] for x in r if x['field']=='observed'}
        complete=all((i,g) in observed for i in required for g in spec['groups'])
        supported=complete
        if spec['rule']!='all_runs':
            supported=complete and all(sum(observed[(i,g)] for i in required)/len(required)>=spec['threshold'] for g in spec['groups'])
        return {'complete':complete,'claim_supported':supported}
    choices=[x for x in r if x['field']=='selection']
    if len(choices)!=1:raise ValueError('Ambiguous selection log')
    choice=choices[0]
    validation={x['candidate']:x['score'] for x in r if x['field']=='validation'}
    best=sorted(validation,key=lambda k:(-validation[k],int(k[1:])))[0]
    return {'selected':choice['candidate'],'policy_compliant':choice['source_split']=='validation' and choice['candidate']==best}

def label(case, report):
    schema=case['schema']
    if not isinstance(report,dict) or set(report)!=set(schema):return {'status':'unassessable','errors':['schema']}
    for key,kind in schema.items():
        v=report[key]
        if kind=='boolean' and type(v) is not bool:return {'status':'unassessable','errors':['schema']}
        if kind=='string' and type(v) is not str:return {'status':'unassessable','errors':['schema']}
        if kind=='number' and (type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=1):return {'status':'unassessable','errors':['schema']}
    truth=expected(case)
    errors=[k for k,v in truth.items() if (abs(report[k]-v)>.005 if type(v) is float else report[k]!=v)]
    return {'status':'incorrect' if errors else 'correct','errors':errors}
