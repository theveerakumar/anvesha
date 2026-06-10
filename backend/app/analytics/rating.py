from datetime import date

from ..analytics.returns import compute_max_drawdown, compute_returns
from ..analytics.risk import (
    classify_risk,
    compute_all_risk_metrics,
    compute_daily_returns,
    compute_risk_score,
)


def compute_smart_rating(
    returns: dict,
    risk_metrics: dict,
    expense_ratio: float | None,
    nav_history: list[tuple[date, float]],
) -> dict:
    performance_score = _compute_performance_score(returns)
    consistency_score = _compute_consistency_score(nav_history)
    risk_s = _compute_risk_score_component(risk_metrics)
    cost_score = _compute_cost_score(expense_ratio)
    portfolio_score = _compute_portfolio_quality_score(returns, risk_metrics)

    overall = (
        performance_score * 0.35
        + consistency_score * 0.15
        + risk_s * 0.25
        + cost_score * 0.10
        + portfolio_score * 0.15
    )

    overall = max(0, min(100, overall))

    stars = _score_to_stars(overall)

    return {
        "star_rating": stars,
        "overall_score": round(overall, 1),
        "performance_score": round(performance_score, 1),
        "consistency_score": round(consistency_score, 1),
        "risk_score": round(risk_s, 1),
        "cost_score": round(cost_score, 1),
        "portfolio_quality_score": round(portfolio_score, 1),
    }


def _compute_performance_score(returns: dict) -> float:
    score = 50
    cagr_3y = returns.get("cagr_3y")
    cagr_5y = returns.get("cagr_5y")
    return_1y = returns.get("return_1y")

    if cagr_5y and cagr_5y > 15:
        score += 20
    elif cagr_5y and cagr_5y > 10:
        score += 10
    elif cagr_5y and cagr_5y > 5:
        score += 5
    elif cagr_5y and cagr_5y < 0:
        score -= 15

    if cagr_3y and cagr_3y > 18:
        score += 15
    elif cagr_3y and cagr_3y > 12:
        score += 10
    elif cagr_3y and cagr_3y > 8:
        score += 5
    elif cagr_3y and cagr_3y < 0:
        score -= 10

    if return_1y and return_1y > 25:
        score += 10
    elif return_1y and return_1y > 15:
        score += 5
    elif return_1y and return_1y < -10:
        score -= 10

    return max(0, min(100, score))


def _compute_consistency_score(nav_history: list[tuple[date, float]]) -> float:
    if len(nav_history) < 252:
        return 50

    sorted_navs = sorted(nav_history, key=lambda x: x[0])
    prices = [n[1] for n in sorted_navs]

    positive_periods = 0
    total_periods = max(1, len(prices) - 1)

    for i in range(1, len(prices)):
        if prices[i] >= prices[i - 1]:
            positive_periods += 1

    consistency_ratio = positive_periods / total_periods
    score = consistency_ratio * 100

    return max(0, min(100, score))


def _compute_risk_score_component(risk_metrics: dict) -> float:
    score = 50
    sharpe = risk_metrics.get("sharpe_ratio", 0)
    sortino = risk_metrics.get("sortino_ratio", 0)
    max_dd = risk_metrics.get("max_drawdown", 0)

    if sharpe and sharpe > 2:
        score += 20
    elif sharpe and sharpe > 1:
        score += 10
    elif sharpe and sharpe > 0.5:
        score += 5
    elif sharpe and sharpe < 0:
        score -= 20

    if sortino and sortino > 3:
        score += 10
    elif sortino and sortino > 1.5:
        score += 5
    elif sortino and sortino < 0:
        score -= 10

    if max_dd and abs(max_dd) < 5:
        score += 15
    elif max_dd and abs(max_dd) < 10:
        score += 10
    elif max_dd and abs(max_dd) < 20:
        score += 5
    elif max_dd and abs(max_dd) > 30:
        score -= 15

    return max(0, min(100, score))


def _compute_cost_score(expense_ratio: float | None) -> float:
    if expense_ratio is None:
        return 50
    if expense_ratio <= 0.3:
        return 90
    elif expense_ratio <= 0.5:
        return 80
    elif expense_ratio <= 0.8:
        return 70
    elif expense_ratio <= 1.0:
        return 60
    elif expense_ratio <= 1.5:
        return 50
    elif expense_ratio <= 2.0:
        return 35
    elif expense_ratio <= 2.5:
        return 20
    else:
        return 10


def _compute_portfolio_quality_score(returns: dict, risk_metrics: dict) -> float:
    score = 60
    max_dd = risk_metrics.get("max_drawdown", 0)
    sharpe = risk_metrics.get("sharpe_ratio", 0)

    if max_dd and abs(max_dd) < 5:
        score += 15
    elif max_dd and abs(max_dd) > 25:
        score -= 15

    if sharpe and sharpe > 1.5:
        score += 15
    elif sharpe and sharpe < 0:
        score -= 15

    cagr_5y = returns.get("cagr_5y")
    cagr_3y = returns.get("cagr_3y")
    if cagr_5y and cagr_3y and cagr_3y >= cagr_5y:
        score += 10

    return max(0, min(100, score))


def _score_to_stars(score: float) -> int:
    if score >= 80:
        return 5
    elif score >= 60:
        return 4
    elif score >= 40:
        return 3
    elif score >= 20:
        return 2
    else:
        return 1
