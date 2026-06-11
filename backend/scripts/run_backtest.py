"""Run backtesting engine for factor predictive power analysis.

Usage:
    docker compose exec -T backend python3 scripts/run_backtest.py
    docker compose exec -T backend python3 scripts/run_backtest.py --groups equity,hybrid,debt
    docker compose exec -T backend python3 scripts/run_backtest.py --factors momentum_1y,cost
"""

import argparse
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, text

from app.analytics.backtest import (
    FACTOR_DEFINITIONS,
    FORWARD_WINDOWS,
    backtest_category_group,
)
from app.core.database import async_session_factory, init_db
from app.models import Fund
from app.models.analytics import BacktestResult

CATEGORY_GROUPS = ["equity", "hybrid", "debt"]


async def load_fund_data(category_group: str) -> list[dict]:
    """Load all fund NAV data for a category group in batch."""
    async with async_session_factory() as session:
        funds = await session.execute(
            select(Fund).where(
                Fund.category_group == category_group,
                Fund.rolling_return_1y_avg.isnot(None),
            )
        )
        funds = funds.scalars().all()
        fund_map = {str(f.id): f for f in funds}

    async with async_session_factory() as session:
        rows = await session.execute(
            text(
                "SELECT fund_id, nav_date, nav FROM fund_nav_history "
                "WHERE fund_id = ANY(:fids) ORDER BY fund_id, nav_date"
            ),
            {"fids": [f.id for f in funds]},
        )
        nav_rows = rows.all()

    by_fund: dict[str, list] = {}
    for fid, nd, nv in nav_rows:
        by_fund.setdefault(str(fid), []).append((nd, nv))

    result = []
    for fid_str, nav_history in by_fund.items():
        if len(nav_history) < 120:
            continue
        fund = fund_map[fid_str]
        result.append(
            {
                "id": fid_str,
                "scheme_code": fund.scheme_code,
                "nav_history": nav_history,
                "expense_ratio": fund.expense_ratio,
                "aum_cr": fund.aum_cr,
            }
        )

    return result


async def store_result(session, result: dict):
    """Store a backtest result row."""
    existing = await session.execute(
        select(BacktestResult).where(
            BacktestResult.factor_name == result["factor_name"],
            BacktestResult.category_group == result["category_group"],
        )
    )
    existing = existing.scalar_one_or_none()

    if existing:
        existing.predictive_power = result["predictive_power"]
        existing.direction = result["direction"]
        existing.avg_top_quintile_fwd = result["avg_top_quintile_fwd"]
        existing.avg_bottom_quintile_fwd = result["avg_bottom_quintile_fwd"]
        existing.spread = result["spread"]
        existing.hit_rate = result["hit_rate"]
        existing.observation_count = result["observation_count"]
    else:
        session.add(
            BacktestResult(
                factor_name=result["factor_name"],
                category_group=result["category_group"],
                predictive_power=result["predictive_power"],
                direction=result["direction"],
                avg_top_quintile_fwd=result["avg_top_quintile_fwd"],
                avg_bottom_quintile_fwd=result["avg_bottom_quintile_fwd"],
                spread=result["spread"],
                hit_rate=result["hit_rate"],
                observation_count=result["observation_count"],
            )
        )


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--groups",
        default=",".join(CATEGORY_GROUPS),
        help="Comma-separated category groups",
    )
    parser.add_argument(
        "--factors",
        default=",".join(FACTOR_DEFINITIONS.keys()),
        help="Comma-separated factor names",
    )
    parser.add_argument(
        "--forward",
        default=",".join(str(w) for w in FORWARD_WINDOWS),
        help="Comma-separated forward windows in days",
    )
    args = parser.parse_args()

    groups = args.groups.split(",")
    factors = args.factors.split(",")
    forward_windows = [int(w) for w in args.forward.split(",")]

    await init_db()

    all_results = []
    for group in groups:
        print(f"\nLoading {group} funds ...")
        fund_data = await load_fund_data(group)
        print(f"  {len(fund_data)} funds with ≥120 NAV points")

        if not fund_data:
            print(f"  Skipping {group} - no data")
            continue

        for factor in factors:
            for fwd_days in forward_windows:
                print(f"  Backtesting {factor} fwd={fwd_days}d ...")
                result = backtest_category_group(
                    fund_data, factor, group, forward_days=fwd_days
                )
                all_results.append(result)
                print(
                    f"    spread={result['spread']:+.2f}% "
                    f"hit_rate={result['hit_rate']:.1%} "
                    f"obs={result['observation_count']}"
                )

    print(f"\n=== Storing {len(all_results)} results ===")
    async with async_session_factory() as session:
        for result in all_results:
            await store_result(session, result)
        await session.commit()

    print("\n=== Backtest Summary ===")
    print(
        f"{'Factor':<20} {'Group':<10} {'Fwd':<6} {'Spread':<10} {'HitRate':<10} {'Power':<10} {'Obs':<6}"
    )
    print("-" * 72)
    for r in sorted(all_results, key=lambda x: abs(x["spread"] or 0), reverse=True):
        print(
            f"{r['factor_name']:<20} {r['category_group']:<10} "
            f"{r['forward_days']:<6} {r['spread']:<+8.2f}%  "
            f"{r['hit_rate']:<9.1%} {r['predictive_power']:<+8.4f}  "
            f"{r['observation_count']:<6}"
        )


if __name__ == "__main__":
    asyncio.run(main())
