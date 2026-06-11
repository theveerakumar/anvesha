"use client";

import { useEffect, useState, useRef } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import * as echarts from "echarts";
import { getFundDetail, getFundHoldings, FundDetailResponse, HoldingsResponse } from "@/lib/api";

const formatPct = (v: number | null | undefined, digits = 2) =>
  v != null ? `${v >= 0 ? "+" : ""}${v.toFixed(digits)}%` : "—";

const formatNum = (v: number | null | undefined, digits = 2) =>
  v != null ? v.toFixed(digits) : "—";

const riskColor = (level: string | null) => {
  switch (level) {
    case "Very Low Risk": return "text-bloomberg-green";
    case "Low Risk": return "text-bloomberg-cyan";
    case "Moderate Risk": return "text-bloomberg-yellow";
    case "High Risk": return "text-orange-400";
    case "Very High Risk": return "text-bloomberg-red";
    default: return "text-bloomberg-dim";
  }
};

const recColor = (rec: string | null) => {
  switch (rec) {
    case "Strong Buy": return "text-bloomberg-green";
    case "Buy": return "text-bloomberg-cyan";
    case "Hold": return "text-bloomberg-yellow";
    case "Watchlist": return "text-orange-400";
    case "Avoid": return "text-bloomberg-red";
    default: return "text-bloomberg-dim";
  }
};

const StarDisplay = ({ rating }: { rating: number }) => (
  <span className="text-bloomberg-yellow text-lg">
    {"★".repeat(rating)}{"☆".repeat(5 - rating)}
  </span>
);

