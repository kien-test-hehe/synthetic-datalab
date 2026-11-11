"""Milestone 2: 1600 controlled-instantiation SFT QA (no API, no real documents).

32 individually authored reasoning task programs + 200 independently simulated fictional
company worlds. ALL instantiated rows are tagged controlled_programmatic_instantiation.
Original manually authored 100 M1 rows remain separate at sft/m1/.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from src.m2.financial_world import SECTORS, audit_world, create_world, flat
from src.m2.documents import build_documents
from src.m2.task_bank import TASKS, Task

GROUPS=('earnings','cashflow','working_capital','liquidity',
        'temporal','segments','version_scope','robustness')
LANGS=('vi-vi','en-en','vi-en','en-vi')


def eval_expr(expression: str, variables: dict) -> float:
    """Safe expression evaluator: only numeric constants, known variable names and +,-,*,/."""
    def calc(node):
        if isinstance(node,ast.Expression):return calc(node.body)
        if isinstance(node,ast.Name):
            if node.id not in variables:raise KeyError(f'Unknown financial variable: {node.id}')
            v=variables[node.id]
            if type(v) not in (float,int):raise TypeError(f'Not numerical: {node.id}')
            return float(v)
        if isinstance(node,ast.Constant) and type(node.value) in (int,float):return float(node.value)
        if isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.UAdd,ast.USub)):
            v=calc(node.operand)
            return v if isinstance(node.op,ast.UAdd) else -v
        if isinstance(node,ast.BinOp) and isinstance(node.op,(ast.Add,ast.Sub,ast.Mult,ast.Div)):
            a,b=calc(node.left),calc(node.right)
            if isinstance(node.op,ast.Add):return a+b
            if isinstance(node.op,ast.Sub):return a-b
            if isinstance(node.op,ast.Mult):return a*b
            return a/b
        raise ValueError(f'Unsupported mathematical syntax: {expression!r}')
    result=calc(ast.parse(expression,mode='eval'))
    if not math.isfinite(result):raise ValueError(f'Nonfinite financial result: {expression}')
    return result


def expr_vars(expr: str) -> set[str]:
    return {n.id for n in ast.walk(ast.parse(expr,mode='eval')) if isinstance(n,ast.Name)}


def numeric_expression(expr: str, values: dict) -> str:
    """Replace variable symbols by observed source values, for a reproducible worked step."""
    import re
    return re.sub(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b',
                  lambda m: str(values[m.group(0)]) if m.group(0) in values else m.group(0),expr)


def build_example(w:dict,t:Task,index:int,position:int,group_i:int,seed:int,langpair:str) -> dict:
    evidence_lang,answer_lang=langpair.split('-')
    style=(index+group_i+seed)%3
    alldocs=build_documents(w,evidence_lang,style)
    rng=random.Random(f'docs.{seed}.{index}.{t.id}')
    picked=[dict(alldocs[x]) for x in t.documents]
    # In the reconciliation exercise, withhold the reported CFO output line to
    # prevent simple direct answer copying. The raw input components remain.
    if t.id == 'C1':
        target=next((d for d in picked if d['id']=='CF25'),None)
        if target:
            target['text']='\n'.join(line for line in target['text'].split('\n')
                if not line.strip().startswith(('CFO:', '• CFO', '| CFO |',
                    'Operating cash flow:', '• Operating cash flow', '| Operating cash flow |')))
    rng.shuffle(picked)
    assert all(e in t.documents for e in t.gold_evidence_ids)
    assert len(set(t.gold_evidence_ids))==len(t.gold_evidence_ids)
    facts=flat(w)
    no_answer=t.expr is None
    result=None if no_answer else eval_expr(t.expr,facts)
    if result is not None:
        assert math.isfinite(result)
        rendered=f'{result:,.2f}' if answer_lang=='en' else f'{result:,.2f}'.replace(',','_').replace('.',',').replace('_','.')
    else:rendered=None
    question_opts=t.question_vi if answer_lang=='vi' else t.question_en
    question=question_opts[(position//4 + seed + group_i)%2]
    if answer_lang=='vi':
        question=f'{w["name"]} (tài liệu hoàn toàn giả lập). {question}'
        rationale=t.principle_vi
        if t.id=='L2' and result is not None and result < 0:
            rationale+=' Dấu âm biểu thị tiền lớn hơn tổng nợ vay theo định nghĩa nợ ròng, không phải hệ số nợ dương.'
        cite='; '.join(f'[{s}]' for s in t.gold_evidence_ids)
        if no_answer:
            answer=f'Không đủ bằng chứng để kết luận theo câu hỏi. {rationale} Nguồn được kiểm tra: {cite}.'
        else:
            ansunit={'percent':'%','pp':'điểm phần trăm','days':'ngày','times':'lần','money':'triệu USD'}[t.unit]
            expression=numeric_expression(t.expr,facts)
            answer=f'{rationale} Kết quả: {rendered} {ansunit}. Phép tính kiểm chứng: {expression} = {rendered}. Bằng chứng: {cite}.'
        sys=('Bạn là trợ lý phân tích báo cáo tài chính. Chỉ sử dụng các bằng chứng được cung cấp. '
             'Phải chọn đúng phạm vi, năm tài chính và phiên bản; nêu phép tính có thể kiểm chứng và citation ID. '
             'Nếu thiếu cơ sở kết luận, hãy nói rõ.')
        head=('Các tài liệu dưới đây hoàn toàn hư cấu, nhằm học suy luận tài chính. '
              'Đơn vị trình bày là triệu USD; các doanh nghiệp tuân theo mô hình kế toán dồn tích giản lược. '
              'CFO bao gồm thuế/lãi đã trả, khấu hao không là chi tiền; không có biến động phi tiền mặt ngoài những gì nêu.')
    else:
        question=f'{w["name"]} (entirely fictional case). {question}'
        rationale=t.principle_en
        if t.id=='L2' and result is not None and result < 0:
            rationale+=' A negative net leverage ratio indicates cash exceeds financial debt under this definition.'
        cite='; '.join(f'[{s}]' for s in t.gold_evidence_ids)
        if no_answer:
            answer=f'Insufficient evidence to determine the requested conclusion. {rationale} Evidence checked: {cite}.'
        else:
            ansunit={'percent':'%','pp':'percentage points','days':'days','times':'times','money':'USD million'}[t.unit]
            expression=numeric_expression(t.expr,facts)
            answer=f'{rationale} Verified result: {rendered} {ansunit}. Checkable calculation: {expression} = {rendered}. Evidence: {cite}.'
        sys=('You analyze financial documents only from supplied evidence. Select matching report period, scope and version, '
             'show verifiable arithmetic, cite evidence IDs, and abstain if information is missing.')
        head=('All documents below are entirely fictional educational examples. Figures are USD million. '
              'A simplified accrual ledger is used; CFO includes cash interest and taxes, depreciation is noncash, '
              'and there are no unlisted noncash working-capital reclassifications.')
    source='\n\n'.join(f'[{d["id"]}] {d["title"]} | scope={d["statement_scope"]} | fiscal_year={d["fiscal_year"]}\n{d["text"]}' for d in picked)
    user=head+'\n\n'+source+'\n\n'+('Câu hỏi: ' if answer_lang=='vi' else 'Question: ')+question
    result_obj=None if no_answer else dict(expression=t.expr,
                 operands={k:facts[k] for k in sorted(expr_vars(t.expr))},
                 result=round(result,6),output_rounded=round(result,2),unit=t.unit)
    out=dict(
        id=f'{w["id"]}-{t.id}',world_id=w['id'],source='controlled_programmatic_instantiation',
        authoring='original_handwritten_task_program_plus_deterministic_financial_world',
        original_task_id=t.id,category=t.group,difficulty=t.difficulty,sector=w['sector'],
        split=None,language_pair=langpair,doc_layout=style,
        accounting_standard=w['standard'],source_type='fully_synthetic_only',
        question=question,answer=answer,answerability='insufficient' if no_answer else 'answerable',
        evidence=picked,evidence_ids=list(t.gold_evidence_ids),program=result_obj,
        messages=[{'role':'system','content':sys},{'role':'user','content':user},
                  {'role':'assistant','content':answer}],
        requirements={'same_world_only':True,'ignore_unofficial_revenue_versions': t.group in ('version_scope',)},
    )
    return out


def generate(worlds=200,seed=42,out_dir='sft/m2/outputs'):
    if worlds%20:raise ValueError('worlds must be a multiple of 20, for reproducible 80/10/10 world splits')
    out_dir=Path(out_dir);out_dir.mkdir(parents=True,exist_ok=True)
    schedule=['train']*(worlds*8//10)+['dev']*(worlds//10)+['test']*(worlds//10)
    rng=random.Random(seed)
    indices=list(range(worlds));rng.shuffle(indices)
    world_split={index:schedule[j] for j,index in enumerate(indices)}
    bysplit={k:[] for k in ('train','dev','test')}
    world_manifest=[]
    for split in ('train','dev','test'):
        split_ids=sorted(i for i in range(worlds) if world_split[i]==split)
        for pos,i in enumerate(split_ids):
            sector=SECTORS[(pos+pos//16)%4]
            language=LANGS[pos%4]
            w=create_world(seed,i,sector)
            audit_world(w)
            world_manifest.append(dict(id=w['id'],split=split,sector=sector,language_pair=language))
            for gi,g in enumerate(GROUPS):
                options=[x for x in TASKS if x.group==g]
                assert len(options)==4
                # Every group appears once in each world; task index rotates across worlds.
                t=options[(pos+pos//4+gi)%4]
                row=build_example(w,t,i,pos,gi,seed,language)
                row['split']=split
                bysplit[split].append(row)
    for split,rows in bysplit.items():
        with (out_dir/f'm2_{split}.jsonl').open('w',encoding='utf-8') as f:
            for r in rows:f.write(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n')
    report={
      'dataset':'FinancialDocLab M2 controlled programmatic curriculum',
      'source_policy':'fully fictional worlds and authored blueprints; no actual financial filings or benchmark QA',
      'total_rows':sum(map(len,bysplit.values())),'world_count':worlds,
      'world_splits':dict(Counter(x['split'] for x in world_manifest)),
      'splits':{k:len(v) for k,v in bysplit.items()},
      'type_count':len(TASKS),'category_distribution':dict(Counter(r['category'] for v in bysplit.values() for r in v)),
      'task_distribution':dict(Counter(r['original_task_id'] for v in bysplit.values() for r in v)),
      'language_distribution':dict(Counter(r['language_pair'] for v in bysplit.values() for r in v)),
      'sector_distribution':dict(Counter(r['sector'] for v in bysplit.values() for r in v)),
      'answerability':dict(Counter(r['answerability'] for v in bysplit.values() for r in v)),
      'difficulty_distribution':dict(Counter(r['difficulty'] for v in bysplit.values() for r in v)),
      'authors_note':('The 32 task definitions and narrative principles were written individually; '
        'the 1600 records are controlled, verified numerical and documentary instantiations, NOT 1600 hand-written QAs.'),
      'limitations':('Simplified US-dollar accrual worlds, 32 program families, short textual financial excerpts, '
        'no scanned documents or accounting professional certification. Evaluate real-domain transfer before SFT deployment.'),
      'seed':seed
    }
    (out_dir/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--worlds',type=int,default=200)
    p.add_argument('--seed',type=int,default=42)
    p.add_argument('--out',default='sft/m2/outputs')
    args=p.parse_args()
    print(json.dumps(generate(args.worlds,args.seed,args.out),ensure_ascii=False,indent=2))
