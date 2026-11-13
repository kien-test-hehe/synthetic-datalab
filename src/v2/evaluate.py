"""HF base/adapter evaluation on pinned local, evaluation-only datasets.

Use the same grading implementation as Ollama baseline. The test split requires
a frozen experiment protocol and explicit unlock; use dev for iteration.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from src.v2.build import digest,require
from src.v2.training import model_fingerprint,token_ids
from src.eval.independent import FROZEN_V1
from src.eval.model_eval import run

def fingerprint(args):
    return {"model_sha256":model_fingerprint(args.model),
            "adapter_sha256":model_fingerprint(args.adapter) if args.adapter else None,
            "template_kwargs":json.loads(args.template_kwargs),"num_ctx":args.num_ctx,
            "max_tokens":args.max_tokens,"temperature":0,"seed":42}

def verify_eval(args,signature):
    root=Path(args.benchmark_root)
    path=root/(args.split+".jsonl")
    require(digest(path)==FROZEN_V1[args.split]["sha256"],"Frozen evaluation SHA mismatch")
    if args.split=="test":
        require(args.unlock_test and args.protocol,"Test locked: explicit unlock and protocol required")
        require(not args.limit,"Full test split required")
        protocol=json.loads(Path(args.protocol).read_text(encoding="utf-8"))
        require(protocol==signature,"Model or settings differ from preregistered protocol")
    return path

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--model",required=True);p.add_argument("--adapter");p.add_argument("--output",required=True)
    p.add_argument("--split",choices=("dev","test"),default="dev")
    p.add_argument("--benchmark-root",default="evaluation/independent/exports")
    p.add_argument("--num-ctx",type=int,default=8192);p.add_argument("--max-tokens",type=int,default=512)
    p.add_argument("--template-kwargs",default="{}");p.add_argument("--limit",type=int,default=0)
    p.add_argument("--protocol");p.add_argument("--unlock-test",action="store_true")
    p.add_argument("--write-protocol",action="store_true")
    args=p.parse_args()
    sig=fingerprint(args)
    require(isinstance(sig["template_kwargs"],dict) and not (set(sig["template_kwargs"])&{"tokenize","add_generation_prompt","return_tensors","return_dict","truncation","max_length"}),"Invalid template kwargs")
    if args.write_protocol:
        require(args.split=="dev" and args.protocol and not Path(args.protocol).exists(),"Protocol must be newly written before test")
        Path(args.protocol).parent.mkdir(parents=True,exist_ok=True)
        Path(args.protocol).write_text(json.dumps(sig,indent=2)+"\n",encoding="utf-8")
        return
    dataset=verify_eval(args,sig)
    out=Path(args.output)
    require(not out.exists() and not out.with_suffix(".summary.json").exists(),"Refusing to overwrite eval")
    import torch
    from transformers import AutoTokenizer,AutoModelForCausalLM,set_seed
    require(torch.cuda.is_available() and torch.cuda.is_bf16_supported(),"CUDA BF16 required")
    set_seed(42)
    tok=AutoTokenizer.from_pretrained(args.model,local_files_only=True,trust_remote_code=False)
    model=AutoModelForCausalLM.from_pretrained(args.model,local_files_only=True,trust_remote_code=False,torch_dtype=torch.bfloat16).to("cuda")
    if args.adapter:
        from peft import PeftModel
        model=PeftModel.from_pretrained(model,args.adapter,local_files_only=True)
    model.eval()
    def call(messages,model_name,endpoint,timeout,temperature,num_ctx,max_tokens):
        ids=token_ids(tok,messages,True,sig["template_kwargs"])
        require(len(ids)+max_tokens<=num_ctx,"Token budget exceeded; no truncation")
        x=torch.tensor([ids],device="cuda")
        with torch.inference_mode():
            y=model.generate(input_ids=x,attention_mask=torch.ones_like(x),max_new_tokens=max_tokens,do_sample=False,
                 pad_token_id=tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id)
        new=y[0,len(ids):].tolist()
        return tok.decode(new,skip_special_tokens=True),{"prompt_eval_count":len(ids),"eval_count":len(new),"done_reason":"length" if len(new)>=max_tokens else "stop"}
    settings=SimpleNamespace(endpoint="http://127.0.0.1:11434",dataset=str(dataset),kind="synthetic",context="gold",chunks=None,db=None,k=10,
        limit=args.limit,output=str(out),model=str(args.model)+("+"+str(args.adapter) if args.adapter else ""),timeout=180,
        temperature=0,num_ctx=args.num_ctx,max_tokens=args.max_tokens,max_context_chars=200000)
    result=run(settings,call=call)
    result["hf_signature"]=sig
    result["split"]=args.split
    out.with_suffix(".summary.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(result["summary"],indent=2))

if __name__=="__main__":main()
