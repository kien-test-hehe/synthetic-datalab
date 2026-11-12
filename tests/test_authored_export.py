import tempfile
import unittest
from pathlib import Path
from src.authored_export import build,read_jsonl,materialize_batch

class AuthoredOnlyTests(unittest.TestCase):
    def test_batch_005(self):
        rows,report=materialize_batch("sft/authored/batch_005")
        self.assertEqual(report["cases"],48)
        self.assertEqual(report["rows"],100)
        self.assertEqual(report["arithmetic_checks"],83)
        self.assertEqual(report["oracle_kinds"],{"numeric":76,"qualitative":12,"insufficient":12})
        self.assertEqual(sorted(report["language_pairs"].values()),[25]*4)

    def test_batch_006(self):
        rows,report=materialize_batch("sft/authored/batch_006")
        self.assertEqual(report["cases"],40)
        self.assertEqual(report["rows"],80)
        self.assertEqual(report["arithmetic_checks"],41)
        self.assertEqual(report["oracle_kinds"],{"numeric":38,"qualitative":25,"insufficient":17})
        self.assertEqual(sorted(report["language_pairs"].values()),[20]*4)

    def test_combined_authored_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            report=build(out=tmp)
            self.assertEqual(report["total_rows"],320)
            self.assertEqual(report["total_cases"],148)
            self.assertEqual(report["new_rows"],180)
            self.assertEqual(report["new_arithmetic_checks"],124)
            self.assertEqual({s:v["rows"] for s,v in report["splits"].items()},{"train":292,"dev":14,"test":14})
            self.assertEqual(report["remaining_training_rows"],9708)
            self.assertEqual(report["new_lexical_review_flags"],[])
            allrows=[x for s in ("train","dev","test") for x in read_jsonl(Path(tmp)/f"{s}.jsonl")]
            self.assertTrue(all(r["source"]=="original_fictional_hand_authored" for r in allrows))
            self.assertFalse(any("original_task_id" in r for r in allrows))

if __name__=="__main__":unittest.main()
