"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import ContextMenu from "@/components/ContextMenu";
import {
  getDashboard,
  getSwpRecommendations,
  getSipRecommendations,
  getDataStatus,
  compareFunds,
  DashboardResponse,
  DashboardTab,
  SubCategoryInfo,
  FundRow,
  TopPick,
  CompareResponse,
  RecommendationFund,
} from "@/lib/api";

const SORT_OPTIONS: { key: string; label: string }[] = [
  { key: "future_return_indicator", label: "Future" },
  { key: "composite_score", label: "Score" },
  { key: "rolling_return_1y_avg", label: "1Y Return" },
  { key: "rolling_return_3y_avg", label: "3Y Roll" },
  { key: "rolling_return_5y_avg", label: "5Y Roll" },
  { key: "aum_cr", label: "AUM" },
  { key: "expense_ratio", label: "Expense" },
  { key: "nav", label: "NAV" },
  { key: "fund_age_years", label: "Age" },
  { key: "backtest_confidence", label: "Confidence" },
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
  const [compareSelection, setCompareSelection] = useState<FundRow[]>([]);
  const [compareResult, setCompareResult] = useState<CompareResponse | null>(null);
  const [comparing, setComparing] = useState(false);
  const [contextMenu, setContextMenu] = useState<{ fund: FundRow; x: number; y: number } | null>(null);
  const [swpRecs, setSwpRecs] = useState<RecommendationFund[]>([]);
  const [sipRecs, setSipRecs] = useState<RecommendationFund[]>([]);
  const [lastUpdate, setLastUpdate] = useState<string | null>(null);
  const compareRef = useRef<HTMLDivElement>(null);

  const handleCompare = async () => {
    setComparing(true);
    try {
      const r = await compareFunds(compareSelection.map(f => f.scheme_code));
      setCompareResult(r);
      setTimeout(() => compareRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 100);
    } catch { /* ignore */ }
    setComparing(false);
    setContextMenu(null);
  };

  const handleSwp = (fund: FundRow) => {
    router.push(`/swp?scheme_code=${fund.scheme_code}`);
  };

  const toggleCompare = (f: FundRow) => {
    setCompareSelection(prev => {
      const exists = prev.find(s => s.scheme_code === f.scheme_code);
      if (exists) return prev.filter(s => s.scheme_code !== f.scheme_code);
      if (prev.length >= 5) return prev;
      return [...prev, f];
    });
  };

  useEffect(() => {
    setPage(1);
  }, [tab, subCategory, sortBy, sortOrder]);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [d, swp, sip, ds] = await Promise.all([
          getDashboard(tab, subCategory, sortBy, sortOrder, page, 20),
          getSwpRecommendations(5),
          getSipRecommendations(5),
          getDataStatus(),
        ]);
        setData(d);
        setSwpRecs(swp.funds);
        setSipRecs(sip.funds);
        setLastUpdate(ds.last_update);
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
      ? v >= 100000
        ? `₹${(v / 100000).toFixed(1)}L Cr`
        : v >= 1000
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
            <div className="text-xs text-bloomberg-dim uppercase">Top SWP Picks</div>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-lg font-semibold text-bloomberg-cyan">{swpRecs.length}</span>
              <span className="text-[10px] text-bloomberg-dim">funds</span>
            </div>
          </div>
          <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-3">
            <div className="text-xs text-bloomberg-dim uppercase">Top SIP Picks</div>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-lg font-semibold text-bloomberg-green">{sipRecs.length}</span>
              <span className="text-[10px] text-bloomberg-dim">funds</span>
            </div>
          </div>
          <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-3">
            <div className="text-xs text-bloomberg-dim uppercase">Data</div>
            <div className="flex flex-col mt-1">
              <span className="text-sm font-semibold text-bloomberg-green">AMFI + MFAPI.in</span>
              {lastUpdate && (
                <span className="text-[10px] font-mono text-bloomberg-dim">
                  {new Date(lastUpdate).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}
                </span>
              )}
            </div>
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

      {/* Recommendation section */}
      {!loading && (swpRecs.length > 0 || sipRecs.length > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {swpRecs.length > 0 && (
            <div className="bg-bloomberg-surface border border-bloomberg-border rounded">
              <div className="px-3 py-2 border-b border-bloomberg-border flex items-center justify-between">
                <span className="text-xs font-semibold text-bloomberg-cyan uppercase tracking-wider">Top SWP Picks</span>
                <span className="text-[9px] text-bloomberg-dim">Capital Preservation</span>
              </div>
              <div className="divide-y divide-bloomberg-border">
                {swpRecs.map((f, i) => (
                  <div
                    key={f.scheme_code}
                    onClick={() => router.push(`/funds/${f.scheme_code}`)}
                    className="flex items-center gap-2 px-3 py-2 hover:bg-bloomberg-highlight cursor-pointer transition-colors"
                  >
                    <span className="text-[10px] font-mono text-bloomberg-dim w-4 shrink-0">{i + 1}</span>
                    <div className="flex-1 min-w-0">
                      <div className="text-xs text-bloomberg-text truncate">{f.scheme_name}</div>
                      <div className="text-[9px] text-bloomberg-dim">
                        {f.category_group}
                        {f.sub_category ? ` · ${f.sub_category.replace(/_/g, " ")}` : ""}
                        {f.risk_level ? ` · ${f.risk_level}` : ""}
                      </div>
                    </div>
                    <div className="text-right shrink-0">
                      <div className="text-xs font-mono text-bloomberg-green">{f.rec_score?.toFixed(1)}</div>
                      <div className="text-[9px] text-bloomberg-dim">Score</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          {sipRecs.length > 0 && (
            <div className="bg-bloomberg-surface border border-bloomberg-border rounded">
              <div className="px-3 py-2 border-b border-bloomberg-border flex items-center justify-between">
                <span className="text-xs font-semibold text-bloomberg-green uppercase tracking-wider">Top SIP Picks</span>
                <span className="text-[9px] text-bloomberg-dim">Wealth Creation</span>
              </div>
              <div className="divide-y divide-bloomberg-border">
                {sipRecs.map((f, i) => (
                  <div
                    key={f.scheme_code}
                    onClick={() => router.push(`/funds/${f.scheme_code}`)}
                    className="flex items-center gap-2 px-3 py-2 hover:bg-bloomberg-highlight cursor-pointer transition-colors"
                  >
                    <span className="text-[10px] font-mono text-bloomberg-dim w-4 shrink-0">{i + 1}</span>
                    <div className="flex-1 min-w-0">
                      <div className="text-xs text-bloomberg-text truncate">{f.scheme_name}</div>
                      <div className="text-[9px] text-bloomberg-dim">
                        {f.category_group}
                        {f.sub_category ? ` · ${f.sub_category.replace(/_/g, " ")}` : ""}
                        {f.risk_level ? ` · ${f.risk_level}` : ""}
                      </div>
                    </div>
                    <div className="text-right shrink-0">
                      <div className="text-xs font-mono text-bloomberg-green">{f.rec_score?.toFixed(1)}</div>
                      <div className="text-[9px] text-bloomberg-dim">Score</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
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
                  <th className="text-right py-2 px-2 font-medium">Age</th>
                  <th className="text-right py-2 px-2 font-medium">Risk</th>
                  <th className="text-right py-2 px-2 font-medium">Future</th>
                  <th className="text-right py-2 px-2 font-medium">Conf</th>
                  <th className="text-right py-2 px-2 font-medium">Score</th>
                </tr>
              </thead>
              <tbody>
                {data.funds.map(f => (
                  <tr
                    key={f.scheme_code}
                    className={`border-b border-bloomberg-border hover:bg-bloomberg-highlight transition-colors cursor-pointer ${compareSelection.some(s => s.scheme_code === f.scheme_code) ? "border-l-2 border-l-bloomberg-cyan bg-bloomberg-cyan/[0.03]" : ""}`}
                    onClick={() => router.push(`/funds/${f.scheme_code}`)}
                    onContextMenu={(e) => { e.preventDefault(); setContextMenu({ fund: f, x: e.clientX, y: e.clientY }); }}
                  >
                    <td className="py-2 px-2 text-bloomberg-text truncate max-w-[240px]">{f.scheme_name}</td>
                    <td className="py-2 px-2 text-bloomberg-dim">{f.sub_category?.replace(/_/g, " ") || f.scheme_category || "—"}</td>
                    <td className="py-2 px-2 text-right font-mono">{formatNum(f.nav)}</td>
                    <td className={`py-2 px-2 text-right font-mono ${(f.rolling_return_1y_avg ?? 0) >= 0 ? "text-bloomberg-green" : "text-bloomberg-red"}`}>
                      {formatPct(f.rolling_return_1y_avg)}
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
                    <td className="py-2 px-2 text-right font-mono text-bloomberg-dim">
                      {f.fund_age_years != null ? `${f.fund_age_years}Y` : "—"}
                    </td>
                    <td className="py-2 px-2 text-right">
                      <span className={`font-medium ${
                        f.risk_level === "Very High Risk" ? "text-red-400" :
                        f.risk_level === "High Risk" ? "text-orange-400" :
                        f.risk_level === "Moderate Risk" ? "text-yellow-400" :
                        f.risk_level === "Low Risk" ? "text-green-400" :
                        f.risk_level === "Very Low Risk" ? "text-emerald-400" :
                        "text-bloomberg-dim"
                      }`}>{f.risk_level || "—"}</span>
                    </td>
                      <td className="py-2 px-2 text-right"><ScoreBadge score={f.future_return_indicator} /></td>
                      <td className="py-2 px-2 text-right font-mono text-bloomberg-dim">
                        {f.backtest_confidence != null ? (f.backtest_confidence * 100).toFixed(0) + "%" : "—"}
                      </td>
                      <td className="py-2 px-2 text-right"><ScoreBadge score={f.composite_score} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {contextMenu && (
            <ContextMenu
              fund={contextMenu.fund}
              x={contextMenu.x}
              y={contextMenu.y}
              isSelected={compareSelection.some(s => s.scheme_code === contextMenu.fund.scheme_code)}
              compareSelection={compareSelection}
              onCompare={toggleCompare}
              onRemoveFromCompare={(f) => setCompareSelection(prev => prev.filter(s => s.scheme_code !== f.scheme_code))}
              onCompareNow={handleCompare}
              comparing={comparing}
              onSwp={handleSwp}
              onClose={() => setContextMenu(null)}
            />
          )}

          {/* Compare selection bar */}
          {compareSelection.length > 0 && (
            <div className="sticky bottom-0 z-40 bg-bloomberg-surface border border-bloomberg-border rounded-t-lg shadow-lg px-3 py-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5 flex-1 flex-wrap">
                  {compareSelection.map(f => (
                    <span
                      key={f.scheme_code}
                      className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] bg-bloomberg-highlight text-bloomberg-text"
                    >
                      {f.scheme_name.length > 20 ? f.scheme_name.slice(0, 20) + "…" : f.scheme_name}
                      <button
                        onClick={() => setCompareSelection(prev => prev.filter(s => s.scheme_code !== f.scheme_code))}
                        className="text-bloomberg-dim hover:text-bloomberg-red transition-colors"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                  <span className="text-[10px] text-bloomberg-dim">{compareSelection.length}/5</span>
                </div>
                <div className="flex items-center gap-2 shrink-0 ml-2">
                  <button
                    onClick={() => { setCompareSelection([]); setCompareResult(null); }}
                    className="text-[10px] text-bloomberg-dim hover:text-bloomberg-text transition-colors"
                  >
                    Clear
                  </button>
                  {compareSelection.length >= 2 && (
                    <button
                      onClick={handleCompare}
                      disabled={comparing}
                      className="text-[11px] bg-bloomberg-cyan text-black font-semibold px-3 py-1 rounded hover:opacity-90 disabled:opacity-30 transition-opacity"
                    >
                      {comparing ? "Comparing..." : "Compare"}
                    </button>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Comparison results */}
          {compareResult && (
            <div ref={compareRef} className="bg-bloomberg-surface border border-bloomberg-border rounded overflow-x-auto">
              <div className="flex items-center justify-between px-3 py-2 border-b border-bloomberg-border">
                <span className="text-xs font-semibold text-bloomberg-text">Comparison</span>
                <button
                  onClick={() => setCompareResult(null)}
                  className="text-[10px] text-bloomberg-dim hover:text-bloomberg-text transition-colors"
                >
                  Close
                </button>
              </div>
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-bloomberg-dim border-b border-bloomberg-border">
                    <th className="text-left py-2.5 px-3 font-medium w-32">Metric</th>
                    {compareResult.funds.map((f, i) => (
                      <th key={i} className="text-left py-2.5 px-3 font-medium text-bloomberg-text min-w-[160px]">
                        <a href={`/funds/${f.scheme_code}`} className="hover:text-bloomberg-cyan">
                          {f.scheme_name.length > 30 ? f.scheme_name.slice(0, 30) + "…" : f.scheme_name}
                        </a>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {compareResult.comparison.map((row) => (
                    <tr key={row.metric} className="border-b border-bloomberg-border hover:bg-bloomberg-highlight">
                      <td className="py-2.5 px-3 text-bloomberg-dim font-medium">{row.metric}</td>
                      {Object.entries(row.values).map(([code, val], i) => (
                        <td
                          key={i}
                          className={`py-2.5 px-3 font-mono ${
                            row.winner === code ? "text-bloomberg-green font-semibold" : "text-bloomberg-text"
                          }`}
                        >
                          {row.winner === code && <span className="mr-1">▶</span>}{val}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

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
