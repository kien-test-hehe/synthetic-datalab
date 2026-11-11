# Synthetic reasoning curriculum (no real source content)

## Goal

Teach a compact post-trained model to identify financial evidence, normalize periods/scope/units, build executable arithmetic plans, reconcile statements, cite evidence and abstain when information is missing. Training data must use fictional businesses and generated facts only.

## Skills

| Stage | Subskills |
|---|---|
| L1 | Metric terminology, fiscal period, units, standalone vs consolidated |
| L2 | YoY growth, gross margin, current ratio, percent vs pp |
| L3 | Indirect CFO, working-capital adjustments, cross-statement reconciliation |
| L4 | Multi-year restatements, business segments and intra-group eliminations |
| L5 | Missing evidence, contradictions, analytical uncertainty |

## Trusted synthetic data generation

1. Deterministic Python company-world and ledger generator.
2. Constraint engine verifies accounting identities and solvability.
3. Document renderer emits evidence (tables, notes, PDFs) and IDs.
4. Program generator constructs question operations and oracle answer.
5. LLM teacher paraphrases question and renders concise, evidence-anchored solution; teacher **cannot change** oracle numbers, evidence IDs or formula.
6. Validator rejects mismatches and near-duplicates; domain-expert spot audit.
7. Export only synthetic rows to training; split by **company-world**, not question.

## v0.1 and future

The included generator produces five simple tasks: YoY, gross margin, current ratio, indirect CFO and insufficient CFO. It is reproducible and automatically numerically checked but **NOT** a complete financial-reporting simulator, IFRS/VAS compliant dataset, or a proof of learning deeper accounting reasoning.

Next: ledger-consistent multi-year three-statement generation; multi-document consolidation; contradictions; bilingual evidence/query mismatches; document rendering; program-vs-final-answer reward.

Run:
```bash
python -m unittest discover -s tests -v
python -m src.generate_sft --worlds 100 --seed 42 --out data
```

Before expanding to 30K examples, train a 3–5K pilot, evaluate on a fixed unseen real-doc validation set and independently held-out fictional worlds, and retain general instruction-following performance.
