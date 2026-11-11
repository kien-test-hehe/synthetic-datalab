"""Run a pre-SFT baseline against M1 held-out QA using a LOCAL Ollama server.

No cloud APIs. This script does NOT train models, and never touches real-company eval docs.
The simple automatic indicators are NOT reliable substitutes for financial QA judging.
"""
from __future__ import annotations
import argparse
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

def call_ollama(messages, model, endpoint, timeout, temperature):
    url=endpoint.rstrip("/")+"/api/chat"
    payload={"model":model,"messages":messages,"stream":False,"options":{"temperature":temperature}}
    req=urllib.request.Request(url,data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=timeout) as response:
        reply=json.loads(response.read().decode("utf-8"))
    return reply.get("message",{}).get("content","")

def run(args):
    inputs=[json.loads(line) for line in Path(args.dataset).read_text(encoding="utf-8").splitlines() if line.strip()]
    if args.max_rows>0: inputs=inputs[:args.max_rows]
    Path(args.output).parent.mkdir(parents=True,exist_ok=True)
    indicators={"count":0,"error":0,"has_any_gold_citation":0,"has_all_gold_citations":0}
    with Path(args.output).open("w",encoding="utf-8") as out:
        for row in inputs:
            start=time.monotonic()
            try:
                response=call_ollama(row["messages"][:2],args.model,args.endpoint,args.timeout,args.temperature)
                err=None
            except (urllib.error.URLError,ValueError,TimeoutError) as exc:
                response="";err=f"{type(exc).__name__}: {exc}"
            citations=[f"[{s}]" for s in row["evidence_ids"]]
            rec={
                "id":row["id"],"case_id":row["case_id"],"split":row["split"],"model":args.model,
                "response":response,"gold_answer":row["answer"],
                "gold_evidence_ids":row["evidence_ids"],"expected_answerability":row["answerability"],
                "latency_seconds":round(time.monotonic()-start,3),
                "error":err,
                "has_any_gold_citation":any(s in response for s in citations),
                "has_all_gold_citations":bool(citations) and all(s in response for s in citations),
                "automatic_correctness":"NOT_SCORED__MANUAL_OR_VERIFIED_JUDGE_REQUIRED"
            }
            out.write(json.dumps(rec,ensure_ascii=False)+"\n")
            indicators["count"]+=1
            if err:indicators["error"]+=1
            if rec["has_any_gold_citation"]:indicators["has_any_gold_citation"]+=1
            if rec["has_all_gold_citations"]:indicators["has_all_gold_citations"]+=1
            print(f"{indicators['count']}/{len(inputs)} {row['id']} {rec['latency_seconds']}s",flush=True)
    print(json.dumps(indicators,indent=2))
    print("NOTE: citation indicators are NOT financial answer accuracy; manually grade answers and numeric calculations.")

if __name__=="__main__":
    p=argparse.ArgumentParser(description="Evaluate local Ollama model on fully synthetic SFT M1 holdout")
    p.add_argument("--dataset",default="sft/m1/exports/test.jsonl")
    p.add_argument("--model",required=True,help="Locally installed Ollama model name")
    p.add_argument("--endpoint",default="http://127.0.0.1:11434")
    p.add_argument("--output",default="reports/m1_model_baseline.jsonl")
    p.add_argument("--temperature",type=float,default=0)
    p.add_argument("--max-rows",type=int,default=0)
    p.add_argument("--timeout",type=int,default=180)
    run(p.parse_args())
