"""Normalize original FinanceBench, FinQA and TAT-QA benchmark QA into evaluation-only JSONL.

No cloud LLM calls, no fabricated labels. Requires network only for downloading the
original source files; --offline-dir accepts previously downloaded files.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

SOURCES={
 "financebench":("https://raw.githubusercontent.com/patronus-ai/financebench/main/data/financebench_open_source.jsonl","CC-BY-NC-4.0","open_source"),
 "finqa":("https://raw.githubusercontent.com/czyssrs/FinQA/main/dataset/test.json","CC-BY-4.0","test"),
 "tatqa":("https://raw.githubusercontent.com/NExTplusplus/TAT-QA/master/dataset_raw/tatqa_dataset_test_gold.json","CC-BY-4.0","test_gold")
}

def normalize_financebench(raw):
 return [dict(id=str(x["financebench_id"]),source_dataset="financebench",source_split="open_source",
              license="CC-BY-NC-4.0",question=x["question"],answer=x["answer"],
              task_type=x.get("question_reasoning") or x.get("question_type") or "other",
              source_doc_id=x.get("doc_name"),source_link=x.get("doc_link"),
              evidence=x.get("evidence",[]),
              metadata={"company":x.get("company"),"doc_period":x.get("doc_period"),"justification":x.get("justification")},
              usage="EVALUATION_ONLY") for x in raw]

def normalize_finqa(raw):
 out=[]
 for x in raw:
  qa=x.get("qa",{})
  if "exe_ans" not in qa or not qa.get("question"): continue
  out.append(dict(id="finqa:"+str(x["id"]),source_dataset="finqa",source_split="test",
                  license="CC-BY-4.0",question=qa["question"],answer=qa["exe_ans"],
                  task_type="numerical_program",source_doc_id=x.get("filename") or x.get("id"),
                  source_link="https://github.com/czyssrs/FinQA",
                  evidence={"pre_text":x.get("pre_text",[]),"post_text":x.get("post_text",[]),"table":x.get("table",[])},
                  metadata={"program":qa.get("program"),"gold_inds":qa.get("gold_inds"),"answer_text":qa.get("answer")},
                  usage="EVALUATION_ONLY"))
 return out

def normalize_tatqa(raw):
 out=[]
 for group in raw:
  table=group.get("table",{})
  doc_id=group.get("id") or (table.get("uid") if isinstance(table,dict) else None)
  for q in group.get("questions",[]):
   if "answer" not in q or not q.get("question"):continue
   out.append(dict(id="tatqa:"+str(q.get("uid") or hashlib.sha256(q["question"].encode()).hexdigest()[:18]),
                   source_dataset="tatqa",source_split="test_gold",license="CC-BY-4.0",
                   question=q["question"],answer=q["answer"],
                   task_type=q.get("answer_type") or "other",source_doc_id=doc_id or q.get("uid"),
                   source_link="https://github.com/NExTplusplus/TAT-QA",
                   evidence={"table":table,"paragraphs":group.get("paragraphs",[])},
                   metadata={"scale":q.get("scale"),"derivation":q.get("derivation"),"answer_from":q.get("answer_from")},
                   usage="EVALUATION_ONLY"))
 return out

NORMALIZE={"financebench":normalize_financebench,"finqa":normalize_finqa,"tatqa":normalize_tatqa}

def sample(rows,limit,seed):
 if limit>=len(rows):return sorted(rows,key=lambda x:x["id"])
 rank=lambda x:hashlib.sha256(f"{seed}|{x['id']}".encode()).hexdigest()
 by_doc=defaultdict(list)
 for row in rows:by_doc[str(row.get("source_doc_id") or row["id"])].append(row)
 first=[];later=[]
 for doc_rows in by_doc.values():
  items=sorted(doc_rows,key=rank)
  first.append(items[0]);later.extend(items[1:])
 def choose(pool,k):
  buckets=defaultdict(list)
  for row in pool:buckets[str(row["task_type"])].append(row)
  for items in buckets.values():items.sort(key=rank)
  out=[]
  while len(out)<k and any(buckets.values()):
   for key in sorted(buckets):
    if len(out)<k and buckets[key]:out.append(buckets[key].pop(0))
  return out
 got=choose(first,min(limit,len(first)))
 if len(got)<limit:got+=choose(later,limit-len(got))
 return sorted(got,key=lambda x:x["id"])

def build(out="real_eval",limit=150,seed=42,offline_dir=None):
 target=Path(out);target.mkdir(parents=True,exist_ok=True)
 manifest={"usage":"EVALUATION_ONLY","seed":seed,"cap_per_source":limit,"sources":{}}
 merged=[]
 for src,(url,license_name,split) in SOURCES.items():
  if offline_dir:
   name="financebench.jsonl" if src=="financebench" else src+".json"
   raw_bytes=(Path(offline_dir)/name).read_bytes()
  else:
   req=urllib.request.Request(url,headers={"User-Agent":"FinancialDocLab-Research/0.2"})
   with urllib.request.urlopen(req,timeout=120) as response:raw_bytes=response.read()
  records=([json.loads(line) for line in raw_bytes.decode().splitlines() if line.strip()]
           if src=="financebench" else json.loads(raw_bytes.decode()))
  candidates=NORMALIZE[src](records)
  selected=sample(candidates,limit,seed)
  with (target/(src+"_eval.jsonl")).open("w",encoding="utf-8") as f:
   for row in selected:f.write(json.dumps(row,ensure_ascii=False)+"\n")
  merged+=selected
  manifest["sources"][src]=dict(n_available=len(candidates),n_selected=len(selected),
      license=license_name,source_split=split,source_url=url,
      sha256=hashlib.sha256(raw_bytes).hexdigest(),
      task_distribution=dict(Counter(str(x["task_type"]) for x in selected)))
 (target/"eval_balanced.jsonl").write_text("".join(json.dumps(x,ensure_ascii=False)+"\n" for x in merged),encoding="utf-8")
 manifest["total"]=len(merged)
 (target/"eval_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
 assert all(r["usage"]=="EVALUATION_ONLY" for r in merged)
 return manifest

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--limit-per-source",type=int,default=150)
 p.add_argument("--seed",type=int,default=42)
 p.add_argument("--out",default="real_eval")
 p.add_argument("--offline-dir")
 a=p.parse_args()
 print(json.dumps(build(a.out,a.limit_per_source,a.seed,a.offline_dir),indent=2))
