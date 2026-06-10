import random

SECTOR_ALLOCATIONS = {
    "Large Growth": {
        "Technology": 35,
        "Financial Services": 15,
        "Healthcare": 12,
        "Consumer Cyclical": 10,
        "Communication": 8,
        "Industrial": 6,
        "Consumer Defensive": 5,
        "Energy": 4,
        "Utilities": 3,
        "Real Estate": 2,
    },
    "Large Value": {
        "Financial Services": 25,
        "Energy": 15,
        "Industrial": 12,
        "Healthcare": 10,
        "Consumer Defensive": 8,
        "Technology": 8,
        "Utilities": 7,
        "Communication": 5,
        "Consumer Cyclical": 5,
        "Real Estate": 5,
    },
    "Mid Growth": {
        "Technology": 30,
        "Healthcare": 18,
        "Consumer Cyclical": 15,
        "Industrial": 12,
        "Financial Services": 10,
        "Communication": 5,
        "Consumer Defensive": 4,
        "Energy": 3,
        "Real Estate": 2,
        "Utilities": 1,
    },
    "Mid Value": {
        "Financial Services": 20,
        "Industrial": 18,
        "Healthcare": 12,
        "Energy": 12,
        "Consumer Defensive": 10,
        "Technology": 8,
        "Consumer Cyclical": 7,
        "Utilities": 5,
        "Communication": 4,
        "Real Estate": 4,
    },
    "Small Growth": {
        "Technology": 35,
        "Healthcare": 20,
        "Consumer Cyclical": 15,
        "Industrial": 12,
        "Financial Services": 8,
        "Communication": 5,
        "Energy": 3,
        "Real Estate": 1,
        "Consumer Defensive": 1,
        "Utilities": 0,
    },
    "Small Value": {
        "Industrial": 22,
        "Financial Services": 18,
        "Energy": 15,
        "Technology": 12,
        "Healthcare": 10,
        "Consumer Cyclical": 8,
        "Consumer Defensive": 5,
        "Utilities": 4,
        "Communication": 3,
        "Real Estate": 3,
    },
    "ELSS": {
        "Technology": 25,
        "Financial Services": 20,
        "Healthcare": 12,
        "Consumer Cyclical": 10,
        "Industrial": 10,
        "Energy": 7,
        "Communication": 5,
        "Consumer Defensive": 5,
        "Utilities": 3,
        "Real Estate": 3,
    },
    "Banking": {
        "Financial Services": 85,
        "Technology": 5,
        "Consumer Cyclical": 3,
        "Industrial": 2,
        "Energy": 2,
        "Healthcare": 1,
        "Communication": 1,
        "Utilities": 1,
        "Consumer Defensive": 0,
        "Real Estate": 0,
    },
    "Technology": {
        "Technology": 80,
        "Communication": 8,
        "Consumer Cyclical": 4,
        "Healthcare": 3,
        "Industrial": 2,
        "Financial Services": 2,
        "Consumer Defensive": 1,
        "Energy": 0,
        "Utilities": 0,
        "Real Estate": 0,
    },
    "Healthcare": {
        "Healthcare": 75,
        "Technology": 8,
        "Consumer Defensive": 5,
        "Financial Services": 4,
        "Industrial": 3,
        "Consumer Cyclical": 2,
        "Communication": 2,
        "Energy": 1,
        "Utilities": 0,
        "Real Estate": 0,
    },
    "FMCG": {
        "Consumer Defensive": 70,
        "Consumer Cyclical": 10,
        "Technology": 5,
        "Financial Services": 4,
        "Healthcare": 3,
        "Industrial": 3,
        "Communication": 2,
        "Energy": 1,
        "Utilities": 1,
        "Real Estate": 1,
    },
    "Pharma": {
        "Healthcare": 80,
        "Technology": 6,
        "Consumer Defensive": 4,
        "Financial Services": 3,
        "Industrial": 2,
        "Consumer Cyclical": 2,
        "Communication": 1,
        "Energy": 1,
        "Utilities": 1,
        "Real Estate": 0,
    },
    "PSU": {
        "Energy": 25,
        "Financial Services": 20,
        "Industrial": 18,
        "Utilities": 12,
        "Communication": 8,
        "Consumer Cyclical": 5,
        "Technology": 4,
        "Healthcare": 3,
        "Consumer Defensive": 3,
        "Real Estate": 2,
    },
    "Dividend": {
        "Financial Services": 25,
        "Energy": 15,
        "Consumer Defensive": 12,
        "Utilities": 10,
        "Healthcare": 8,
        "Industrial": 8,
        "Technology": 6,
        "Communication": 6,
        "Consumer Cyclical": 5,
        "Real Estate": 5,
    },
    "Index": {
        "Technology": 25,
        "Financial Services": 22,
        "Healthcare": 10,
        "Consumer Cyclical": 8,
        "Consumer Defensive": 7,
        "Energy": 7,
        "Industrial": 6,
        "Communication": 5,
        "Utilities": 5,
        "Real Estate": 5,
    },
}

