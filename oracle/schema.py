"""
Oracle v1 — the input/output contract.

These dataclasses ARE the JSON/API surface. pack.py returns dicts derived from
them; Streamlit renders them; the optional FastAPI layer serialises them; the
tests assert against them. One source of truth for the shape of an underwriting
pack.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional


# ----------------------------- INPUT -----------------------------
@dataclass
class DealInput:
    """Everything an underwriter enters to run a deal."""
    asset_id: str
    year_of_manufacture: int
    operating_hours: float
    condition_grade: str            # excellent | good | fair | poor
    location_country: str           # ISO-2, e.g. "GB"
    requested_financing_amount: float
    total_project_cost: float
    requested_term_months: int
    # non-asset context — drives FLAGS ONLY, never valuation (kept out of scope)
    si_name: str = ""
    end_customer_industry: str = ""
    service_contract: bool = False
    includes_tooling: bool = False
    currency: str = "GBP"

    def to_dict(self) -> dict:
        return asdict(self)


# ----------------------------- OUTPUT SUB-OBJECTS -----------------------------
@dataclass
class AssetProfile:
    asset_id: str
    manufacturer: str
    model: str
    series: str
    arm_class: str
    payload_kg: float
    reach_mm: float
    axes: int
    controller_family: str
    generation: str
    year_introduced: int
    year_discontinued: Optional[int]
    secondary_market_liquidity: str
    typical_applications: list


@dataclass
class Comp:
    obs_id: str
    observed_price: float
    currency: str
    observation_date: str
    condition_grade: str
    operating_hours: Optional[float]
    age_years: float
    source_type: str
    source_name: str
    location_country: str


@dataclass
class Valuation:
    fmv_low: float
    fmv_central: float
    fmv_high: float
    currency: str
    confidence_score: int
    confidence_band: str
    comp_count: int
    method: str                     # comp_based | curve_fallback
    adjustments: dict               # {age, condition, hours, geography, generation}
    comps_used: list = field(default_factory=list)


@dataclass
class LTVRecommendation:
    recommended_ltv_pct: float
    max_ltv_pct: float
    requested_ltv_pct: float
    advance_recommended: float
    decision: str                   # go | review | reject
    rationale: str


@dataclass
class Recovery:
    base_recovery_value: float
    stress_recovery_value: float
    base_haircut_pct: float
    stress_haircut_pct: float
    time_to_sell_months_base: float
    time_to_sell_months_stress: float
    preferred_path: str             # redeployment | liquidation
    recovery_confidence: str
    stress_covers_financing: bool


@dataclass
class RiskFlag:
    flag_type: str
    severity: str                   # info | caution | warning
    message: str


# ----------------------------- TOP-LEVEL PACK -----------------------------
@dataclass
class UnderwritingPack:
    deal_id: str
    inputs: dict
    asset_profile: AssetProfile
    valuation: Valuation
    ltv: LTVRecommendation
    recovery: Recovery
    risk_flags: list
    disclaimer: str = (
        "Asset specs are real; market transactions are synthetic for this case. "
        "Schema, valuation/recovery logic, and the API surface are production-shaped."
    )

    def to_dict(self) -> dict:
        return asdict(self)
