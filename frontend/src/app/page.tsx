"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { listFunds, Fund } from "@/lib/api";

export default function DashboardPage() {
  const [topFunds, setTopFunds] = useState<Fund[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await listFunds(1, 10);
        setTopFunds(data.funds);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load funds");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const summaryCards = [
    { label: "Total Schemes Tracked", value: loading ? "—" : "3,000+", color: "text-bloomberg-cyan" },
    { label: "Categories", value: "30+", color: "text-bloomberg-green" },
    { label: "Data Source", value: "MFAPI.in", color: "text-bloomberg-yellow" },
    { label: "Status", value: "Live", color: "text-bloomberg-green" },
  ];

  return (
    <div className="p-4 md:p-6 space-y-6">
      {/* Market Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {summaryCards.map((card) => (
          <div
            key={card.label}
            className="bg-bloomberg-surface border border-bloomberg-border rounded p-3"
          >
            <div className="text-[10px] text-bloomberg-dim uppercase tracking-wider">{card.label}</div>
            <div className={`text-lg font-mono font-semibold mt-1 ${card.color}`}>{card.value}</div>
          </div>
        ))}
      </div>

      {/* Quick Search */}
      <div>
        <Link
          href="/funds"
          className="inline-flex items-center gap-2 bg-bloomberg-surface border border-bloomberg-border rounded px-4 py-2.5 text-sm text-bloomberg-dim hover:text-bloomberg-text hover:border-bloomberg-cyan transition-colors w-full md:w-auto"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          Search mutual funds by name, AMC, or category...
        </Link>
      </div>

      {/* Top Funds */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-bloomberg-text">Available Funds</h2>
          <Link href="/funds" className="text-[11px] text-bloomberg-cyan hover:underline">
            View All
          </Link>
        </div>

        {loading && (
          <div className="space-y-2">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="skeleton h-8 w-full" />
            ))}
          </div>
        )}

        {error && (
          <div className="bg-bloomberg-surface border border-bloomberg-red/30 rounded p-4 text-sm text-bloomberg-red">
            {error}
          </div>
        )}

        {!loading && !error && topFunds.length === 0 && (
          <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-6 text-center text-sm text-bloomberg-dim">
            No funds loaded yet. Run the seed script to populate the database.
          </div>
        )}

        {!loading && topFunds.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-bloomberg-dim border-b border-bloomberg-border">
                  <th className="text-left py-2 px-2 font-medium">Scheme Name</th>
                  <th className="text-left py-2 px-2 font-medium">Category</th>
                  <th className="text-right py-2 px-2 font-medium">NAV</th>
                  <th className="text-right py-2 px-2 font-medium">1Y Return</th>
                  <th className="text-right py-2 px-2 font-medium">Expense Ratio</th>
                </tr>
              </thead>
              <tbody>
                {topFunds.map((fund) => (
                  <tr
                    key={fund.id}
                    className="border-b border-bloomberg-border hover:bg-bloomberg-highlight transition-colors cursor-pointer"
                    onClick={() => window.location.href = `/funds/${fund.scheme_code}`}
                  >
                    <td className="py-2 px-2 text-bloomberg-text truncate max-w-[300px]">
                      {fund.scheme_name}
                    </td>
                    <td className="py-2 px-2 text-bloomberg-dim">{fund.scheme_category || "—"}</td>
                    <td className="py-2 px-2 text-right font-mono">{fund.nav?.toFixed(2) || "—"}</td>
                    <td className={`py-2 px-2 text-right font-mono ${(fund.return_1y ?? 0) >= 0 ? "text-bloomberg-green" : "text-bloomberg-red"}`}>
                      {fund.return_1y != null ? `${fund.return_1y.toFixed(2)}%` : "—"}
                    </td>
                    <td className="py-2 px-2 text-right font-mono">{fund.expense_ratio != null ? `${fund.expense_ratio.toFixed(2)}%` : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Risk Disclaimer */}
      <div className="text-[10px] text-bloomberg-dim border-t border-bloomberg-border pt-3">
        ⚠ This platform is for research and educational purposes only. It is not personalized investment advice.
        Past performance does not guarantee future returns. Consult a SEBI-registered investment advisor for
        investment decisions.
      </div>
    </div>
  );
}
