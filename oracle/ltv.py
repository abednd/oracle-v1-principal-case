"""
LTV recommendation — rule-based.

Advance is sized against fmv_central, then sanity-checked against stress recovery
(collateral must hold under stress). Decision = go / review / reject.
"""
from . import params


def recommend_ltv(valuation, recovery, deal):
    band = valuation["confidence_band"]
    geo_tier = valuation["_geo_tier"]
    fmv_central = valuation["fmv_central"]

    ceiling = params.LTV_CEILING[band][geo_tier]

    deductions = []
    total_deduct = 0

    if valuation["_hours"] is not None and valuation["_hours"] > params.HOURS_FLAG_THRESHOLD:
        total_deduct += params.LTV_DEDUCT["high_hours"]; deductions.append("high hours")
    if valuation["adjustments"]["generation"] < 1.0:
        total_deduct += params.LTV_DEDUCT["generation_obsolescence"]; deductions.append("obsolescence")
    if valuation["_used_fallback"] or valuation["comp_count"] < 3:
        total_deduct += params.LTV_DEDUCT["thin_comps"]; deductions.append("thin comps")
    if str(deal.get("end_customer_industry", "")).lower() in params.END_USE_SPECIFIC_INDUSTRIES:
        total_deduct += params.LTV_DEDUCT["end_use_specificity"]; deductions.append("end-use specificity")
    if deal.get("requested_term_months", 0) > params.LONG_TERM_MONTHS:
        total_deduct += params.LTV_DEDUCT["long_term"]; deductions.append("long term")

    recommended = max(0, ceiling - total_deduct)
    requested_amt = float(deal["requested_financing_amount"])
    requested_ltv = (requested_amt / fmv_central * 100) if fmv_central else 999

    advance_recommended = recommended / 100.0 * fmv_central

    # hard cap: advance must not exceed stress recovery.
    # Only treat it as a *material* cap (worth surfacing) when the advance sits
    # meaningfully above stress recovery, not when they're within rounding noise.
    stress_recovery = recovery["stress_recovery_value"]
    capped_by_stress = False
    CAP_MATERIAL_MARGIN = 0.02  # 2% of stress recovery
    if advance_recommended > stress_recovery:
        material = (advance_recommended - stress_recovery) > (stress_recovery * CAP_MATERIAL_MARGIN)
        advance_recommended = stress_recovery
        if material:
            capped_by_stress = True
            recommended = min(recommended, round(stress_recovery / fmv_central * 100)) if fmv_central else recommended

    # decision
    stress_covers = stress_recovery >= requested_amt
    if requested_ltv <= recommended and stress_covers:
        decision = "go"
    elif requested_ltv <= recommended and not stress_covers:
        decision = "review"
    elif requested_ltv <= recommended + params.DECISION_REVIEW_BAND:
        decision = "review"
    else:
        decision = "reject"

    # rationale
    bits = [f"requested {requested_ltv:.0f}% vs recommended {recommended:.0f}%"]
    bits.append(f"{band} confidence")
    if deductions:
        bits.append("deductions: " + ", ".join(deductions))
    bits.append("stress recovery covers financing" if stress_covers else "stress recovery does NOT cover financing")
    if capped_by_stress:
        bits.append("recommended advance held at stress-recovery level for safety")
    rationale = "; ".join(bits) + "."

    return {
        "recommended_ltv_pct": round(recommended, 1),
        "max_ltv_pct": round(ceiling, 1),
        "requested_ltv_pct": round(requested_ltv, 1),
        "advance_recommended": round(advance_recommended / 500) * 500,
        "decision": decision,
        "rationale": rationale,
        "_stress_covers": stress_covers,
    }
