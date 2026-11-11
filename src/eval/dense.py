"""Optional fully LOCAL multilingual dense embedding retrieval for FinanceBench.

Install: pip install numpy sentence-transformers
Examples:
  python -m src.eval.dense build --chunks real_eval/financebench/chunks.jsonl --model BAAI/bge-m3
  python -m src.eval.dense eval --qa real_eval/financebench/questions.jsonl \
      --chunks real_eval/financebench/chunks.jsonl --index real_eval/financebench/embeddings.npz \
      --model BAAI/bge-m3 --k 10

No cloud API and no training on benchmark answers.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from src.eval.financebench import read_jsonl


def score_retrieval(qa, outputs, k):
    total=0;doc_hits=0;page_hits=0;all_gold_pages=0
    for item,got in zip(qa,outputs):
        gold={(e.get("doc_name",item["doc_name"]),int(e["evidence_page_num"]))
              for e in item.get("evidence",[]) if e.get("evidence_page_num") is not None}
        if not gold:continue
        retrieved={(x["doc_id"],x["page"]) for x in got[:k]}
        total+=1
        doc_hits+=int(any(y[0] in {g[0] for g in gold} for y in retrieved))
        page_hits+=int(bool(retrieved & gold))
        all_gold_pages+=int(gold<=retrieved)
    if not total:raise ValueError("No QA items with gold evidence pages")
    return {"questions":total,"doc_recall_at_k":doc_hits/total,"page_recall_at_k":page_hits/total,
            "all_gold_pages_at_k":all_gold_pages/total}


def _dependencies():
    try:
        import numpy as np
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError("Requires local dependencies: pip install numpy sentence-transformers") from exc
    return np,SentenceTransformer


def make_index(chunks_path,index_path,model_name="BAAI/bge-m3",device=None,batch_size=16):
    np,SentenceTransformer=_dependencies()
    rows=read_jsonl(chunks_path)
    if any(r.get("source")!="original_pdf_page_text_only" for r in rows):
        raise ValueError("Only original PDF chunks can enter the benchmark index")
    model=SentenceTransformer(model_name,device=device)
    vectors=model.encode([r["text"] for r in rows],batch_size=batch_size,
            normalize_embeddings=True,convert_to_numpy=True,show_progress_bar=True)
    vectors=np.asarray(vectors,dtype=np.float32)
    if vectors.shape[0]!=len(rows):raise ValueError("Embedding row count mismatch")
    path=Path(index_path);path.parent.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(path,vectors=vectors,ids=np.asarray([r["chunk_id"] for r in rows]))
    metadata={"model":model_name,"rows":len(rows),"embedding_dims":int(vectors.shape[1]),
              "source":"original_pdf_chunks_only","note":"Do not insert QA answers or evidence annotations into embeddings."}
    (path.with_suffix(".manifest.json")).write_text(json.dumps(metadata,indent=2)+"\n",encoding="utf-8")
    return metadata


def dense_rank(embedding_matrix,query_vector,k,doc_ids=None,required_doc=None):
    """Dependency-free linear search helper for tests; numpy used in actual CLI."""
    scores=[sum(float(a)*float(b) for a,b in zip(vec,query_vector)) for vec in embedding_matrix]
    indices=range(len(scores))
    if required_doc is not None:
        indices=[i for i in indices if doc_ids[i]==required_doc]
    return sorted(indices,key=lambda i:(-scores[i],i))[:k]


def evaluate(qa_path,chunks_path,index_path,model_name,k=10,oracle_doc=False,
             include_company=False,device=None):
    np,SentenceTransformer=_dependencies()
    qa=read_jsonl(qa_path);rows=read_jsonl(chunks_path)
    z=np.load(index_path,allow_pickle=False)
    ids=[str(x) for x in z["ids"]]
    vecs=np.asarray(z["vectors"],dtype=np.float32)
    if ids!=[r["chunk_id"] for r in rows]:
        raise ValueError("Chunk ids/order differ from the embedding index; rebuild")
    manifest=json.loads(Path(index_path).with_suffix(".manifest.json").read_text())
    if manifest["model"]!=model_name:raise ValueError("Model mismatch with stored embeddings")
    model=SentenceTransformer(model_name,device=device)
    query_texts=[((x.get("company","")+" ") if include_company else "")+x["question"] for x in qa]
    qvecs=model.encode(query_texts,normalize_embeddings=True,convert_to_numpy=True,
        batch_size=16,show_progress_bar=True)
    outputs=[]
    for q,v in zip(qa,qvecs):
        sims=vecs @ np.asarray(v,dtype=np.float32)
        if oracle_doc:
            mask=np.array([r["doc_id"]==q["doc_name"] for r in rows])
            sims=np.where(mask,sims,-np.inf)
        idx=np.argsort(-sims,kind="stable")[:k]
        outputs.append([{"chunk_id":rows[int(i)]["chunk_id"],"doc_id":rows[int(i)]["doc_id"],
                         "page":rows[int(i)]["page"],"score":float(sims[int(i)])}
                        for i in idx if np.isfinite(sims[int(i)])])
    result=score_retrieval(qa,outputs,k)
    result.update({"retriever":"local_dense","embedding_model":model_name,"k":k,
                   "scope":"oracle_doc" if oracle_doc else "full_index",
                   "query_prefix":"company" if include_company else "question_only"})
    return result


def main():
    ap=argparse.ArgumentParser()
    sub=ap.add_subparsers(dest="action",required=True)
    b=sub.add_parser("build")
    b.add_argument("--chunks",required=True)
    b.add_argument("--index",default="real_eval/financebench/embeddings.npz")
    b.add_argument("--model",default="BAAI/bge-m3")
    b.add_argument("--device")
    b.add_argument("--batch-size",type=int,default=16)
    a=sub.add_parser("eval")
    a.add_argument("--qa",required=True)
    a.add_argument("--chunks",required=True)
    a.add_argument("--index",required=True)
    a.add_argument("--model",default="BAAI/bge-m3")
    a.add_argument("--device")
    a.add_argument("--k",type=int,default=10)
    a.add_argument("--oracle-doc",action="store_true")
    a.add_argument("--include-company",action="store_true")
    args=ap.parse_args()
    if args.action=="build":result=make_index(args.chunks,args.index,args.model,args.device,args.batch_size)
    else:result=evaluate(args.qa,args.chunks,args.index,args.model,args.k,args.oracle_doc,args.include_company,args.device)
    print(json.dumps(result,indent=2,ensure_ascii=False))


if __name__=="__main__":
    main()
