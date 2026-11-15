"""Materialize 40 individually written M4 financial QA samples, with explicit numeric oracles.

Only fictional authored case files are read. No generation, real report data, or LLM API.
"""
from __future__ import annotations
import argparse
import json
import math
from collections import Counter
from pathlib import Path
from src.m1_validate import arithmetic

ROOT=Path("sft/m4")
SOURCE="original_fictional_hand_authored"

def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]

def materialize(root=ROOT):
    cases=[c for p in sorted((Path(root)/"cases").glob("*.jsonl")) for c in read_jsonl(p)]
    assert len(cases)==20
    assert len({c["case_id"] for c in cases})==20
    assert len({c["scenario_family"] for c in cases})==20
    rows=[]
    checks=0
    for c in cases:
        assert len(c["qas"])==2
        assert c["split"] in ("train","dev","test")
        evidence={e["id"]:e["text"] for e in c["evidence"]}
        assert len(evidence)==len(c["evidence"])
        assert len(evidence)>=2
        vi=c["language_pair"].endswith("-vi")
        for q in c["qas"]:
            assert q["evidence_ids"] and set(q["evidence_ids"])<=set(evidence)
            assert q["oracle"]["kind"] in ("numeric","qualitative","insufficient")
            for expr,expected in q["checks"]:
                value=arithmetic(expr)
                assert math.isfinite(value) and math.isclose(value,expected,rel_tol=1e-8,abs_tol=1e-8),(c["case_id"],q["id"],expr,value,expected)
                checks+=1
            if q["oracle"]["kind"]=="numeric":
                assert q["checks"]
                assert math.isclose(q["oracle"]["value"],q["checks"][-1][1],rel_tol=1e-8,abs_tol=1e-8)
                assert q["oracle"]["unit"]
            elif q["oracle"]["kind"]=="insufficient":
                assert not q["checks"]
            system=("Chỉ phân tích các bằng chứng tài chính hư cấu được cung cấp. Nêu phương pháp, kết quả, đơn vị và citation ID; không suy diễn ngoài bằng chứng."
                    if vi else "Analyze only the supplied fictional financial evidence. Explain the calculation or principle, state units and cite evidence IDs; abstain when unsupported.")
            user=("Tình huống GIẢ LẬP. Giả định: " if vi else "FICTIONAL case. Assumptions: ")+c["assumptions"]+"\n"
            user+="\n".join(f"[{k}] {v}" for k,v in evidence.items())
            user+=("\n\nCâu hỏi: " if vi else "\n\nQuestion: ")+q["question"]
            answer=q["answer"]+"\n"+("Bằng chứng: " if vi else "Evidence: ")+" ".join(f"[{e}]" for e in q["evidence_ids"])
            rows.append(dict(id=c["case_id"]+"-"+q["id"],case_id=c["case_id"],split=c["split"],source=SOURCE,
                source_type="fully_synthetic_only",sector=c["sector"],scenario_family=c["scenario_family"],
                language_pair=c["language_pair"],accounting_assumptions=c["assumptions"],question=q["question"],
                answer=answer,evidence=c["evidence"],evidence_ids=q["evidence_ids"],oracle=q["oracle"],
                answerability="insufficient" if q["oracle"]["kind"]=="insufficient" else "answerable",
                checks=q["checks"],messages=[{"role":"system","content":system},{"role":"user","content":user},{"role":"assistant","content":answer}]))
    assert len(rows)==40 and len({x["id"] for x in rows})==40 and len({x["question"].casefold() for x in rows})==40
    assert Counter(r["split"] for r in rows)=={"train":32,"dev":4,"test":4}
    assert Counter(r["language_pair"] for r in rows)=={"vi-vi":10,"en-en":10,"en-vi":10,"vi-en":10}
    report={"rows":len(rows),"cases":len(cases),"scenario_families":len({c["scenario_family"] for c in cases}),
            "splits":dict(Counter(r["split"] for r in rows)),"language_pairs":dict(Counter(r["language_pair"] for r in rows)),
            "oracle_kinds":dict(Counter(r["oracle"]["kind"] for r in rows)),"arithmetic_checks":checks,
            "source":"individually authored fictional cases, not template instantiations","accountant_review":"not performed"}
    return rows,report

def build(root=ROOT,out=None):
    root=Path(root)
    out=Path(out) if out else root/"exports"
    out.mkdir(parents=True,exist_ok=True)
    rows,report=materialize(root)
    for split in ("train","dev","test"):
        with (out/f"{split}.jsonl").open("w",encoding="utf-8") as f:
            for r in rows:
                if r["split"]==split:f.write(json.dumps(r,ensure_ascii=False,sort_keys=True)+"\n")
    (out/"manifest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",default=str(ROOT));p.add_argument("--out")
    args=p.parse_args();print(json.dumps(build(args.root,args.out),indent=2,ensure_ascii=False))
