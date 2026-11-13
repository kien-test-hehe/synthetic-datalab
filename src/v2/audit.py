"""Candidate screening, not proof of semantic or language correctness."""
from __future__ import annotations
import argparse
import json
import re
from collections import Counter
from pathlib import Path
from src.v2.build import read,norm,write

def tokens(text):
    return set(re.findall(r"[^\W\d_]+|\d+",norm(text)))

def jaccard(a,b):
    return len(a&b)/len(a|b) if a or b else 0.0

def audit(canonical,held,out,threshold=.72):
    train=read(canonical)
    evaluation=[r for p in held for r in read(p)]
    eq=[(r["id"],tokens(r["question"])) for r in evaluation]
    candidates=[]
    for r in train:
        qt=tokens(r["question"])
        for eid,et in eq:
            score=jaccard(qt,et)
            if score>=threshold:
                candidates.append({"train_id":r["id"],"eval_id":eid,"question_jaccard":round(score,5)})
    candidates.sort(key=lambda r:(-r["question_jaccard"],r["train_id"],r["eval_id"]))
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    stats=write(out/"similarity_candidates.jsonl",candidates)
    report={"method":"question token-set Jaccard; screening only","threshold":threshold,
            "train_rows":len(train),"held_rows":len(evaluation),"candidates":stats,
            "cases":len({r["case_id"] for r in train}),
            "difficulty":dict(Counter(r["difficulty"] for r in train)),
            "review_required":True,"warning":"Similar questions may be legitimate; dissimilar wording may share semantics. Never auto-delete or declare zero semantic leakage."}
    (out/"audit_report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--canonical",default="sft/v2/exports/canonical.jsonl")
    p.add_argument("--held",nargs="+",default=["sft/authored/exports/dev.jsonl","sft/authored/exports/test.jsonl","evaluation/independent/exports/dev.jsonl","evaluation/independent/exports/test.jsonl"])
    p.add_argument("--out",default="sft/v2/exports/audit");a=p.parse_args()
    print(json.dumps(audit(a.canonical,a.held,a.out),indent=2))
