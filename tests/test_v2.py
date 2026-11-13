import unittest
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
        base={"id":"old","case_id":"case","split":"train","source":"original_fictional_hand_authored","sector":"retail",
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
