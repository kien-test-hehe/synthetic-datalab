# FinancialDocLab V2 (pilot)

V1 remains immutable. The independent 500-dev/1,000-test benchmark is frozen.
V2 only exports individually authored revisions/new rows from batches/*.jsonl;
unreviewed V1 rows are explicitly listed in the backlog, never silently upgraded.

Each revision pins a parent ID. Evidence, assumptions and oracle are inherited
from the frozen V1 export, while the question, concise/detailed explanation,
final answer, citation IDs and named calculation operands are individually
authored. New fictional rows specify all evidence and oracle. All variants of a
counterfactual family share case_group. No crawled financial documents enter SFT.

The calculator supports a bounded arithmetic AST and named operands with source
IDs. Numeric rows need executable verification against their oracle. Source-ID
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
calculator-lite and calculator-reasoning (two examples per program: plan and
trusted-result final answer). Program and final-answer tasks are distinct; a
backend must execute and validate a plan before injecting the result. The
direct task preserves the existing evaluator's five-key JSON answer contract.
No actual GPU training is implied by a successful export.
