# M3 — 14,400 synthetic robustness examples + FinanceBench real-evidence RAG baseline

## Status
M1 (100 hand-authored rows) and M2 (1,600 controlled world instantiations) were merged into \`main\`.

M3 is **not** a set of 14,400 manually authored independent questions. It reuses M2's 32 individually authored financial reasoning programs, generated across 800 fictional company worlds, then adds intentionally conflicting **cross-company distractor** and **missing-target evidence** variants. The generator is deterministic; it invokes NO external LLM API and does not touch any real-company benchmark data.

## Synthetic M3 dataset

\`\`\`bash
python -m src.m3.augment --worlds 800 --seed 42 --out sft/m3/outputs
python -m src.m3.validate --worlds 800 --root sft/m3/outputs
\`\`\`

Expected:
- 800 fictional worlds, **14,400 rows**, 11,520 train / 1,440 dev / 1,440 test
- 6,400 original M2-context rows, 6,400 correct-answer cross-company distractor rows, 1,600 target-evidence-absent rows
- 4 language combinations balanced (VI/EN), 4 sectors balanced
- 100% citation, arithmetic-program, accounting-world and split checks
- One world never occurs in more than one split

M3 is suitable for an ablation against M2 to examine whether provenance-aware evidence selection and abstention improve. It does **not** by itself prove the model can generalize to unseen task patterns or real annual reports.

GitHub Actions \`.github/workflows/m3_quality.yml\` builds and uploads the JSONL as a downloadable CI artifact. Do not commit gigabytes of outputs or trained weights.

## FinanceBench local RAG

Real benchmark data are strictly **evaluation-only**, never for any LLM training. Original published QA and PDF filings are kept in \`real_eval/\` (gitignored), outside the SFT pipeline. FinanceBench's open sample is published under **CC BY-NC 4.0**. Company PDF rights may differ, so carefully review them before using or distributing. An explicit acknowledgement is required before downloading PDFs via the CLI.

\`\`\`bash
# Network used only for original official-file download
python -m src.eval.financebench download-qa --out real_eval/financebench/questions.jsonl
python -m src.eval.financebench download-pdfs \
  --qa real_eval/financebench/questions.jsonl \
  --out real_eval/financebench/pdfs \
  --acknowledge-rights

# Purely LOCAL PDF parsing and lexical index
python -m pip install pymupdf
python -m src.eval.financebench parse \
  --pdfs real_eval/financebench/pdfs --out real_eval/financebench/chunks.jsonl
python -m src.eval.financebench index \
  --chunks real_eval/financebench/chunks.jsonl --db real_eval/financebench/fts.sqlite
python -m src.eval.financebench eval \
  --qa real_eval/financebench/questions.jsonl \
  --db real_eval/financebench/fts.sqlite --k 10 \
  --out reports/financebench_fts.json

# Local dense retrieval alternative. No cloud model or API.
python -m pip install numpy sentence-transformers
python -m src.eval.dense build \
  --chunks real_eval/financebench/chunks.jsonl \
  --model BAAI/bge-m3 \
  --index real_eval/financebench/embeddings.npz
python -m src.eval.dense eval \
  --qa real_eval/financebench/questions.jsonl \
  --chunks real_eval/financebench/chunks.jsonl \
  --model BAAI/bge-m3 --index real_eval/financebench/embeddings.npz
\`\`\`

Optional \`--oracle-doc\` restricts retrieval to the correct report and isolates within-document retrieval quality. \`--include-company\` adds company metadata to query and should be reported explicitly as a separate condition. Compare full-index vs oracle-document baselines.

**Very important:** PDFs are not stored in this PR. PyMuPDF extracts physical PDF pages, with 1-based page numbering. Published \`evidence_page_num\` labels may have a different index convention in edge cases; audit a sample manually before trusting page-recall. Scanned image-only pages require OCR or visual retrieval, not silently blank pages.

This pipeline measures evidence-document and evidence-page retrieval recall, **not** financial answer accuracy or successful SFT. For complete RAG, add a local answering model and verify final answers separately against the original, unchanged official labels.

## Research-quality warning

The larger M3 pool can create severe template overfitting because there are still only 32 underlying algorithmic families. Do not call this a high-quality 14K hand-authored dataset. Run model scaling ablations, hold out some task *families* entirely from training, and use fresh real-document evaluation whose labels never influence SFT.
