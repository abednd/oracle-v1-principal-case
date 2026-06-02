"""Risk flags — simple rule set over the valuation, recovery and deal."""
from . import params


def build_flags(asset, valuation, recovery, ltv, deal):
    flags = []

    def add(ftype, severity, msg):
        flags.append({"flag_type": ftype, "severity": severity, "message": msg})

    if valuation["_used_fallback"] or valuation["comp_count"] < 3:
        add("thin_comps", "warning",
            f"Only {valuation['comp_count']} comparable(s); valuation widened and confidence reduced.")

    if valuation["_hours"] is not None and valuation["_hours"] > params.HOURS_FLAG_THRESHOLD:
        add("high_hours", "caution",
            f"{int(valuation['_hours']):,} operating hours exceeds the {params.HOURS_FLAG_THRESHOLD:,}h threshold.")

    if valuation["adjustments"]["generation"] < 1.0:
        add("generation_obsolescence", "caution",
            "Model discontinued or controller superseded; resale and redeployability discounted.")

    if valuation["_geo_tier"] == "C":
        add("geography_illiquid", "caution",
            "Thin local secondary market; longer time-to-sell and deeper stress haircut applied.")

    if str(deal.get("end_customer_industry", "")).lower() in params.END_USE_SPECIFIC_INDUSTRIES:
        add("end_use_specificity", "caution",
            f"End use ({deal['end_customer_industry']}) may narrow redeployability.")

    # single-source comps
    src_types = {c["source_type"] for c in valuation["comps_used"]}
    if valuation["comp_count"] >= 1 and len(src_types) == 1:
        add("single_source_comps", "info",
            "All comparables come from a single source type; price signal less independent.")

    if ltv["requested_ltv_pct"] > ltv["recommended_ltv_pct"]:
        gap = ltv["requested_ltv_pct"] - ltv["recommended_ltv_pct"]
        sev = "warning" if gap > params.DECISION_REVIEW_BAND else "caution"
        add("high_requested_ltv", sev,
            f"Requested LTV exceeds recommended by {gap:.0f}pts.")

    if not recovery["stress_covers_financing"]:
        add("stress_recovery_shortfall", "warning",
            "Stress-case recovery does not cover requested financing on the arm alone.")

    return flags
