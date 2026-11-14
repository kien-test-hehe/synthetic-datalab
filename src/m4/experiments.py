"""Prepare fair SFT ablations using a single frozen M3 world split.

Important: the independent 200-world M2 and 800-world M3 builds can assign the
same company-world ID to DIFFERENT splits. Do not directly concatenate their
files or compare M2 training against arbitrary M3 test examples.

This module NEVER reads real evaluation QA or real financial documents.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import random
import re
from collections import Counter
from pathlib import Path
from src.authored_export import SOURCE as AUTHORED_SOURCE, FROZEN_HOLDOUT_SHA256
from src.eval.model_eval import SCHEMA, synthetic_oracle
from copy import deepcopy
from src.m3.ood_split import DEFAULT_HOLDOUT

def read_rows(path):
    return [json.loads(s) for s in Path(path).read_text(encoding="utf-8").splitlines() if s.strip()]

def world(row):
    return row.get("world_id") or row.get("case_id") or ""

def allowed_source(row):
    return row.get("source") in ("original_fictional_hand_authored",
        "controlled_programmatic_instantiation","controlled_robustness_augmentation")

def load_authored(root):
    root=Path(root)
    manifest=json.loads((root/"manifest.json").read_text(encoding="utf-8"))
    rows={}
    for split,n in (("train",10000),("dev",14),("test",14)):
        path=root/f"{split}.jsonl"
        meta=manifest["splits"][split]
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        if digest!=meta["sha256"]:
            raise ValueError(f"Authored export checksum mismatch: {split}")
        if split in FROZEN_HOLDOUT_SHA256 and digest!=FROZEN_HOLDOUT_SHA256[split]:
            raise ValueError(f"Frozen authored holdout mismatch: {split}")
        rows[split]=read_rows(path)
        if len(rows[split])!=n or meta["rows"]!=n:
            raise ValueError(f"Expected {n} authored {split} rows")
        if any(r["source"]!=AUTHORED_SOURCE or r["split"]!=split for r in rows[split]):
            raise ValueError(f"Invalid authored provenance: {split}")
    all_rows=[r for group in rows.values() for r in group]
    if len({r["id"] for r in all_rows})!=len(all_rows):
        raise ValueError("Duplicate authored IDs")
    return rows,manifest

def structured_row(row):
    r=deepcopy(row)
    oracle=synthetic_oracle(r)
    # Multi-result questions retain all results in the full authored answer;
    # do not force one arbitrary result into the scalar value field.
    body=r["answer"]
    body=re.sub(r"\n(?:Bằng chứng|Evidence):\s*(?:\[[^\]]+\]\s*)+$","",body).strip()
    payload={"status":"insufficient" if oracle["kind"]=="insufficient" else "answerable",
             "answer":body,"value":oracle["value"] if oracle["kind"]=="numeric" else None,
             "unit":oracle["unit"] if oracle["kind"]=="numeric" else None,
             "citations":r["evidence_ids"]}
    r["oracle"]=oracle
    r["messages"][0]["content"]+="\n"+SCHEMA
    r["messages"][2]["content"]=json.dumps(payload,ensure_ascii=False,allow_nan=False)
    r["output_contract"]="financial_json_v1"
    return r

def prepare(m3="sft/m3/outputs",out="sft/m4/experiments",m1="sft/m1/exports",m4="sft/m4",ood=False,authored_root="sft/authored/exports"):
    m3=Path(m3);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    source={s:read_rows(m3/f"m3_{s}.jsonl") for s in ("train","dev","test")}
    authored,m4report=({s:[] for s in source},None) if ood else load_authored(authored_root)
    # Include foreign evidence owners in split checks, not only target worlds.
    def owners(rows):
        return {world(r) for r in rows}|{e["owner_world_id"] for r in rows for e in r["evidence"] if e.get("owner_world_id")}
    owner_sets={s:owners(source[s]+authored[s]) for s in source}
    if any(owner_sets[a]&owner_sets[b] for a,b in (("train","dev"),("train","test"),("dev","test"))):
        raise ValueError("Evidence owner leakage across splits")
    world_sets={s:{world(r) for r in source[s]+authored[s]} for s in source}
    assert all(world_sets[s] and "" not in world_sets[s] for s in source)
    assert not (world_sets["train"]&world_sets["dev"] or world_sets["train"]&world_sets["test"] or world_sets["dev"]&world_sets["test"])
    holdout=set(DEFAULT_HOLDOUT)
    if ood:
        # No authored seed added: conceptual overlap with the held-out programs is not audited.
        pool=[r for r in source["train"] if r["original_task_id"] not in holdout]
        dev=[r for r in source["dev"] if r["original_task_id"] not in holdout]
        test=[r for r in source["test"] if r["original_task_id"] in holdout]
        assert all(r["original_task_id"] not in holdout for r in pool+dev)
        assert all(r["original_task_id"] in holdout for r in test)
    else:
        pool=source["train"];dev=source["dev"];test=source["test"]
    gold=[r for r in pool if r["variant_type"]=="m2_gold_context"]
    conditions={"gold_only":gold,"robust_all":pool}
    # Size-matched comparison isolates augmentation from the number of SFT examples.
    # Stratify by source task, then sample rows deterministically within each group.
    # Both arms are selected exclusively from identical training-world partitions.
    rng=random.Random(42)
    matched=[]
    bytask={}
    for row in pool:bytask.setdefault(row["original_task_id"],[]).append(row)
    target=Counter(r["original_task_id"] for r in gold)
    for task,n in sorted(target.items()):
        candidates=list(bytask[task]);rng.shuffle(candidates)
        matched.extend(candidates[:n])
    assert len(matched)==len(gold)
    assert Counter(r["original_task_id"] for r in matched)==target
    conditions["robust_size_matched"]=matched
    if not ood:
        conditions["authored_only"]=authored["train"]
        conditions["authored_verified_oracle"]=[r for r in authored["train"] if synthetic_oracle(r)["kind"] in ("numeric","qualitative","insufficient")]
        conditions["authored_plus_robust"]=authored["train"]+pool
        conditions["authored_plus_gold"]=authored["train"]+gold
    def write(name,rows):
        path=out/(name+".jsonl")
        ids=set()
        for row in rows:
            assert allowed_source(row) and world(row)
            assert row["id"] not in ids
            ids.add(row["id"])
            assert [x["role"] for x in row["messages"]]==["system","user","assistant"]
        with path.open("w",encoding="utf-8") as f:
            for r in rows:f.write(json.dumps(structured_row(r),ensure_ascii=False,sort_keys=True)+"\n")
        return {"rows":len(rows),"worlds":len({world(r) for r in rows}),
                "sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
                "source_counts":dict(Counter(r["source"] for r in rows))}
    summaries={}
    for name,rows in conditions.items():
        assert all(r["split"]=="train" for r in rows)
        assert {world(r) for r in rows}.isdisjoint(world_sets["dev"]|world_sets["test"])
        summaries[name]=write(name,rows)
    summaries["common_dev"]=write("common_dev",dev)
    summaries["common_test"]=write("common_test",test)
    if not ood:
        summaries["authored_dev"]=write("authored_dev",authored["dev"])
        summaries["authored_test"]=write("authored_test",authored["test"])
    report={"mode":"program_ood" if ood else "world_holdout",
            "holdout_task_types":sorted(holdout) if ood else [],
            "files":summaries,"authored_export":m4report,"output_contract":"financial_json_v1",
            "notes":["Use the SAME common_dev/common_test within a mode.",
                     "The gold-only arm is derived from M3, not the old independently split M2 export.",
                     "Train with assistant/completion-only loss; inspect tokenizer length and reject truncated examples.",
                     "The size-matched arm matches row count and task composition, not exact token count or unique worlds.",
                     "OOD mode deliberately excludes M1/M4 authored data to avoid conceptual holdout overlap.",
                     "Never add real FinanceBench labels to these files."]}
    (out/"manifest.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--m3",default="sft/m3/outputs");p.add_argument("--out",default="sft/m4/experiments")
    p.add_argument("--m1",default="sft/m1/exports");p.add_argument("--m4",default="sft/m4");p.add_argument("--authored-root",default="sft/authored/exports");p.add_argument("--ood",action="store_true")
    a=p.parse_args();print(json.dumps(prepare(a.m3,a.out,a.m1,a.m4,a.ood,a.authored_root),indent=2,ensure_ascii=False))
