# Independent fictional financial benchmark (M6)

Evaluation only. Original 60-QA pilot is preserved in cases.jsonl. Additional individually authored cases are in batches/. Never include this directory in SFT or augmentation. Version 1 is complete and pinned by split count and SHA-256 in src/eval/independent.py. Any future edits require explicit benchmark versioning.

| Split | Cases | QA | Numeric | Qualitative | Insufficient |
|---|---:|---:|---:|---:|---:|
| Dev | 68 | 500 | 346 | 94 | 60 |
| Test | 134 | 1,000 | 696 | 194 | 110 |
| Total | 202 | 1,500 | 1,042 | 288 | 170 |

All 1,440 additions were individually authored rather than instantiated from a programmatic QA generator. Questions in the same case are correlated. Adversarial tags indicate case-level coverage unless a QA overrides them, not a verified per-question difficulty label. Language pairs are declared metadata, not an independently audited language classification. Full supplied evidence with distractors evaluates answer generation/grounding, not retrieval recall. Exact overlap checks are not semantic independence guarantees.

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

## Frozen v1 checksums

- Dev: `a26de9d4903b87d8821396b85163a5b68f1c4d87fcfb7ef52015283317677499`
- Test: `40ce1a95a9505c07276a41e21ba5baf1f7fa29db85ec584659551cef60c34de3`
- Authored train at validation: `e19ffd2ffdefedf8a7fd7f932f2015106feb92fa03c800724f82693c85f10c5e`

CI validation of the full casebook: https://github.com/kien-test-hehe/synthetic-datalab/actions/runs/43218943023
