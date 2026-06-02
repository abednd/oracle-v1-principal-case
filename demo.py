"""
demo.py — fallback demo + saved-JSON generator.

Runs the two canonical deals (baseline + stressed), prints a readable summary,
and writes saved/baseline_pack.json and saved/stressed_pack.json. If Streamlit
dies live, this proves the decision change straight from the terminal / files.

Usage:
    python demo.py            # print summaries
    python demo.py --save     # also (re)write the saved JSON payloads
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oracle.pack import underwriting_pack

HERE = os.path.dirname(os.path.abspath(__file__))
SAVED = os.path.join(HERE, "saved")

# ---- canonical demo deals --------------------------------------------------
BASELINE = dict(
    asset_id="fanuc_r2000ic_210f",
    year_of_manufacture=2021,
    operating_hours=12000,
    condition_grade="good",
    location_country="GB",
    requested_financing_amount=40000,
    total_project_cost=280000,
    requested_term_months=48,
    si_name="Northgate Automation",
    end_customer_industry="packaging",
    service_contract=True,
    includes_tooling=False,
    currency="GBP",
)

# Stressed = same deal, hours 12k -> 45k (the dramatic GO -> REJECT flip).
# For a softer GO -> REVIEW demo, set operating_hours=31000 instead.
STRESSED = dict(BASELINE, operating_hours=45000)


def summarise(tag, pack):
    v, l, r = pack["valuation"], pack["ltv"], pack["recovery"]
    print(f"\n================ {tag} ================")
    a = pack["asset_profile"]
    print(f"Asset: {a['manufacturer']} {a['model']} ({a['arm_class']}, {a['payload_kg']}kg/{a['reach_mm']}mm)")
    print(f"Inputs: MY{pack['inputs']['year_of_manufacture']}, "
          f"{pack['inputs']['operating_hours']:,}h, {pack['inputs']['condition_grade']}, "
          f"{pack['inputs']['location_country']}; financing GBP {pack['inputs']['requested_financing_amount']:,}")
    print(f"Valuation: GBP {v['fmv_central']:,}  (range {v['fmv_low']:,}-{v['fmv_high']:,})  "
          f"| confidence {v['confidence_score']} ({v['confidence_band']}) | {v['comp_count']} comps | {v['method']}")
    print(f"LTV: recommended {l['recommended_ltv_pct']}%  requested {l['requested_ltv_pct']}%  "
          f"max {l['max_ltv_pct']}%  ->  DECISION: {l['decision'].upper()}")
    print(f"Recovery: base GBP {r['base_recovery_value']:,}  stress GBP {r['stress_recovery_value']:,}  "
          f"| path {r['preferred_path']} | stress covers financing: {r['stress_covers_financing']}")
    flags = pack["risk_flags"]
    if flags:
        print("Flags:")
        for f in flags:
            print(f"   [{f['severity']:<7}] {f['flag_type']}: {f['message']}")
    else:
        print("Flags: none")


def main():
    base = underwriting_pack(BASELINE)
    stress = underwriting_pack(STRESSED)
    summarise("BASELINE", base)
    summarise("STRESSED (operating hours 12k -> 45k)", stress)

    print("\n---------------------------------------------")
    print(f"DECISION CHANGE:  {base['ltv']['decision'].upper()}  ->  {stress['ltv']['decision'].upper()}")
    print("---------------------------------------------")

    if "--save" in sys.argv:
        os.makedirs(SAVED, exist_ok=True)
        with open(os.path.join(SAVED, "baseline_pack.json"), "w") as f:
            json.dump(base, f, indent=2)
        with open(os.path.join(SAVED, "stressed_pack.json"), "w") as f:
            json.dump(stress, f, indent=2)
        print(f"\nsaved -> {SAVED}/baseline_pack.json, stressed_pack.json")


if __name__ == "__main__":
    main()
