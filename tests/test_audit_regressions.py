import unittest
from src.eval.financebench import gold_pages
from src.eval.dense import score_retrieval
from src.eval.model_eval import numeric_matches, canonical_unit, parse_response
from src.m4.experiments import structured_row

class AuditRegressionTests(unittest.TestCase):
    def test_page_zero_is_first_physical_page(self):
        qa=[{"doc_name":"D","evidence":[{"evidence_page_num":0},{"evidence_page_num":2}]}]
        self.assertEqual(gold_pages(qa[0]),{("D",1),("D",3)})
        good=[[{"doc_id":"D","page":1},{"doc_id":"D","page":3}]]
        bad=[[{"doc_id":"D","page":0},{"doc_id":"D","page":2}]]
        self.assertEqual(score_retrieval(qa,good,2)["all_gold_pages_at_k"],1)
        self.assertEqual(score_retrieval(qa,bad,2)["page_recall_at_k"],0)

    def test_numeric_tolerance_and_alias(self):
        self.assertFalse(numeric_matches(0,{"value":0.01}))
        self.assertFalse(numeric_matches(-0.01,{"value":0.01}))
        self.assertTrue(numeric_matches(0.333,{"value":1/3}))
        self.assertEqual(canonical_unit("ratio"),canonical_unit("times"))

    def test_structured_answer_keeps_original_text(self):
        row={"answer":"Worked result.\\nEvidence: [A]".replace("\\n","\n"),
             "oracle":{"kind":"numeric","value":2,"unit":"times"},
             "evidence_ids":["A"],"messages":[{"role":"system","content":"original"},
                 {"role":"user","content":"context"},{"role":"assistant","content":"old"}]}
        r=structured_row(row)
        result=parse_response(r["messages"][2]["content"])
        self.assertEqual(result["value"],2)
        self.assertEqual(result["citations"],["A"])
        self.assertEqual(result["answer"],"Worked result.")
        self.assertEqual(row["messages"][2]["content"],"old")
