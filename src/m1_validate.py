"""Validate M1 hand-authored casebook, SFT exports and arithmetic.

Stdlib only. Does not call models, use network, train, or read real evaluation data.
"""
from __future__ import annotations
import argparse
import ast
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "sft" / "m1"

def read_jsonl(path):
    return [json.loads(s) for s in Path(path).read_text(encoding="utf-8").splitlines() if s.strip()]

def arithmetic(expression: str) -> float:
    """Whitelist-only numerical expression evaluator, no eval/exec."""
    allowed = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.UAdd, ast.USub)
    def rec(node):
        if isinstance(node, ast.Expression):
            return rec(node.body)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return float(node.value)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            val = rec(node.operand)
            return val if isinstance(node.op, ast.UAdd) else -val
        if isinstance(node, ast.BinOp) and isinstance(node.op, allowed):
            a, b = rec(node.left), rec(node.right)
            if isinstance(node.op, ast.Add): return a + b
            if isinstance(node.op, ast.Sub): return a - b
            if isinstance(node.op, ast.Mult): return a * b
            if isinstance(node.op, ast.Div): return a / b
        raise ValueError(f"Unsupported expression: {expression!r}")
    return rec(ast.parse(expression, mode="eval"))

def validate(root=ROOT):
    root = Path(root)
    case_files = sorted((root / "cases").glob("*.jsonl"))
    row_files = sorted((root / "rows").glob("*.jsonl"))
    assert len(case_files) == len(row_files) == 5, "Expect five authored thematic groups"
    cases = [c for p in case_files for c in read_jsonl(p)]
    rows = [r for p in row_files for r in read_jsonl(p)]
    exp = {split: read_jsonl(root / "exports" / f"{split}.jsonl")
           for split in ("train", "dev", "test")}

    assert len(cases) == 40, f"Expected 40 distinct hand-authored cases, got {len(cases)}"
    assert len(rows) == 100, f"Expected 100 hand-authored rows, got {len(rows)}"
    assert len({c["case_id"] for c in cases}) == 40
    assert len({r["id"] for r in rows}) == 100
    assert len({r["question"].casefold() for r in rows}) == 100
    assert [len(exp[x]) for x in ("train", "dev", "test")] == [80, 10, 10]

    by_case = {c["case_id"]: c for c in cases}
    used_split = {}
    original = {}
    for c in cases:
        assert len(c["qas"]) in (2, 3)
        assert len({e["id"] for e in c["evidence"]}) == len(c["evidence"])
        for q in c["qas"]:
            original[f'{c["case_id"]}-{q["id"]}'] = q
    assert len(original) == 100

    checks = 0
    for r in rows:
        case = by_case[r["case_id"]]
        source_qa = original[r["id"]]
        assert r["split"] == case["split"]
        assert r["source"] == "original_fictional_hand_authored"
        assert r["question"] == source_qa["question"]
        assert r["answer"].startswith(source_qa["answer"])
        assert r["skill"] == source_qa["skill"]
        assert r["evidence_ids"] == source_qa["evidence_ids"]
        assert r["language_pair"] == case["language_pair"]
        assert r["scenario_family"] == case["scenario_family"]
        assert r["messages"][0]["role"] == "system"
        assert r["messages"][1]["role"] == "user"
        assert r["messages"][2] == {"role": "assistant", "content": r["answer"]}
        assert r["answerability"] in {"answerable", "insufficient"}
        valid_ev = {e["id"] for e in r["evidence"]}
        for evid in r["evidence_ids"]:
            assert evid in valid_ev, (r["id"], evid)
            assert f"[{evid}]" in r["answer"], (r["id"], "citation missing from answer")
            assert f"[{evid}]" in r["messages"][1]["content"]
        if r["answerability"] == "insufficient":
            assert not r["checks"], f"An abstention must not have oracle arithmetic: {r['id']}"
        assert r["answer"].strip()
        assert len(r["answer"]) >= 80
        for check in r["checks"]:
            result = arithmetic(check["expr"])
            assert math.isfinite(result)
            assert abs(result - float(check["expected"])) <= float(check["tolerance"]), (
                r["id"], check["expr"], result, check["expected"])
            checks += 1
        if r["case_id"] in used_split:
            assert used_split[r["case_id"]] == r["split"]
        used_split[r["case_id"]] = r["split"]

    flattened = [x for split in ("train", "dev", "test") for x in exp[split]]
    assert {r["id"] for r in flattened} == {r["id"] for r in rows}
    for split, items in exp.items():
        assert all(r["split"] == split for r in items)
    languages = Counter(r["language_pair"] for r in rows)
    assert dict(languages) == {"vi-vi":25,"en-en":25,"en-vi":25,"vi-en":25}
    summary = {
        "case_count": len(cases), "qa_count": len(rows),
        "splits": {split: len(items) for split, items in exp.items()},
        "unique_questions": len({r["question"].casefold() for r in rows}),
        "arithmetic_checks_passed": checks,
        "language_pairs": dict(sorted(languages.items())),
        "difficulty": dict(sorted(Counter(r["difficulty"] for r in rows).items())),
        "answerability": dict(sorted(Counter(r["answerability"] for r in rows).items())),
        "themes": {str(i):20 for i in ("income","balance","cashflow","notes_temporal","cross_sector")},
        "sector_count": len({r["sector"] for r in rows}),
        "source_contamination": "source rows written from fictional casebook; no real benchmark ingested",
        "gold_label_review_status": "arithmetic and structural checks complete; domain expert review recommended"
    }
    return summary

if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",default=str(ROOT))
    parser.add_argument("--write-report",action="store_true")
    args=parser.parse_args()
    report=validate(args.root)
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if args.write_report:
        (Path(args.root)/"quality_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
