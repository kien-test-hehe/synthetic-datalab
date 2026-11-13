# FinancialDocLab V2 (4,000-QA pilot)

V1 remains immutable. The independent 500-dev/1,000-test benchmark is frozen.
This checkpoint contains 4,000 canonical QA: 3,352 individual V1 revisions and 648 new fictional QA. The remaining 6,648 V1 rows are not upgraded automatically. The full V2 target remains 12,000 canonical QA (10,000 V1 revisions and 2,000 new fictional QA). V2 only exports individually authored revisions/new rows from batches/*.jsonl;
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

## 3,000-QA checkpoint

Added exactly 1,000 canonical rows: 838 individually authored V1 revisions in m7_031–m7_042 and m7_044–m7_048, plus 162 new fictional QA in m8_007–m8_009 (18 new case groups). All 1,000 added parent/new IDs are unique. This increment includes 561 English and 439 Vietnamese answers; 250 easy, 560 medium and 190 hard questions. Task counts: 413 multi-document, 119 basic reasoning, 111 advanced reasoning, 83 conflict, 83 abstention, 72 table, 53 financial explanation, 21 unit conversion, 18 multi-result, 10 temporal, 8 evidence selection, 7 extraction and 2 robustness. Task labels are mutually exclusive; skills may overlap in the evidence.

Nine already revised parent IDs were excluded, two excessive-operand programs were deferred rather than widening the bounded calculator, and one question-only numeric assumption was replaced by a grounded case. An uncommitted draft batch was not counted. V1 and benchmark snapshots remain frozen. No bulk question or rationale generator was used: code serializes the authored records, verifies calculations and builds export variants. Independent financial expert certification, semantic-leakage guarantees and GPU fine-tuning are not claimed.


## 4,000-QA checkpoint

Added exactly 1,000 canonical rows: 838 individually authored V1 revisions in m7_049–m7_064 and 162 original fictional QA in m8_010–m8_012 (18 new case groups). The increment has 611 single-numeric, 18 multi-numeric, 222 qualitative and 149 insufficient-evidence QA; 520 Vietnamese and 480 English answers; 225 easy, 648 medium and 127 hard. Task counts: 345 multi-document, 149 abstention, 124 conflict, 117 basic reasoning, 93 financial explanation, 59 advanced reasoning, 50 table, 22 evidence selection, 18 multi-result, 14 unit conversion, 7 temporal and 2 extraction. Task labels are mutually exclusive.

New fictional cases V2-N075–V2-N092 cover liquidity caps, secured receivable financing, supplier finance, reinsurance caps, effective-interest bonds, weighted EPS, pension movements, NCI, contract catch-up, restricted deposits, deferred tax recoverability, investment waterfalls, acquisition earn-outs, emission obligations, take-or-pay, regulatory assets, progressive royalty and invalid ad impressions. Previously revised parents were excluded. A036-19-d was deferred because the exact integer floor operation is outside the bounded arithmetic calculator; A033-29-h was not selected to keep the increment at exactly 838 revisions. No changes to the calculator whitelist or frozen V1 oracles were made.

The 3,000-row lexical audit candidate V2-N066-d vs IE-D07-c (Jaccard 0.75) was manually inspected: deferred grant liability versus deferred tax liability, with distinct source facts, accounting mechanisms and answers. It is a lexical similarity candidate, not an exact duplicate. This review does not prove absence of semantic leakage. The independent benchmark and V1 remain frozen. No bulk question/rationale generator, independent financial expert certification, or GPU training claim.
