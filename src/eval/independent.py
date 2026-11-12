"""Validate and export hand-authored, evaluation-only fictional cases.

The authored training builder and SFT arms never consume this directory.
Exact case, question, and evidence-text leakage is checked against the pinned
10K authored snapshot and legacy dev/test; this is not semantic OOD proof.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

from src.authored_export import read_jsonl, normalized_question
from src.m1_validate import arithmetic
from src.m4.experiments import allowed_source, load_authored
from src.financial_units import normalize_oracle

SOURCE="independent_fictional_evaluation_only"
FROZEN_V1={
    "dev":{"rows":500,"cases":68,"sha256":"a26de9d4903b87d8821396b85163a5b68f1c4d87fcfb7ef52015283317677499"},
    "test":{"rows":1000,"cases":134,"sha256":"40ce1a95a9505c07276a41e21ba5baf1f7fa29db85ec584659551cef60c34de3"},
}

def validate_frozen_v1(counts):
    for split,expected in FROZEN_V1.items():
        for field,value in expected.items():
            if counts[split][field]!=value:
                raise ValueError(f"Independent v1 changed: {split}.{field}; version the benchmark explicitly")


def evidence_hash(evidence):
    return hashlib.sha256(json.dumps(sorted(normalized_question(e["text"]) for e in evidence),ensure_ascii=False).encode()).hexdigest()

def build(cases_path="evaluation/independent/cases.jsonl",authored_root="sft/authored/exports",out="evaluation/independent/exports"):
    authored,manifest=load_authored(authored_root)
    old=[r for split in authored.values() for r in split]
    forbidden_ids={r["id"] for r in old}
    forbidden_cases={r["case_id"] for r in old}
    forbidden_questions={normalized_question(r["question"]) for r in old}
    forbidden_contexts={evidence_hash(r["evidence"]) for r in old}
    forbidden_evidence={normalized_question(e["text"]) for r in old for e in r["evidence"]}
    rows=[];seen_cases=set();seen_contexts=set();seen_questions=set();seen_ids=set();seen_evidence={}
    cases_path=Path(cases_path)
    # The original pilot remains unchanged; new batches live alongside it.
    paths=[cases_path]+sorted(cases_path.parent.glob("batches/*.jsonl")) if cases_path.name=="cases.jsonl" else [cases_path]
    cases=[c for path in paths for c in read_jsonl(path)]
    for case in cases:
        cid=case["case_id"];split=case["split"]
        assert cid.startswith("IE-") and cid not in forbidden_cases|seen_cases
        assert split in ("dev","test")
        assert case["language_pair"] in ("vi-vi","en-en","vi-en","en-vi")
        seen_cases.add(cid)
        evidence=case["evidence"];ids={e["id"] for e in evidence}
        assert len(ids)==len(evidence)>=2
        context=evidence_hash(evidence)
        assert context not in forbidden_contexts|seen_contexts
        assert not ({normalized_question(e["text"]) for e in evidence}&forbidden_evidence)
        seen_contexts.add(context)
        for e in evidence:
            key=normalized_question(e["text"])
            previous=seen_evidence.setdefault(key, (split,cid))
            assert previous==(split,cid), (cid, "duplicate evaluation evidence", previous)
        tags=case.get("adversarial_tags",["legacy_pilot"]) 
        assert tags and all(isinstance(t,str) and t.strip() for t in tags)
        for q in case["qas"]:
            rid=cid+"-"+q["id"];question=normalized_question(q["question"])
            assert rid not in forbidden_ids|seen_ids
            assert question not in forbidden_questions|seen_questions
            seen_ids.add(rid);seen_questions.add(question)
            cites=q["evidence_ids"]
            assert cites and len(cites)==len(set(cites)) and set(cites)<=ids
            oracle=normalize_oracle(q["oracle"],rid)
            assert oracle["kind"] in ("numeric","qualitative","insufficient")
            if oracle["kind"]=="numeric":
                assert q["checks"] and oracle["unit"]
                for expr,expected in q["checks"]:
                    assert math.isclose(arithmetic(expr),expected,rel_tol=1e-8,abs_tol=1e-8),rid
                assert math.isclose(q["checks"][-1][1],oracle["value"],rel_tol=1e-8,abs_tol=1e-8),rid
            else:
                assert not q["checks"]
            vi=case["language_pair"].endswith("-vi")
            user=case["assumptions"]+"\n\n"+"\n\n".join("["+e["id"]+"] "+e["text"] for e in evidence)+"\n\n"+q["question"]
            system="Chỉ trả lời từ bằng chứng giả định; giải thích và dẫn ID, không suy diễn khi thiếu dữ liệu." if vi else "Answer only from the fictional evidence. Explain, cite evidence IDs, and abstain if insufficient."
            answer=q["answer"]+"\nEvidence: "+" ".join("["+c+"]" for c in cites)
            row={"id":rid,"case_id":cid,"split":split,"category":case["category"],"language_pair":case["language_pair"],
                 "source":SOURCE,"source_type":"fully_synthetic_only","variant_type":"independent_evaluation",
                 "accounting_assumptions":case["assumptions"],"evidence":evidence,"question":q["question"],
                 "adversarial_tags":q.get("adversarial_tags",tags),
                 "answer":answer,"oracle":oracle,"checks":q["checks"],"evidence_ids":cites,
                 "answerability":"insufficient" if oracle["kind"]=="insufficient" else "answerable",
                 "messages":[{"role":"system","content":system},{"role":"user","content":user},{"role":"assistant","content":answer}]}
            assert not allowed_source(row)
            rows.append(row)
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    counts={}
    for split in ("dev","test"):
        selected=[r for r in rows if r["split"]==split]
        path=out/f"{split}.jsonl"
        path.write_text("".join(json.dumps(r,ensure_ascii=False,sort_keys=True)+"\n" for r in selected),encoding="utf-8")
        counts[split]={"rows":len(selected),"cases":len({r["case_id"] for r in selected}),"oracle_kinds":dict(Counter(r["oracle"]["kind"] for r in selected)),"sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
    assert all(counts[s]["rows"]>0 for s in counts)
    frozen=cases_path.name=="cases.jsonl"
    if frozen:
        validate_frozen_v1(counts)
    report={"benchmark_version":"independent-v1" if frozen else "unfrozen-custom","source":SOURCE,"splits":counts,"authored_train_sha256":manifest["splits"]["train"]["sha256"],
            "casebook_sha256":hashlib.sha256(cases_path.read_bytes()).hexdigest(),
            "casebook_files":{str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in paths},
            "target":{"dev":500,"test":1000},
            "remaining":{s:max(0,n-counts[s]["rows"]) for s,n in (("dev",500),("test",1000))},
            "categories":dict(Counter(r["category"] for r in rows)),
            "languages":dict(Counter(r["language_pair"] for r in rows)),
            "adversarial_tags":dict(Counter(t for r in rows for t in r["adversarial_tags"])),
            "exact_leakage_checks":"pass","limitations":["Fictional benchmark, not representative of all real-world finance questions.","No exact question, case or evidence overlap with authored corpus; conceptual skill overlap possible.","No expert adjudication or model evaluation performed."]}
    (out/"manifest.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--cases",default="evaluation/independent/cases.jsonl")
    p.add_argument("--authored-root",default="sft/authored/exports")
    p.add_argument("--out",default="evaluation/independent/exports")
    args=p.parse_args();print(json.dumps(build(args.cases,args.authored_root,args.out),indent=2,ensure_ascii=False))
