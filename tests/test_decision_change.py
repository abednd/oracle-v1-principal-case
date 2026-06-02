"""
The demo-critical test: changing one input flips the underwriting decision.
Plus monotonicity sanity checks so the engine never behaves absurdly on stage.

Run:  python -m pytest tests/ -q     (or)     python tests/test_decision_change.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from oracle.pack import underwriting_pack

BASE = dict(
    asset_id="fanuc_r2000ic_210f", year_of_manufacture=2021, operating_hours=12000,
    condition_grade="good", location_country="GB", requested_financing_amount=40000,
    total_project_cost=280000, requested_term_months=48,
    end_customer_industry="packaging", currency="GBP",
)


def _decision(**overrides):
    deal = dict(BASE, **overrides)
    return underwriting_pack(deal)["ltv"]["decision"]


def _fmv(**overrides):
    deal = dict(BASE, **overrides)
    return underwriting_pack(deal)["valuation"]["fmv_central"]


def _conf(**overrides):
    deal = dict(BASE, **overrides)
    return underwriting_pack(deal)["valuation"]["confidence_score"]


def test_baseline_is_go():
    assert _decision() == "go", "baseline deal should be GO"


def test_hours_stress_flips_decision():
    base = _decision()
    stressed = _decision(operating_hours=45000)
    assert base == "go"
    assert stressed in ("review", "reject")
    assert stressed != base, "raising hours must change the decision"


def test_geography_stress_flips_decision():
    base = _decision()
    stressed = _decision(location_country="BR")
    assert stressed != base, "thin geography must change the decision"


def test_more_hours_lowers_value():
    assert _fmv(operating_hours=45000) < _fmv(operating_hours=12000), \
        "more operating hours must not increase value"


def test_worse_condition_lowers_value():
    assert _fmv(condition_grade="poor") < _fmv(condition_grade="good") < _fmv(condition_grade="excellent")


def test_thin_market_model_has_lower_confidence():
    # yaskawa_gp180 has only 2 comps -> should score lower than the 7-comp baseline arm
    thin = underwriting_pack(dict(BASE, asset_id="yaskawa_gp180"))["valuation"]["confidence_score"]
    rich = _conf()
    assert thin < rich, "a thinly-comped model should have lower confidence"


def test_pack_shape_is_complete():
    p = underwriting_pack(BASE)
    for key in ("deal_id", "inputs", "asset_profile", "valuation", "ltv", "recovery", "risk_flags", "disclaimer"):
        assert key in p, f"pack missing {key}"
    for key in ("fmv_low", "fmv_central", "fmv_high", "confidence_score", "confidence_band", "comps_used"):
        assert key in p["valuation"], f"valuation missing {key}"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for fn in fns:
        try:
            fn(); print(f"PASS  {fn.__name__}"); passed += 1
        except AssertionError as e:
            print(f"FAIL  {fn.__name__}: {e}")
    print(f"\n{passed}/{len(fns)} tests passed")
    sys.exit(0 if passed == len(fns) else 1)
