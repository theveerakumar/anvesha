"""Compute future_return_indicator per fund from backtest results + component scores."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, text
from app.core.database import async_session_factory
from app.models.analytics import BacktestResult
from app.models.fund import Fund

# Map backtest factors to fund score columns
FACTOR_TO_SCORE = {
    "momentum_1y": "score_performance",
    "momentum_3y": "score_consistency",
    "scale": "score_scale",
    "cost": "score_cost",
}

DEFAULT_WEIGHTS = {
    "equity": {"momentum_1y": 0.15, "momentum_3y": 0.25, "scale": 0.50, "cost": 0.10},
    "hybrid": {"momentum_1y": 0.10, "momentum_3y": 0.25, "scale": 0.55, "cost": 0.10},
    "debt": {"momentum_1y": 0.40, "momentum_3y": 0.35, "scale": 0.15, "cost": 0.10},
    "index": {"momentum_1y": 0.30, "momentum_3y": 0.30, "scale": 0.20, "cost": 0.20},
    "gold_silver": {
        "momentum_1y": 0.50,
        "momentum_3y": 0.30,
        "scale": 0.10,
        "cost": 0.10,
    },
    "global": {"momentum_1y": 0.30, "momentum_3y": 0.30, "scale": 0.20, "cost": 0.20},
    "solution": {"momentum_1y": 0.25, "momentum_3y": 0.25, "scale": 0.25, "cost": 0.25},
    "other": {"momentum_1y": 0.25, "momentum_3y": 0.25, "scale": 0.25, "cost": 0.25},
}


async def load_backtest_weights(async_session) -> dict[str, dict[str, float]]:
    """Derive per-category factor weights from backtest predictive_power."""
    result = await async_session.execute(select(BacktestResult))
    bt_rows = result.scalars().all()

    weights: dict[str, dict[str, float]] = {}
    for r in bt_rows:
        group = r.category_group
        if group not in weights:
            weights[group] = {}
        pp = abs(r.predictive_power) if r.predictive_power else 0.0
        weights[group][r.factor_name] = pp

    # Normalize weights to sum to 1.0 per group
    for group in weights:
        total = sum(weights[group].values())
        if total > 0:
            for f in weights[group]:
                weights[group][f] /= total

    return weights


def compute(fund: Fund, weights: dict[str, float]) -> tuple[float | None, float | None]:
    """Compute future_return_indicator and backtest_confidence for one fund."""
    values = []
    confidences = []

    for factor, score_col in FACTOR_TO_SCORE.items():
        w = weights.get(factor, 0)
        if w <= 0:
            continue

        score_val = getattr(fund, score_col, None)
        if score_val is not None:
            # Normalize score to 0-1 if it's 0-100
            if score_val > 1:
                score_val = score_val / 100.0
            values.append(score_val * w)
            confidences.append(w)

    if not values:
        return None, None

    indicator = sum(values) * 100  # back to 0-100 scale
    confidence = sum(confidences)

    return round(min(indicator, 100), 1), round(min(confidence, 1.0), 3)


async def main():
    async with async_session_factory() as session:
        # Load backtest-derived weights
        bt_weights = await load_backtest_weights(session)
        print("Backtest-derived weights per category:")
        for group, fw in sorted(bt_weights.items()):
            print(f"  {group:10s}: ", end="")
            for factor, w in sorted(fw.items()):
                print(f"{factor}={w:.3f} ", end="")
            print()

        # Merge with defaults for categories without backtest data
        for group in DEFAULT_WEIGHTS:
            if group not in bt_weights:
                bt_weights[group] = DEFAULT_WEIGHTS[group]

        # Load all scored funds
        result = await session.execute(
            select(Fund).where(Fund.composite_score.isnot(None))
        )
        funds = result.scalars().all()
        print(f"\nFound {len(funds)} scored funds")

        updated = 0
        for fund in funds:
            group = fund.category_group or "other"
            weights = bt_weights.get(group, DEFAULT_WEIGHTS["other"])
            indicator, confidence = compute(fund, weights)
            if indicator is not None:
                fund.future_return_indicator = indicator
                fund.backtest_confidence = confidence
                updated += 1

        await session.commit()
        print(f"Updated {updated} funds with future_return_indicator")

        # Show top 10 by future_return_indicator
        result2 = await session.execute(
            select(Fund)
            .where(Fund.future_return_indicator.isnot(None))
            .order_by(Fund.future_return_indicator.desc())
            .limit(10)
        )
        top = result2.scalars().all()
        print("\nTop 10 funds by future_return_indicator:")
        for f in top:
            print(
                f"  {f.scheme_name[:55]:55s} "
                f"ind={f.future_return_indicator:5.1f} "
                f"conf={f.backtest_confidence:.2f} "
                f"score={f.composite_score:.0f} "
                f"group={f.category_group}"
            )


if __name__ == "__main__":
    asyncio.run(main())
