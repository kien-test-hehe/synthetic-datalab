# M1 financial QA review rubric (manual review)

These 100 examples have passed structured/arithmetic checks, **not professional accountant signoff**. Review every case before treating this as financial-domain instruction-tuning supervision.

Score each criterion 0/1/2 (10 points max):

1. **Financial principles and economic plausibility** (0 incorrect, 1 simplification ambiguous, 2 valid under clearly stated assumptions).
2. **Evidence scope and version** (0 unsupported/mixed scope, 1 citation weak, 2 traceable and period/scope correct).
3. **Solution correctness** (0 math/logic wrong, 1 incomplete, 2 verified steps and correct conclusion).
4. **Non-overclaiming / abstention** (0 material hallucination, 1 ambiguous qualification, 2 appropriately calibrated).
5. **Clarity and transferability** (0 memorization-only/unreadable, 1 formulaic, 2 clear and generalizable).

Suggested acceptance threshold: at least 8/10 and no critical zero in financial principles, evidence or reasoning. Reviewers should record \`case_id, reviewer, scores, issues, status, reviewed_at\`.

Automated checks prove **only** numerical program consistency and structural evidence references. They do not prove the economic scenario, accounting convention or reasoning is professionally certified.

## Important design risks

- There are only 40 distinct scenarios and 100 QAs, so context style repeats; unsuitable as the sole dataset for broad SFT.
- L2–L5 mix is weighted toward L3/L4 rather than perfectly uniform.
- No image/table bounding-box extraction or long PDFs are included yet.
- Sector-specific standards (banking and insurance) are synthetic educational illustrations, not full regulatory reports.
- Several rows require admitting uncertainty; ask whether the cited evidence truly excludes all possible answers.
- Public base models might have seen FinanceBench/FinQA elsewhere; maintain an additional private or freshly written holdout.
