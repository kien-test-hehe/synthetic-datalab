import argparse
import json
import tempfile
import unittest
from pathlib import Path

from src.m4.authored import materialize,build
from src.m4.experiments import prepare,read_rows,world
from src.authored_export import build as build_authored
from src.m3.augment import build as build_m3
from src.eval.model_eval import (parse_response,grade,synthetic_example,
                                 financebench_examples,run,validate_endpoint)
from src.eval.compare import compare


class M4AuthorshipTests(unittest.TestCase):
    def test_all_original_cases_and_oracles(self):
        rows,report=materialize()
        self.assertEqual(report["rows"],40)
        self.assertEqual(report["cases"],20)
        self.assertEqual(report["scenario_families"],20)
        self.assertEqual(report["splits"],{"train":32,"dev":4,"test":4})
        for row in rows:
            self.assertEqual(row["source"],"original_fictional_hand_authored")
            self.assertEqual(row["source_type"],"fully_synthetic_only")
            self.assertEqual(row["messages"][-1]["content"],row["answer"])
            for cite in row["evidence_ids"]:
                self.assertIn("["+cite+"]",row["answer"])
                self.assertIn("["+cite+"]",row["messages"][1]["content"])

    def test_export_and_common_world_comparison(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            build(out=root/"authored")
            self.assertEqual(len(read_rows(root/"authored"/"train.jsonl")),32)
            build_m3(worlds=20,seed=42,out_dir=str(root/"m3"))
            build_authored(out=root/"full")
            r=prepare(str(root/"m3"),str(root/"exp"),authored_root=root/"full")
            self.assertEqual(r["files"]["authored_only"]["rows"],10000)
            self.assertEqual(r["files"]["authored_plus_gold"]["rows"],10128)
            self.assertEqual(r["files"]["authored_plus_robust"]["rows"],10288)
            sample=read_rows(root/"exp"/"authored_only.jsonl")[-1]
            self.assertIsNotNone(parse_response(sample["messages"][-1]["content"]))
            self.assertEqual(r["files"]["gold_only"]["rows"],128)
            self.assertEqual(r["files"]["robust_all"]["rows"],288)
            self.assertEqual(r["files"]["robust_size_matched"]["rows"],128)
            test=read_rows(root/"exp"/"common_test.jsonl")
            train=read_rows(root/"exp"/"authored_plus_robust.jsonl")
            self.assertTrue({world(x) for x in test}.isdisjoint({world(x) for x in train}))

    def test_program_ood_uses_no_authored_cases(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            build_m3(worlds=200,seed=42,out_dir=str(root/"m3"))
            r=prepare(str(root/"m3"),str(root/"ood"),ood=True)
            self.assertNotIn("authored_only",r["files"])
            seen=read_rows(root/"ood"/"robust_all.jsonl")
            unseen=read_rows(root/"ood"/"common_test.jsonl")
            self.assertTrue({x["original_task_id"] for x in seen}.isdisjoint(
                {x["original_task_id"] for x in unseen}))


class M4ModelEvalTests(unittest.TestCase):
    def test_strict_units_citations_and_parse(self):
        rows,_=materialize()
        row=next(r for r in rows if r["split"]=="test" and r["oracle"]["kind"]=="numeric")
        ex=synthetic_example(row)
        oracle=row["oracle"]
        good={"status":"answerable","answer":"Worked answer",
              "value":oracle["value"],"unit":oracle["unit"],"citations":row["evidence_ids"]}
        self.assertTrue(grade(ex,parse_response(json.dumps(good)))["auto_pass"])
        wrong_unit=dict(good,unit="wrong")
        self.assertFalse(grade(ex,parse_response(json.dumps(wrong_unit)))["auto_pass"])
        invented=dict(good,citations=row["evidence_ids"]+["MADE_UP"])
        self.assertFalse(grade(ex,parse_response(json.dumps(invented)))["auto_pass"])
        self.assertFalse(grade(ex,None)["auto_pass"])
        self.assertIsNone(parse_response('{"status":"answerable","answer":"x","value":true,"unit":"percent","citations":[]}'))

    def test_local_only_and_no_gold_answer_leakage(self):
        for bad in ("https://api.openai.com","http://localhost.attacker.example","http://127.0.0.1:11434/?x=y"):
            with self.assertRaises(ValueError):validate_endpoint(bad)
        self.assertEqual(validate_endpoint("http://127.0.0.1:11434"),"http://127.0.0.1:11434")
        row={"financebench_id":"test","doc_name":"FICTIONAL",
             "question":"What is revenue?","answer":"NEVER_PUT_GOLD_IN_PROMPT",
             "evidence":[{"evidence_text":"Revenue was 80 million."}]}
        ex=next(financebench_examples([row]))
        self.assertIn("Revenue was 80 million.",ex["messages"][1]["content"])
        self.assertNotIn(row["answer"],json.dumps(ex["messages"]))
        self.assertIsNone(ex["gold_citations"])

    def test_full_mock_local_run_and_paired_comparison(self):
        rows,_=materialize()
        selected=[r for r in rows if r["split"]=="test" and r["oracle"]["kind"]=="numeric"][:1]
        self.assertTrue(selected)
        row=selected[0]
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);data=root/"test.jsonl"
            data.write_text("".join(json.dumps(r)+"\n" for r in selected))
            def call_good(messages,*args):
                self.assertEqual(len(messages),2)
                self.assertNotIn(row["answer"],json.dumps(messages))
                return json.dumps({"status":"answerable","answer":"Worked answer",
                    "value":row["oracle"]["value"],"unit":row["oracle"]["unit"],
                    "citations":row["evidence_ids"]}),{"done_reason":"stop"}
            def call_bad(messages,*args):
                return json.dumps({"status":"answerable","answer":"Wrong answer",
                    "value":999999,"unit":row["oracle"]["unit"],"citations":[]}),{"done_reason":"stop"}
            common=dict(kind="synthetic",dataset=str(data),endpoint="http://127.0.0.1:11434",
                        context="gold",chunks=None,db=None,k=10,limit=0,timeout=30,
                        temperature=0,num_ctx=8192,max_tokens=1024,max_context_chars=14000)
            b=root/"base.jsonl";a=root/"adapter.jsonl"
            rb=run(argparse.Namespace(**common,model="base",output=str(b)),call=call_bad)
            ra=run(argparse.Namespace(**common,model="adapter",output=str(a)),call=call_good)
            self.assertEqual(rb["summary"]["auto_pass"]["mean"],0)
            self.assertEqual(ra["summary"]["auto_pass"]["mean"],1)
            result=compare(b,a)
            self.assertEqual(result["metrics"]["auto_pass"]["delta"],1)
            self.assertEqual(result["matched_examples"],1)


if __name__=="__main__":unittest.main()
