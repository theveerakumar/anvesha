from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_session
from ..models import Fund

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])

TAB_GROUPS = [
    "all",
    "equity",
    "hybrid",
    "index",
    "gold_silver",
    "global",
    "debt",
    "solution",
    "other",
]


class TabInfo(BaseModel):
    key: str
    label: str
    count: int
    total_aum_cr: float | None = None


class SubCategoryInfo(BaseModel):
    key: str
    label: str
    count: int
    avg_composite: float | None = None


class FundRow(BaseModel):
    scheme_code: int
    scheme_name: str
    category_group: str | None = None
    sub_category: str | None = None
    scheme_category: str | None = None
    amc: str | None = None
    nav: float | None = None
    aum_cr: float | None = None
    expense_ratio: float | None = None
    return_1y: float | None = None
    rolling_return_3y_avg: float | None = None
    rolling_return_5y_avg: float | None = None
    rolling_return_positive_pct: float | None = None
    risk_level: str | None = None
    composite_score: float | None = None
    score_performance: float | None = None
    score_risk: float | None = None
    score_consistency: float | None = None
    score_cost: float | None = None
    score_scale: float | None = None
    future_return_indicator: float | None = None
    fund_age_years: int | None = None


class TopPick(BaseModel):
    scheme_code: int
    scheme_name: str
    sub_category: str | None = None
    composite_score: float | None = None
    return_1y: float | None = None
    aum_cr: float | None = None


class DashboardResponse(BaseModel):
    tabs: list[TabInfo]
    current_tab: str
    total: int
    total_aum_cr: float | None = None
    page: int
    page_size: int
    total_pages: int
    funds: list[FundRow]
    sub_categories: list[SubCategoryInfo] = []
    top_picks: list[TopPick] = []


TAB_LABELS = {
    "all": "All Funds",
    "equity": "Equity",
    "hybrid": "Hybrid",
    "index": "Index & ETFs",
    "gold_silver": "Gold & Silver",
    "global": "Global",
    "debt": "Debt",
    "solution": "Solution Oriented",
    "other": "Others",
}


