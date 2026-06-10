from datetime import date
from pydantic import BaseModel


class ReturnsResponse(BaseModel):
    scheme_code: int
    scheme_name: str
    return_1m: float | None = None
    return_3m: float | None = None
    return_6m: float | None = None
    return_1y: float | None = None
    cagr_3y: float | None = None
    cagr_5y: float | None = None
    cagr_7y: float | None = None
    cagr_10y: float | None = None
    max_drawdown: float | None = None


class RiskMetricsResponse(BaseModel):
    scheme_code: int
    scheme_name: str
    std_dev: float | None = None
    beta: float | None = None
    alpha: float | None = None
    sharpe_ratio: float | None = None
    sortino_ratio: float | None = None
    treynor_ratio: float | None = None
    information_ratio: float | None = None
    max_drawdown: float | None = None
    risk_score: int | None = None
    risk_level: str | None = None


class NAVPoint(BaseModel):
    date: str
    nav: float


class NAVHistoryResponse(BaseModel):
    scheme_code: int
    scheme_name: str
    nav_history: list[NAVPoint]


class CategoryFundSummary(BaseModel):
    scheme_code: int
    scheme_name: str
    nav: float | None = None
    return_1y: float | None = None
    cagr_3y: float | None = None
    cagr_5y: float | None = None
    expense_ratio: float | None = None
    aum_cr: float | None = None
    sharpe_ratio: float | None = None
    risk_level: str | None = None


class CategoryResponse(BaseModel):
    category: str
    total_funds: int
    avg_return_1y: float | None = None
    avg_cagr_3y: float | None = None
    avg_cagr_5y: float | None = None
    top_funds: list[CategoryFundSummary] = []


class FundDetailResponse(BaseModel):
    fund: dict
    returns: ReturnsResponse
    risk: RiskMetricsResponse
    nav_history: NAVHistoryResponse
