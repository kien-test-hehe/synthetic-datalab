import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
from src.v2.evaluate import verify_eval
class TestProtocol(unittest.TestCase):
    def test_lock(self):
        args=SimpleNamespace(benchmark_root="unused",split="test",unlock_test=False,protocol=None,limit=0)
        with patch("src.v2.evaluate.digest",return_value="40ce1a95a9505c07276a41e21ba5baf1f7fa29db85ec584659551cef60c34de3"):
            with self.assertRaises(ValueError):verify_eval(args,{})
            with TemporaryDirectory() as td:
                args.unlock_test=True;args.protocol=str(Path(td)/"p.json")
                Path(args.protocol).write_text('{"a":1}')
                with self.assertRaises(ValueError):verify_eval(args,{"a":2})
                self.assertEqual(verify_eval(args,{"a":1}),Path("unused/test.jsonl"))
