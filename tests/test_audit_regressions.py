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

    def test_m1_oracles_cover_all_original_rows(self):
        from pathlib import Path
        from src.authored_export import read_jsonl
        from src.m1_oracles import ORACLES, m1_oracle
        all_rows=[r for split in ("train","dev","test")
                  for r in read_jsonl(Path("sft/m1/exports")/(split+".jsonl"))]
        self.assertEqual(set(ORACLES),{r["id"] for r in all_rows})
        self.assertEqual(m1_oracle("M1-IS02-01")["value"],25)
        self.assertEqual(m1_oracle("M1-IS02-02")["value"],8)
        self.assertEqual(m1_oracle("M1-NT32-01")["value"],60)
        self.assertEqual(m1_oracle("M1-IS05-01")["kind"],"multi_numeric")
        for row in all_rows:
            self.assertEqual(m1_oracle(row["id"])["kind"]=="insufficient",
                             row["answerability"]=="insufficient")

    def test_source_language_review_preserves_intent(self):
        from src.authored_language import case_language_metadata, REVIEWED_EN_CASES, screen_language
        self.assertEqual(len(REVIEWED_EN_CASES),131)
        c={"case_id":"A027-26","language_pair":"vi-en",
           "evidence":[{"text":"Bank parent owns 80%."}]}
        q={"question":"Find ownership remaining.","answer":"20%."}
        out=case_language_metadata(c,q)
        self.assertEqual(out["declared_language_pair"],"vi-en")
        self.assertEqual(out["language_pair"],"en-en")
        self.assertEqual(out["evidence_language"],"en")
        self.assertEqual(out["question_language"],"unreviewed")
        self.assertEqual(out["question_language_candidate"],"en_candidate")
        self.assertEqual(out["answer_language_candidate"],"numeric_or_unit")
        self.assertEqual(screen_language("Tính doanh thu cuối kỳ?"),"vi_candidate")

    def test_unit_registry_scale_and_context(self):
        from src.financial_units import (RAW_AUTHORED_UNITS, canonical_unit,
            normalize_oracle, numeric_matches)
        self.assertEqual(len(RAW_AUTHORED_UNITS),144)
        self.assertEqual(canonical_unit("litres"),"liters")
        self.assertEqual(canonical_unit("tonnes_co2e"),"tco2e")
        self.assertNotEqual(canonical_unit("percent"),canonical_unit("pp"))
        self.assertNotEqual(canonical_unit("million_usd"),canonical_unit("usd"))
        self.assertNotEqual(canonical_unit("billion_vnd"),canonical_unit("million_vnd"))
        self.assertNotEqual(canonical_unit("usd_per_room_night","A015-17-a"),
                            canonical_unit("usd_per_room_night","A021-15-c"))
        o=normalize_oracle({"kind":"numeric","value":95,"unit":"usd_per_room_night"},"A015-17-a")
        self.assertEqual(o["unit"],"usd_per_available_room_night")
        self.assertEqual(o["original_unit"],"usd_per_room_night")
        self.assertEqual(o["value"],95)
        self.assertEqual(normalize_oracle(o,"A015-17-a"),o)
        self.assertFalse(numeric_matches(100.001,{"value":100,"unit":"claims"}))
        self.assertTrue(numeric_matches(100,{"value":100,"unit":"claims"}))
        self.assertFalse(numeric_matches(0,{"value":0.01,"unit":"million_usd"}))
        self.assertFalse(numeric_matches(float("inf"),{"value":1,"unit":"times"}))
        self.assertFalse(numeric_matches(True,{"value":1,"unit":"times"}))
