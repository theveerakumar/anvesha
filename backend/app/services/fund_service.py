import uuid

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Fund
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