DEFAULT_ALLOCATION = {
    "Technology": 20,
    "Financial Services": 18,
    "Healthcare": 12,
    "Consumer Cyclical": 10,
    "Industrial": 10,
    "Energy": 8,
    "Consumer Defensive": 7,
    "Communication": 6,
    "Utilities": 5,
    "Real Estate": 4,
}

STOCKS_BY_SECTOR = {
    "Technology": [
        "Infosys",
        "TCS",
        "HCL Tech",
        "Wipro",
        "Tech Mahindra",
        "LTIMindtree",
        "Hinduja Global",
        "Mphasis",
        "Mindtree",
        "Persistent Systems",
    ],
    "Financial Services": [
        "HDFC Bank",
        "ICICI Bank",
        "Kotak Mahindra",
        "Axis Bank",
        "SBI",
        "Bajaj Finance",
        "IndusInd Bank",
        "Yes Bank",
        "PNB",
        "BOB",
    ],
    "Healthcare": [
        "Sun Pharma",
        "Dr Reddy's",
        "Cipla",
        "Lupin",
        "Aurobindo Pharma",
        "Divis Labs",
        "Biocon",
        "Glenmark",
        "Torrent Pharma",
        "Cadila Healthcare",
    ],
    "Consumer Cyclical": [
        "Tata Motors",
        "M&M",
        "Maruti Suzuki",
        "Bajaj Auto",
        "Hero MotoCorp",
        "Titan",
        "Asian Paints",
        "Page Industries",
        "Voltas",
        "Whirlpool",
    ],
    "Consumer Defensive": [
        "HUL",
        "ITC",
        "Nestle India",
        "Britannia",
        "Dabur",
        "Marico",
        "Colgate Palmolive",
        "Godrej Consumer",
        "Emami",
        "Tata Consumer",
    ],
    "Energy": [
        "Reliance Industries",
        "ONGC",
        "Indian Oil",
        "BPCL",
        "HPCL",
        "GAIL",
        "Coal India",
        "Oil India",
        "Petronet LNG",
        "Gujarat Gas",
    ],
    "Industrial": [
        "L&T",
        "Siemens",
        "BHEL",
        "ABB India",
        "Cummins",
        "Thermax",
        "KEC International",
        "Bharat Electronics",
        "GE Power",
        "HAL",
    ],
    "Communication": [
        "Bharti Airtel",
        "Reliance Jio",
        "Vodafone Idea",
        "Tata Communications",
        "MTNL",
        "Tejas Networks",
        "HFCL",
        "Sterlite Tech",
        "Railtel",
        "GTPL Hathway",
    ],
    "Utilities": [
        "NTPC",
        "Power Grid",
        "Tata Power",
        "Adani Power",
        "NHPC",
        "Torrent Power",
        "JSW Energy",
        "SJVN",
        "CESC",
        "Adani Transmission",
    ],
    "Real Estate": [
        "DLF",
        "Oberoi Realty",
        "Godrej Properties",
        "Brigade Enterprises",
        "Prestige Estates",
        "Sobha Ltd",
        "Phoenix Mills",
        "Sunteck Realty",
        "Mahindra Lifespace",
        "Kolte Patil",
    ],
}

MARKET_CAP_CATEGORIES = ["Large Cap", "Mid Cap", "Small Cap"]

