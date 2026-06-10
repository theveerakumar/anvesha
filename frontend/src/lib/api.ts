const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface Fund {
  id: string;
  scheme_code: number;
  scheme_name: string;
  amc: string | null;
  scheme_type: string | null;
  scheme_category: string | null;
  fund_family: string | null;
  isin: string | null;
  isin_growth: string | null;
  nav: number | null;
  nav_date: string | null;
  aum_cr: number | null;
  expense_ratio: number | null;
  fund_manager: string | null;
  risk_level: string | null;
  return_1y: number | null;
  return_3y: number | null;
  return_5y: number | null;
  benchmark: string | null;
}

export interface FundSearchResult {
  total: number;
  page: number;
  page_size: number;
  results: Fund[];
}

export interface FundListResponse {
  total: number;
  page: number;
  page_size: number;
  funds: Fund[];
}

async function fetchJSON<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function searchFunds(q: string, page = 1, pageSize = 20): Promise<FundSearchResult> {
  return fetchJSON<FundSearchResult>(
    `${API_URL}/funds/search?q=${encodeURIComponent(q)}&page=${page}&page_size=${pageSize}`
  );
}

export async function getFund(schemeCode: number): Promise<Fund> {
  return fetchJSON<Fund>(`${API_URL}/funds/${schemeCode}`);
}

export async function listFunds(page = 1, pageSize = 50): Promise<FundListResponse> {
  return fetchJSON<FundListResponse>(
    `${API_URL}/funds?page=${page}&page_size=${pageSize}`
  );
}
