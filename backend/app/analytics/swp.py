"""SWP (Systematic Withdrawal Plan) calculations."""

import math


def compute_swp(
    corpus: float,
    monthly_withdrawal: float,
    annual_return: float,
    duration_years: int,
) -> dict:
    monthly_rate = annual_return / 100 / 12
    total_months = duration_years * 12
    balance = corpus
    yearly_snapshots = []

    for year in range(1, duration_years + 1):
        start_balance = balance
        annual_withdrawn = 0.0
        for _ in range(12):
            if balance <= 0:
                break
            balance = balance * (1 + monthly_rate) - monthly_withdrawal
            annual_withdrawn += monthly_withdrawal
            if balance <= 0:
                balance = 0.0
                break

        returns_earned = (balance + annual_withdrawn) - start_balance
        yearly_snapshots.append(
            {
                "year": year,
                "start_balance": round(start_balance, 2),
                "annual_withdrawn": round(annual_withdrawn, 2),
                "returns_earned": round(returns_earned, 2),
                "end_balance": round(balance, 2),
            }
        )
        if balance <= 0:
            break

    total_withdrawn = sum(s["annual_withdrawn"] for s in yearly_snapshots)
    total_returns = total_withdrawn + balance - corpus

    return {
        "corpus": round(corpus, 2),
        "monthly_withdrawal": round(monthly_withdrawal, 2),
        "annual_return": annual_return,
        "duration_years": duration_years,
        "total_withdrawn": round(total_withdrawn, 2),
        "final_value": round(balance, 2),
        "total_returns": round(total_returns, 2),
        "yearly_snapshots": yearly_snapshots,
    }


def compute_swp_longevity(
    corpus: float,
    monthly_withdrawal: float,
    annual_return: float,
    max_years: int = 100,
) -> dict:
    monthly_rate = annual_return / 100 / 12
    balance = corpus
    month = 0
    annual_projections = []

    for year in range(1, max_years + 1):
        start_balance = balance
        annual_withdrawn = 0.0
        months_in_year = 0
        for _ in range(12):
            if balance <= 0:
                break
            balance = balance * (1 + monthly_rate) - monthly_withdrawal
            annual_withdrawn += monthly_withdrawal
            months_in_year += 1
            month += 1
            if balance <= 0:
                balance = 0.0
                break

        returns_earned = (balance + annual_withdrawn) - start_balance
        annual_projections.append(
            {
                "year": year,
                "start_balance": round(start_balance, 2),
                "annual_withdrawn": round(annual_withdrawn, 2),
                "returns_earned": round(returns_earned, 2),
                "end_balance": round(balance, 2),
            }
        )
        if balance <= 0:
            break

    total_withdrawn = sum(s["annual_withdrawn"] for s in annual_projections)
    return {
        "corpus": round(corpus, 2),
        "monthly_withdrawal": round(monthly_withdrawal, 2),
        "annual_return": annual_return,
        "total_months": month,
        "total_years": round(month / 12, 1),
        "total_withdrawn": round(total_withdrawn, 2),
        "final_shortfall": round(abs(balance) if balance == 0 else 0, 2),
        "yearly_snapshots": annual_projections,
    }


def compute_swp_max_withdrawal(
    corpus: float,
    duration_years: int,
    annual_return: float,
) -> dict:
    monthly_rate = annual_return / 100 / 12
    n = duration_years * 12

    if monthly_rate == 0:
        monthly_withdrawal = corpus / n
    else:
        monthly_withdrawal = (
            corpus
            * (monthly_rate * (1 + monthly_rate) ** n)
            / ((1 + monthly_rate) ** n - 1)
        )

    result = compute_swp(corpus, monthly_withdrawal, annual_return, duration_years)
    result["monthly_withdrawal"] = round(monthly_withdrawal, 2)
    return result


SCENARIOS = {
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


def compute_swp_stress_test(
    corpus: float,
    monthly_withdrawal: float,
    duration_years: int,
) -> dict:
    results = {}
    for key, sc in SCENARIOS.items():
        swp_result = compute_swp(
            corpus, monthly_withdrawal, sc["return_rate"], duration_years
        )
        results[key] = {
            "label": sc["label"],
            "description": sc["description"],
            **swp_result,
        }
    return {
        "corpus": round(corpus, 2),
        "monthly_withdrawal": round(monthly_withdrawal, 2),
        "duration_years": duration_years,
        "scenarios": results,
    }
