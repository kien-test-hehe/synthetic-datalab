import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from src.eval.financebench import (
    qa_manifest, chunk_text, build_fts, retrieve, eval_retrieval, fts_query
)
from src.eval.dense import dense_rank, score_retrieval


class FinanceBenchLocalEvalTests(unittest.TestCase):
    def test_chunking_preserves_page_context(self):
        raw="Company XYZ. " + ("Consolidated revenue and operating profit. " * 90)
        spans=chunk_text(raw,max_chars=240,overlap=30)
        self.assertGreater(len(spans),4)
        self.assertTrue(all(0<=a<b and len(t)>0 for a,b,t in spans))
        self.assertLess(max(len(s) for a,b,s in spans),260)

    def test_qa_manifest_and_no_training_metadata(self):
        fake=[{"financebench_id":"q1","doc_name":"EXAMPLE_2025_10K",
               "question":"How much?","answer":"100","evidence":[{"evidence_page_num":3}]}]
        result=qa_manifest(fake)
        self.assertEqual(result["published_question_count"],1)
        self.assertEqual(result["required_pdf_stems"],["EXAMPLE_2025_10K"])
        self.assertEqual(result["usage"],"EVALUATION_ONLY")
        with self.assertRaises(ValueError):
            qa_manifest(fake+fake)

    def test_fts5_answer_is_not_indexed(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            records=[
                {"chunk_id":"REPORT_A:p1:c0","doc_id":"REPORT_A","page":1,
                 "text":"Revenue in fiscal year 2025 was 1200 USD million.",
                 "source":"original_pdf_page_text_only"},
                {"chunk_id":"REPORT_B:p1:c0","doc_id":"REPORT_B","page":1,
                 "text":"Administrative costs increased during the quarter.",
                 "source":"original_pdf_page_text_only"}
            ]
            chunks=root/"chunks.jsonl"
            chunks.write_text("".join(json.dumps(x)+"\n" for x in records))
            db=root/"fts.db"
            report=build_fts(chunks,db)
            self.assertEqual(report["indexed_chunks"],2)
            with sqlite3.connect(db) as con:
                hits=retrieve(con,"revenue fiscal year 2025",k=2)
                self.assertEqual(hits[0]["doc_id"],"REPORT_A")
                self.assertEqual(hits[0]["page"],1)
            qa=[{"financebench_id":"q1","doc_name":"REPORT_A","question":"What was fiscal revenue in 2025?",
                 "company":"Report A", "answer":"secret_gold_not_indexed",
                 "evidence":[{"doc_name":"REPORT_A","evidence_page_num":1}]}]
            qpath=root/"questions.jsonl";qpath.write_text(json.dumps(qa[0])+"\n")
            metrics=eval_retrieval(qpath,db,k=2)
            self.assertEqual(metrics["evaluated_questions"],1)
            self.assertEqual(metrics["page_recall_at_k"],1)
            with sqlite3.connect(db) as con:
                self.assertFalse(retrieve(con,"secret_gold_not_indexed",k=1))

    def test_dense_scoring_without_model_downloads(self):
        rank=dense_rank([[1,0],[0,1],[.8,.2]],[1,0],k=2)
        self.assertEqual(rank,[0,2])
        qa=[{"doc_name":"A","evidence":[{"evidence_page_num":3,"doc_name":"A"}]}]
        got=[[{"doc_id":"A","page":3}]]
        self.assertEqual(score_retrieval(qa,got,1)["page_recall_at_k"],1)

if __name__=="__main__":
    unittest.main()
