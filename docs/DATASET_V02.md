# FinancialDocLab v0.2 — offline-first, NO LLM API required

## Hard isolation

**REAL EVAL ONLY:** Published FinanceBench, FinQA, TAT-QA questions and original answers are never used for SFT, DPO, GRPO, distillation, or synthetic-world generation.

**SYNTHETIC ONLY:** A deterministic financial-world simulator and rule-based QA generator create fictional companies with verifiable financial arithmetic. No original company reports, questions, or annotations are imported into the synthetic corpus.

## Real evaluation sources and original labels

- FinanceBench 150 official open-source QAs, **CC BY-NC 4.0**, source: https://huggingface.co/datasets/PatronusAI/financebench — 150 official QA/evidence records are vendored *for evaluation only* in `eval/financebench/part_01.jsonl` through `part_03.jsonl` (50 per file).
- FinQA original `test.json`, **CC BY 4.0**, https://github.com/czyssrs/FinQA/tree/main/dataset
- TAT-QA original `tatqa_dataset_test_gold.json`, **CC BY 4.0**, https://github.com/NExTplusplus/TAT-QA/tree/master/dataset_raw

Dataset license != rights to each upstream company PDF. Attribution required. Public model pretraining may contain released questions: mark possible contamination.

The bundled **local release archive** `financialdoclab_v02.zip` (shared in the conversation) includes the full Python `src/import_eval.py` script that downloads the original FinQA and TAT-QA source files and produces a balanced 150+150+150 evaluation-only sample. Original gold labels remain unchanged. The sandbox cannot directly fetch the two large files today; do not claim their samples have been imported yet.

## Synthetic SFT (local archive)

The full standalone local release archive contains `src/build_balanced.py`, 11,520 generated JSONL examples and tests. Run:

```bash
python -m unittest discover -s tests -v
python -m src.build_balanced --worlds 480 --seed 42 --out data_balanced
python -m src.import_eval --limit-per-source 150 --seed 42 --out real_eval
```

Breakdown of 11,520 synthetic samples:
- world disjoint split: **train 9,216 / dev 1,152 / test 1,152**
- **6 equal task groups**: Income, Balance, Cash Flow, Cross-Statement, Multi-Document and Robustness
- **24 equally sized task types** (four in every group)
- **4 equal company sectors**: manufacturing, retail, logistics, software
- **4 equal language pairs**: vi→vi, en→en, vi→en, en→vi
- 4/24 question types require abstaining because missing or conflicting information.

Deterministic ledger invariants: assets=liabilities+equity, cash roll-forward, intersegment elimination. Income statement, working-capital and cash-flow facts are consistent under declared simplifications.

**Limitations:** Seed curriculum has only 24 fixed programs, so accuracy can reflect pattern memorization. It is not a complete IFRS/VAS model, does not yet render PDFs, and does not demonstrate generalization to unseen financial reports. Use document-disjoint real QA and a fresh benchmark to validate transfer before treating SFT as successful.
