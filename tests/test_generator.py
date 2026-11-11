import json
import tempfile
import unittest
from pathlib import Path
from src.generate_sft import generate, split_for, steps_result, validate_record, world, samples

class GeneratorTests(unittest.TestCase):
    def test_formula(self):
        self.assertEqual(str(steps_result({"a":120,"b":150},[
            {"id":"delta","op":"sub","args":["b","a"]},
            {"id":"ratio","op":"div","args":["delta","a"]},
            {"id":"result","op":"mul","args":["ratio",100]}])), "25.00")

    def test_worlds(self):
        for i in range(200):
            w = world(42,i)
            for sample in samples(w): validate_record(sample)
            self.assertEqual(w["cfo"],w["ni"]+w["depreciation"]-
                (w["ar1"]-w["ar0"])-(w["inv1"]-w["inv0"])+(w["ap1"]-w["ap0"]))

    def test_splits(self):
        with tempfile.TemporaryDirectory() as tmp:
            stats=generate(40,5,tmp)
            self.assertEqual(sum(stats.values()),200)
            seen={}
            for split in ("train","dev","test"):
                for line in (Path(tmp)/f"synthetic_{split}.jsonl").read_text().splitlines():
                    row=json.loads(line)
                    self.assertEqual(split,split_for(row["world_id"]))
                    self.assertEqual(seen.setdefault(row["world_id"],split),split)

if __name__=="__main__": unittest.main()
