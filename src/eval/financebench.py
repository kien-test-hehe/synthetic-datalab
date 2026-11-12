"""Local FinanceBench QA + PDF ingestion, page-aware chunking and FTS5 retrieval eval.

Published QA and PDF source data are EVALUATION ONLY. No answers, evidence snippets
or annotations enter chunk text, training data, DPO or synthetic world generation.

Requires internet ONLY to download published source files, then runs offline.
PDF parsing: optional PyMuPDF (pip install pymupdf). Retrieval: SQLite FTS5 stdlib.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import urllib.request
from collections import Counter
from pathlib import Path

QA_URL = "https://raw.githubusercontent.com/patronus-ai/financebench/main/data/financebench_open_source.jsonl"
PDF_BASE = "https://raw.githubusercontent.com/patronus-ai/financebench/main/pdfs/"
REPO = "https://github.com/patronus-ai/financebench"
DOC_RX = re.compile(r"^[A-Za-z0-9_.-]+$")


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def read_jsonl(path):
    return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]


def qa_manifest(qa):
    ids=[x["financebench_id"] for x in qa]
    docs=sorted(set(x["doc_name"] for x in qa))
    if len(ids)!=len(set(ids)):
        raise ValueError("Duplicate official QA identifier")
    if any(not DOC_RX.fullmatch(name) for name in docs):
        raise ValueError("Unexpected document filename in source data")
    return {
        "published_question_count":len(qa),
        "required_pdf_count":len(docs),
        "required_pdf_stems":docs,
        "usage":"EVALUATION_ONLY",
        "license_of_published_qa":"CC-BY-NC-4.0",
        "pdf_rights":"CHECK separately; published QA license does not grant blanket rights to PDFs",
        "upstream_qa":QA_URL,
        "upstream_repo":REPO,
    }


def fetch(url, timeout=90):
    req=urllib.request.Request(url,headers={"User-Agent":"FinancialDocLab/0.3 (noncommercial research)"})
    with urllib.request.urlopen(req,timeout=timeout) as response:
        return response.read()


def download_qa(path):
    b=fetch(QA_URL)
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(b)
    qa=read_jsonl(path)
    meta=qa_manifest(qa)
    meta["sha256"]=sha256_bytes(b)
    (path.parent/"qa_manifest.json").write_text(json.dumps(meta,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return meta


def download_pdfs(qa_path, out_dir, limit=0, acknowledge_rights=False):
    if not acknowledge_rights:
        raise PermissionError("Explicit --acknowledge-rights required. Verify the rights applicable to upstream PDFs.")
    qa=read_jsonl(qa_path); names=qa_manifest(qa)["required_pdf_stems"]
    out=Path(out_dir);out.mkdir(parents=True,exist_ok=True)
    report={"requested_pdf_count":len(names),"downloads":[]}
    for stem in names[:limit or None]:
        path=out/(stem+".pdf")
        if path.exists() and path.stat().st_size>100:
            b=path.read_bytes();status="cached"
        else:
            b=fetch(PDF_BASE+stem+".pdf")
            if not b.startswith(b"%PDF"):
                raise ValueError(f"Invalid PDF header for {stem}")
            path.write_bytes(b);status="downloaded"
        report["downloads"].append({
            "doc_name":stem,"status":status,"size_bytes":len(b),
            "sha256":sha256_bytes(b),"url":PDF_BASE+stem+".pdf"
        })
    (out/"pdf_checksums.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    return report


def chunk_text(text: str, max_chars=1200, overlap=160):
    if max_chars<50 or overlap<0 or overlap>=max_chars:
        raise ValueError("Invalid char chunk parameters")
    text=" ".join(text.split())
    if not text: return []
    out=[];start=0
    while start<len(text):
        end=min(start+max_chars,len(text))
        if end<len(text):
            position=text.rfind(" ",start+max_chars//2,end)
            if position>start+max_chars//2:end=position
        segment=text[start:end].strip()
        if segment:out.append((start,end,segment))
        if end==len(text):break
        next_start=max(start+1,end-overlap)
        while next_start>start+1 and text[next_start-1].isalnum() and text[next_start].isalnum():
            next_start-=1
        start=next_start
    return out


def pdf_to_chunks(pdf_path, doc_id, max_chars=1200, overlap=160):
    try:
        import fitz  # PyMuPDF, optional
    except ImportError as exc:
        raise RuntimeError("pip install pymupdf to parse PDF pages") from exc
    records=[];empty_pages=0
    with fitz.open(str(pdf_path)) as pdf:
        for page_index,page in enumerate(pdf):
            # PDF physical page numbering, 1-based. Do not infer printed page numbers.
            blocks=page.get_text("blocks",sort=True)
            text="\n".join(str(b[4]) for b in blocks if len(b)>6 and b[6]==0)
            page_parts=chunk_text(text,max_chars=max_chars,overlap=overlap)
            if not page_parts:empty_pages+=1
            for cidx,(begin,end,segment) in enumerate(page_parts):
                records.append({
                    "chunk_id":f"{doc_id}:p{page_index+1}:c{cidx}",
                    "doc_id":doc_id,"page":page_index+1,
                    "start_char":begin,"end_char":end,"text":segment,
                    "source":"original_pdf_page_text_only"
                })
    return records,empty_pages


def parse_corpus(pdf_dir, out_path, max_chars=1200, overlap=160):
    root=Path(pdf_dir)
    files=sorted(root.glob("*.pdf"))
    if not files:raise FileNotFoundError("No PDFs found in folder")
    out=Path(out_path);out.parent.mkdir(parents=True,exist_ok=True)
    chunks=0;empty_pages=0
    with out.open("w",encoding="utf-8") as fd:
        for path in files:
            doc_id=path.stem
            docs,empty=pdf_to_chunks(path,doc_id,max_chars,overlap)
            for row in docs:
                fd.write(json.dumps(row,ensure_ascii=False)+"\n")
            chunks+=len(docs);empty_pages+=empty
    return {"pdfs":len(files),"chunks":chunks,"empty_or_unextractable_pages":empty_pages,
        "note":"Image-only pages need a separate OCR/PDF-vision path; no OCR is silently invented."}


def build_fts(chunks_path, db_path):
    db_path=Path(db_path);db_path.parent.mkdir(parents=True,exist_ok=True)
    if db_path.exists():db_path.unlink()
    conn=sqlite3.connect(db_path)
    try:
        conn.execute("CREATE VIRTUAL TABLE chunks_fts USING fts5("
            "chunk_id UNINDEXED, doc_id UNINDEXED, page UNINDEXED, text, "
            "tokenize='unicode61 remove_diacritics 2')")
        n=0
        for r in read_jsonl(chunks_path):
            if r.get("source")!="original_pdf_page_text_only":
                raise ValueError("Indexing only original PDF text chunks is permitted")
            conn.execute("INSERT INTO chunks_fts(chunk_id,doc_id,page,text) VALUES (?,?,?,?)",
                         (r["chunk_id"],r["doc_id"],int(r["page"]),r["text"]))
            n+=1
        conn.commit()
    finally:
        conn.close()
    return {"indexed_chunks":n,"db_path":str(db_path),"retriever":"sqlite_fts5_bm25"}


STOP={"the","what","was","were","for","from","that","this","with","which","does",
      "how","and","are","did","has","have","its","can","give","based","according",
      "please","estimate","calculate","year","fiscal","financial","company","of","in",
      "to","on","a","an","as","by","at","or","is","be"}


def fts_query(q: str, term_limit=24) -> str:
    words=re.findall(r"[^\W_]+",q.casefold(),flags=re.UNICODE)
    seen=set();kept=[]
    for word in words:
        if len(word)<2 or word in STOP or word in seen:continue
        seen.add(word);kept.append('"'+word+'"')
        if len(kept)>=term_limit:break
    return " OR ".join(kept)


def retrieve(conn, query, k=10, doc_id=None):
    needle=fts_query(query)
    if not needle:return []
    where="chunks_fts MATCH ?"
    params=[needle]
    if doc_id:
        where+=" AND doc_id = ?"
        params.append(doc_id)
    sql=f"SELECT chunk_id,doc_id,page,bm25(chunks_fts) AS score FROM chunks_fts WHERE {where} ORDER BY score LIMIT ?"
    params.append(k)
    return [{"chunk_id":x[0],"doc_id":x[1],"page":int(x[2]),"score":float(x[3])}
            for x in conn.execute(sql,params)]


def gold_pages(item):
    """Official FinanceBench indices are zero-based; stored PDF pages are one-based."""
    return {(e.get("doc_name") or item["doc_name"], int(e["evidence_page_num"]) + 1)
            for e in item.get("evidence", []) if e.get("evidence_page_num") is not None}


def eval_retrieval(qa_path,db_path,k=10,oracle_doc=False,include_company=False):
    qas=read_jsonl(qa_path)
    stats=Counter();samples=[];conn=sqlite3.connect(db_path)
    try:
        for item in qas:
            evidence=item.get("evidence") or []
            gold=gold_pages(item)
            if not gold:continue
            query=(item.get("company","")+" "+item["question"] if include_company
                    else item["question"])
            got=retrieve(conn,query,k=k,doc_id=item["doc_name"] if oracle_doc else None)
            predicted={(x["doc_id"],x["page"]) for x in got}
            page_hit=bool(gold & predicted)
            all_pages=gold<=predicted
            doc_hit=any(x["doc_id"] in {y[0] for y in gold} for x in got)
            stats["questions"]+=1
            stats["page_hit"]+=int(page_hit)
            stats["all_gold_pages"]+=int(all_pages)
            stats["doc_hit"]+=int(doc_hit)
            samples.append({"id":item["financebench_id"],"gold":sorted(gold),
                            "retrieved":got,"page_hit":page_hit,
                            "all_gold_pages":all_pages,"doc_hit":doc_hit})
    finally:
        conn.close()
    n=max(stats["questions"],1)
    return {
        "source":"official_financebench_published_QA",
        "retriever":"SQLite FTS5 BM25 lexical baseline",
        "scope":"oracle_doc_only" if oracle_doc else "full_index",
        "query_prefix":"company" if include_company else "question_only",
        "top_k":k,"evaluated_questions":stats["questions"],
        "doc_recall_at_k":stats["doc_hit"]/n,
        "page_recall_at_k":stats["page_hit"]/n,
        "all_gold_pages_at_k":stats["all_gold_pages"]/n,
        "page_numbering":"one_based_physical_pdf; official zero-based gold converted",
        "per_question":samples,
    }


def main():
    p=argparse.ArgumentParser(description="FinanceBench local ingestion and lexical retrieval benchmark")
    sub=p.add_subparsers(dest="command",required=True)
    a=sub.add_parser("download-qa");a.add_argument("--out",default="real_eval/financebench/questions.jsonl")
    a=sub.add_parser("download-pdfs");a.add_argument("--qa",required=True);a.add_argument("--out",default="real_eval/financebench/pdfs");a.add_argument("--limit",type=int,default=0);a.add_argument("--acknowledge-rights",action="store_true")
    a=sub.add_parser("parse");a.add_argument("--pdfs",required=True);a.add_argument("--out",default="real_eval/financebench/chunks.jsonl");a.add_argument("--chars",type=int,default=1200);a.add_argument("--overlap",type=int,default=160)
    a=sub.add_parser("index");a.add_argument("--chunks",required=True);a.add_argument("--db",default="real_eval/financebench/fts.sqlite")
    a=sub.add_parser("eval");a.add_argument("--qa",required=True);a.add_argument("--db",required=True);a.add_argument("--k",type=int,default=10);a.add_argument("--oracle-doc",action="store_true");a.add_argument("--include-company",action="store_true");a.add_argument("--out")
    args=p.parse_args()
    if args.command=="download-qa":result=download_qa(args.out)
    elif args.command=="download-pdfs":result=download_pdfs(args.qa,args.out,args.limit,args.acknowledge_rights)
    elif args.command=="parse":result=parse_corpus(args.pdfs,args.out,args.chars,args.overlap)
    elif args.command=="index":result=build_fts(args.chunks,args.db)
    else:
        result=eval_retrieval(args.qa,args.db,args.k,args.oracle_doc,args.include_company)
        if args.out:
            Path(args.out).parent.mkdir(parents=True,exist_ok=True)
            Path(args.out).write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
            result={k:v for k,v in result.items() if k!="per_question"}
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
