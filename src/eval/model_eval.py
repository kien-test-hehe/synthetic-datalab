"""Leakage-safe local model evaluation for synthetic QA and official FinanceBench.

Runs Ollama on loopback only. No model output or evaluation data is written to SFT.
Numeric synthetic questions are graded against explicit oracles, with unit and
answerability checks. Qualitative/FinanceBench answers require manual review.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import sqlite3
import time
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit

from src.eval.financebench import read_jsonl, retrieve
from src.m1_oracles import m1_oracle

SCHEMA = (
    'Return a single JSON object with keys status ("answerable" or "insufficient"), '
    'answer (string containing the explanation and conclusion), value (number or null), '
    'unit (string or null), citations (array of exact evidence IDs). '
    'For a numeric question put only the requested numerical result in value, not an intermediate number. '
    'Use the requested scale and sign. Allowed standard units where applicable: percent, pp, days, times, '
    'million_usd, billion_vnd, million_shares, usd_per_share. Other requested units are allowed. Use null for value/unit if not numerical or if multiple distinct results are requested; put all results in answer. '
    'Do not make claims unsupported by the supplied evidence.'
)

def validate_endpoint(endpoint):
    parsed=urlsplit(endpoint)
    if parsed.scheme!="http" or parsed.hostname not in ("localhost","127.0.0.1","::1") or parsed.username or parsed.password or parsed.path not in ("","/") or parsed.query or parsed.fragment:
        raise ValueError("Only a local HTTP Ollama loopback endpoint is permitted")
    return endpoint.rstrip("/")

def ollama(messages,model,endpoint,timeout,temperature,context_tokens,max_tokens):
    endpoint=validate_endpoint(endpoint)
    payload={"model":model,"messages":messages,"stream":False,"format":"json",
             "options":{"temperature":temperature,"num_ctx":context_tokens,"num_predict":max_tokens,"seed":42}}
    req=urllib.request.Request(endpoint+"/api/chat",data=json.dumps(payload).encode(),
         headers={"Content-Type":"application/json"},method="POST")
    # Never forward local-only prompts via an HTTP redirect.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*args,**kwargs):
            return None
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    with opener.open(req,timeout=timeout) as response:
        data=json.loads(response.read())
    return data["message"]["content"], {"prompt_eval_count":data.get("prompt_eval_count"),
        "eval_count":data.get("eval_count"),"done_reason":data.get("done_reason")}

def parse_response(content):
    try:
        obj=json.loads(content)
    except (ValueError,TypeError):
        return None
    if not isinstance(obj,dict) or obj.get("status") not in ("answerable","insufficient"):return None
    if not isinstance(obj.get("answer"),str) or not obj["answer"].strip():return None
    if not isinstance(obj.get("citations"),list) or not all(isinstance(x,str) for x in obj["citations"]):return None
    if "value" not in obj or "unit" not in obj:return None
    v=obj["value"];u=obj["unit"]
    if v is not None and (type(v) not in (int,float) or not math.isfinite(v)):return None
    if u is not None and not isinstance(u,str):return None
    if obj["status"]=="insufficient" and (v is not None or u is not None):return None
    if (v is None)!=(u is None):return None
    if u is not None and not u.strip():return None
    if len(set(obj["citations"]))!=len(obj["citations"]):return None
    return obj

def synthetic_oracle(row):
    if row.get("oracle") is not None:return row["oracle"]
    annotated=m1_oracle(row.get("id"))
    if annotated is not None:return annotated
    if row.get("answerability")=="insufficient":return {"kind":"insufficient"}
    p=row.get("program")
    if p is not None:
        unit={"money":"million_usd"}.get(p["unit"],p["unit"])
        return {"kind":"numeric","value":p["output_rounded"],"unit":unit}
    return {"kind":"manual_review"} if row.get("checks") else {"kind":"qualitative"}

def synthetic_example(row):
    if row.get("split") not in ("dev","test"):
        raise ValueError("Model evaluator accepts held-out synthetic dev/test rows only")
    if row.get("source_type")!="fully_synthetic_only" and row.get("source")!="original_fictional_hand_authored":
        raise ValueError("Unexpected synthetic provenance")
    messages=[dict(m) for m in row["messages"][:2]]
    assert [m["role"] for m in messages]==["system","user"]
    if SCHEMA not in messages[0]["content"]:messages[0]["content"]+="\n"+SCHEMA
    return {"id":row["id"],"messages":messages,"gold_answer":row["answer"],
            "oracle":synthetic_oracle(row),"gold_citations":row["evidence_ids"],
            "allowed_citations":[x["id"] if "id" in x else x["evidence_id"] for x in row["evidence"]],
            "group":row.get("category",row.get("scenario_family","other")),
            "language_pair":row.get("language_pair","unknown"),
            "variant":row.get("variant_type","authored")}

def financebench_examples(qa,mode="gold",chunks=None,db=None,k=10):
    # Only question and source evidence are sent. Official answer stays in output labels.
    if mode=="lexical":
        if not chunks or not db:raise ValueError("Lexical mode requires --chunks and --db")
        records={r["chunk_id"]:r for r in read_jsonl(chunks)}
        if any(x.get("source")!="original_pdf_page_text_only" for x in records.values()):
            raise ValueError("Only original PDF chunks accepted")
        conn=sqlite3.connect(db)
    else:
        records={};conn=None
    try:
        for row in qa:
            if mode=="gold":
                blocks=[(f"G{i+1}",e.get("evidence_text") or e.get("evidence_text_full_page") or "")
                        for i,e in enumerate(row.get("evidence",[]))]
                blocks=[(i,t) for i,t in blocks if t.strip()]
            else:
                hits=retrieve(conn,row["question"],k=k)
                blocks=[(h["chunk_id"],records[h["chunk_id"]]["text"]) for h in hits]
            system="Answer financial questions only from the supplied evidence. Cite the exact IDs. "+SCHEMA
            user="\n\n".join(f"[{key}]\n{val}" for key,val in blocks)+"\n\nQuestion: "+row["question"]
            yield {"id":row["financebench_id"],"messages":[{"role":"system","content":system},{"role":"user","content":user}],
                   "gold_answer":row["answer"],"oracle":{"kind":"qualitative"},
                   "gold_citations":None,"allowed_citations":[x[0] for x in blocks],
                   "group":row.get("question_reasoning") or row.get("question_type") or "other",
                   "language_pair":"en-en","variant":"financebench_"+mode}
    finally:
        if conn:conn.close()

def canonical_unit(unit):
    if unit is None:return None
    key=unit.strip().casefold().replace(" ","_")
    return {"ratio":"times","x":"times","percentage":"percent","%":"percent",
            "percentage_points":"pp","percentage_point":"pp"}.get(key,key)

def numeric_matches(value, oracle):
    if value is None:return False
    gold=oracle["value"]
    # Explicit per-label rounding tolerance wins. Otherwise require close
    # agreement at the requested scale, never accept zero for nonzero gold.
    if gold!=0 and (value==0 or (value>0)!=(gold>0)):return False
    tolerance=oracle.get("abs_tolerance")
    if tolerance is None:
        tolerance=min(0.005,abs(gold)*0.005) if gold else 1e-9
    if not math.isfinite(tolerance) or tolerance<0:raise ValueError("Invalid oracle tolerance")
    return math.isclose(value,gold,rel_tol=0,abs_tol=tolerance+1e-12)

def grade(example,parsed):
    oracle=example["oracle"];allowed=set(example["allowed_citations"])
    result={"valid_json":parsed is not None,"numeric_correct":None,"unit_correct":None,
            "answerability_correct":None,"citation_precision":None,"citation_recall":None,
            "auto_pass":None,"manual_review_required":True}
    kind=oracle["kind"]
    if parsed is None:
        if kind in ("numeric","insufficient"):result["auto_pass"]=False
        return result
    citations=set(parsed["citations"])
    result["citation_ids_valid"]=citations<=allowed
    result["citation_precision"]=len(citations&allowed)/len(citations) if citations else 0.0
    if example["gold_citations"] is not None:
        gold=set(example["gold_citations"])
        result["citation_precision"]=len(citations&gold)/len(citations) if citations else 0.0
        result["citation_recall"]=len(citations&gold)/len(gold) if gold else None
    if kind=="numeric":
        result["answerability_correct"]=parsed["status"]=="answerable"
        v=parsed["value"]
        result["numeric_correct"]=numeric_matches(v,oracle)
        result["unit_correct"]=canonical_unit(parsed["unit"])==canonical_unit(oracle["unit"])
        result["auto_pass"]=bool(result["answerability_correct"] and result["numeric_correct"] and result["unit_correct"]
            and result["citation_ids_valid"] and citations==set(example["gold_citations"] or []))
        # Correct numeric result does not certify narrative financial interpretation.
    elif kind=="insufficient":
        result["answerability_correct"]=parsed["status"]=="insufficient"
        result["auto_pass"]=bool(result["answerability_correct"] and result["citation_ids_valid"] and citations==set(example["gold_citations"] or []))
    elif example["gold_citations"] is not None:
        result["answerability_correct"]=parsed["status"]=="answerable"
    return result

def aggregate(rows):
    out={"attempted":len(rows),"completed":sum(r["error"] is None for r in rows),"error_count":sum(r["error"] is not None for r in rows)}
    eligible=[r for r in rows if r["gold_oracle"]["kind"] in ("numeric","insufficient")]
    out["auto_eligible"]=len(eligible)
    out["auto_pass_end_to_end"]=sum(r["scores"].get("auto_pass") is True for r in eligible)/len(eligible) if eligible else None
    out["completion_rate"]=out["completed"]/len(rows) if rows else None
    for metric in ("valid_json","numeric_correct","unit_correct","answerability_correct","auto_pass","citation_precision","citation_recall"):
        v=[r["scores"][metric] for r in rows if r["scores"].get(metric) is not None]
        out[metric]={"scored":len(v),"mean":sum(v)/len(v) if v else None}
    lat=[r["latency_seconds"] for r in rows if r["error"] is None]
    out["mean_latency_seconds"]=sum(lat)/len(lat) if lat else None
    return out

def run(args,call=ollama):
    validate_endpoint(args.endpoint)
    source=Path(args.dataset)
    raw=read_jsonl(source)
    if args.kind=="synthetic":
        examples=[synthetic_example(x) for x in raw]
    else:
        examples=list(financebench_examples(raw,args.context,args.chunks,args.db,args.k))
    if args.limit:examples=examples[:args.limit]
    if not examples:raise ValueError("No evaluation examples")
    if len({x["id"] for x in examples})!=len(examples):raise ValueError("Duplicate IDs")
    output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
    results=[]
    with output.open("w",encoding="utf-8") as f:
        for ex in examples:
            start=time.monotonic();error=None;raw_output="";tokens={}
            try:
                if sum(len(m["content"]) for m in ex["messages"])>args.max_context_chars:
                    raise ValueError("Context exceeds configured character budget; refused rather than silently truncating")
                raw_output,tokens=call(ex["messages"],args.model,args.endpoint,args.timeout,args.temperature,args.num_ctx,args.max_tokens)
                if tokens.get("done_reason")=="length":raise ValueError("Model output truncated at generation limit")
            except Exception as e:
                error=f"{type(e).__name__}: {e}"
            parsed=parse_response(raw_output) if error is None else None
            row={"id":ex["id"],"group":ex["group"],"language_pair":ex["language_pair"],"variant":ex["variant"],
                 "model":args.model,"gold_answer":ex["gold_answer"],"gold_oracle":ex["oracle"],
                 "gold_citations":ex["gold_citations"],"allowed_citations":ex["allowed_citations"],
                 "prompt_sha256":hashlib.sha256(json.dumps(ex["messages"],ensure_ascii=False,sort_keys=True).encode()).hexdigest(),
                 "raw_response":raw_output,"prediction":parsed,"scores":grade(ex,parsed),
                 "error":error,"token_counts":tokens,"latency_seconds":round(time.monotonic()-start,4)}
            f.write(json.dumps(row,ensure_ascii=False)+"\n");f.flush();results.append(row)
    grouped={}
    for field in ("group","variant","language_pair"):
        groups=defaultdict(list)
        for r in results:groups[str(r[field])].append(r)
        grouped[field]={k:aggregate(v) for k,v in groups.items()}
    report={"model":args.model,"kind":args.kind,"context":args.context,"dataset_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
            "evaluated_ids":[r["id"] for r in results],"temperature":args.temperature,
            "num_ctx":args.num_ctx,"max_tokens":args.max_tokens,"max_context_chars":args.max_context_chars,
            "retrieval_k":args.k,"chunk_sha256":hashlib.sha256(Path(args.chunks).read_bytes()).hexdigest() if args.chunks else None,
            "index_sha256":hashlib.sha256(Path(args.db).read_bytes()).hexdigest() if args.db else None,
            "summary":aggregate(results),"breakdown":grouped,
            "warning":"auto_pass is a strict numeric/abstention/citation proxy, NOT overall financial answer correctness. All FinanceBench and qualitative examples require manual or separately verified grading. Character budgets do not guarantee token-fit; inspect reported prompt token counts."}
    output.with_suffix(".summary.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--kind",choices=("synthetic","financebench"),required=True)
    p.add_argument("--dataset",required=True);p.add_argument("--model",required=True)
    p.add_argument("--endpoint",default="http://127.0.0.1:11434");p.add_argument("--output",required=True)
    p.add_argument("--context",choices=("gold","lexical"),default="gold")
    p.add_argument("--chunks");p.add_argument("--db");p.add_argument("--k",type=int,default=10)
    p.add_argument("--limit",type=int,default=0);p.add_argument("--timeout",type=int,default=180)
    p.add_argument("--temperature",type=float,default=0);p.add_argument("--num-ctx",type=int,default=8192)
    p.add_argument("--max-tokens",type=int,default=1024);p.add_argument("--max-context-chars",type=int,default=14000)
    args=p.parse_args()
    print(json.dumps(run(args),indent=2,ensure_ascii=False))

if __name__=="__main__":main()
