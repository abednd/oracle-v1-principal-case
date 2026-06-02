# Oracle v1 — Robotic Arm Underwriting Intelligence Pack

**Live demo:** _<paste your Streamlit Cloud URL here after deploy>_

A production-shaped prototype for Cenotian's SMG case. An internal underwriter
inputs a robotic-arm-backed deal and gets a lightweight underwriting pack:
asset profile, comparable market observations, a confidence-scored valuation,
a recommended LTV with a **go / review / reject** call, a base/stress recovery
view, and risk flags — all available as a JSON/API payload.

**It is not** a robot database, a dashboard, or a full credit platform. It proves
four things the case asks for: **data schema, valuation logic, user-flow logic,
and an API surface** — and it visibly **changes an underwriting decision** when a
deal input changes.

---

## What's real vs mock

- **Real:** specs for 19 industrial arm models (FANUC, ABB, KUKA, Yaskawa,
  Universal Robots) — payload, reach, axes, controller, intro year.
- **Synthetic:** all market transactions/comps, generated around the real spine
  with class-appropriate retention and deliberately uneven comp depth (so the
  confidence score is meaningful).
- **Production-shaped:** the schema, the comp-based valuation method, the
  confidence scoring, the LTV/recovery logic, and the API contract. Swap the
  synthetic comp table for a real transaction feed and the same logic runs.

---

## Run

```bash
pip install -r requirements.txt

# 1) (re)generate synthetic comps around the real spine
python scripts/generate_comps.py

# 2) the demo UI
streamlit run app.py

# 3) fallback / saved JSON (also prints the GO -> REJECT flip in the terminal)
python demo.py            # print summaries
python demo.py --save     # rewrite saved/baseline_pack.json + stressed_pack.json

# 4) tests — the demo-critical decision-flip + monotonicity checks
python tests/test_decision_change.py

# OPTIONAL — build a DuckDB file for the live SQL beat
python scripts/build_db.py

# OPTIONAL — the API surface (same logic as the UI)
uvicorn api.main:app --port 8000      # then open http://localhost:8000/docs
```

---

## The demo (≈3 minutes)

1. **Baseline.** FANUC R-2000iC/210F, MY2021, 12,000 hrs, good, UK; financing
   £40k, term 48mo. → FMV **£68,500** (high confidence, 7 comps), recommended
   LTV 59% vs requested 58% → **GO**, stress recovery covers financing, no flags.
2. **Walk the pack.** Asset profile → the comps it used → valuation + the
   adjustments applied → LTV → recovery (base £60.5k / stress £40.5k) → flags.
3. **The wow moment — change one input.** Push operating hours 12,000 → 45,000
   and regenerate. FMV falls to £56k, requested LTV jumps to 71%, decision flips
   **GO → REJECT**, and `high_hours` + `stress_recovery_shortfall` fire.
   *(For a softer GO → REVIEW step, use ~31,000 hours instead; or switch the
   location to a thin market like BR for a confidence-driven flip.)*
4. **Show the foundation.** Toggle **"Show as JSON / API payload"** — the same
   pack as a clean `POST /underwriting-pack` response. *"This is what Quone
   consumes, where Bubble Boy's telemetry and Newman's data would land. The UI is
   throwaway; this surface is the product."*
5. **Close.** *"v1 proves the schema, the valuation and recovery logic, the user
   flow, and the API. The mission from here is making the comps real and getting
   it in front of underwriters on live deals."*

**If challenged on valuation credibility:** *"The transactions are synthetic — I'm
not claiming the numbers are accurate today. I'm claiming the method is sound and
inspectable: comp-based with explicit adjustments you can see, and a confidence
score that's honest about thin data — watch it drop on a 2-comp model. Point it
at a real feed and the same logic produces real numbers."* (Open `params.py` for
the constants, or the comps table for the inputs.)

---

## Architecture (the risk firewall)

```
Streamlit (app.py)  ─┐
FastAPI (optional)  ─┼─►  oracle/  (PURE LOGIC CORE)  ◄─ params.py (all constants)
demo.py / tests     ─┘         │
                               ▼
                       data_access.py  (DuckDB-over-CSV → pandas fallback)
                               │
                          data/*.csv   (real specs + synthetic comps)
```

`oracle/pack.py:underwriting_pack(deal) -> dict` is the single entry point. The
UI, the API, `demo.py`, and the tests all call it. The core imports no
framework, so if any outer layer breaks, the decision still computes — and the
saved JSON payloads prove the decision change even with nothing running.

### Files
- `oracle/params.py` — every calibratable constant (curves, multipliers, LTV table, haircuts)
- `oracle/schema.py` — input/output dataclasses = the JSON/API contract
- `oracle/data_access.py` — load assets + comps (DuckDB, pandas fallback)
- `oracle/valuation.py` — comp-based FMV + adjustments + confidence
- `oracle/ltv.py` — LTV ceiling/deductions/decision
- `oracle/recovery.py` — base/stress recovery, time-to-sell, path
- `oracle/flags.py` — risk-flag rules
- `oracle/pack.py` — **the entry point**
- `app.py` — Streamlit UI · `api/main.py` — optional FastAPI
- `demo.py` — fallback demo + saved-JSON generator
- `data/` — `assets_seed.csv` (real), `comps_seed.csv` (synthetic), `schema.sql`
- `saved/` — `baseline_pack.json`, `stressed_pack.json`
- `tests/` — decision-flip + monotonicity

### Scope (deliberately excluded)
No SI/credit scoring · no portfolio dashboard · no real scraping · no ML ·
no full automation stack (arms only) · no auth · no FX engine · no UI polish.

---

## Deploy (Streamlit Community Cloud)

This repo is deploy-ready. To publish a shareable link:

1. Push this folder to a public GitHub repo.
2. Go to https://share.streamlit.io → **New app** → pick the repo/branch.
3. Set **Main file path** to `app.py`. Deploy.

Streamlit Cloud reads `requirements.txt` (core deps only), `runtime.txt`
(Python 3.12), and `.streamlit/config.toml` (the light Cenotian theme). The
synthetic comps are committed; if ever missing, the app regenerates them on
first run (deterministic, seed=42). No secrets, no database server, no setup.
