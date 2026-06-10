"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getFund, Fund } from "@/lib/api";

export default function FundDetailPage() {
  const params = useParams();
  const schemeCode = Number(params.code);
  const [fund, setFund] = useState<Fund | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await getFund(schemeCode);
        setFund(data);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load fund details");
      } finally {
        setLoading(false);
      }
    }
    if (schemeCode) load();
  }, [schemeCode]);

  if (loading) {
    return (
      <div className="p-4 md:p-6 space-y-4">
        <div className="skeleton h-5 w-64" />
        <div className="skeleton h-8 w-full" />
        <div className="skeleton h-32 w-full" />
      </div>
    );
  }

  if (error || !fund) {
    return (
      <div className="p-4 md:p-6">
        <div className="bg-bloomberg-surface border border-bloomberg-red/30 rounded p-4 text-sm text-bloomberg-red">
          {error || "Fund not found"}
        </div>
        <Link href="/funds" className="text-bloomberg-cyan text-sm hover:underline mt-4 inline-block">
          ← Back to Fund Screener
        </Link>
      </div>
    );
  }

  const metrics = [
    { label: "NAV", value: fund.nav?.toFixed(2) || "—" },
    { label: "NAV Date", value: fund.nav_date || "—" },
    { label: "Category", value: fund.scheme_category || "—" },
    { label: "Type", value: fund.scheme_type || "—" },
    { label: "AMC", value: fund.amc || fund.fund_family || "—" },
    { label: "AUM (Cr)", value: fund.aum_cr != null ? `₹${fund.aum_cr.toFixed(2)}` : "—" },
    { label: "Expense Ratio", value: fund.expense_ratio != null ? `${fund.expense_ratio.toFixed(2)}%` : "—" },
    { label: "Risk Level", value: fund.risk_level || "—" },
    { label: "Benchmark", value: fund.benchmark || "—" },
    { label: "Fund Manager", value: fund.fund_manager || "—" },
  ];

  return (
    <div className="p-4 md:p-6 space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-xs text-bloomberg-dim">
        <Link href="/" className="hover:text-bloomberg-text">Dashboard</Link>
        <span>/</span>
        <Link href="/funds" className="hover:text-bloomberg-text">Fund Screener</Link>
        <span>/</span>
        <span className="text-bloomberg-cyan truncate max-w-[300px]">{fund.scheme_name}</span>
      </div>

      {/* Fund Header */}
      <div>
        <h1 className="text-base font-semibold text-bloomberg-text leading-tight">
          {fund.scheme_name}
        </h1>
        <div className="flex items-center gap-3 mt-1 text-[11px] text-bloomberg-dim">
          <span>{fund.scheme_category || "Uncategorized"}</span>
          <span className="w-1 h-1 rounded-full bg-bloomberg-border" />
          <span>Code: {fund.scheme_code}</span>
          {fund.isin && (
            <>
              <span className="w-1 h-1 rounded-full bg-bloomberg-border" />
              <span>ISIN: {fund.isin}</span>
            </>
          )}
        </div>
      </div>

      {/* Metrics grid */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {metrics.map((m) => (
          <div key={m.label} className="bg-bloomberg-surface border border-bloomberg-border rounded p-3">
            <div className="text-[10px] text-bloomberg-dim uppercase tracking-wider">{m.label}</div>
            <div className="text-sm font-mono text-bloomberg-text mt-1">{m.value}</div>
          </div>
        ))}
      </div>

      {/* Returns */}
      <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-4">
        <h2 className="text-sm font-semibold text-bloomberg-text mb-3">Returns</h2>
        <div className="grid grid-cols-3 gap-3">
          {[
            { label: "1 Year", value: fund.return_1y },
            { label: "3 Years (CAGR)", value: fund.return_3y },
            { label: "5 Years (CAGR)", value: fund.return_5y },
          ].map((r) => (
            <div key={r.label} className="text-center">
              <div className="text-[10px] text-bloomberg-dim uppercase">{r.label}</div>
              <div
                className={`text-lg font-mono font-semibold ${
                  r.value != null ? (r.value >= 0 ? "text-bloomberg-green" : "text-bloomberg-red") : "text-bloomberg-dim"
                }`}
              >
                {r.value != null ? `${r.value.toFixed(2)}%` : "—"}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Placeholder for charts */}
      <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-4">
        <h2 className="text-sm font-semibold text-bloomberg-text mb-3">NAV History</h2>
        <div className="h-48 flex items-center justify-center text-bloomberg-dim text-xs border border-dashed border-bloomberg-border rounded">
          NAV chart will be rendered here with ECharts (coming in Phase 2)
        </div>
      </div>

      {/* Risk Disclosure */}
      <div className="text-[10px] text-bloomberg-dim border-t border-bloomberg-border pt-3">
        ⚠ Past performance is not indicative of future returns. This data is for informational purposes only
        and does not constitute investment advice. Please consult a SEBI-registered investment advisor.
      </div>
    </div>
  );
}
