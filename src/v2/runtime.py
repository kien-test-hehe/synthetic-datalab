"""Validate and execute only supported calculator plans; never run arbitrary code."""
from src.v2.calculator import calculate

def run_plan(plan,allowed_citations):
    if not isinstance(plan,dict) or set(plan)!={"status","operands","expression","unit","citations"} or plan["status"] not in ("answerable","direct","insufficient"):
        raise ValueError("Invalid calculator plan")
    cites=plan["citations"]
    if not isinstance(cites,list) or not cites or not all(isinstance(c,str) for c in cites) or len(set(cites))!=len(cites) or not set(cites)<=set(allowed_citations):
        raise ValueError("Invalid citation IDs")
    if plan["status"]!="answerable":
        if plan["operands"]!={} or plan["expression"] is not None or plan["unit"] is not None:
            raise ValueError("Non-calculation routes must not supply operands")
        return None
    unit=plan["unit"]
    if not isinstance(unit,str) or not unit.strip() or len(unit)>80:
        raise ValueError("Invalid unit")
    ops=plan["operands"]
    if not isinstance(ops,dict):raise ValueError("Invalid operands")
    values={}
    for k,v in ops.items():
        if not isinstance(v,dict) or set(v)!={"value","evidence_id","label"} or not isinstance(v["label"],str) or not v["label"].strip() or v["evidence_id"] not in cites:
            raise ValueError("Invalid operand source reference")
        values[k]=v["value"]
    return {"value":calculate(plan["expression"],values),"unit":unit}
