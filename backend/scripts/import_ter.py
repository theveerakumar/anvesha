"""Import real Total Expense Ratio data from AMFI Excel into fund records."""

import asyncio
import difflib
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import openpyxl
from sqlalchemy import select

from app.core.database import async_session_factory
from app.models.fund import Fund

TER_PATH = "/tmp/ter.xlsx"

RE_FLAGS = re.IGNORECASE

FREQ = r"(?:Daily|Weekly|Fortnightly|Monthly|Quarterly|Half Yearly|Annual|Periodic)"

SUFFIX_PATTERNS = [
    rf" - Direct Plan$",
    rf" - Regular Plan$",
    rf" - Retail Plan$",
    rf" - Institutional Plan$",
    rf" - Direct$",
    rf" - Regular$",
    rf" - Retail$",
    rf" - Institutional$",
    rf" - Bonus( Option)?$",
    rf" - Appreciation$",
    rf" - Unclaimed( Redemption( - Beyond \d+ years)?)?$",
    rf" - Delisted$",
    rf" - Reinvestment( Option)?$",
    rf" - Growth( Option)?$",
    rf" - IDCW$",
    rf" - {FREQ} ?IDCW$",
    rf" - Regular {FREQ} ?IDCW$",
    rf" - Direct {FREQ} ?IDCW$",
    rf" - {FREQ} Dividend Payout$",
    rf" - {FREQ} Dividend Reinvestment$",
    rf" - {FREQ} Dividend$",
    rf" - Dividend( Payout| Reinvestment)?$",
    rf" - {FREQ} Payout( of Income)?( Discontinued)?$",
    rf" - Regular {FREQ} Payout( of Income)?$",
    rf" - Direct {FREQ} Payout( of Income)?$",
    rf" - Payout( of Income)?( Discontinued)?$",
    rf" - Income Distribution( cum Capital Withdrawal)?( {FREQ})?$",
    rf" - Income Distribution( cum Capital Withdrawal)?( ?IDCW)?( {FREQ})?$",
    rf" - (Direct|Regular) Plan - [A-Za-z ]+$",
    rf" - (Retail|Institutional) Plan - [A-Za-z ]+$",
    rf" - Institutional - [A-Za-z ]+$",
    rf" - Segregated Portfolio \d+",
    rf" \(Segregated - \d+\)",
    rf" \(Segregated Portfolio \d+\)",
    rf" - Premium( {FREQ})? ?(Dividend)?$",
    rf" - {FREQ} Dividend Option$",
    rf" - Dividend Option$",
    rf" - Weekly Dividend$",
    rf" - Maturity( Option)?$",
    rf" - Growth & Dividend Option$",
    rf" - Cumulative Option$",
    rf" - Super Premium {FREQ} Dividend$",
    rf" - (?:Direct|Regular|Retail|Institutional)(?: Plan)? (?:Growth|IDCW|Dividend(?: Option| Payout| Reinvestment)?|Maturity)$",
    rf" - Super Premium {FREQ} Dividend$",
    rf" - Defunct Plan$",
    rf" - Defunct$",
    rf" - Daily Div$",
    rf" - {FREQ} Div$",
    rf" - (?:SI |Daily |Weekly |Monthly )?Dividend Option$",
    rf" - Super Plus Plan$",
    rf" - Dynamic Plan(?: - .+)?$",
    rf" - Flex(?:ible)? Plan(?: - .+)?$",
    rf" - Savings Plan(?: - .+)?$",
    rf" - Advantage Plan(?: - .+)?$",
    rf" - Privilege Plan(?: - .+)?$",
    rf" - Premium Plan(?: - .+)?$",
    rf" - (?:Plan|Option) [A-Z]$",
    rf" - \(Regular\)$",
    rf" - \(Direct\)$",
    rf" \(Regular\)$",
    rf" \(Direct\)$",
    rf" - Growth Plan$",
    rf" - IDCW Plan$",
    rf" - Dividend Plan$",
    rf" - Growth Direct$",
    rf" - \(Growth\)$",
    rf" - \(IDCW\)$",
    rf" - \(Dividend\)$",
    rf" - (?:Direct|Regular) Plan (?:Growth|IDCW|Dividend) Plan$",
    rf" - (?:Direct|Regular) Plan (?:Growth|IDCW|Dividend)(?: Option)?$",
]

