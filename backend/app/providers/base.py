from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date


@dataclass
class FundSearchItem:
    scheme_code: int
    scheme_name: str
    scheme_type: str | None = None
    scheme_category: str | None = None
    amc: str | None = None
    fund_family: str | None = None
    isin: str | None = None
    isin_growth: str | None = None
    nav: float | None = None
    nav_date: date | None = None


@dataclass
class NAVRecord:
    date: date
    nav: float


@dataclass
class FundDetail:
    scheme_code: int
    scheme_name: str
    scheme_type: str | None = None
    scheme_category: str | None = None
    amc: str | None = None
    fund_family: str | None = None
    isin: str | None = None
    isin_growth: str | None = None
    nav: float | None = None
    nav_date: date | None = None
    nav_history: list[NAVRecord] | None = None


class MutualFundProvider(ABC):
    @abstractmethod
    async def search_funds(self, query: str) -> list[FundSearchItem]: ...

    @abstractmethod
    async def get_all_funds(self) -> list[FundSearchItem]: ...

    @abstractmethod
    async def get_fund_detail(self, scheme_code: int) -> FundDetail | None: ...
