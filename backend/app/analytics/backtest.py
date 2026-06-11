"""Backtesting engine for factor predictive power analysis.

Tests whether various factors (momentum, cost, scale, consistency)
predict future returns in mutual funds.

For each factor x category_group x forward_window combination,
computes:
  - predictive_power: correlation between factor and forward return
  - direction: "positive" or "negative"
  - avg_top_quintile_fwd: mean forward return of top quintile
  - avg_bottom_quintile_fwd: mean forward return of bottom quintile
  - spread: top - bottom quintile difference
  - hit_rate: % of eval periods where top quintile beats bottom
  - observation_count: number of eval periods
"""

import numpy as np
import pandas as pd
from datetime import date, timedelta
from typing import Any

FACTOR_DEFINITIONS = {
    "momentum_1y": {
        "label": "1-Year Momentum",
        "description": "Past 1-year return as predictor",
        "direction": "positive",
    },
    "momentum_3y": {
        "label": "3-Year Momentum",
        "description": "Past 3-year rolling avg return as predictor",
        "direction": "positive",
    },
    "cost": {
        "label": "Expense Ratio",
        "description": "Lower expense ratio predicts higher returns",
        "direction": "negative",
    },
    "scale": {
        "label": "AUM Scale",
        "description": "Fund size as predictor",
        "direction": "positive",
    },
}

FORWARD_WINDOWS = [180, 365]  # 6-month, 12-month forward returns


def compute_factors_at_point(
    nav_history: list[tuple[date, float]],
    eval_date: date,
) -> dict[str, float | None]:
    """Compute factor values for a fund at a given evaluation date."""
    navs = [(d, n) for d, n in nav_history if d <= eval_date]
    if len(navs) < 60:
        return {}

    df = pd.DataFrame(navs, columns=["date", "nav"]).set_index("date").sort_index()
    latest_nav = df["nav"].iloc[-1]

    factors: dict[str, float | None] = {}

    # Momentum 1y: NAV at eval_date vs NAV ~1 year prior
    lookback_1y = eval_date - timedelta(days=365)
    before_1y = df[df.index <= lookback_1y]
    if len(before_1y) > 0:
        nav_1y_ago = before_1y["nav"].iloc[-1]
        if nav_1y_ago > 0:
            factors["momentum_1y"] = (latest_nav / nav_1y_ago) - 1

    # Forward returns (computed from future data)
    future = [(d, n) for d, n in nav_history if d > eval_date]
    if future:
        future_df = (
            pd.DataFrame(future, columns=["date", "nav"]).set_index("date").sort_index()
        )
        for fwd_days in FORWARD_WINDOWS:
            target = eval_date + timedelta(days=fwd_days)
            fwd = future_df[future_df.index <= target + timedelta(days=15)]
            if len(fwd) > 0:
                fwd_return = (fwd["nav"].iloc[-1] / latest_nav) - 1
                factors[f"fwd_{fwd_days}d"] = fwd_return

    # Rolling return stability (consistency proxy)
    if len(navs) >= 365:
        rolling_rets = []
        step = 21
        for i in range(0, len(navs) - 252, step):
            start_nav = navs[i][1]
            end_nav = navs[i + 252][1] if i + 252 < len(navs) else navs[-1][1]
            if start_nav > 0:
                rolling_rets.append((end_nav / start_nav) - 1)
        if rolling_rets:
            factors["consistency"] = 1.0 - (
                np.std(rolling_rets) / max(abs(np.mean(rolling_rets)), 0.001)
            )

    return factors


