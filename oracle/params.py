"""
Oracle v1 — calibratable parameters.

Every magic number in the valuation / LTV / recovery logic lives here so it is
easy to tune during rehearsal and easy to point at when challenged in the room.
All values are ILLUSTRATIVE defaults chosen to be plausible, not ground truth.
"""

# --- Age retention curve (fraction of new price retained, by age in years) ---
# Industrial arms are durable: a meaningful first-year drop, then a slow decline
# to a functional-value floor. Calibratable per class via CLASS_RETENTION_MULT.
AGE_RETENTION = {
    0: 1.00,
    1: 0.86,
    2: 0.78,
    3: 0.72,
    4: 0.66,
    5: 0.60,
    6: 0.55,
    7: 0.50,
    8: 0.45,
    9: 0.41,
    10: 0.37,
    11: 0.33,
    12: 0.30,  # floor applied for >=12
}
AGE_RETENTION_FLOOR = 0.28

# Class-level tilt on the retention curve.
# Heavy arms (workhorses) hold value; cobots fall faster (tech obsolescence).
CLASS_RETENTION_MULT = {
    "heavy": 1.05,
    "medium": 1.00,
    "small": 0.96,
    "cobot": 0.88,
}

# --- Condition multipliers (baseline = "good") ---
CONDITION_MULT = {
    "excellent": 1.10,
    "good": 1.00,
    "fair": 0.82,
    "poor": 0.62,
}

# --- Operating-hours penalty ---
# Negligible below FREE; linear-ish decline to FLOOR at HEAVY hours.
HOURS_FREE = 20_000          # no penalty below this
HOURS_REFERENCE = 60_000     # ~major-service / heavy-use reference
HOURS_MULT_AT_REFERENCE = 0.70
HOURS_MULT_FLOOR = 0.60
HOURS_FLAG_THRESHOLD = 40_000  # raise high_hours flag above this

# --- Geography / secondary-market liquidity tiers ---
# Tier A: mature dealer markets. Multiplier on value + base time-to-sell driver.
GEO_TIER = {
    # country_code: tier
    "US": "A", "DE": "A", "JP": "A", "GB": "A", "IT": "A", "FR": "A",
    "CN": "A", "KR": "A", "ES": "B", "PL": "B", "CZ": "B", "MX": "B",
    "BR": "C", "IN": "C", "ZA": "C", "AE": "C", "SA": "C",
}
GEO_DEFAULT_TIER = "B"
GEO_TIER_MULT = {"A": 1.00, "B": 0.92, "C": 0.80}

# --- Generation / controller obsolescence ---
OBSOLESCENCE_MULT = 0.90       # applied if model discontinued / controller superseded
OBSOLESCENCE_FLAG = True

# --- Confidence scoring (0-100) ---
CONF_START = 50
CONF_COMP_COUNT = {0: -25, 1: -10, 2: -10, 3: 10, 4: 10, 5: 10}  # >=6 -> +20
CONF_COMP_COUNT_HIGH = 20      # for comp_count >= 6
CONF_DISPERSION_TIGHT = 10     # coeff. of variation below DISP_TIGHT
CONF_DISPERSION_WIDE = -15     # coeff. of variation above DISP_WIDE
DISP_TIGHT = 0.12
DISP_WIDE = 0.30
CONF_RECENT_BONUS = 8          # any comp < 12 months
CONF_STALE_PENALTY = -10       # all comps > 36 months
CONF_MULTISOURCE_BONUS = 6     # >= 2 distinct source types
CONF_SINGLESOURCE_PENALTY = -8
CONF_LIQUID_BONUS = {"A": 6, "B": 0, "C": -10}

# Confidence band thresholds -> (band label, +/- range width fraction)
CONF_BANDS = [
    (75, "high", 0.10),
    (55, "medium-high", 0.15),
    (40, "medium", 0.22),
    (0,  "low", 0.35),
]

# --- LTV ceiling table: confidence band x geo tier ---
LTV_CEILING = {
    "high":        {"A": 70, "B": 64, "C": 56},
    "medium-high": {"A": 62, "B": 56, "C": 48},
    "medium":      {"A": 52, "B": 46, "C": 40},
    "low":         {"A": 42, "B": 38, "C": 32},
}

# LTV deductions (percentage points)
LTV_DEDUCT = {
    "high_hours": 5,
    "generation_obsolescence": 8,
    "thin_comps": 5,
    "end_use_specificity": 4,
    "long_term": 4,            # term > LONG_TERM_MONTHS
    "single_source_comps": 3,
}
LONG_TERM_MONTHS = 60

# Decision thresholds (percentage points of LTV)
DECISION_REVIEW_BAND = 8       # requested within this many pts above recommended -> REVIEW

# End-use specificity: industries whose tooling/config narrows redeployability
END_USE_SPECIFIC_INDUSTRIES = {"aerospace", "medical", "semiconductor", "food_grade"}

# --- Recovery ---
RECOVERY_BASE_HAIRCUT = {"redeployment": 0.12, "liquidation": 0.20}
RECOVERY_STRESS_HAIRCUT = {"redeployment": 0.35, "liquidation": 0.45}
RECOVERY_STRESS_TIER_C_EXTRA = 0.10  # extra stress haircut in thin geographies

# Time-to-sell (months) by liquidity, base case; stress ~= 2x capped
TIME_TO_SELL_BASE = {"high": 4, "medium": 6, "low": 9, "thin": 9}
TIME_TO_SELL_STRESS_MULT = 2.0
TIME_TO_SELL_STRESS_CAP = 18

# Recovery path preference: redeploy if liquid & broadly applicable
REDEPLOY_MIN_APPLICATIONS = 2
REDEPLOY_LIQUIDITY_OK = {"high", "medium"}

# Currency for the demo
DEFAULT_CURRENCY = "GBP"
