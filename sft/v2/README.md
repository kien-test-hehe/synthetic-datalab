# FinancialDocLab V2 (11,000-QA pilot)

V1 remains immutable. The independent 500-dev/1,000-test benchmark is frozen.
This checkpoint contains 11,000 canonical QA: 9,164 individual V1 revisions and 1,836 new fictional QA. The remaining 836 V1 rows are not upgraded automatically. The full V2 target remains 12,000 canonical QA (10,000 V1 revisions and 2,000 new fictional QA). V2 only exports individually authored revisions/new rows from batches/*.jsonl;
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


## 5,000-QA checkpoint

Added exactly 1,000 canonical rows: 838 individually authored V1 revisions in m7_065–m7_078 and 162 original fictional QA in m8_013–m8_015 (18 new case groups, V2-N093–V2-N110). All 1,000 parent/new IDs are unique. Difficulty: 196 easy, 715 medium, 89 hard. Task counts: 332 multi-document, 168 abstention, 142 conflict, 87 basic reasoning, 54 table, 53 financial explanation, 51 advanced reasoning, 38 unit conversion, 36 evidence selection, 18 temporal, 18 multi-result and 3 robustness.

Topics include NPL evidence conflicts, grant subsidy, agency revenue, unitized NAV, compute credits, layered reinsurance, downstream consolidation, FX receivables, SSP allocation, guarantees, hedge cash versus OCI, pharma milestones, joint-cost decisions, collateral stress, reserve sweeps, gift-card chargebacks, SBC forfeiture and turnover rent. Some V1 concise/detailed explanations share the same individually authored core reasoning, with citations added to the detailed version; this is not a claim of independent or uniformly longer rationale variants. New cases contain separately authored concise and detailed explanations. Previously revised parents and unsupported or over-bounded calculator examples were skipped rather than changing the frozen oracle or calculator limits. No bulk content generator, expert certification, semantic-leakage guarantee or GPU fine-tuning is claimed. Remaining target: 5,810 V1 revisions and 1,190 new fictional QA.


## 6,000-QA checkpoint

Added exactly 1,000 canonical rows: 838 individually authored V1 revisions in m7_079–m7_093 and 162 original fictional QA in m8_016–m8_018 (18 new case groups, V2-N111–V2-N128). All 1,000 parent/new IDs are unique. The increment comprises 689 single-numeric, 19 multi-numeric, 148 qualitative, and 144 insufficient-evidence QA; 510 Vietnamese and 490 English answers; 190 easy, 683 medium, and 127 hard. Task counts: 376 multi-document, 144 abstention, 104 advanced reasoning, 101 financial explanation, 99 basic reasoning, 65 table, 47 conflict, 19 multi-result, 17 unit conversion, 12 evidence selection, 8 robustness, 7 temporal, and 1 extraction.

New fictional cases cover carve-out EBITDA, restricted and trapped cash, diluted EPS, debt modification, PPE component replacement, supplier rebates, pension OCI, signed report version precedence, uncertain tax claims, OCR unit/sign errors, guarantees, turnover rent, customer return liabilities, partial lease termination, held-for-sale machinery, repo collateral, acquisition escrow and contingent consideration, and constant-currency revenue bridges. Every added row has a concise rationale and separately authored explanatory detail; the detailed answer may also repeat the short calculation for clarity. Previously revised parents and examples without sufficiently supported or bounded arithmetic were skipped. Calculator expressions were corrected for reserved names, allowed arithmetic constants, AST size and source-number formatting; neither V1 oracles nor calculator limits were changed. V1 and independent benchmark remain frozen. Code serializes authored rows and validates and exports them; no bulk QA generator, independent financial expert certification, semantic leakage guarantee, or completed model fine-tuning is claimed.

Remaining target: 4,972 V1 revisions and 1,028 new fictional QA (6,000 total).


## 7,000-QA checkpoint

Added exactly 1,000 canonical rows: 838 individually authored V1 revisions in m7_094–m7_108 and 162 new fictional QA in m8_019–m8_021 (18 new case groups, V2-N129–V2-N146). The increment contains 569 numeric, 19 multi-numeric, 220 qualitative and 192 insufficient-information answers; 513 Vietnamese and 487 English; 114 easy, 734 medium and 152 hard. Tasks: 328 multi-document, 192 abstention, 141 financial explanation, 94 basic reasoning, 87 conflict, 51 advanced reasoning, 33 evidence selection, 20 temporal, 20 unit conversion, 19 multi-result, 13 robustness, 1 extraction and 1 table.

The new fictional cases cover import duties/VAT, syndicated lending, roaming settlement, pharmaceutical milestones, fuel surcharge, concession reserves, fund fee transitions, commodity collars, consignment, covenant waiver dates, spoilage, merchant settlement, prior-period errors, interline tickets, progressive royalties, reinsurance reinstatement, cash-settled share-based payments and acquisition measurement-period adjustments. Related financial concepts can recur; distinct cases do not establish semantic OOD. V1 parents already revised were skipped. Quarterly accrual expressions use permitted calculator literals (2+1) instead of a disallowed literal 3. No bulk question generator was used; code serializes authored rows and verifies arithmetic.

The 7,000-row artifact was compared against the 6,000-row artifact: exactly 1,000 added IDs, zero removed, zero changed prior canonical rows, and byte-identical full V1 control. The lexical audit still reports two candidates at Jaccard 0.75 (V2-N066-d / IE-D07-c and V2-N117-f / M4-10-a); no additional candidates appeared at the 0.72 threshold. Semantic review remains required. No independent financial expert certification or fine-tuning result is claimed.

Remaining target: 4,134 V1 revisions and 866 new fictional QA (5,000 total).


## 9,000-QA checkpoint

The combined 7,000-to-9,000 increment adds exactly 2,000 canonical rows: 1,676 individually authored V1 revisions (m7_109–m7_135) and 324 new fictional QA (m8_022–m8_027, V2-N147–V2-N182, 36 new case groups). The final 548-row increment from the independently verified 8,452 snapshot comprises 386 V1 revisions and 162 fictional QA. Duplicate parent candidates were removed; decimal-comma source references, reserved calculator names, allowed literals and unit scales were corrected without changing V1 oracles.

The full 2,000-row increment contains 1,158 numeric, 429 qualitative and 413 insufficient-evidence QA; 1,024 Vietnamese and 976 English answers; 26 easy, 1,798 medium and 176 hard. The final 548-row increment adds 222 advanced reasoning, 114 abstention, 103 financial explanation, 93 multi-document, 12 conflict and 4 evidence selection tasks. The difficulty and task distributions are author labels, not measured model difficulty. Coverage includes consolidation and reporting corrections, valuation (DCF, FCFE, WACC, APV, residual income), scenario-weighted ECL, capacity decisions, pension OCI, acquisition consideration, supplier rebates, and cash-versus-accrual judgment.

The 9,000-row artifact from commit 9cd76a712b05879f0ca09ce3e59b5bfa254669ea (workflow run 43666262914) was independently compared with the 7,000 and 8,452 artifacts: exactly 2,000 and 548 new IDs respectively, zero prior canonical rows removed or changed, byte-identical full V1 control, valid ZIP integrity and all export SHA-256 checks passed. The lexical audit still identifies the same two candidates at Jaccard 0.75; it is screening only and does not prove semantic separation.

Exports: canonical 9,000; SFT Lite and Lite Answer-only 8,013 each; SFT Reasoning and Reasoning Answer-only 9,000 each; Calculator Lite 12,931; Calculator Reasoning 14,755; matched V1 control 7,542; full V1 control 10,000. Calculator variants include multiple training examples for some canonical QA and are not additional unique questions. Total cases 1,114; case groups 1,105. No independent financial expert certification, real-world accounting compliance, or successful model training is claimed.

Remaining target: 2,458 V1 revisions and 542 new fictional QA (3,000 total).


## 10,000-QA checkpoint

Added exactly 1,000 canonical QA: 838 individually authored V1 revisions (m7_136–m7_149) and 162 original fictional QA (m8_028–m8_030; 18 new case groups V2-N183–V2-N200). The increment includes 540 single-numeric, 231 qualitative, and 229 insufficient-information answers; 489 Vietnamese and 511 English answers. Difficulty labels: 4 easy, 979 medium, 17 hard. Tasks: 390 multi-document, 229 abstention, 225 financial explanation, 117 advanced reasoning, 15 unit conversion, 14 temporal, 6 conflict and 4 evidence selection. These are author labels, not empirically measured difficulty.

Coverage includes disclosure and governance, multi-period reporting, segment and sector economics, cash conversion, portfolio attribution, factoring, foreign exchange exposures, cash equivalents and covenant instruments. Fictional cases add borrowing-base lending, healthcare capitation, freight, loyalty, nonaccrual interest, water utility, construction contracts, telecommunications allocation, agriculture, margin lending, marketplace principal/agent, wind generation, warranty provisions, bank NIM, consignment, solar curtailment, insurance combined ratio and SaaS ARR retention. Related concepts may recur. Some concise and detailed explanations in m7_146–m7_148 intentionally share the same individually authored rationale with citation formatting; they are not independent rationale rewrites.

The 10,000-row artifact from commit 6986676819e9b249bbf83b350adf11b3629bef0b (workflow run 43670065724, artifact 14143836983) was compared with the 9,000-row artifact: 1,000 new unique IDs, zero removed, zero changed prior canonical rows, byte-identical full V1 control, ZIP integrity and all ten export row counts and SHA-256 checks passed. The grouped warehouse capacity operand was corrected to thousands of slots and scaled by 1,000 to avoid comma-token parsing ambiguity; the V1 oracle was unchanged. The lexical audit still reports the two existing candidates at Jaccard 0.75 (V2-N066-d / IE-D07-c and V2-N117-f / M4-10-a), with no new candidates at threshold 0.72. Semantic review remains required.

Exports: canonical 10,000; SFT Lite and Lite Answer-only 8,996 each; SFT Reasoning and Reasoning Answer-only 10,000 each; Calculator Lite 14,437; Calculator Reasoning 16,295; matched V1 control 8,380; full V1 control 10,000. There are 1,236 cases and 1,227 case groups. No independent expert validation, accounting compliance guarantee, semantic leakage guarantee, or GPU training result is claimed.

Remaining target: 1,620 V1 revisions and 380 new fictional QA (2,000 total).


## 10,358-QA checkpoint

Added 358 canonical QA: 304 individually authored V1 revisions (m7_150–m7_157, completing the A039 and A022 backlogs) and 54 new fictional QA (m8_031, V2-N201–V2-N206). The increment includes 230 numeric, 68 qualitative, and 60 insufficient-evidence answers; 219 English and 139 Vietnamese answers. Author difficulty labels: 2 easy, 335 medium, 21 hard. Tasks: 186 multi-document, 60 abstention, 39 advanced reasoning, 35 conflict, 33 financial explanation, 2 temporal, 2 evidence selection and 1 unit conversion.

Coverage includes long-context audited financial reporting, consolidation, bank regulatory ratios under toy definitions, environmental scope boundaries, marketplace GMV, counterparty impairment, REIT AFFO, private-fund multiples, hospital and telecom metrics, aviation economics, survey response bounds, mining and electricity reliability, and treasury instruments. The six new fictional cases cover data-center energy efficiency, preference dividends and EPS, premium refunds, concession accounting, asset-management fees and pharmacy inventory. Two insufficient-evidence labels and inherited evidence-language metadata were corrected without changing any frozen oracle. Some short and detailed rationales share the same individually authored core with citation formatting.

Artifact 14155832528 from commit ce2547b42b173c1f7d92f1b3bb1cbf6f1e4d024c (run 43699660311) was checked against the 10,000-QA artifact: 358 added IDs, zero removed, zero changed prior canonical rows, byte-identical V1 full control, valid ZIP and all ten export counts and SHA-256 checks passed. The same two lexical similarity candidates remain; there are no additional candidates at the 0.72 threshold. The audit is not proof of semantic separation.

Exports: canonical 10,358; SFT Lite and Lite Answer-only 9,333 each; SFT Reasoning and Reasoning Answer-only 10,358 each; Calculator Lite 14,983; Calculator Reasoning 16,883; matched V1 control 8,684; full V1 control 10,000. Cases: 1,265; case groups: 1,256. No independent expert certification, accounting compliance or training success is claimed.

Remaining target: 1,316 V1 revisions and 326 new fictional QA (1,642 total).


## 11,000-QA checkpoint

Added 642 individually authored canonical QA: 480 V1 revisions (m7_158–m7_166) and 162 new fictional QA (m8_032–m8_034, 18 groups V2-N207–V2-N224). Completed all 240 A040 transaction-audit parents, 230 of the 240 A012 parents, and ten early M1 parents. The ten remaining A012 rows include question-only parameters and decimal-comma assumptions that require careful operand provenance; they have not been exported automatically. The reserved calculator operand name in A040-16 was corrected without changing its arithmetic or frozen oracle.

Increment: 452 numeric, 105 qualitative, 85 insufficient; 334 English, 308 Vietnamese. Author difficulty labels: 1 easy, 589 medium, 52 hard. Tasks: 322 multi-document, 125 advanced reasoning, 85 abstention, 69 financial explanation, 36 conflict, 3 evidence selection and 2 temporal. These labels are author declarations, not measured model difficulty. Some short/detailed explanations share one individually authored rationale with citation formatting.

Topics include goodwill, VAT, working capital, interest rate swaps, deferred fees, discounted collateral recovery, credit loss, bond convexity, rights-of-use, inventory rebates, true-sale and secured financing, insurance cancellations, share-class NAV, bundled service contracts, commodity provisional pricing, customer-funded infrastructure, and fictional cases covering effective interest, component replacement, annual stop-loss, tax-loss utilization, batteries, reagent inventory, undrawn facilities, paid leave, segregated client funds, take-or-pay and rehabilitation provisions.

Artifact 14157112224 from commit 09eb3637d3877fded8ca7c7bb062c84905205bf7 (run 43702253185) was checked against the 10,358-QA artifact: 642 added IDs, zero removed, zero changed prior canonical rows, byte-identical V1 full control, ZIP integrity and all ten export counts and SHA-256 checks passed. The same two lexical candidates remain at Jaccard 0.75; no additional candidates at threshold 0.72. Semantic separation is not established by this audit.

Exports: canonical 11,000; SFT Lite and Lite Answer-only 9,923 each; SFT Reasoning and Reasoning Answer-only 11,000 each; Calculator Lite 15,973; Calculator Reasoning 17,977; matched V1 control 9,164; full V1 control 10,000. Cases 1,331; case groups 1,322. Answer languages: 5,503 English and 5,497 Vietnamese. Oracle kinds: 6,977 numeric, 125 multi-numeric, 2,065 qualitative, 1,833 insufficient. No independent expert certification or GPU training result is claimed.

Remaining target: 836 V1 revisions and 164 new fictional QA (1,000 total). Larger V1 groups: A010 124, A009 120, A005 100, A006 78, A007 76, A037 64; remaining 274 in other groups.
