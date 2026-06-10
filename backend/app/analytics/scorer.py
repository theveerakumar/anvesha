from dataclasses import dataclass


@dataclass
class FundMetrics:
    return_1y: float | None = None
    rolling_3y: float | None = None
    rolling_5y: float | None = None
    rolling_positive_pct: float | None = None
    rolling_upside_downside: float | None = None
    sharpe: float | None = None
    sortino: float | None = None
    max_drawdown: float | None = None
    rolling_std: float | None = None
    expense_ratio: float | None = None
    expense_ratio_peer_avg: float | None = None
    aum_cr: float | None = None
    fund_age_years: float | None = None
    aum_growth_1y: float | None = None


def _minmax(val: float | None, min_v: float, max_v: float) -> float:
    if val is None:
        return 50.0
    if max_v == min_v:
        return 50.0
    return max(0, min(100, (val - min_v) / (max_v - min_v) * 100))


def _zscore(val: float | None, mean: float, std: float) -> float:
    if val is None or std <= 0:
        return 50.0
    z = (val - mean) / std
    return max(0, min(100, (z * 15 + 50)))


def compute_composite_score(
    metrics: FundMetrics,
    peer_means: FundMetrics | None = None,
    peer_stds: FundMetrics | None = None,
    peer_bounds: dict[str, tuple[float, float]] | None = None,
) -> dict[str, float]:
    scores: dict[str, float] = {}

    bounds = peer_bounds or {}

    # Performance (35%)
    perf_scores = []
    perf_weights = [0.10, 0.075, 0.05, 0.075, 0.05]

    for metric, weight in zip(
        [
            "return_1y",
            "rolling_3y",
            "rolling_5y",
            "rolling_positive_pct",
            "rolling_upside_downside",
        ],
        perf_weights,
    ):
        val = getattr(metrics, metric, None)
        if val is not None:
            min_v, max_v = bounds.get(metric, (min(0, val), max(20, val)))
            if peer_means and peer_stds:
                s = _zscore(
                    val,
                    getattr(peer_means, metric, 0) or 0,
                    getattr(peer_stds, metric, 1) or 1,
                )
            else:
                s = _minmax(val, min_v, max_v)
            perf_scores.append(s * weight)

    weights_sum = sum(
        w
        for w, v in zip(
            perf_weights,
            [
                metrics.return_1y,
                metrics.rolling_3y,
                metrics.rolling_5y,
                metrics.rolling_positive_pct,
                metrics.rolling_upside_downside,
            ],
        )
        if v is not None
    )
    scores["score_performance"] = round(
        sum(perf_scores) / weights_sum if perf_scores and weights_sum > 0 else 50, 1
    )

    # Risk (25%)
    risk_scores = []
    risk_weights = [0.08, 0.05, 0.05, 0.04, 0.03]

    # Sharpe: higher is better
    if metrics.sharpe is not None:
        s_min, s_max = bounds.get("sharpe", (-1, 3))
        risk_scores.append(_minmax(metrics.sharpe, s_min, s_max) * 0.08)

    # Sortino: higher is better
    if metrics.sortino is not None:
        so_min, so_max = bounds.get("sortino", (-0.5, 5))
        risk_scores.append(_minmax(metrics.sortino, so_min, so_max) * 0.05)

    # Max drawdown: lower (less negative) is better → invert
    if metrics.max_drawdown is not None:
        dd_min, dd_max = bounds.get("max_drawdown", (-60, 0))
        risk_scores.append(
            (1 - _minmax(abs(metrics.max_drawdown), 0, abs(dd_min)) / 100) * 100 * 0.05
        )

    # Rolling std: lower (more stable) is better → invert
    if metrics.rolling_std is not None:
        std_min, std_max = bounds.get("rolling_std", (5, 40))
        risk_scores.append(
            (1 - _minmax(metrics.rolling_std, std_min, std_max) / 100) * 100 * 0.04
        )

    scores["score_risk"] = round(
        (
            sum(risk_scores) / sum(risk_weights[: len(risk_scores)])
            if risk_scores
            else 50
        ),
        1,
    )

    # Consistency (15%)
    cons_scores = []
    if metrics.rolling_positive_pct is not None:
        cons_scores.append(metrics.rolling_positive_pct * 0.05)

    # Rolling return stability (low std dev of rolling returns = consistent)
    if metrics.rolling_3y is not None and metrics.rolling_5y is not None:
        spread = abs(metrics.rolling_3y - metrics.rolling_5y)
        cons_scores.append(max(0, 100 - spread * 2) * 0.05)
        cons_scores.append(max(0, 100 - spread * 1.5) * 0.05)

    scores["score_consistency"] = round(
        (sum(cons_scores) / 0.15 if cons_scores else 50), 1
    )

    # Cost (15%)
    cost_scores = []

    # Expense ratio: lower is better
    if metrics.expense_ratio is not None:
        if (
            metrics.expense_ratio_peer_avg is not None
            and metrics.expense_ratio_peer_avg > 0
        ):
            ratio = metrics.expense_ratio / metrics.expense_ratio_peer_avg
            cost_scores.append(max(0, min(100, (2 - ratio) * 50)) * 0.08)
        else:
            er_min, er_max = bounds.get("expense_ratio", (0.1, 2.5))
            cost_scores.append(
                (1 - _minmax(metrics.expense_ratio, er_min, er_max) / 100) * 100 * 0.08
            )

    # Fund age adds cost credibility
    if metrics.fund_age_years is not None and metrics.fund_age_years >= 3:
        cost_scores.append(min(metrics.fund_age_years / 10 * 100, 100) * 0.04)
    elif metrics.fund_age_years is not None:
        cost_scores.append(metrics.fund_age_years / 3 * 100 * 0.04)

    scores["score_cost"] = round(
        (sum(cost_scores) / sum([0.08, 0.04]) if cost_scores else 50), 1
    )

    # Scale (10%)
    scale_scores = []

    if metrics.aum_cr is not None:
        aum_min, aum_max = bounds.get("aum_cr", (10, 50000))
        scale_scores.append(_minmax(metrics.aum_cr, aum_min, aum_max) * 0.04)

    if metrics.aum_growth_1y is not None:
        growth_min, growth_max = bounds.get("aum_growth_1y", (-50, 200))
        scale_scores.append(
            _minmax(metrics.aum_growth_1y, growth_min, growth_max) * 0.03
        )

    if metrics.fund_age_years is not None:
        scale_scores.append(min(metrics.fund_age_years / 10 * 100, 100) * 0.03)

    scores["score_scale"] = round((sum(scale_scores) / 0.10 if scale_scores else 50), 1)

    # Composite
    composite = (
        scores.get("score_performance", 50) * 0.35
        + scores.get("score_risk", 50) * 0.25
        + scores.get("score_consistency", 50) * 0.15
        + scores.get("score_cost", 50) * 0.15
        + scores.get("score_scale", 50) * 0.10
    )
    scores["composite_score"] = round(composite, 1)

    return scores
