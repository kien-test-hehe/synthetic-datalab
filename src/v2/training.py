"""Local HF/PEFT pilot trainer. No model downloads, no evaluation in training."""
from __future__ import annotations
import argparse
import hashlib
import json
import random
from pathlib import Path
from src.v2.build import read,require,digest,SOURCE

def token_ids(tokenizer,messages,add_generation_prompt,kwargs):
    ids=tokenizer.apply_chat_template(messages,tokenize=True,add_generation_prompt=add_generation_prompt,**kwargs)
    if hasattr(ids,"tolist"):ids=ids.tolist()
    if isinstance(ids,dict) or hasattr(ids,"keys"):ids=ids["input_ids"]
    if ids and isinstance(ids[0],list):
        if len(ids)!=1:raise ValueError("Unexpected batched tokenizer output")
        ids=ids[0]
    if not isinstance(ids,list) or not ids or not all(type(x)==int for x in ids):
        raise ValueError("Tokenizer must return a single sequence of token IDs")
    return ids

def tokenize_row(tokenizer,row,max_length,kwargs=None):
    require(row["source"]==SOURCE and row["split"]=="train","Training provenance")
    msgs=row["messages"];kwargs=kwargs or {}
    require([m["role"] for m in msgs]==["system","user","assistant"],"Only single-turn exports are supported")
    prefix=token_ids(tokenizer,msgs[:2],True,kwargs)
    full=token_ids(tokenizer,msgs,False,kwargs)
    # Template-dependent generation prefixes can differ from full-turn prefixes.
    # Reject, rather than silently masking user tokens or training on a different prompt.
    require(full[:len(prefix)]==prefix,"Chat template prefix mismatch: inspect template/thinking settings")
    require(len(full)>len(prefix),"Empty assistant target")
    require(len(full)<=max_length,f"{row['id']}: {len(full)} tokens exceeds {max_length}; no truncation")
    return {"input_ids":full,"attention_mask":[1]*len(full),"labels":[-100]*len(prefix)+full[len(prefix):]}

def select_groups(rows,limit,seed):
    from collections import Counter,defaultdict
    groups={}
    for r in rows:groups.setdefault(r["case_group"],[]).append(r)
    strata=defaultdict(list)
    for key,group in groups.items():
        tasks=Counter(r.get("task","unknown") for r in group)
        dominant=sorted(tasks,key=lambda t:(-tasks[t],t))[0]
        lang=group[0].get("language",{}).get("answer","unknown")
        strata[(dominant,lang)].append(key)
    rng=random.Random(seed)
    for keys in strata.values():
        keys.sort();rng.shuffle(keys)
    order=[]
    while any(strata.values()):
        for key in sorted(strata):
            if strata[key]:order.append(strata[key].pop())
    selected=[]
    for key in order:
        group=groups[key]
        # Prefix cutoff makes increasing budgets nested.
        if limit and len(selected)+len(group)>limit:break
        selected.extend(group)
    require(bool(selected),"No complete case groups fit requested sample budget")
    return selected

def load_training(path,manifest,limit,seed):
    path=Path(path);meta=json.loads(Path(manifest).read_text(encoding="utf-8"))
    entry=meta["exports"].get(path.stem)
    require(entry and digest(path)==entry["sha256"],"Unverified export checksum")
    require(path.stem in ("sft_lite","sft_reasoning","sft_calculator_lite","sft_calculator_reasoning","sft_lite_answer_only","sft_reasoning_answer_only","v1_control_matched","v1_control_full"),"Not an SFT export")
    rows=read(path)
    require(len(rows)==entry["rows"] and len({r["id"] for r in rows})==len(rows),"Export count/IDs")
    require(all(r["source"]==SOURCE and r["split"]=="train" for r in rows),"Unexpected training provenance")
    return select_groups(rows,limit,seed)

def collator(pad_id):
    import torch
    def collate(rows):
        n=max(len(x["input_ids"]) for x in rows)
        return {key:torch.tensor([x[key]+[pad]*(n-len(x[key])) for x in rows],dtype=torch.long)
                for key,pad in (("input_ids",pad_id),("attention_mask",0),("labels",-100))}
    return collate

def model_fingerprint(root):
    root=Path(root)
    files=[p for p in root.rglob("*") if p.is_file() and (p.suffix in (".safetensors",".bin",".json",".model",".jinja",".txt"))]
    require(any(p.suffix in (".safetensors",".bin") for p in files),"Local model weights required")
    manifest={}
    for p in sorted(files):
        h=hashlib.sha256()
        with p.open("rb") as f:
            for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
        manifest[str(p.relative_to(root))]=h.hexdigest()
    return hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest()

