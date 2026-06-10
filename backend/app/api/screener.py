from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..core.database import get_session
from ..models import Fund
from ..schemas.fund import FundResponse, FundSearchResult
from ..services.fund_service import FundService

router = APIRouter(prefix="/api/v1/screener", tags=["screener"])


@router.get("/funds", response_model=FundSearchResult)
async def screen_funds(
    q: str | None = Query(None, description="Search query"),
    category: str | None = Query(None, description="Category filter"),
    min_return_1y: float | None = Query(None, description="Minimum 1Y return (%)"),
    max_return_1y: float | None = Query(None, description="Maximum 1Y return (%)"),
    min_return_3y: float | None = Query(None, description="Minimum 3Y CAGR (%)"),
    max_return_3y: float | None = Query(None, description="Maximum 3Y CAGR (%)"),
    min_return_5y: float | None = Query(None, description="Minimum 5Y CAGR (%)"),
    max_expense_ratio: float | None = Query(
        None, description="Maximum expense ratio (%)"
    ),
    min_aum_cr: float | None = Query(None, description="Minimum AUM (Cr)"),
    risk_level: str | None = Query(None, description="Risk level filter"),
    sort_by: str = Query("return_1y", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_session),
):
    service = FundService(db)
    conditions = []

    if q:
        conditions.append(Fund.scheme_name.ilike(f"%{q}%"))
    if category:
        conditions.append(Fund.scheme_category.ilike(f"%{category}%"))
    if min_return_1y is not None:
        conditions.append(Fund.return_1y >= min_return_1y)
    if max_return_1y is not None:
        conditions.append(Fund.return_1y <= max_return_1y)
    if min_return_3y is not None:
        conditions.append(Fund.return_3y >= min_return_3y)
    if max_return_3y is not None:
        conditions.append(Fund.return_3y <= max_return_3y)
    if min_return_5y is not None:
        conditions.append(Fund.return_5y >= min_return_5y)
    if max_expense_ratio is not None:
        conditions.append(Fund.expense_ratio <= max_expense_ratio)
    if min_aum_cr is not None:
        conditions.append(Fund.aum_cr >= min_aum_cr)
    if risk_level:
        conditions.append(Fund.risk_level.ilike(f"%{risk_level}%"))

    order_col = getattr(Fund, sort_by, Fund.return_1y)
    order = order_col.desc() if sort_order == "desc" else order_col.asc()

    stmt = select(Fund).where(and_(*conditions) if conditions else True).order_by(order)
    count_stmt = select(Fund.id).where(and_(*conditions) if conditions else True)

    offset = (page - 1) * page_size
    total = len((await db.execute(count_stmt)).scalars().all())
    stmt = stmt.offset(offset).limit(page_size)
    result = await db.execute(stmt)
    funds = result.scalars().all()

    return FundSearchResult(
        total=total,
        page=page,
        page_size=page_size,
        results=[FundResponse.model_validate(f) for f in funds],
    )
