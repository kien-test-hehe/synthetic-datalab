import json
import pathlib
import tempfile
import unittest
from src.m2.build_m2 import generate,eval_expr
from src.m2.financial_world import create_world,audit_world
from src.m2.validate_m2 import check_dataset
from src.m2.task_bank import TASKS

class FinancialDataLabM2Tests(unittest.TestCase):
    def test_ledger_integrity(self):
        for i in range(200):
            world=create_world(42,i,['manufacturing','retail','logistics','software'][i%4])
            self.assertTrue(audit_world(world))
            self.assertEqual(world['source'],'entirely_fictional_event_simulator')

    def test_task_bank(self):
        self.assertEqual(len(TASKS),32)
        self.assertEqual(len(set(x.id for x in TASKS)),32)
        self.assertEqual(len(set(x.group for x in TASKS)),8)
        self.assertEqual(sum(x.expr is None for x in TASKS),3)
        for x in TASKS:
            self.assertTrue(x.gold_evidence_ids)
            self.assertTrue(set(x.gold_evidence_ids)<=set(x.documents))

    def test_whitelisted_arithmetic(self):
        self.assertAlmostEqual(eval_expr('(a-b)/b*100',{'a':125,'b':100}),25)
        for bad in ['__import__("os")','a**2','globals()','a[0]']:
            with self.assertRaises((ValueError,KeyError,TypeError,ZeroDivisionError,SyntaxError)):
                eval_expr(bad,{'a':3})

    def test_full_generation_checks(self):
        with tempfile.TemporaryDirectory() as temp:
            report=generate(200,42,temp)
            self.assertEqual(report['total_rows'],1600)
            qa=check_dataset(temp)
            self.assertEqual(qa['numeric_expressions_validated'],1450)
            self.assertEqual(qa['world_split_leakage'],0)
            self.assertEqual(qa['language_counts'],{'vi-vi':400,'en-en':400,'vi-en':400,'en-vi':400})

    def test_reproducible_outputs(self):
        with tempfile.TemporaryDirectory() as a,tempfile.TemporaryDirectory() as b:
            generate(20,19,a);generate(20,19,b)
            for f in ('m2_train.jsonl','m2_dev.jsonl','m2_test.jsonl','manifest.json'):
                self.assertEqual((pathlib.Path(a)/f).read_bytes(),(pathlib.Path(b)/f).read_bytes())

if __name__=='__main__':unittest.main()
