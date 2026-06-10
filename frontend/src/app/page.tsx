"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  getDashboard,
  DashboardResponse,
  DashboardTab,
  SubCategoryInfo,
  FundRow,
  TopPick,
} from "@/lib/api";

const SORT_OPTIONS: { key: string; label: string }[] = [
  { key: "composite_score", label: "Score" },
  { key: "return_1y", label: "1Y Return" },
  { key: "rolling_return_3y_avg", label: "3Y Roll" },
  { key: "rolling_return_5y_avg", label: "5Y Roll" },
  { key: "aum_cr", label: "AUM" },
  { key: "expense_ratio", label: "Expense" },
  { key: "nav", label: "NAV" },
];

export default function DashboardPage() {
  const router = useRouter();
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState("all");
  const [subCategory, setSubCategory] = useState<string | undefined>();
  const [sortBy, setSortBy] = useState("composite_score");
  const [sortOrder, setSortOrder] = useState("desc");
  const [page, setPage] = useState(1);

  useEffect(() => {
    setPage(1);
  }, [tab, subCategory, sortBy, sortOrder]);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const d = await getDashboard(tab, subCategory, sortBy, sortOrder, page, 20);
        setData(d);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [tab, subCategory, sortBy, sortOrder, page]);

  const handleSort = (key: string) => {
    if (sortBy === key) {
      setSortOrder(o => (o === "desc" ? "asc" : "desc"));
    } else {
      setSortBy(key);
      setSortOrder("desc");
    }
  };

  const formatPct = (v: number | null | undefined) =>
    v != null ? `${v >= 0 ? "+" : ""}${v.toFixed(2)}%` : "—";

  const formatNum = (v: number | null | undefined, d = 2) =>
    v != null ? v.toFixed(d) : "—";

  const formatAum = (v: number | null | undefined) =>
    v != null
      ? v >= 10000
        ? `₹${(v / 1000).toFixed(1)}K Cr`
        : `₹${v.toFixed(0)} Cr`
      : "—";

  const tabLabels: Record<string, string> = {
    all: "All Funds", equity: "Equity", hybrid: "Hybrid",
    index: "Index & ETFs", gold_silver: "Gold & Silver",
    global: "Global", debt: "Debt", solution: "Solution Oriented", other: "Others",
  };

  const subCatLabels: Record<string, string> = {
    large_cap: "Large Cap", mid_cap: "Mid Cap", small_cap: "Small Cap",
    multi_cap: "Multi Cap", flexi_cap: "Flexi Cap", elss: "ELSS",
    sectoral: "Sectoral / Thematic", value: "Value / Contra",
    dividend_yield: "Dividend Yield", focused: "Focused",
  };

  const SortIcon = ({ col }: { col: string }) => {
    if (sortBy !== col) return <span className="text-bloomberg-dim/30 ml-1">↕</span>;
    return <span className="text-bloomberg-cyan ml-1">{sortOrder === "desc" ? "↓" : "↑"}</span>;
  };

  const ScoreBadge = ({ score }: { score: number | null }) => {
    if (score == null) return <span className="text-bloomberg-dim">—</span>;
    const color =
      score >= 80 ? "text-bloomberg-green" :
      score >= 60 ? "text-bloomberg-cyan" :
      score >= 40 ? "text-bloomberg-yellow" :
      "text-bloomberg-red";
    return (
      <span className={`font-mono font-bold ${color} ${score >= 80 ? "text-glow" : ""}`}>
        {score.toFixed(0)}
      </span>
    );
  };

  return (
    <div className="p-4 md:p-6 space-y-4">
      {/* Summary */}
      {data && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {data.tabs.filter(t => t.key === tab).map(t => (
            <div key={t.key} className="bg-bloomberg-surface border border-bloomberg-border rounded p-3 col-span-2 md:col-span-1">
              <div className="text-xs text-bloomberg-dim uppercase">{tabLabels[t.key] || t.key}</div>
              <div className="flex items-baseline gap-3 mt-1">
                <span className="text-xl font-semibold text-bloomberg-text">{t.count.toLocaleString()}</span>
                <span className="text-xs font-mono text-bloomberg-cyan">{t.total_aum_cr ? formatAum(t.total_aum_cr) : "—"}</span>
              </div>
            </div>
          ))}
          <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-3">
            <div className="text-xs text-bloomberg-dim uppercase">Data Source</div>
            <div className="text-sm font-semibold text-bloomberg-green mt-1">AMFI + MFAPI.in</div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex flex-wrap gap-1 border-b border-bloomberg-border pb-1">
        {data?.tabs.map(t => (
          <button
            key={t.key}
            onClick={() => { setTab(t.key); setSubCategory(undefined); }}
            className={`px-3 py-1.5 text-xs rounded-t transition-colors whitespace-nowrap ${
              tab === t.key
                ? "bg-bloomberg-surface border-l border-t border-r border-bloomberg-border text-bloomberg-text font-semibold -mb-[1px] border-b-2 border-b-bloomberg-cyan"
                : "text-bloomberg-dim hover:text-bloomberg-text hover:bg-bloomberg-highlight"
            }`}
          >
            {tabLabels[t.key] || t.key}
            <span className="ml-1.5 text-[10px] text-bloomberg-dim font-normal">
              {t.count.toLocaleString()}
            </span>
          </button>
        ))}
      </div>

      {/* Sub-category pills (equity only) */}
      {tab === "equity" && data && data.sub_categories.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          <button
            onClick={() => setSubCategory(undefined)}
            className={`text-[10px] px-2 py-1 rounded-full transition-colors ${
              !subCategory
                ? "bg-bloomberg-cyan/20 text-bloomberg-cyan border border-bloomberg-cyan/30"
                : "bg-bloomberg-highlight text-bloomberg-dim hover:text-bloomberg-text border border-transparent"
            }`}
          >
            All
          </button>
          {data.sub_categories.map(sc => (
            <button
              key={sc.key}
              onClick={() => setSubCategory(sc.key)}
              className={`text-[10px] px-2 py-1 rounded-full transition-colors ${
                subCategory === sc.key
                  ? "bg-bloomberg-cyan/20 text-bloomberg-cyan border border-bloomberg-cyan/30"
                  : "bg-bloomberg-highlight text-bloomberg-dim hover:text-bloomberg-text border border-transparent"
              }`}
            >
              {subCatLabels[sc.key] || sc.key.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())}
              <span className="ml-1 text-[9px] opacity-60">{sc.count}</span>
            </button>
          ))}
        </div>
      )}

      {/* Top Picks */}
      {data && data.top_picks.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2">
          {data.top_picks.map(pick => (
            <div
              key={pick.scheme_code}
              onClick={() => router.push(`/funds/${pick.scheme_code}`)}
              className="bg-bloomberg-surface border border-bloomberg-border rounded p-2.5 cursor-pointer hover:border-bloomberg-cyan/50 transition-all group"
            >
              <div className="text-[9px] text-bloomberg-dim uppercase mb-1">
                {subCatLabels[pick.sub_category || ""] || pick.sub_category?.replace(/_/g, " ") || "Top Pick"}
              </div>
              <div className="text-xs text-bloomberg-text truncate group-hover:text-bloomberg-cyan transition-colors">
                {pick.scheme_name}
              </div>
              <div className="flex items-center gap-2 mt-1.5">
                <ScoreBadge score={pick.composite_score} />
                <span className="text-[10px] font-mono text-bloomberg-green">{formatPct(pick.return_1y)}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Sort controls */}
      <div className="flex items-center gap-2 text-[10px] text-bloomberg-dim">
        <span>Sort by:</span>
        {SORT_OPTIONS.map(opt => (
          <button
            key={opt.key}
            onClick={() => handleSort(opt.key)}
            className={`px-2 py-0.5 rounded transition-colors ${
              sortBy === opt.key
                ? "bg-bloomberg-cyan/20 text-bloomberg-cyan"
                : "hover:text-bloomberg-text"
            }`}
          >
            {opt.label}
            <SortIcon col={opt.key} />
          </button>
        ))}
      </div>

      {/* Loading */}
      {loading && (
        <div className="space-y-2">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="skeleton h-9 w-full" />
          ))}
        </div>
      )}

      {error && (
        <div className="bg-bloomberg-surface border border-bloomberg-red/30 rounded p-3 text-sm text-bloomberg-red">{error}</div>
      )}

      {/* Fund table */}
      {!loading && data && data.funds.length > 0 && (
        <>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-bloomberg-dim border-b border-bloomberg-border">
                  <th className="text-left py-2 px-2 font-medium">Scheme Name</th>
                  <th className="text-left py-2 px-2 font-medium">Category</th>
                  <th className="text-right py-2 px-2 font-medium">NAV</th>
                  <th className="text-right py-2 px-2 font-medium">1Y</th>
                  <th className="text-right py-2 px-2 font-medium">3Y Roll</th>
                  <th className="text-right py-2 px-2 font-medium">5Y Roll</th>
                  <th className="text-right py-2 px-2 font-medium">Expense</th>
                  <th className="text-right py-2 px-2 font-medium">AUM</th>
                  <th className="text-right py-2 px-2 font-medium">Risk</th>
                  <th className="text-right py-2 px-2 font-medium">Score</th>
                </tr>
              </thead>
              <tbody>
                {data.funds.map(f => (
                  <tr
                    key={f.scheme_code}
                    className="border-b border-bloomberg-border hover:bg-bloomberg-highlight transition-colors cursor-pointer"
                    onClick={() => router.push(`/funds/${f.scheme_code}`)}
                  >
                    <td className="py-2 px-2 text-bloomberg-text truncate max-w-[260px]">{f.scheme_name}</td>
                    <td className="py-2 px-2 text-bloomberg-dim">{f.sub_category?.replace(/_/g, " ") || f.scheme_category || "—"}</td>
                    <td className="py-2 px-2 text-right font-mono">{formatNum(f.nav)}</td>
                    <td className={`py-2 px-2 text-right font-mono ${(f.return_1y ?? 0) >= 0 ? "text-bloomberg-green" : "text-bloomberg-red"}`}>
                      {formatPct(f.return_1y)}
                    </td>
                    <td className={`py-2 px-2 text-right font-mono ${(f.rolling_return_3y_avg ?? 0) >= 0 ? "text-bloomberg-green" : "text-bloomberg-red"}`}>
                      {formatPct(f.rolling_return_3y_avg)}
                    </td>
                    <td className={`py-2 px-2 text-right font-mono ${(f.rolling_return_5y_avg ?? 0) >= 0 ? "text-bloomberg-green" : "text-bloomberg-red"}`}>
                      {formatPct(f.rolling_return_5y_avg)}
                    </td>
                    <td className="py-2 px-2 text-right font-mono text-bloomberg-dim">
                      {formatNum(f.expense_ratio, 2)}%
                    </td>
                    <td className="py-2 px-2 text-right font-mono text-bloomberg-cyan">
                      {formatAum(f.aum_cr)}
                    </td>
                    <td className="py-2 px-2 text-right">
                      <span className={`inline-block px-1.5 py-0.5 rounded text-[9px] font-medium ${
                        f.risk_level === "Very High" ? "bg-red-900/40 text-red-400" :
                        f.risk_level === "High" ? "bg-orange-900/40 text-orange-400" :
                        f.risk_level === "Moderate" ? "bg-yellow-900/40 text-yellow-400" :
                        f.risk_level === "Low" ? "bg-green-900/40 text-green-400" :
                        "bg-bloomberg-dim/10 text-bloomberg-dim"
                      }`}>{f.risk_level || "—"}</span>
                    </td>
                    <td className="py-2 px-2 text-right"><ScoreBadge score={f.composite_score} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {data.total_pages > 1 && (
            <div className="flex items-center justify-center gap-2 text-xs">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="px-3 py-1.5 bg-bloomberg-surface border border-bloomberg-border rounded hover:bg-bloomberg-highlight disabled:opacity-30 transition-colors"
              >
                Previous
              </button>
              <span className="text-bloomberg-dim font-mono">{page} / {data.total_pages}</span>
              <button
                onClick={() => setPage(p => Math.min(data.total_pages, p + 1))}
                disabled={page >= data.total_pages}
                className="px-3 py-1.5 bg-bloomberg-surface border border-bloomberg-border rounded hover:bg-bloomberg-highlight disabled:opacity-30 transition-colors"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}

      {!loading && !error && data && data.funds.length === 0 && (
        <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-6 text-center text-sm text-bloomberg-dim">
          No funds in this category. Run the enrichment script to populate data.
        </div>
      )}

      <div className="text-xs text-bloomberg-dim border-t border-bloomberg-border pt-3">
        Data sourced from AMFI India + MFAPI.in + mfdata.in. Composite scores are peer-relative within each category group.
        Past performance does not guarantee future returns.
      </div>
    </div>
  );
}
