"""
Valuation engine — comp-based FMV with explicit, inspectable adjustments.

Method (no ML):
  1. Gather comps for the exact asset; if < 3, widen to near comps and flag thin.
  2. Reference price = reliability-weighted median of comps, each first
     normalised to a "good condition / baseline" equivalent.
  3. Apply subject adjustments: age, condition, hours, geography, generation.
  4. Confidence score (0-100) from comp depth, dispersion, recency, sources,
     liquidity -> band -> +/- range width.
"""
import numpy as np
import pandas as pd

from . import params, data_access


def _geo_tier(country):
    return params.GEO_TIER.get(str(country).upper(), params.GEO_DEFAULT_TIER)


def _age_retention(age, arm_class):
    age = int(max(0, age))
    base = params.AGE_RETENTION.get(age, params.AGE_RETENTION_FLOOR) if age <= 12 else params.AGE_RETENTION_FLOOR
    return base * params.CLASS_RETENTION_MULT.get(arm_class, 1.0)


def _hours_mult(hours):
    if hours is None or pd.isna(hours) or hours <= params.HOURS_FREE:
        return 1.0
    if hours >= params.HOURS_REFERENCE:
        return params.HOURS_MULT_FLOOR
    # linear between FREE (1.0) and REFERENCE (HOURS_MULT_AT_REFERENCE)
    span = params.HOURS_REFERENCE - params.HOURS_FREE
    frac = (hours - params.HOURS_FREE) / span
    return 1.0 - frac * (1.0 - params.HOURS_MULT_AT_REFERENCE)


def _condition_mult(grade):
    return params.CONDITION_MULT.get(grade, 1.0)


def _normalise_comp_to_baseline(row, arm_class):
    """Strip a comp's own condition/age/hours so comps are comparable."""
    price = float(row["observed_price"])
    cond_f = _condition_mult(row.get("condition_grade", "good"))
    age_f = _age_retention(row.get("age_years", 0), arm_class)
    hrs_f = _hours_mult(row.get("operating_hours"))
    denom = cond_f * age_f * hrs_f
    return price / denom if denom > 0 else price


def _confidence(comps, geo_tier, used_fallback):
    n = len(comps)
    score = params.CONF_START
    if n >= 6:
        score += params.CONF_COMP_COUNT_HIGH
    else:
        score += params.CONF_COMP_COUNT.get(n, -25)

    if n >= 2:
        prices = comps["observed_price"].astype(float)
        cov = prices.std(ddof=0) / prices.mean() if prices.mean() else 1.0
        if cov < params.DISP_TIGHT:
            score += params.CONF_DISPERSION_TIGHT
        elif cov > params.DISP_WIDE:
            score += params.CONF_DISPERSION_WIDE

    if n >= 1 and "observation_date" in comps:
        dates = pd.to_datetime(comps["observation_date"], errors="coerce")
        newest = dates.max()
        if pd.notna(newest):
            months = (pd.Timestamp("2026-05-01") - newest).days / 30.0
            if months < 12:
                score += params.CONF_RECENT_BONUS
            oldest_months = (pd.Timestamp("2026-05-01") - dates.min()).days / 30.0
            if oldest_months > 36:
                score += params.CONF_STALE_PENALTY

    if n >= 1:
        sources = comps["source_type"].nunique()
        if sources >= 2:
            score += params.CONF_MULTISOURCE_BONUS
        else:
            score += params.CONF_SINGLESOURCE_PENALTY

    score += params.CONF_LIQUID_BONUS.get(geo_tier, 0)
    if used_fallback:
        score -= 8

    return int(max(1, min(99, score)))


def _band(score):
    for threshold, label, width in params.CONF_BANDS:
        if score >= threshold:
            return label, width
    return "low", 0.35


def value_asset(asset, year_of_manufacture, operating_hours, condition_grade,
                location_country, valuation_year=2026, currency=None):
    """Return a valuation dict (matches schema.Valuation)."""
    currency = currency or params.DEFAULT_CURRENCY
    arm_class = asset["arm_class"]
    age = max(0, valuation_year - int(year_of_manufacture))
    geo_tier = _geo_tier(location_country)

    comps = data_access.get_comps_for_asset(asset["asset_id"])
    used_fallback = False
    if len(comps) < 3:
        near = data_access.get_near_comps(asset)
        if len(near) > len(comps):
            comps = near
            used_fallback = True

    # reference price from normalised comps
    if len(comps) > 0:
        normalised = comps.apply(lambda r: _normalise_comp_to_baseline(r, arm_class), axis=1)
        weights = comps["reliability_weight"].astype(float).values
        order = np.argsort(normalised.values)
        sorted_vals = normalised.values[order]
        sorted_w = weights[order]
        cum = np.cumsum(sorted_w)
        cutoff = cum[-1] / 2.0
        ref_baseline = float(sorted_vals[np.searchsorted(cum, cutoff)])
        method = "comp_based"
    else:
        # last-resort curve fallback from MSRP
        new_gbp = float(asset["msrp_new_usd"]) * 0.79
        ref_baseline = new_gbp
        method = "curve_fallback"
        used_fallback = True

    # apply subject adjustments to the baseline reference
    adj_age = _age_retention(age, arm_class)
    adj_cond = _condition_mult(condition_grade)
    adj_hours = _hours_mult(operating_hours)
    adj_geo = params.GEO_TIER_MULT[geo_tier]
    disc = str(asset.get("year_discontinued", "")).strip()
    adj_gen = params.OBSOLESCENCE_MULT if disc not in ("", "nan", "None") else 1.0

    central = ref_baseline * adj_age * adj_cond * adj_hours * adj_geo * adj_gen

    score = _confidence(comps, geo_tier, used_fallback)
    band, width = _band(score)
    low = central * (1 - width)
    high = central * (1 + width)

    # comps_used preview (most recent / most reliable first, cap 6)
    comps_preview = []
    if len(comps) > 0:
        c = comps.copy()
        c["observation_date"] = pd.to_datetime(c["observation_date"], errors="coerce")
        c = c.sort_values(["reliability_weight", "observation_date"], ascending=False).head(6)
        for _, r in c.iterrows():
            comps_preview.append({
                "obs_id": r["obs_id"],
                "observed_price": int(r["observed_price"]),
                "currency": r["currency"],
                "observation_date": r["observation_date"].date().isoformat() if pd.notna(r["observation_date"]) else None,
                "condition_grade": r["condition_grade"],
                "operating_hours": None if pd.isna(r["operating_hours"]) else int(r["operating_hours"]),
                "age_years": float(r["age_years"]),
                "source_type": r["source_type"],
                "source_name": r["source_name"],
                "location_country": r["location_country"],
            })

    return {
        "fmv_low": round(low / 500) * 500,
        "fmv_central": round(central / 500) * 500,
        "fmv_high": round(high / 500) * 500,
        "currency": currency,
        "confidence_score": score,
        "confidence_band": band,
        "comp_count": int(len(comps)),
        "method": method,
        "adjustments": {
            "age": round(adj_age, 3),
            "condition": round(adj_cond, 3),
            "hours": round(adj_hours, 3),
            "geography": round(adj_geo, 3),
            "generation": round(adj_gen, 3),
        },
        "comps_used": comps_preview,
        # internal extras used downstream (not strictly in schema, handy for flags)
        "_geo_tier": geo_tier,
        "_used_fallback": used_fallback,
        "_age": age,
        "_hours": None if (operating_hours is None or pd.isna(operating_hours)) else float(operating_hours),
    }
