from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..analytics.recommendation_engine import recommend_swp, recommend_sip
from ..core.database import get_session

router = APIRouter(prefix="/api/v1/recommendations", tags=["recommendations"])


class RecommendationFund(BaseModel):
    scheme_code: int
    scheme_name: str
    sub_category: str | None = None
    category_group: str | None = None
    composite_score: float | None = None
    rolling_return_3y_avg: float | None = None
    rolling_return_positive_pct: float | None = None
    risk_level: str | None = None
    aum_cr: float | None = None
    expense_ratio: float | None = None
    rolling_return_5y_avg: float | None = None
    rec_score: float | None = None


class RecommendationsResponse(BaseModel):
    funds: list[RecommendationFund]


@router.get("/swp", response_model=RecommendationsResponse)
async def get_swp_recommendations(
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_session),
):
    funds = await recommend_swp(db, limit=limit)
    return RecommendationsResponse(funds=[RecommendationFund(**f) for f in funds])


@router.get("/sip", response_model=RecommendationsResponse)
async def get_sip_recommendations(
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_session),
):
    funds = await recommend_sip(db, limit=limit)
    return RecommendationsResponse(funds=[RecommendationFund(**f) for f in funds])
