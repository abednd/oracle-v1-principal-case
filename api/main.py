"""
OPTIONAL — FastAPI wrapper over the SAME core logic.

Proves the API surface is real and runnable. NOT on the demo critical path: the
Streamlit JSON view already shows the contract. If this layer has any issue,
delete it and nothing downstream changes.

Run:  uvicorn api.main:app --reload --port 8000   ->   http://localhost:8000/docs
"""
import os
import sys
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from oracle.pack import underwriting_pack
from oracle import data_access, valuation as val

app = FastAPI(title="Oracle v1 — Arm Underwriting Intelligence", version="0.1.0")


class DealRequest(BaseModel):
    asset_id: str
    year_of_manufacture: int
    operating_hours: float
    condition_grade: str
    location_country: str
    requested_financing_amount: float
    total_project_cost: float
    requested_term_months: int
    end_customer_industry: str = ""
    si_name: str = ""
    service_contract: bool = False
    includes_tooling: bool = False
    currency: str = "GBP"


@app.get("/assets")
def list_assets():
    return data_access.list_assets()


@app.get("/assets/{asset_id}")
def get_asset(asset_id: str):
    a = data_access.get_asset(asset_id)
    if a is None:
        raise HTTPException(404, f"Unknown asset_id: {asset_id}")
    return a


@app.get("/assets/{asset_id}/comparables")
def get_comparables(asset_id: str):
    df = data_access.get_comps_for_asset(asset_id)
    return df.to_dict("records")


@app.post("/valuations")
def post_valuation(req: DealRequest):
    asset = data_access.get_asset(req.asset_id)
    if asset is None:
        raise HTTPException(404, f"Unknown asset_id: {req.asset_id}")
    v = val.value_asset(asset, req.year_of_manufacture, req.operating_hours,
                        req.condition_grade, req.location_country, currency=req.currency)
    return {k: val_ for k, val_ in v.items() if not k.startswith("_")}


@app.post("/underwriting-pack")
def post_pack(req: DealRequest):
    try:
        return underwriting_pack(req.model_dump())
    except ValueError as e:
        raise HTTPException(400, str(e))
