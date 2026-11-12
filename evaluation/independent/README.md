# Independent fictional evaluation pilot

20 individually authored cases (8 dev, 12 test), 60 QA. Evaluation only; never include in training, validation-based training selection for test, or SFT augmentation.

Run after building the authored corpus:
```bash
python -m src.eval.independent
python -m src.eval.model_eval --kind synthetic --dataset evaluation/independent/exports/dev.jsonl --model YOUR_LOCAL_MODEL --output evaluation/results/independent_dev.jsonl
```

For test, use test.jsonl only after finalizing the model and settings. Gold arithmetic and exact citation sets are an automatic proxy. Review qualitative answers and explanation correctness manually. Exact leakage checks cover the full authored corpus, not semantic novelty or external benchmark contamination. This is a pilot, not the planned larger independent benchmark.
