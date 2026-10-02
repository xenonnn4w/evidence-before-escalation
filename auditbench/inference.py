"""Lazy HF imports so data/checking/analysis can run without CUDA or torch."""
import math
import time

def normalized_error(log_error,log_ok):
    d=log_ok-log_error
    return math.exp(-d)/(1+math.exp(-d)) if d>0 else 1/(1+math.exp(d))


def sequence_log_likelihood(model, prefix, target, torch, device):
    """Score only forced continuation, including its termination; never prompt tokens."""
    if not prefix or not target:raise ValueError('Empty prefix/target')
    x=torch.tensor([prefix+target],device=device)
    with torch.inference_mode():
        out=model(input_ids=x,attention_mask=torch.ones_like(x),use_cache=False,logits_to_keep=len(target)+1)
        logits=out.logits[0,:-1,:].float()
        labels=torch.tensor(target,device=device)
        return float(torch.log_softmax(logits,dim=-1).gather(1,labels[:,None]).sum().cpu())

class HFModel:
    def __init__(self, model, revision, max_input_tokens=4096):
        import torch
        from transformers import AutoModelForCausalLM,AutoTokenizer
        if not revision or len(revision)!=40:raise ValueError('Immutable model revision required')
        if not torch.cuda.is_available():raise RuntimeError('Real experiment requires CUDA; use fixture mode only for software tests')
        self.torch=torch;self.cap=max_input_tokens
        self.tokenizer=AutoTokenizer.from_pretrained(model,revision=revision)
        start=time.perf_counter()
        self.model=AutoModelForCausalLM.from_pretrained(model,revision=revision,torch_dtype=torch.bfloat16,attn_implementation='sdpa').to('cuda').eval()
        torch.cuda.synchronize();self.load_seconds=time.perf_counter()-start

    def encode(self,messages):
        ids=self.tokenizer.apply_chat_template(messages,tokenize=True,add_generation_prompt=True,enable_thinking=False)
        if len(ids)>self.cap:raise ValueError(f'Input length {len(ids)} exceeds cap {self.cap}; refusing truncation')
        return ids

    def generate(self,messages,settings,seed):
        from transformers import set_seed
        t=self.torch;ids=self.encode(messages);set_seed(seed)
        x=t.tensor([ids],device='cuda');t.cuda.reset_peak_memory_stats();t.cuda.synchronize();start=time.perf_counter()
        with t.inference_mode():
            y=self.model.generate(input_ids=x,attention_mask=t.ones_like(x),do_sample=True,temperature=settings['temperature'],top_p=settings['top_p'],top_k=settings['top_k'],max_new_tokens=settings['max_new_tokens'],pad_token_id=self.tokenizer.eos_token_id)
        t.cuda.synchronize()
        output=y[0,len(ids):].tolist()
        return {'raw':self.tokenizer.decode(output,skip_special_tokens=True),'input_tokens':len(ids),'output_tokens':len(output),'seconds':time.perf_counter()-start,'peak_vram_bytes':t.cuda.max_memory_allocated(),'truncated':len(output)>=settings['max_new_tokens'] and output[-1]!=self.tokenizer.eos_token_id}

    def score(self,messages):
        t=self.torch;prefix=self.encode(messages)
        prompt=self.tokenizer.decode(prefix,skip_special_tokens=False)
        t.cuda.reset_peak_memory_stats();t.cuda.synchronize();start=time.perf_counter();logs={};targets={}
        for name in ['ERROR','OK']:
            # Re-tokenize the actual prompt boundary and assert it is unchanged.
            joint=self.tokenizer.encode(prompt+name,add_special_tokens=False)
            if joint[:len(prefix)]!=prefix:raise ValueError('Label changes prompt tokenization boundary')
            target=joint[len(prefix):]+[self.tokenizer.eos_token_id]
            if not target or len(target)>16:raise ValueError('Unexpected verdict tokenization')
            logs[name]=sequence_log_likelihood(self.model,prefix,target,t,'cuda')
            targets[name]=target
        t.cuda.synchronize()
        if not all(math.isfinite(v) for v in logs.values()):raise ValueError('Nonfinite likelihood')
        return {'p_error':normalized_error(logs['ERROR'],logs['OK']),'log_likelihoods':logs,'label_token_ids':targets,'input_tokens':len(prefix),'seconds':time.perf_counter()-start,'peak_vram_bytes':t.cuda.max_memory_allocated()}
