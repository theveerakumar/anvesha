from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_session
from ..schemas.analytics import ManagerResponse
from ..services.fund_service import FundService

router = APIRouter(prefix="/api/v1/managers", tags=["managers"])


@router.get("", response_model=list[ManagerResponse])
async def list_managers(
    db: AsyncSession = Depends(get_session),
):
    service = FundService(db)
    data = await service.get_managers()
    return [ManagerResponse(**m) for m in data]
