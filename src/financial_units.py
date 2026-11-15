"""Audited unit vocabulary for the original 10K authored snapshot.

No automatic change of scale, currency, magnitude or numeric gold value.
Global aliases are dimension/scale equivalent. Context-dependent legacy
labels are resolved only for specifically reviewed QA IDs.
"""
from copy import deepcopy
import math
import re

RAW_AUTHORED_UNITS = frozenset([
    "bed_days",
    "billion_vnd",
    "billion_vnd_per_publication",
    "billion_vnd_per_year",
    "bps",
    "claims",
    "container_days",
    "containers",
    "covers",
    "days",
    "hours",
    "incidents_per_million_hours",
    "individuals",
    "kg_per_tonne_km",
    "km",
    "kt_per_million_usd",
    "kwh",
    "litres",
    "member_months",
    "million_ask",
    "million_attempts",
    "million_calls",
    "million_eur",
    "million_events",
    "million_gb",
    "million_hours",
    "million_kg",
    "million_km",
    "million_kwh",
    "million_liters",
    "million_m3",
    "million_mwh",
    "million_parcels",
    "million_passengers",
    "million_people",
    "million_requests",
    "million_rpk",
    "million_shares",
    "million_subscriber_months",
    "million_subscribers",
    "million_tablets",
    "million_tco2e",
    "million_tonnes",
    "million_transactions",
    "million_units",
    "million_usd",
    "million_usd_per_batch",
    "million_usd_per_month",
    "million_usd_per_year",
    "million_usd_years",
    "million_vnd",
    "million_vnd_per_bed_day",
    "million_vnd_per_day",
    "million_vnd_per_hour",
    "million_vnd_per_kg",
    "million_vnd_per_m2",
    "million_vnd_per_tonne",
    "million_vnd_per_unit",
    "million_vnd_per_visit",
    "minutes",
    "months",
    "mw_hours",
    "mwh",
    "pallet_days",
    "percent",
    "policies",
    "pp",
    "ratio",
    "room_nights",
    "seats",
    "subscriber_minutes",
    "tco2e_per_mwh",
    "tenants",
    "tenants_per_tower",
    "teu",
    "thousand_appointments",
    "thousand_bundles",
    "thousand_credits",
    "thousand_hours",
    "thousand_kg",
    "thousand_member_months",
    "thousand_moves",
    "thousand_mwh",
    "thousand_orders",
    "thousand_shipments",
    "thousand_subscribers",
    "thousand_tco2e",
    "thousand_teu",
    "thousand_tonnes",
    "thousand_units",
    "thousand_vnd_per_kwh",
    "thousand_vnd_per_month",
    "thousand_vnd_per_share",
    "times",
    "tonnes",
    "tonnes_co2e",
    "tonnes_per_mwh",
    "units",
    "usd",
    "usd_per_ask",
    "usd_per_available_room",
    "usd_per_barrel",
    "usd_per_bed_day",
    "usd_per_claim",
    "usd_per_customer",
    "usd_per_customer_month",
    "usd_per_device",
    "usd_per_discharge",
    "usd_per_episode",
    "usd_per_gb",
    "usd_per_ha",
    "usd_per_hour",
    "usd_per_kg",
    "usd_per_km",
    "usd_per_liter",
    "usd_per_m3",
    "usd_per_member_month",
    "usd_per_month",
    "usd_per_mwh",
    "usd_per_order",
    "usd_per_ounce",
    "usd_per_policy",
    "usd_per_request",
    "usd_per_room_night",
    "usd_per_rpk",
    "usd_per_share",
    "usd_per_student",
    "usd_per_tablet",
    "usd_per_tco2e",
    "usd_per_thousand",
    "usd_per_tonne",
    "usd_per_tonne_km",
    "usd_per_unit",
    "usd_per_visit",
    "vnd_per_ask",
    "vnd_per_gb",
    "vnd_per_hour",
    "vnd_per_km",
    "vnd_per_month",
    "vnd_per_rpk",
    "vnd_per_share",
    "weeks",
    "weighted_cases",
    "years"
])
ALIASES = {
    "ratio":"times", "x":"times", "×":"times",
    "percentage":"percent", "%":"percent",
    "percentage_points":"pp", "percentage_point":"pp",
    "basis_points":"bps", "basis_point":"bps", "bp":"bps",
    "litres":"liters", "litre":"liters", "liter":"liters",
    "mw_hours":"mwh", "mw_hour":"mwh", "megawatt_hours":"mwh",
    "tonnes_co2e":"tco2e", "tonnes_co2_equivalent":"tco2e", "t_co2e":"tco2e",
}
# ID -> (legacy label, context-specific canonical label).
ROW_UNIT_OVERRIDES = {
    "A013-29-a":("tonnes_per_mwh","tco2e_per_mwh"),
    "A013-29-b":("tonnes_per_mwh","tco2e_per_mwh"),
    "A013-29-c":("tonnes_per_mwh","tco2e_per_mwh"),
    "A015-17-a":("usd_per_room_night","usd_per_available_room_night"),
    "A021-15-d":("usd_per_available_room","usd_per_available_room_night"),
    "A021-15-c":("usd_per_room_night","usd_per_occupied_room_night"),
    "A015-23-a":("usd_per_thousand","usd_per_thousand_impressions"),
    "A021-01-c":("million_vnd_per_day","million_vnd_per_bed_day"),
    "A039-16-a":("minutes","minutes_per_customer"),
    "A039-16-b":("minutes","minutes_per_customer"),
    "A039-16-e":("minutes","minutes_per_customer"),
    "A039-16-f":("minutes","minutes_per_customer"),
    "A043-09-c":("kt_per_million_usd","thousand_tco2e_per_million_usd"),
    "A043-26-b":("kg_per_tonne_km","kg_co2e_per_tonne_km"),
}

