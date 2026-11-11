# M1 — 40 individually authored financial cases, 100 SFT rows

## Why these are not template-generated rows

Each case (40 total) has uniquely written fictional financial disclosures and a particular financial reasoning challenge. Every QA (100 total) has its own question, evidence references, worked explanation and optional arithmetic program. There is **no loop that invents new finance facts or substitutes random numbers into a question template**.

The \`rows/*.jsonl\` and \`exports/*.jsonl\` files are materialized copies of these authored questions with in-context evidence and assistant citations. Scripted verification and serialization are allowed, but the financial content has been authored case by case.

## Current distribution

| Split | Cases | Questions |
|---|---:|---:|
| train | 32 | 80 |
| dev | 4 | 10 |
| test | 4 | 10 |
| total | 40 | 100 |

Five thematic families, exactly 20 QA each:
1. \`01_income\`: revenue, margins, mix, recognition, FX, one-offs.
2. \`02_balance\`: liquidity, leverage, receivables, debt maturity, basic/diluted EPS.
3. \`03_cashflow\`: CFO reconciliation, working capital, cash vs earnings, capex/FCF, FX effect.
4. \`04_notes_temporal\`: accounting estimates, restatement, consolidation, acquisitions, covenants and contingencies.
5. \`05_cross_sector\`: banking, insurance, real estate, capitalized R&D, energy, ESG and version conflicts.

Four language paths (25 QA each): \`vi-vi\`, \`en-en\`, \`en-vi\`, \`vi-en\`. First component is the evidence language; second is the question/answer language.

Answerability: 81 supported-answer rows, 19 insufficient-evidence/unsupported-claim rows.

Difficulty: L2=12, L3=50, L4=33, L5=5. 114 arithmetic assertions are supplied with tolerances and validated against a safe numerical expression interpreter.

## Row format

- \`id, case_id, split, source, scenario_family, sector\`
- \`language_pair, skill, difficulty, answerability\`
- \`accounting_assumptions\`: simplify and limit all accounting inferences
- \`evidence\`: list of independently labeled synthetic notes/financial statement excerpts
- \`question, answer, evidence_ids, checks\`
- \`messages\`: [system, user with all evidence blocks, assistant with worked answer + citations]

The assistant output is explicitly grounded in evidence IDs like \`[i23]\`, for supervised generation of grounded, concise written solutions.

## Validation

Run: \`python -m src.m1_validate --write-report\`

Checks:
- 40 cases and 100 unique IDs/questions;
- source QA content matches materialized rows;
- every evidence ID exists, is in the user prompt, and is cited in the assistant answer;
- math expressions use only +, -, *, / and parentheses, and match intended numeric result;
- train/dev/test have zero shared fictional company cases;
- exports exactly match the complete 100-row set;
- language and family distribution.

**Not automatically verified:** complex accounting judgments, empirical domain transfer, model behavior, or expert signoff.

## Evaluation etiquette

Do not fine-tune on dev/test or reuse original public FinanceBench/FinQA/TAT-QA labels as SFT. Do not tune on the final real-world evaluation set. Before training, review cases for accounting logic, authoring bias, and realistic financial language; broaden weak areas, especially long-context and visual document interpretation.
