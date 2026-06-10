import re

CATEGORY_GROUP_RULES: list[tuple[str, list[str]]] = [
    ("gold_silver", ["gold", "silver", "precious metal"]),
    (
        "global",
        [
            "international",
            "global",
            "world",
            "overseas",
            "foreign",
            "us stock",
            "us equity",
            "nasdaq",
            "s&p 500",
            "dow jones",
            "developed market",
            "emerging market",
            "europe",
            "china",
            "japan",
            "brazil",
            "russia",
        ],
    ),
    (
        "index",
        [
            "index",
            "etf",
            "exchange traded",
            "nifty",
            "sensex",
            "bse",
            "nse",
            "bees",
            "next 50",
            "next50",
            "midcap 150",
            "smallcap 250",
            "largecap 200",
            "alpha 50",
            "quality 50",
            "value 50",
            "momentum 50",
            "low vol",
            "100 esg",
            "shariah",
            "pharma etf",
            "bank etf",
            "it etf",
            "psu etf",
            "energy etf",
        ],
    ),
    (
        "equity",
        [
            "equity",
            "large cap",
            "mid cap",
            "small cap",
            "multi cap",
            "multicap",
            "midcap",
            "smallcap",
            "flexi cap",
            "elss",
            "tax saver",
            "tax saving",
            "value fund",
            "contra fund",
            "focused fund",
            "blue chip",
            "dividend yield",
            "opportunities",
            "top 100",
            "top 200",
            "growth fund",
            "sector",
            "thematic",
            "infrastructure",
            "banking",
            "technology",
            "pharma",
            "healthcare",
            "fmcg",
            "consumption",
            "psu",
            "mnc",
            "energy",
            "manufacturing",
            "services",
            "transport",
        ],
    ),
    (
        "hybrid",
        [
            "hybrid",
            "balanced",
            "aggressive",
            "conservative",
            "monthly income",
            "mip",
            "children's fund",
            "retirement fund",
            "pension",
        ],
    ),
    (
        "debt",
        [
            "income",
            "debt",
            "bond",
            "gilt",
            "government security",
            "g-sec",
            "g sec",
            "corporate bond",
            "credit risk",
            "banking & psu",
            "banking and psu",
            "liquid",
            "money market",
            "ultra short",
            "short duration",
            "short term",
            "medium duration",
            "medium term",
            "long duration",
            "long term",
            "dynamic bond",
            "floating rate",
            "overnight",
            "treasury",
            "10 yr",
            "10 year",
            "constant maturity",
            "low duration",
            "credit opportunity",
            "accrual",
        ],
    ),
    (
        "solution",
        [
            "retirement",
            "pension",
            "children",
            "education",
            "savings plan",
            "investment cum insurance",
        ],
    ),
]

GROUP_ORDER = [
    "equity",
    "hybrid",
    "index",
    "gold_silver",
    "global",
    "debt",
    "solution",
    "other",
]

EQUITY_SUB_RULES: list[tuple[str, list[str]]] = [
    ("large_cap", ["large cap", "largecap", "top 100", "blue chip", "bluechip"]),
    ("mid_cap", ["mid cap", "midcap", "mid-cap"]),
    ("small_cap", ["small cap", "smallcap", "small-cap"]),
    ("multi_cap", ["multi cap", "multicap", "multi-cap"]),
    ("flexi_cap", ["flexi cap", "flexicap"]),
    ("elss", ["elss", "tax saver", "tax saving", "taxsaving"]),
    (
        "sectoral",
        [
            "sector",
            "thematic",
            "infrastructure",
            "banking",
            "technology",
            "pharma",
            "healthcare",
            "fmcg",
            "consumption",
            "psu",
            "mnc",
            "energy",
            "manufacturing",
            "services",
            "transport",
            "media",
            "insurance",
            "financial services",
            "consumption",
            "esg",
            "shariah",
            "defence",
            "railway",
            "tourism",
            "hotel",
        ],
    ),
    ("value", ["value", "contra"]),
    ("dividend_yield", ["dividend yield", "dividend opportunities"]),
    ("focused", ["focused", "focus"]),
]

CATEGORY_TO_GROUP: dict[str, str] = {
    "large cap": "equity",
    "mid cap": "equity",
    "small cap": "equity",
    "multi cap": "equity",
    "flexi cap": "equity",
    "elss": "equity",
    "value": "equity",
    "contra": "equity",
    "focused": "equity",
    "dividend yield": "equity",
    "sectoral": "equity",
    "thematic": "equity",
    "infrastructure": "equity",
    "banking": "equity",
    "technology": "equity",
    "pharma": "equity",
    "healthcare": "equity",
    "psu": "equity",
    "consumption": "equity",
    "services": "equity",
    "energy": "equity",
    "hybrid": "hybrid",
    "balanced": "hybrid",
    "monthly income": "hybrid",
    "income": "debt",
    "liquid": "debt",
    "overnight": "debt",
    "money market": "debt",
    "short duration": "debt",
    "corporate bond": "debt",
    "credit risk": "debt",
    "gilt": "debt",
    "index": "index",
    "etf": "index",
    "gold": "gold_silver",
    "silver": "gold_silver",
    "international": "global",
    "global": "global",
    "retirement": "solution",
    "children": "solution",
}


def _normalize(text: str | None) -> str:
    return (text or "").lower().replace("-", " ").replace("_", " ").strip()


def infer_category_group(
    scheme_name: str | None, scheme_category: str | None = None
) -> str:
    name = _normalize(scheme_name)
    cat = _normalize(scheme_category)

    # First try scheme_category mapping
    for key, group in CATEGORY_TO_GROUP.items():
        if key in cat or key in name:
            return group

    # Then try rule-based matching on scheme_name
    for group, keywords in CATEGORY_GROUP_RULES:
        for kw in keywords:
            if kw in name:
                return group

    return "other"


def infer_sub_category(
    scheme_name: str | None, scheme_category: str | None = None
) -> str | None:
    name = _normalize(scheme_name)
    cat = _normalize(scheme_category)
    combined = f"{name} {cat}"

    for sub_cat, keywords in EQUITY_SUB_RULES:
        for kw in keywords:
            if kw in combined:
                return sub_cat

    return None


def classify(
    schenme_name: str | None, scheme_category: str | None = None
) -> tuple[str, str | None]:
    group = infer_category_group(schenme_name, scheme_category)
    sub = (
        infer_sub_category(schenme_name, scheme_category) if group == "equity" else None
    )
    return group, sub
