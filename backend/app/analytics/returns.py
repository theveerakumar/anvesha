from datetime import date, datetime

import numpy as np
import pandas as pd


def calculate_absolute_return(start_nav: float, end_nav: float) -> float:
    if start_nav <= 0:
        return 0.0
    return ((end_nav - start_nav) / start_nav) * 100


def calculate_cagr(start_nav: float, end_nav: float, years: float) -> float:
    if start_nav <= 0 or years <= 0:
        return 0.0
    return ((end_nav / start_nav) ** (1 / years) - 1) * 100


def get_nav_at_date(
    nav_history: list[tuple[date, float]], target: date
) -> float | None:
    closest = None
    for nav_date, nav_val in nav_history:
        if nav_date <= target:
            closest = (nav_date, nav_val)
        else:
            break
    return closest[1] if closest else None


def compute_returns(nav_history: list[tuple[date, float]]) -> dict[str, float | None]:
    if not nav_history:
        return {}

    nav_history_sorted = sorted(nav_history, key=lambda x: x[0])
    latest_nav = nav_history_sorted[-1][1]
    latest_date = nav_history_sorted[-1][0]

    periods = {
        "return_1m": 30,
        "return_3m": 90,
        "return_6m": 180,
        "return_1y": 365,
    }

    result: dict[str, float | None] = {}

    for key, days in periods.items():
        target_date = latest_date - __import__("datetime").timedelta(days=days)
        nav_then = get_nav_at_date(nav_history_sorted, target_date)
        if nav_then and nav_then > 0:
            result[key] = round(calculate_absolute_return(nav_then, latest_nav), 2)
        else:
            result[key] = None

    cagr_periods = {
        "cagr_3y": 3,
        "cagr_5y": 5,
        "cagr_7y": 7,
        "cagr_10y": 10,
    }

    today = latest_date
    for key, years in cagr_periods.items():
        target_date = date(today.year - years, today.month, today.day)
        # Handle leap year edge cases
        try:
            target_date = target_date.replace(day=min(today.day, 28))
        except ValueError:
            target_date = date(target_date.year, target_date.month, 28)
        nav_then = get_nav_at_date(nav_history_sorted, target_date)
        if nav_then and nav_then > 0:
            result[key] = round(calculate_cagr(nav_then, latest_nav, years), 2)
        else:
            result[key] = None

    return result


def compute_daily_returns(nav_history: list[tuple[date, float]]) -> list[float]:
    navs = sorted(nav_history, key=lambda x: x[0])
    if len(navs) < 2:
        return []
    prices = [n[1] for n in navs]
    return [
        (prices[i] - prices[i - 1]) / prices[i - 1] * 100 for i in range(1, len(prices))
    ]


def compute_max_drawdown(nav_history: list[tuple[date, float]]) -> float:
    navs = sorted(nav_history, key=lambda x: x[0])
    if len(navs) < 2:
        return 0.0
    prices = [n[1] for n in navs]
    peak = prices[0]
    max_dd = 0.0
    for p in prices:
        if p > peak:
            peak = p
        dd = (peak - p) / peak * 100
        if dd > max_dd:
            max_dd = dd
    return round(max_dd, 2)
