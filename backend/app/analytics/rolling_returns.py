import math
from datetime import date, timedelta
from typing import Any


def compute_cagr(start_nav: float, end_nav: float, days: float) -> float | None:
    if start_nav <= 0 or end_nav <= 0 or days <= 0:
        return None
    years = days / 365.25
    if years <= 0:
        return None
    return (end_nav / start_nav) ** (1 / years) - 1


def compute_rolling_returns(
    nav_history: list[tuple[date, float]],
    windows: list[int] = [1, 3, 5],
) -> dict[str, Any]:
    if not nav_history or len(nav_history) < 60:
        return {
            "rolling_return_1y_avg": None,
            "rolling_return_3y_avg": None,
            "rolling_return_5y_avg": None,
            "rolling_window_count": 0,
            "rolling_return_positive_pct": None,
        }

    sorted_nav = sorted(nav_history, key=lambda x: x[0])
    result: dict[str, Any] = {}
    all_positive = True
    total_windows = 0

    for window_years in windows:
        window_days = window_years * 365
        returns: list[float] = []

        for i in range(len(sorted_nav)):
            start_date, start_nav = sorted_nav[i]
            target_date = start_date + timedelta(days=window_days)

            # Find the NAV closest to target_date (within 30 days tolerance)
            end_idx = None
            for j in range(i + 1, len(sorted_nav)):
                if sorted_nav[j][0] >= target_date:
                    end_idx = j
                    break
            if end_idx is None:
                break

            end_date, end_nav = sorted_nav[end_idx]
            actual_days = (end_date - start_date).days
            if actual_days < window_days - 30:
                continue

            cagr = compute_cagr(start_nav, end_nav, float(actual_days))
            if cagr is not None:
                returns.append(cagr)

        if returns:
            returns.sort()
            n = len(returns)
            avg = sum(returns) / n
            result[f"rolling_return_{window_years}y_avg"] = round(avg * 100, 2)
            result[f"rolling_return_{window_years}y_max"] = round(returns[-1] * 100, 2)
            result[f"rolling_return_{window_years}y_min"] = round(returns[0] * 100, 2)
            positive = sum(1 for r in returns if r > 0)
            if window_years == 1:
                total_windows = n
                all_positive = positive == n
        else:
            result[f"rolling_return_{window_years}y_avg"] = None
            result[f"rolling_return_{window_years}y_max"] = None
            result[f"rolling_return_{window_years}y_min"] = None

    result["rolling_window_count"] = total_windows
    result["rolling_return_positive_pct"] = round(
        sum(1 for r in [] if r > 0) / max(total_windows, 1) * 100, 1
    )

    # Recompute positive pct properly
    pos_count = 0
    total = 0
    for w in windows:
        avg_key = f"rolling_return_{w}y_avg"
        if avg_key in result and result[avg_key] is not None:
            total += 1
            if result[avg_key] > 0:
                pos_count += 1
    result["rolling_return_positive_pct"] = round(pos_count / max(total, 1) * 100, 1)

    return result


def compute_max_drawdown_from_nav(
    nav_history: list[tuple[date, float]],
) -> float | None:
    if not nav_history:
        return None
    sorted_nav = sorted(nav_history, key=lambda x: x[0])
    peak = sorted_nav[0][1]
    max_dd = 0.0
    for _, nav_val in sorted_nav:
        if nav_val > peak:
            peak = nav_val
        dd = (peak - nav_val) / peak * 100
        if dd > max_dd:
            max_dd = dd
    return round(max_dd, 2)
