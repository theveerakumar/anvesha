import uuid
from datetime import date, timedelta

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..analytics.returns import compute_max_drawdown, compute_returns
from ..analytics.risk import (
    classify_risk,
    compute_all_risk_metrics,
    compute_daily_returns,
    compute_risk_score,
)
from ..models import Fund, FundNAVHistory
from ..schemas.fund import FundCreate, FundResponse
from ..providers import get_provider, MutualFundProvider


class FundService:
    def __init__(self, db: AsyncSession, provider: MutualFundProvider | None = None):
        self.db = db
        self.provider = provider or get_provider()

    async def search_funds(
        self, query: str, page: int = 1, page_size: int = 20
    ) -> tuple[list[FundResponse], int]:
        stmt = (
            select(Fund)
            .where(
                or_(
                    Fund.scheme_name.ilike(f"%{query}%"),
                    Fund.amc.ilike(f"%{query}%"),
                    Fund.scheme_category.ilike(f"%{query}%"),
                    Fund.fund_family.ilike(f"%{query}%"),
                )
            )
            .order_by(Fund.scheme_name)
        )

        count_stmt = select(Fund.id).where(
            or_(
                Fund.scheme_name.ilike(f"%{query}%"),
                Fund.amc.ilike(f"%{query}%"),
                Fund.scheme_category.ilike(f"%{query}%"),
                Fund.fund_family.ilike(f"%{query}%"),
            )
        )
        total = len((await self.db.execute(count_stmt)).scalars().all())

        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)
        result = await self.db.execute(stmt)
        funds = result.scalars().all()

        return [FundResponse.model_validate(f) for f in funds], total

    async def get_fund_by_scheme_code(self, scheme_code: int) -> FundResponse | None:
        stmt = select(Fund).where(Fund.scheme_code == scheme_code)
        result = await self.db.execute(stmt)
        fund = result.scalar_one_or_none()
        if fund:
            return FundResponse.model_validate(fund)
        return None

    async def upsert_fund(self, fund_data: FundCreate) -> FundResponse:
        stmt = select(Fund).where(Fund.scheme_code == fund_data.scheme_code)
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            for key, value in fund_data.model_dump(exclude_unset=True).items():
                setattr(existing, key, value)
            await self.db.flush()
            return FundResponse.model_validate(existing)
        else:
            fund = Fund(**fund_data.model_dump(), id=uuid.uuid4())
            self.db.add(fund)
            await self.db.flush()
            return FundResponse.model_validate(fund)

    async def sync_all_funds(self):
        items = await self.provider.get_all_funds()
        count = 0
        for item in items:
            fund_data = FundCreate(
                scheme_code=item.scheme_code,
                scheme_name=item.scheme_name,
                scheme_type=item.scheme_type,
                scheme_category=item.scheme_category,
                fund_family=item.fund_family,
            )
            await self.upsert_fund(fund_data)
            count += 1
        await self.db.commit()
        return count

    async def get_funds_list(
        self, page: int = 1, page_size: int = 50
    ) -> tuple[list[FundResponse], int]:
        stmt = select(Fund).order_by(Fund.scheme_name)
        count_stmt = select(Fund.id)
        total = len((await self.db.execute(count_stmt)).scalars().all())

        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)
        result = await self.db.execute(stmt)
        funds = result.scalars().all()

        return [FundResponse.model_validate(f) for f in funds], total

    async def get_fund_nav_history(
        self, scheme_code: int
    ) -> tuple[Fund | None, list[tuple[date, float]]]:
        stmt = select(Fund).where(Fund.scheme_code == scheme_code)
        result = await self.db.execute(stmt)
        fund = result.scalar_one_or_none()
        if not fund:
            return None, []

        db_records = await self.db.execute(
            select(FundNAVHistory)
            .where(FundNAVHistory.fund_id == fund.id)
            .order_by(FundNAVHistory.nav_date)
        )
        db_navs = db_records.scalars().all()

        if len(db_navs) < 30:
            detail = await self.provider.get_fund_detail(scheme_code)
            if detail and detail.nav_history:
                for nav in detail.nav_history:
                    exists = await self.db.execute(
                        select(FundNAVHistory).where(
                            FundNAVHistory.fund_id == fund.id,
                            FundNAVHistory.nav_date == nav.date,
                        )
                    )
                    if not exists.scalar_one_or_none():
                        self.db.add(
                            FundNAVHistory(
                                fund_id=fund.id,
                                nav_date=nav.date,
                                nav=nav.nav,
                            )
                        )
                await self.db.commit()

                db_records = await self.db.execute(
                    select(FundNAVHistory)
                    .where(FundNAVHistory.fund_id == fund.id)
                    .order_by(FundNAVHistory.nav_date)
                )
                db_navs = db_records.scalars().all()

                if detail.nav:
                    fund.nav = detail.nav
                if detail.nav_date:
                    fund.nav_date = detail.nav_date
                await self.db.commit()

        nav_history = [(r.nav_date, r.nav) for r in db_navs]
        return fund, nav_history

    async def get_fund_returns(self, scheme_code: int) -> dict | None:
        fund, nav_history = await self.get_fund_nav_history(scheme_code)
        if not fund or not nav_history:
            return None

        returns = compute_returns(nav_history)
        max_dd = compute_max_drawdown(nav_history)

        return {
            "scheme_code": fund.scheme_code,
            "scheme_name": fund.scheme_name,
            **returns,
            "max_drawdown": max_dd,
        }

    async def get_fund_risk_metrics(self, scheme_code: int) -> dict | None:
        fund, nav_history = await self.get_fund_nav_history(scheme_code)
        if not fund or not nav_history:
            return None

        daily_returns = compute_daily_returns(nav_history)
        max_dd = compute_max_drawdown(nav_history)

        risk_metrics = compute_all_risk_metrics(daily_returns, benchmark_returns=None)
        risk_metrics["max_drawdown"] = max_dd
        risk_score = compute_risk_score(risk_metrics)

        return {
            "scheme_code": fund.scheme_code,
            "scheme_name": fund.scheme_name,
            **risk_metrics,
            "risk_score": risk_score,
            "risk_level": classify_risk(risk_score),
        }

    async def get_funds_by_category(
        self, category: str, limit: int = 10
    ) -> list[FundResponse]:
        stmt = (
            select(Fund)
            .where(Fund.scheme_category.ilike(f"%{category}%"))
            .order_by(Fund.scheme_name)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        funds = result.scalars().all()
        return [FundResponse.model_validate(f) for f in funds]

    async def get_category_avg_returns(self, category: str) -> dict:
        stmt = select(Fund).where(Fund.scheme_category.ilike(f"%{category}%"))
        result = await self.db.execute(stmt)
        funds = result.scalars().all()

        returns_1y = [f.return_1y for f in funds if f.return_1y is not None]
        returns_3y = [f.return_3y for f in funds if f.return_3y is not None]
        returns_5y = [f.return_5y for f in funds if f.return_5y is not None]

        return {
            "category": category,
            "total_funds": len(funds),
            "avg_return_1y": round(sum(returns_1y) / len(returns_1y), 2)
            if returns_1y
            else None,
            "avg_cagr_3y": round(sum(returns_3y) / len(returns_3y), 2)
            if returns_3y
            else None,
            "avg_cagr_5y": round(sum(returns_5y) / len(returns_5y), 2)
            if returns_5y
            else None,
        }
