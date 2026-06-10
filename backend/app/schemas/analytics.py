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


class RatingResponse(BaseModel):
    scheme_code: int
    scheme_name: str
    star_rating: int
    overall_score: float
    performance_score: float | None = None
    consistency_score: float | None = None
    risk_score: float | None = None
    cost_score: float | None = None
    portfolio_quality_score: float | None = None


class RecommendationResponse(BaseModel):
    scheme_code: int
    scheme_name: str
    recommendation: str
    confidence_score: float
    reasoning: str
    strengths: str | None = None
    weaknesses: str | None = None
    opportunities: str | None = None
    risks: str | None = None


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
    returns: ReturnsResponse | None = None
    risk: RiskMetricsResponse | None = None
    rating: RatingResponse | None = None
    recommendation: RecommendationResponse | None = None
    nav_history: NAVHistoryResponse | None = None


class CompareFundRow(BaseModel):
    metric: str
    values: dict[str, str]
    winner: str | None = None


class CompareResponse(BaseModel):
    schemes: list[int]
    funds: list[dict]
    comparison: list[CompareFundRow]


class OverlapHolding(BaseModel):
    stock: str
    sector: str | None = None
    weight_a: float | None = None
    weight_b: float | None = None


class OverlapResponse(BaseModel):
    scheme_code_a: int
    scheme_name_a: str
    scheme_code_b: int
    scheme_name_b: str
    common_holdings: list[OverlapHolding]
    overlap_percentage: float
    diversification_score: int
