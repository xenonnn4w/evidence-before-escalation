import gc
import json
import math
import platform
import random
import time
from pathlib import Path
from .common import ROOT,append,read,write,digest,code_hash,lines
from .cases import public
from .checker import label
from .prompts import messages
from .inference import HFModel,normalized_error


def parse_report(raw):
    """Reject non-standard JSON and duplicate keys rather than repairing model output."""
    def bad_constant(value):raise ValueError('Non-standard JSON number: '+value)
    def unique_pairs(pairs):
        result={}
        for key,value in pairs:
            if key in result:raise ValueError('Duplicate report field: '+key)
            result[key]=value
        return result
    try:return json.loads(raw,parse_constant=bad_constant,object_pairs_hook=unique_pairs)
    except (ValueError,TypeError):return None

CONDITIONS=['report_only','original_order_evidence','claim_organized_evidence']

def selected(dataset, phase):
    cases=dataset['cases']
    if phase=='smoke':return [next(c for c in cases if c['split']=='development' and c['family']==f) for f in sorted({c['family'] for c in cases})]
    return [c for c in cases if (c['split']=='development')==(phase=='development')]

def signature(cfg,dataset):return {'code_hash':code_hash(),'config_hash':digest(cfg),'dataset_hash':digest(dataset)}

def freeze(cfg,dataset,devrun,destination):
    manifest=read(Path(devrun)/'manifest.json')
    if manifest['mode']!='real' or manifest['phase']!='development':raise ValueError('Freeze requires a completed REAL development run')
    if manifest['signature']!=signature(cfg,dataset):raise ValueError('Development run is stale; repeat after changes')
    validate(cfg,dataset,devrun)
    write(destination,{'signature':signature(cfg,dataset),'development_run':str(Path(devrun).resolve()),'created_unix':time.time()})

