# Financial evaluation datasets — license audit (2026-11-11)

**This file is about licenses of published datasets, not blanket copyright permissions for every corporate filing/figure.** Store each document's provenance, permissions, attribution and hash. Non-commercial research use only for this project.

| Dataset | URL | Declared dataset license | Caveat |
|---|---|---|---|
| FinanceBench open sample, 150 QA | https://huggingface.co/datasets/PatronusAI/financebench | CC BY-NC 4.0 | Full benchmark is commercial license only; verify third-party filings separately. |
| FinQA (~8K QA) | https://huggingface.co/datasets/ibm-research/finqa | CC BY 4.0 | Source company filings may have separate rights. |
| TAT-QA (16,552 QA) | https://github.com/NExTplusplus/TAT-QA | CC BY 4.0 | Repo code license is not dataset license. |
| TAT-DQA (financial VQA) | https://huggingface.co/datasets/next-tat/TAT-DQA | CC BY 4.0 | Images may carry separate third-party rights. |
| Vietnam company annual reports 2000–2025 | https://zenodo.org/records/20949551 | **Not verified from the Zenodo rights field** | Accessible files are not automatically reusable; obtain explicit permission before bulk reuse. |

**Data governance:** Real reports, QA, labels and model outputs on evaluation sources must never enter SFT, DPO, GRPO, or teacher-training loops. Existing public benchmarks may have pretraining contamination; maintain a fresh external holdout where possible.
