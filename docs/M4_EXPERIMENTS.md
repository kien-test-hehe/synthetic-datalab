# M4 — original financial cases and controlled SFT experiments

## What is new

- 20 independently written fictional accounting cases; 40 original QAs (32 train, 4 dev, 4 test). The questions, facts, explanations, and oracles were composed individually, not by templates or an external model API.
- Across M1 and M4: 140 authored QA rows, including 112 train rows. M3's 14,400 programmatic rows are a different provenance class.
- 10 rows per Vietnamese/English evidence-to-answer language pair. M4 covers leases, asset impairment, deferred tax, inventory write-downs, capitalized interest, principal/agent, noncash PPE additions, discontinued operations, share compensation, pensions, FX, warranty provision, contract assets, TTM, factoring, covenants, ARR, hedge OCI, weighted-average EPS and segment profit.
- 36 arithmetic assertions checked. All assistant answers cite supplied evidence. Expert accounting review remains necessary; these are simplified educational cases.

## Build reproducible training arms

```bash
python -m unittest discover -s tests -v
python -m src.m4.authored
python -m src.m3.augment --worlds 800 --seed 42 --out sft/m3/outputs
python -m src.m3.validate --worlds 800 --root sft/m3/outputs
python -m src.m4.experiments
python -m src.m4.experiments --ood --out sft/m4/experiments_ood
```

The standard world-held-out experiment uses exactly the SAME 640 training worlds and 80+80 held-out worlds. The old separately generated M2 (200 worlds) must NOT be combined blindly with M3 (800 worlds): the same world ID can receive a different split.

| Arm | Training rows | Purpose |
|---|---:|---|
| gold_only | 5,120 | Clean gold-context baseline, from the frozen M3 train split |
| robust_size_matched | 5,120 | Same row count and task-type mix as gold_only, with controlled distractor/missing-evidence variants |
| robust_all | 11,520 | Full M3 robustness curriculum |
| authored_only | 112 | M1 + M4 independently authored examples only |
| authored_plus_gold | 5,232 | Authored + clean contexts |
| authored_plus_robust | 11,632 | Authored + full robustness curriculum |

Use common_dev (1,440) to choose settings and common_test (1,440) for final within-world-split comparisons. authored_dev/test are independent small authored sets (14 each). Never train on either.

The OOD mode excludes M1/M4 authored training data: their conceptual overlap with the 8 held-out M3 task programs has not been audited. Use its own common_dev and common_test (360 unseen-program QA), never mix modes when calculating deltas. Size-matched arms match rows and task counts, NOT necessarily token count, number of unique contexts, or semantic complexity.

## Run local model baseline and adapter

This is an evaluation CLI, not a training implementation. It invokes Ollama on loopback only. No cloud LLM APIs. The exact same model prompt and evaluation data must be used for both the base checkpoint and the model after local SFT.

```bash
python -m src.eval.model_eval --kind synthetic \
  --dataset sft/m4/experiments/common_dev.jsonl \
  --model YOUR_LOCAL_BASE_MODEL --output reports/base_dev.jsonl --limit 30
python -m src.eval.model_eval --kind synthetic \
  --dataset sft/m4/experiments/common_dev.jsonl \
  --model YOUR_LOCAL_SFT_MODEL --output reports/sft_dev.jsonl --limit 30
python -m src.eval.compare --base reports/base_dev.jsonl --adapted reports/sft_dev.jsonl
```

Remove the limit for full dev evaluation; freeze settings before the final test. Start with the same base and adapter architecture, checkpoint, tokenizer, chat template, decoding parameters and context size. Inspect input token lengths before training. Prefer completion-only loss; never silently truncate a context.

The evaluation prompt requires a structured JSON prediction with the final numeric value and unit. This measures format compliance as well as financial reasoning. Numeric oracle accuracy and valid evidence citations can be checked programmatically; explanation quality cannot. The strict auto_pass metric is only a proxy. For qualitative answers, manual financial review is required. Compare.py rejects unmatched datasets, evaluation IDs, retrieval settings and generation budgets.

## FinanceBench evaluation-only

The M3 pipeline downloads official QA and (only after checking rights) PDF files. M4 supports gold-context model evaluation from the official evidence, plus end-to-end lexical retrieval from the original PDF chunks. Neither answers nor justification annotations are included in model input.

```bash
python -m src.eval.financebench download-qa --out real_eval/financebench/questions.jsonl
python -m src.eval.model_eval --kind financebench --context gold \
  --dataset real_eval/financebench/questions.jsonl \
  --model YOUR_LOCAL_BASE_MODEL --output reports/financebench_base_gold.jsonl

# After building the PDF chunk and FTS index using docs/M3_GUIDE.md:
python -m src.eval.model_eval --kind financebench --context lexical \
  --dataset real_eval/financebench/questions.jsonl \
  --chunks real_eval/financebench/chunks.jsonl --db real_eval/financebench/fts.sqlite \
  --model YOUR_LOCAL_BASE_MODEL --output reports/financebench_base_lexical.jsonl --k 10
```

Repeat with the SFT model and manually assess financial correctness against the unchanged published labels. The runner records official answers separately in predictions for review. Citation IDs in real eval are local context IDs; citation-ID validity is NOT correct gold page recall. Report gold vs retrieved contexts separately. No model inference on real documents, embeddings, fine-tuning, expert review or measured quality improvements were performed in CI; mocked model responses are for software tests only.

## Deliverables

Generated M4 exports and prepared experiments are published as the GitHub Actions artifact `financialdoclab-m4-experiments` (30-day retention). All data are reproducible from the source with the same commands.

## M5 corrected experiment contract

Before running the experiment builder, run `python -m src.authored_export`. The builder verifies the manifest and exact 10,000/14/14 split counts. Train using `sft/m4/experiments/authored_only.jsonl`, not the raw authored export or M4 seed export. All experiment arms use JSON assistant messages; the `answer` field preserves the original authored text for traceability. `authored_verified_oracle` excludes multi-result/manual-review rows from the scalar-contract ablation; all 100 M1 rows have manual oracle annotations. Multi-result QA retain every result in the answer field and require manual review. It is not a guarantee of domain correctness. The legacy full arm remains available for ablation, not a recommendation to train before review. The official FinanceBench gold indices are zero-based and converted to physical one-based page numbers. Old dense indices need rebuilding after the content hash change. Existing dev/test are small; results remain preliminary.
