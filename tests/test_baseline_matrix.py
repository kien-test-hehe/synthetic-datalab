import json
import hashlib
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from src.eval.baseline_matrix import matrix
from src.eval.independent import SOURCE

class MatrixTests(unittest.TestCase):
    def test_local_matched_baseline_and_test_lock(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            row={"id":"IE-fixture-a","case_id":"IE-fixture","split":"dev","source":SOURCE,
                 "source_type":"fully_synthetic_only","messages":[{"role":"system","content":"Answer"},{"role":"user","content":"Cash 4?"},{"role":"assistant","content":"4"}],
                 "answer":"4","oracle":{"kind":"numeric","value":4,"unit":"million_usd"},"evidence_ids":["A"],"evidence":[{"id":"A","text":"Cash 4"}]}
            d=root/"dev.jsonl";d.write_text(json.dumps(row)+"\n")
            (root/"manifest.json").write_text(json.dumps({"source":SOURCE,"splits":{"dev":{"rows":1,"sha256":hashlib.sha256(d.read_bytes()).hexdigest()}}}))
            reg=root/"models.json";reg.write_text(json.dumps({"models":[{"id":"small","name":"qwen-local","digest":"abc","untouched_attestation":"test fixture"}]}))
            a=SimpleNamespace(dataset_root=root,models=reg,output=root/"run",endpoint="http://127.0.0.1:11434",split="dev",unlock_test=False,limit=0,timeout=5,num_ctx=8192,max_tokens=1024,max_context_chars=14000)
            discover=lambda _:{"qwen-local":{"digest":"abc"}}
            def fake(messages,*args):
                self.assertEqual(len(messages),2)
                return json.dumps({"status":"answerable","answer":"4 million USD","value":4,"unit":"million_usd","citations":["A"]}),{"done_reason":"stop"}
            self.assertEqual(matrix(a,discover,fake)["small"]["summary"]["auto_pass_end_to_end"],1)
            with self.assertRaises(FileExistsError):matrix(a,discover,fake)
            a.split="test"
            with self.assertRaisesRegex(ValueError,"Test locked"):matrix(a,discover,fake)
            a.split="dev";a.output=root/"run2"
            with self.assertRaisesRegex(ValueError,"digest mismatch"):matrix(a,lambda _: {},fake)
