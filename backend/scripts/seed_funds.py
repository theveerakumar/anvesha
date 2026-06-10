"""Seed fund data from MFAPI.in into the database."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import async_session_factory, init_db
from app.providers import get_provider
from app.services.fund_service import FundService


async def seed():
    print("Initializing database...")
    await init_db()

    print("Fetching all funds from MFAPI.in...")
    async with async_session_factory() as session:
        service = FundService(session)
        count = await service.sync_all_funds()
        print(f"Seeded {count} funds into database.")


if __name__ == "__main__":
    asyncio.run(seed())
