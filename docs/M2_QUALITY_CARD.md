# M2 research and quality card

## What was personally authored vs generated

- **Authored**: 32 explicit financial reasoning programs, 2 Vietnamese and 2 English question phrasings for each, a bilingual explanation principle and evidence requirements per program.
- **Generated**: 200 fictional three-year accrual ledgers, period-specific documents, language-appropriate source excerpts, contextual distractors, numerical substitution, answers and balanced split assignment.
- **No LLM API** and **no real financial report** was used to create M2.

## All 8 domains have 200 QA rows

1. Earnings — revenue/gross/operating/net income ratios.
2. Cash Flow — indirect CFO, simple FCF, CFO vs earnings, cash roll-forward.
3. Working Capital — DSO, DIO, DPO with implied purchases, cash conversion cycle.
4. Liquidity — consolidated current ratio, net debt/EBITDA, EBIT interest cover, financial debt/equity.
5. Temporal — 2023–2025 comparisons, earnings, FCF and retained equity.
6. Segments — external-revenue share, segment margin, mix shift, elimination of intra-group sales.
7. Document Versions/Scope — audited vs unaudited, restated vs originally filed, parent vs consolidated.
8. Robustness — three deliberately unanswerable task types plus one cash reconciliation.

## Ledger invariants

The educational synthetic model uses net income = revenue − cost of sales − cash operating expense − depreciation − interest − tax. Cash operations use NI + depreciation − Δreceivables − Δinventory + Δtrade payables. Capital spending drives CFI and PP&E, loans and dividends drive CFF, and all assets balance liabilities plus equity. There is **no claim of IFRS/US GAAP/VAS compliance**.

## QA guarantees checked automatically

- 1,600 unique IDs, 200 disjoint worlds and 80/10/10 split.
- 32 task types evenly represented within each split.
- Four language directions and four sectors evenly represented within each split.
- Every gold evidence ID exists, occurs in the prompt, and is cited in the assistant completion.
- 1,450 whitelisted arithmetic programs evaluate to expected results and are finite.
- 600 annual accounting ledger identity checks, and reproducibility with fixed seed.
- 150 no-answer examples are explicitly marked and contain no numeric gold program.

## Limitations requiring explicit review

- Finite task bank. Repetition of the same algorithm can induce template memorization.
- Numeric/structural checks do not verify whether every narrative accounting claim is appropriate.
- Short synthetic text excerpts, not lengthy actual corporate filings; no OCR, bounding boxes, or visual table parsing.
- Year/version distortions and standalone statements are controlled examples, not full audited legal financial statements.
- Evidence sufficiency is checked within provided context, not across arbitrary outside knowledge.
- No domain-expert accounting signoff.
- No local LLM baseline or fine-tuning was executed.

## Next model experiments

Start with fixed base-model gold-context evaluations, then hold tokenizer/context settings constant in 1K–4K SFT experiments. Compare M1-only vs M2-only vs combined train, while selecting only on dev. Evaluate final transfer separately on licensed FinanceBench/FinQA/TAT-QA **never used for SFT**. Avoid using public benchmark answers for training, teacher data, DPO or GRPO.
