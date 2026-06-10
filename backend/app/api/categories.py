from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_session
from ..models import Fund
from ..schemas.analytics import CategoryResponse, CategoryFundSummary
from ..schemas.fund import FundResponse
from ..services.fund_service import FundService

router = APIRouter(prefix="/api/v1/categories", tags=["categories"])


@router.get("")
async def list_categories(db: AsyncSession = Depends(get_session)):
    stmt = (
        select(Fund.scheme_category)
        .distinct()
        .where(Fund.scheme_category.isnot(None))
        .order_by(Fund.scheme_category)
    )
    result = await db.execute(stmt)
    categories = [r[0] for r in result.all()]
    return {"categories": categories, "total": len(categories)}


@router.get("/{category_name}", response_model=CategoryResponse)
async def get_category(
    category_name: str,
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_session),
):
    service = FundService(db)
    avg = await service.get_category_avg_returns(category_name)

    funds = await service.get_funds_by_category(category_name, limit=limit)
    top_funds = []
    for f in funds:
        top_funds.append(
            CategoryFundSummary(
                scheme_code=f.scheme_code,
                scheme_name=f.scheme_name,
                nav=f.nav,
                return_1y=f.return_1y,
                cagr_3y=f.return_3y,
                cagr_5y=f.return_5y,
                expense_ratio=f.expense_ratio,
                aum_cr=f.aum_cr,
                risk_level=f.risk_level,
            )
        )

    return CategoryResponse(
        category=avg["category"],
        total_funds=avg["total_funds"],
        avg_return_1y=avg["avg_return_1y"],
        avg_cagr_3y=avg["avg_cagr_3y"],
        avg_cagr_5y=avg["avg_cagr_5y"],
        top_funds=top_funds,
    )
