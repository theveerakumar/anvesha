"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { searchFunds, Fund } from "@/lib/api";

export default function FundScreenerPage() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Fund[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const doSearch = useCallback(async (q: string, p: number) => {
    if (!q.trim()) {
      setResults([]);
      setTotal(0);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await searchFunds(q, p, pageSize);
      setResults(data.results);
      setTotal(data.total);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Search failed");
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      if (query) {
        setPage(1);
        doSearch(query, 1);
      } else {
        setResults([]);
        setTotal(0);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [query, doSearch]);

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="p-4 md:p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-sm font-semibold text-bloomberg-text">Fund Screener</h1>
        <span className="text-[10px] text-bloomberg-dim font-mono">
          {total > 0 ? `${total} results` : ""}
        </span>
      </div>

      {/* Search bar */}
      <div className="relative">
        <svg
          className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-bloomberg-dim"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search by fund name, AMC, or category..."
          className="w-full bg-bloomberg-surface border border-bloomberg-border rounded pl-10 pr-4 py-2.5 text-sm text-bloomberg-text placeholder:text-bloomberg-dim/50 outline-none focus:border-bloomberg-cyan transition-colors font-mono"
          autoFocus
        />
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
                  <th className="text-left py-2 px-2 font-medium">Scheme Name</th>
                  <th className="text-left py-2 px-2 font-medium">AMC</th>
                  <th className="text-left py-2 px-2 font-medium">Category</th>
                  <th className="text-right py-2 px-2 font-medium">NAV</th>
                  <th className="text-right py-2 px-2 font-medium">1Y Return</th>
                  <th className="text-right py-2 px-2 font-medium">Expense Ratio</th>
                </tr>
              </thead>
              <tbody>
                {results.map((fund) => (
                  <tr
                    key={fund.id}
                    className="border-b border-bloomberg-border hover:bg-bloomberg-highlight transition-colors cursor-pointer"
                    onClick={() => router.push(`/funds/${fund.scheme_code}`)}
                  >
                    <td className="py-2.5 px-2 text-bloomberg-text truncate max-w-[350px]">
                      {fund.scheme_name}
                    </td>
                    <td className="py-2.5 px-2 text-bloomberg-dim">{fund.amc || fund.fund_family || "—"}</td>
                    <td className="py-2.5 px-2 text-bloomberg-dim">{fund.scheme_category || "—"}</td>
                    <td className="py-2.5 px-2 text-right font-mono">{fund.nav?.toFixed(2) || "—"}</td>
                    <td className={`py-2.5 px-2 text-right font-mono ${(fund.return_1y ?? 0) >= 0 ? "text-bloomberg-green" : "text-bloomberg-red"}`}>
                      {fund.return_1y != null ? `${fund.return_1y.toFixed(2)}%` : "—"}
                    </td>
                    <td className="py-2.5 px-2 text-right font-mono">
                      {fund.expense_ratio != null ? `${fund.expense_ratio.toFixed(2)}%` : "—"}
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
                onClick={() => { setPage(p => Math.max(1, p - 1)); doSearch(query, page - 1); }}
                disabled={page <= 1}
                className="px-3 py-1.5 bg-bloomberg-surface border border-bloomberg-border rounded hover:bg-bloomberg-highlight disabled:opacity-30 transition-colors"
              >
                Previous
              </button>
              <span className="text-bloomberg-dim font-mono">
                {page} / {totalPages}
              </span>
              <button
                onClick={() => { setPage(p => Math.min(totalPages, p + 1)); doSearch(query, page + 1); }}
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
      {!loading && !error && query && results.length === 0 && (
        <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-6 text-center text-sm text-bloomberg-dim">
          No funds found for &quot;{query}&quot;
        </div>
      )}

      {!loading && !query && (
        <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-6 text-center text-sm text-bloomberg-dim">
          Type at least one character to search across {">"}3,000 mutual fund schemes
        </div>
      )}

      {/* Risk Disclaimer */}
      <div className="text-[10px] text-bloomberg-dim border-t border-bloomberg-border pt-3">
        Data sourced from MFAPI.in. For research purposes only. Not investment advice.
      </div>
    </div>
  );
}
