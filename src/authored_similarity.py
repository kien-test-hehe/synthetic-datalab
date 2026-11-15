"""Conservative similarity diagnostics. Never delete or rewrite an authored QA.

A repeated skill, formula shape, or lexical score is not semantic duplication.
The queue exposes context, reasoning and gold collisions separately.
"""
from __future__ import annotations

import ast
import hashlib
import json
from collections import Counter

def digest(x):
    return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True).encode()).hexdigest()

def shape(expr):
    try:
        tree=ast.parse(expr,mode="eval")
    except (TypeError,SyntaxError):
        return None
    for node in ast.walk(tree):
        if isinstance(node,ast.Constant) and type(node.value) in (int,float):
            node.value=0
    return ast.dump(tree,include_attributes=False)

def reasoning(row):
    checks=row.get("checks") or []
    return tuple(shape(c[0]) for c in checks if isinstance(c,(list,tuple)) and c)

def screen_pairs(rows,pairs):
    by_id={r["id"]:r for r in rows}
    contexts={r["id"]:digest([r.get("accounting_assumptions"),r.get("evidence")]) for r in rows}
    shapes={r["id"]:reasoning(r) for r in rows}
    records=[]
    for p in pairs:
        a,b=(by_id[p[k]] for k in ("id1","id2"))
        ai,bi=a["id"],b["id"]
        same_case=a["case_id"]==b["case_id"]
        same_context=contexts[ai]==contexts[bi]
        same_formula=bool(a.get("checks")) and a.get("checks")==b.get("checks")
        same_shape=bool(shapes[ai]) and shapes[ai]==shapes[bi]
        oa,ob=a.get("oracle") or {},b.get("oracle") or {}
        same_gold=oa.get("kind")=="numeric" and ob.get("kind")=="numeric" and oa.get("value")==ob.get("value") and oa.get("unit")==ob.get("unit")
        if not same_case and same_context:
            priority="cross_case_context_collision"
        elif not same_case and same_formula:
            priority="cross_case_formula_collision"
        elif same_case and same_formula and same_gold:
            priority="same_case_same_formula_gold"
        elif p["jaccard"]>=.8:
            priority="high_lexical_review"
        else:
            priority="ordinary_lexical_overlap"
        records.append({**p,"same_case":same_case,"same_context":same_context,
                        "same_formula":same_formula,"same_reasoning_shape":same_shape,
                        "same_numeric_gold_and_unit":same_gold,"priority":priority,
                        "disposition":"retain_pending_semantic_review"})
    report={"pairs":len(records),"same_case_pairs":sum(x["same_case"] for x in records),
            "cross_case_pairs":sum(not x["same_case"] for x in records),
            "high_lexical_pairs":sum(x["jaccard"]>=.8 for x in records),
            "priorities":dict(Counter(x["priority"] for x in records)),
            "rows_deleted":0,"note":"Screening only; same skill across separate evidence can be intentional."}
    return records,report
