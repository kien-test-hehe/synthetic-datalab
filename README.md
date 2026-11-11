# Synthetic DataLab — FinancialDocLab v0.1

Two **strictly separated** pipelines:

1. **Real eval only:** FinQA, FinanceBench, TAT-QA, TAT-DQA, and separately permission-reviewed financial reports. Do not train, distill, optimize DPO/GRPO, or mine SFT examples from real evaluation docs, questions, answers, or model traces.
2. **Synthetic SFT only:** entirely fictional financial worlds, synthetic evidence snippets, executable arithmetic solutions, and local model training examples.

The generator in `src/generate_sft.py` uses only the Python standard library. All data are synthetic and automatically verified. It is a **seed** generator, not IFRS/VAS-complete software.

```bash
python -m unittest discover -s tests -v
python -m src.generate_sft --worlds 100 --seed 42 --out data
```

Outputs are `data/synthetic_train.jsonl`, `data/synthetic_dev.jsonl`, `data/synthetic_test.jsonl`; split at the fictional-world level to avoid leakage.

See `docs/EVAL_SOURCES.md`, `docs/EVAL_QA_PROMPT.md`, and `docs/SFT_PLAN.md` for license-aware evaluation, prompts, curriculum and safeguards.
