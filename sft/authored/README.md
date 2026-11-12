# Financial-SFT-Authored — independently written training data

This directory contains the expanding **authored-only** SFT corpus. Do not count M2/M3 programmatically generated examples toward the 10,000 authored training-row target.

## Progress as of 2026-11-12

| Origin | Cases | Train | Dev | Test | Total |
|---|---:|---:|---:|---:|---:|
| M1 (sft/m1) | 40 | 80 | 10 | 10 | 100 |
| M4 (sft/m4) | 20 | 32 | 4 | 4 | 40 |
| batch_005 | 48 | 100 | 0 | 0 | 100 |
| batch_006 | 40 | 80 | 0 | 0 | 80 |
| Total | 148 | 292 | 14 | 14 | 320 |

**Target:** 10,000 training rows; **9,708 remaining**. All newly authored rows have individually composed questions, fictional evidence, assumptions and written solutions. Shared context is intentional within each case, but questions are distinct; code only serializes and validates.

### New batch coverage

- Batch 005: valuation and corporate finance; banking, insurance and investment funds; acquisition, consolidation, accounting policies; multi-document and cross-language questions.
- Batch 006: audit and going concern; liquidity and cash-flow bridges; operating performance; financial notes, tax, asset recognition; cross-company, version and scope reasoning.
- 180 new QA, 88 cases, 302 evidence blocks. 45 new rows per language pair.
- New rows: 114 numeric, 37 qualitative, 29 insufficient-evidence. 124 arithmetic assertions checked.
- 320 unique normalized questions; lexical screening threshold Jaccard >= 0.60 found no pairs involving the new rows. This does not establish full semantic novelty.

## Build / download

```bash
python -m unittest discover -s tests -v
python -m src.authored_export
```

The output `sft/authored/exports/train.jsonl` contains 292 authored-only SFT examples. Dev/test retain the original 14 rows each; do not train on them. `manifest.json` records source counts, dataset hashes, checks and remaining target. GitHub Actions publishes `financial-sft-authored-only` as a ZIP artifact (30-day retention).

The original casebooks are committed; exported JSONL can always be rebuilt offline. The old M4 experimental arms remain frozen; the new authored-only export is a separate dataset and does not silently alter those experiments.

## Authoring policy

1. Write the scenario, disclosure facts, assumptions, question and worked answer individually; do not substitute numbers in question templates or use the generated M2/M3 corpus as supervision.
2. Use only fictional companies and facts. No public benchmark, corporate report or model output from real evaluation enters the authored corpus.
3. Include multiple evidence blocks, irrelevant or conflicting facts when appropriate; numerical rows include explicit independently specified oracles and verified arithmetic; unsupported questions require explicit abstention.
4. Keep case IDs and scenario names unique, preserve prior evaluation sets, and audit overlap and near-duplicates.
5. Add new casebooks under a new batch directory; the exporter does not generate examples.

## Limitations

Not 10,000 rows yet. These are synthetic, simplified educational examples, not expert-reviewed accounting statements or complete IFRS/VAS implementations. Automated arithmetic, evidence ID and lexical checks are not proof of financial correctness, semantic diversity or learning gain. The current authored holdout is small, and later training cases may overlap broad financial concepts; do not describe it as a strict unseen-topic test. Long-document and visual reasoning are still underrepresented. No actual SFT or model accuracy improvement has been measured.
