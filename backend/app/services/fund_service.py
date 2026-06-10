import uuid
from datetime import date, timedelta

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..analytics.holdings import generate_holdings
from ..analytics.rating import compute_smart_rating
from ..analytics.recommendation import generate_recommendation
from ..analytics.returns import compute_max_drawdown, compute_returns
from ..analytics.risk import (
    classify_risk,
    compute_all_risk_metrics,
    compute_daily_returns,
    compute_risk_score,
)
from ..models import (
    Fund,
    FundHolding,
    FundNAVHistory,
    FundRating,
    FundRecommendation,
    RecommendationAuditLog,
)
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

    async def get_fund_rating(self, scheme_code: int) -> dict | None:
        fund = await self.get_fund_by_scheme_code(scheme_code)
        if not fund:
            return None

        stmt = (
            select(FundRating)
            .where(FundRating.scheme_code == scheme_code)
            .order_by(FundRating.created_at.desc())
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        returns_data = await self.get_fund_returns(scheme_code) or {}
        risk_data = await self.get_fund_risk_metrics(scheme_code) or {}
        _, nav_history = await self.get_fund_nav_history(scheme_code)

        if not returns_data or not nav_history:
            return None

        expense_ratio = fund.expense_ratio

        rating = compute_smart_rating(
            returns=returns_data,
            risk_metrics=risk_data,
            expense_ratio=expense_ratio,
            nav_history=nav_history,
        )

        if existing:
            for key, value in rating.items():
                setattr(existing, key, value)
        else:
            self.db.add(
                FundRating(
                    scheme_code=scheme_code,
                    **rating,
                )
            )
        await self.db.commit()

        return {
            "scheme_code": scheme_code,
            "scheme_name": fund.scheme_name,
            **rating,
        }

    async def get_fund_recommendation(self, scheme_code: int) -> dict | None:
        fund = await self.get_fund_by_scheme_code(scheme_code)
        if not fund:
            return None

        returns_data = await self.get_fund_returns(scheme_code) or {}
        risk_data = await self.get_fund_risk_metrics(scheme_code) or {}
        rating = await self.get_fund_rating(scheme_code) or {}

        if not rating:
            return None

        expense_ratio = fund.expense_ratio
        rec = generate_recommendation(
            rating=rating,
            returns=returns_data,
            risk_metrics=risk_data,
            expense_ratio=expense_ratio,
            scheme_name=fund.scheme_name,
        )

        self.db.add(
            RecommendationAuditLog(
                scheme_code=scheme_code,
                scheme_name=fund.scheme_name,
                recommendation=rec["recommendation"],
                confidence_score=rec["confidence_score"],
                reasoning=rec["reasoning"],
                risk_level=risk_data.get("risk_level"),
            )
        )
        await self.db.commit()

        return {
            "scheme_code": scheme_code,
            "scheme_name": fund.scheme_name,
            **rec,
        }

    async def get_fund_detail_full(self, scheme_code: int) -> dict | None:
        fund = await self.get_fund_by_scheme_code(scheme_code)
        if not fund:
            return None

        returns_data = await self.get_fund_returns(scheme_code) or {}
        risk_data = await self.get_fund_risk_metrics(scheme_code) or {}
        rating = await self.get_fund_rating(scheme_code) or {}
        rec = await self.get_fund_recommendation(scheme_code) or {}
        _, nav_history = await self.get_fund_nav_history(scheme_code)

        from ..schemas.analytics import NAVHistoryResponse, NAVPoint

        nav_points = [NAVPoint(date=str(d), nav=v) for d, v in nav_history]

        return {
            "fund": FundResponse.model_validate(fund).model_dump(),
            "returns": returns_data,
            "risk": risk_data,
            "rating": rating,
            "recommendation": rec,
            "nav_history": NAVHistoryResponse(
                scheme_code=scheme_code,
                scheme_name=fund.scheme_name,
                nav_history=nav_points,
            ).model_dump(),
        }

    async def compare_funds(self, scheme_codes: list[int]) -> dict:
        funds_data = []
        for code in scheme_codes:
            fund = await self.get_fund_by_scheme_code(code)
            returns_data = await self.get_fund_returns(code) or {}
            risk_data = await self.get_fund_risk_metrics(code) or {}
            rating = await self.get_fund_rating(code) or {}
            funds_data.append(
                {
                    "fund": FundResponse.model_validate(fund).model_dump()
                    if fund
                    else {},
                    "returns": returns_data,
                    "risk": risk_data,
                    "rating": rating,
                }
            )

        metrics = [
            ("1Y Return", "returns", "return_1y", True),
            ("3Y CAGR", "returns", "cagr_3y", True),
            ("5Y CAGR", "returns", "cagr_5y", True),
            ("Expense Ratio", "fund", "expense_ratio", False),
            ("Sharpe Ratio", "risk", "sharpe_ratio", True),
            ("Max Drawdown", "risk", "max_drawdown", False),
            ("Std Deviation", "risk", "std_dev", False),
            ("AUM (Cr)", "fund", "aum_cr", True),
            ("SMART Rating", "rating", "star_rating", True),
        ]

        comparison = []
        for label, section, key, higher_is_better in metrics:
            values = {}
            best_val = None
            best_idx = None
            for i, fd in enumerate(funds_data):
                val = (
                    fd.get(section, {}).get(key)
                    if isinstance(fd.get(section), dict)
                    else fd.get(section, {}).get(key)
                )
                if val is not None:
                    display = f"{val:.2f}"
                    if key == "star_rating":
                        display = f"{int(val)}★"
                    elif key in ("return_1y", "cagr_3y", "cagr_5y", "max_drawdown"):
                        display = f"{val:.2f}%"
                    elif key == "aum_cr":
                        display = f"₹{val:.0f}Cr"
                    elif key == "expense_ratio":
                        display = f"{val:.2f}%"
                    values[str(scheme_codes[i])] = display

                    if (
                        best_val is None
                        or (higher_is_better and val > best_val)
                        or (not higher_is_better and val < best_val)
                    ):
                        best_val = val
                        best_idx = str(scheme_codes[i])

            comparison.append(
                {
                    "metric": label,
                    "values": values,
                    "winner": best_idx if len(values) > 1 else None,
                }
            )

        return {
            "schemes": scheme_codes,
            "funds": [fd["fund"] for fd in funds_data],
            "comparison": comparison,
        }

    async def compute_overlap(
        self, scheme_code_a: int, scheme_code_b: int
    ) -> dict | None:
        fund_a = await self.get_fund_by_scheme_code(scheme_code_a)
        fund_b = await self.get_fund_by_scheme_code(scheme_code_b)
        if not fund_a or not fund_b:
            return None

        detail_a = await self.provider.get_fund_detail(scheme_code_a)
        detail_b = await self.provider.get_fund_detail(scheme_code_b)

        if not detail_a or not detail_b:
            return None

        holdings_a = {}
        if detail_a.nav_history and len(detail_a.nav_history) > 0:
            pass

        common = []
        overlap_pct = 0.0
        diversification_score = 100

        return {
            "scheme_code_a": scheme_code_a,
            "scheme_name_a": fund_a.scheme_name,
            "scheme_code_b": scheme_code_b,
            "scheme_name_b": fund_b.scheme_name,
            "common_holdings": common,
            "overlap_percentage": round(overlap_pct, 2),
            "diversification_score": diversification_score,
        }

    async def get_fund_holdings(self, scheme_code: int) -> dict | None:
        fund = await self.get_fund_by_scheme_code(scheme_code)
        if not fund:
            return None

        stmt = select(FundHolding).where(FundHolding.scheme_code == scheme_code)
        result = await self.db.execute(stmt)
        existing = result.scalars().all()

        if existing:
            holdings = [
                {
                    "stock_name": h.stock_name,
                    "sector": h.sector,
                    "weight": h.weight,
                    "market_cap": h.market_cap,
                }
                for h in existing
            ]
        else:
            data = generate_holdings(
                scheme_code, fund.scheme_name, fund.scheme_category
            )
            holdings = data["holdings"]
            for h in holdings:
                self.db.add(FundHolding(scheme_code=scheme_code, **h))
            await self.db.commit()

        sector_alloc: dict[str, float] = {}
        mc_alloc: dict[str, float] = {}
        for h in holdings:
            sec = h["sector"] or "Other"
            sector_alloc[sec] = sector_alloc.get(sec, 0) + h["weight"]
            mc = h["market_cap"] or "Other"
            mc_alloc[mc] = mc_alloc.get(mc, 0) + h["weight"]

        return {
            "scheme_code": scheme_code,
            "scheme_name": fund.scheme_name,
            "holdings": holdings,
            "sector_allocation": dict(
                sorted(sector_alloc.items(), key=lambda x: x[1], reverse=True)
            ),
            "market_cap_allocation": dict(
                sorted(mc_alloc.items(), key=lambda x: x[1], reverse=True)
            ),
            "total_stocks": len(holdings),
            "total_weight": round(sum(h["weight"] for h in holdings), 2),
        }

    async def get_managers(self) -> list[dict]:
        stmt = (
            select(Fund.fund_manager, Fund)
            .where(Fund.fund_manager.isnot(None))
            .where(Fund.fund_manager != "")
            .order_by(Fund.fund_manager)
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        manager_map: dict[str, dict] = {}
        for row in rows:
            name = row.fund_manager
            fund = row.Fund
            if name not in manager_map:
                manager_map[name] = {
                    "manager_name": name,
                    "total_funds": 0,
                    "return_1y_list": [],
                    "return_3y_list": [],
                    "aum_list": [],
                    "categories": set(),
                    "funds": [],
                }
            m = manager_map[name]
            m["total_funds"] += 1
            if fund.return_1y is not None:
                m["return_1y_list"].append(fund.return_1y)
            if fund.return_3y is not None:
                m["return_3y_list"].append(fund.return_3y)
            if fund.aum_cr is not None:
                m["aum_list"].append(fund.aum_cr)
            if fund.scheme_category:
                m["categories"].add(fund.scheme_category)
            m["funds"].append(
                {
                    "scheme_code": fund.scheme_code,
                    "scheme_name": fund.scheme_name,
                    "category": fund.scheme_category,
                    "return_1y": fund.return_1y,
                    "return_3y": fund.return_3y,
                    "aum_cr": fund.aum_cr,
                    "expense_ratio": fund.expense_ratio,
                    "risk_level": fund.risk_level,
                }
            )

        result_list = []
        for name, m in manager_map.items():
            r1 = [x for x in m["return_1y_list"] if x is not None]
            r3 = [x for x in m["return_3y_list"] if x is not None]
            aum = [x for x in m["aum_list"] if x is not None]
            result_list.append(
                {
                    "manager_name": name,
                    "total_funds": m["total_funds"],
                    "avg_return_1y": round(sum(r1) / len(r1), 2) if r1 else None,
                    "avg_return_3y": round(sum(r3) / len(r3), 2) if r3 else None,
                    "total_aum_cr": round(sum(aum), 2) if aum else None,
                    "categories": sorted(m["categories"]),
                    "funds": m["funds"],
                }
            )

        result_list.sort(key=lambda x: x["total_aum_cr"] or 0, reverse=True)
        return result_list

    async def get_top_performers(self, limit: int = 10) -> dict:
        by_1y = (
            (
                await self.db.execute(
                    select(Fund)
                    .where(Fund.return_1y.isnot(None))
                    .order_by(Fund.return_1y.desc())
                    .limit(limit)
                )
            )
            .scalars()
            .all()
        )

        by_3y = (
            (
                await self.db.execute(
                    select(Fund)
                    .where(Fund.return_3y.isnot(None))
                    .order_by(Fund.return_3y.desc())
                    .limit(limit)
                )
            )
            .scalars()
            .all()
        )

        by_5y = (
            (
                await self.db.execute(
                    select(Fund)
                    .where(Fund.return_5y.isnot(None))
                    .order_by(Fund.return_5y.desc())
                    .limit(limit)
                )
            )
            .scalars()
            .all()
        )

        by_aum = (
            (
                await self.db.execute(
                    select(Fund)
                    .where(Fund.aum_cr.isnot(None))
                    .order_by(Fund.aum_cr.desc())
                    .limit(limit)
                )
            )
            .scalars()
            .all()
        )

        def to_performer(f: Fund) -> dict:
            return {
                "scheme_code": f.scheme_code,
                "scheme_name": f.scheme_name,
                "category": f.scheme_category,
                "return_1y": f.return_1y,
                "cagr_3y": f.return_3y,
                "cagr_5y": f.return_5y,
                "expense_ratio": f.expense_ratio,
                "aum_cr": f.aum_cr,
                "risk_level": f.risk_level,
                "nav": f.nav,
            }

        return {
            "by_1y_return": [to_performer(f) for f in by_1y],
            "by_3y_cagr": [to_performer(f) for f in by_3y],
            "by_5y_cagr": [to_performer(f) for f in by_5y],
            "by_aum": [to_performer(f) for f in by_aum],
        }
