"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { listManagers, ManagerResponse } from "@/lib/api";

export default function ManagersPage() {
  const router = useRouter();
  const [managers, setManagers] = useState<ManagerResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<ManagerResponse | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await listManagers();
        setManagers(data);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load managers");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const formatPct = (v: number | null | undefined) =>
    v != null ? `${v >= 0 ? "+" : ""}${v.toFixed(2)}%` : "—";

  const formatAum = (v: number | null | undefined) =>
    v != null ? `₹${(v / 1000).toFixed(1)}K Cr` : "—";

  if (loading) {
    return (
      <div className="p-4 md:p-6 space-y-4">
        <div className="skeleton h-5 w-48" />
        <div className="skeleton h-64 w-full" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 md:p-6">
        <div className="bg-bloomberg-surface border border-bloomberg-red/30 rounded p-4 text-sm text-bloomberg-red">{error}</div>
      </div>
    );
  }

  return (
    <div className="p-4 md:p-6 space-y-4">
      <h1 className="text-sm font-semibold text-bloomberg-text">Fund Manager Analysis</h1>

      {/* Stats summary */}
      <div className="grid grid-cols-4 gap-3">
        <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-3">
          <div className="text-[10px] text-bloomberg-dim uppercase">Total Managers</div>
          <div className="text-lg font-mono font-semibold text-bloomberg-text">{managers.length}</div>
        </div>
        <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-3">
          <div className="text-[10px] text-bloomberg-dim uppercase">Top 1Y Avg Return</div>
          <div className="text-lg font-mono font-semibold text-bloomberg-green">
            {managers.length > 0 ? formatPct(managers[0].avg_return_1y) : "—"}
          </div>
        </div>
        <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-3">
          <div className="text-[10px] text-bloomberg-dim uppercase">Largest AUM</div>
          <div className="text-lg font-mono font-semibold text-bloomberg-cyan">
            {managers.length > 0 ? formatAum(managers[0].total_aum_cr) : "—"}
          </div>
        </div>
        <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-3">
          <div className="text-[10px] text-bloomberg-dim uppercase">Top Manager</div>
          <div className="text-sm font-semibold text-bloomberg-yellow truncate">
            {managers.length > 0 ? managers[0].manager_name : "—"}
          </div>
        </div>
      </div>

      {/* Manager list */}
      <div className="grid md:grid-cols-3 gap-4">
        {/* Sidebar */}
        <div className="bg-bloomberg-surface border border-bloomberg-border rounded overflow-hidden">
          <div className="text-[10px] text-bloomberg-dim uppercase px-3 py-2 border-b border-bloomberg-border">Managers</div>
          <div className="overflow-y-auto max-h-[600px]">
            {managers.map((m) => (
              <div
                key={m.manager_name}
                onClick={() => setSelected(m)}
                className={`px-3 py-2 border-b border-bloomberg-border cursor-pointer transition-colors ${
                  selected?.manager_name === m.manager_name
                    ? "bg-bloomberg-highlight border-l-2 border-l-bloomberg-cyan"
                    : "hover:bg-bloomberg-highlight"
                }`}
              >
                <div className="text-xs text-bloomberg-text truncate">{m.manager_name}</div>
                <div className="text-[10px] text-bloomberg-dim mt-0.5">
                  {m.total_funds} funds · {m.categories.length} categories
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Detail */}
        <div className="md:col-span-2">
          {selected ? (
            <div className="space-y-4">
              <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-4">
                <h2 className="text-sm font-semibold text-bloomberg-text">{selected.manager_name}</h2>
                <div className="grid grid-cols-4 gap-3 mt-3">
                  <div>
                    <div className="text-[10px] text-bloomberg-dim">Funds Managed</div>
                    <div className="text-base font-mono font-semibold text-bloomberg-text">{selected.total_funds}</div>
                  </div>
                  <div>
                    <div className="text-[10px] text-bloomberg-dim">Avg 1Y Return</div>
                    <div className={`text-base font-mono font-semibold ${(selected.avg_return_1y ?? 0) >= 0 ? "text-bloomberg-green" : "text-bloomberg-red"}`}>
                      {formatPct(selected.avg_return_1y)}
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] text-bloomberg-dim">Avg 3Y CAGR</div>
                    <div className={`text-base font-mono font-semibold ${(selected.avg_return_3y ?? 0) >= 0 ? "text-bloomberg-green" : "text-bloomberg-red"}`}>
                      {formatPct(selected.avg_return_3y)}
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] text-bloomberg-dim">Total AUM</div>
                    <div className="text-base font-mono font-semibold text-bloomberg-cyan">{formatAum(selected.total_aum_cr)}</div>
                  </div>
                </div>
                {selected.categories.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-3">
                    {selected.categories.map(c => (
                      <span key={c} className="text-[10px] px-1.5 py-0.5 rounded bg-bloomberg-highlight text-bloomberg-dim">{c}</span>
                    ))}
                  </div>
                )}
              </div>

              <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-4">
                <h3 className="text-xs font-semibold text-bloomberg-text mb-3">Managed Funds</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="text-bloomberg-dim border-b border-bloomberg-border">
                        <th className="text-left py-2 px-2 font-medium">Scheme Name</th>
                        <th className="text-left py-2 px-2 font-medium">Category</th>
                        <th className="text-right py-2 px-2 font-medium">1Y Return</th>
                        <th className="text-right py-2 px-2 font-medium">3Y CAGR</th>
                        <th className="text-right py-2 px-2 font-medium">AUM (Cr)</th>
                        <th className="text-right py-2 px-2 font-medium">Expense Ratio</th>
                        <th className="text-right py-2 px-2 font-medium">Risk</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selected.funds.map((f) => (
                        <tr
                          key={f.scheme_code}
                          className="border-b border-bloomberg-border hover:bg-bloomberg-highlight transition-colors cursor-pointer"
                          onClick={() => router.push(`/funds/${f.scheme_code}`)}
                        >
                          <td className="py-2 px-2 text-bloomberg-text truncate max-w-[250px]">{f.scheme_name}</td>
                          <td className="py-2 px-2 text-bloomberg-dim">{f.category || "—"}</td>
                          <td className={`py-2 px-2 text-right font-mono ${(f.return_1y ?? 0) >= 0 ? "text-bloomberg-green" : "text-bloomberg-red"}`}>
                            {formatPct(f.return_1y)}
                          </td>
                          <td className={`py-2 px-2 text-right font-mono ${(f.return_3y ?? 0) >= 0 ? "text-bloomberg-green" : "text-bloomberg-red"}`}>
                            {formatPct(f.return_3y)}
                          </td>
                          <td className="py-2 px-2 text-right font-mono">{f.aum_cr != null ? `₹${f.aum_cr.toFixed(0)}` : "—"}</td>
                          <td className="py-2 px-2 text-right font-mono">{f.expense_ratio != null ? `${f.expense_ratio.toFixed(2)}%` : "—"}</td>
                          <td className="py-2 px-2 text-right">
                            <span className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-medium ${
                              f.risk_level === "Very High" ? "bg-red-900/40 text-red-400" :
                              f.risk_level === "High" ? "bg-orange-900/40 text-orange-400" :
                              f.risk_level === "Moderate" ? "bg-yellow-900/40 text-yellow-400" :
                              f.risk_level === "Low" ? "bg-green-900/40 text-green-400" :
                              f.risk_level === "Very Low" ? "bg-teal-900/40 text-teal-400" :
                              "bg-bloomberg-dim/10 text-bloomberg-dim"
                            }`}>{f.risk_level || "—"}</span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-6 text-center text-sm text-bloomberg-dim">
              Select a manager from the list to view their fund portfolio
            </div>
          )}
        </div>
      </div>

      <div className="text-[10px] text-bloomberg-dim border-t border-bloomberg-border pt-3">
        Manager data sourced from scheme filings. Past performance does not guarantee future returns.
      </div>
    </div>
  );
}
