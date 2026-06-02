"""
OPTIONAL — build a DuckDB file from the schema + seed CSVs.

Lets you show the schema as a real database and run a live comp query in the
demo. The compute path does NOT need this (it reads CSVs directly), so this is
purely for the "here's the schema / here's a SQL query" beat.

Usage:  python scripts/build_db.py   ->   data/oracle.duckdb
"""
import os
import duckdb

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DB = os.path.join(ROOT, "data", "oracle.duckdb")
ASSETS = os.path.join(ROOT, "data", "assets_seed.csv")
COMPS = os.path.join(ROOT, "data", "comps_seed.csv")

if os.path.exists(DB):
    os.remove(DB)

con = duckdb.connect(DB)
con.execute(f"CREATE TABLE assets AS SELECT * FROM read_csv_auto('{ASSETS}')")
con.execute(f"CREATE TABLE market_observations AS SELECT * FROM read_csv_auto('{COMPS}')")

n_assets = con.execute("SELECT count(*) FROM assets").fetchone()[0]
n_comps = con.execute("SELECT count(*) FROM market_observations").fetchone()[0]
print(f"built {DB}: {n_assets} assets, {n_comps} comps")

# demo query: comp depth + median price per model (what confidence scoring leans on)
print("\nExample query — comp depth & median price by model:")
rows = con.execute("""
    SELECT a.manufacturer, a.model, a.arm_class,
           count(m.obs_id) AS comps,
           CAST(median(m.observed_price) AS INTEGER) AS median_price
    FROM assets a
    LEFT JOIN market_observations m USING (asset_id)
    GROUP BY 1,2,3
    ORDER BY comps DESC
    LIMIT 8
""").fetchall()
for r in rows:
    print(f"  {r[0]:<16} {r[1]:<20} {r[2]:<7} comps={r[3]:<2} median=£{r[4]:,}")

con.close()
