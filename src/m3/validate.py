"""Validate source provenance and numerical correctness of M3 evidence curricula."""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from src.m2.build_m2 import eval_expr

VARIANTS = ("m2_gold_context", "cross_company_distractors", "missing_target_evidence")


def validate(root="sft/m3/outputs", worlds=200):
    folder=Path(root)
    splits={}
    for split in ("train","dev","test"):
        splits[split]=[json.loads(line) for line in
            (folder/f"m3_{split}.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    allrows=[r for items in splits.values() for r in items]
    assert len(allrows)==18*worlds
    assert [len(splits[s]) for s in ("train","dev","test")]==[
        worlds*18*8//10, worlds*18//10, worlds*18//10]
    assert len({r["id"] for r in allrows})==len(allrows)
    assert len({r["world_id"] for r in allrows})==worlds
    assert set(r["source_type"] for r in allrows)=={"fully_synthetic_only"}
    byworld=defaultdict(list)
    citations=0; numerical=0; foreign_checked=0; missing_checked=0
    world_to_split={}
    for split,rows in splits.items():
        for r in rows:
            assert r["split"]==split
            if r["world_id"] in world_to_split:
                assert world_to_split[r["world_id"]]==split
            else:
                world_to_split[r["world_id"]]=split
            assert r["variant_type"] in VARIANTS
            assert r["language_pair"] in ("vi-vi","en-en","vi-en","en-vi")
            assert r["messages"][2]["content"]==r["answer"]
            assert r["question"] in r["messages"][1]["content"]
            ev={e["id"]:e for e in r["evidence"]}
            assert len(ev)==len(r["evidence"])
            assert set(r["evidence_ids"])<=set(ev)
            for cited in r["evidence_ids"]:
                assert f"[{cited}]" in r["messages"][1]["content"]
                assert f"[{cited}]" in r["answer"]
                citations+=1
            program=r["program"]
            if program is not None:
                assert r["answerability"]=="answerable"
                expected=eval_expr(program["expression"],program["operands"])
                assert math.isfinite(expected)
                assert abs(expected-program["result"]) < 0.0000011
                numerical+=1
            else:
                assert r["answerability"]=="insufficient"
            if r["variant_type"]=="cross_company_distractors":
                foreign=[d for d in r["evidence"] if d["owner_world_id"]!=r["world_id"]]
                target=[d for d in r["evidence"] if d["owner_world_id"]==r["world_id"]]
                assert len(foreign)==2 and target
                assert all(d["id"] not in r["evidence_ids"] for d in foreign)
                assert all(d["owner_company"] in r["messages"][1]["content"] for d in foreign)
                foreign_checked+=1
            if r["variant_type"]=="missing_target_evidence":
                assert program is None
                target=[d for d in r["evidence"] if d["owner_world_id"]==r["world_id"]]
                foreign=[d for d in r["evidence"] if d["owner_world_id"]!=r["world_id"]]
                assert [d["id"] for d in target]==["IN25"]
                assert len(foreign)==2
                assert r["evidence_ids"]==["IN25"]
                assert r["source"]=="controlled_robustness_augmentation"
                missing_checked+=1
            byworld[r["world_id"]].append(r)
    for world,rows in byworld.items():
        assert len(rows)==18
        typ=Counter(r["variant_type"] for r in rows)
        assert typ=={"m2_gold_context":8,"cross_company_distractors":8,"missing_target_evidence":2}
        assert len({r["language_pair"] for r in rows})==1
        assert len({r["sector"] for r in rows})==1
        assert len({r["split"] for r in rows})==1
    expected_lang=worlds*18//4
    languages=Counter(r["language_pair"] for r in allrows)
    assert sorted(languages.values())==[expected_lang]*4
    sectors=Counter(r["sector"] for r in allrows)
    assert sorted(sectors.values())==[expected_lang]*4
    return {
        "rows":len(allrows),
        "worlds":len(byworld),
        "splits":{key:len(value) for key,value in splits.items()},
        "variants":dict(Counter(r["variant_type"] for r in allrows)),
        "answerability":dict(Counter(r["answerability"] for r in allrows)),
        "language_pairs":dict(sorted(languages.items())),
        "sectors":dict(sorted(sectors.items())),
        "numeric_program_checks":numerical,
        "citation_checks":citations,
        "cross_company_checked":foreign_checked,
        "missing_target_checked":missing_checked,
        "split_leakage":0,
        "expert_review":"NOT DONE",
        "out_of_template_transfer":"NOT ESTABLISHED",
    }


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",default="sft/m3/outputs")
    p.add_argument("--worlds",type=int,default=200)
    args=p.parse_args()
    print(json.dumps(validate(args.root,args.worlds),indent=2,ensure_ascii=False))