def prepare(args):
    from transformers import AutoTokenizer
    model=Path(args.model).resolve();require(model.is_dir(),"Use an existing local model directory")
    tokenizer=AutoTokenizer.from_pretrained(str(model),local_files_only=True,trust_remote_code=False)
    kwargs=json.loads(args.template_kwargs)
    require(isinstance(kwargs,dict) and not (set(kwargs)&{"tokenize","add_generation_prompt","return_tensors","return_dict","truncation","max_length"}),"Invalid template kwargs")
    rows=load_training(args.dataset,args.manifest,args.limit,args.seed)
    if args.extra_dataset:
        extra=load_training(args.extra_dataset,args.manifest,0,args.seed)
        groups={r["case_group"] for r in rows}
        rows+= [r for r in extra if r["case_group"] in groups]
    require(len({r["id"] for r in rows})==len(rows),"Duplicate export IDs")
    encoded=[tokenize_row(tokenizer,r,args.max_length,kwargs) for r in rows]
    lengths=sorted(len(x["input_ids"]) for x in encoded)
    report={"selected_rows":len(rows),"selected_groups":len({r["case_group"] for r in rows}),
        "selected_ids":[r["id"] for r in rows],"total_tokens":sum(lengths),
        "assistant_tokens":sum(sum(y!=-100 for y in x["labels"]) for x in encoded),
        "min_tokens":lengths[0],"median_tokens":lengths[len(lengths)//2],"max_tokens":lengths[-1],
        "dataset_sha256":digest(args.dataset),"extra_dataset_sha256":digest(args.extra_dataset) if args.extra_dataset else None,
        "model_dir":str(model),"template_kwargs":kwargs,"max_length":args.max_length,"seed":args.seed}
    return tokenizer,encoded,report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--model",required=True);p.add_argument("--dataset",required=True)
    p.add_argument("--extra-dataset");p.add_argument("--manifest",default="sft/v2/exports/manifest.json")
    p.add_argument("--output",required=True);p.add_argument("--max-length",type=int,default=4096)
    p.add_argument("--limit",type=int,default=0);p.add_argument("--seed",type=int,default=42)
    p.add_argument("--epochs",type=float,default=1);p.add_argument("--lr",type=float,default=1e-4)
    p.add_argument("--rank",type=int,default=16);p.add_argument("--accum",type=int,default=16)
    p.add_argument("--template-kwargs",default="{}");p.add_argument("--dry-run",action="store_true")
    args=p.parse_args()
    out=Path(args.output)
    require(not out.exists() or not any(out.iterdir()),"Refusing to overwrite run directory")
    out.mkdir(parents=True,exist_ok=True)
    tokenizer,encoded,report=prepare(args)
    report.update({"model_sha256":model_fingerprint(args.model),"epochs":args.epochs,"lr":args.lr,"rank":args.rank,"accum":args.accum,"dry_run":args.dry_run})
    (out/"preflight.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k!="selected_ids"},indent=2))
    if args.dry_run:return
    import torch
    from transformers import AutoModelForCausalLM,Trainer,TrainingArguments,set_seed
    from peft import LoraConfig,get_peft_model
    require(torch.cuda.is_available() and torch.cuda.is_bf16_supported(),"CUDA with BF16 required")
    set_seed(args.seed)
    model=AutoModelForCausalLM.from_pretrained(args.model,local_files_only=True,trust_remote_code=False,torch_dtype=torch.bfloat16)
    model.config.use_cache=False
    model=get_peft_model(model,LoraConfig(r=args.rank,lora_alpha=2*args.rank,lora_dropout=.05,target_modules="all-linear",task_type="CAUSAL_LM"))
    model.enable_input_require_grads()
    pad=tokenizer.pad_token_id if tokenizer.pad_token_id is not None else tokenizer.eos_token_id
    require(pad is not None,"Tokenizer needs pad or EOS token")
    config=TrainingArguments(output_dir=str(out/"checkpoints"),num_train_epochs=args.epochs,
        per_device_train_batch_size=1,gradient_accumulation_steps=args.accum,learning_rate=args.lr,
        bf16=True,gradient_checkpointing=True,logging_steps=1,save_strategy="epoch",
        report_to="none",remove_unused_columns=False,seed=args.seed,data_seed=args.seed)
    trainer=Trainer(model=model,args=config,train_dataset=encoded,data_collator=collator(pad))
    result=trainer.train()
    trainer.save_model(str(out/"adapter"));tokenizer.save_pretrained(str(out/"adapter"))
    (out/"train_metrics.json").write_text(json.dumps(result.metrics,indent=2)+"\n",encoding="utf-8")

if __name__=="__main__":main()
