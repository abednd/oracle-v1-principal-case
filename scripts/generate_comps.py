"""
Generate synthetic market observations (comps) around the REAL asset spine.

Design goals (believability levers, in priority order):
  1. Anchor each comp to its model's real new price x class-appropriate retention,
     so heavy arms hold value and cobots fall faster.
  2. Deliberately uneven comp DEPTH across models, so the confidence score is
     visibly meaningful (some models richly comped, some thin).
  3. Realistic source mix (dealer listings sit above auction results).
  4. Plausible geography spread (most comps in mature markets).

Output: data/comps_seed.csv  (transactions are SYNTHETIC; specs are real.)
"""
import csv
import os
import random
from datetime import date, timedelta

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from oracle import params

random.seed(42)  # deterministic build

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, "data", "assets_seed.csv")
OUT = os.path.join(ROOT, "data", "comps_seed.csv")

USD_GBP = 0.79  # fixed demo rate; specs list USD, comps shown in GBP

# How many comps per model — deliberately uneven (thin models expose confidence).
# Keyed by asset_id suffix patterns; default applies otherwise.
DEPTH_OVERRIDES = {
    "fanuc_r2000ic_210f": 7,   # the baseline demo arm — medium-rich
    "yaskawa_gp180": 2,        # deliberately thin
    "yaskawa_hc10": 2,         # thin cobot
    "ur_ur16e": 3,
    "kuka_kr60_r2100": 3,
}
DEPTH_BY_LIQUIDITY = {"high": 9, "medium": 5, "low": 3, "thin": 2}

SOURCE_MIX = [
    ("dealer_listing", "RobotWorx", 1.00),
    ("dealer_listing", "EU Robots", 0.98),
    ("broker_quote", "IRS Robotics", 0.97),
    ("auction_result", "Surplus Auctions", 0.88),
    ("oem_refurb", "OEM Certified", 1.08),
]
SOURCE_RELIABILITY = {
    "dealer_listing": 0.85,
    "broker_quote": 0.75,
    "auction_result": 0.70,
    "oem_refurb": 0.90,
}
COND_FACTORS = params.CONDITION_MULT
GEO_POOL = ["DE", "US", "GB", "IT", "FR", "JP", "ES", "PL", "MX", "BR"]
GEO_WEIGHTS = [22, 20, 14, 9, 8, 8, 6, 5, 4, 4]  # mature markets dominate


def retention_for_age(age, arm_class):
    base = params.AGE_RETENTION.get(min(age, 12), params.AGE_RETENTION_FLOOR)
    if age > 12:
        base = params.AGE_RETENTION_FLOOR
    mult = params.CLASS_RETENTION_MULT.get(arm_class, 1.0)
    return base * mult


def load_assets():
    with open(ASSETS, newline="") as f:
        return list(csv.DictReader(f))


def gen():
    assets = load_assets()
    rows = []
    obs_n = 0
    today = date(2026, 5, 1)
    for a in assets:
        aid = a["asset_id"]
        arm_class = a["arm_class"]
        liquidity = a["secondary_market_liquidity"]
        new_usd = float(a["msrp_new_usd"])
        new_gbp = new_usd * USD_GBP
        intro = int(a["year_introduced"])
        depth = DEPTH_OVERRIDES.get(aid, DEPTH_BY_LIQUIDITY.get(liquidity, 4))

        for _ in range(depth):
            # pick a plausible manufacture year and resulting age
            man_year = random.randint(max(intro, 2014), 2023)
            age = max(0, 2026 - man_year)
            cond = random.choices(
                ["excellent", "good", "fair", "poor"], weights=[15, 50, 28, 7]
            )[0]
            hours = random.choice([None, None, 4000, 9000, 14000, 22000, 31000, 45000])
            src_type, src_name, src_price_mult = random.choices(
                SOURCE_MIX, weights=[30, 18, 20, 22, 10]
            )[0]
            geo = random.choices(GEO_POOL, weights=GEO_WEIGHTS)[0]

            ret = retention_for_age(age, arm_class)
            cond_f = COND_FACTORS[cond]
            # hours effect on the *observed* price (mild; full model lives in valuation.py)
            hours_f = 1.0 if not hours else max(0.82, 1.0 - (hours / 200_000))
            noise = random.uniform(0.90, 1.12)  # market dispersion
            price = new_gbp * ret * cond_f * hours_f * src_price_mult * noise
            price = round(price / 500) * 500  # round to nearest £500

            days_ago = random.randint(20, 760)  # within ~25 months
            obs_date = today - timedelta(days=days_ago)

            obs_n += 1
            rows.append({
                "obs_id": f"obs_{obs_n:04d}",
                "asset_id": aid,
                "observed_price": int(price),
                "currency": "GBP",
                "observation_date": obs_date.isoformat(),
                "condition_grade": cond,
                "operating_hours": "" if hours is None else int(hours),
                "age_years": age,
                "source_type": src_type,
                "source_name": src_name,
                "location_country": geo,
                "includes_tooling": random.choice([True, False]),
                "includes_controller": True,
                "reliability_weight": SOURCE_RELIABILITY[src_type],
            })

    fields = list(rows[0].keys())
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} synthetic comps across {len(assets)} models -> {OUT}")


if __name__ == "__main__":
    gen()
