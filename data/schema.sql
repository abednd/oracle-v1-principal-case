-- Oracle v1 — schema (production-shaped). DuckDB/SQLite compatible.
-- The DB is the schema-of-record and powers the optional live SQL beat.
-- The compute path reads DataFrames and does NOT hard-depend on this DB.

CREATE TABLE IF NOT EXISTS assets (
    asset_id                    TEXT PRIMARY KEY,
    manufacturer                TEXT NOT NULL,
    model                       TEXT NOT NULL,
    series                      TEXT,
    arm_class                   TEXT,        -- small | medium | heavy | cobot
    payload_kg                  DOUBLE,
    reach_mm                    DOUBLE,
    axes                        INTEGER,
    controller_family           TEXT,
    generation                  TEXT,
    year_introduced             INTEGER,
    year_discontinued           INTEGER,     -- nullable
    msrp_new_usd                DOUBLE,
    typical_applications        TEXT,        -- pipe-delimited
    secondary_market_liquidity  TEXT         -- high | medium | low | thin
);

CREATE TABLE IF NOT EXISTS market_observations (
    obs_id              TEXT PRIMARY KEY,
    asset_id            TEXT REFERENCES assets(asset_id),
    observed_price      DOUBLE,
    currency            TEXT,
    observation_date    DATE,
    condition_grade     TEXT,                -- excellent | good | fair | poor
    operating_hours     DOUBLE,              -- nullable
    age_years           DOUBLE,
    source_type         TEXT,                -- dealer_listing | auction_result | broker_quote | oem_refurb
    source_name         TEXT,
    location_country    TEXT,
    includes_tooling    BOOLEAN,
    includes_controller BOOLEAN,
    reliability_weight  DOUBLE               -- 0..1 trust weight
);

-- Output tables (written by the engine; shown here to document the contract).
CREATE TABLE IF NOT EXISTS deals (
    deal_id                     TEXT PRIMARY KEY,
    si_name                     TEXT,
    end_customer_industry       TEXT,
    location_country            TEXT,
    total_project_cost          DOUBLE,
    requested_financing_amount  DOUBLE,
    requested_term_months       INTEGER,
    currency                    TEXT,
    service_contract            BOOLEAN
);

CREATE TABLE IF NOT EXISTS valuations (
    valuation_id        TEXT PRIMARY KEY,
    deal_id             TEXT REFERENCES deals(deal_id),
    asset_id            TEXT REFERENCES assets(asset_id),
    fmv_low             DOUBLE,
    fmv_central         DOUBLE,
    fmv_high            DOUBLE,
    currency            TEXT,
    confidence_score    INTEGER,
    confidence_band     TEXT,
    comp_count          INTEGER,
    method              TEXT                 -- comp_based | curve_fallback
);

CREATE TABLE IF NOT EXISTS ltv_recommendations (
    ltv_id              TEXT PRIMARY KEY,
    valuation_id        TEXT REFERENCES valuations(valuation_id),
    recommended_ltv_pct DOUBLE,
    max_ltv_pct         DOUBLE,
    requested_ltv_pct   DOUBLE,
    advance_recommended DOUBLE,
    decision            TEXT,                -- go | review | reject
    rationale           TEXT
);

CREATE TABLE IF NOT EXISTS recovery_assumptions (
    recovery_id                 TEXT PRIMARY KEY,
    valuation_id                TEXT REFERENCES valuations(valuation_id),
    base_recovery_value         DOUBLE,
    stress_recovery_value       DOUBLE,
    base_haircut_pct            DOUBLE,
    stress_haircut_pct          DOUBLE,
    time_to_sell_months_base    DOUBLE,
    time_to_sell_months_stress  DOUBLE,
    preferred_path              TEXT,        -- redeployment | liquidation
    recovery_confidence         TEXT
);

CREATE TABLE IF NOT EXISTS risk_flags (
    flag_id      TEXT PRIMARY KEY,
    deal_id      TEXT REFERENCES deals(deal_id),
    flag_type    TEXT,
    severity     TEXT,                       -- info | caution | warning
    message      TEXT
);
