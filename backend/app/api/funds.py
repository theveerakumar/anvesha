from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_session
from ..schemas.analytics import (
    CategoryResponse,
    CategoryFundSummary,
    CompareResponse,
    CompareFundRow,
    FundDetailResponse,
    NAVHistoryResponse,
    NAVPoint,
    OverlapResponse,
    RatingResponse,
    RecommendationResponse,
    ReturnsResponse,
    RiskMetricsResponse,
)
from ..schemas.fund import FundListResponse, FundResponse, FundSearchResult
from ..services.fund_service import FundService

router = APIRouter(prefix="/api/v1/funds", tags=["funds"])


@router.get("/search", response_model=FundSearchResult)
async def search_funds(
    q: str = Query(..., min_length=1, description="Search query"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_session),
):
    service = FundService(db)
    results, total = await service.search_funds(q, page=page, page_size=page_size)
    return FundSearchResult(
        total=total, page=page, page_size=page_size, results=results
    )


@router.get("/{scheme_code}", response_model=FundResponse)
async def get_fund(
    scheme_code: int,
    db: AsyncSession = Depends(get_session),
):
    service = FundService(db)
    fund = await service.get_fund_by_scheme_code(scheme_code)
    if not fund:
        raise HTTPException(status_code=404, detail="Fund not found")
    return fund


@router.get("", response_model=FundListResponse)
async def list_funds(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_session),
):
    service = FundService(db)
    funds, total = await service.get_funds_list(page=page, page_size=page_size)
    return FundListResponse(total=total, page=page, page_size=page_size, funds=funds)


@router.get("/{scheme_code}/returns", response_model=ReturnsResponse)
async def get_fund_returns(
    scheme_code: int,
    db: AsyncSession = Depends(get_session),
):
    service = FundService(db)
    data = await service.get_fund_returns(scheme_code)
    if not data:
        raise HTTPException(
            status_code=404, detail="Fund not found or no NAV history available"
        )
    return ReturnsResponse(**data)


@router.get("/{scheme_code}/risk", response_model=RiskMetricsResponse)
async def get_fund_risk(
    scheme_code: int,
    db: AsyncSession = Depends(get_session),
):
    service = FundService(db)
    data = await service.get_fund_risk_metrics(scheme_code)
    if not data:
        raise HTTPException(
            status_code=404, detail="Fund not found or no NAV history available"
        )
    return RiskMetricsResponse(**data)


@router.get("/{scheme_code}/rating", response_model=RatingResponse)
async def get_fund_rating(
    scheme_code: int,
    db: AsyncSession = Depends(get_session),
):
    service = FundService(db)
    data = await service.get_fund_rating(scheme_code)
    if not data:
        raise HTTPException(
            status_code=404, detail="Fund not found or insufficient data"
        )
    return RatingResponse(**data)


@router.get("/{scheme_code}/recommendation", response_model=RecommendationResponse)
async def get_fund_recommendation(
    scheme_code: int,
    db: AsyncSession = Depends(get_session),
):
    service = FundService(db)
    data = await service.get_fund_recommendation(scheme_code)
    if not data:
        raise HTTPException(
            status_code=404, detail="Fund not found or insufficient data"
        )
    return RecommendationResponse(**data)


@router.get("/{scheme_code}/nav-history", response_model=NAVHistoryResponse)
async def get_fund_nav_history(
    scheme_code: int,
    db: AsyncSession = Depends(get_session),
):
    service = FundService(db)
    fund, nav_history = await service.get_fund_nav_history(scheme_code)
    if not fund:
        raise HTTPException(status_code=404, detail="Fund not found")

    points = [NAVPoint(date=str(d), nav=v) for d, v in nav_history]
    return NAVHistoryResponse(
        scheme_code=fund.scheme_code,
        scheme_name=fund.scheme_name,
        nav_history=points,
    )


@router.get("/{scheme_code}/detail", response_model=FundDetailResponse)
async def get_fund_detail_full(
    scheme_code: int,
    db: AsyncSession = Depends(get_session),
):
    service = FundService(db)
    data = await service.get_fund_detail_full(scheme_code)
    if not data:
        raise HTTPException(status_code=404, detail="Fund not found")
    return FundDetailResponse(**data)


@router.post("/compare", response_model=CompareResponse)
async def compare_funds(
    scheme_codes: list[int],
    db: AsyncSession = Depends(get_session),
):
    if len(scheme_codes) < 2:
        raise HTTPException(status_code=400, detail="At least 2 scheme codes required")
    if len(scheme_codes) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 scheme codes allowed")
    service = FundService(db)
    data = await service.compare_funds(scheme_codes)
    return CompareResponse(**data)


@router.get("/overlap", response_model=OverlapResponse)
async def fund_overlap(
    a: int = Query(..., description="First scheme code"),
    b: int = Query(..., description="Second scheme code"),
    db: AsyncSession = Depends(get_session),
):
    service = FundService(db)
    data = await service.compute_overlap(a, b)
    if not data:
        raise HTTPException(status_code=404, detail="One or both funds not found")
    return OverlapResponse(**data)
