"use client";

import { useState } from "react";
import * as echarts from "echarts";
import { useEffect, useRef } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export default function SIPPage() {
  const [monthly, setMonthly] = useState(5000);
  const [years, setYears] = useState(10);
  const [returnRate, setReturnRate] = useState(12);
  const [result, setResult] = useState<any>(null);
  const [stressResult, setStressResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const chartRef = useRef<HTMLDivElement>(null);

  const calculate = async () => {
    setLoading(true);
    try {
      const [sipRes, stressRes] = await Promise.all([
        fetch(`${API_URL}/sip/calculate`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ monthly_amount: monthly, duration_years: years, expected_return: returnRate }),
        }),
        fetch(`${API_URL}/sip/stress-test`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ monthly_amount: monthly, duration_years: years }),
        }),
      ]);
      const sipData = await sipRes.json();
      const stressData = await stressRes.json();
      setResult(sipData.result);
      setStressResult(stressData.result);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!stressResult || !chartRef.current) return;

    const chart = echarts.init(chartRef.current);
    const scenarios = stressResult.scenarios;

    chart.setOption({
      backgroundColor: "transparent",
      tooltip: { trigger: "axis", backgroundColor: "#13181f", borderColor: "#1e2a3a", textStyle: { color: "#c5d0e0" } },
      legend: { data: ["Bull Market", "Bear Market", "Sideways Market"], textStyle: { color: "#6a7a8e", fontSize: 10 } },
      grid: { left: 60, right: 20, top: 40, bottom: 30 },
      xAxis: {
        type: "category",
        data: ["Total Invested", "Current Value", "Total Returns"],
        axisLine: { lineStyle: { color: "#1e2a3a" } },
        axisLabel: { color: "#6a7a8e", fontSize: 10 },
      },
      yAxis: {
        type: "value",
        axisLabel: { color: "#6a7a8e", fontSize: 10, formatter: "₹{value}" },
        splitLine: { lineStyle: { color: "#1e2a3a", type: "dashed" } },
      },
      series: [
        {
          name: "Bull Market", type: "bar",
          data: [scenarios.bull.total_invested, scenarios.bull.current_value, scenarios.bull.total_returns],
          itemStyle: { color: "#00c853" },
        },
        {
          name: "Bear Market", type: "bar",
          data: [scenarios.bear.total_invested, scenarios.bear.current_value, scenarios.bear.total_returns],
          itemStyle: { color: "#ff1744" },
        },
        {
          name: "Sideways Market", type: "bar",
          data: [scenarios.sideways.total_invested, scenarios.sideways.current_value, scenarios.sideways.total_returns],
          itemStyle: { color: "#ffd600" },
        },
      ],
    });

    const handleResize = () => chart.resize();
    window.addEventListener("resize", handleResize);
    return () => { window.removeEventListener("resize", handleResize); chart.dispose(); };
  }, [stressResult]);

  const formatInr = (v: number) =>
    new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(v);

  return (
    <div className="p-4 md:p-6 space-y-6">
      <h1 className="text-sm font-semibold text-bloomberg-text">SIP Calculator</h1>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Input */}
        <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-4 space-y-4">
          <div>
            <label className="text-[10px] text-bloomberg-dim uppercase block mb-1">Monthly SIP (₹)</label>
            <input type="number" value={monthly} onChange={(e) => setMonthly(Number(e.target.value))}
              className="w-full bg-bloomberg-bg border border-bloomberg-border rounded px-3 py-2 text-sm text-bloomberg-text outline-none focus:border-bloomberg-cyan font-mono" />
          </div>
          <div>
            <label className="text-[10px] text-bloomberg-dim uppercase block mb-1">Duration (Years)</label>
            <input type="number" value={years} onChange={(e) => setYears(Number(e.target.value))}
              className="w-full bg-bloomberg-bg border border-bloomberg-border rounded px-3 py-2 text-sm text-bloomberg-text outline-none focus:border-bloomberg-cyan font-mono" />
          </div>
          <div>
            <label className="text-[10px] text-bloomberg-dim uppercase block mb-1">Expected Return (%)</label>
            <input type="number" value={returnRate} onChange={(e) => setReturnRate(Number(e.target.value))} step="0.5"
              className="w-full bg-bloomberg-bg border border-bloomberg-border rounded px-3 py-2 text-sm text-bloomberg-text outline-none focus:border-bloomberg-cyan font-mono" />
          </div>
          <button onClick={calculate} disabled={loading}
            className="w-full bg-bloomberg-cyan text-black font-semibold text-sm py-2 rounded hover:opacity-90 disabled:opacity-30 transition-opacity">
            {loading ? "Calculating..." : "Calculate SIP"}
          </button>
        </div>

        {/* Results */}
        {result && (
          <div className="space-y-3">
            <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-4">
              <h2 className="text-[10px] text-bloomberg-dim uppercase mb-3">Projected Returns at {returnRate}%</h2>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <div className="text-[10px] text-bloomberg-dim">Total Invested</div>
                  <div className="text-lg font-mono font-semibold text-bloomberg-text">{formatInr(result.total_invested)}</div>
                </div>
                <div>
                  <div className="text-[10px] text-bloomberg-dim">Current Value</div>
                  <div className="text-lg font-mono font-semibold text-bloomberg-green">{formatInr(result.current_value)}</div>
                </div>
                <div>
                  <div className="text-[10px] text-bloomberg-dim">Total Returns</div>
                  <div className="text-lg font-mono font-semibold text-bloomberg-cyan">{formatInr(result.total_returns)}</div>
                </div>
                <div>
                  <div className="text-[10px] text-bloomberg-dim">CAGR</div>
                  <div className="text-lg font-mono font-semibold text-bloomberg-yellow">{result.cagr}%</div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Stress Test */}
      {stressResult && (
        <>
          <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-4">
            <h2 className="text-sm font-semibold text-bloomberg-text mb-3">SIP Stress Test — Scenario Comparison</h2>
            <div ref={chartRef} className="h-64 w-full" />
          </div>

          <div className="grid md:grid-cols-3 gap-3">
            {Object.entries(stressResult.scenarios).map(([key, s]: [string, any]) => (
              <div key={key} className="bg-bloomberg-surface border border-bloomberg-border rounded p-3">
                <div className={`text-sm font-semibold ${
                  key === "bull" ? "text-bloomberg-green" : key === "bear" ? "text-bloomberg-red" : "text-bloomberg-yellow"
                }`}>{s.label}</div>
                <div className="text-[10px] text-bloomberg-dim mt-1">{s.description}</div>
                <div className="mt-3 space-y-1 text-[11px]">
                  <div className="flex justify-between"><span className="text-bloomberg-dim">Invested</span><span className="font-mono">{formatInr(s.total_invested)}</span></div>
                  <div className="flex justify-between"><span className="text-bloomberg-dim">Value</span><span className="font-mono">{formatInr(s.current_value)}</span></div>
                  <div className="flex justify-between"><span className="text-bloomberg-dim">Returns</span><span className={`font-mono ${s.total_returns >= 0 ? "text-bloomberg-green" : "text-bloomberg-red"}`}>{formatInr(s.total_returns)}</span></div>
                  <div className="flex justify-between"><span className="text-bloomberg-dim">CAGR</span><span className={`font-mono ${s.cagr >= 0 ? "text-bloomberg-green" : "text-bloomberg-red"}`}>{s.cagr}%</span></div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      <div className="text-[10px] text-bloomberg-dim border-t border-bloomberg-border pt-3">
        ⚠ SIP projections are for illustrative purposes only. Actual returns depend on market conditions.
        Past performance does not guarantee future returns. Consult a SEBI-registered investment advisor.
      </div>
    </div>
  );
}
