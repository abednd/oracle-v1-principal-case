"""
pack.py — THE entry point.

underwriting_pack(deal_input) -> dict, shaped exactly like the API response and
the schema.UnderwritingPack contract. Streamlit, FastAPI, demo.py and the tests
all call this one function. Everything else is an adapter around it.
"""
import uuid

from . import data_access, valuation as val, recovery as rec, ltv as ltv_mod, flags as flag_mod
from .schema import DealInput


DISCLAIMER = (
    "Asset specs are real; market transactions are synthetic for this case. "
    "Schema, valuation/recovery logic, and the API surface are production-shaped."
)


def _clean_internal(d):
    """Drop internal helper keys (prefixed with _) from a sub-dict."""
    return {k: v for k, v in d.items() if not k.startswith("_")}


def underwriting_pack(deal):
    """deal: DealInput or dict -> full underwriting pack dict."""
    if isinstance(deal, DealInput):
        deal = deal.to_dict()

    asset = data_access.get_asset(deal["asset_id"])
    if asset is None:
        raise ValueError(f"Unknown asset_id: {deal['asset_id']}")

    # 1. valuation
    valuation = val.value_asset(
        asset,
        year_of_manufacture=deal["year_of_manufacture"],
        operating_hours=deal.get("operating_hours"),
        condition_grade=deal["condition_grade"],
        location_country=deal["location_country"],
        currency=deal.get("currency"),
    )

    # 2. recovery (needs valuation)
    recovery = rec.assess_recovery(asset, valuation, deal)

    # 3. LTV (needs valuation + recovery)
    ltv = ltv_mod.recommend_ltv(valuation, recovery, deal)

    # 4. flags (needs everything)
    risk_flags = flag_mod.build_flags(asset, valuation, recovery, ltv, deal)

    # assemble asset profile
    disc = asset.get("year_discontinued")
    try:
        disc = int(disc) if str(disc).strip() not in ("", "nan", "None") else None
    except Exception:
        disc = None

    asset_profile = {
        "asset_id": asset["asset_id"],
        "manufacturer": asset["manufacturer"],
        "model": asset["model"],
        "series": asset.get("series", ""),
        "arm_class": asset["arm_class"],
        "payload_kg": float(asset["payload_kg"]),
        "reach_mm": float(asset["reach_mm"]),
        "axes": int(asset["axes"]),
        "controller_family": asset.get("controller_family", ""),
        "generation": asset.get("generation", ""),
        "year_introduced": int(asset["year_introduced"]),
        "year_discontinued": disc,
        "secondary_market_liquidity": asset.get("secondary_market_liquidity", ""),
        "typical_applications": [a for a in str(asset.get("typical_applications", "")).split("|") if a],
    }

    return {
        "deal_id": "deal_" + uuid.uuid4().hex[:8],
        "inputs": deal,
        "asset_profile": asset_profile,
        "valuation": _clean_internal(valuation),
        "ltv": _clean_internal(ltv),
        "recovery": recovery,
        "risk_flags": risk_flags,
        "disclaimer": DISCLAIMER,
    }
