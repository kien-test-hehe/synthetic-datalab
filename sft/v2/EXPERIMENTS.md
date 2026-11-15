# Pilot experiment protocol

Use the same base snapshot, tokenizer/template options, prompt budget, decoding
settings and held-out IDs for every arm. For each model record:
- E0 untouched base, 500 dev QA (no adapter)
- E1 original V1 (matched parent-only control, then full V1 separately)
- E2 V2-lite/Reasoning pilot with short/detailed direct targets
- E3 same reviewed QA with final-only target (reasoning ablation)
- E4 same direct dataset plus calculator plan and final targets

Compare model sizes separately. The tool-assisted arm must run the arithmetic
backend and validate citation IDs; direct-only inference on the tool-trained
adapter is not a tool-assisted benchmark. Measure end-to-end tool execution,
operand support, numeric result, unit, citations and abstention.

Run HF evaluation without converting adapters to Ollama:
    python -m src.v2.evaluate --model /local/base --output runs/base-dev.jsonl
    python -m src.v2.evaluate --model /local/base --adapter runs/lite-adapter/adapter --output runs/lite-dev.jsonl

Before any full test run, freeze chosen settings:
    python -m src.v2.evaluate --model /local/base --adapter runs/lite-adapter/adapter --output unused.jsonl --protocol runs/locked.json --write-protocol
    python -m src.v2.evaluate --model /local/base --adapter runs/lite-adapter/adapter --output runs/lite-test.jsonl --split test --unlock-test --protocol runs/locked.json

The protocol is an explicit local safeguard, not an immutable experiment
registry. It records hashes and settings; it cannot attest that the user has
never seen the test data. Existing strict citation/numeric scores are proxies;
qualitative answers need independent review. Report all attempted samples,
including malformed JSON and token-budget failures. No GPU run has been
performed by this repository CI.
