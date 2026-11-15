import unittest
from src.financial_calculations import verify_graph

class GraphTests(unittest.TestCase):
    def test_rejects_missing_citation_or_anchor(self):
        r={"id":"q","oracle":{"kind":"numeric","value":10,"unit":"million_usd"},"evidence_ids":["A"],"evidence":[{"id":"A","text":"Cash 10"}]}
        operand={"value":10,"unit":"million_usd","evidence_id":"A","quote":"Cash 10","literal":"10","scope":"cash","period":"current","format":"decimal"}
        g={"id":"q","expression":"cash","result_unit":"million_usd","operands":{"cash":operand}}
        self.assertEqual(verify_graph(r,g),10)
        with self.assertRaises(AssertionError):verify_graph({**r,"evidence_ids":[]},g)
        with self.assertRaises(AssertionError):verify_graph({**r,"evidence":[{"id":"A","text":"Cash 12"}]},g)
        bad={**g,"expression":"cash+1"}
        with self.assertRaises(AssertionError):verify_graph(r,bad)
