"""Recompute rolling returns and composite scores for all funds with NAV history.

Usage:
    docker compose exec -T backend python3 scripts/compute_rolling_and_scores.py
"""

import asyncio
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, text

from app.analytics.rolling_returns import compute_rolling_returns
from app.analytics.scorer import FundMetrics, compute_composite_score
from app.core.database import async_session_factory, init_db
from app.models import Fund


async def compute_all_rolling_returns():
    print("\n=== Computing Rolling Returns ===")
    async with async_session_factory() as session:
        result = await session.execute(
            select(Fund).where(
                Fund.category_group.isnot(None),
                Fund.rolling_return_3y_avg.is_(None),
                Fund.scheme_name.notilike("%dividend%"),
                Fund.scheme_name.notilike("%idcw%"),
                Fund.scheme_name.notilike("%unclaimed%"),
                Fund.scheme_name.notilike("%income distribution%"),
                Fund.scheme_name.notilike("%payout%"),
            )
        )
        funds = result.scalars().all()
        fund_ids = [f.id for f in funds]

    computed = 0
    for fid in fund_ids:
        async with async_session_factory() as session:
            try:
                fund = await session.get(Fund, fid)
                if not fund:
                    continue

                rows = await session.execute(
                    text(
                        "SELECT nav_date, nav FROM fund_nav_history WHERE fund_id = :fid ORDER BY nav_date"
                    ),
                    {"fid": fid},
                )
                rows = rows.all()
                if len(rows) < 60:
                    continue

                nav_history = [(r[0], r[1]) for r in rows]
                rr = compute_rolling_returns(nav_history)
                for k, v in rr.items():
                    if isinstance(v, (int, float)) and k != "rolling_window_count":
                        if v is not None:
                            is_debt = fund.category_group == "debt"
                            if "1y" in k and (v > (50 if is_debt else 100) or v < -50):
                                v = None
                            elif "3y" in k and (v > (30 if is_debt else 60) or v < -30):
                                v = None
                            elif "5y" in k and (v > (25 if is_debt else 50) or v < -25):
                                v = None
                    setattr(fund, k, v)
                await session.commit()
                computed += 1
            except Exception as e:
                print(f"  Error computing fund {fid}: {e}", flush=True)

        if computed % 100 == 0 and computed > 0:
            print(f"  ... {computed} computed", flush=True)

    print(f"Computed rolling returns for {computed} funds")
    return computed


async def compute_all_scores():
    print("\n=== Computing Composite Scores ===")
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

    print(f"Computed scores for {total} funds total")
    return total


async def main():
    await init_db()
    rr = await compute_all_rolling_returns()
    sc = await compute_all_scores()
    print(f"\nDone: {rr} rolling returns, {sc} scores")


if __name__ == "__main__":
    asyncio.run(main())
