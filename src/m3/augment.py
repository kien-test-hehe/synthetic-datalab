"""M3 controlled evidence-robustness curriculum, never using real company data.

M3 deliberately separates authored reasoning *programs* (32 M2 task types)
from programmatically instantiated rows. It is NOT 14,400 hand-written QAs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import Counter
from copy import deepcopy
from pathlib import Path

from src.m2.build_m2 import generate as generate_m2
from src.m2.documents import build_documents
from src.m2.financial_world import create_world, audit_world


def _deterministic_rng(seed: int, origin_id: str, variant: str) -> random.Random:
    digest = hashlib.sha256(f"{seed}|{origin_id}|{variant}".encode()).hexdigest()
    return random.Random(int(digest[:16], 16))


def _header(row: dict) -> str:
    original = row["messages"][1]["content"]
    split_marker = "\n\n["
    if split_marker not in original:
        raise ValueError(f"Unrecognized M2 prompt shape: {row['id']}")
    return original.split(split_marker, 1)[0]


def _foreign_docs(row: dict, seed: int, index: int) -> list[dict]:
    # New, out-of-distribution fictional companies outside the main 0..worlds-1.
    sector = row["sector"]
    # A random stress-path may violate the toy ledger's positivity constraints.
    # Use deterministic rejection sampling; do NOT weaken financial identities.
    outsider = None
    for attempt in range(100):
        try:
            candidate = create_world(seed + 73 + attempt, 300000 + index, sector)
            audit_world(candidate)
        except AssertionError:
            continue
        outsider = candidate
        break
    if outsider is None:
        raise RuntimeError("Could not generate a valid distractor company world")
    lang = row["language_pair"].split("-")[0]
    lookup = build_documents(outsider, lang, (index + 2) % 3)
    # Prefer same document types and fiscal periods, but from a *different* company.
    options = [e["id"] for e in row["evidence"] if e["id"] in lookup]
    options = list(dict.fromkeys(options))
    if len(options) < 2:
        options.extend(k for k in ("IS25", "BS25", "CF25", "VN25") if k not in options)
    chosen = options[:2]
    docs = []
    for j, doc_id in enumerate(chosen):
        d = deepcopy(lookup[doc_id])
        d["id"] = f"foreign_{index}_{j}"
        d["document_id"] = f"{outsider['id']}/{doc_id}"
        d["owner_world_id"] = outsider["id"]
        d["owner_company"] = outsider["name"]
        docs.append(d)
    return docs


def _target_docs(row: dict) -> list[dict]:
    docs = deepcopy(row["evidence"])
    for doc in docs:
        doc["owner_world_id"] = row["world_id"]
        doc["owner_company"] = row["question"].split(" (", 1)[0]
    return docs


def _render_context(row: dict, documents: list[dict], seed: int, variant: str) -> str:
    rng = _deterministic_rng(seed, row["id"], variant)
    shuffled = deepcopy(documents)
    rng.shuffle(shuffled)
    lang = row["language_pair"].split("-")[0]
    intro = ("Tài liệu thuộc các doanh nghiệp GIẢ LẬP khác nhau; chỉ dùng số liệu của đúng doanh nghiệp được hỏi."
             if lang == "vi" else
             "All records concern FICTIONAL companies; use ONLY evidence belonging to the company named in the question.")
    blocks = []
    for doc in shuffled:
        blocks.append(
            f"[{doc['id']}] company={doc['owner_company']} | "
            f"document={doc['document_id']} | year={doc['fiscal_year']} | "
            f"scope={doc['statement_scope']}\n{doc['title']}\n{doc['text']}"
        )
    suffix = "Câu hỏi: " if row["language_pair"].endswith("-vi") else "Question: "
    return _header(row) + "\n" + intro + "\n\n" + "\n\n".join(blocks) + "\n\n" + suffix + row["question"]


def _add_distractors(row: dict, seed: int, index: int) -> dict:
    out = deepcopy(row)
    out["id"] = row["id"] + "__cross_company_distractors"
    out["variant_type"] = "cross_company_distractors"
    out["origin_m2_id"] = row["id"]
    out["source"] = "controlled_robustness_augmentation"
    out["authoring"] = "authored_m2_reasoning_program_plus_provenance_checked_distractors"
    out["evidence"] = _target_docs(row) + _foreign_docs(row, seed, index)
    out["messages"][1]["content"] = _render_context(row, out["evidence"], seed, out["variant_type"])
    if out["language_pair"].endswith("-vi"):
        out["answer"] = row["answer"] + " Không dùng số liệu của doanh nghiệp khác để thay cho số liệu của công ty được hỏi."
    else:
        out["answer"] = row["answer"] + " Numbers from other companies do not answer the question about this company."
    out["messages"][2]["content"] = out["answer"]
    return out


def _missing_target(row: dict, seed: int, index: int) -> dict:
    out = deepcopy(row)
    out["id"] = row["id"] + "__missing_target"
    out["variant_type"] = "missing_target_evidence"
    out["origin_m2_id"] = row["id"]
    out["source"] = "controlled_robustness_augmentation"
    out["authoring"] = "authored_m2_reasoning_program_plus_provenance_checked_absence"
    lang = row["language_pair"].split("-")[0]
    # Only general policy for the intended company, plus specific numbers from a different company.
    origin_index = int(row["world_id"].rsplit("-", 1)[1])
    w = create_world(seed, origin_index, row["sector"])
    policy = deepcopy(build_documents(w, lang)["IN25"])
    policy["owner_world_id"] = row["world_id"]
    policy["owner_company"] = w["name"]
    docs = [policy] + _foreign_docs(row, seed, index)
    out["evidence"] = docs
    out["evidence_ids"] = ["IN25"]
    out["program"] = None
    out["answerability"] = "insufficient"
    out["requirements"] = dict(out["requirements"], target_data_absent=True)
    out["messages"][1]["content"] = _render_context(row, docs, seed, out["variant_type"])
    if row["language_pair"].endswith("-vi"):
        out["answer"] = (
            "Không đủ dữ liệu để tính hay kết luận cho doanh nghiệp được hỏi. "
            "Tài liệu [IN25] chỉ mô tả chính sách chung, không chứa các chỉ tiêu cần thiết; "
            "các báo cáo có số liệu còn lại thuộc doanh nghiệp khác nên không thể dùng thay thế."
        )
    else:
        out["answer"] = (
            "Insufficient evidence to compute or establish the requested answer for the target company. "
            "The [IN25] policy note lacks the necessary target-company financial values; "
            "other numerical reports belong to a different fictional company and cannot substitute for them."
        )
    out["messages"][2]["content"] = out["answer"]
    return out


def build(worlds: int = 200, seed: int = 42, out_dir: str = "sft/m3/outputs") -> dict:
    if worlds % 20:
        raise ValueError("World count must be a multiple of 20")
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    from tempfile import TemporaryDirectory
    bysplit: dict[str, list[dict]] = {s: [] for s in ("train", "dev", "test")}
    with TemporaryDirectory() as source_folder:
        generate_m2(worlds, seed, source_folder)
        for split in bysplit:
            raw = Path(source_folder, f"m2_{split}.jsonl").read_text(encoding="utf-8").splitlines()
            byworld: dict[str, list[dict]] = {}
            for line in raw:
                x = json.loads(line)
                byworld.setdefault(x["world_id"], []).append(x)
            for widx, (world_id, rows) in enumerate(sorted(byworld.items())):
                assert len(rows) == 8
                for pos, row in enumerate(rows):
                    origin = deepcopy(row)
                    origin["variant_type"] = "m2_gold_context"
                    origin["origin_m2_id"] = row["id"]
                    bysplit[split].append(origin)
                    bysplit[split].append(_add_distractors(row, seed, widx * 8 + pos + 100000 * (0 if split == "train" else 1 if split == "dev" else 2)))
                # Exactly 2 abstention challenges per company, one from a numeric type and
                # one from an already unanswerable M2 task if present.
                numeric = next(x for x in rows if x["category"] == "working_capital")
                caution = next(x for x in rows if x["category"] == "version_scope")
                base_index = widx * 8 + 700000 * (0 if split == "train" else 1 if split == "dev" else 2)
                bysplit[split].append(_missing_target(numeric, seed, base_index))
                bysplit[split].append(_missing_target(caution, seed, base_index + 1))
    for split, rows in bysplit.items():
        with (root / f"m3_{split}.jsonl").open("w", encoding="utf-8") as fh:
            for x in rows:
                fh.write(json.dumps(x, ensure_ascii=False, sort_keys=True) + "\n")
    allrows = [r for group in bysplit.values() for r in group]
    report = {
        "dataset": "FinancialDocLab M3 structured evidence robustness curriculum",
        "worlds": worlds,
        "total_rows": len(allrows),
        "splits": {k: len(v) for k, v in bysplit.items()},
        "variant_distribution": dict(Counter(r["variant_type"] for r in allrows)),
        "language_distribution": dict(Counter(r["language_pair"] for r in allrows)),
        "sector_distribution": dict(Counter(r["sector"] for r in allrows)),
        "answerability_distribution": dict(Counter(r["answerability"] for r in allrows)),
        "provenance": "32 individually authored M2 reasoning program definitions, all instantiated/augmented programmatically; zero API calls",
        "scope": "Fictional documents only; no FinQA/FinanceBench/TAT-QA data used in SFT",
        "limitations": "Reuses M2 task programs and simulated financial worlds; no evidence of unseen-task generalization or accountant review",
        "seed": seed,
    }
    (root / "manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--worlds", type=int, default=200)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="sft/m3/outputs")
    args = ap.parse_args()
    print(json.dumps(build(args.worlds, args.seed, args.out), ensure_ascii=False, indent=2))
