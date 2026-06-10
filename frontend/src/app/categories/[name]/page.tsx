"use client";

import { useEffect, useState, useRef } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import * as echarts from "echarts";
import { getCategory, CategoryResponse } from "@/lib/api";

export default function CategoryDetailPage() {
  const params = useParams();
  const categoryName = decodeURIComponent(params.name as string);
  const [data, setData] = useState<CategoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const chartRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getCategory(categoryName, 15)
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [categoryName]);

  useEffect(() => {
    if (!data || !chartRef.current || data.top_funds.length === 0) return;

    const chart = echarts.init(chartRef.current);
    const sorted = [...data.top_funds]
      .filter((f) => f.return_1y != null)
      .sort((a, b) => (b.return_1y ?? 0) - (a.return_1y ?? 0))
      .slice(0, 10);

    chart.setOption({
      backgroundColor: "transparent",
      grid: { left: 20, right: 80, top: 20, bottom: 20 },
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "shadow" },
        backgroundColor: "#13181f",
        borderColor: "#1e2a3a",
        textStyle: { color: "#c5d0e0", fontSize: 12 },
        formatter: (params: any) => {
          const p = params[0];
          const fund = sorted[p.dataIndex];
          return `<b>${fund.scheme_name}</b><br/>
            1Y: <span style="color:${(fund.return_1y ?? 0) >= 0 ? "#00c853" : "#ff1744"}">${fund.return_1y?.toFixed(2)}%</span><br/>
            3Y: ${fund.cagr_3y != null ? fund.cagr_3y.toFixed(2) + "%" : "—"}<br/>
            NAV: ${fund.nav ?? "—"}`;
        },
      },
      xAxis: {
        type: "value",
        axisLine: { lineStyle: { color: "#1e2a3a" } },
        axisLabel: { color: "#6a7a8e", fontSize: 10, formatter: "{value}%" },
        splitLine: { lineStyle: { color: "#1e2a3a", type: "dashed" } },
      },
      yAxis: {
        type: "category",
        data: sorted.map((f) => {
          const name = f.scheme_name.length > 30 ? f.scheme_name.slice(0, 30) + "…" : f.scheme_name;
          return name;
        }),
        axisLine: { show: false },
        axisLabel: { color: "#c5d0e0", fontSize: 10 },
        splitLine: { show: false },
      },
      series: [
        {
          type: "bar",
          data: sorted.map((f) => ({
            value: f.return_1y,
            itemStyle: {
              color: (f.return_1y ?? 0) >= 0
                ? new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                    { offset: 0, color: "rgba(0,200,83,0.3)" },
                    { offset: 1, color: "#00c853" },
                  ])
                : new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                    { offset: 0, color: "rgba(255,23,68,0.3)" },
                    { offset: 1, color: "#ff1744" },
                  ]),
            },
          })),
          barMaxWidth: 20,
        },
      ],
    });

    const handleResize = () => chart.resize();
    window.addEventListener("resize", handleResize);
    return () => {
      window.removeEventListener("resize", handleResize);
      chart.dispose();
    };
  }, [data]);

  return (
    <div className="p-4 md:p-6 space-y-4">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-xs text-bloomberg-dim">
        <Link href="/" className="hover:text-bloomberg-text">Dashboard</Link>
        <span>/</span>
        <Link href="/categories" className="hover:text-bloomberg-text">Categories</Link>
        <span>/</span>
        <span className="text-bloomberg-cyan">{categoryName}</span>
      </div>

      {loading && (
        <div className="space-y-3">
          <div className="skeleton h-5 w-48" />
          <div className="skeleton h-64 w-full" />
        </div>
      )}

      {error && (
        <div className="bg-bloomberg-surface border border-bloomberg-red/30 rounded p-3 text-sm text-bloomberg-red">
          {error}
        </div>
      )}

      {data && (
        <>
          {/* Category Summary */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-3">
              <div className="text-[10px] text-bloomberg-dim uppercase">Total Funds</div>
              <div className="text-lg font-mono font-semibold text-bloomberg-text">{data.total_funds}</div>
            </div>
            <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-3">
              <div className="text-[10px] text-bloomberg-dim uppercase">Avg 1Y Return</div>
              <div className={`text-lg font-mono font-semibold ${(data.avg_return_1y ?? 0) >= 0 ? "text-bloomberg-green" : "text-bloomberg-red"}`}>
                {data.avg_return_1y != null ? `${data.avg_return_1y.toFixed(2)}%` : "—"}
              </div>
            </div>
            <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-3">
              <div className="text-[10px] text-bloomberg-dim uppercase">Avg 3Y CAGR</div>
              <div className={`text-lg font-mono font-semibold ${(data.avg_cagr_3y ?? 0) >= 0 ? "text-bloomberg-green" : "text-bloomberg-red"}`}>
                {data.avg_cagr_3y != null ? `${data.avg_cagr_3y.toFixed(2)}%` : "—"}
              </div>
            </div>
            <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-3">
              <div className="text-[10px] text-bloomberg-dim uppercase">Avg 5Y CAGR</div>
              <div className={`text-lg font-mono font-semibold ${(data.avg_cagr_5y ?? 0) >= 0 ? "text-bloomberg-green" : "text-bloomberg-red"}`}>
                {data.avg_cagr_5y != null ? `${data.avg_cagr_5y.toFixed(2)}%` : "—"}
              </div>
            </div>
          </div>

          {/* Bar Chart */}
          <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-4">
            <h2 className="text-sm font-semibold text-bloomberg-text mb-3">Top Funds by 1Y Return</h2>
            <div ref={chartRef} className="h-72 w-full" />
          </div>

          {/* Top Funds Table */}
          <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-4">
            <h2 className="text-sm font-semibold text-bloomberg-text mb-3">Top Funds</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-bloomberg-dim border-b border-bloomberg-border">
                    <th className="text-left py-2 px-2 font-medium">Fund Name</th>
                    <th className="text-right py-2 px-2 font-medium">NAV</th>
                    <th className="text-right py-2 px-2 font-medium">1Y Return</th>
                    <th className="text-right py-2 px-2 font-medium">3Y CAGR</th>
                    <th className="text-right py-2 px-2 font-medium">5Y CAGR</th>
                    <th className="text-right py-2 px-2 font-medium">Expense Ratio</th>
                    <th className="text-right py-2 px-2 font-medium">AUM (Cr)</th>
                    <th className="text-right py-2 px-2 font-medium">Risk</th>
                  </tr>
                </thead>
                <tbody>
                  {data.top_funds.map((f) => (
                    <tr
                      key={f.scheme_code}
                      className="border-b border-bloomberg-border hover:bg-bloomberg-highlight transition-colors cursor-pointer"
                      onClick={() => window.location.href = `/funds/${f.scheme_code}`}
                    >
                      <td className="py-2 px-2 text-bloomberg-text truncate max-w-[250px]">{f.scheme_name}</td>
                      <td className="py-2 px-2 text-right font-mono">{f.nav?.toFixed(2) ?? "—"}</td>
                      <td className={`py-2 px-2 text-right font-mono ${(f.return_1y ?? 0) >= 0 ? "text-bloomberg-green" : "text-bloomberg-red"}`}>
                        {f.return_1y != null ? `${f.return_1y.toFixed(2)}%` : "—"}
                      </td>
                      <td className={`py-2 px-2 text-right font-mono ${(f.cagr_3y ?? 0) >= 0 ? "text-bloomberg-green" : "text-bloomberg-red"}`}>
                        {f.cagr_3y != null ? `${f.cagr_3y.toFixed(2)}%` : "—"}
                      </td>
                      <td className={`py-2 px-2 text-right font-mono ${(f.cagr_5y ?? 0) >= 0 ? "text-bloomberg-green" : "text-bloomberg-red"}`}>
                        {f.cagr_5y != null ? `${f.cagr_5y.toFixed(2)}%` : "—"}
                      </td>
                      <td className="py-2 px-2 text-right font-mono">{f.expense_ratio != null ? `${f.expense_ratio.toFixed(2)}%` : "—"}</td>
                      <td className="py-2 px-2 text-right font-mono">{f.aum_cr != null ? `₹${f.aum_cr.toFixed(0)}` : "—"}</td>
                      <td className="py-2 px-2 text-right font-mono text-bloomberg-dim">{f.risk_level || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="text-[10px] text-bloomberg-dim border-t border-bloomberg-border pt-3">
            ⚠ Category averages are for reference only. Past performance does not guarantee future returns.
          </div>
        </>
      )}
    </div>
  );
}
