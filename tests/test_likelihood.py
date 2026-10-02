"""Optional CPU test of exact production scoring on a tiny randomly initialized Qwen3."""
import importlib.util
import unittest

@unittest.skipUnless(importlib.util.find_spec('torch') and importlib.util.find_spec('transformers'),'Install inference dependencies for Qwen3 CPU likelihood verification')
class LikelihoodTests(unittest.TestCase):
    def test_teacher_forcing_matches_full_logits_reference(self):
        import torch
        from transformers import Qwen3Config,Qwen3ForCausalLM
        from auditbench.inference import sequence_log_likelihood
        torch.manual_seed(5)
        model=Qwen3ForCausalLM(Qwen3Config(vocab_size=64,hidden_size=32,intermediate_size=64,num_hidden_layers=2,num_attention_heads=4,num_key_value_heads=2,head_dim=8,attention_dropout=0)).eval()
        prefix=[1,6,10,3];target=[12,14,2]
        actual=sequence_log_likelihood(model,prefix,target,torch,'cpu')
        with torch.inference_mode():
            logits=model(input_ids=torch.tensor([prefix+target]),use_cache=False).logits[0]
            expected=sum(float(torch.log_softmax(logits[len(prefix)-1+j],-1)[token]) for j,token in enumerate(target))
        self.assertAlmostEqual(actual,expected,places=5)
        # Single-token answer still scores its termination; empty context is rejected.
        self.assertTrue(torch.isfinite(torch.tensor(sequence_log_likelihood(model,prefix,[2],torch,'cpu'))))
        with self.assertRaises(ValueError):sequence_log_likelihood(model,[],target,torch,'cpu')
