"""Pilot evidence-linked arithmetic graphs for seven manually reviewed QAs.

Named operands must be anchored to the cited source verbatim. This is an
arithmetic/provenance check, not automated accounting-policy adjudication.
"""
from __future__ import annotations

import ast
import math
from decimal import Decimal

GRAPHS = [
  {
    "id": "A040-01-i",
    "result_unit": "billion_vnd",
    "expression": "receipts-ordinary-warranty-recall+insurance-finance-tax-capex",
    "operands": {
      "receipts": {
        "value": 940,
        "unit": "billion_vnd",
        "evidence_id": "E",
        "quote": "Customer receipts 940",
        "literal": "940",
        "scope": "customer_cash",
        "period": "current_period",
        "format": "decimal"
      },
      "ordinary": {
        "value": 740,
        "unit": "billion_vnd",
        "evidence_id": "E",
        "quote": "ordinary production/selling cash paid 740",
        "literal": "740",
        "scope": "ordinary_cash",
        "period": "current_period",
        "format": "decimal"
      },
      "warranty": {
        "value": 22,
        "unit": "billion_vnd",
        "evidence_id": "B",
        "quote": "settlements 28 gồm 22 cash",
        "literal": "22",
        "scope": "warranty_cash",
        "period": "current_period",
        "format": "decimal"
      },
      "recall": {
        "value": 8,
        "unit": "billion_vnd",
        "evidence_id": "C",
        "quote": "Cash repairs 8 already settled",
        "literal": "8",
        "scope": "recall_cash",
        "period": "current_period",
        "format": "decimal"
      },
      "insurance": {
        "value": 5,
        "unit": "billion_vnd",
        "evidence_id": "D",
        "quote": "cash received 5",
        "literal": "5",
        "scope": "insurance_cash",
        "period": "current_period",
        "format": "decimal"
      },
      "finance": {
        "value": 20,
        "unit": "billion_vnd",
        "evidence_id": "E",
        "quote": "finance cash20",
        "literal": "20",
        "scope": "interest_cash",
        "period": "current_period",
        "format": "decimal"
      },
      "tax": {
        "value": 16,
        "unit": "billion_vnd",
        "evidence_id": "E",
        "quote": "tax cash16",
        "literal": "16",
        "scope": "tax_cash",
        "period": "current_period",
        "format": "decimal"
      },
      "capex": {
        "value": 70,
        "unit": "billion_vnd",
        "evidence_id": "F",
        "quote": "Cash capex 70",
        "literal": "70",
        "scope": "cash_capex",
        "period": "current_period",
        "format": "decimal"
      }
    }
  },
  {
    "id": "A040-01-j",
    "result_unit": "billion_vnd",
    "expression": "opening+receipts-ordinary-warranty-recall+insurance-finance-tax-capex+draw-repay",
    "operands": {
      "receipts": {
        "value": 940,
        "unit": "billion_vnd",
        "evidence_id": "E",
        "quote": "Customer receipts 940",
        "literal": "940",
        "scope": "customer_cash",
        "period": "current_period",
        "format": "decimal"
      },
      "ordinary": {
        "value": 740,
        "unit": "billion_vnd",
        "evidence_id": "E",
        "quote": "ordinary production/selling cash paid 740",
        "literal": "740",
        "scope": "ordinary_cash",
        "period": "current_period",
        "format": "decimal"
      },
      "warranty": {
        "value": 22,
        "unit": "billion_vnd",
        "evidence_id": "B",
        "quote": "settlements 28 gồm 22 cash",
        "literal": "22",
        "scope": "warranty_cash",
        "period": "current_period",
        "format": "decimal"
      },
      "recall": {
        "value": 8,
        "unit": "billion_vnd",
        "evidence_id": "C",
        "quote": "Cash repairs 8 already settled",
        "literal": "8",
        "scope": "recall_cash",
        "period": "current_period",
        "format": "decimal"
      },
      "insurance": {
        "value": 5,
        "unit": "billion_vnd",
        "evidence_id": "D",
        "quote": "cash received 5",
        "literal": "5",
        "scope": "insurance_cash",
        "period": "current_period",
        "format": "decimal"
      },
      "finance": {
        "value": 20,
        "unit": "billion_vnd",
        "evidence_id": "E",
        "quote": "finance cash20",
        "literal": "20",
        "scope": "interest_cash",
        "period": "current_period",
        "format": "decimal"
      },
      "tax": {
        "value": 16,
        "unit": "billion_vnd",
        "evidence_id": "E",
        "quote": "tax cash16",
        "literal": "16",
        "scope": "tax_cash",
        "period": "current_period",
        "format": "decimal"
      },
      "capex": {
        "value": 70,
        "unit": "billion_vnd",
        "evidence_id": "F",
        "quote": "Cash capex 70",
        "literal": "70",
        "scope": "cash_capex",
        "period": "current_period",
        "format": "decimal"
      },
      "opening": {
        "value": 80,
        "unit": "billion_vnd",
        "evidence_id": "F",
        "quote": "Opening cash 80",
        "literal": "80",
        "scope": "cash",
        "period": "opening",
        "format": "decimal"
      },
      "draw": {
        "value": 25,
        "unit": "billion_vnd",
        "evidence_id": "F",
        "quote": "borrowing cash 25",
        "literal": "25",
        "scope": "debt_cash",
        "period": "current_period",
        "format": "decimal"
      },
      "repay": {
        "value": 10,
        "unit": "billion_vnd",
        "evidence_id": "F",
        "quote": "principal repayment10",
        "literal": "10",
        "scope": "debt_cash",
        "period": "current_period",
        "format": "decimal"
      }
    }
  },
  {
    "id": "A046-04-n",
    "result_unit": "times",
    "expression": "(receipts-drop+cert-opex-tax)/(interest+principal)",
    "operands": {
      "receipts": {
        "value": 1050,
        "unit": "billion_vnd",
        "evidence_id": "B",
        "quote": "collections1.050",
        "literal": "1.050",
        "scope": "customer_cash",
        "period": "base_period",
        "format": "thousands_dot"
      },
      "drop": {
        "value": 160,
        "unit": "billion_vnd",
        "evidence_id": "G",
        "quote": "Customer collections drop by160",
        "literal": "160",
        "scope": "customer_cash_stress",
        "period": "stress_period",
        "format": "decimal"
      },
      "cert": {
        "value": 35,
        "unit": "billion_vnd",
        "evidence_id": "B",
        "quote": "Certificate revenue35 cash",
        "literal": "35",
        "scope": "certificate_cash",
        "period": "current_period",
        "format": "decimal"
      },
      "opex": {
        "value": 520,
        "unit": "billion_vnd",
        "evidence_id": "D",
        "quote": "Actual opex520",
        "literal": "520",
        "scope": "operating_cash",
        "period": "current_period",
        "format": "decimal"
      },
      "tax": {
        "value": 45,
        "unit": "billion_vnd",
        "evidence_id": "D",
        "quote": "tax45",
        "literal": "45",
        "scope": "tax_cash",
        "period": "current_period",
        "format": "decimal"
      },
      "interest": {
        "value": 90,
        "unit": "billion_vnd",
        "evidence_id": "D",
        "quote": "interest90",
        "literal": "90",
        "scope": "debt_service",
        "period": "current_period",
        "format": "decimal"
      },
      "principal": {
        "value": 150,
        "unit": "billion_vnd",
        "evidence_id": "D",
        "quote": "Scheduled principal150",
        "literal": "150",
        "scope": "debt_service",
        "period": "current_period",
        "format": "decimal"
      }
    }
  },
  {
    "id": "A046-04-o",
    "result_unit": "billion_vnd",
    "expression": "opening+receipts-drop+cert-opex-tax-interest-principal-maint-dsra-reserve-floor",
    "operands": {
      "receipts": {
        "value": 1050,
        "unit": "billion_vnd",
        "evidence_id": "B",
        "quote": "collections1.050",
        "literal": "1.050",
        "scope": "customer_cash",
        "period": "base_period",
        "format": "thousands_dot"
      },
      "drop": {
        "value": 160,
        "unit": "billion_vnd",
        "evidence_id": "G",
        "quote": "Customer collections drop by160",
        "literal": "160",
        "scope": "customer_cash_stress",
        "period": "stress_period",
        "format": "decimal"
      },
      "cert": {
        "value": 35,
        "unit": "billion_vnd",
        "evidence_id": "B",
        "quote": "Certificate revenue35 cash",
        "literal": "35",
        "scope": "certificate_cash",
        "period": "current_period",
        "format": "decimal"
      },
      "opex": {
        "value": 520,
        "unit": "billion_vnd",
        "evidence_id": "D",
        "quote": "Actual opex520",
        "literal": "520",
        "scope": "operating_cash",
        "period": "current_period",
        "format": "decimal"
      },
      "tax": {
        "value": 45,
        "unit": "billion_vnd",
        "evidence_id": "D",
        "quote": "tax45",
        "literal": "45",
        "scope": "tax_cash",
        "period": "current_period",
        "format": "decimal"
      },
      "interest": {
        "value": 90,
        "unit": "billion_vnd",
        "evidence_id": "D",
        "quote": "interest90",
        "literal": "90",
        "scope": "debt_service",
        "period": "current_period",
        "format": "decimal"
      },
      "principal": {
        "value": 150,
        "unit": "billion_vnd",
        "evidence_id": "D",
        "quote": "Scheduled principal150",
        "literal": "150",
        "scope": "debt_service",
        "period": "current_period",
        "format": "decimal"
      },
      "opening": {
        "value": 100,
        "unit": "billion_vnd",
        "evidence_id": "D",
        "quote": "Opening unrestricted cash100",
        "literal": "100",
        "scope": "unrestricted_cash",
        "period": "opening",
        "format": "decimal"
      },
      "maint": {
        "value": 70,
        "unit": "billion_vnd",
        "evidence_id": "E",
        "quote": "Maintenance capex70",
        "literal": "70",
        "scope": "unrestricted_capex",
        "period": "current_period",
        "format": "decimal"
      },
      "dsra": {
        "value": 20,
        "unit": "billion_vnd",
        "evidence_id": "E",
        "quote": "DSRA top-up20",
        "literal": "20",
        "scope": "reserve_transfer",
        "period": "current_period",
        "format": "decimal"
      },
      "reserve": {
        "value": 15,
        "unit": "billion_vnd",
        "evidence_id": "E",
        "quote": "maintenance reserve top-up15",
        "literal": "15",
        "scope": "reserve_transfer",
        "period": "current_period",
        "format": "decimal"
      },
      "floor": {
        "value": 60,
        "unit": "billion_vnd",
        "evidence_id": "F",
        "quote": "Minimum unrestricted cash60",
        "literal": "60",
        "scope": "covenant_floor",
        "period": "current_period",
        "format": "decimal"
      }
    }
  },
  {
    "id": "A039-06-i",
    "result_unit": "million_usd",
    "expression": "premium-claims-expense-((a_rec-a_coll)*a_rate+(b_rec-b_coll)*b_rate+c_rec*c_rate)+invest-tax",
    "operands": {
      "a_rec": {
        "value": 90,
        "unit": "million_usd",
        "evidence_id": "B",
        "quote": "|A|90|30|20|",
        "literal": "90",
        "scope": "reinsurer_A_recoverable",
        "period": "current_period",
        "format": "decimal"
      },
      "a_coll": {
        "value": 30,
        "unit": "million_usd",
        "evidence_id": "B",
        "quote": "|A|90|30|20|",
        "literal": "30",
        "scope": "reinsurer_A_collateral",
        "period": "current_period",
        "format": "decimal"
      },
      "b_rec": {
        "value": 60,
        "unit": "million_usd",
        "evidence_id": "B",
        "quote": "|B|60|10|0|",
        "literal": "60",
        "scope": "reinsurer_B_recoverable",
        "period": "current_period",
        "format": "decimal"
      },
      "b_coll": {
        "value": 10,
        "unit": "million_usd",
        "evidence_id": "B",
        "quote": "|B|60|10|0|",
        "literal": "10",
        "scope": "reinsurer_B_collateral",
        "period": "current_period",
        "format": "decimal"
      },
      "c_rec": {
        "value": 30,
        "unit": "million_usd",
        "evidence_id": "B",
        "quote": "|C|30|0|15|",
        "literal": "30",
        "scope": "reinsurer_C_recoverable",
        "period": "current_period",
        "format": "decimal"
      },
      "a_rate": {
        "value": 0.02,
        "unit": "fraction",
        "evidence_id": "C",
        "quote": "A2%",
        "literal": "2%",
        "scope": "reinsurer_A_base",
        "period": "current_period",
        "format": "percent"
      },
      "b_rate": {
        "value": 0.05,
        "unit": "fraction",
        "evidence_id": "C",
        "quote": "B5%",
        "literal": "5%",
        "scope": "reinsurer_B_base",
        "period": "current_period",
        "format": "percent"
      },
      "c_rate": {
        "value": 0.1,
        "unit": "fraction",
        "evidence_id": "C",
        "quote": "C10%",
        "literal": "10%",
        "scope": "reinsurer_C_base",
        "period": "current_period",
        "format": "percent"
      },
      "premium": {
        "value": 500,
        "unit": "million_usd",
        "evidence_id": "D",
        "quote": "Net earned premium500",
        "literal": "500",
        "scope": "net_premium",
        "period": "current_period",
        "format": "decimal"
      },
      "claims": {
        "value": 330,
        "unit": "million_usd",
        "evidence_id": "D",
        "quote": "net incurred claims330",
        "literal": "330",
        "scope": "net_claims",
        "period": "current_period",
        "format": "decimal"
      },
      "expense": {
        "value": 110,
        "unit": "million_usd",
        "evidence_id": "D",
        "quote": "underwriting expense110",
        "literal": "110",
        "scope": "underwriting_expense",
        "period": "current_period",
        "format": "decimal"
      },
      "invest": {
        "value": 25,
        "unit": "million_usd",
        "evidence_id": "D",
        "quote": "Investment net income25",
        "literal": "25",
        "scope": "investment_income",
        "period": "current_period",
        "format": "decimal"
      },
      "tax": {
        "value": 10,
        "unit": "million_usd",
        "evidence_id": "D",
        "quote": "tax10",
        "literal": "10",
        "scope": "tax",
        "period": "current_period",
        "format": "decimal"
      }
    }
  },
  {
    "id": "A039-06-j",
    "result_unit": "percent",
    "expression": "(eligible-((a_rec-a_coll)*a_rate+(b_rec-b_coll)*b_rate+c_rec*c_rate))/required",
    "operands": {
      "a_rec": {
        "value": 90,
        "unit": "million_usd",
        "evidence_id": "B",
        "quote": "|A|90|30|20|",
        "literal": "90",
        "scope": "reinsurer_A_recoverable",
        "period": "current_period",
        "format": "decimal"
      },
      "a_coll": {
        "value": 30,
        "unit": "million_usd",
        "evidence_id": "B",
        "quote": "|A|90|30|20|",
        "literal": "30",
        "scope": "reinsurer_A_collateral",
        "period": "current_period",
        "format": "decimal"
      },
      "b_rec": {
        "value": 60,
        "unit": "million_usd",
        "evidence_id": "B",
        "quote": "|B|60|10|0|",
        "literal": "60",
        "scope": "reinsurer_B_recoverable",
        "period": "current_period",
        "format": "decimal"
      },
      "b_coll": {
        "value": 10,
        "unit": "million_usd",
        "evidence_id": "B",
        "quote": "|B|60|10|0|",
        "literal": "10",
        "scope": "reinsurer_B_collateral",
        "period": "current_period",
        "format": "decimal"
      },
      "c_rec": {
        "value": 30,
        "unit": "million_usd",
        "evidence_id": "B",
        "quote": "|C|30|0|15|",
        "literal": "30",
        "scope": "reinsurer_C_recoverable",
        "period": "current_period",
        "format": "decimal"
      },
      "a_rate": {
        "value": 0.02,
        "unit": "fraction",
        "evidence_id": "C",
        "quote": "A2%",
        "literal": "2%",
        "scope": "reinsurer_A_base",
        "period": "current_period",
        "format": "percent"
      },
      "b_rate": {
        "value": 0.05,
        "unit": "fraction",
        "evidence_id": "C",
        "quote": "B5%",
        "literal": "5%",
        "scope": "reinsurer_B_base",
        "period": "current_period",
        "format": "percent"
      },
      "c_rate": {
        "value": 0.1,
        "unit": "fraction",
        "evidence_id": "C",
        "quote": "C10%",
        "literal": "10%",
        "scope": "reinsurer_C_base",
        "period": "current_period",
        "format": "percent"
      },
      "eligible": {
        "value": 250,
        "unit": "million_usd",
        "evidence_id": "E",
        "quote": "Eligible capital before this newly calculated ECL charge250",
        "literal": "250",
        "scope": "eligible_capital",
        "period": "current_period",
        "format": "decimal"
      },
      "required": {
        "value": 200,
        "unit": "million_usd",
        "evidence_id": "E",
        "quote": "required capital200",
        "literal": "200",
        "scope": "required_capital",
        "period": "current_period",
        "format": "decimal"
      }
    }
  },
  {
    "id": "A039-06-l",
    "result_unit": "million_usd",
    "expression": "(a_rec-a_coll*(1-haircut))*stress_rate+(b_rec-b_coll)*b_rate+c_rec*c_rate-((a_rec-a_coll)*a_rate+(b_rec-b_coll)*b_rate+c_rec*c_rate)",
    "operands": {
      "a_rec": {
        "value": 90,
        "unit": "million_usd",
        "evidence_id": "B",
        "quote": "|A|90|30|20|",
        "literal": "90",
        "scope": "reinsurer_A_recoverable",
        "period": "current_period",
        "format": "decimal"
      },
      "a_coll": {
        "value": 30,
        "unit": "million_usd",
        "evidence_id": "B",
        "quote": "|A|90|30|20|",
        "literal": "30",
        "scope": "reinsurer_A_collateral",
        "period": "current_period",
        "format": "decimal"
      },
      "b_rec": {
        "value": 60,
        "unit": "million_usd",
        "evidence_id": "B",
        "quote": "|B|60|10|0|",
        "literal": "60",
        "scope": "reinsurer_B_recoverable",
        "period": "current_period",
        "format": "decimal"
      },
      "b_coll": {
        "value": 10,
        "unit": "million_usd",
        "evidence_id": "B",
        "quote": "|B|60|10|0|",
        "literal": "10",
        "scope": "reinsurer_B_collateral",
        "period": "current_period",
        "format": "decimal"
      },
      "c_rec": {
        "value": 30,
        "unit": "million_usd",
        "evidence_id": "B",
        "quote": "|C|30|0|15|",
        "literal": "30",
        "scope": "reinsurer_C_recoverable",
        "period": "current_period",
        "format": "decimal"
      },
      "a_rate": {
        "value": 0.02,
        "unit": "fraction",
        "evidence_id": "C",
        "quote": "A2%",
        "literal": "2%",
        "scope": "reinsurer_A_base",
        "period": "current_period",
        "format": "percent"
      },
      "b_rate": {
        "value": 0.05,
        "unit": "fraction",
        "evidence_id": "C",
        "quote": "B5%",
        "literal": "5%",
        "scope": "reinsurer_B_base",
        "period": "current_period",
        "format": "percent"
      },
      "c_rate": {
        "value": 0.1,
        "unit": "fraction",
        "evidence_id": "C",
        "quote": "C10%",
        "literal": "10%",
        "scope": "reinsurer_C_base",
        "period": "current_period",
        "format": "percent"
      },
      "haircut": {
        "value": 0.5,
        "unit": "fraction",
        "evidence_id": "F",
        "quote": "A eligible collateral loses 50% of value",
        "literal": "50%",
        "scope": "reinsurer_A_stress",
        "period": "current_period",
        "format": "percent"
      },
      "stress_rate": {
        "value": 0.08,
        "unit": "fraction",
        "evidence_id": "F",
        "quote": "A ECL rate rises to8%",
        "literal": "8%",
        "scope": "reinsurer_A_stress",
        "period": "current_period",
        "format": "percent"
      }
    }
  }
]

