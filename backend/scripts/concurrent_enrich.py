"""Concurrent NAV history fetcher.

Usage:
    docker compose exec -T backend python3 scripts/concurrent_enrich.py
    docker compose exec -T backend python3 scripts/concurrent_enrich.py --limit 1000 --batch 30

Batch sizes:
    --limit   total funds to process (default: 500)
    --batch   concurrent requests (default: 20)
"""

import argparse
import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from app.core.database import async_session_factory, init_db
from app.models import Fund
from app.providers import get_provider


async def fetch_one(provider, fund_id: int, scheme_code: int) -> int | None:
    detail = await provider.get_fund_detail(scheme_code)
    if not detail or not detail.nav_history:
        return None

    async with async_session_factory() as session:
        fund = await session.get(Fund, fund_id)
        if not fund:
            return None

        for nav in detail.nav_history:
            existing = await session.execute(
                text(
                    "SELECT id FROM fund_nav_history WHERE fund_id = :fid AND nav_date = :nd"
                ),
                {"fid": fund.id, "nd": nav.date},
            )
            if not existing.scalar_one_or_none():
                await session.execute(
                    text(
                        "INSERT INTO fund_nav_history (id, fund_id, nav_date, nav) "
                        "VALUES (gen_random_uuid(), :fid, :nd, :n)"
                    ),
                    {"fid": fund.id, "nd": nav.date, "n": nav.nav},
                )

        if detail.nav is not None:
            fund.nav = detail.nav
        if detail.nav_date is not None:
            fund.nav_date = detail.nav_date
        if fund.launch_date is None and detail.nav_history:
            fund.launch_date = detail.nav_history[0].date

        await session.commit()

    return scheme_code


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--batch", type=int, default=20)
    args = parser.parse_args()

    await init_db()
    provider = get_provider()

    async with async_session_factory() as session:
        rows = await session.execute(
            text(
                "SELECT id, scheme_code FROM funds "
                "WHERE scheme_code IS NOT NULL "
                "AND NOT EXISTS (SELECT 1 FROM fund_nav_history WHERE fund_nav_history.fund_id = funds.id) "
                "ORDER BY "
                "  CASE category_group "
                "    WHEN 'equity' THEN 1 "
                "    WHEN 'hybrid' THEN 2 "
                "    WHEN 'debt' THEN 3 "
                "    WHEN 'index' THEN 4 "
                "    WHEN 'gold_silver' THEN 5 "
                "    WHEN 'global' THEN 6 "
                "    WHEN 'solution' THEN 7 "
                "    ELSE 8 "
                "  END "
                "LIMIT :lim"
            ),
            {"lim": args.limit},
        )
        queue = [(r[0], r[1]) for r in rows]

    if not queue:
        print("No funds to process.")
        return

    print(f"Processing {len(queue)} funds (batch={args.batch}) ...")
    start = time.time()

    sem = asyncio.Semaphore(args.batch)

    async def process(fid: int, sc: int) -> int | None:
        async with sem:
            return await fetch_one(provider, fid, sc)

    tasks = [process(fid, sc) for fid, sc in queue]
    results = await asyncio.gather(*tasks)

    elapsed = time.time() - start
    success = sum(1 for r in results if r is not None)
    print(
        f"\nDone: {success}/{len(queue)} enriched in {elapsed:.1f}s ({elapsed / len(queue):.2f}s per fund)"
    )

    await provider.close()


if __name__ == "__main__":
    asyncio.run(main())
