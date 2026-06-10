from datetime import date, datetime

import httpx

from .base import FundDetail, FundSearchItem, MutualFundProvider, NAVRecord


class MFAPIProvider(MutualFundProvider):
    def __init__(self, base_url: str = "https://api.mfapi.in"):
        self.base_url = base_url
        self._client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        await self._client.aclose()

    async def search_funds(self, query: str) -> list[FundSearchItem]:
        resp = await self._client.get(f"{self.base_url}/search", params={"q": query})
        resp.raise_for_status()
        data = resp.json()
        return [
            FundSearchItem(
                scheme_code=item.get("schemeCode", 0),
                scheme_name=item.get("schemeName", ""),
                scheme_type=item.get("schemeType"),
                scheme_category=item.get("schemeCategory"),
                fund_family=item.get("fundFamily"),
            )
            for item in data
        ]

    async def get_all_funds(self) -> list[FundSearchItem]:
        resp = await self._client.get(f"{self.base_url}/mf")
        resp.raise_for_status()
        data = resp.json()
        return [
            FundSearchItem(
                scheme_code=item.get("schemeCode", 0),
                scheme_name=item.get("schemeName", ""),
                scheme_type=item.get("schemeType"),
                scheme_category=item.get("schemeCategory"),
                fund_family=item.get("fundFamily"),
            )
            for item in data
        ]

    async def get_fund_detail(self, scheme_code: int) -> FundDetail | None:
        try:
            resp = await self._client.get(f"{self.base_url}/mf/{scheme_code}")
            resp.raise_for_status()
            data = resp.json()
            meta = data.get("meta", {})
            nav_history_data = data.get("data", [])

            nav_records = []
            for record in nav_history_data:
                try:
                    nav_date = datetime.strptime(record["date"], "%d-%m-%Y").date()
                except (ValueError, KeyError):
                    continue
                try:
                    nav_val = float(record["nav"])
                except (ValueError, TypeError):
                    continue
                nav_records.append(NAVRecord(date=nav_date, nav=nav_val))

            latest_nav = nav_records[-1] if nav_records else None

            return FundDetail(
                scheme_code=meta.get("scheme_code", scheme_code),
                scheme_name=meta.get("scheme_name", ""),
                scheme_type=meta.get("scheme_type"),
                scheme_category=meta.get("scheme_category"),
                amc=None,
                fund_family=meta.get("fund_family"),
                isin=meta.get("isin"),
                isin_growth=meta.get("isin_growth"),
                nav=latest_nav.nav if latest_nav else None,
                nav_date=latest_nav.date if latest_nav else None,
                nav_history=nav_records,
            )
        except httpx.HTTPError:
            return None
