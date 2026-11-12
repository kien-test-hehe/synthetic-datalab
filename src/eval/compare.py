"""Matched before/after comparison for local model evaluation reports.

Reject different prompts/settings, datasets, IDs or contexts. Preserve paired
sample results. Report automated checks separately from human-reviewed answers.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

FIELDS=("kind","context","dataset_sha256","evaluated_ids","temperature","num_ctx",
        "max_tokens","max_context_chars","retrieval_k","chunk_sha256","index_sha256")
def compare(base_path, adapted_path):
    base_path=Path(base_path);adapted_path=Path(adapted_path)
    b=json.loads(base_path.with_suffix(".summary.json").read_text(encoding="utf-8"))
    a=json.loads(adapted_path.with_suffix(".summary.json").read_text(encoding="utf-8"))
    for field in FIELDS:
        if b[field]!=a[field]:raise ValueError(f"Incompatible experiment settings: {field}")
    def read(p):
        rows=[json.loads(s) for s in p.read_text(encoding="utf-8").splitlines() if s.strip()]
        if len({r["id"] for r in rows})!=len(rows):raise ValueError("Duplicate prediction IDs")
        return {r["id"]:r for r in rows}
    bm=read(base_path);am=read(adapted_path)
    if set(bm)!=set(am) or set(bm)!=set(b["evaluated_ids"]):raise ValueError("Unmatched prediction IDs")
    paired={}
    for metric in ("valid_json","numeric_correct","unit_correct","answerability_correct","auto_pass","citation_precision","citation_recall"):
        # Compare the identical set of samples that have the relevant metric.
        common=[k for k in bm if bm[k]["scores"].get(metric) is not None and am[k]["scores"].get(metric) is not None]
        if not common:
            paired[metric]={"n":0,"base":None,"adapted":None,"delta":None}
            continue
        bv=[float(bm[k]["scores"][metric]) for k in common];av=[float(am[k]["scores"][metric]) for k in common]
        paired[metric]={"n":len(common),"base":sum(bv)/len(common),"adapted":sum(av)/len(common),
                        "delta":sum(y-x for x,y in zip(bv,av))/len(common),
                        "improved":sum(y>x for x,y in zip(bv,av)),
                        "regressed":sum(y<x for x,y in zip(bv,av))}
    return {"base_model":b["model"],"adapted_model":a["model"],"matched_examples":len(bm),
            "base_errors":b["summary"]["error_count"],"adapted_errors":a["summary"]["error_count"],
            "metrics":paired,
            "warning":"Numeric/format/citation signals only. Paired metrics exclude items unscored in either run; auto_pass counts failed numeric or abstention outputs. FinanceBench answer correctness needs human/verified labels."}

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--base",required=True);p.add_argument("--adapted",required=True);p.add_argument("--out")
    args=p.parse_args();r=compare(args.base,args.adapted);s=json.dumps(r,indent=2,ensure_ascii=False)
    if args.out:Path(args.out).write_text(s+"\n",encoding="utf-8")
    print(s)