CATEGORY_MARKET_CAP_MIX = {
    "Large Growth": {"Large Cap": 70, "Mid Cap": 20, "Small Cap": 10},
    "Large Value": {"Large Cap": 75, "Mid Cap": 18, "Small Cap": 7},
    "Mid Growth": {"Large Cap": 20, "Mid Cap": 55, "Small Cap": 25},
    "Mid Value": {"Large Cap": 25, "Mid Cap": 55, "Small Cap": 20},
    "Small Growth": {"Large Cap": 5, "Mid Cap": 25, "Small Cap": 70},
    "Small Value": {"Large Cap": 10, "Mid Cap": 25, "Small Cap": 65},
    "ELSS": {"Large Cap": 50, "Mid Cap": 30, "Small Cap": 20},
    "Banking": {"Large Cap": 70, "Mid Cap": 25, "Small Cap": 5},
    "Technology": {"Large Cap": 55, "Mid Cap": 30, "Small Cap": 15},
    "Healthcare": {"Large Cap": 50, "Mid Cap": 35, "Small Cap": 15},
    "FMCG": {"Large Cap": 80, "Mid Cap": 15, "Small Cap": 5},
    "Pharma": {"Large Cap": 50, "Mid Cap": 35, "Small Cap": 15},
    "PSU": {"Large Cap": 65, "Mid Cap": 25, "Small Cap": 10},
    "Dividend": {"Large Cap": 75, "Mid Cap": 20, "Small Cap": 5},
    "Index": {"Large Cap": 90, "Mid Cap": 8, "Small Cap": 2},
}

DEFAULT_MARKET_CAP_MIX = {"Large Cap": 50, "Mid Cap": 30, "Small Cap": 20}


def _match_category(category: str) -> str:
    if not category:
        return "Index"
    cat_lower = category.lower()
    for key in SECTOR_ALLOCATIONS:
        if key.lower() in cat_lower or cat_lower in key.lower():
            return key
    if "bank" in cat_lower:
        return "Banking"
    if "tech" in cat_lower or "it" in cat_lower:
        return "Technology"
    if "pharma" in cat_lower or "health" in cat_lower:
        return "Pharma"
    if "fmcg" in cat_lower or "consum" in cat_lower:
        return "FMCG"
    if "elss" in cat_lower or "tax" in cat_lower:
        return "ELSS"
    if "psu" in cat_lower or "public" in cat_lower:
        return "PSU"
    if "dividend" in cat_lower:
        return "Dividend"
    if "small" in cat_lower:
        return "Small Growth"
    if "mid" in cat_lower:
        return "Mid Growth"
    if "large" in cat_lower or "flexi" in cat_lower:
        return "Large Growth"
    if "value" in cat_lower:
        return "Large Value"
    if "index" in cat_lower or "sensex" in cat_lower or "nifty" in cat_lower:
        return "Index"
    return "Large Growth"


def generate_holdings(scheme_code: int, scheme_name: str, category: str | None) -> dict:
    profile = _match_category(category)
    sector_alloc = SECTOR_ALLOCATIONS.get(profile, DEFAULT_ALLOCATION)
    mc_mix = CATEGORY_MARKET_CAP_MIX.get(profile, DEFAULT_MARKET_CAP_MIX)

    holdings = []
    total_weight = 0
    random.seed(scheme_code)

    for sector, alloc_pct in sector_alloc.items():
        if alloc_pct == 0:
            continue
        stocks = STOCKS_BY_SECTOR.get(sector, ["Company A", "Company B", "Company C"])
        num_stocks = max(1, alloc_pct // 5 + random.randint(0, 1))
        selected = random.sample(stocks, min(num_stocks, len(stocks)))
        remaining = alloc_pct
        for i, stock in enumerate(selected):
            if i == len(selected) - 1:
                weight = round(remaining, 2)
            else:
                weight = round(
                    remaining * random.uniform(0.3, 0.7) / (len(selected) - i), 2
                )
            remaining -= weight
            total_weight += weight

            r = random.random()
            if r < mc_mix.get("Large Cap", 33) / 100:
                cap = "Large Cap"
            elif r < (mc_mix.get("Large Cap", 33) + mc_mix.get("Mid Cap", 33)) / 100:
                cap = "Mid Cap"
            else:
                cap = "Small Cap"

            holdings.append(
                {
                    "stock_name": stock,
                    "sector": sector,
                    "weight": weight,
                    "market_cap": cap,
                }
            )

    sector_allocation = {}
    for h in holdings:
        sector_allocation[h["sector"]] = (
            sector_allocation.get(h["sector"], 0) + h["weight"]
        )

    market_cap_allocation = {}
    for h in holdings:
        market_cap_allocation[h["market_cap"]] = (
            market_cap_allocation.get(h["market_cap"], 0) + h["weight"]
        )

    return {
        "scheme_code": scheme_code,
        "scheme_name": scheme_name,
        "holdings": sorted(holdings, key=lambda x: x["weight"], reverse=True),
        "sector_allocation": dict(
            sorted(sector_allocation.items(), key=lambda x: x[1], reverse=True)
        ),
        "market_cap_allocation": dict(
            sorted(market_cap_allocation.items(), key=lambda x: x[1], reverse=True)
        ),
        "total_stocks": len(holdings),
        "total_weight": round(total_weight, 2),
    }
