"""Recommendation engine — research analyst grade.

SWP: prioritises capital preservation, consistency, and downside protection.
SIP: prioritises long-term growth, performance, and future potential.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


SWP_SUB_CATEGORIES = (
    "large_cap",
    "flexi_cap",
)

SWP_DEBT_CATEGORIES = (
    "Debt Scheme - Liquid Fund",
    "Debt Scheme - Ultra Short Duration Fund",
    "Debt Scheme - Short Duration Fund",
    "Debt Scheme - Low Duration Fund",
    "Debt Scheme - Overnight Fund",
    "Debt Scheme - Money Market Fund",
    "Debt Scheme - Corporate Bond Fund",
    "Debt Scheme - Banking and PSU Fund",
)

SIP_CATEGORIES = (
    "equity",
    "hybrid",
)

SIP_EXCLUDE_SUB_CATEGORIES = (
    "sectoral",
    "dividend_yield",
)


async def recommend_swp(db: AsyncSession, limit: int = 5) -> list[dict]:
    """Top N funds for SWP — stable, consistent, capital-preserving."""
    debt_cats_escaped = ", ".join(
        f"'{c.replace(chr(39), chr(39) + chr(39))}'" for c in SWP_DEBT_CATEGORIES
    )
    equity_subs = ", ".join(f"'{g}'" for g in SWP_SUB_CATEGORIES)

    rows = await db.execute(
        text(f"""
            WITH scored AS (
                SELECT
                    scheme_code, scheme_name, sub_category, category_group,
                    composite_score, rolling_return_3y_avg,
                    rolling_return_positive_pct, risk_level, aum_cr,
                    expense_ratio, score_consistency, score_cost,
                    rolling_return_1y_min, rolling_return_5y_avg,
                    ROUND((
                        COALESCE(rolling_return_positive_pct, 0) * 0.30
                        + COALESCE(score_consistency, 0) * 0.25
                        + GREATEST(COALESCE(rolling_return_3y_avg, 0), 0) * 1.5
                        + GREATEST(100 + COALESCE(rolling_return_1y_min, -100), 0) * 0.15
                        + COALESCE(score_cost, 0) * 0.15
                    )::numeric, 1) AS rec_score
                FROM funds
                WHERE composite_score IS NOT NULL
                  AND rolling_return_3y_avg IS NOT NULL
                  AND (
                      sub_category IN ({equity_subs})
                      OR category_group = 'hybrid'
                      OR (category_group = 'debt' AND scheme_category IN ({debt_cats_escaped}))
                  )
            )
            SELECT * FROM scored
            ORDER BY rec_score DESC
            LIMIT {limit}
        """)
    )
    results = []
    for r in rows.all():
        results.append(
            {
                "scheme_code": r[0],
                "scheme_name": r[1],
                "sub_category": r[2],
                "category_group": r[3],
                "composite_score": round(r[4], 1) if r[4] else None,
                "rolling_return_3y_avg": round(r[5], 2) if r[5] else None,
                "rolling_return_positive_pct": round(r[6], 1) if r[6] else None,
                "risk_level": r[7],
                "aum_cr": round(r[8], 1) if r[8] else None,
                "expense_ratio": round(r[9], 3) if r[9] else None,
                "rolling_return_5y_avg": round(r[13], 2) if r[13] else None,
                "rec_score": r[14],
            }
        )
    return results


async def recommend_sip(db: AsyncSession, limit: int = 5) -> list[dict]:
    """Top N funds for SIP — growth-oriented, consistent, high-potential."""
    equity_groups = ", ".join(f"'{g}'" for g in SIP_CATEGORIES)
    exclude_subs = ", ".join(f"'{c}'" for c in SIP_EXCLUDE_SUB_CATEGORIES)

    rows = await db.execute(
        text(f"""
            WITH scored AS (
                SELECT
                    scheme_code, scheme_name, sub_category, category_group,
                    composite_score, rolling_return_3y_avg,
                    rolling_return_positive_pct, risk_level, aum_cr,
                    expense_ratio, score_performance, future_return_indicator,
                    score_consistency, rolling_return_5y_avg,
                    ROUND((
                        COALESCE(score_performance, 0) * 0.30
                        + GREATEST(COALESCE(rolling_return_5y_avg, 0), 0) * 1.5
                        + COALESCE(future_return_indicator, 0) * 0.20
                        + COALESCE(rolling_return_positive_pct, 0) * 0.15
                        + COALESCE(score_consistency, 0) * 0.15
                    )::numeric, 1) AS rec_score
                FROM funds
                WHERE composite_score IS NOT NULL
                  AND score_performance IS NOT NULL
                  AND rolling_return_3y_avg IS NOT NULL
                  AND category_group IN ({equity_groups})
                  AND (sub_category IS NULL OR sub_category NOT IN ({exclude_subs}))
            )
            SELECT * FROM scored
            ORDER BY rec_score DESC
            LIMIT {limit}
        """)
    )
    results = []
    for r in rows.all():
        results.append(
            {
                "scheme_code": r[0],
                "scheme_name": r[1],
                "sub_category": r[2],
                "category_group": r[3],
                "composite_score": round(r[4], 1) if r[4] else None,
                "rolling_return_3y_avg": round(r[5], 2) if r[5] else None,
                "rolling_return_positive_pct": round(r[6], 1) if r[6] else None,
                "risk_level": r[7],
                "aum_cr": round(r[8], 1) if r[8] else None,
                "expense_ratio": round(r[9], 3) if r[9] else None,
                "rolling_return_5y_avg": round(r[13], 2) if r[13] else None,
                "rec_score": r[14],
            }
        )
    return results
