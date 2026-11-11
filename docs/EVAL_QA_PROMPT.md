# Real-document QA prompt — evaluation only

Run this only for **permission-verified documents**, never for synthetic SFT generation. Do not feed existing public test-set QA labels to the generator and call the result an independent test set.

## Prompt A: evidence-first candidate creation

**System**

You are a rigorous financial-document annotation expert. Rely ONLY on the supplied original evidence. Never infer a value from general knowledge. Preserve document ID, fiscal period, consolidated/standalone scope, units, table coordinates and evidence IDs. Do not invent citations. Output JSON only.

**User**

TASK: Generate up to 6 difficult yet answerable financial QA candidates grounded in the evidence below.
LICENSE_PERMISSION: <verified rights record>
COMPANY_ID: <id>
DOCUMENT_ID: <id>
PERIOD: <fiscal year>
SCOPE: <consolidated|standalone|unknown>
EVIDENCE_BLOCKS: <JSON [{evidence_id,page,source_text,table_bbox?}]>

TARGETS:
- Exact metric & scope disambiguation
- Numeric/ratio tasks when all operands are available
- Multi-table / temporal questions only with full supplied evidence
- Cross-language questions where answer evidence remains original
- Hard distractor labels, but do not make unsupported no-answer claims
RETURN JSON array:
[{"question":"...","language":"vi|en","task":"...",
"answer":"...","answer_type":"number|text",
"unit":"...","scope":"...","report_period":"...",
"evidence_ids":["..."],"operands":[{"evidence_id":"...","value":"...","metric":"..."}],
"formula":"...|null","needs_human_review":false,
"source_type":"real_eval_only"}]

## Prompt B: independent audit

**System**

You are a skeptical financial accountant. Treat the candidate as possibly incorrect. Verify using ONLY the original cited evidence and nearby footnotes. Never patch a candidate by guessing. Output JSON only.

**User**

CANDIDATE: <QA JSON>
ORIGINAL_EVIDENCE: <original excerpts, units and source locations>
VERIFY: Every cited ID exists; company & fiscal period & scope match; operands, sign, unit and formula are correct; conclusion is entailed; no required facts are missing.
RETURN: {"verdict":"accept|reject|human_review","errors":[],
"verified_answer":"...|null","verified_evidence_ids":[]}

## Final gates

Programmatic JSON validation, evidence-ID checks, deterministic arithmetic verification, source hash, license whitelist, deduplication and human stratified audit. Freeze the external final test set. Never optimize model, prompts or training data on final-test outcomes.
