"""Recompute composite scores for all scored funds (preserves rolling returns).

Use this after updating expense_ratio (or other input data) to refresh:
  - score_performance, score_risk, score_consistency, score_cost, score_scale
  - composite_score

Does NOT recompute rolling returns (requires rolling_return_3y_avg IS NOT NULL).

Usage:
    docker compose exec -T backend python3 scripts/recompute_scores.py
"""

import asyncio
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, text

from app.analytics.scorer import FundMetrics, compute_composite_score
from app.core.database import async_session_factory, init_db
from app.models import Fund


async def recompute_all_scores():
    print("\n=== Recomputing Composite Scores ===")
    async with async_session_factory() as session:
        groups = await session.execute(
            text(
                "SELECT DISTINCT category_group FROM funds WHERE category_group IS NOT NULL"
            )
        )
        groups = [r[0] for r in groups.all()]

    total = 0
    for group in groups:
        async with async_session_factory() as session:
            result = await session.execute(
                select(Fund).where(
                    Fund.category_group == group,
                    Fund.rolling_return_3y_avg.isnot(None),
                )
            )
            funds = result.scalars().all()
            if not funds:
                continue

            vals_1y = [
                f.rolling_return_1y_avg for f in funds if f.rolling_return_1y_avg
            ]
            vals_3y = [
                f.rolling_return_3y_avg for f in funds if f.rolling_return_3y_avg
            ]
            vals_aum = [f.aum_cr for f in funds if f.aum_cr]
            vals_exp = [f.expense_ratio for f in funds if f.expense_ratio]

            mean_1y = sum(vals_1y) / len(vals_1y) if vals_1y else 10
            mean_3y = sum(vals_3y) / len(vals_3y) if vals_3y else 12
            mean_aum = sum(vals_aum) / len(vals_aum) if vals_aum else 1000
            mean_exp = sum(vals_exp) / len(vals_exp) if vals_exp else 1.5

            std_1y = (
                (sum((v - mean_1y) ** 2 for v in vals_1y) / len(vals_1y)) ** 0.5
                if vals_1y
                else 10
            )
            std_3y = (
                (sum((v - mean_3y) ** 2 for v in vals_3y) / len(vals_3y)) ** 0.5
                if vals_3y
                else 8
            )

            peer_means = FundMetrics(
                return_1y=mean_1y,
                rolling_3y=mean_3y,
                expense_ratio=mean_exp,
            )
            peer_stds = FundMetrics(
                return_1y=std_1y,
                rolling_3y=std_3y,
            )

            bounds = {
                "return_1y": (
                    min(vals_1y) if vals_1y else -20,
                    max(vals_1y) if vals_1y else 80,
                ),
                "aum_cr": (0, max(vals_aum) if vals_aum else 100000),
                "expense_ratio": (
                    min(vals_exp) if vals_exp else 0.0,
                    max(vals_exp) if vals_exp else 3.0,
                ),
            }

            for fund in funds:
                today = date.today()
                age = (
                    (today - fund.launch_date).days / 365.25
                    if fund.launch_date
                    else None
                )

                metrics = FundMetrics(
                    return_1y=fund.rolling_return_1y_avg,
                    rolling_3y=fund.rolling_return_3y_avg,
                    rolling_5y=fund.rolling_return_5y_avg,
                    rolling_positive_pct=fund.rolling_return_positive_pct,
                    expense_ratio=fund.expense_ratio,
                    expense_ratio_peer_avg=mean_exp,
                    aum_cr=fund.aum_cr,
                    fund_age_years=age,
                )

                scores = compute_composite_score(
                    metrics,
                    peer_means=peer_means,
                    peer_stds=peer_stds,
                    peer_bounds=bounds,
                )
                for k, v in scores.items():
                    setattr(fund, k, v)
                total += 1

            await session.commit()
            print(f"  Scored {len(funds)} funds in '{group}'", flush=True)

    print(f"Recomputed scores for {total} funds total")
    return total


async def main():
    await init_db()
    sc = await recompute_all_scores()
    print(f"\nDone: {sc} scores recomputed")


if __name__ == "__main__":
    asyncio.run(main())
