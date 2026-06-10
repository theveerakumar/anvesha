from datetime import date


def generate_recommendation(
    rating: dict,
    returns: dict,
    risk_metrics: dict,
    expense_ratio: float | None,
    scheme_name: str = "",
) -> dict:
    star_rating = rating["star_rating"]
    overall_score = rating["overall_score"]
    risk_level = risk_metrics.get("risk_level", "Moderate")
    max_dd = risk_metrics.get("max_drawdown", 0)
    sharpe = risk_metrics.get("sharpe_ratio", 0)
    cagr_3y = returns.get("cagr_3y")
    cagr_5y = returns.get("cagr_5y")
    return_1y = returns.get("return_1y")

    strengths = []
    weaknesses = []
    opportunities = []
    risks = []

    if star_rating >= 4:
        strengths.append("Strong overall SMART rating")
    if cagr_5y and cagr_5y > 10:
        strengths.append("Consistent long-term performance")
    if cagr_3y and cagr_3y > 12:
        strengths.append("Strong 3-year growth trajectory")
    if sharpe and sharpe > 1:
        strengths.append("Superior risk-adjusted returns")
    if max_dd and abs(max_dd) < 8:
        strengths.append("Excellent downside protection")
    if expense_ratio is not None and expense_ratio <= 0.5:
        strengths.append("Low expense ratio")
    if expense_ratio is not None and expense_ratio <= 0.3:
        strengths.append("Industry-leading low cost")

    if star_rating <= 2:
        weaknesses.append("Below-average SMART rating")
    if cagr_5y and cagr_5y < 5:
        weaknesses.append("Underperforming long-term benchmark")
    if cagr_3y and cagr_3y < 0:
        weaknesses.append("Negative 3-year returns")
    if max_dd and abs(max_dd) > 20:
        weaknesses.append("High historical drawdown")
    if sharpe is not None and sharpe < 0:
        weaknesses.append("Negative risk-adjusted returns")
    if expense_ratio is not None and expense_ratio > 2.0:
        weaknesses.append("High expense ratio")
    if return_1y and return_1y < 0:
        weaknesses.append("Negative 1-year return")

    if risk_level in ("Very Low Risk", "Low Risk"):
        opportunities.append("Stable performer suitable for conservative portfolios")
    elif risk_level in ("Moderate Risk",):
        opportunities.append("Balanced risk-reward profile")
    if sharpe and sharpe > 1.5:
        opportunities.append("Improving risk-adjusted efficiency")

    if risk_level in ("Very High Risk",):
        risks.append(
            "Extremely high volatility — not suitable for risk-averse investors"
        )
    if max_dd and abs(max_dd) > 25:
        risks.append("Excessive concentration risk or sector exposure")

    if star_rating >= 4:
        recommendation = "Strong Buy"
        confidence = min(95, 60 + overall_score * 0.35)
    elif star_rating >= 3:
        recommendation = "Buy"
        confidence = min(85, 50 + overall_score * 0.35)
    elif star_rating >= 2:
        recommendation = "Hold"
        confidence = min(65, 40 + overall_score * 0.25)
    elif star_rating >= 1:
        recommendation = "Watchlist"
        confidence = min(50, 30 + overall_score * 0.2)
    else:
        recommendation = "Avoid"
        confidence = min(40, 20 + overall_score * 0.2)

    confidence = round(confidence)

    reasoning_parts = []
    if star_rating >= 4:
        reasoning_parts.append(
            f"{scheme_name} has demonstrated strong performance with a SMART rating of {star_rating}/5 ({overall_score}/100)."
        )
        if cagr_5y:
            reasoning_parts.append(f"It has delivered {cagr_5y:.1f}% CAGR over 5 years")
        if sharpe:
            reasoning_parts.append(f"with a Sharpe ratio of {sharpe:.2f}")
        if expense_ratio is not None and expense_ratio <= 1.0:
            reasoning_parts.append(
                f"and a competitive expense ratio of {expense_ratio:.2f}%"
            )
        reasoning_parts.append(
            "making it a compelling investment option for suitable investors."
        )
    elif star_rating >= 3:
        reasoning_parts.append(
            f"{scheme_name} offers a balanced profile with a SMART rating of {star_rating}/5 ({overall_score}/100)."
        )
        if cagr_3y:
            reasoning_parts.append(f"It has generated {cagr_3y:.1f}% CAGR over 3 years")
        reasoning_parts.append(
            "and may be suitable for investors with aligned risk tolerance."
        )
    elif star_rating >= 2:
        reasoning_parts.append(
            f"{scheme_name} has a SMART rating of {star_rating}/5 ({overall_score}/100). "
            "Investors should monitor performance closely before increasing allocation."
        )
    else:
        reasoning_parts.append(
            f"Based on our analysis, {scheme_name} scores {overall_score}/100 on the SMART rating scale. "
            "Consider alternatives with stronger fundamentals and better risk-adjusted returns."
        )

    if risks:
        reasoning_parts.append(f"Key risk: {'; '.join(risks[:2])}.")

    reasoning = " ".join(reasoning_parts)

    return {
        "recommendation": recommendation,
        "confidence_score": confidence,
        "reasoning": reasoning,
        "strengths": "; ".join(strengths[:5]) if strengths else None,
        "weaknesses": "; ".join(weaknesses[:5]) if weaknesses else None,
        "opportunities": "; ".join(opportunities[:3]) if opportunities else None,
        "risks": "; ".join(risks[:3]) if risks else None,
    }
