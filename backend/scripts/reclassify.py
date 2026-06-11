"""Reclassify mis-categorized funds after categorizer fix."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.analytics.categorizer import classify
from app.core.database import async_session_factory
from app.models.fund import Fund


async def reclassify():
    async with async_session_factory() as session:
        result = await session.execute(
            select(Fund).where(Fund.scheme_category.isnot(None))
        )
        funds = result.scalars().all()

        fixed = 0
        for fund in funds:
            group, sub = classify(fund.scheme_name, fund.scheme_category)
            if group != fund.category_group or sub != fund.sub_category:
                fund.category_group = group
                fund.sub_category = sub
                fixed += 1

        await session.commit()
        print(f"Reclassified {fixed} funds out of {len(funds)} checked")


if __name__ == "__main__":
    asyncio.run(reclassify())
