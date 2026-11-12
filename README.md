# FinancialDocLab — financial QA datasets and local RAG research

**Key boundary:** real-company financial filings and published benchmark answers are EVALUATION-ONLY. No real evaluation documents, QA answers or retrieved evidence are used to produce synthetic SFT/DPO/GRPO data.

## Current milestones

| Milestone | Rows | Origin | Status |
|---|---:|---|---|
| M1 | 100 | 40 entirely fictional hand-authored financial cases | Merged into main |
| M2 | 1,600 | 32 hand-authored reasoning task programs, 200 programmatically simulated fictional company worlds | Merged into main |
| M3 | 14,400 | M2's same 32 programs scaled to 800 fictional worlds with source-company distractors and evidence-absent cases | PR; CI builds dataset, outputs untracked |

**Do not confuse the 14,400 rows with 14,400 independently written QAs.** M3 is an experimental evidence-robustness curriculum to test grounded reasoning, rather than a new accounting theory dataset. Validate transfer on held-out real documents and on task-program OOD splits.

## Quick start: M3 fully offline

```bash
python -m unittest discover -s tests -v
python -m src.m3.augment --worlds 800 --seed 42 --out sft/m3/outputs
python -m src.m3.validate --worlds 800 --root sft/m3/outputs
python -m src.m3.ood_split --input sft/m3/outputs --out sft/m3/ood
```

Generated outputs and model weights are gitignored; GitHub Actions uploads dataset artifacts.

## FinanceBench PDF retrieval evaluation, NOT training

```bash
python -m src.eval.financebench download-qa --out real_eval/financebench/questions.jsonl
# Review PDF rights and terms first; then explicitly acknowledge:
python -m src.eval.financebench download-pdfs --qa real_eval/financebench/questions.jsonl --acknowledge-rights
python -m pip install pymupdf
python -m src.eval.financebench parse --pdfs real_eval/financebench/pdfs
python -m src.eval.financebench index --chunks real_eval/financebench/chunks.jsonl
python -m src.eval.financebench eval --qa real_eval/financebench/questions.jsonl --db real_eval/financebench/fts.sqlite --k 10
```

For locally computed multilingual embeddings, use `src.eval.dense` with `sentence-transformers` (default: `BAAI/bge-m3`). See [M3 research guide](docs/M3_GUIDE.md).

## Non-claims

- M1/M2/M3 are simplified educational accounting scenarios, not an audited VAS/IFRS financial dataset.
- Automatic math, metadata and split checks **do not** certify natural-language financial conclusions.
- The public FinanceBench/FinQA/TAT-QA labels may already appear in base-model pretraining; do not use them for instruction training or iterative answer-label mining.
- No local model has yet been fine-tuned or benchmarked against these real PDF files in this repository.
