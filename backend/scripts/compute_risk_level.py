"""Compute and store risk_level for all funds with NAV history."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.analytics.risk import (
    classify_risk,
    compute_all_risk_metrics,
    compute_daily_returns,
    compute_risk_score,
)
from app.core.database import async_session_factory
from app.models.fund import Fund, FundNAVHistory


async def main():
    async with async_session_factory() as session:
        result = await session.execute(
            select(Fund).where(Fund.composite_score.isnot(None))
        )
        funds = result.scalars().all()
        print(f"Funds with scores: {len(funds)}")

        updated = 0
        for fund in funds:
            nav_result = await session.execute(
                select(FundNAVHistory)
                .where(FundNAVHistory.fund_id == fund.id)
                .order_by(FundNAVHistory.nav_date)
            )
            nav_tuples = [
                (r.nav_date, r.nav) for r in nav_result.scalars().all() if r.nav > 0
            ]

            if len(nav_tuples) < 10:
                continue

            daily_returns = compute_daily_returns(nav_tuples)
            risk_metrics = compute_all_risk_metrics(
                daily_returns, benchmark_returns=None
            )
            risk_score = compute_risk_score(risk_metrics)
            fund.risk_level = classify_risk(risk_score)
            updated += 1

            if updated % 1000 == 0:
                await session.commit()
                print(f"  Updated {updated} funds...")

        await session.commit()
        print(f"Updated {updated} funds with risk_level")


if __name__ == "__main__":
    asyncio.run(main())