def _literal_value(literal,fmt):
    if fmt=="percent":
        assert literal.endswith("%")
        return Decimal(literal[:-1])/100
    if fmt=="thousands_dot":
        assert "." in literal and all(len(x)==3 for x in literal.split(".")[1:])
        return Decimal(literal.replace(".",""))
    assert fmt=="decimal"
    return Decimal(literal)

def verify_graph(row,graph):
    assert row["id"]==graph["id"]
    evidence={e["id"]:e["text"] for e in row["evidence"]}
    values={}; used=set()
    for name,operand in graph["operands"].items():
        cite=operand["evidence_id"]
        assert cite in row["evidence_ids"] and cite in evidence,(row["id"],name,cite)
        assert operand["quote"] in evidence[cite],(row["id"],name,"missing quote")
        assert operand["literal"] in operand["quote"],(row["id"],name,"missing literal")
        assert operand["scope"] and operand["period"]
        val=_literal_value(operand["literal"],operand["format"])
        assert val==Decimal(str(operand["value"])),(row["id"],name,"value mismatch")
        values[name]=(val,operand["unit"])
    def evaluate(n):
        if isinstance(n,ast.Name):
            used.add(n.id);return values[n.id]
        if isinstance(n,ast.Constant) and type(n.value)==int and n.value in (0,1):
            return Decimal(n.value),"fraction"
        if isinstance(n,ast.BinOp):
            a,ua=evaluate(n.left);b,ub=evaluate(n.right)
            if isinstance(n.op,(ast.Add,ast.Sub)):
                assert ua==ub,(row["id"],"incompatible add/sub",ua,ub)
                return (a+b if isinstance(n.op,ast.Add) else a-b),ua
            if isinstance(n.op,ast.Mult):
                assert "fraction" in (ua,ub),(row["id"],"unsupported multiplication",ua,ub)
                return a*b,ub if ua=="fraction" else ua
            if isinstance(n.op,ast.Div):
                assert b!=0
                if ua==ub:return a/b,"fraction"
                assert ub=="fraction",(row["id"],"unsupported division",ua,ub)
                return a/b,ua
        raise ValueError("Unsafe or unsupported graph node: "+type(n).__name__)
    val,unit=evaluate(ast.parse(graph["expression"],mode="eval").body)
    assert used==set(values),(row["id"],"unused operands")
    expected_unit=graph["result_unit"]
    if expected_unit=="percent":
        assert unit=="fraction";val*=100
    elif expected_unit=="times":
        assert unit=="fraction"
    else:assert unit==expected_unit
    assert row["oracle"]["kind"]=="numeric" and row["oracle"]["unit"]==expected_unit
    assert math.isclose(float(val),row["oracle"]["value"],rel_tol=1e-8,abs_tol=1e-8),row["id"]
    return float(val)

def apply_graphs(rows):
    by_id={r["id"]:r for r in rows}
    assert len({g["id"] for g in GRAPHS})==len(GRAPHS)
    for g in GRAPHS:
        r=by_id[g["id"]]
        assert r["split"]=="train"
        verify_graph(r,g)
        r["calculation_graph"]={**g,"verification":"manual_operand_annotation_arithmetic_checked","limitations":"Scope/period tags are authored metadata; not accounting-policy proof."}
    return {"verified_graphs":len(GRAPHS),"named_operands":sum(len(g["operands"]) for g in GRAPHS),"full_corpus_coverage":False}
