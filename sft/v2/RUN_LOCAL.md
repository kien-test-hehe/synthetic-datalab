# Local pilot on the two 16 GB GPUs

Use locally downloaded, untouched model weights and a transformers version
supporting your exact model architecture. This is a pilot, not a full V2 release.
The code has CPU unit tests with a fake tokenizer; actual tokenizer/model
compatibility and VRAM must be checked on your PCs. Do not disable prefix checks
just to get a run to start. Qwen thinking/non-thinking templates can differ.

    python -m src.authored_export
    python -m src.eval.independent
    python -m src.v2.build
    python -m src.v2.training --model /path/to/local/model --dataset sft/v2/exports/sft_lite.jsonl --output runs/lite-preflight --dry-run
    python -m src.v2.training --model /path/to/local/model --dataset sft/v2/exports/sft_lite.jsonl --output runs/lite-adapter --max-length 4096
    python -m src.v2.training --model /path/to/local/2b --dataset sft/v2/exports/sft_reasoning.jsonl --output runs/reasoning-adapter --max-length 8192
    python -m src.v2.training --model /path/to/local/model --dataset sft/v2/exports/sft_lite.jsonl --extra-dataset sft/v2/exports/sft_calculator_lite.jsonl --output runs/lite-tool-adapter

If the tokenizer has an explicit non-thinking setting, pass
--template-kwargs '{"enable_thinking":false}' consistently to training and
inference, after verifying the model's own template supports it.
Each run records model file fingerprint, dataset SHA, selected row IDs, token
counts and settings. It refuses truncation and masks all system/user tokens.
Use a separate output directory per run; no automatic overwrite.
Only dev is used for selection. Do not unlock the frozen test until the
experiment is pre-registered. No claim of successful real training is made.
