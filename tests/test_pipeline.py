import copy
import math
import tempfile
import unittest
from pathlib import Path
import numpy as np
from auditbench.cases import build,public,evidence,make_case
from auditbench.checker import expected,label
from auditbench.common import config,read,lines,write
from auditbench.runner import run,validate,freeze
from auditbench.analysis import queue,cluster_indices
from auditbench.inference import normalized_error
from auditbench.__main__ import verify_data

class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.root=Path(cls.temp.name);cls.cfg=config();cls.data=build(cls.cfg,cls.root/'data.json')
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def test_dataset_and_controls(self):
        result=verify_data(self.data);self.assertEqual(result['cases'],180);self.assertGreater(result['reordered_cases'],150)
        cases=self.data['cases']
        self.assertEqual(sum(c['split']=='development' for c in cases),30)
        for f in self.cfg['families']:
            dev={c['variant'] for c in cases if c['family']==f and c['split']=='development'}
            hold={c['variant'] for c in cases if c['family']==f and c['split']=='held_out_variant'}
            self.assertFalse(dev & hold)
    def test_hand_computed_metrics(self):
        c={'spec':{'metric':'macro_f1'},'records':[{'field':m,'tn':6,'fp':2,'fn':1,'tp':3} for m in ['A','B']]}
        val=expected(c);self.assertAlmostEqual(val['score_A'],round(((6/9)+(12/15))/2,4));self.assertEqual(val['winner'],'tie')
        c['spec']['metric']='precision';self.assertEqual(expected(c)['score_A'],.6)
    def test_zero_denominator(self):
        c={'spec':{'metric':'precision'},'records':[{'field':m,'tn':10,'fp':0,'fn':0,'tp':0} for m in ['A','B']]}
        self.assertEqual(expected(c)['score_A'],0)
    def test_report_about_bad_workflow_can_be_correct(self):
        for c in self.data['cases']:
            if c['family']=='evaluation_selection' and c['gold']['policy_compliant'] is False:
                self.assertEqual(label(public(c),c['gold'])['status'],'correct');return
        self.fail('No noncompliant cases')
    def test_missing_run_and_subgroup_threshold(self):
        c={'spec':{'rule':'subgroup_minimum','threshold':.02,'groups':['g1','g2']},'records':[{'field':'required','run':1},{'field':'observed','run':1,'group':'g1','improvement':.1}]}
        self.assertEqual(expected(c),{'complete':False,'claim_supported':False})
        c['records'].append({'field':'observed','run':1,'group':'g2','improvement':-.01})
        self.assertEqual(expected(c),{'complete':True,'claim_supported':False})
    def test_checker_ignores_gold(self):
        c=copy.deepcopy(self.data['cases'][0]);truth=expected(c);c['gold']={'nonsense':123};c['corrupt']={};self.assertEqual(expected(c),truth)
    def test_schema_and_numeric_tolerance(self):
        c=self.data['cases'][0];r=copy.deepcopy(c['gold']);r['score_A']=float('nan');self.assertEqual(label(public(c),r)['status'],'unassessable')
        r=copy.deepcopy(c['gold']);r['extra']=True;self.assertEqual(label(public(c),r)['status'],'unassessable')
        r=copy.deepcopy(c['gold']);r['score_A']+=.004;self.assertEqual(label(public(c),r)['status'],'correct')
    def test_same_evidence_no_gold_in_public(self):
        for c in self.data['cases']:
            self.assertEqual(sorted(evidence(c,'original_order_evidence').splitlines()),sorted(evidence(c,'claim_organized_evidence').splitlines()))
            self.assertFalse(set(public(c)) & {'gold','corrupt','split','family','id','corruption_subtype'})
    def test_queue_oracle_ceiling_and_policies(self):
        y=np.array([1]*50+[0]*50);ties=np.arange(100)
        self.assertEqual(queue(y,y,.2,ties)['recall'],.4)
        self.assertEqual(queue(y,1-y,.2,ties)['recall'],0)
        self.assertTrue(math.isnan(queue(np.zeros(10),np.zeros(10),.2,np.arange(10))['recall']))
    def test_bootstrap_keeps_pairs(self):
        reports=[{'case_id':str(i),'family':'f','split':'s'} for i in range(5) for _ in range(2)]
        idx=cluster_indices(reports,np.random.default_rng(3))
        for i in range(0,10,2):self.assertEqual(sum(idx==i),sum(idx==i+1))
    def test_normalization(self):
        self.assertAlmostEqual(normalized_error(math.log(.8),math.log(.2)),.8)
        self.assertEqual(normalized_error(-10000,0),0);self.assertEqual(normalized_error(0,-10000),1)
    def test_resume_and_missing_scores_detected(self):
        out=self.root/'resume';run(self.cfg,self.data,out,'smoke','fixture');before=(out/'scores.jsonl').read_bytes()
        run(self.cfg,self.data,out,'smoke','fixture');self.assertEqual(before,(out/'scores.jsonl').read_bytes());self.assertTrue(validate(self.cfg,self.data,out)['valid'])
        scorelines=(out/'scores.jsonl').read_text().splitlines();(out/'scores.jsonl').write_text('\n'.join(scorelines[:-1])+'\n')
        with self.assertRaises(ValueError):validate(self.cfg,self.data,out)
        run(self.cfg,self.data,out,'smoke','fixture');self.assertTrue(validate(self.cfg,self.data,out)['valid'])
    def test_real_test_requires_freeze(self):
        with self.assertRaises(ValueError):run(self.cfg,self.data,self.root/'no-freeze','test','real')
    def test_fixture_cannot_authorize_real_freeze(self):
        out=self.root/'fake-development';run(self.cfg,self.data,out,'development','fixture')
        with self.assertRaises(ValueError):freeze(self.cfg,self.data,out,self.root/'freeze.json')
    def test_optional_extension_reuses_existing_records(self):
        out=self.root/'extension';run(self.cfg,self.data,out,'development','fixture')
        before=lines(out/'scores.jsonl');generated=(out/'generation.jsonl').read_bytes()
        run(self.cfg,self.data,out,'development','fixture',optional=True)
        after=lines(out/'scores.jsonl')
        self.assertEqual(after[:len(before)],before);self.assertEqual((out/'generation.jsonl').read_bytes(),generated)
        self.assertEqual(len(after),len(before)*3//2)
        self.assertTrue(validate(self.cfg,self.data,out)['valid'])
    def test_strict_json_rejects_duplicate_and_nonfinite(self):
        from auditbench.runner import parse_report
        self.assertIsNone(parse_report('{"score": NaN}'))
        self.assertIsNone(parse_report('{"score": 1, "score": 2}'))
        self.assertIsNone(parse_report('```json {} ```'))
        self.assertEqual(parse_report('{"score": 1}'),{'score':1})
    def test_validator_rejects_tampered_prompt_and_score(self):
        from auditbench.common import append,digest
        out=self.root/'tamper';run(self.cfg,self.data,out,'smoke','fixture')
        original=(out/'scores.jsonl').read_text();rows=lines(out/'scores.jsonl')
        rows[0]['prompt'][1]['content']='different prompt';rows[0]['prompt_hash']=digest(rows[0]['prompt'])
        (out/'scores.jsonl').unlink()
        for row in rows:append(out/'scores.jsonl',row)
        with self.assertRaises(ValueError):validate(self.cfg,self.data,out)
        (out/'scores.jsonl').write_text(original);rows=lines(out/'scores.jsonl');rows[0]['p_error']=.12345
        (out/'scores.jsonl').unlink()
        for row in rows:append(out/'scores.jsonl',row)
        with self.assertRaises(ValueError):validate(self.cfg,self.data,out)

    def test_auroc_ties_and_reversal(self):
        from auditbench.analysis import auroc
        self.assertEqual(auroc([0,1],[.2,.8]),1)
        self.assertEqual(auroc([0,1],[.8,.2]),0)
        self.assertEqual(auroc([0,1],[.5,.5]),.5)

    def test_resume_rejects_changed_config(self):
        out=self.root/'changed';run(self.cfg,self.data,out,'smoke','fixture');c=copy.deepcopy(self.cfg);c['generator']['seed']+=1
        with self.assertRaises(ValueError):run(c,self.data,out,'smoke','fixture')

if __name__=='__main__':unittest.main()
