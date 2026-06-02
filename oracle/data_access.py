"""
Data access — loads the asset registry and comps into pandas DataFrames.

Risk firewall: tries DuckDB querying the CSVs directly (no import step, gives us
real SQL for the demo). On ANY failure it falls back to pandas.read_csv. The
compute layer always receives identical DataFrames, so the DB is never a hard
runtime dependency.
"""
import os
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS_CSV = os.path.join(ROOT, "data", "assets_seed.csv")
COMPS_CSV = os.path.join(ROOT, "data", "comps_seed.csv")

_cache = {}


def _ensure_comps():
    """Self-heal: if comps_seed.csv is missing (e.g. fresh clone), generate it.
    The generator is deterministic (seed=42), so output is identical every time."""
    if os.path.exists(COMPS_CSV):
        return
    gen_path = os.path.join(ROOT, "scripts", "generate_comps.py")
    if os.path.exists(gen_path):
        import runpy
        runpy.run_path(gen_path, run_name="__main__")


def _load_via_duckdb():
    import duckdb
    con = duckdb.connect()
    assets = con.execute(f"SELECT * FROM read_csv_auto('{ASSETS_CSV}')").df()
    comps = con.execute(f"SELECT * FROM read_csv_auto('{COMPS_CSV}')").df()
    con.close()
    return assets, comps, "duckdb"


def _load_via_pandas():
    assets = pd.read_csv(ASSETS_CSV)
    comps = pd.read_csv(COMPS_CSV)
    return assets, comps, "pandas"


def load_data(prefer_duckdb=True):
    """Return (assets_df, comps_df, backend_used). Cached after first call."""
    if _cache:
        return _cache["assets"], _cache["comps"], _cache["backend"]
    _ensure_comps()
    assets = comps = None
    backend = None
    if prefer_duckdb:
        try:
            assets, comps, backend = _load_via_duckdb()
        except Exception:
            assets = None
    if assets is None:
        assets, comps, backend = _load_via_pandas()

    # normalise types
    comps["operating_hours"] = pd.to_numeric(comps["operating_hours"], errors="coerce")
    comps["observation_date"] = pd.to_datetime(comps["observation_date"], errors="coerce")
    _cache.update(assets=assets, comps=comps, backend=backend)
    return assets, comps, backend


def get_asset(asset_id):
    assets, _, _ = load_data()
    row = assets[assets["asset_id"] == asset_id]
    if row.empty:
        return None
    return row.iloc[0].to_dict()


def get_comps_for_asset(asset_id):
    _, comps, _ = load_data()
    return comps[comps["asset_id"] == asset_id].copy()


def get_near_comps(asset, payload_tol=0.25, reach_tol=0.25):
    """Fallback comp set: same class + payload/reach within tolerance."""
    _, comps, _ = load_data()
    assets, _, _ = load_data()
    cls = asset["arm_class"]
    pay = float(asset["payload_kg"])
    reach = float(asset["reach_mm"])
    same_class_ids = assets[
        (assets["arm_class"] == cls)
        & (assets["payload_kg"].between(pay * (1 - payload_tol), pay * (1 + payload_tol)))
        & (assets["reach_mm"].between(reach * (1 - reach_tol), reach * (1 + reach_tol)))
    ]["asset_id"].tolist()
    return comps[comps["asset_id"].isin(same_class_ids)].copy()


def list_assets():
    assets, _, _ = load_data()
    return assets[["asset_id", "manufacturer", "model", "arm_class",
                   "payload_kg", "reach_mm"]].to_dict("records")


def all_comps():
    """Full comp table (joined with model name) for the Data-sources view."""
    assets, comps, _ = load_data()
    df = comps.merge(
        assets[["asset_id", "manufacturer", "model"]], on="asset_id", how="left"
    )
    df["model_name"] = df["manufacturer"].fillna("") + " " + df["model"].fillna("")
    cols = ["model_name", "observed_price", "currency", "observation_date",
            "condition_grade", "operating_hours", "age_years", "source_type",
            "source_name", "location_country", "reliability_weight"]
    out = df[cols].copy()
    out["observation_date"] = out["observation_date"].dt.date.astype(str)
    return out.sort_values(["model_name", "observation_date"], ascending=[True, False])


# How each source type is obtained — honest production framing (synthetic for the case).
SOURCE_LEGEND = [
    ("dealer_listing", "Used-robot dealer listings",
     "Asking prices published by used-robot dealers (e.g. RobotWorx, EU Robots). "
     "In production: scraped from dealer catalogues + periodic partner feeds. Most plentiful, list-price biased."),
    ("auction_result", "Auction / liquidation results",
     "Hammer prices from industrial auctions and liquidations. "
     "In production: scraped from auction houses + bid platforms. Lower, distressed signal — useful for stress recovery."),
    ("broker_quote", "Broker / reseller quotes",
     "Indicative quotes from equipment brokers. "
     "In production: collected via broker relationships / RFQs. Mid-market signal, less independent."),
    ("oem_refurb", "OEM certified refurbished",
     "Prices for OEM-refurbished units with warranty. "
     "In production: OEM refurb programmes + authorised channels. Upper bound, highest reliability."),
]
