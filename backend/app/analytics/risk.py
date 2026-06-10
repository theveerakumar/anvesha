import numpy as np

from .returns import compute_daily_returns


def compute_std_dev(daily_returns: list[float], annualize: bool = True) -> float:
    if len(daily_returns) < 2:
        return 0.0
    std = float(np.std(daily_returns, ddof=1))
    if annualize:
        std *= np.sqrt(252)
    return round(std, 4)


def compute_beta(daily_returns: list[float], benchmark_returns: list[float]) -> float:
    if len(daily_returns) < 2 or len(benchmark_returns) < 2:
        return 0.0
    min_len = min(len(daily_returns), len(benchmark_returns))
    fund_rets = np.array(daily_returns[-min_len:])
    bench_rets = np.array(benchmark_returns[-min_len:])

    cov = np.cov(fund_rets, bench_rets)[0][1]
    var = np.var(bench_rets, ddof=1)
    if var == 0:
        return 0.0
    return round(float(cov / var), 4)


def compute_alpha(
    daily_returns: list[float],
    benchmark_returns: list[float],
    risk_free_rate: float = 6.0,
) -> float:
    beta = compute_beta(daily_returns, benchmark_returns)
    fund_annualized = float(np.mean(daily_returns)) * 252 * 100 if daily_returns else 0
    bench_annualized = (
        float(np.mean(benchmark_returns)) * 252 * 100 if benchmark_returns else 0
    )
    alpha = fund_annualized - (
        risk_free_rate + beta * (bench_annualized - risk_free_rate)
    )
    return round(alpha, 4)


def compute_sharpe_ratio(
    daily_returns: list[float],
    risk_free_rate: float = 6.0,
) -> float:
    if len(daily_returns) < 2:
        return 0.0
    excess_returns = np.array(daily_returns) - (risk_free_rate / (252 * 100))
    mean_excess = float(np.mean(excess_returns)) * 252
    std_excess = float(np.std(excess_returns, ddof=1)) * np.sqrt(252)
    if std_excess == 0:
        return 0.0
    return round(mean_excess / std_excess, 4)


def compute_sortino_ratio(
    daily_returns: list[float],
    risk_free_rate: float = 6.0,
) -> float:
    if len(daily_returns) < 2:
        return 0.0
    excess_returns = np.array(daily_returns) - (risk_free_rate / (252 * 100))
    mean_excess = float(np.mean(excess_returns)) * 252
    downside = excess_returns[excess_returns < 0]
    if len(downside) == 0:
        return 0.0
    downside_std = float(np.std(downside, ddof=1)) * np.sqrt(252)
    if downside_std == 0:
        return 0.0
    return round(mean_excess / downside_std, 4)


def compute_treynor_ratio(
    daily_returns: list[float],
    benchmark_returns: list[float],
    risk_free_rate: float = 6.0,
) -> float:
    beta = compute_beta(daily_returns, benchmark_returns)
    if beta == 0:
        return 0.0
    fund_annualized = float(np.mean(daily_returns)) * 252 * 100 if daily_returns else 0
    return round((fund_annualized - risk_free_rate) / beta, 4)


def compute_information_ratio(
    daily_returns: list[float],
    benchmark_returns: list[float],
) -> float:
    if len(daily_returns) < 2 or len(benchmark_returns) < 2:
        return 0.0
    min_len = min(len(daily_returns), len(benchmark_returns))
    fund_rets = np.array(daily_returns[-min_len:])
    bench_rets = np.array(benchmark_returns[-min_len:])
    excess = fund_rets - bench_rets
    mean_excess = float(np.mean(excess)) * 252
    tracking_error = float(np.std(excess, ddof=1)) * np.sqrt(252)
    if tracking_error == 0:
        return 0.0
    return round(mean_excess / tracking_error, 4)


def compute_risk_score(risk_metrics: dict) -> int:
    score = 50
    std_dev = risk_metrics.get("std_dev", 0)
    if std_dev > 30:
        score += 25
    elif std_dev > 20:
        score += 15
    elif std_dev > 10:
        score += 5
    elif std_dev < 5:
        score -= 15

    max_dd = risk_metrics.get("max_drawdown", 0)
    if abs(max_dd) > 40:
        score += 25
    elif abs(max_dd) > 25:
        score += 15
    elif abs(max_dd) > 15:
        score += 5
    elif abs(max_dd) < 8:
        score -= 10

    sharpe = risk_metrics.get("sharpe_ratio", 0)
    if sharpe > 2:
        score -= 20
    elif sharpe > 1:
        score -= 10
    elif sharpe > 0.5:
        score -= 5
    elif sharpe < 0:
        score += 15

    return max(0, min(100, score))


def classify_risk(score: int) -> str:
    if score <= 20:
        return "Very Low Risk"
    elif score <= 40:
        return "Low Risk"
    elif score <= 60:
        return "Moderate Risk"
    elif score <= 80:
        return "High Risk"
    else:
        return "Very High Risk"


def compute_all_risk_metrics(
    daily_returns: list[float],
    benchmark_returns: list[float] | None = None,
) -> dict:
    metrics = {
        "std_dev": compute_std_dev(daily_returns),
        "sharpe_ratio": compute_sharpe_ratio(daily_returns),
        "sortino_ratio": compute_sortino_ratio(daily_returns),
    }

    if benchmark_returns:
        metrics["beta"] = compute_beta(daily_returns, benchmark_returns)
        metrics["alpha"] = compute_alpha(daily_returns, benchmark_returns)
        metrics["treynor_ratio"] = compute_treynor_ratio(
            daily_returns, benchmark_returns
        )
        metrics["information_ratio"] = compute_information_ratio(
            daily_returns, benchmark_returns
        )
    else:
        metrics["beta"] = None
        metrics["alpha"] = None
        metrics["treynor_ratio"] = None
        metrics["information_ratio"] = None

    return metrics
