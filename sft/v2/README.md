# FinancialDocLab V2 (2,000-QA pilot)

V1 remains immutable. The independent 500-dev/1,000-test benchmark is frozen.
This checkpoint contains 2,000 canonical QA: 1,676 individual V1 revisions and 324 new fictional QA. The remaining 8,324 V1 rows are not upgraded automatically. The full V2 target remains 12,000 canonical QA (10,000 V1 revisions and 2,000 new fictional QA). V2 only exports individually authored revisions/new rows from batches/*.jsonl;
unreviewed V1 rows are explicitly listed in the backlog, never silently upgraded.

Each revision pins a parent ID. Evidence, assumptions and oracle are inherited
from the frozen V1 export, while the question, concise/detailed explanation,
final answer, citation IDs and named calculation operands are individually
authored. New fictional rows specify all evidence and oracle. All variants of a
counterfactual family share case_group. No crawled financial documents enter SFT.

The calculator supports a bounded arithmetic AST and named operands with source
IDs. An explicit @assumptions operand source is supported only for a numeric token present in the scenario assumptions; it is not an evidence citation. This validates token presence, not semantic extraction. Numeric rows need executable verification against their oracle. Source-ID
checks are not proof that values are correctly extracted from evidence; review
the labels and evidence manually. Independent review and language verification
are not claimed. Exact question, evidence-block and case checks against both
frozen benchmarks do not prove semantic separation.

Build:
    python -m src.authored_export
    python -m src.eval.independent
    python -m src.v2.build
    python -m unittest discover -s tests -p test_v2.py -v

Exports: canonical, lite (easy/medium only), reasoning (all reviewed rows),
calculator-lite and calculator-reasoning (one routing plan for every row, plus a
trusted-result final example for each single-result calculation). Program and final-answer tasks are distinct; a
backend must execute and validate a plan before injecting the result. The
direct task preserves the existing evaluator's five-key JSON answer contract.
No actual GPU training is implied by a successful export.

## 1,500-QA checkpoint

Batches m7_016–m7_023 contribute 440 individually rewritten V1 QA after duplicate parent removal; m8_004 contributes 60 new fictional QA across ten new case groups. The 500 added rows include 308 single numeric programs, 94 insufficient-evidence answers, and 98 qualitative answers. Source facts and V1 oracles remain frozen. No bulk question or rationale generator is used: code only serializes explicitly authored records and computes export variants. The additional rows have not been independently expert-audited or used in a training run.

## 2,000-QA checkpoint

Batches m7_024–m7_030 add 398 individually authored V1 revisions; m8_005–m8_006 add 102 original fictional QA in 17 cases and 16 case groups. The 500 additions contain 345 single-numeric, 17 multi-numeric, 75 qualitative, and 63 insufficient-evidence answers. Added coverage includes 38 multi-document, 14 table, 17 multi-result, 11 conflict, and 3 robustness tasks (task tags are mutually exclusive; evidence can exercise additional skills). A paired covenant-waiver counterfactual shares a case group across the before/after-reporting-date variants. The calculation programs retain named operands and signed numeric values; the source/oracle snapshots and both held-out benchmarks are unchanged. No bulk rationale or question generation, no independent financial expert certification, and no GPU training claim.
