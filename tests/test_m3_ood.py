import tempfile
import unittest
from pathlib import Path

from src.m3.augment import build
from src.m3.ood_split import build_ood,read_rows


class M3OODTests(unittest.TestCase):
    def test_held_out_programs_are_unseen_in_training(self):
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder)/"base"
            target=Path(folder)/"ood"
            build(worlds=200,seed=42,out_dir=str(base))
            r=build_ood(str(base),str(target))
            self.assertEqual(len(r["holdout_task_types"]),8)
            self.assertGreater(r["counts"]["train_seen"],0)
            self.assertGreater(r["counts"]["test_unseen"],0)
            train=read_rows(target/"train_seen.jsonl")
            unseen=read_rows(target/"test_unseen.jsonl")
            self.assertTrue(set(r["holdout_task_types"]).isdisjoint(
                {row["original_task_id"] for row in train}))
            self.assertEqual({row["original_task_id"] for row in unseen},
                             set(r["holdout_task_types"]))
            self.assertTrue({row["world_id"] for row in train}.isdisjoint(
                {row["world_id"] for row in unseen}))


if __name__=="__main__":
    unittest.main()
