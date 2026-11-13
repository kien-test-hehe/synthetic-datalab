"""Validate a model's calculation plan against the evidence IDs, then execute.

Numeric operand extraction remains a model responsibility; execution does NOT
prove the operands are supported by the cited text.
"""
from src.v2.calculator import calculate

def run_plan(plan,allowed_citations):
    if not isinstance(plan,dict) or set(plan)!={"status","operands","expression","unit","citations"} or plan["status"]!="answerable":
        raise ValueError("Invalid calculator plan")
    cites=plan["citations"]
    if not isinstance(cites,list) or not cites or not all(isinstance(c,str) for c in cites) or len(set(cites))!=len(cites) or not set(cites)<=set(allowed_citations):
        raise ValueError("Invalid citation IDs")
    unit=plan["unit"]
    if not isinstance(unit,str) or not unit.strip() or len(unit)>80:
        raise ValueError("Invalid unit")
    return {"value":calculate(plan["expression"],plan["operands"]),"unit":unit}
