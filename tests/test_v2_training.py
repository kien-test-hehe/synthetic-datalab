import unittest
from src.v2.training import tokenize_row,select_groups
from src.v2.runtime import run_plan

class FakeTokenizer:
    def apply_chat_template(self,messages,tokenize,add_generation_prompt,**kwargs):
        return [1,2,3] if add_generation_prompt else [1,2,3,4,5]
class Tests(unittest.TestCase):
    def test_mask(self):
        row={"id":"x","source":"original_fictional_hand_authored","split":"train","messages":[{"role":r,"content":"x"} for r in ("system","user","assistant")]}
        self.assertEqual(tokenize_row(FakeTokenizer(),row,5)["labels"],[-100,-100,-100,4,5])
        with self.assertRaises(ValueError):tokenize_row(FakeTokenizer(),row,4)
        row["split"]="dev"
        with self.assertRaises(ValueError):tokenize_row(FakeTokenizer(),row,5)
    def test_groups(self):
        rows=[{"id":str(i),"case_group":g} for i,g in enumerate(["a","a","b","b"])]
        result=select_groups(rows,3,42)
        self.assertEqual(len(result),2);self.assertEqual(len({r["case_group"] for r in result}),1)
    def test_runtime(self):
        plan={"status":"answerable","operands":{"x":{"value":5,"evidence_id":"A","label":"x"},"y":{"value":2,"evidence_id":"A","label":"y"}},"expression":"x-y","unit":"usd","citations":["A"]}
        self.assertEqual(run_plan(plan,["A"]),{"value":3.0,"unit":"usd"})
        with self.assertRaises(ValueError):run_plan(plan,["B"])
        plan["operands"]["y"]["evidence_id"]="B"
        with self.assertRaises(ValueError):run_plan(plan,["A"])
        self.assertIsNone(run_plan({"status":"insufficient","operands":{},"expression":None,"unit":None,"citations":["A"]},["A"]))
