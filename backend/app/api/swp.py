from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..analytics.swp import (
    compute_swp,
    compute_swp_longevity,
    compute_swp_max_withdrawal,
    compute_swp_stress_test,
)

router = APIRouter(prefix="/api/v1/swp", tags=["swp"])


class SWPCalculateRequest(BaseModel):
    corpus: float
    monthly_withdrawal: float
    expected_return: float = 12.0
    duration_years: int = 10


class SWPLongevityRequest(BaseModel):
    corpus: float
    monthly_withdrawal: float
    expected_return: float = 12.0


class SWPMaxWithdrawalRequest(BaseModel):
    corpus: float
    duration_years: int
    expected_return: float = 12.0


class SWPStressTestRequest(BaseModel):
    corpus: float
    monthly_withdrawal: float
    duration_years: int = 10


@router.post("/calculate")
async def calculate_swp(req: SWPCalculateRequest):
    if req.corpus <= 0:
        raise HTTPException(status_code=400, detail="Corpus must be positive")
    if req.monthly_withdrawal <= 0:
        raise HTTPException(
            status_code=400, detail="Monthly withdrawal must be positive"
        )
    if req.monthly_withdrawal > req.corpus:
        raise HTTPException(status_code=400, detail="Monthly withdrawal exceeds corpus")
    if req.duration_years <= 0 or req.duration_years > 100:
        raise HTTPException(
            status_code=400, detail="Duration must be between 1 and 100 years"
        )
    result = compute_swp(
        req.corpus, req.monthly_withdrawal, req.expected_return, req.duration_years
    )
    return {"input": req.model_dump(), "result": result}


@router.post("/longevity")
async def longevity_swp(req: SWPLongevityRequest):
    if req.corpus <= 0:
        raise HTTPException(status_code=400, detail="Corpus must be positive")
    if req.monthly_withdrawal <= 0:
        raise HTTPException(
            status_code=400, detail="Monthly withdrawal must be positive"
        )
    if req.monthly_withdrawal > req.corpus:
        raise HTTPException(status_code=400, detail="Monthly withdrawal exceeds corpus")
    result = compute_swp_longevity(
        req.corpus, req.monthly_withdrawal, req.expected_return
    )
    return {"input": req.model_dump(), "result": result}


@router.post("/max-withdrawal")
async def max_withdrawal_swp(req: SWPMaxWithdrawalRequest):
    if req.corpus <= 0:
        raise HTTPException(status_code=400, detail="Corpus must be positive")
    if req.duration_years <= 0 or req.duration_years > 100:
        raise HTTPException(
            status_code=400, detail="Duration must be between 1 and 100 years"
        )
    result = compute_swp_max_withdrawal(
        req.corpus, req.duration_years, req.expected_return
    )
    return {"input": req.model_dump(), "result": result}


@router.post("/stress-test")
async def stress_test_swp(req: SWPStressTestRequest):
    if req.corpus <= 0:
        raise HTTPException(status_code=400, detail="Corpus must be positive")
    if req.monthly_withdrawal <= 0:
        raise HTTPException(
            status_code=400, detail="Monthly withdrawal must be positive"
        )
    if req.duration_years <= 0 or req.duration_years > 100:
        raise HTTPException(
            status_code=400, detail="Duration must be between 1 and 100 years"
        )
    result = compute_swp_stress_test(
        req.corpus, req.monthly_withdrawal, req.duration_years
    )
    return {"input": req.model_dump(), "result": result}
