import unittest
from src.m1_validate import validate,arithmetic

class HandAuthoredM1Tests(unittest.TestCase):
    def test_dataset_invariants(self):
        report=validate()
        self.assertEqual(report["qa_count"],100)
        self.assertEqual(report["case_count"],40)
        self.assertEqual(report["splits"],{"train":80,"dev":10,"test":10})
        self.assertEqual(sum(report["language_pairs"].values()),100)
        self.assertGreaterEqual(report["arithmetic_checks_passed"],110)
    def test_arithmetic_whitelist(self):
        self.assertAlmostEqual(arithmetic("(900-760)/760*100"),18.42105263158)
        self.assertEqual(arithmetic("100+40-70-30+20"),60)
        for bad in ["__import__('os').system('echo bad')","2**100","a+1","1//2"]:
            with self.assertRaises((ValueError,SyntaxError)):
                arithmetic(bad)

if __name__=="__main__":
    unittest.main()
