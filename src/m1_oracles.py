"""Manual oracle annotations of the existing M1 authored answers.

No source QA is generated, changed, or moved across splits. Single requested
results get numeric labels; multi-result and qualitative questions require
review of the full narrative. Gold results are not inferred from the final
arithmetic check (which may be an intermediate or distractor).
"""
from copy import deepcopy

ORACLES = {
    "M1-IS02-01": {
        "kind": "numeric",
        "value": 25,
        "unit": "percent"
    },
    "M1-IS02-02": {
        "kind": "numeric",
        "value": 8,
        "unit": "pp"
    },
    "M1-IS02-03": {
        "kind": "insufficient"
    },
    "M1-IS03-01": {
        "kind": "qualitative"
    },
    "M1-IS03-02": {
        "kind": "qualitative"
    },
    "M1-IS05-01": {
        "kind": "multi_numeric",
        "results": [
            {
                "metric": "net_revenue",
                "value": 1350,
                "unit": "million_usd"
            },
            {
                "metric": "gross_margin",
                "value": 30,
                "unit": "percent"
            }
        ]
    },
    "M1-IS05-02": {
        "kind": "insufficient"
    },
    "M1-IS06-01": {
        "kind": "multi_numeric",
        "results": [
            {
                "metric": "completion",
                "value": 40,
                "unit": "percent"
            },
            {
                "metric": "recognized_revenue",
                "value": 360,
                "unit": "million_usd"
            }
        ]
    },
    "M1-IS06-02": {
        "kind": "numeric",
        "value": 140,
        "unit": "million_usd"
    },
    "M1-IS06-03": {
        "kind": "insufficient"
    },
    "M1-IS07-01": {
        "kind": "multi_numeric",
        "results": [
            {
                "metric": "usd_growth",
                "value": 4,
                "unit": "percent"
            },
            {
                "metric": "vnd_growth",
                "value": 8.333333,
                "unit": "percent"
            }
        ]
    },
    "M1-IS07-02": {
        "kind": "insufficient"
    },
    "M1-IS08-01": {
        "kind": "multi_numeric",
        "results": [
            {
                "metric": "operating_profit",
                "value": 200,
                "unit": "billion_vnd"
            },
            {
                "metric": "profit_before_tax",
                "value": 270,
                "unit": "billion_vnd"
            }
        ]
    },
    "M1-IS08-02": {
        "kind": "qualitative"
    },
    "M1-IS08-03": {
        "kind": "numeric",
        "value": 44.444444,
        "unit": "percent"
    },
    "M1-BS09-01": {
        "kind": "numeric",
        "value": 1.2,
        "unit": "times"
    },
    "M1-BS09-02": {
        "kind": "qualitative"
    },
    "M1-BS10-01": {
        "kind": "multi_numeric",
        "results": [
            {
                "metric": "2024_turnover",
                "value": 4,
                "unit": "times"
            },
            {
                "metric": "2025_turnover",
                "value": 3,
                "unit": "times"
            }
        ]
    },
    "M1-BS10-02": {
        "kind": "numeric",
        "value": 30.416667,
        "unit": "days"
    },
    "M1-BS10-03": {
        "kind": "insufficient"
    },
    "M1-BS12-01": {
        "kind": "numeric",
        "value": 1.625,
        "unit": "times"
    },
    "M1-BS12-02": {
        "kind": "numeric",
        "value": 1.825,
        "unit": "times"
    },
    "M1-BS12-03": {
        "kind": "insufficient"
    },
    "M1-BS13-01": {
        "kind": "numeric",
        "value": 105,
        "unit": "million_usd"
    },
    "M1-BS13-02": {
        "kind": "numeric",
        "value": 6,
        "unit": "pp"
    },
    "M1-BS15-01": {
        "kind": "numeric",
        "value": 320,
        "unit": "billion_vnd"
    },
    "M1-BS15-02": {
        "kind": "qualitative"
    },
    "M1-BS16-01": {
        "kind": "numeric",
        "value": 2400,
        "unit": "vnd_per_share"
    },
    "M1-BS16-02": {
        "kind": "numeric",
        "value": 2290.90909,
        "unit": "vnd_per_share"
    },
    "M1-BS16-03": {
        "kind": "qualitative"
    },
    "M1-CF18-01": {
        "kind": "numeric",
        "value": 180,
        "unit": "billion_vnd"
    },
    "M1-CF18-02": {
        "kind": "numeric",
        "value": 80,
        "unit": "billion_vnd"
    },
    "M1-CF18-03": {
        "kind": "insufficient"
    },
    "M1-CF19-01": {
        "kind": "numeric",
        "value": -310,
        "unit": "million_usd"
    },
    "M1-CF19-02": {
        "kind": "numeric",
        "value": 10,
        "unit": "million_usd"
    },
    "M1-CF20-01": {
        "kind": "numeric",
        "value": 140,
        "unit": "million_usd"
    },
    "M1-CF20-02": {
        "kind": "qualitative"
    },
    "M1-CF20-03": {
        "kind": "qualitative"
    },
    "M1-CF21-01": {
        "kind": "multi_numeric",
        "results": [
            {
                "metric": "recognized_revenue",
                "value": 60,
                "unit": "million_usd"
            },
            {
                "metric": "contract_liability",
                "value": 180,
                "unit": "million_usd"
            }
        ]
    },
    "M1-CF21-02": {
        "kind": "qualitative"
    },
    "M1-CF23-01": {
        "kind": "numeric",
        "value": 120,
        "unit": "billion_vnd"
    },
    "M1-CF23-02": {
        "kind": "numeric",
        "value": 40,
        "unit": "percent"
    },
    "M1-CF24-01": {
        "kind": "numeric",
        "value": -20,
        "unit": "billion_vnd"
    },
    "M1-CF24-02": {
        "kind": "qualitative"
    },
    "M1-CF24-03": {
        "kind": "qualitative"
    },
    "M1-NT25-01": {
        "kind": "numeric",
        "value": 180,
        "unit": "billion_vnd"
    },
    "M1-NT25-02": {
        "kind": "insufficient"
    },
    "M1-NT26-01": {
        "kind": "numeric",
        "value": 18.4210526,
        "unit": "percent"
    },
    "M1-NT26-02": {
        "kind": "numeric",
        "value": 12.5,
        "unit": "percent"
    },
    "M1-NT26-03": {
        "kind": "qualitative"
    },
    "M1-NT27-01": {
        "kind": "numeric",
        "value": 1250,
        "unit": "million_usd"
    },
    "M1-NT27-02": {
        "kind": "qualitative"
    },
    "M1-NT28-01": {
        "kind": "numeric",
        "value": 300,
        "unit": "million_usd"
    },
    "M1-NT28-02": {
        "kind": "numeric",
        "value": 10,
        "unit": "million_usd"
    },
    "M1-NT28-03": {
        "kind": "qualitative"
    },
    "M1-NT30-01": {
        "kind": "qualitative"
    },
    "M1-NT30-02": {
        "kind": "numeric",
        "value": 3.6,
        "unit": "times"
    },
    "M1-NT30-03": {
        "kind": "insufficient"
    },
    "M1-NT31-01": {
        "kind": "multi_numeric",
        "results": [
            {
                "metric": "loan",
                "value": 200,
                "unit": "billion_vnd"
            },
            {
                "metric": "interest",
                "value": 16,
                "unit": "billion_vnd"
            }
        ]
    },
    "M1-NT31-02": {
        "kind": "numeric",
        "value": 8,
        "unit": "percent"
    },
    "M1-X33-01": {
        "kind": "numeric",
        "value": 5,
        "unit": "percent"
    },
    "M1-X33-02": {
        "kind": "numeric",
        "value": 3,
        "unit": "percent"
    },
    "M1-X34-01": {
        "kind": "numeric",
        "value": 93,
        "unit": "percent"
    },
    "M1-X34-02": {
        "kind": "numeric",
        "value": 56,
        "unit": "million_usd"
    },
    "M1-X34-03": {
        "kind": "insufficient"
    },
    "M1-X35-01": {
        "kind": "numeric",
        "value": 640,
        "unit": "million_usd"
    },
    "M1-X35-02": {
        "kind": "insufficient"
    },
    "M1-X36-01": {
        "kind": "numeric",
        "value": 50,
        "unit": "million_usd"
    },
    "M1-X36-02": {
        "kind": "multi_numeric",
        "results": [
            {
                "metric": "net_carrying_amount",
                "value": 50,
                "unit": "million_usd"
            },
            {
                "metric": "development_cash_outflow",
                "value": 100,
                "unit": "million_usd"
            }
        ]
    },
    "M1-X36-03": {
        "kind": "numeric",
        "value": 50,
        "unit": "million_usd"
    },
    "M1-X37-01": {
        "kind": "numeric",
        "value": 8,
        "unit": "percent"
    },
    "M1-X37-02": {
        "kind": "insufficient"
    },
    "M1-X38-01": {
        "kind": "numeric",
        "value": -5,
        "unit": "percent"
    },
    "M1-X38-02": {
        "kind": "qualitative"
    },
    "M1-X38-03": {
        "kind": "qualitative"
    },
    "M1-X39-01": {
        "kind": "insufficient"
    },
    "M1-X39-02": {
        "kind": "numeric",
        "value": 8,
        "unit": "percent"
    },
    "M1-X40-01": {
        "kind": "numeric",
        "value": 870,
        "unit": "billion_vnd"
    },
    "M1-X40-02": {
        "kind": "multi_numeric",
        "results": [
            {
                "metric": "downward_revision",
                "value": 30,
                "unit": "billion_vnd"
            },
            {
                "metric": "downward_revision_percent",
                "value": 3.333333,
                "unit": "percent"
            }
        ]
    },
    "M1-X40-03": {
        "kind": "insufficient"
    },
    "M1-IS01-01": {
        "kind": "multi_numeric",
        "results": [
            {
                "metric": "revenue_growth",
                "value": 30,
                "unit": "percent"
            },
            {
                "metric": "gross_margin_change",
                "value": -5,
                "unit": "pp"
            }
        ]
    },
    "M1-IS01-02": {
        "kind": "qualitative"
    },
    "M1-BS11-01": {
        "kind": "multi_numeric",
        "results": [
            {
                "metric": "2024_current_ratio",
                "value": 1.42857,
                "unit": "times"
            },
            {
                "metric": "2025_current_ratio",
                "value": 1.65,
                "unit": "times"
            },
            {
                "metric": "2024_cash_ratio",
                "value": 0.42857,
                "unit": "times"
            },
            {
                "metric": "2025_cash_ratio",
                "value": 0.225,
                "unit": "times"
            }
        ]
    },
    "M1-BS11-02": {
        "kind": "insufficient"
    },
    "M1-CF22-01": {
        "kind": "qualitative"
    },
    "M1-CF22-02": {
        "kind": "qualitative"
    },
    "M1-CF22-03": {
        "kind": "insufficient"
    },
    "M1-NT32-01": {
        "kind": "numeric",
        "value": 60,
        "unit": "billion_vnd"
    },
    "M1-NT32-02": {
        "kind": "qualitative"
    },
    "M1-NT32-03": {
        "kind": "insufficient"
    },
    "M1-IS04-01": {
        "kind": "numeric",
        "value": 14,
        "unit": "percent"
    },
    "M1-IS04-02": {
        "kind": "multi_numeric",
        "results": [
            {
                "metric": "2024_revpar",
                "value": 60,
                "unit": "usd"
            },
            {
                "metric": "2025_revpar",
                "value": 68.4,
                "unit": "usd"
            }
        ]
    },
    "M1-IS04-03": {
        "kind": "insufficient"
    },
    "M1-BS14-01": {
        "kind": "numeric",
        "value": 35.714286,
        "unit": "percent"
    },
    "M1-BS14-02": {
        "kind": "numeric",
        "value": 150,
        "unit": "million_usd"
    },
    "M1-BS14-03": {
        "kind": "insufficient"
    },
    "M1-CF17-01": {
        "kind": "numeric",
        "value": 110,
        "unit": "billion_vnd"
    },
    "M1-CF17-02": {
        "kind": "qualitative"
    },
    "M1-NT29-01": {
        "kind": "numeric",
        "value": 700,
        "unit": "million_usd"
    },
    "M1-NT29-02": {
        "kind": "qualitative"
    }
}

def m1_oracle(row_id):
    return deepcopy(ORACLES.get(row_id))
