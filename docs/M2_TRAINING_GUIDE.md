# Training and evaluation guidance

M1 \`sft/m1/exports/train.jsonl\` contains 80 entirely hand-authored SFT examples. M2 generates 1,280 new controlled-instantiation train records (200 worlds × 8 tasks, with 80% held for training). The two sources must retain separate provenance and should not be conflated as all hand-written.

Recommended baseline comparisons:
- Local base model on gold-context real financial QA (separate from SFT).
- Local base model on M2 synthetic test, recognizing that the same 32 task patterns recur.
- SFT M1-only, M2-only, M1+M2; assess train/dev/test but prioritize real held-out financial QA.
- Track numeric exact accuracy, citation and scope correctness, abstention precision, and multilingual gaps.
- Never select the model solely by FinanceBench or another final-test result; reserve unseen real evaluation for final reporting.

The corpus uses \`messages\` with system, user, assistant. Use completion-only loss for assistant when available and ensure long evidence is not silently truncated. QLoRA vs BF16 LoRA should be chosen by current model-specific VRAM benchmarks. No default checkpoint or claimed improvement is included.