export default function FundDetailPage() {
  const params = useParams();
  const schemeCode = Number(params.code);
  const [data, setData] = useState<FundDetailResponse | null>(null);
  const [holdings, setHoldings] = useState<HoldingsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);
  const sectorChartRef = useRef<HTMLDivElement>(null);
  const mcChartRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    async function load() {
      try {
        const [d, h] = await Promise.all([
          getFundDetail(schemeCode),
          getFundHoldings(schemeCode).catch(() => null),
        ]);
        setData(d);
        setHoldings(h);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load fund details");
      } finally {
        setLoading(false);
      }
    }
    if (schemeCode) load();
  }, [schemeCode]);

  useEffect(() => {
    if (!data?.nav_history || !chartRef.current) return;

    if (chartInstance.current) chartInstance.current.dispose();

    const chart = echarts.init(chartRef.current, undefined, { renderer: "canvas" });
    chartInstance.current = chart;

    const navData = data.nav_history.nav_history.slice(-500);
    const dates = navData.map((p) => p.date);
    const values = navData.map((p) => p.nav);

    chart.setOption({
      backgroundColor: "transparent",
      grid: { left: 60, right: 20, top: 20, bottom: 30 },
      tooltip: {
        trigger: "axis",
        formatter: (params: any) => {
          const p = params[0];
          return `<div style="font-size:12px">${p.axisValue}<br/><span style="color:#00c853">NAV: <b>${p.value}</b></span></div>`;
        },
        backgroundColor: "#13181f",
        borderColor: "#1e2a3a",
        textStyle: { color: "#c5d0e0" },
      },
      xAxis: {
        type: "category", data: dates,
        axisLine: { lineStyle: { color: "#1e2a3a" } },
        axisLabel: { color: "#6a7a8e", fontSize: 10, formatter: (v: string) => v.slice(0, 7) },
        splitLine: { show: false },
      },
      yAxis: {
        type: "value",
        axisLine: { show: false },
        axisLabel: { color: "#6a7a8e", fontSize: 10 },
        splitLine: { lineStyle: { color: "#1e2a3a", type: "dashed" } },
      },
      series: [{
        type: "line", data: values, smooth: true, showSymbol: false,
        lineStyle: { color: "#00bcd4", width: 1.5 },
        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: "rgba(0,188,212,0.3)" },
          { offset: 1, color: "rgba(0,188,212,0.02)" },
        ]) },
      }],
    });

    const handleResize = () => chart.resize();
    window.addEventListener("resize", handleResize);
    return () => {
      window.removeEventListener("resize", handleResize);
      chart.dispose();
    };
  }, [data]);

  useEffect(() => {
    if (!holdings || !sectorChartRef.current) return;

    const sectorChart = echarts.init(sectorChartRef.current);
    const sectorData = Object.entries(holdings.sector_allocation)
      .map(([name, value]) => ({ name, value: Math.round(value * 10) / 10 }))
      .filter(d => d.value > 0);

    sectorChart.setOption({
      backgroundColor: "transparent",
      tooltip: { trigger: "item", formatter: "{b}: {c}%", backgroundColor: "#13181f", borderColor: "#1e2a3a", textStyle: { color: "#c5d0e0" } },
      series: [{
        type: "pie", radius: ["40%", "70%"], center: ["50%", "50%"],
        data: sectorData,
        label: { color: "#6a7a8e", fontSize: 10, formatter: "{b}\n{d}%" },
        labelLine: { lineStyle: { color: "#1e2a3a" } },
        itemStyle: { borderRadius: 4 },
        color: ["#00c853", "#00bcd4", "#ffd600", "#ff6d00", "#ff1744", "#7c4dff", "#00e5ff", "#76ff03", "#c6ff00", "#ff4081"],
      }],
    });

    const handleResize = () => sectorChart.resize();
    window.addEventListener("resize", handleResize);

    return () => { window.removeEventListener("resize", handleResize); sectorChart.dispose(); };
  }, [holdings]);

  useEffect(() => {
    if (!holdings || !mcChartRef.current) return;

    const mcChart = echarts.init(mcChartRef.current);
    const mcData = Object.entries(holdings.market_cap_allocation)
      .map(([name, value]) => ({ name, value: Math.round(value * 10) / 10 }))
      .filter(d => d.value > 0);

    mcChart.setOption({
      backgroundColor: "transparent",
      tooltip: { trigger: "item", formatter: "{b}: {c}%", backgroundColor: "#13181f", borderColor: "#1e2a3a", textStyle: { color: "#c5d0e0" } },
      series: [{
        type: "pie", radius: ["40%", "70%"], center: ["50%", "50%"],
        data: mcData,
        label: { color: "#6a7a8e", fontSize: 10, formatter: "{b}\n{d}%" },
        labelLine: { lineStyle: { color: "#1e2a3a" } },
        color: ["#00bcd4", "#7c4dff", "#00c853"],
        itemStyle: { borderRadius: 4 },
      }],
    });

    const handleResize = () => mcChart.resize();
    window.addEventListener("resize", handleResize);

    return () => { window.removeEventListener("resize", handleResize); mcChart.dispose(); };
  }, [holdings]);

  if (loading) {
    return (
      <div className="p-4 md:p-6 space-y-4">
        <div className="skeleton h-5 w-64" />
        <div className="skeleton h-8 w-full" />
        <div className="skeleton h-64 w-full" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-4 md:p-6">
        <div className="bg-bloomberg-surface border border-bloomberg-red/30 rounded p-4 text-sm text-bloomberg-red">
          {error || "Fund not found"}
        </div>
        <Link href="/funds" className="text-bloomberg-cyan text-sm hover:underline mt-4 inline-block">← Back</Link>
      </div>
    );
  }

  const { fund, returns, risk, rating, recommendation } = data;

  const returnItems = [
    { label: "1 Month", value: returns?.return_1m },
    { label: "3 Month", value: returns?.return_3m },
    { label: "6 Month", value: returns?.return_6m },
    { label: "1 Year", value: returns?.return_1y },
    { label: "3Y CAGR", value: returns?.cagr_3y },
    { label: "5Y CAGR", value: returns?.cagr_5y },
    { label: "7Y CAGR", value: returns?.cagr_7y },
    { label: "10Y CAGR", value: returns?.cagr_10y },
  ];

  const riskItems = [
    { label: "Std Dev", value: risk ? formatNum(risk.std_dev) : "—", desc: "How much returns vary from average. Higher values mean higher volatility." },
    { label: "Beta", value: risk?.beta != null ? formatNum(risk.beta) : "—", desc: "Sensitivity to market moves. >1 amplifies market changes, <1 is less volatile." },
    { label: "Alpha", value: risk?.alpha != null ? formatPct(risk.alpha) : "—", desc: "Risk-adjusted excess return vs benchmark. Positive = outperformed expectations." },
    { label: "Sharpe", value: risk ? formatNum(risk.sharpe_ratio) : "—", desc: "Return per unit of risk. Higher is better. >1 good, >2 excellent." },
    { label: "Sortino", value: risk ? formatNum(risk.sortino_ratio) : "—", desc: "Like Sharpe ratio but only considers downside volatility. Higher = better downside risk-adjusted returns." },
    { label: "Treynor", value: risk?.treynor_ratio != null ? formatNum(risk.treynor_ratio) : "—", desc: "Return per unit of systematic risk (beta). Higher = better relative to market risk taken." },
    { label: "Info Ratio", value: risk?.information_ratio != null ? formatNum(risk.information_ratio) : "—", desc: "Active return relative to tracking error. Higher = more consistent outperformance." },
    { label: "Max DD", value: risk ? formatPct(risk.max_drawdown) : "—", desc: "Largest peak-to-trough decline. Less negative = smaller historical losses." },
  ];

  const scoreItems = [
    { label: "Performance", value: rating?.performance_score, weight: "35%", desc: "Score based on historical returns (1Y, 3Y, 5Y CAGR) relative to category peers." },
    { label: "Consistency", value: rating?.consistency_score, weight: "15%", desc: "How consistently the fund has outperformed its benchmark across time periods." },
    { label: "Risk", value: rating?.risk_score, weight: "25%", desc: "Overall risk assessment combining volatility, drawdown, and downside risk metrics." },
    { label: "Cost", value: rating?.cost_score, weight: "10%", desc: "Expense ratio and load structure score. Lower costs score higher." },
    { label: "Portfolio", value: rating?.portfolio_quality_score, weight: "15%", desc: "Portfolio quality based on holdings diversification and concentration risk." },
  ];

  return (
    <div className="p-4 md:p-6 space-y-6">
      <div className="flex items-center gap-2 text-xs text-bloomberg-dim">
        <Link href="/" className="hover:text-bloomberg-text">Dashboard</Link>
        <span>/</span>
        <Link href="/funds" className="hover:text-bloomberg-text">Screener</Link>
        <span>/</span>
        <span className="text-bloomberg-cyan truncate max-w-[400px]">{fund.scheme_name}</span>
      </div>

      {/* Header with SMART Rating */}
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div className="flex-1 min-w-0">
          <h1 className="text-base font-semibold text-bloomberg-text leading-tight">{fund.scheme_name}</h1>
          <div className="flex items-center gap-3 mt-1 text-[11px] text-bloomberg-dim flex-wrap">
            <span>{fund.scheme_category || "Uncategorized"}</span>
            <span className="w-1 h-1 rounded-full bg-bloomberg-border" />
            <span>Code: {fund.scheme_code}</span>
          </div>
        </div>
        <div className="flex items-center gap-6 shrink-0">
          {rating && (
            <div className="text-center">
              <div className="text-[10px] text-bloomberg-dim uppercase">SMART Rating</div>
              <StarDisplay rating={rating.star_rating} />
              <div className="text-[10px] text-bloomberg-dim">{rating.overall_score}/100</div>
            </div>
          )}
          {recommendation && (
            <div className="text-center">
              <div className="text-[10px] text-bloomberg-dim uppercase">Recommendation</div>
              <div className={`text-sm font-bold ${recColor(recommendation.recommendation)}`}>
                {recommendation.recommendation}
              </div>
              <div className="text-[10px] text-bloomberg-dim">{recommendation.confidence_score}% confidence</div>
            </div>
          )}
          {risk?.risk_level && (
            <div className={`text-center ${riskColor(risk.risk_level)}`}>
              <div className="text-[10px] uppercase tracking-wider text-bloomberg-dim">Risk</div>
              <div className="text-sm font-semibold">{risk.risk_level}</div>
              {risk.risk_score != null && <div className="text-[10px] text-bloomberg-dim">{risk.risk_score}/100</div>}
            </div>
          )}
        </div>
      </div>

      {/* Recommendation Reasoning */}
      {recommendation && (
        <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-4">
          <div className="flex items-start gap-3">
            <div className={`text-lg font-bold shrink-0 ${recColor(recommendation.recommendation)}`}>
              {recommendation.recommendation === "Strong Buy" ? "🟢" :
               recommendation.recommendation === "Buy" ? "🔵" :
               recommendation.recommendation === "Hold" ? "🟡" :
               recommendation.recommendation === "Watchlist" ? "🟠" : "🔴"}
            </div>
            <div>
              <div className="text-xs text-bloomberg-text leading-relaxed">{recommendation.reasoning}</div>
              {recommendation.strengths && (
                <div className="mt-2 text-[11px] text-bloomberg-green">
                  <span className="font-semibold">Strengths:</span> {recommendation.strengths}
                </div>
              )}
              {recommendation.weaknesses && (
                <div className="text-[11px] text-bloomberg-red">
                  <span className="font-semibold">Weaknesses:</span> {recommendation.weaknesses}
                </div>
              )}
              {recommendation.risks && (
                <div className="text-[11px] text-orange-400">
                  <span className="font-semibold">Risks:</span> {recommendation.risks}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* SMART Score Breakdown */}
      {rating && (
        <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-4">
          <h2 className="text-sm font-semibold text-bloomberg-text mb-3">SMART Score Breakdown</h2>
          <div className="grid grid-cols-5 gap-3">
            {scoreItems.map((s) => (
              <div key={s.label} className="text-center group relative">
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2.5 py-1.5 rounded bg-gray-900 border border-gray-700 text-[10px] text-gray-200 leading-tight opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 shadow-lg max-w-[220px] whitespace-normal">
                  {s.desc}
                </div>
                <div className="text-[10px] text-bloomberg-dim uppercase">{s.label}</div>
                <div className="text-lg font-mono font-semibold text-bloomberg-text">
                  {s.value != null ? `${s.value.toFixed(0)}` : "—"}
                </div>
                <div className="text-[9px] text-bloomberg-dim">wt {s.weight}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Returns */}
      <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-4">
        <h2 className="text-sm font-semibold text-bloomberg-text mb-3">Returns</h2>
        <div className="grid grid-cols-4 md:grid-cols-8 gap-3">
          {returnItems.map((r) => (
            <div key={r.label} className="text-center">
              <div className="text-[10px] text-bloomberg-dim uppercase">{r.label}</div>
              <div className={`text-sm font-mono font-semibold mt-1 ${
                r.value != null ? (r.value >= 0 ? "text-bloomberg-green" : "text-bloomberg-red") : "text-bloomberg-dim"
              }`}>
                {formatPct(r.value)}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* NAV Chart */}
      {data.nav_history && (
        <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-4">
          <h2 className="text-sm font-semibold text-bloomberg-text mb-3">NAV History</h2>
          <div ref={chartRef} className="h-72 w-full" />
        </div>
      )}

      {/* Risk Metrics */}
      <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-4">
        <h2 className="text-sm font-semibold text-bloomberg-text mb-3">Risk Metrics</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {riskItems.map((r) => (
            <div key={r.label} className="text-center p-2 group relative">
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2.5 py-1.5 rounded bg-gray-900 border border-gray-700 text-[10px] text-gray-200 leading-tight opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 shadow-lg max-w-[220px] whitespace-normal">
                {r.desc}
              </div>
              <div className="text-[10px] text-bloomberg-dim uppercase">{r.label}</div>
              <div className="text-sm font-mono font-semibold mt-1 text-bloomberg-text">{r.value}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Holdings & Sector Allocation */}
      {holdings && (
        <>
          <div className="grid md:grid-cols-2 gap-4">
            <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-4">
              <h2 className="text-sm font-semibold text-bloomberg-text mb-3">Sector Allocation</h2>
              <div ref={sectorChartRef} className="h-96 w-full" />
            </div>
            <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-4">
              <h2 className="text-sm font-semibold text-bloomberg-text mb-3">Market Cap Allocation</h2>
              <div ref={mcChartRef} className="h-96 w-full" />
            </div>
          </div>

          <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-4">
            <h2 className="text-sm font-semibold text-bloomberg-text mb-3">
              Top Holdings <span className="text-[10px] text-bloomberg-dim font-normal">({holdings.total_stocks} stocks, {holdings.total_weight}% weight)</span>
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-bloomberg-dim border-b border-bloomberg-border">
                    <th className="text-left py-2 px-2 font-medium">Stock</th>
                    <th className="text-left py-2 px-2 font-medium">Sector</th>
                    <th className="text-right py-2 px-2 font-medium">Weight (%)</th>
                    <th className="text-right py-2 px-2 font-medium">Market Cap</th>
                  </tr>
                </thead>
                <tbody>
                  {holdings.holdings.map((h, i) => (
                    <tr key={i} className="border-b border-bloomberg-border hover:bg-bloomberg-highlight transition-colors">
                      <td className="py-2 px-2 text-bloomberg-text">{h.stock_name}</td>
                      <td className="py-2 px-2 text-bloomberg-dim">{h.sector || "—"}</td>
                      <td className="py-2 px-2 text-right font-mono text-bloomberg-cyan">{h.weight.toFixed(2)}%</td>
                      <td className="py-2 px-2 text-right">
                        <span className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-medium ${
                          h.market_cap === "Large Cap" ? "bg-blue-900/40 text-blue-400" :
                          h.market_cap === "Mid Cap" ? "bg-yellow-900/40 text-yellow-400" :
                          "bg-green-900/40 text-green-400"
                        }`}>{h.market_cap || "—"}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      <div className="text-[10px] text-bloomberg-dim border-t border-bloomberg-border pt-3 space-y-1">
        <p>⚠ Past performance is not indicative of future returns. SMART ratings and recommendations are AI-generated based on historical data and are for informational purposes only. They do not constitute personalized investment advice.</p>
        <p>⚡ Recommendation generated at confidence of {recommendation?.confidence_score ?? "—"}%. Consult a SEBI-registered investment advisor before making investment decisions.</p>
      </div>
    </div>
  );
}