def run(cfg,dataset,out,phase,mode,freeze_path=None,optional=False):
    out=Path(out);sig=signature(cfg,dataset)
    if mode=='real' and phase=='test':
        if not freeze_path or read(freeze_path)['signature']!=sig:raise ValueError('A matching development freeze is required before test inference')
    if optional and phase=='smoke':raise ValueError('Optional extension applies after core development/test, not the smoke run')
    manifest={'signature':sig,'mode':mode,'phase':phase,'optional':optional,'models':(cfg['auditors'][:1] if phase=='smoke' else cfg['auditors'])+([cfg['optional_auditor']] if optional else [])}
    out.mkdir(parents=True,exist_ok=True)
    if (out/'manifest.json').exists():
        old=read(out/'manifest.json')
        if any(old[k]!=v for k,v in manifest.items()):
            extension=(optional and old['optional'] is False and all(old[k]==manifest[k] for k in ['signature','mode','phase']) and old['models']==cfg['auditors'])
            if not extension:raise ValueError('Incompatible existing run directory; use a new directory')
            validate(cfg,dataset,out)
            old.update(manifest);old['optional_extension_started_unix']=time.time()
            write(out/'manifest.json',old)
    else:
        hardware={}
        if mode=='real':
            import torch, importlib.metadata, subprocess
            if not torch.cuda.is_available():raise RuntimeError('CUDA required for real runs')
            hardware={'gpu':torch.cuda.get_device_name(0),'vram_bytes':torch.cuda.get_device_properties(0).total_memory,'cuda':torch.version.cuda,'torch':torch.__version__,'transformers':importlib.metadata.version('transformers'),'cpu':platform.processor(),'system':platform.platform(),'batch_size':1,'dtype':'bfloat16'}
            hardware['driver']=subprocess.check_output(['nvidia-smi','--query-gpu=driver_version','--format=csv,noheader'],text=True).strip()
        write(out/'manifest.json',dict(manifest,hardware=hardware,created_unix=time.time(),python=platform.python_version(),fixture_notice='SYNTHETIC SOFTWARE TEST DATA — NOT EXPERIMENTAL RESULTS' if mode=='fixture' else None))
    cases=selected(dataset,phase)
    generated=lines(out/'generation.jsonl');byid={x['case_id']:x for x in generated}
    if len(byid)!=len(generated):raise ValueError('Duplicate generation IDs')
    model=None
    try:
        for c in cases:
            if c['id'] in byid:continue
            prompt=messages(public(c));seed=cfg['generator']['seed']+int(digest(c['id'])[:8],16)%1000000
            if mode=='fixture':
                rng=random.Random(seed)
                fake=c['gold'] if rng.random()>.3 else c['corrupt']
                raw=json.dumps(fake) if rng.random()>.05 else 'malformed fixture'
                record={'raw':raw,'seconds':0.0,'input_tokens':0,'output_tokens':0,'peak_vram_bytes':0,'truncated':False}
            else:
                if model is None:
                    model=HFModel(cfg['generator']['model'],cfg['generator']['revision'],cfg['inference']['max_input_tokens'])
                    append(out/'performance.jsonl',{'event':'model_load','model':cfg['generator']['model'],'seconds':model.load_seconds})
                record=model.generate(prompt,cfg['generator'],seed)
            record.update(case_id=c['id'],seed=seed,prompt=prompt,prompt_hash=digest(prompt),mode=mode)
            append(out/'generation.jsonl',record);byid[c['id']]=record
    except Exception as e:
        append(out/'errors.jsonl',{'stage':'generation','error':repr(e),'time':time.time()});raise
    finally:
        del model;gc.collect()
        if mode=='real':
            import torch
            torch.cuda.empty_cache()
    reports=[]
    for c in cases:
        g=byid[c['id']]
        natural=parse_report(g['raw']) if not g['truncated'] else None
        if label(public(c),natural)['status']=='unassessable':natural=None
        for arm,report in [('natural',natural),('canonical_correct',c['gold']),('controlled_incorrect',c['corrupt'])]:
            start=time.perf_counter();verdict=label(public(c),report);duration=time.perf_counter()-start
            reports.append({'id':c['id']+':'+arm,'case_id':c['id'],'family':c['family'],'variant':c['variant'],'split':c['split'],'arm':'natural' if arm=='natural' else 'controlled','report_kind':arm,'report':report,**verdict,'checker_seconds':duration,'mode':mode})
    if (out/'reports.json').exists():
        previous=read(out/'reports.json')
        strip_time=lambda rs:[{k:v for k,v in r.items() if k!='checker_seconds'} for r in rs]
        if strip_time(previous)!=strip_time(reports):raise ValueError('Persisted reports differ from generation/artifacts')
        reports=previous
    else:write(out/'reports.json',reports)
    scores=lines(out/'scores.jsonl');keys={x['key'] for x in scores}
    if len(keys)!=len(scores):raise ValueError('Duplicate audit keys')
    cmap={c['id']:c for c in cases}
    for item in manifest['models']:
        model=None
        try:
            for r in reports:
                if r['status']=='unassessable':continue
                for condition in cfg['conditions']:
                    key=digest([r['id'],item,condition,sig])
                    if key in keys:continue
                    prompt=messages(public(cmap[r['case_id']]),r['report'],condition)
                    if mode=='fixture':
                        rng=random.Random(int(key[:16],16));p=rng.uniform(.01,.99)
                        record={'p_error':p,'log_likelihoods':{'ERROR':math.log(p),'OK':math.log(1-p)},'label_token_ids':{},'seconds':0.0,'input_tokens':0,'peak_vram_bytes':0}
                    else:
                        if model is None:
                            model=HFModel(item['model'],item['revision'],cfg['inference']['max_input_tokens'])
                            append(out/'performance.jsonl',{'event':'model_load','model':item['model'],'seconds':model.load_seconds})
                        record=model.score(prompt)
                    record.update(key=key,report_id=r['id'],case_id=r['case_id'],model=item['model'],revision=item['revision'],condition=condition,prompt=prompt,prompt_hash=digest(prompt),mode=mode)
                    append(out/'scores.jsonl',record);keys.add(key)
        except Exception as e:
            append(out/'errors.jsonl',{'stage':'audit','model':item,'error':repr(e),'time':time.time()});raise
        finally:
            del model;gc.collect()
            if mode=='real':
                import torch
                torch.cuda.empty_cache()
    write(out/'validation.json',validate(cfg,dataset,out))

