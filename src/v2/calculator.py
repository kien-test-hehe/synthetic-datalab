"""Bounded arithmetic DSL. No eval/exec, imports, attributes or arbitrary calls."""
from __future__ import annotations
import ast
import math
import operator
import re

OPS={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv}
NAME=re.compile(r"^[a-z][a-z0-9_]{0,31}$")
LIMIT=1e18

def number(v):
    if type(v) not in (int,float):
        raise ValueError("Expected numeric scalar")
    try:
        if not math.isfinite(v) or abs(v)>LIMIT:
            raise ValueError("Non-finite or out-of-range number")
    except OverflowError as exc:
        raise ValueError("Out-of-range number") from exc
    return float(v)

def calculate(expression, operands):
    if not isinstance(expression,str) or not 1<=len(expression)<=400:
        raise ValueError("Invalid expression length")
    if not isinstance(operands,dict) or not 1<=len(operands)<=24:
        raise ValueError("Invalid operand count")
    if any(not isinstance(k,str) or not NAME.fullmatch(k) for k in operands):
        raise ValueError("Invalid operand name")
    values={k:number(v) for k,v in operands.items()}
    try:
        root=ast.parse(expression,mode="eval")
    except (SyntaxError,RecursionError) as exc:
        raise ValueError("Invalid expression") from exc
    if sum(1 for _ in ast.walk(root))>120:
        raise ValueError("Expression too complex")
    used=set()
    def walk(node,depth=0):
        if depth>20:
            raise ValueError("Expression too deep")
        if isinstance(node,ast.Name) and node.id in values:
            used.add(node.id)
            return values[node.id]
        if isinstance(node,ast.Constant):
            # Formula constants, not evidence values. Keep the vocabulary tiny.
            if type(node.value) not in (int,float) or node.value not in (0,1,2,4,12,100,1000,1000000):
                raise ValueError("Use named operands for source numbers")
            return number(node.value)
        if isinstance(node,ast.BinOp) and type(node.op) in OPS:
            try:
                return number(OPS[type(node.op)](walk(node.left,depth+1),walk(node.right,depth+1)))
            except (ZeroDivisionError,OverflowError) as exc:
                raise ValueError("Invalid arithmetic") from exc
        if isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.USub,ast.UAdd)):
            v=walk(node.operand,depth+1)
            return -v if isinstance(node.op,ast.USub) else v
        raise ValueError("Unsupported arithmetic node")
    result=walk(root.body)
    if used!=set(values):
        raise ValueError("Unused operands")
    return result

# A numeric-token check is intentionally narrower than semantic extraction.
ASSUMPTION_REF="@assumptions"
def assumption_has_number(assumptions,value):
    if not isinstance(assumptions,str) or not assumptions.strip():return False
    target=number(value)
    for token in re.findall(r"(?<![0-9.])[+-]?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)(?![0-9.])",assumptions):
        try:
            if math.isclose(float(token),target,rel_tol=1e-12,abs_tol=1e-12):return True
        except (ValueError,OverflowError):continue
    return False
