import json
import unittest
from src.v2.evaluate import calculator_call

class ToolEvaluationTests(unittest.TestCase):
    def test_prediction_not_oracle(self):
        messages=[{"role":"system","content":"Answer."},{"role":"user","content":"[A] sales 90; cost 40. Profit?"}]
        plan={"status":"answerable","operands":{"sales":{"value":90,"evidence_id":"A","label":"sales"},"cost":{"value":40,"evidence_id":"A","label":"cost"}},"expression":"sales-cost","unit":"million_usd","citations":["A"]}
        calls=[]
        def generate(msgs):
            calls.append(msgs)
            return (json.dumps(plan) if len(calls)==1 else "final"),{"done_reason":"stop","eval_count":2}
        final,stats=calculator_call(messages,["A"],"en",generate)
        self.assertEqual(final,"final")
        self.assertEqual(stats["calculator_result"]["value"],50)
        self.assertIn("Application calculator result",calls[1][1]["content"])
        self.assertNotIn("Application calculator result",calls[0][1]["content"])
    def test_invalid_citation_refused(self):
        messages=[{"role":"system","content":"Answer."},{"role":"user","content":"Question"}]
        plan={"status":"insufficient","operands":{},"expression":None,"unit":None,"citations":["X"]}
        with self.assertRaises(ValueError):
            calculator_call(messages,["A"],"en",lambda _: (json.dumps(plan),{}))
    def test_insufficient_route(self):
        messages=[{"role":"system","content":"Answer."},{"role":"user","content":"Question"}]
        plan={"status":"insufficient","operands":{},"expression":None,"unit":None,"citations":["A"]}
        calls=[]
        def generate(msgs):
            calls.append(msgs)
            return (json.dumps(plan) if len(calls)==1 else "final"),{}
        _,stats=calculator_call(messages,["A"],"en",generate)
        self.assertIsNone(stats["calculator_result"])
        self.assertEqual(calls[1],messages)
