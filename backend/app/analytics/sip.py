from datetime import date, timedelta
import math


def compute_sip(
    monthly_amount: float,
    duration_years: int,
    annual_return: float,
) -> dict:
    total_months = duration_years * 12
    monthly_rate = annual_return / 100 / 12

    total_invested = monthly_amount * total_months

    if monthly_rate == 0:
        current_value = total_invested
    else:
        current_value = (
            monthly_amount
            * (((1 + monthly_rate) ** total_months - 1) / monthly_rate)
            * (1 + monthly_rate)
        )

    cagr = _compute_sip_cagr(total_invested, current_value, duration_years)

    return {
        "monthly_amount": monthly_amount,
        "duration_years": duration_years,
        "total_invested": round(total_invested, 2),
        "current_value": round(current_value, 2),
        "cagr": round(cagr, 2),
        "total_returns": round(current_value - total_invested, 2),
        "return_percentage": round(
            ((current_value - total_invested) / total_invested) * 100, 2
        )
        if total_invested > 0
        else 0,
    }


def compute_sip_stress_test(
    monthly_amount: float,
    duration_years: int,
    current_nav: float | None = None,
) -> dict:
    scenarios = {
        "bull": {
            "label": "Bull Market",
            "return_rate": 15.0,
            "description": "Strong economic growth, rising markets",
        },
        "bear": {
            "label": "Bear Market",
            "return_rate": -5.0,
            "description": "Economic downturn, falling markets",
        },
        "sideways": {
            "label": "Sideways Market",
            "return_rate": 3.0,
            "description": "Range-bound market, low volatility",
        },
    }

    results = {}
    for key, scenario in scenarios.items():
        sip_result = compute_sip(
            monthly_amount, duration_years, scenario["return_rate"]
        )
        results[key] = {
            "label": scenario["label"],
            "description": scenario["description"],
            **sip_result,
        }

    return {
        "monthly_amount": monthly_amount,
        "duration_years": duration_years,
        "scenarios": results,
    }


def compute_xirr(cash_flows: list[tuple[date, float]], guess: float = 0.1) -> float:
    if not cash_flows:
        return 0.0

    sorted_cfs = sorted(cash_flows, key=lambda x: x[0])
    start_date = sorted_cfs[0][0]

    def xirr_func(rate):
        result = 0.0
        for cf_date, cf_amount in sorted_cfs:
            days = (cf_date - start_date).days
            if days < 0:
                days = 0
            result += cf_amount / (1 + rate) ** (days / 365.0)
        return result

    rate = guess
    for _ in range(1000):
        f = xirr_func(rate)
        if abs(f) < 1e-7:
            break
        f_prime = 0.0
        for cf_date, cf_amount in sorted_cfs:
            days = (cf_date - start_date).days
            if days < 0:
                days = 0
            f_prime += -days / 365.0 * cf_amount / (1 + rate) ** (days / 365.0 + 1)
        if f_prime == 0:
            break
        rate = rate - f / f_prime

    return rate * 100


def _compute_sip_cagr(total_invested: float, current_value: float, years: int) -> float:
    if total_invested <= 0 or years <= 0:
        return 0.0
    ratio = current_value / total_invested
    if ratio <= 0:
        return 0.0
    return (ratio ** (1 / years) - 1) * 100
