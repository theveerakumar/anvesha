from .categorizer import classify, infer_category_group, infer_sub_category
from .holdings import generate_holdings
from .rating import compute_smart_rating
from .recommendation import generate_recommendation
from .returns import compute_max_drawdown, compute_returns, get_nav_at_date
from .rolling_returns import compute_max_drawdown_from_nav, compute_rolling_returns
from .scorer import FundMetrics, compute_composite_score
from .risk import (
    compute_all_risk_metrics,
    compute_beta,
    compute_daily_returns,
    compute_information_ratio,
    compute_risk_score,
    compute_sharpe_ratio,
    compute_sortino_ratio,
    compute_std_dev,
    classify_risk,
)
from .sip import compute_sip, compute_sip_stress_test, compute_xirr
from .swp import (
    compute_swp,
    compute_swp_longevity,
    compute_swp_max_withdrawal,
    compute_swp_stress_test,
)

__all__ = [
    "classify",
    "infer_category_group",
    "infer_sub_category",
    "compute_smart_rating",
    "generate_recommendation",
    "generate_holdings",
    "compute_max_drawdown",
    "compute_max_drawdown_from_nav",
    "compute_rolling_returns",
    "FundMetrics",
    "compute_composite_score",
    "compute_returns",
    "get_nav_at_date",
    "compute_all_risk_metrics",
    "compute_beta",
    "compute_daily_returns",
    "compute_information_ratio",
    "compute_risk_score",
    "compute_sharpe_ratio",
    "compute_sortino_ratio",
    "compute_std_dev",
    "classify_risk",
    "compute_sip",
    "compute_sip_stress_test",
    "compute_xirr",
    "compute_swp",
    "compute_swp_longevity",
    "compute_swp_max_withdrawal",
    "compute_swp_stress_test",
]
