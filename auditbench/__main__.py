import argparse
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from .common import ROOT,config,read,write,digest
from .cases import build,public,evidence
from .checker import label
from .runner import run,freeze,validate


def verify_data(dataset):
    cases=dataset['cases'];ids=set();reordered=0
    for c in cases:
        if c['id'] in ids:raise ValueError('Duplicate case ID')
        ids.add(c['id'])
        if label(public(c),c['gold'])['status']!='correct':raise ValueError('Gold checker mismatch: '+c['id'])
        if label(public(c),c['corrupt'])['status']!='incorrect':raise ValueError('Mutation failed: '+c['id'])
        u=evidence(c,'original_order_evidence');s=evidence(c,'claim_organized_evidence')
        if sorted(u.splitlines())!=sorted(s.splitlines()):raise ValueError('Evidence mismatch')
        reordered+=u!=s
        if c['raw']:
            for model,data in c['raw'].items():
                y,p=data['labels'],data['predictions']
                for name,a,b in [('tn',0,0),('fp',0,1),('fn',1,0),('tp',1,1)]:
                    if sum(r[name] for r in c['records'] if r['field']==model)!=sum(yy==a and pp==b for yy,pp in zip(y,p)):raise ValueError('Raw prediction/count mismatch')
    return {'valid':True,'cases':len(cases),'reordered_cases':reordered,'unchanged_cases':len(cases)-reordered}

def preflight(cfg,dataset,out):
    import importlib.metadata
    import shutil
    from transformers import AutoTokenizer
    from .prompts import messages
    result={'python':platform.python_version(),'free_disk_bytes':shutil.disk_usage(ROOT).free,'data':verify_data(dataset),'tokenization':[],'packages':{}}
    for package in ['torch','transformers','accelerate','numpy','matplotlib']:
        try:result['packages'][package]=importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:result['packages'][package]=None
    for item in cfg['auditors']:
        tokenizer=AutoTokenizer.from_pretrained(item['model'],revision=item['revision']);maxlen=0;labels={}
        for c in dataset['cases']:
            for condition in cfg['conditions']:
                for report in [c['gold'],c['corrupt']]:
                    prompt=messages(public(c),report,condition)
                    ids=tokenizer.apply_chat_template(prompt,tokenize=True,add_generation_prompt=True,enable_thinking=False)
                    maxlen=max(maxlen,len(ids))
                    text=tokenizer.decode(ids,skip_special_tokens=False)
                    for answer in ['ERROR','OK']:
                        joined=tokenizer.encode(text+answer,add_special_tokens=False)
                        if joined[:len(ids)]!=ids:raise ValueError('Token boundary changed')
                        labels[answer]=joined[len(ids):]+[tokenizer.eos_token_id]
                    if len(ids)>cfg['inference']['max_input_tokens']:raise ValueError('Case exceeds context cap')
        result['tokenization'].append(dict(model=item['model'],revision=item['revision'],max_input_tokens=maxlen,label_tokens=labels))
    try:
        result['gpu']=subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.total,driver_version','--format=csv,noheader'],text=True).strip()
    except (OSError,subprocess.SubprocessError):result['gpu']=None
    write(out,result);return result

def main():
    parser=argparse.ArgumentParser(description='Evidence Before Escalation: prepare, run, validate, analyze')
    parser.add_argument('--config',default=str(ROOT/'configs/core.json'))
    sub=parser.add_subparsers(dest='command',required=True)
    a=sub.add_parser('build-cases');a.add_argument('--output',default=str(ROOT/'data/cases.json'))
    for name in ['verify-data','preflight','run','validate-run','freeze']:
        a=sub.add_parser(name);a.add_argument('--data',default=str(ROOT/'data/cases.json'))
        if name=='preflight':a.add_argument('--output',default=str(ROOT/'outputs/preflight.json'))
        if name in ['run','validate-run']:a.add_argument('--out',required=True)
        if name=='run':
            a.add_argument('--phase',choices=['smoke','development','test'],required=True);a.add_argument('--mode',choices=['real','fixture'],default='real');a.add_argument('--freeze');a.add_argument('--optional-8b',action='store_true')
        if name=='freeze':a.add_argument('--development-run',required=True);a.add_argument('--output',default=str(ROOT/'data/freeze.json'))
    a=sub.add_parser('analyze');a.add_argument('--out',required=True);a.add_argument('--quick-fixture',action='store_true')
    args=parser.parse_args();cfg=read(args.config)
    if args.command=='build-cases':
        payload=build(cfg,args.output);print(json.dumps(verify_data(payload)));return
    if args.command=='analyze':
        from .analysis import analyze
        # Validate against the run's frozen dataset/config before plotting.
        validate(cfg,read(ROOT/'data/cases.json'),args.out)
        print(analyze(cfg,args.out,args.quick_fixture));return
    dataset=read(args.data)
    if dataset['config_hash']!=digest(cfg):raise ValueError('Dataset/config mismatch: rebuild cases before running')
    if args.command=='verify-data':print(json.dumps(verify_data(dataset)))
    elif args.command=='preflight':print(json.dumps(preflight(cfg,dataset,args.output),indent=2))
    elif args.command=='validate-run':print(json.dumps(validate(cfg,dataset,args.out)))
    elif args.command=='freeze':freeze(cfg,dataset,args.development_run,args.output);print('Frozen:',args.output)
    else:
        import fcntl
        Path(args.out).mkdir(parents=True,exist_ok=True)
        with (Path(args.out)/'.lock').open('w') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            run(cfg,dataset,args.out,args.phase,args.mode,args.freeze,args.optional_8b)
        print(json.dumps(validate(cfg,dataset,args.out)))

if __name__=='__main__':main()
