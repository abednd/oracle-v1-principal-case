"""
Recovery logic — base and stress scenarios.

base_recovery   = fmv_central x (1 - base_haircut)        [orderly sale]
stress_recovery = fmv_low     x (1 - stress_haircut)      [forced sale, weak market]

Path = redeployment if liquid AND broadly applicable, else liquidation.
The headline underwriting signal is stress_recovery vs requested_financing.
"""
from . import params


def _liquidity_bucket(asset, geo_tier):
    liq = str(asset.get("secondary_market_liquidity", "medium")).lower()
    # thin geography drags effective liquidity down a notch
    if geo_tier == "C":
        order = ["high", "medium", "low", "thin"]
        if liq in order:
            i = min(order.index(liq) + 1, len(order) - 1)
            liq = order[i]
    return liq


def assess_recovery(asset, valuation, deal):
    geo_tier = valuation["_geo_tier"]
    liq = _liquidity_bucket(asset, geo_tier)
    apps = str(asset.get("typical_applications", "")).split("|")
    n_apps = len([a for a in apps if a])

    redeployable = (liq in params.REDEPLOY_LIQUIDITY_OK) and (n_apps >= params.REDEPLOY_MIN_APPLICATIONS)
    path = "redeployment" if redeployable else "liquidation"

    base_haircut = params.RECOVERY_BASE_HAIRCUT[path]
    stress_haircut = params.RECOVERY_STRESS_HAIRCUT[path]
    if geo_tier == "C":
        stress_haircut += params.RECOVERY_STRESS_TIER_C_EXTRA

    base_recovery = valuation["fmv_central"] * (1 - base_haircut)
    stress_recovery = valuation["fmv_low"] * (1 - stress_haircut)

    tts_base = params.TIME_TO_SELL_BASE.get(liq, 6)
    tts_stress = min(tts_base * params.TIME_TO_SELL_STRESS_MULT, params.TIME_TO_SELL_STRESS_CAP)

    # recovery confidence: liquidity + comp depth + standardisation
    if liq in ("high", "medium") and valuation["comp_count"] >= 4 and n_apps >= 2:
        rec_conf = "high"
    elif liq in ("low", "thin") or valuation["comp_count"] < 3:
        rec_conf = "low"
    else:
        rec_conf = "medium"

    requested_amt = float(deal["requested_financing_amount"])
    stress_covers = stress_recovery >= requested_amt

    return {
        "base_recovery_value": round(base_recovery / 500) * 500,
        "stress_recovery_value": round(stress_recovery / 500) * 500,
        "base_haircut_pct": round(base_haircut * 100, 1),
        "stress_haircut_pct": round(stress_haircut * 100, 1),
        "time_to_sell_months_base": tts_base,
        "time_to_sell_months_stress": tts_stress,
        "preferred_path": path,
        "recovery_confidence": rec_conf,
        "stress_covers_financing": bool(stress_covers),
    }
