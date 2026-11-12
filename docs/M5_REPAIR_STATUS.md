# M5 repair status

This branch preserves 10,000 original fictional hand-authored training questions, with M3 augmentation in separate arms. The original raw authored export is retained as an archival label format. The training-ready experiment export uses financial_json_v1.

## Completed in code
- Manifest verification (SHA-256, exact split counts and authored provenance); raw dev/test SHA-256 frozen to the validated M5 build. FinanceBench download pinned to upstream commit and expected QA Git blob checksum.
- One-based physical PDF page conversion shared by lexical and dense retrieval.
- JSON assistant target for all experiment arms; manually annotated all 100 M1 oracle types/results. Multi-result and qualitative questions require narrative review; frozen held-out source files unchanged.
- Explicit numeric tolerance, sign check and limited aliases; qualitative conclusions still require review.
- Split owner leakage check, dense chunk hash, prompt hash, eligible end-to-end numeric/abstention metric.
- Source case citation repairs in A038, A039, A040, A041 and A046; evidence checked directly. Several worked explanations expanded.
- Manual language metadata for A020-28, A027-05, A027-07, A027-25. Remaining labels are explicitly unreviewed.

## Open blockers to production-quality SFT
- Manually resolve remaining operand flags; a numeric match in unrelated evidence does not establish support.
- Review all language flags, semantic duplicate candidates, and 144 unit types. Do not silently relabel, auto-add citations or delete examples.
- Build evidence-linked operands with entity, period, unit, scope and version. Current arithmetic checks still cannot prove financial semantics.
- Author independent larger dev/test and adversarial cases; do not tune on the final test.
- Complete retrieval, PDF/table/vision, and local training experiments separately.
- Accounting expert review and actual model training are not performed by this repair.

Do not treat a green structural CI as certification of all financial conclusions.