def validate(cfg,dataset,out):
    out=Path(out);m=read(out/'manifest.json')
    if m['signature']!=signature(cfg,dataset):raise ValueError('Run fingerprints do not match current sources/config/dataset')
    cases=selected(dataset,m['phase']);cmap={c['id']:c for c in cases};reports=read(out/'reports.json');scores=lines(out/'scores.jsonl');gen=lines(out/'generation.jsonl')
    if len(gen)!=len(cases) or {g['case_id'] for g in gen}!=set(cmap):raise ValueError('Incomplete generation')
    expected_reports={c['id']+':'+kind for c in cases for kind in cfg['reports_per_case']}
    if len(reports)!=len(expected_reports) or {r['id'] for r in reports}!=expected_reports:raise ValueError('Incomplete/duplicate reports')
    genmap={g['case_id']:g for g in gen}
    for g in gen:
        wanted=messages(public(cmap[g['case_id']]))
        if g['mode']!=m['mode'] or g['prompt']!=wanted or g['prompt_hash']!=digest(wanted):raise ValueError('Generation provenance mismatch')
    for r in reports:
        c=cmap[r['case_id']]
        if r['family']!=c['family'] or r['variant']!=c['variant'] or r['split']!=c['split'] or r['mode']!=m['mode']:raise ValueError('Report metadata mismatch')
        kind=r['report_kind']
        if kind=='natural':
            g=genmap[r['case_id']];wanted=parse_report(g['raw']) if not g['truncated'] else None
            if label(public(c),wanted)['status']=='unassessable':wanted=None
        else:wanted=c['gold'] if kind=='canonical_correct' else c['corrupt']
        if wanted!=r['report'] or r['id']!=r['case_id']+':'+kind:raise ValueError('Report/generation mismatch')
        actual=label(public(cmap[r['case_id']]),r['report'])
        if actual['status']!=r['status'] or actual['errors']!=r['errors']:raise ValueError('Report labels changed')
        if r['report_kind']=='canonical_correct' and r['status']!='correct':raise ValueError('Broken positive control')
        if r['report_kind']=='controlled_incorrect' and r['status']!='incorrect':raise ValueError('Broken corruption')
    expected={(r['id'],model['model'],cond) for r in reports if r['status']!='unassessable' for model in m['models'] for cond in cfg['conditions']}
    actual={(s['report_id'],s['model'],s['condition']) for s in scores}
    if len(scores)!=len(actual) or actual!=expected:raise ValueError(f'Incomplete/duplicate scores: {len(scores)} vs {len(expected)}')
    if any(s['mode']!=m['mode'] or not math.isfinite(s['p_error']) or not 0<=s['p_error']<=1 or s['prompt_hash']!=digest(s['prompt']) for s in scores):raise ValueError('Invalid score or provenance')
    rmap={r['id']:r for r in reports};modelmap={i['model']:i for i in m['models']}
    for score in scores:
        report=rmap[score['report_id']];item=modelmap[score['model']]
        wanted=messages(public(cmap[report['case_id']]),report['report'],score['condition'])
        if score['prompt']!=wanted or score['revision']!=item['revision'] or score['case_id']!=report['case_id']:raise ValueError('Audit prompt/model provenance mismatch')
        if score['key']!=digest([report['id'],item,score['condition'],m['signature']]):raise ValueError('Audit key mismatch')
        logs=score['log_likelihoods']
        if not all(math.isfinite(v) for v in logs.values()) or abs(normalized_error(logs['ERROR'],logs['OK'])-score['p_error'])>1e-8:raise ValueError('Score/likelihood mismatch')
    return {'valid':True,'mode':m['mode'],'cases':len(cases),'reports':len(reports),'scores':len(scores),'unassessable':sum(r['status']=='unassessable' for r in reports)}
