"""Run matched, explicitly local, untouched-model baselines on a pinned evaluation snapshot.

No cloud inference, downloads or auto-pulls. A model name is not proof of base
weights: operator must register the untouched model and verify its local digest.
Test is gated; no automatic model selection using test data.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import urllib.request
from pathlib import Path
from types import SimpleNamespace
from src.eval.model_eval import run, validate_endpoint, ollama
from src.eval.independent import SOURCE

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def local_models(endpoint):
    endpoint=validate_endpoint(endpoint)
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*args,**kwargs):return None
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    with opener.open(endpoint+"/api/tags",timeout=10) as r:
        data=json.loads(r.read())
    return {m.get("name",m.get("model")):m for m in data["models"]}

def matrix(args,discover=local_models,call=ollama):
    endpoint=validate_endpoint(args.endpoint)
    root=Path(args.dataset_root);manifest=json.loads((root/"manifest.json").read_text())
    if manifest["source"]!=SOURCE:raise ValueError("Independent evaluation manifest required")
    split=args.split
    if split=="test" and not args.unlock_test:raise ValueError("Test locked; freeze settings and pass --unlock-test explicitly")
    if split=="test" and args.limit:raise ValueError("Test cannot be subset-selected")
    dataset=root/(split+".jsonl")
    expected=manifest["splits"][split]
    if sha(dataset)!=expected["sha256"]:raise ValueError("Evaluation checksum mismatch")
    rows=[json.loads(s) for s in dataset.read_text().splitlines() if s.strip()]
    if len(rows)!=expected["rows"] or any(r["split"]!=split or r["source"]!=SOURCE for r in rows):
        raise ValueError("Evaluation split/provenance mismatch")
    registry=json.loads(Path(args.models).read_text())
    models=registry["models"]
    if not models or len({m["id"] for m in models})!=len(models):raise ValueError("Missing or duplicate model IDs")
    available=discover(endpoint)
    for m in models:
        if not m.get("untouched_attestation") or not m.get("digest"):raise ValueError("Untouched attestation and exact local digest required")
        if not m["id"].isalnum() and not all(c.isalnum() or c in "-_" for c in m["id"]):raise ValueError("Unsafe model ID")
        if available.get(m["name"],{}).get("digest")!=m["digest"]:raise ValueError("Local model missing or digest mismatch: "+m["name"])
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    config={"dataset_sha256":sha(dataset),"manifest_sha256":sha(root/"manifest.json"),
            "split":split,"limit":args.limit,"temperature":0,"num_ctx":args.num_ctx,
            "max_tokens":args.max_tokens,"max_context_chars":args.max_context_chars,"models":models}
    config_hash=hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest()
    config_path=out/"matrix_config.json"
    if config_path.exists():raise FileExistsError("Use a new output directory to prevent overwriting a baseline")
    config_path.write_text(json.dumps(config,indent=2)+"\n")
    results={}
    for m in models:
        # Recheck before each run: tags may have been changed since initial discovery.
        if discover(endpoint).get(m["name"],{}).get("digest")!=m["digest"]:raise ValueError("Model changed")
        run_args=SimpleNamespace(kind="synthetic",dataset=str(dataset),model=m["name"],endpoint=endpoint,
             output=str(out/(m["id"]+".jsonl")),context="gold",chunks=None,db=None,k=10,
             limit=args.limit,timeout=args.timeout,temperature=0,num_ctx=args.num_ctx,
             max_tokens=args.max_tokens,max_context_chars=args.max_context_chars)
        report=run(run_args,call=call)
        if discover(endpoint).get(m["name"],{}).get("digest")!=m["digest"]:raise ValueError("Model changed during evaluation")
        results[m["id"]]={"model":m["name"],"digest":m["digest"],"summary":report["summary"]}
        (out/"matrix_results.json").write_text(json.dumps({"config_sha256":config_hash,"results":results,
           "complete":len(results)==len(models),"note":"Automated proxy only; untouched provenance attested by operator, not proven by digest."},indent=2)+"\n")
    return results

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--dataset-root",default="evaluation/independent/exports")
    p.add_argument("--models",required=True);p.add_argument("--output",required=True)
    p.add_argument("--endpoint",default="http://127.0.0.1:11434")
    p.add_argument("--split",choices=("dev","test"),default="dev");p.add_argument("--unlock-test",action="store_true")
    p.add_argument("--limit",type=int,default=0);p.add_argument("--timeout",type=int,default=180)
    p.add_argument("--num-ctx",type=int,default=8192);p.add_argument("--max-tokens",type=int,default=1024)
    p.add_argument("--max-context-chars",type=int,default=14000)
    a=p.parse_args()
    if a.limit<0 or min(a.timeout,a.num_ctx,a.max_tokens,a.max_context_chars)<=0:p.error("Invalid limits")
    print(json.dumps(matrix(a),indent=2))
if __name__=="__main__":main()
