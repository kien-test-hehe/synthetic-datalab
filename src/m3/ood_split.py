"""Out-of-template split for M3, holding out whole reasoning programs.

A world-disjoint split is NOT a program-disjoint split. This adds a
strict unseen-program evaluation alongside the ordinary train/dev/test.
Do not use the unseen-program test to tune SFT training choices.
"""
from __future__ import annotations
import argparse
import json
from collections import Counter
from pathlib import Path

DEFAULT_HOLDOUT=("E4","C4","W4","L4","T4","S4","V4","U4")


def read_rows(path):
    return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]


def build_ood(input_dir="sft/m3/outputs",out_dir="sft/m3/ood",holdout=DEFAULT_HOLDOUT):
    source=Path(input_dir);dest=Path(out_dir);dest.mkdir(parents=True,exist_ok=True)
    holdout=set(holdout)
    if not holdout:
        raise ValueError("Specify at least one unseen reasoning program")
    original={split:read_rows(source/f"m3_{split}.jsonl") for split in ("train","dev","test")}
    present={row["original_task_id"] for rows in original.values() for row in rows}
    if holdout-present:
        raise ValueError(f"Unknown held-out programs: {sorted(holdout-present)}")
    train_seen=[r for r in original["train"] if r["original_task_id"] not in holdout]
    dev_seen=[r for r in original["dev"] if r["original_task_id"] not in holdout]
    test_seen=[r for r in original["test"] if r["original_task_id"] not in holdout]
    test_unseen=[r for r in original["test"] if r["original_task_id"] in holdout]
    splits={"train_seen":train_seen,"dev_seen":dev_seen,
            "test_seen":test_seen,"test_unseen":test_unseen}
    assert test_unseen and train_seen
    assert not ({r["original_task_id"] for r in train_seen} & holdout)
    assert {r["original_task_id"] for r in test_unseen}<=holdout
    assert not ({r["world_id"] for r in train_seen} & {r["world_id"] for r in test_unseen})
    all_ids=[r["id"] for rows in splits.values() for r in rows]
    assert len(all_ids)==len(set(all_ids))
    for name,rows in splits.items():
        with (dest/f"{name}.jsonl").open("w",encoding="utf-8") as f:
            for row in rows:f.write(json.dumps(row,ensure_ascii=False,sort_keys=True)+"\n")
    report={"holdout_task_types":sorted(holdout),
            "counts":{k:len(v) for k,v in splits.items()},
            "seen_train_types":sorted({x["original_task_id"] for x in train_seen}),
            "unseen_test_types":sorted({x["original_task_id"] for x in test_unseen}),
            "worlds_disjoint":True,
            "programs_disjoint_from_train":True,
            "warning":"Performance on unseen program families may reflect base-model prior knowledge; no LLM API generated the test items."}
    (dest/"manifest.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return report


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="sft/m3/outputs")
    p.add_argument("--out",default="sft/m3/ood")
    p.add_argument("--holdout",default=",".join(DEFAULT_HOLDOUT))
    args=p.parse_args()
    print(json.dumps(build_ood(args.input,args.out,args.holdout.split(",")),indent=2))
