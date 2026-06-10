"""Enrichment pipeline: categories, AUM, launch dates, NAV history, rolling returns, scores."""

import asyncio
import csv
import os
import sys
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, text, update

from app.analytics.categorizer import classify
from app.analytics.rolling_returns import compute_rolling_returns
from app.analytics.scorer import FundMetrics, compute_composite_score
from app.core.database import async_session_factory, init_db
from app.models import Fund
from app.providers import get_provider
from app.services.fund_service import FundService


async def enrich_categories():
    print("\n=== Step 1: Category Classification ===")
    async with async_session_factory() as session:
        result = await session.execute(
            select(Fund).where(Fund.category_group.is_(None)).limit(50000)
        )
        funds = result.scalars().all()
        count = 0
        for fund in funds:
            group, sub = classify(fund.scheme_name, fund.scheme_category)
            fund.category_group = group
            fund.sub_category = sub
            count += 1
        await session.commit()
        print(f"Classified {count} funds")
        return count


async def enrich_from_csv():
    print("\n=== Step 2: Import GitHub Dataset ===")
    csv_path = "/tmp/mutual_fund_data.csv"
    if not os.path.exists(csv_path):
        print("CSV not found, skipping")
        return 0

    with open(csv_path) as f:
        rows = list(csv.DictReader(f))

    async with async_session_factory() as session:
        updated = 0
        for row in rows:
            try:
                code = int(row["Scheme_Code"])
            except (ValueError, KeyError):
                continue

            result = await session.execute(select(Fund).where(Fund.scheme_code == code))
            fund = result.scalar_one_or_none()
            if not fund:
                continue

            if row.get("AMC") and row["AMC"].strip():
                fund.amc = row["AMC"].strip()

            if row.get("Scheme_Type") and row["Scheme_Type"].strip():
                fund.scheme_type = row["Scheme_Type"].strip()

            if row.get("Scheme_Category") and row["Scheme_Category"].strip():
                cat = row["Scheme_Category"].strip()
                if not fund.scheme_category or fund.scheme_category != cat:
                    fund.scheme_category = cat
                    group, sub = classify(fund.scheme_name, cat)
                    fund.category_group = group
                    fund.sub_category = sub

            if row.get("NAV") and row["NAV"].strip():
                try:
                    fund.nav = float(row["NAV"])
                except ValueError:
                    pass

            if row.get("Latest_NAV_Date") and row["Latest_NAV_Date"].strip():
                try:
                    fund.nav_date = datetime.strptime(
                        row["Latest_NAV_Date"].strip(), "%Y-%m-%d"
                    ).date()
                except ValueError:
                    pass

            if row.get("Average_AUM_Cr") and row["Average_AUM_Cr"].strip():
                try:
                    fund.aum_cr = float(row["Average_AUM_Cr"])
                except ValueError:
                    pass

            if row.get("Launch_Date") and row["Launch_Date"].strip():
                try:
                    fund.launch_date = datetime.strptime(
                        row["Launch_Date"].strip(), "%Y-%m-%d"
                    ).date()
                except ValueError:
                    pass

            if row.get("Closure_Date") and row["Closure_Date"].strip():
                try:
                    fd = datetime.strptime(
                        row["Closure_Date"].strip(), "%Y-%m-%d"
                    ).date()
                    if fd != fund.launch_date:
                        fund.closure_date = fd
                except ValueError:
                    pass

            updated += 1
            if updated % 1000 == 0:
                print(f"  ... {updated} updated")

        await session.commit()
        print(f"Updated {updated} funds from CSV")
        return updated


async def enrich_nav_history(limit: int = 100):
    print(f"\n=== Step 3: Fetch NAV History (limit={limit}) ===")
    async with async_session_factory() as session:
        result = await session.execute(
            select(Fund)
            .where(Fund.category_group.isnot(None))
            .order_by(Fund.updated_at)
            .limit(limit)
        )
        funds = result.scalars().all()

    provider = get_provider()
    enriched = 0
    for fund in funds:
        try:
            detail = await provider.get_fund_detail(fund.scheme_code)
            if detail and detail.nav_history:
                async with async_session_factory() as session:
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
                                    "INSERT INTO fund_nav_history (id, fund_id, nav_date, nav) VALUES (gen_random_uuid(), :fid, :nd, :n)"
                                ),
                                {"fid": fund.id, "nd": nav.date, "n": nav.nav},
                            )

                    if detail.nav:
                        fund.nav = detail.nav
                    if detail.nav_date:
                        fund.nav_date = detail.nav_date
                    if not fund.launch_date and detail.nav_history:
                        fund.launch_date = detail.nav_history[0].date
                    await session.commit()
                    enriched += 1
        except Exception as e:
            print(f"  Error {fund.scheme_code}: {e}")

        if enriched % 10 == 0 and enriched > 0:
            print(f"  ... {enriched} enriched")

    print(f"Fetched NAV history for {enriched} funds")
    return enriched


async def compute_all_rolling_returns():
    print("\n=== Step 4: Compute Rolling Returns ===")
    async with async_session_factory() as session:
        result = await session.execute(
            select(Fund)
            .where(
                Fund.rolling_return_3y_avg.is_(None),
                Fund.category_group.isnot(None),
            )
            .limit(5000)
        )
        funds = result.scalars().all()

    computed = 0
    for fund in funds:
        async with async_session_factory() as session:
            try:
                nav_data = await session.execute(
                    text(
                        "SELECT nav_date, nav FROM fund_nav_history WHERE fund_id = :fid ORDER BY nav_date"
                    ),
                    {"fid": fund.id},
                )
                rows = nav_data.all()
                if len(rows) >= 60:
                    nav_history = [(r[0], r[1]) for r in rows]
                    rr = compute_rolling_returns(nav_history)
                    for k, v in rr.items():
                        setattr(fund, k, v)
                    fund.rolling_return_positive_pct = rr.get(
                        "rolling_return_positive_pct"
                    )
                    await session.commit()
                    computed += 1
            except Exception as e:
                print(f"  Error computing {fund.scheme_code}: {e}")

        if computed % 100 == 0 and computed > 0:
            print(f"  ... {computed} computed")

    print(f"Computed rolling returns for {computed} funds")
    return computed


async def compute_all_scores():
    print("\n=== Step 5: Compute Composite Scores ===")
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

            vals_1y = [f.return_1y for f in funds if f.return_1y]
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

                # Simple aum_growth proxy
                aum_growth = None

                metrics = FundMetrics(
                    return_1y=fund.return_1y,
                    rolling_3y=fund.rolling_return_3y_avg,
                    rolling_5y=fund.rolling_return_5y_avg,
                    rolling_positive_pct=fund.rolling_return_positive_pct,
                    expense_ratio=fund.expense_ratio,
                    expense_ratio_peer_avg=mean_exp,
                    aum_cr=fund.aum_cr,
                    fund_age_years=age,
                    aum_growth_1y=aum_growth,
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
            print(f"  Scored {len(funds)} funds in '{group}'")

    print(f"Computed scores for {total} funds total")
    return total


async def main():
    await init_db()
    await enrich_categories()
    await enrich_from_csv()
    await compute_all_rolling_returns()
    await compute_all_scores()
    print("\n=== Enrichment Complete ===")


if __name__ == "__main__":
    asyncio.run(main())
