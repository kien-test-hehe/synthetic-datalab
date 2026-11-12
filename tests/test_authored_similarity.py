import unittest
from src.authored_similarity import screen_pairs,shape

class SimilarityTests(unittest.TestCase):
    def test_formula_shape(self):
        self.assertEqual(shape("100-20"),shape("80-10"))
        self.assertNotEqual(shape("100-20"),shape("100+20"))

    def test_same_arithmetic_does_not_delete_distinct_context(self):
        a={"id":"a","case_id":"A","evidence":[{"id":"A","text":"Revenue 20, cash 12"}],
           "checks":[["20-12",8]],"oracle":{"kind":"numeric","unit":"million_usd","value":8}}
        b={**a,"id":"b","case_id":"B","evidence":[{"id":"A","text":"Rebate 20, settled 12"}]}
        rows,summary=screen_pairs([a,b],[{"id1":"a","id2":"b","jaccard":.9}])
        self.assertEqual(rows[0]["priority"],"cross_case_formula_collision")
        self.assertEqual(rows[0]["disposition"],"retain_pending_semantic_review")
        self.assertEqual(summary["rows_deleted"],0)
