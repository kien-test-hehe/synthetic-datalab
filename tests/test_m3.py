import json
import tempfile
import unittest
from pathlib import Path

from src.m3.augment import build
from src.m3.validate import validate


class M3RobustnessTests(unittest.TestCase):
    def test_complete_200_worlds(self):
        with tempfile.TemporaryDirectory() as folder:
            summary=build(200,42,folder)
            self.assertEqual(summary["total_rows"],3600)
            report=validate(folder,200)
            self.assertEqual(report["rows"],3600)
            self.assertEqual(report["splits"],{"train":2880,"dev":360,"test":360})
            self.assertEqual(report["variants"],{
                "m2_gold_context":1600,
                "cross_company_distractors":1600,
                "missing_target_evidence":400
            })
            self.assertEqual(report["missing_target_checked"],400)
            self.assertEqual(report["cross_company_checked"],1600)
            self.assertEqual(report["split_leakage"],0)

    def test_reproducibility(self):
        with tempfile.TemporaryDirectory() as a,tempfile.TemporaryDirectory() as b:
            build(20,19,a)
            build(20,19,b)
            for filename in ("m3_train.jsonl","m3_dev.jsonl","m3_test.jsonl","manifest.json"):
                self.assertEqual(
                    (Path(a)/filename).read_bytes(),
                    (Path(b)/filename).read_bytes()
                )

if __name__ == "__main__":
    unittest.main()
