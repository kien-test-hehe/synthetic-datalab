"""Strict quality checks on 1,600 teacherless financial QA examples."""
from __future__ import annotations
import argparse
import json
import hashlib
import math
from collections import Counter, defaultdict
from pathlib import Path
from src.m2.build_m2 import eval_expr, expr_vars, generate, GROUPS, LANGS
from src.m2.financial_world import SECTORS, create_world, audit_world
from src.m2.task_bank import TASKS


def check_dataset(directory='sft/m2/outputs', expected_worlds=200):
    root=Path(directory)
    bysplit={split:[json.loads(x) for x in (root/f'm2_{split}.jsonl').read_text(encoding='utf8').splitlines() if x.strip()]
             for split in ('train','dev','test')}
    allrows=[r for rows in bysplit.values() for r in rows]
    expected_rows=8*expected_worlds
    assert len(allrows)==expected_rows
    assert len({r['id'] for r in allrows})==expected_rows
    assert {r['source_type'] for r in allrows}=={'fully_synthetic_only'}
    assert {r['authoring'] for r in allrows}=={'original_handwritten_task_program_plus_deterministic_financial_world'}
    assert {r['source'] for r in allrows}=={'controlled_programmatic_instantiation'}
    case_splits={}
    numeric_count=0
    for split,rows in bysplit.items():
        assert len(rows)==expected_worlds * 8 * (8 if split=='train' else 1)//10
        assert len({r['world_id'] for r in rows})==expected_worlds * (.8 if split=='train' else .1)
        cats=Counter(r['category'] for r in rows)
        assert set(cats)==set(GROUPS)
        assert len(set(cats.values()))==1
        languages=Counter(r['language_pair'] for r in rows)
        assert set(languages)==set(LANGS) and len(set(languages.values()))==1
        sectors=Counter(r['sector'] for r in rows)
        assert set(sectors)==set(SECTORS) and len(set(sectors.values()))==1
        task_counts=Counter(r['original_task_id'] for r in rows)
        assert set(task_counts)=={x.id for x in TASKS}
        assert len(set(task_counts.values()))==1
        for r in rows:
            if r['world_id'] in case_splits:assert case_splits[r['world_id']]==split
            else:case_splits[r['world_id']]=split
            assert len(r['messages'])==3
            assert [x['role'] for x in r['messages']]==['system','user','assistant']
            assert r['messages'][2]['content']==r['answer']
            assert r['question'] in r['messages'][1]['content']
            assert 2<=len(r['evidence'])<=5
            ev={x['id'] for x in r['evidence']}
            assert len(ev)==len(r['evidence'])
            assert set(r['evidence_ids'])<=ev
            assert all(f'[{eid}]' in r['messages'][1]['content'] for eid in r['evidence_ids'])
            assert all(f'[{eid}]' in r['messages'][2]['content'] for eid in r['evidence_ids'])
            assert r['answerability'] in ('answerable','insufficient')
            assert r['source_type']=='fully_synthetic_only'
            if r['answerability']=='insufficient':
                assert r['program'] is None
                assert r['original_task_id'] in ('U1','U2','U3')
            else:
                p=r['program']
                assert p and math.isfinite(p['result'])
                expected=eval_expr(p['expression'],p['operands'])
                assert abs(expected-p['result'])<0.0000011,(r['id'],expected,p)
                assert round(expected,2)==p['output_rounded']
                assert expr_vars(p['expression'])==set(p['operands'])
                assert p['unit'] in ('percent','pp','days','times','money')
                numeric_count+=1
    assert len(case_splits)==expected_worlds
    # Verify all underlying accounting worlds independently of the samples.
    for split,rows in bysplit.items():
        for r in rows[::8]:
            idx=int(r['world_id'].rsplit('-',1)[1])
            w=create_world(42,idx,r['sector'])
            assert audit_world(w)
    out={
       'total_rows':len(allrows),
       'splits':{k:len(v) for k,v in bysplit.items()},
       'worlds':len(case_splits),
       'task_types':len(TASKS),
       'per_task_count':len(allrows)//len(TASKS),
       'category_counts':dict(Counter(r['category'] for r in allrows)),
       'language_counts':dict(Counter(r['language_pair'] for r in allrows)),
       'sector_counts':dict(Counter(r['sector'] for r in allrows)),
       'answerability_counts':dict(Counter(r['answerability'] for r in allrows)),
       'numeric_expressions_validated':numeric_count,
       'world_accounting_ledger_checks':len(case_splits)*3,
       'missing_citations':0,
       'world_split_leakage':0,
       'professional_financial_review':'not performed',
       'template_generalization':'not established',
    }
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--out',default='sft/m2/outputs')
    a=p.parse_args()
    print(json.dumps(check_dataset(a.out),ensure_ascii=False,indent=2))
