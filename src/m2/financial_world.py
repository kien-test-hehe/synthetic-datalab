"""Reproducible, deliberately simplified synthetic double-entry financial worlds.

NOT an accounting standards implementation. Never uses real company reports or labels.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import random

SECTORS = ("manufacturing", "retail", "logistics", "software")


def rnd_percent(value: int, percent: int) -> int:
    return round(value * percent / 100)


def create_world(seed: int, index: int, sector: str) -> dict:
    rng = random.Random(f"financialdoclab.m2.{seed}.{index}")
    name = f"Fictional Meridian {index:04d}"  # distinct from any real source document
    cash, ar, inventory, ppe, ap, debt = (
        rng.randint(600, 2050),rng.randint(190,420),rng.randint(230,570),
        rng.randint(1850,2700),rng.randint(160,380),rng.randint(700,1800))
    equity = cash + ar + inventory + ppe - ap - debt
    previous = None
    years = {}
    sector_ranges={
        "manufacturing": ((55,70),(10,15),(170,285)),
        "retail": ((58,72),(9,14),(75,175)),
        "logistics": ((52,66),(11,17),(185,300)),
        "software": ((45,59),(15,22),(55,135)),
    }
    cog_range, ope_range, cap_range = sector_ranges[sector]
    growth = rng.randint(-7, 20)
    revenue = rng.randrange(1300, 3400, 10)
    for year in (2023, 2024, 2025):
        if year > 2023:
            # Correlated, but non-monotone annual growth to prevent trivial trends.
            growth = max(-25, min(38, growth + rng.randint(-17, 15)))
            revenue = max(1100, rnd_percent(revenue, 100 + growth))
        cogs = rnd_percent(revenue, rng.randint(*cog_range))
        cash_opex = rnd_percent(revenue, rng.randint(*ope_range))
        dep = rng.randrange(25, 73)
        interest = rng.randrange(18, 52)
        pretax = revenue - cogs - cash_opex - dep - interest
        tax = max(0, rnd_percent(pretax, 20))
        net_income = pretax - tax
        d_ar = rng.randrange(-22, 110)
        d_inv = rng.randrange(-26, 106)
        if rng.random() < 0.18:
            # A stress subpopulation: profitable firms with cash trapped in working capital.
            d_ar += rng.randint(90,160)
            d_inv += rng.randint(70,150)
        d_ap = rng.randrange(-18, 82)
        capex = rng.randint(*cap_range)
        new_debt, debt_repaid = rng.randrange(0, 145), rng.randrange(15, 93)
        dividends = rng.randrange(0, 65)
        begin_cash = cash
        prior_ar, prior_inv, prior_ap = ar, inventory, ap
        prior_ppe, prior_debt, prior_equity = ppe, debt, equity
        ar, inventory, ap = ar + d_ar, inventory + d_inv, ap + d_ap
        debt = debt + new_debt - debt_repaid
        ppe = ppe + capex - dep
        cfo = net_income + dep - d_ar - d_inv + d_ap
        cfi = -capex
        cff = new_debt - debt_repaid - dividends
        fx_effect = 0
        cash = begin_cash + cfo + cfi + cff + fx_effect
        current_debt = rnd_percent(debt, 25)
        long_debt = debt - current_debt
        current_assets = cash + ar + inventory
        current_liabilities = ap + current_debt
        assets = current_assets + ppe
        liabilities = ap + debt
        equity = assets - liabilities
        assert equity == prior_equity + net_income - dividends
        assert cash == begin_cash + cfo + cfi + cff
        assert assets == liabilities + equity
        assert min(ar, inventory, ap, debt, cash, ppe, equity) > 0
        assert net_income > 0
        years[str(year)] = dict(
            year=year, revenue=revenue, cogs=cogs, gross_profit=revenue-cogs,
            cash_opex=cash_opex, dep=dep, interest=interest, pretax=pretax,
            tax=tax, net_income=net_income, operating_profit=revenue-cogs-cash_opex-dep,
            begin_cash=begin_cash, cash=cash, ar=ar, inventory=inventory, ap=ap,
            delta_ar=d_ar, delta_inventory=d_inv, delta_ap=d_ap,
            cfo=cfo, cfi=cfi, cff=cff, fx_effect=fx_effect, capex=capex,
            new_debt=new_debt, debt_repaid=debt_repaid, dividends=dividends,
            ppe=ppe, debt=debt, current_debt=current_debt, long_debt=long_debt,
            current_assets=current_assets, current_liabilities=current_liabilities,
            assets=assets, liabilities=liabilities, equity=equity,
            prior_ar=prior_ar, prior_inventory=prior_inv, prior_ap=prior_ap,
            prior_ppe=prior_ppe, prior_debt=prior_debt, prior_equity=prior_equity,
            ebitda=revenue-cogs-cash_opex,  # operating profit + depreciation, simplified EBITDA
        )
    # Segment notes. Product gross revenue includes an intra-group sale that must be eliminated.
    segments = {}
    for year in (2024, 2025):
        y = years[str(year)]
        share = rng.randrange(45, 60)
        ext_a = rnd_percent(y['revenue'], share)
        ext_b = y['revenue'] - ext_a
        cogs_a = rnd_percent(y['cogs'], share - rng.randint(2, 8))
        cogs_b = y['cogs'] - cogs_a
        assert 0 < cogs_a < ext_a and 0 < cogs_b < ext_b
        internal = rng.randint(20, 100)
        segments[str(year)] = dict(ext_a=ext_a, ext_b=ext_b,
                                   cogs_a=cogs_a, cogs_b=cogs_b, internal=internal,
                                   gross_segment_sales=y['revenue']+internal)
    # These are UNOFFICIAL candidate numbers for document-version confusion tasks.
    preliminary_revenue_25 = years['2025']['revenue'] + rng.randint(25, 85)
    originally_reported_24 = years['2024']['revenue'] + rng.randint(20, 66)
    # A classification change shifts sales to other income in originally-issued FY2024; NI unchanged.
    return dict(id=f"m2-world-{index:04d}", name=name, sector=sector,
                fiscal_years=years, segments=segments,
                preliminary_revenue_25=preliminary_revenue_25,
                original_revenue_24=originally_reported_24,
                currency="USD million", standard="synthetic simplified accrual accounting",
                source="entirely_fictional_event_simulator", seed=seed)


def audit_world(w):
    years=w['fiscal_years']
    prev_eq=None
    for yr in ('2023','2024','2025'):
        x=years[yr]
        assert x['revenue']-x['cogs']-x['cash_opex']-x['dep']-x['interest']-x['tax']==x['net_income']
        assert x['net_income']+x['dep']-x['delta_ar']-x['delta_inventory']+x['delta_ap']==x['cfo']
        assert x['begin_cash']+x['cfo']+x['cfi']+x['cff']==x['cash']
        assert x['assets']==x['liabilities']+x['equity']
        if prev_eq is not None:
            assert prev_eq + x['net_income']-x['dividends']==x['equity']
        prev_eq=x['equity']
    for yr in ('2024','2025'):
        s=w['segments'][yr];x=years[yr]
        assert s['ext_a']+s['ext_b']==x['revenue']
        assert s['cogs_a']+s['cogs_b']==x['cogs']
        assert s['gross_segment_sales']-s['internal']==x['revenue']
    return True


def flat(w):
    d={}
    for yr in ('2023','2024','2025'):
        y=w['fiscal_years'][yr];s=yr[-2:]
        d.update({f'{k}{s}':v for k,v in y.items() if isinstance(v,(int,float))})
    for yr in ('2024','2025'):
        d.update({f'{k}{yr[-2:]}':v for k,v in w['segments'][yr].items()})
    d['preliminary_rev25']=w['preliminary_revenue_25']
    d['original_rev24']=w['original_revenue_24']
    return d
