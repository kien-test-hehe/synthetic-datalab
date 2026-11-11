# FinancialDocLab M2 — 1,600 verified teacherless SFT examples

**Status:** Reproducible dataset release and tests. The generated JSONL files are stored as a GitHub Actions **artifact**, not committed as large binaries; the code here generates them offline. Original M1 authored cases (100 QA) remain in \`sft/m1/\` on main.

## Generate locally

Python 3.11+, standard library only; **no LLM API**.

\`\`\`bash
python -m unittest discover -s tests -v
python -m src.m2.build_m2 --worlds 200 --seed 42 --out sft/m2/outputs
python -m src.m2.validate_m2 --out sft/m2/outputs
\`\`\`

The M2 workflow also creates and uploads \`financialdoclab-m2-jsonl\` containing train/dev/test and reports. It does not train or call a model.

## Corpus (synthetic only)

- 200 **fully fictional** company worlds, financial statements for FY2023–2025, with 2–5 evidence excerpts per QA.
- 1,600 QA rows: **1,280 train / 160 dev / 160 test**, split by company-world, never by random question.
- 8 equally sized domains: earnings, cash flow, working capital, liquidity, temporal changes, segments, version/scope disambiguation, abstention/robustness (**200 each**).
- 32 reasoning programs, 50 examples each.
- 4 evidence-question language paths (VI/EN combinations), 400 each; 4 industry categories, 400 each.
- **1,450** numeric/programmed answers, **150** insufficient-evidence responses.
- Three document layouts, controlled distractors for preliminary/audited, original/restated, consolidated/standalone statements.

## Authorship provenance

A strict distinction: **32 task families and their bilingual instructions were manually designed**. The **1,600 realized rows are controlled programmatic instantiations** of those tasks using new fictional facts, varied document layouts and a deterministic financial ledger. They are **NOT** 1,600 independently hand-written answers. Each record includes \`source=controlled_programmatic_instantiation\` and its originating \`original_task_id\`.

Unlike the prior simple template dataset, M2 includes consistent cross-year three-statement ledgers, segment eliminations, multi-document reasoning, scope/version traps and explicit abstention. This still does not guarantee positive SFT transfer.

## QA & limitations

- Accounts checked: assets = liabilities + equity; CFO = NI + depreciation − ΔAR − Δinventory + ΔAP; closing cash roll-forward; retained-earnings movements.
- Numeric answers checked by whitelisted arithmetic evaluation; evidence ID and split isolation checked.
- This is **not an IFRS/VAS-complete accounting simulator**. No financial professional audit, real-company facts or benchmark evaluation has been performed.
- The 32 programs recur across all splits. Company-world holdout is NOT scenario-family holdout; test on real, completely separate reports before claiming reasoning gains.
- No scanned PDF / visual QA is included in this milestone (document layout is text/markdown excerpts).

Read \`docs/M2_QUALITY_CARD.md\` and \`docs/M2_TRAINING_GUIDE.md\`. M1 remains unchanged.
