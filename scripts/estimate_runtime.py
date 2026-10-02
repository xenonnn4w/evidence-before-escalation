"""Forecast remaining test inference from actual development timings, never fixtures."""
import json
import statistics
import sys
from pathlib import Path
root=Path(sys.argv[1])
m=json.loads((root/'manifest.json').read_text())
if m['mode']!='real':raise SystemExit('Refusing to estimate GPU runtime from synthetic fixtures.')
def rows(name):return [json.loads(x) for x in (root/name).read_text().splitlines() if x]
g=rows('generation.jsonl');scores=rows('scores.jsonl');loads=rows('performance.jsonl')
forecast={'generation_seconds_for_150_test_cases':150*statistics.mean(x['seconds'] for x in g),'audit_seconds_by_model':{},'basis_run':str(root),'warning':'Inference-only extrapolation; downloads, export, retries and provider billing are additional.'}
for model in ['Qwen/Qwen3-1.7B','Qwen/Qwen3-4B']:
    subset=[r for r in scores if r['model']==model]
    if not subset:forecast['audit_seconds_by_model'][model]=None;continue
    conditions={r['condition'] for r in subset}
    forecast['audit_seconds_by_model'][model]=sum(450*statistics.mean(r['seconds'] for r in subset if r['condition']==c) for c in conditions)
if all(v is not None for v in forecast['audit_seconds_by_model'].values()):
    seconds=forecast['generation_seconds_for_150_test_cases']+sum(forecast['audit_seconds_by_model'].values())+sum(x['seconds'] for x in loads)
    forecast['estimated_test_hours_with_30pct_contingency']=seconds*1.3/3600
print(json.dumps(forecast,indent=2))