@router.get("", response_model=DashboardResponse)
async def get_dashboard(
    tab: str = Query("all", description="Tab filter"),
    sub_category: str | None = Query(None, description="Sub-category filter"),
    sort_by: str = Query("composite_score", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=10, le=100),
    db: AsyncSession = Depends(get_session),
):
    if tab not in TAB_GROUPS:
        tab = "all"

    # Build tab counts
    tabs = []
    for key in TAB_GROUPS:
        if key == "all":
            cnt_q = select(func.count(Fund.id))
            aum_q = select(func.sum(Fund.aum_cr))
        else:
            cnt_q = select(func.count(Fund.id)).where(Fund.category_group == key)
            aum_q = select(func.sum(Fund.aum_cr)).where(Fund.category_group == key)

        cnt = (await db.execute(cnt_q)).scalar() or 0
        aum = (await db.execute(aum_q)).scalar() or 0
        tabs.append(
            TabInfo(
                key=key,
                label=TAB_LABELS.get(key, key.title()),
                count=cnt,
                total_aum_cr=round(aum, 2) if aum else None,
            )
        )

    # Sub-categories for equity tab
    sub_categories = []
    if tab == "equity":
        sub_q = await db.execute(
            text("""
                SELECT sub_category, COUNT(*) as cnt, AVG(composite_score) as avg_score
                FROM funds WHERE category_group = 'equity' AND sub_category IS NOT NULL
                GROUP BY sub_category ORDER BY cnt DESC
            """)
        )
        for row in sub_q.all():
            sub_categories.append(
                SubCategoryInfo(
                    key=row[0],
                    label=row[0].replace("_", " ").title(),
                    count=row[1],
                    avg_composite=round(row[2], 1) if row[2] else None,
                )
            )

    # Build fund query
    conditions = []
    if tab != "all":
        conditions.append(f"category_group = '{tab}'")
    if sub_category:
        conditions.append(f"sub_category = '{sub_category}'")

    where_clause = " AND ".join(conditions) if conditions else "TRUE"

    allowed_sorts = {
        "composite_score",
        "return_1y",
        "rolling_return_3y_avg",
        "rolling_return_5y_avg",
        "aum_cr",
        "expense_ratio",
        "nav",
        "rolling_return_positive_pct",
    }
    if sort_by not in allowed_sorts:
        sort_by = "composite_score"
    if sort_order not in ("asc", "desc"):
        sort_order = "desc"

    offset = (page - 1) * page_size

    # Count total
    total = (
        await db.execute(text(f"SELECT COUNT(*) FROM funds WHERE {where_clause}"))
    ).scalar() or 0

    total_aum = (
        await db.execute(text(f"SELECT SUM(aum_cr) FROM funds WHERE {where_clause}"))
    ).scalar() or 0

    # Fetch funds
    fund_rows = await db.execute(
        text(f"""
            SELECT
                scheme_code, scheme_name, category_group, sub_category,
                scheme_category, amc, nav, aum_cr, expense_ratio,
                return_1y, rolling_return_3y_avg, rolling_return_5y_avg,
                rolling_return_positive_pct, risk_level,
                composite_score, score_performance, score_risk,
                score_consistency, score_cost, score_scale,
                future_return_indicator,
                EXTRACT(YEAR FROM age(launch_date))::int as fund_age_years
            FROM funds
            WHERE {where_clause}
            ORDER BY {sort_by} {sort_order} NULLS LAST
            LIMIT {page_size} OFFSET {offset}
        """)
    )
    funds = []
    for r in fund_rows.all():
        funds.append(
            FundRow(
                scheme_code=r[0],
                scheme_name=r[1],
                category_group=r[2],
                sub_category=r[3],
                scheme_category=r[4],
                amc=r[5],
                nav=round(r[6], 2) if r[6] else None,
                aum_cr=round(r[7], 2) if r[7] else None,
                expense_ratio=round(r[8], 3) if r[8] else None,
                return_1y=round(r[9], 2) if r[9] else None,
                rolling_return_3y_avg=round(r[10], 2) if r[10] else None,
                rolling_return_5y_avg=round(r[11], 2) if r[11] else None,
                rolling_return_positive_pct=round(r[12], 1) if r[12] else None,
                risk_level=r[13],
                composite_score=round(r[14], 1) if r[14] else None,
                score_performance=round(r[15], 1) if r[15] else None,
                score_risk=round(r[16], 1) if r[16] else None,
                score_consistency=round(r[17], 1) if r[17] else None,
                score_cost=round(r[18], 1) if r[18] else None,
                score_scale=round(r[19], 1) if r[19] else None,
                future_return_indicator=round(r[20], 1) if r[20] else None,
                fund_age_years=r[21],
            )
        )

    # Top picks: top 5 by composite score per sub-category
    top_picks = []
    if tab == "equity":
        for sc in [
            "large_cap",
            "mid_cap",
            "small_cap",
            "multi_cap",
            "flexi_cap",
            "elss",
        ]:
            rows = await db.execute(
                text(f"""
                    SELECT scheme_code, scheme_name, sub_category, composite_score, return_1y, aum_cr
                    FROM funds WHERE category_group = 'equity' AND sub_category = '{sc}'
                    AND composite_score IS NOT NULL
                    ORDER BY composite_score DESC LIMIT 1
                """)
            )
            r = rows.first()
            if r:
                top_picks.append(
                    TopPick(
                        scheme_code=r[0],
                        scheme_name=r[1],
                        sub_category=r[2],
                        composite_score=round(r[3], 1) if r[3] else None,
                        return_1y=round(r[4], 1) if r[4] else None,
                        aum_cr=round(r[5], 1) if r[5] else None,
                    )
                )
    elif tab == "gold_silver":
        rows = await db.execute(
            text("""
                SELECT scheme_code, scheme_name, sub_category, composite_score, return_1y, aum_cr
                FROM funds WHERE category_group = 'gold_silver' AND composite_score IS NOT NULL
                ORDER BY composite_score DESC LIMIT 5
            """)
        )
        for r in rows.all():
            top_picks.append(
                TopPick(
                    scheme_code=r[0],
                    scheme_name=r[1],
                    sub_category=r[2],
                    composite_score=round(r[3], 1) if r[3] else None,
                    return_1y=round(r[4], 1) if r[4] else None,
                    aum_cr=round(r[5], 1) if r[5] else None,
                )
            )

    return DashboardResponse(
        tabs=tabs,
        current_tab=tab,
        total=total,
        total_aum_cr=round(total_aum, 2) if total_aum else None,
        page=page,
        page_size=page_size,
        total_pages=max(1, (total + page_size - 1) // page_size),
        funds=funds,
        sub_categories=sub_categories if tab == "equity" else [],
        top_picks=top_picks,
    )