def unit_key(unit):
    if unit is None:return None
    return re.sub(r"[\s-]+","_",unit.strip().casefold())

def canonical_unit(unit,row_id=None):
    key=unit_key(unit)
    override=ROW_UNIT_OVERRIDES.get(row_id)
    if override and key==override[0]:return override[1]
    return ALIASES.get(key,key)

CANONICAL_UNITS = frozenset(canonical_unit(u) for u in RAW_AUTHORED_UNITS) | frozenset(v[1] for v in ROW_UNIT_OVERRIDES.values())
# These are unscaled counts; an integer requested result should not accept
# fractional items. Forecast/expected fractional counts retain precision policy.
DISCRETE_COUNTS=frozenset("bed_days claims container_days containers covers individuals member_months pallet_days policies room_nights seats subscriber_minutes tenants teu units weighted_cases".split())

def normalize_oracle(oracle,row_id=None):
    out=deepcopy(oracle)
    if out["kind"]=="numeric":
        old=out.get("original_unit",out["unit"])
        canonical=canonical_unit(old,row_id)
        if canonical!=old:
            out["original_unit"]=old
        out["unit"]=canonical
    elif out["kind"]=="multi_numeric":
        for entry in out["results"]:
            entry["unit"]=canonical_unit(entry["unit"],row_id)
    return out

def tolerance_for(oracle):
    gold=oracle["value"]
    explicit=oracle.get("abs_tolerance")
    if explicit is not None:
        if type(explicit) not in (int,float) or not math.isfinite(explicit) or explicit<0:
            raise ValueError("Invalid oracle abs_tolerance")
        return explicit
    unit=canonical_unit(oracle.get("unit"))
    if unit in DISCRETE_COUNTS and float(gold).is_integer():
        return 0.0
    if gold==0:return 1e-9
    # Conservative default: allow rounding at two decimal places only when
    # it is small relative to the gold value; exact scale still required.
    return min(.005,abs(gold)*.005)

def numeric_matches(value,oracle):
    if type(value) not in (int,float):return False
    try:
        if not math.isfinite(value):return False
    except OverflowError:
        return False
    gold=oracle["value"]
    if gold!=0 and (value==0 or (value>0)!=(gold>0)):return False
    tolerance=tolerance_for(oracle)
    return math.isclose(value,gold,rel_tol=0,abs_tol=tolerance+(1e-12 if tolerance else 0))