EXTRA_PATTERNS = [
    (r"(?<= )-Regular(?: Plan)?(?: - .+)?$", ""),
    (r"(?<= )-Direct(?: Plan)?(?: - .+)?$", ""),
    (r"(?<= )-Retail(?: Plan)?(?: - .+)?$", ""),
    (r"(?<= )-Institutional(?: Plan)?(?: - .+)?$", ""),
    (r" - Instnl? Plan - Growth Option$", ""),
    (r" - Instnl? Plan$", ""),
    (r" - Instnl?$", ""),
    (r" Plan - Growth Option$", ""),
    (r" Plan - Quarterly Dividend$", ""),
    (r" Plan - Dividend Option$", ""),
    (r" Option - Dividend$", ""),
    (r" Option - Growth$", ""),
    (r" Option - IDCW$", ""),
    (r" Option - Quarterly IDCW$", ""),
    (r" Option - Half Yearly Dividend$", ""),
    (r" Option - Maturity$", ""),
    (r"\(Dividend Option\)$", ""),
    (r"\(Growth Option\)$", ""),
    (r"\(Reinvestment Option\)$", ""),
    (r"\(IDCW Option\)$", ""),
    (r"\(IDCW Reinvestment\)$", ""),
    (r"\(Regular\)$", ""),
    (r"\(Direct\)$", ""),
    (r"\(Growth\)$", ""),
    (r"\(IDCW\)$", ""),
    (r"\(Dividend\)$", ""),
    (r" Fund Option$", " Fund"),
    (r" - formerly known as .+$", ""),
    (r" - Formerly .+$", ""),
]


def normalize(name: str) -> str:
    """Strip plan/suffix info to get the master scheme name."""
    if not name:
        return ""
    result = name.strip()
    # Remove trailing period
    if result.endswith("."):
        result = result[:-1].strip()
    # Normalize whitespace around dashes
    result = re.sub(r"\s*-\s*", " - ", result)
    all_patterns = SUFFIX_PATTERNS + EXTRA_PATTERNS
    while True:
        prev = result
        for pat in all_patterns:
            if isinstance(pat, tuple):
                result = re.sub(pat[0], pat[1], result, flags=RE_FLAGS).strip()
            else:
                result = re.sub(pat, "", result, flags=RE_FLAGS).strip()
        if result == prev:
            break
    result = re.sub(r"\s{2,}", " ", result).strip()
    return result


def load_excel_ter() -> dict[str, dict]:
    """Load TER data from Excel, deduplicate master scheme -> latest TER."""
    wb = openpyxl.load_workbook(TER_PATH, read_only=True, data_only=True)
    ws = wb.active

    schemes: dict[str, dict] = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        name = row[1]
        if not name:
            continue
        r_ter = row[9]
        d_ter = row[14]
        cat = row[3]
        if r_ter is not None or d_ter is not None:
            schemes[name] = {"r_ter": r_ter, "d_ter": d_ter, "cat": cat}

    wb.close()
    return schemes


def build_index(ter_data: dict[str, dict]) -> dict[str, tuple[str, dict]]:
    """Build a normalized name -> (original, info) lookup."""
    idx: dict[str, tuple[str, dict]] = {}
    for raw_name, info in ter_data.items():
        norm = normalize(raw_name)
        if not norm:
            continue
        key = norm.lower()
        if key not in idx:
            idx[key] = (raw_name, info)
        # Also index with stripped common words
        stripped = re.sub(r"\b(fund|scheme|plan|option)\b", "", key).strip()
        stripped = re.sub(r"\s+", " ", stripped)
        if stripped and stripped != key and stripped not in idx:
            idx[stripped] = (raw_name, info)
    return idx


async def main():
    print("Loading AMFI TER Excel data...")
    ter_data = load_excel_ter()
    print(f"Loaded {len(ter_data)} master schemes from Excel")

    index = build_index(ter_data)
    print(f"Built index with {len(index)} normalized entries")

    async with async_session_factory() as session:
        result = await session.execute(select(Fund).where(Fund.scheme_name.isnot(None)))
        funds = result.scalars().all()
        print(f"Processing {len(funds)} funds...")

        # Pre-build fuzzy matcher from index keys
        index_keys = list(index.keys())

        updated = 0
        fuzzy_matched = 0
        skipped = 0
        matched_names: set[str] = set()

        for fund in funds:
            name = fund.scheme_name
            if not name:
                continue

            name_lower = name.lower()
            is_direct = "direct" in name_lower
            norm = normalize(name).lower()
            if not norm:
                skipped += 1
                continue

            match = index.get(norm)

            # Fuzzy fallback: try close matches
            if not match:
                close = difflib.get_close_matches(norm, index_keys, n=1, cutoff=0.80)
                if close:
                    match = index[close[0]]
                    fuzzy_matched += 1

            if not match:
                skipped += 1
                continue

            _, info = match
            matched_names.add(norm)

            ter = info["d_ter"] if is_direct else info["r_ter"]
            if ter is None or ter == 0:
                ter = info["r_ter"] or info["d_ter"]
            if ter is None or ter == 0:
                skipped += 1
                continue

            fund.expense_ratio = round(float(ter), 4)
            updated += 1

            if updated % 2000 == 0:
                print(f"  ... {updated} updated")

        await session.commit()

    print(f"\nUpdated: {updated}")
    print(f"Fuzzy matched: {fuzzy_matched}")
    print(f"Skipped: {skipped}")
    print(f"Unique master schemes matched: {len(matched_names)}")


if __name__ == "__main__":
    asyncio.run(main())
