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

export interface ReturnsData {
  scheme_code: number;
  scheme_name: string;
  return_1m: number | null;
  return_3m: number | null;
  return_6m: number | null;
  return_1y: number | null;
  cagr_3y: number | null;
  cagr_5y: number | null;
  cagr_7y: number | null;
  cagr_10y: number | null;
  max_drawdown: number | null;
}

export interface RiskData {
  scheme_code: number;
  scheme_name: string;
  std_dev: number | null;
  beta: number | null;
  alpha: number | null;
  sharpe_ratio: number | null;
  sortino_ratio: number | null;
  treynor_ratio: number | null;
  information_ratio: number | null;
  max_drawdown: number | null;
  risk_score: number | null;
  risk_level: string | null;
}

export interface NAVPoint {
  date: string;
  nav: number;
}

export interface NAVHistoryData {
  scheme_code: number;
  scheme_name: string;
  nav_history: NAVPoint[];
}

export interface RatingData {
  scheme_code: number;
  scheme_name: string;
  star_rating: number;
  overall_score: number;
  performance_score: number | null;
  consistency_score: number | null;
  risk_score: number | null;
  cost_score: number | null;
  portfolio_quality_score: number | null;
}

export interface RecommendationData {
  scheme_code: number;
  scheme_name: string;
  recommendation: string;
  confidence_score: number;
  reasoning: string;
  strengths: string | null;
  weaknesses: string | null;
  opportunities: string | null;
  risks: string | null;
}

export interface CompareRow {
  metric: string;
  values: Record<string, string>;
  winner: string | null;
}

export interface CompareResponse {
  schemes: number[];
  funds: Fund[];
  comparison: CompareRow[];
}

export interface OverlapResponse {
  scheme_code_a: number;
  scheme_name_a: string;
  scheme_code_b: number;
  scheme_name_b: string;
  common_holdings: { stock: string; sector: string | null; weight_a: number | null; weight_b: number | null }[];
  overlap_percentage: number;
  diversification_score: number;
}

export interface FundDetailResponse {
  fund: Fund;
  returns: ReturnsData | null;
  risk: RiskData | null;
  rating: RatingData | null;
  recommendation: RecommendationData | null;
  nav_history: NAVHistoryData | null;
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

export interface CategoryResponse {
  category: string;
  total_funds: number;
  avg_return_1y: number | null;
  avg_cagr_3y: number | null;
  avg_cagr_5y: number | null;
  top_funds: {
    scheme_code: number;
    scheme_name: string;
    nav: number | null;
    return_1y: number | null;
    cagr_3y: number | null;
    cagr_5y: number | null;
    expense_ratio: number | null;
    aum_cr: number | null;
    sharpe_ratio: number | null;
    risk_level: string | null;
  }[];
}

export interface CategoryListResponse {
  categories: string[];
  total: number;
}

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, options);
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

export async function getFundDetail(schemeCode: number): Promise<FundDetailResponse> {
  return fetchJSON<FundDetailResponse>(`${API_URL}/funds/${schemeCode}/detail`);
}

export async function getFundReturns(schemeCode: number): Promise<ReturnsData> {
  return fetchJSON<ReturnsData>(`${API_URL}/funds/${schemeCode}/returns`);
}

export async function getFundRisk(schemeCode: number): Promise<RiskData> {
  return fetchJSON<RiskData>(`${API_URL}/funds/${schemeCode}/risk`);
}

export async function getFundNavHistory(schemeCode: number): Promise<NAVHistoryData> {
  return fetchJSON<NAVHistoryData>(`${API_URL}/funds/${schemeCode}/nav-history`);
}

export async function listFunds(page = 1, pageSize = 50): Promise<FundListResponse> {
  return fetchJSON<FundListResponse>(`${API_URL}/funds?page=${page}&page_size=${pageSize}`);
}

export async function listCategories(): Promise<CategoryListResponse> {
  return fetchJSON<CategoryListResponse>(`${API_URL}/categories`);
}

export async function getCategory(name: string, limit = 10): Promise<CategoryResponse> {
  return fetchJSON<CategoryResponse>(`${API_URL}/categories/${encodeURIComponent(name)}?limit=${limit}`);
}

export async function getFundRating(schemeCode: number): Promise<RatingData> {
  return fetchJSON<RatingData>(`${API_URL}/funds/${schemeCode}/rating`);
}

export async function getFundRecommendation(schemeCode: number): Promise<RecommendationData> {
  return fetchJSON<RecommendationData>(`${API_URL}/funds/${schemeCode}/recommendation`);
}

export async function compareFunds(schemeCodes: number[]): Promise<CompareResponse> {
  return fetchJSON<CompareResponse>(`${API_URL}/funds/compare`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(schemeCodes),
  });
}

export async function getFundOverlap(a: number, b: number): Promise<OverlapResponse> {
  return fetchJSON<OverlapResponse>(`${API_URL}/funds/overlap?a=${a}&b=${b}`);
}
