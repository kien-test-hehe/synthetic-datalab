import unittest
import json
from src.v2.calculator import calculate
from src.v2.build import canonical,direct,calculator_rows

class CalculatorTests(unittest.TestCase):
    def test_safe(self):
        self.assertAlmostEqual(calculate("(current-previous)/previous*100",{"current":1000,"previous":800}),25)
    def test_reject(self):
        for expr,ops in [("__import__('os')",{"x":1}),("x**2",{"x":2}),("x/0",{"x":2}),("x+y",{"x":2}),("x",{"x":True}),("x",{"x":float("nan")}),("x",{"x":2,"y":3}),("x+999",{"x":2})]:
            with self.subTest(expr=expr),self.assertRaises(ValueError):
                calculate(expr,ops)

class CanonicalTests(unittest.TestCase):
    def fixture(self):
        base={"id":"old","question":"Growth?","case_id":"case","split":"train","source":"original_fictional_hand_authored","sector":"retail",
              "evidence":[{"id":"A","text":"Revenue 2025 100; 2024 80."}],"accounting_assumptions":"USD","oracle":{"kind":"numeric","value":25,"unit":"percent"}}
        rec={"parent_id":"old","question":"Growth?","task":"basic_reasoning","difficulty":"easy","language":{"context":"en","question":"en","answer":"en"},
             "gold":{"answer":"25%.","short":["(100-80)/80*100."],"detailed":["Use A's current and prior values."],"citations":["A"],
                     "program":{"expression":"(current-prior)/prior*100","operands":{"current":{"value":100,"evidence_id":"A","label":"2025"},"prior":{"value":80,"evidence_id":"A","label":"2024"}}}}}
        return rec,base
    def test_exports(self):
        rec,base=self.fixture();r=canonical(rec,base)
        self.assertEqual(r["case_group"],"case")
        d=direct(r,"lite");self.assertEqual([m["role"] for m in d["messages"]],["system","user","assistant"])
        self.assertNotIn("25%",d["messages"][1]["content"])
        c=calculator_rows(r,"lite");self.assertEqual(len(c),2)
        self.assertNotIn("Application calculator result",c[0]["messages"][1]["content"])
        self.assertIn("Application calculator result",c[1]["messages"][1]["content"])
    def test_explicit_assumptions(self):
        rec,base=self.fixture()
        base["accounting_assumptions"]="USD; comparison base 80."
        rec["gold"]["program"]["operands"]["prior"]["evidence_id"]="@assumptions"
        self.assertEqual(canonical(rec,base)["oracle"]["value"],25)
        base["accounting_assumptions"]="USD; comparison base missing."
        with self.assertRaises(ValueError):canonical(rec,base)
    def test_bad_operand(self):
        rec,base=self.fixture();rec["gold"]["program"]["operands"]["prior"]["value"]=70
        with self.assertRaises(ValueError):canonical(rec,base)
    def test_bad_citation(self):
        rec,base=self.fixture();rec["gold"]["citations"]=["B"]
        with self.assertRaises(ValueError):canonical(rec,base)
    def test_no_program(self):
        rec,base=self.fixture();del rec["gold"]["program"]
        with self.assertRaises(ValueError):canonical(rec,base)
    def test_wrong_split(self):
        rec,base=self.fixture();base["split"]="test"
        with self.assertRaises(ValueError):canonical(rec,base)

    def test_answer_only_preserves_abstention_fields(self):
        rec,base=self.fixture()
        base["oracle"]={"kind":"insufficient"}
        rec["task"]="abstention"
        rec["gold"]={"answer":"Insufficient evidence.","short":["Not supplied."],"detailed":["[A] Prior costs are missing."],"citations":["A"],"missing":["Prior costs"]}
        r=canonical(rec,base)
        a=json.loads(direct(r,"lite",True)["messages"][-1]["content"])
        self.assertEqual(a["status"],"insufficient")
        self.assertIn("Prior costs",a["answer"])
        self.assertNotIn("Not supplied.",a["answer"])

    def test_answer_only_preserves_multiple_results(self):
        rec,base=self.fixture()
        base["oracle"]={"kind":"multi_numeric","results":[{"metric":"current","value":100,"unit":"million_usd"},{"metric":"prior","value":80,"unit":"million_usd"}]}
        rec["task"]="multi_result"
        rec["gold"]={"answer":"100 and 80.","short":["Read the two periods."],"detailed":["[A] Use the two disclosed values."],"citations":["A"],"results":[{"name":n,"value":v,"unit":"million_usd","program":{"expression":n,"operands":{n:{"value":v,"evidence_id":"A","label":n}}}} for n,v in [("current",100),("prior",80)]]}
        r=canonical(rec,base)
        a=json.loads(direct(r,"reasoning",True)["messages"][-1]["content"])
        self.assertIsNone(a["value"])
        self.assertIsNone(a["unit"])
        self.assertIn('"name": "current"',a["answer"])
        self.assertNotIn('"program"',a["answer"])

    def test_question_operand_requires_original_parameter(self):
        rec,base=self.fixture()
        base["question"]="Growth versus 80?"
        rec["question"]="Compare against 80; growth?"
        rec["gold"]["program"]["operands"]["prior"]["evidence_id"]="@question"
        self.assertEqual(canonical(rec,base)["oracle"]["value"],25)
        base["question"]="Growth?"
        with self.assertRaises(ValueError):canonical(rec,base)

    def test_decimal_comma_assumption(self):
        from src.v2.calculator import assumption_has_number
        self.assertTrue(assumption_has_number("Giá 1,8 triệu",1.8))
        self.assertFalse(assumption_has_number("Giá 1,8 triệu",1.9))


def test_bounded_bid_calculation():
    assert calculate("floor(min(economic,budget)/step)*step",{"economic":34.258385,"budget":55,"step":1})==34
    import pytest
    with pytest.raises(ValueError):calculate("floor(x, x)",{"x":1})
    with pytest.raises(ValueError):calculate("min(x,x,x)",{"x":1})
    with pytest.raises(ValueError):calculate("max(x,x)",{"x":1})
