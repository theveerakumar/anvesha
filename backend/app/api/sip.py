from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..analytics.sip import compute_sip, compute_sip_stress_test, compute_xirr

router = APIRouter(prefix="/api/v1/sip", tags=["sip"])


class SIPRequest(BaseModel):
    monthly_amount: float
    duration_years: int
    expected_return: float = 12.0


class SIPStressTestRequest(BaseModel):
    monthly_amount: float
    duration_years: int


class XIRRRequest(BaseModel):
    cash_flows: list[dict]


@router.post("/calculate")
async def calculate_sip(req: SIPRequest):
    if req.monthly_amount <= 0:
        raise HTTPException(status_code=400, detail="Monthly amount must be positive")
    if req.duration_years <= 0 or req.duration_years > 50:
        raise HTTPException(
            status_code=400, detail="Duration must be between 1 and 50 years"
        )
    result = compute_sip(req.monthly_amount, req.duration_years, req.expected_return)
    return {"input": req.model_dump(), "result": result}


@router.post("/stress-test")
async def sip_stress_test(req: SIPStressTestRequest):
    if req.monthly_amount <= 0:
        raise HTTPException(status_code=400, detail="Monthly amount must be positive")
    if req.duration_years <= 0 or req.duration_years > 50:
        raise HTTPException(
            status_code=400, detail="Duration must be between 1 and 50 years"
        )
    result = compute_sip_stress_test(req.monthly_amount, req.duration_years)
    return {"input": req.model_dump(), "result": result}


@router.post("/xirr")
async def calculate_xirr(req: XIRRRequest):
    from datetime import date

    cash_flows = []
    for cf in req.cash_flows:
        try:
            d = date.fromisoformat(cf.get("date", ""))
            amount = float(cf.get("amount", 0))
            cash_flows.append((d, amount))
        except (ValueError, KeyError):
            continue
    if not cash_flows:
        raise HTTPException(status_code=400, detail="No valid cash flows provided")
    xirr = compute_xirr(cash_flows)
    return {"xirr": round(xirr, 2)}