def backtest_category_group(
    fund_data: list[dict[str, Any]],
    factor_name: str,
    category_group: str,
    forward_days: int = 365,
    min_funds_per_date: int = 10,
) -> dict[str, Any]:
    """Run backtest for a single factor within a category group.

    Args:
        fund_data: List of dicts with keys 'id', 'scheme_code',
                   'nav_history', 'expense_ratio', 'aum_cr'
        factor_name: Key in FACTOR_DEFINITIONS
        category_group: Name of category group
        forward_days: Forward return window in days
        min_funds_per_date: Minimum funds needed at an eval date

    Returns:
        dict with backtest results
    """
    for fund in fund_data:
        nav_list = fund.get("nav_history", [])
        if not nav_list:
            fund["_monthly"] = pd.DataFrame()
            continue

        df = pd.DataFrame(nav_list, columns=["date", "nav"])
        df["date"] = pd.to_datetime(df["date"])
        df = df.drop_duplicates(subset=["date"]).sort_values("date")
        monthly = df.set_index("date").resample("ME").last().dropna()
        monthly["nav"] = monthly["nav"].astype(float)
        monthly["fund_id"] = fund["id"]

        monthly["past_1y"] = (
            monthly["nav"] / monthly["nav"].shift(12).replace(0, np.nan) - 1
        )
        monthly["past_3y_avg"] = (
            monthly["nav"]
            .rolling(36, min_periods=12)
            .apply(
                lambda x: (x.iloc[-1] / x.iloc[0]) ** (1 / 3) - 1
                if x.iloc[0] > 0
                else np.nan,
                raw=False,
            )
        )
        fwd_nav = monthly["nav"].shift(-forward_days // 30)
        monthly[f"fwd_{forward_days}d"] = (
            fwd_nav / monthly["nav"].replace(0, np.nan) - 1
        )

        monthly["expense_ratio"] = fund.get("expense_ratio")
        monthly["aum_cr"] = fund.get("aum_cr")

        fund["_monthly"] = monthly

    monthly_all = pd.concat(
        [f["_monthly"] for f in fund_data if not f["_monthly"].empty]
    )

    if monthly_all.empty:
        return empty_result(factor_name, category_group, forward_days)

    monthly_all = monthly_all.reset_index()
    monthly_all = monthly_all.dropna(subset=[f"fwd_{forward_days}d"])

    def get_factor(grp):
        if factor_name == "momentum_1y":
            return grp["past_1y"].dropna()
        elif factor_name == "momentum_3y":
            return grp["past_3y_avg"].dropna()
        elif factor_name == "cost":
            return grp["expense_ratio"].dropna() * -1
        elif factor_name == "scale":
            return grp["aum_cr"].dropna()
        return grp.get("past_1y", pd.Series(dtype=float)).dropna()

    eval_periods = []
    for eval_date, group in monthly_all.groupby("date"):
        factor_vals = get_factor(group)
        fwd_rets = group.loc[factor_vals.index, f"fwd_{forward_days}d"]

        if len(factor_vals) < min_funds_per_date:
            continue

        try:
            quintiles = (
                pd.qcut(
                    factor_vals.rank(method="first"), 5, labels=False, duplicates="drop"
                )
                + 1
            )
        except ValueError:
            continue

        q1_mask = quintiles == 1
        q5_mask = quintiles == quintiles.max()

        if q1_mask.sum() == 0 or q5_mask.sum() == 0:
            continue

        q1_fwd = fwd_rets[q1_mask].replace([np.inf, -np.inf], np.nan).mean()
        q5_fwd = fwd_rets[q5_mask].replace([np.inf, -np.inf], np.nan).mean()

        if np.isnan(q1_fwd) or np.isnan(q5_fwd):
            continue

        eval_periods.append(
            {
                "eval_date": eval_date,
                "q1_fwd": q1_fwd,
                "q5_fwd": q5_fwd,
                "q1_count": int(q1_mask.sum()),
                "q5_count": int(q5_mask.sum()),
            }
        )

    if not eval_periods:
        return empty_result(factor_name, category_group, forward_days)

    ep_df = pd.DataFrame(eval_periods)

    direction = FACTOR_DEFINITIONS.get(factor_name, {}).get("direction", "positive")

    q1_avg = float(ep_df["q1_fwd"].mean())
    q5_avg = float(ep_df["q5_fwd"].mean())

    if direction == "positive":
        top_avg = q5_avg
        bot_avg = q1_avg
        spread = q5_avg - q1_avg
        hits = (ep_df["q5_fwd"] > ep_df["q1_fwd"]).sum()
    else:
        top_avg = q1_avg
        bot_avg = q5_avg
        spread = q1_avg - q5_avg
        hits = (ep_df["q1_fwd"] > ep_df["q5_fwd"]).sum()

    hit_rate = hits / len(ep_df)

    spread_series = ep_df["q5_fwd"] - ep_df["q1_fwd"]
    spread_std = float(spread_series.std())
    pred_power = round(float(spread) / spread_std, 4) if spread_std > 0 else 0.0

    return {
        "factor_name": factor_name,
        "category_group": category_group,
        "forward_days": forward_days,
        "predictive_power": round(pred_power, 4),
        "direction": direction,
        "avg_top_quintile_fwd": round(float(top_avg) * 100, 2),
        "avg_bottom_quintile_fwd": round(float(bot_avg) * 100, 2),
        "spread": round(float(spread) * 100, 2),
        "hit_rate": round(float(hit_rate), 4),
        "observation_count": len(eval_periods),
    }


def empty_result(
    factor_name: str, category_group: str, forward_days: int
) -> dict[str, Any]:
    return {
        "factor_name": factor_name,
        "category_group": category_group,
        "forward_days": forward_days,
        "predictive_power": 0.0,
        "direction": "neutral",
        "avg_top_quintile_fwd": 0.0,
        "avg_bottom_quintile_fwd": 0.0,
        "spread": 0.0,
        "hit_rate": 0.0,
        "observation_count": 0,
    }
