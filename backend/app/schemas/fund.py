import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class FundBase(BaseModel):
    scheme_code: int
    scheme_name: str
    amc: str | None = None
    scheme_type: str | None = None
    scheme_category: str | None = None
    fund_family: str | None = None
    isin: str | None = None
    isin_growth: str | None = None
    nav: float | None = None
    nav_date: date | None = None
    aum_cr: float | None = None
    expense_ratio: float | None = None
    fund_manager: str | None = None
    risk_level: str | None = None
    return_1y: float | None = None
    return_3y: float | None = None
    return_5y: float | None = None
    benchmark: str | None = None


class FundCreate(FundBase):
    pass


class FundResponse(FundBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FundSearchResult(BaseModel):
    total: int
    page: int
    page_size: int
    results: list[FundResponse]


class FundNAVData(BaseModel):
    date: date
    nav: float


class FundNAVHistoryResponse(BaseModel):
    scheme_code: int
    scheme_name: str
    nav_history: list[FundNAVData]


class FundListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    funds: list[FundResponse]
