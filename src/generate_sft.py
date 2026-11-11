"""Synthetic-only financial QA generator. No real-company documents or external APIs."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

SYS = (
    "Bạn là trợ lý phân tích báo cáo tài chính. Chỉ dùng bằng chứng đã cung cấp; "
    "nêu phép tính và ID bằng chứng. Nếu thiếu dữ liệu, nói rõ không đủ thông tin."
)
EN_SYS = (
    "You are a financial statement analysis assistant. Use only the supplied "
    "evidence, show a verifiable calculation and cite evidence IDs. "
    "If information is missing, explicitly abstain."
)


def round2(x):
    return Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def split_for(world_id):
    # Split at the fictional company-world level, not at the question level.
    n = int(hashlib.sha256(world_id.encode()).hexdigest(), 16) % 10
    return "test" if n == 0 else "dev" if n == 1 else "train"


def steps_result(inputs, steps):
    env = {k: Decimal(str(v)) for k, v in inputs.items()}
    for step in steps:
        vals = [env[x] if isinstance(x, str) and x in env else Decimal(str(x)) for x in step["args"]]
        op = step["op"]
        if op == "add": val = sum(vals, Decimal(0))
        elif op == "sub": val = vals[0] - vals[1]
        elif op == "mul": val = vals[0] * vals[1]
        elif op == "div":
            if vals[1] == 0: raise ValueError("division by zero")
            val = vals[0] / vals[1]
        else: raise ValueError(f"unsupported operation: {op}")
        env[step["id"]] = val
    return round2(env[steps[-1]["id"]])


def world(seed, i):
    r = random.Random(seed * 1_000_003 + i)
    language = "vi" if i % 2 == 0 else "en"
    name = (f"Công ty Hư Cấu {i:05d}" if language == "vi" else f"Fictional Company {i:05d}")
    prior = r.randrange(600, 3800, 10)
    curr = prior * r.randrange(75, 151) // 100
    cogs = curr * r.randrange(45, 76) // 100
    opex = curr * r.randrange(8, 19) // 100
    interest = curr * r.randrange(1, 4) // 100
    pretax = curr - cogs - opex - interest
    tax = max(pretax, 0) * 20 // 100
    ni = pretax - tax
    depreciation = r.randint(15, 100)
    ar0, inv0, ap0 = r.randint(100, 320), r.randint(130, 400), r.randint(100, 270)
    dar, dinv, dap = r.randint(-30, 115), r.randint(-30, 105), r.randint(-25, 70)
    ar1, inv1, ap1 = ar0 + dar, inv0 + dinv, ap0 + dap
    cash, other_cur, short_debt = r.randint(90, 360), r.randint(20, 130), r.randint(90, 330)
    cfo = ni + depreciation - dar - dinv + dap
    return dict(id=f"fw-{seed}-{i:05d}", name=name, lang=language,
                period=2024, prior=prior, revenue=curr, cogs=cogs, ni=ni,
                depreciation=depreciation, ar0=ar0, ar1=ar1, inv0=inv0, inv1=inv1,
                ap0=ap0, ap1=ap1, cash=cash, other_cur=other_cur,
                short_debt=short_debt, cfo=cfo, sector=r.choice(["manufacturing", "retail", "logistics", "software"]))


def context(w, keys):
    vi = w["lang"] == "vi"
    titles = {
        "prior": ("Doanh thu 2023", "Revenue 2023"),
        "revenue": ("Doanh thu 2024", "Revenue 2024"),
        "cogs": ("Giá vốn 2024", "Cost of goods sold 2024"),
        "ni": ("LNST 2024", "Net income 2024"),
        "depreciation": ("Khấu hao 2024", "Depreciation 2024"),
        "ar0": ("Phải thu 2023", "Receivables 2023"),
        "ar1": ("Phải thu 2024", "Receivables 2024"),
        "inv0": ("Tồn kho 2023", "Inventory 2023"),
        "inv1": ("Tồn kho 2024", "Inventory 2024"),
        "ap0": ("Phải trả NCC 2023", "Trade payables 2023"),
        "ap1": ("Phải trả NCC 2024", "Trade payables 2024"),
        "cash": ("Tiền cuối kỳ", "Cash at year-end"),
        "other_cur": ("Tài sản ngắn hạn khác", "Other current assets"),
        "short_debt": ("Vay ngắn hạn", "Short-term debt"),
    }
    unit = "tỷ VND" if vi else "USD million"
    return [{"evidence_id": f"ev_{k}", "text": f"{titles[k][0 if vi else 1]}: {w[k]} {unit}"} for k in keys]


def make(w, task, keys, query_vi, query_en, steps, missing=None):
    vi = w["lang"] == "vi"
    evid = context(w, keys)
    inputs = {k: w[k] for k in keys}
    result = None if missing else steps_result(inputs, steps)
    unit = "%" if task in {"yoy_growth", "gross_margin"} else ("lần" if task == "current_ratio" else ("tỷ VND" if vi else "USD million"))
    if missing:
        answer = (f"Không đủ dữ liệu để tính chính xác CFO: thiếu {missing}." if vi else
                  f"Insufficient evidence to compute exact CFO: missing {missing}.")
    else:
        formula = " ; ".join(f"{s['id']}={s['op']}({', '.join(map(str,s['args']))})" for s in steps)
        labels = ", ".join(f"[{x['evidence_id']}]" for x in evid)
        answer = (f"Kết quả: {result} {unit}. Phép tính: {formula}. Bằng chứng: {labels}." if vi else
                  f"Result: {result} {unit}. Calculation: {formula}. Evidence: {labels}.")
    question = query_vi if vi else query_en
    source_text = "\n".join(f"[{e['evidence_id']}] {e['text']}" for e in evid)
    prefix = (f"Tài liệu GIẢ LẬP của {w['name']}, năm 2024. "
              "Trong ví dụ hệ số thanh toán, các khoản nêu là toàn bộ tài sản/nợ ngắn hạn. "
              "Các điều chỉnh CFO khác được giả định bằng 0 chỉ khi bài yêu cầu tính CFO đầy đủ." if vi else
              f"SYNTHETIC financial statements for {w['name']}, FY2024. "
              "For current ratio, listed components exhaust current assets and liabilities. "
              "Other CFO adjustments are zero only in the complete CFO task.")
    user = prefix + "\n" + source_text + "\n\n" + ("Câu hỏi: " if vi else "Question: ") + question
    return {
        "id": f"{w['id']}-{task}", "source": "generated_synthetic_only",
        "world_id": w["id"], "split": split_for(w["id"]), "sector": w["sector"],
        "task": task, "language": w["lang"], "difficulty": "L3" if task == "cfo" else "L2",
        "messages": [{"role": "system", "content": SYS if vi else EN_SYS},
                     {"role": "user", "content": user}, {"role": "assistant", "content": answer}],
        "evidence": evid,
        "program": {"inputs": inputs, "steps": steps, "result": str(result) if result is not None else None,
                    "result_unit": unit, "missing": missing},
    }


def samples(w):
    yield make(w, "yoy_growth", ["prior", "revenue"], "Doanh thu 2024 tăng bao nhiêu phần trăm so với 2023?",
               "What is revenue growth from 2023 to 2024?", [
        {"id": "delta", "op": "sub", "args": ["revenue", "prior"]},
        {"id": "ratio", "op": "div", "args": ["delta", "prior"]},
        {"id": "result", "op": "mul", "args": ["ratio", 100]}])
    yield make(w, "gross_margin", ["revenue", "cogs"], "Biên lợi nhuận gộp 2024 là bao nhiêu phần trăm?",
               "What is the 2024 gross profit margin?", [
        {"id": "gross", "op": "sub", "args": ["revenue", "cogs"]},
        {"id": "ratio", "op": "div", "args": ["gross", "revenue"]},
        {"id": "result", "op": "mul", "args": ["ratio", 100]}])
    yield make(w, "current_ratio", ["cash", "ar1", "inv1", "other_cur", "ap1", "short_debt"],
               "Hệ số thanh toán hiện hành cuối năm 2024 là bao nhiêu lần?",
               "What is the 2024 year-end current ratio?", [
        {"id": "assets", "op": "add", "args": ["cash", "ar1", "inv1", "other_cur"]},
        {"id": "liabilities", "op": "add", "args": ["ap1", "short_debt"]},
        {"id": "result", "op": "div", "args": ["assets", "liabilities"]}])
    cfo_steps = [
        {"id": "delta_ar", "op": "sub", "args": ["ar1", "ar0"]},
        {"id": "delta_inv", "op": "sub", "args": ["inv1", "inv0"]},
        {"id": "delta_ap", "op": "sub", "args": ["ap1", "ap0"]},
        {"id": "base", "op": "add", "args": ["ni", "depreciation"]},
        {"id": "step1", "op": "sub", "args": ["base", "delta_ar"]},
        {"id": "step2", "op": "sub", "args": ["step1", "delta_inv"]},
        {"id": "result", "op": "add", "args": ["step2", "delta_ap"]},
    ]
    allkeys = ["ni", "depreciation", "ar0", "ar1", "inv0", "inv1", "ap0", "ap1"]
    yield make(w, "cfo", allkeys, "Tính CFO 2024 theo phương pháp gián tiếp; giả sử không có điều chỉnh nào khác.",
               "Compute 2024 CFO using the indirect method, assuming no other adjustments.", cfo_steps)
    missing = "khấu hao" if w["lang"] == "vi" else "depreciation"
    yield make(w, "cfo_missing", [k for k in allkeys if k != "depreciation"],
               "Có đủ số liệu để tính chính xác CFO năm 2024 hay không?",
               "Is there enough information to compute exact 2024 CFO?", [], missing=missing)


def validate_record(row):
    assert row["source"] == "generated_synthetic_only"
    assert row["split"] == split_for(row["world_id"])
    assert len({x["evidence_id"] for x in row["evidence"]}) == len(row["evidence"])
    assert len(row["messages"]) == 3
    p = row["program"]
    if p["missing"] is None:
        assert str(steps_result(p["inputs"], p["steps"])) == p["result"]
        assert p["result"] in row["messages"][-1]["content"]
    else:
        assert p["result"] is None and not p["steps"]
    for k in p["inputs"]:
        assert f"ev_{k}" in [x["evidence_id"] for x in row["evidence"]]


def generate(n_worlds, seed, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    groups = {s: [] for s in ("train", "dev", "test")}
    for i in range(n_worlds):
        w = world(seed, i)
        for row in samples(w):
            validate_record(row)
            groups[row["split"]].append(row)
    for split, records in groups.items():
        with (out_dir / f"synthetic_{split}.jsonl").open("w", encoding="utf-8") as f:
            for row in records:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return {k: len(v) for k, v in groups.items()}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--worlds", type=int, default=100)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="data")
    a = ap.parse_args()
    print(generate(a.worlds, a.seed, a.out))
