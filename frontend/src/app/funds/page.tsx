"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { screenFunds, listCategories, Fund } from "@/lib/api";

interface Filters {
  q: string;
  category: string;
  min_return_1y: string;
  max_return_1y: string;
  min_return_3y: string;
  max_return_3y: string;
  min_return_5y: string;
  max_expense_ratio: string;
  min_aum_cr: string;
  risk_level: string;
}

const defaultFilters: Filters = {
  q: "",
  category: "",
  min_return_1y: "",
  max_return_1y: "",
  min_return_3y: "",
  max_return_3y: "",
  min_return_5y: "",
  max_expense_ratio: "",
  min_aum_cr: "",
  risk_level: "",
};

const riskLevels = ["Very High", "High", "Moderate", "Low", "Very Low"];

export default function FundScreenerPage() {
  const router = useRouter();
  const [filters, setFilters] = useState<Filters>(defaultFilters);
  const [results, setResults] = useState<Fund[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [sortBy, setSortBy] = useState("return_1y");
  const [sortOrder, setSortOrder] = useState("desc");
  const [categories, setCategories] = useState<string[]>([]);
  const [showFilters, setShowFilters] = useState(false);
  const pageSize = 20;

  useEffect(() => {
    listCategories().then(d => setCategories(d.categories)).catch(() => {});
  }, []);

  const buildParams = useCallback(() => {
    const params: Record<string, string | number | undefined> = {
      page,
      page_size: pageSize,
      sort_by: sortBy,
      sort_order: sortOrder,
    };
    if (filters.q) params.q = filters.q;
    if (filters.category) params.category = filters.category;
    if (filters.min_return_1y) params.min_return_1y = Number(filters.min_return_1y);
    if (filters.max_return_1y) params.max_return_1y = Number(filters.max_return_1y);
    if (filters.min_return_3y) params.min_return_3y = Number(filters.min_return_3y);
    if (filters.max_return_3y) params.max_return_3y = Number(filters.max_return_3y);
    if (filters.min_return_5y) params.min_return_5y = Number(filters.min_return_5y);
    if (filters.max_expense_ratio) params.max_expense_ratio = Number(filters.max_expense_ratio);
    if (filters.min_aum_cr) params.min_aum_cr = Number(filters.min_aum_cr);
    if (filters.risk_level) params.risk_level = filters.risk_level;
    return params;
  }, [filters, page, sortBy, sortOrder]);

  const doSearch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = buildParams();
      const data = await screenFunds(params);
      setResults(data.results);
      setTotal(data.total);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Search failed");
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, [buildParams]);

  useEffect(() => {
    const timer = setTimeout(() => {
      doSearch();
    }, 300);
    return () => clearTimeout(timer);
  }, [doSearch]);

  const handleSort = (col: string) => {
    if (sortBy === col) {
      setSortOrder(o => o === "desc" ? "asc" : "desc");
    } else {
      setSortBy(col);
      setSortOrder("desc");
    }
    setPage(1);
  };

  const clearFilters = () => {
    setFilters(defaultFilters);
    setPage(1);
  };

  const hasActiveFilters = Object.values(filters).some(v => v !== "");
  const totalPages = Math.ceil(total / pageSize);

  const SortIcon = ({ col }: { col: string }) => {
    if (sortBy !== col) return <span className="text-bloomberg-dim/30 ml-1">↕</span>;
    return <span className="text-bloomberg-cyan ml-1">{sortOrder === "desc" ? "↓" : "↑"}</span>;
  };

  const Th = ({ col, children }: { col: string; children: React.ReactNode }) => (
    <th
      className="text-left py-2 px-2 font-medium cursor-pointer hover:text-bloomberg-text select-none"
      onClick={() => handleSort(col)}
    >
      <span className="inline-flex items-center">{children}<SortIcon col={col} /></span>
    </th>
  );

  return (
    <div className="p-4 md:p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-sm font-semibold text-bloomberg-text">Fund Screener</h1>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="text-[10px] text-bloomberg-dim hover:text-bloomberg-cyan transition-colors flex items-center gap-1"
          >
            <svg className={`w-3 h-3 transition-transform ${showFilters ? "rotate-90" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
            Filters
          </button>
          {hasActiveFilters && (
            <button onClick={clearFilters} className="text-[10px] text-bloomberg-red hover:text-bloomberg-red/80 transition-colors">
              Clear all
            </button>
          )}
        </div>
        <span className="text-[10px] text-bloomberg-dim font-mono">
          {total > 0 ? `${total} results` : ""}
        </span>
      </div>

      {/* Search + Filters */}
      <div className="space-y-3">
        <div className="relative">
          <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-bloomberg-dim" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            value={filters.q}
            onChange={(e) => { setFilters(f => ({ ...f, q: e.target.value })); setPage(1); }}
            placeholder="Search by fund name, AMC, or category..."
            className="w-full bg-bloomberg-surface border border-bloomberg-border rounded pl-10 pr-4 py-2.5 text-sm text-bloomberg-text placeholder:text-bloomberg-dim/50 outline-none focus:border-bloomberg-cyan transition-colors font-mono"
            autoFocus
          />
        </div>

        {showFilters && (
          <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-3">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div>
                <label className="text-[10px] text-bloomberg-dim uppercase block mb-1">Category</label>
                <select
                  value={filters.category}
                  onChange={(e) => { setFilters(f => ({ ...f, category: e.target.value })); setPage(1); }}
                  className="w-full bg-bloomberg-bg border border-bloomberg-border rounded px-2 py-1.5 text-xs text-bloomberg-text outline-none focus:border-bloomberg-cyan"
                >
                  <option value="">All Categories</option>
                  {categories.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <div>
                <label className="text-[10px] text-bloomberg-dim uppercase block mb-1">1Y Return (%)</label>
                <div className="flex gap-1">
                  <input type="number" placeholder="Min" value={filters.min_return_1y}
                    onChange={(e) => { setFilters(f => ({ ...f, min_return_1y: e.target.value })); setPage(1); }}
                    className="w-full bg-bloomberg-bg border border-bloomberg-border rounded px-2 py-1.5 text-xs text-bloomberg-text outline-none focus:border-bloomberg-cyan font-mono placeholder:text-bloomberg-dim/40" />
                  <input type="number" placeholder="Max" value={filters.max_return_1y}
                    onChange={(e) => { setFilters(f => ({ ...f, max_return_1y: e.target.value })); setPage(1); }}
                    className="w-full bg-bloomberg-bg border border-bloomberg-border rounded px-2 py-1.5 text-xs text-bloomberg-text outline-none focus:border-bloomberg-cyan font-mono placeholder:text-bloomberg-dim/40" />
                </div>
              </div>
              <div>
                <label className="text-[10px] text-bloomberg-dim uppercase block mb-1">3Y CAGR (%)</label>
                <div className="flex gap-1">
                  <input type="number" placeholder="Min" value={filters.min_return_3y}
                    onChange={(e) => { setFilters(f => ({ ...f, min_return_3y: e.target.value })); setPage(1); }}
                    className="w-full bg-bloomberg-bg border border-bloomberg-border rounded px-2 py-1.5 text-xs text-bloomberg-text outline-none focus:border-bloomberg-cyan font-mono placeholder:text-bloomberg-dim/40" />
                  <input type="number" placeholder="Max" value={filters.max_return_3y}
                    onChange={(e) => { setFilters(f => ({ ...f, max_return_3y: e.target.value })); setPage(1); }}
                    className="w-full bg-bloomberg-bg border border-bloomberg-border rounded px-2 py-1.5 text-xs text-bloomberg-text outline-none focus:border-bloomberg-cyan font-mono placeholder:text-bloomberg-dim/40" />
                </div>
              </div>
              <div>
                <label className="text-[10px] text-bloomberg-dim uppercase block mb-1">5Y CAGR (%)</label>
                <input type="number" placeholder="Min" value={filters.min_return_5y}
                  onChange={(e) => { setFilters(f => ({ ...f, min_return_5y: e.target.value })); setPage(1); }}
                  className="w-full bg-bloomberg-bg border border-bloomberg-border rounded px-2 py-1.5 text-xs text-bloomberg-text outline-none focus:border-bloomberg-cyan font-mono placeholder:text-bloomberg-dim/40" />
              </div>
              <div>
                <label className="text-[10px] text-bloomberg-dim uppercase block mb-1">Max Expense Ratio (%)</label>
                <input type="number" placeholder="e.g. 1.5" step="0.1" value={filters.max_expense_ratio}
                  onChange={(e) => { setFilters(f => ({ ...f, max_expense_ratio: e.target.value })); setPage(1); }}
                  className="w-full bg-bloomberg-bg border border-bloomberg-border rounded px-2 py-1.5 text-xs text-bloomberg-text outline-none focus:border-bloomberg-cyan font-mono placeholder:text-bloomberg-dim/40" />
              </div>
              <div>
                <label className="text-[10px] text-bloomberg-dim uppercase block mb-1">Min AUM (Cr)</label>
                <input type="number" placeholder="e.g. 1000" value={filters.min_aum_cr}
                  onChange={(e) => { setFilters(f => ({ ...f, min_aum_cr: e.target.value })); setPage(1); }}
                  className="w-full bg-bloomberg-bg border border-bloomberg-border rounded px-2 py-1.5 text-xs text-bloomberg-text outline-none focus:border-bloomberg-cyan font-mono placeholder:text-bloomberg-dim/40" />
              </div>
              <div>
                <label className="text-[10px] text-bloomberg-dim uppercase block mb-1">Risk Level</label>
                <select
                  value={filters.risk_level}
                  onChange={(e) => { setFilters(f => ({ ...f, risk_level: e.target.value })); setPage(1); }}
                  className="w-full bg-bloomberg-bg border border-bloomberg-border rounded px-2 py-1.5 text-xs text-bloomberg-text outline-none focus:border-bloomberg-cyan"
                >
                  <option value="">All Risk Levels</option>
                  {riskLevels.map(r => <option key={r} value={r}>{r}</option>)}
                </select>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="bg-bloomberg-surface border border-bloomberg-red/30 rounded p-3 text-sm text-bloomberg-red">
          {error}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="space-y-2">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="skeleton h-8 w-full" />
          ))}
        </div>
      )}

      {/* Results */}
      {!loading && results.length > 0 && (
        <>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-bloomberg-dim border-b border-bloomberg-border">
                  <Th col="scheme_name">Scheme Name</Th>
                  <Th col="fund_family">AMC</Th>
                  <Th col="scheme_category">Category</Th>
                  <Th col="nav">NAV</Th>
                  <Th col="return_1y">1Y Return</Th>
                  <Th col="return_3y">3Y CAGR</Th>
                  <Th col="return_5y">5Y CAGR</Th>
                  <Th col="expense_ratio">Expense Ratio</Th>
                  <Th col="aum_cr">AUM (Cr)</Th>
                  <Th col="risk_level">Risk</Th>
                </tr>
              </thead>
              <tbody>
                {results.map((fund) => (
                  <tr
                    key={fund.id}
                    className="border-b border-bloomberg-border hover:bg-bloomberg-highlight transition-colors cursor-pointer"
                    onClick={() => router.push(`/funds/${fund.scheme_code}`)}
                  >
                    <td className="py-2.5 px-2 text-bloomberg-text truncate max-w-[300px]">
                      {fund.scheme_name}
                    </td>
                    <td className="py-2.5 px-2 text-bloomberg-dim">{fund.amc || fund.fund_family || "—"}</td>
                    <td className="py-2.5 px-2 text-bloomberg-dim">{fund.scheme_category || "—"}</td>
                    <td className="py-2.5 px-2 text-right font-mono">{fund.nav?.toFixed(2) || "—"}</td>
                    <td className={`py-2.5 px-2 text-right font-mono ${(fund.return_1y ?? 0) >= 0 ? "text-bloomberg-green" : "text-bloomberg-red"}`}>
                      {fund.return_1y != null ? `${fund.return_1y.toFixed(2)}%` : "—"}
                    </td>
                    <td className={`py-2.5 px-2 text-right font-mono ${(fund.return_3y ?? 0) >= 0 ? "text-bloomberg-green" : "text-bloomberg-red"}`}>
                      {fund.return_3y != null ? `${fund.return_3y.toFixed(2)}%` : "—"}
                    </td>
                    <td className={`py-2.5 px-2 text-right font-mono ${(fund.return_5y ?? 0) >= 0 ? "text-bloomberg-green" : "text-bloomberg-red"}`}>
                      {fund.return_5y != null ? `${fund.return_5y.toFixed(2)}%` : "—"}
                    </td>
                    <td className="py-2.5 px-2 text-right font-mono">
                      {fund.expense_ratio != null ? `${fund.expense_ratio.toFixed(2)}%` : "—"}
                    </td>
                    <td className="py-2.5 px-2 text-right font-mono">
                      {fund.aum_cr != null ? `₹${fund.aum_cr.toFixed(0)}` : "—"}
                    </td>
                    <td className="py-2.5 px-2">
                      <span className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-medium ${
                        fund.risk_level === "Very High" ? "bg-red-900/40 text-red-400" :
                        fund.risk_level === "High" ? "bg-orange-900/40 text-orange-400" :
                        fund.risk_level === "Moderate" ? "bg-yellow-900/40 text-yellow-400" :
                        fund.risk_level === "Low" ? "bg-green-900/40 text-green-400" :
                        fund.risk_level === "Very Low" ? "bg-teal-900/40 text-teal-400" :
                        "bg-bloomberg-dim/10 text-bloomberg-dim"
                      }`}>
                        {fund.risk_level || "—"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 text-xs">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="px-3 py-1.5 bg-bloomberg-surface border border-bloomberg-border rounded hover:bg-bloomberg-highlight disabled:opacity-30 transition-colors"
              >
                Previous
              </button>
              <span className="text-bloomberg-dim font-mono">
                {page} / {totalPages}
              </span>
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="px-3 py-1.5 bg-bloomberg-surface border border-bloomberg-border rounded hover:bg-bloomberg-highlight disabled:opacity-30 transition-colors"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}

      {/* Empty state */}
      {!loading && !error && hasActiveFilters && results.length === 0 && (
        <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-6 text-center text-sm text-bloomberg-dim">
          No funds match your criteria. Try adjusting the filters.
        </div>
      )}

      {!loading && !error && !hasActiveFilters && results.length === 0 && (
        <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-6 text-center text-sm text-bloomberg-dim">
          Start typing or apply filters to screen mutual funds
        </div>
      )}

      <div className="text-[10px] text-bloomberg-dim border-t border-bloomberg-border pt-3">
        Data sourced from MFAPI.in. For research purposes only. Not investment advice.
      </div>
    </div>
  );
}
