"""Serialize and verify individually authored financial cases ONLY.

No financial facts/questions/answers are generated. Real benchmark and simulated
M2/M3 files are never read. Preserve the existing M1/M4 evaluation splits.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path

from src.m1_validate import arithmetic
from src.m4.authored import materialize as materialize_m4

SOURCE = "original_fictional_hand_authored"
SPLITS = ("train", "dev", "test")

def read_jsonl(path):
    return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]

def normalized_question(text):
    return " ".join(unicodedata.normalize("NFKC",text).casefold().split())

def words(text):
    return {x for x in re.findall(r"\w+", normalized_question(text), re.UNICODE) if len(x)>2}

def materialize_batch(folder):
    folder=Path(folder)
    rows=[];case_ids=set();families=set();checks=0
    for path in sorted((folder/"cases").glob("*.jsonl")):
        for c in read_jsonl(path):
            assert c["case_id"] not in case_ids
            assert c["scenario_family"] not in families
            case_ids.add(c["case_id"]);families.add(c["scenario_family"])
            assert c["split"]=="train", "New authoring batches must preserve frozen eval"
            evidence={e["id"]:e["text"] for e in c["evidence"]}
            assert len(evidence)==len(c["evidence"])>=2
            assert c["language_pair"] in ("vi-vi","en-en","vi-en","en-vi")
            vi=c["language_pair"].endswith("-vi")
            system=("Chỉ phân tích bằng chứng tài chính hư cấu được cung cấp. Giải thích phương pháp, nêu kết quả và đơn vị nếu có, dẫn ID bằng chứng, từ chối suy diễn khi thiếu dữ liệu."
                    if vi else "Analyze only the supplied fictional financial evidence. Explain your reasoning, give the requested result and unit if applicable, cite evidence IDs, and abstain when evidence is insufficient.")
            for q in c["qas"]:
                assert q["question"].strip() and q["answer"].strip()
                assert q["evidence_ids"] and set(q["evidence_ids"])<=set(evidence)
                assert len(set(q["evidence_ids"]))==len(q["evidence_ids"])
                oracle=q["oracle"]
                assert oracle["kind"] in ("numeric","qualitative","insufficient")
                for expr,expected in q["checks"]:
                    actual=arithmetic(expr)
                    assert math.isfinite(actual) and math.isclose(actual,expected,rel_tol=1e-8,abs_tol=1e-8),(c["case_id"],q["id"],expr,actual,expected)
                    checks+=1
                if oracle["kind"]=="numeric":
                    assert q["checks"] and oracle["unit"]
                    assert math.isclose(oracle["value"],q["checks"][-1][1],rel_tol=1e-8,abs_tol=1e-8)
                if oracle["kind"]=="insufficient":
                    assert not q["checks"]
                user=("Tình huống GIẢ LẬP. Giả định: " if vi else "FICTIONAL scenario. Assumptions: ")+c["assumptions"]
                user+="\n\n"+"\n\n".join(f"[{k}] {v}" for k,v in evidence.items())
                user+=("\n\nCâu hỏi: " if vi else "\n\nQuestion: ")+q["question"]
                answer=q["answer"]+"\n"+("Bằng chứng: " if vi else "Evidence: ")+" ".join(f"[{e}]" for e in q["evidence_ids"])
                rows.append({
                    "id":c["case_id"]+"-"+q["id"],"case_id":c["case_id"],
                    "split":c["split"],"source":SOURCE,"source_type":"fully_synthetic_only",
                    "authored_batch":folder.name,"sector":c["sector"],
                    "scenario_family":c["scenario_family"],"language_pair":c["language_pair"],
                    "accounting_assumptions":c["assumptions"],"question":q["question"],
                    "answer":answer,"evidence":c["evidence"],"evidence_ids":q["evidence_ids"],
                    "oracle":oracle,"answerability":"insufficient" if oracle["kind"]=="insufficient" else "answerable",
                    "checks":q["checks"],"messages":[{"role":"system","content":system},
                        {"role":"user","content":user},{"role":"assistant","content":answer}]
                })
    assert rows
    return rows,{"cases":len(case_ids),"rows":len(rows),"arithmetic_checks":checks,
        "language_pairs":dict(sorted(Counter(r["language_pair"] for r in rows).items())),
        "oracle_kinds":dict(sorted(Counter(r["oracle"]["kind"] for r in rows).items()))}

def build(root="sft/authored",out=None,m1="sft/m1/exports",m4="sft/m4"):
    root=Path(root);out=Path(out) if out else root/"exports"
    out.mkdir(parents=True,exist_ok=True)
    rows=[]
    for split in SPLITS:
        for row in read_jsonl(Path(m1)/f"{split}.jsonl"):
            assert row["split"]==split and row["source"]==SOURCE
            rows.append(dict(row,authored_batch="m1"))
    m4rows,m4report=materialize_m4(m4)
    rows.extend(dict(r,authored_batch="m4") for r in m4rows)
    old_count=len(rows)
    batches={}
    for folder in sorted(root.glob("batch_*")):
        if not (folder/"cases").is_dir():continue
        new,stats=materialize_batch(folder)
        batches[folder.name]=stats
        rows.extend(new)
    assert len(rows)==len({r["id"] for r in rows})
    assert len(rows)==len({normalized_question(r["question"]) for r in rows})
    assert all(r["source"]==SOURCE for r in rows)
    case_split={}
    for row in rows:
        case=row["case_id"];split=row["split"]
        assert split in SPLITS
        assert case_split.setdefault(case,split)==split
        assert [m["role"] for m in row["messages"]]==["system","user","assistant"]
        assert row["messages"][-1]["content"]==row["answer"]
        assert row["question"] in row["messages"][1]["content"]
        ev={e["id"] for e in row["evidence"]}
        for c in row["evidence_ids"]:
            assert c in ev and f"[{c}]" in row["messages"][1]["content"] and f"[{c}]" in row["answer"]
    # Lexical screening is only a flag for review, not semantic equivalence proof.
    tokens=[words(r["question"]) for r in rows]
    near=[]
    for i in range(old_count,len(rows)):
        for j in range(i):
            a,b=tokens[i],tokens[j]
            if not a or not b:continue
            if len(a&b)/len(a|b)>=.60:
                near.append({"id1":rows[i]["id"],"id2":rows[j]["id"],
                             "jaccard":round(len(a&b)/len(a|b),4)})
    counts={}
    for split in SPLITS:
        selected=[r for r in rows if r["split"]==split]
        path=out/f"{split}.jsonl"
        path.write_text("".join(json.dumps(r,ensure_ascii=False,sort_keys=True)+"\n" for r in selected),encoding="utf-8")
        counts[split]={"rows":len(selected),"cases":len({r["case_id"] for r in selected}),
                       "sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
    report={"total_rows":len(rows),"total_cases":len(case_split),"splits":counts,
            "language_pairs":dict(sorted(Counter(r["language_pair"] for r in rows).items())),
            "new_batches":batches,"new_rows":len(rows)-old_count,
            "new_arithmetic_checks":sum(b["arithmetic_checks"] for b in batches.values()),
            "exact_duplicate_questions":0,"new_lexical_review_flags":near,
            "source":"individual authored fictional content; code only verifies and serializes",
            "target_training_rows":10000,"remaining_training_rows":max(0,10000-counts["train"]["rows"]),
            "accounting_expert_review":"not performed",
            "limitations":["Lexical deduplication does not prove semantic novelty.",
                "Case-disjoint splits do not establish strict unseen-topic evaluation.",
                "Most evidence is short, synthetic excerpts; no actual PDF pages or visual questions.",
                "No local fine-tuning or real-report accuracy improvement established."]}
    (out/"manifest.json").write_text(json.dumps(report,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",default="sft/authored");p.add_argument("--out")
    p.add_argument("--m1",default="sft/m1/exports");p.add_argument("--m4",default="sft/m4")
    a=p.parse_args();print(json.dumps(build(a.root,a.out,a.m1,a.m4),ensure_ascii=False,indent=2))
