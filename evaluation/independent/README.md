# Independent fictional financial benchmark (M6)

Evaluation only. Original 60-QA pilot is preserved in cases.jsonl. Additional individually authored cases are in batches/. Never include this directory in SFT or augmentation. Target: 500 dev / 1,000 test; progress is recorded in exports/manifest.json.

## Build and run local baseline

```bash
python -m src.authored_export
python -m src.eval.independent
curl --noproxy '*' http://127.0.0.1:11434/api/tags
cp evaluation/independent/models.example.json models.local.json
# Edit names, exact digests and untouched checkpoint/quantization attestations.
python -m src.eval.baseline_matrix --models models.local.json --output evaluation/results/baseline_dev_v1
```

Use locally installed original, unadapted instruction checkpoints (e.g. your chosen small Qwen variants); exact Ollama tags vary by installation. The matrix never pulls models or calls remote inference. A digest pins the installed artifact, not its training history. Use a new output directory for each run. For a smoke test add --limit 6 on dev only. Freeze settings and dataset before test; add --split test --unlock-test to run all test rows. Do not choose hyperparameters on test. Same prompt, data and decoding settings are required for before/after comparison via src.eval.compare.

Automatic numeric, unit, abstention and exact citation checks are proxies. Qualitative and narrative correctness require human review. Exact leakage checks are not proof of semantic or pretraining independence. No measured Qwen results until a real local run completes.
