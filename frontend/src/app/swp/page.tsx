"use client";

import { Suspense, useState, useEffect, useRef } from "react";
import { useSearchParams } from "next/navigation";
import * as echarts from "echarts";
import { getFund, getFundReturns, type Fund, type ReturnsData } from "@/lib/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

type SWPMode = "fixed_withdrawal" | "max_withdrawal";

function SWPPageInner() {
  const searchParams = useSearchParams();
  const schemeCode = searchParams.get("scheme_code");

  const [mode, setMode] = useState<SWPMode>("fixed_withdrawal");
  const [corpus, setCorpus] = useState(1000000);
  const [monthlyWithdrawal, setMonthlyWithdrawal] = useState(10000);
  const [durationYears, setDurationYears] = useState(10);
  const [expectedReturn, setExpectedReturn] = useState(12);
  const [fund, setFund] = useState<Fund | null>(null);
  const [returnsData, setReturnsData] = useState<ReturnsData | null>(null);
  const [result, setResult] = useState<any>(null);
  const [stressResult, setStressResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [fundLoading, setFundLoading] = useState(false);
  const chartRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!schemeCode) return;
    const code = parseInt(schemeCode);
    if (isNaN(code)) return;

    setFundLoading(true);
    Promise.all([
      getFund(code).catch(() => null),
      getFundReturns(code).catch(() => null),
    ]).then(([f, r]) => {
      if (f) setFund(f);
      if (r) {
        setReturnsData(r);
        const defaultReturn = r.cagr_3y || r.return_1y || 12;
        setExpectedReturn(Math.round(defaultReturn * 10) / 10);
      }
    }).finally(() => setFundLoading(false));
  }, [schemeCode]);

  const calculate = async () => {
    setLoading(true);
    try {
      if (mode === "fixed_withdrawal") {
        const [calcRes, longevityRes, stressRes] = await Promise.all([
          fetch(`${API_URL}/swp/calculate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ corpus, monthly_withdrawal: monthlyWithdrawal, expected_return: expectedReturn, duration_years: durationYears }),
          }),
          fetch(`${API_URL}/swp/longevity`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ corpus, monthly_withdrawal: monthlyWithdrawal, expected_return: expectedReturn }),
          }),
          fetch(`${API_URL}/swp/stress-test`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ corpus, monthly_withdrawal: monthlyWithdrawal, duration_years: durationYears }),
          }),
        ]);
        const calcData = await calcRes.json();
        const longevityData = await longevityRes.json();
        const stressData = await stressRes.json();
        setResult({ ...calcData.result, longevity: longevityData.result });
        setStressResult(stressData.result);
      } else {
        const [maxRes, stressRes] = await Promise.all([
          fetch(`${API_URL}/swp/max-withdrawal`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ corpus, duration_years: durationYears, expected_return: expectedReturn }),
          }),
          fetch(`${API_URL}/swp/stress-test`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ corpus, monthly_withdrawal: 0, duration_years: durationYears }),
          }),
        ]);
        const maxData = await maxRes.json();
        const stressData = await stressRes.json();
        setResult(maxData.result);
        stressData.result.scenarios = Object.fromEntries(
          Object.entries(stressData.result.scenarios).map(([k, s]: [string, any]) => {
            const mw = maxData.result.monthly_withdrawal;
            return [k, { ...s, monthly_withdrawal: mw }];
          })
        );
        // Recalculate stress with actual max withdrawal
        if (maxData.result.monthly_withdrawal > 0) {
          const stressRes2 = await fetch(`${API_URL}/swp/stress-test`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ corpus, monthly_withdrawal: maxData.result.monthly_withdrawal, duration_years: durationYears }),
          });
          const stressData2 = await stressRes2.json();
          setStressResult(stressData2.result);
        } else {
          setStressResult(stressData.result);
        }
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!result || !chartRef.current) return;
    const snapshots = result.yearly_snapshots;
    if (!snapshots || snapshots.length === 0) return;

    const chart = echarts.init(chartRef.current);
    const years = snapshots.map((s: any) => `Year ${s.year}`);
    const balances = snapshots.map((s: any) => s.end_balance);

    chart.setOption({
      backgroundColor: "transparent",
      tooltip: {
        trigger: "axis",
        backgroundColor: "#13181f",
        borderColor: "#1e2a3a",
        textStyle: { color: "#c5d0e0", fontSize: 11 },
        formatter: (params: any) => {
          const p = params[0];
          const s = snapshots[p.dataIndex];
          return `<div class="text-[11px]">
            <div class="text-bloomberg-dim mb-1">Year ${s.year}</div>
            <div class="flex justify-between gap-4"><span>Start Balance</span><span class="font-mono text-right">₹${Number(s.start_balance).toLocaleString("en-IN", { maximumFractionDigits: 0 })}</span></div>
            <div class="flex justify-between gap-4"><span>Withdrawn</span><span class="font-mono text-right">₹${Number(s.annual_withdrawn).toLocaleString("en-IN", { maximumFractionDigits: 0 })}</span></div>
            <div class="flex justify-between gap-4"><span>Returns</span><span class="font-mono text-right ${s.returns_earned >= 0 ? "text-bloomberg-green" : "text-bloomberg-red"}">₹${Number(s.returns_earned).toLocaleString("en-IN", { maximumFractionDigits: 0 })}</span></div>
            <div class="flex justify-between gap-4 pt-1 border-t border-bloomberg-border mt-1"><span>End Balance</span><span class="font-mono text-right font-semibold">₹${Number(s.end_balance).toLocaleString("en-IN", { maximumFractionDigits: 0 })}</span></div>
          </div>`;
        },
      },
      grid: { left: 70, right: 30, top: 30, bottom: 40 },
      xAxis: {
        type: "category",
        data: years,
        axisLine: { lineStyle: { color: "#1e2a3a" } },
        axisLabel: { color: "#6a7a8e", fontSize: 10 },
        axisTick: { alignWithLabel: true },
      },
      yAxis: {
        type: "value",
        axisLabel: {
          color: "#6a7a8e",
          fontSize: 10,
          formatter: (v: number) => v >= 10000000 ? `₹${(v / 10000000).toFixed(1)}Cr` : v >= 100000 ? `₹${(v / 100000).toFixed(1)}L` : `₹${v.toLocaleString("en-IN")}`,
        },
        splitLine: { lineStyle: { color: "#1e2a3a", type: "dashed" } },
      },
      series: [{
        type: "line",
        data: balances,
        smooth: true,
        symbol: "circle",
        symbolSize: 6,
        lineStyle: { color: "#00bcd4", width: 2 },
        itemStyle: { color: "#00bcd4" },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "rgba(0, 188, 212, 0.25)" },
            { offset: 1, color: "rgba(0, 188, 212, 0.02)" },
          ]),
        },
        markLine: result.final_value <= 0 ? {
          data: [{ yAxis: 0, label: { formatter: "Depleted", color: "#ff5252", fontSize: 10 }, lineStyle: { color: "#ff5252", type: "dashed" } }],
        } : undefined,
      }],
    });

    const handleResize = () => chart.resize();
    window.addEventListener("resize", handleResize);
    return () => { window.removeEventListener("resize", handleResize); chart.dispose(); };
  }, [result]);

  useEffect(() => {
    calculate();
  }, []);

  const formatInr = (v: number | null | undefined) =>
    v != null ? `₹${v.toLocaleString("en-IN", { maximumFractionDigits: 0 })}` : "—";

  const formatPct = (v: number | null | undefined) =>
    v != null ? `${v >= 0 ? "+" : ""}${Number(v).toFixed(2)}%` : "—";

  const withdrawalRate = result ? (result.monthly_withdrawal * 12 / corpus * 100) : null;

  return (
    <div className="p-4 md:p-6 space-y-6">
      <h1 className="text-sm font-semibold text-bloomberg-text">SWP Calculator</h1>

      {/* Fund info banner */}
      {schemeCode && fundLoading && (
        <div className="skeleton h-16 w-full" />
      )}
      {schemeCode && fund && (
        <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-3">
          <div className="flex items-center justify-between">
            <div className="min-w-0 flex-1">
              <div className="text-xs font-semibold text-bloomberg-text truncate">{fund.scheme_name}</div>
              <div className="text-[10px] text-bloomberg-dim mt-0.5">
                {fund.scheme_category || "—"} · {fund.amc || fund.fund_family || "—"}
              </div>
            </div>
            <div className="flex items-center gap-4 ml-4 shrink-0">
              {returnsData && (
                <>
                  <div className="text-right">
                    <div className="text-[9px] text-bloomberg-dim">1Y Return</div>
                    <div className={`text-xs font-mono font-semibold ${(returnsData.return_1y ?? 0) >= 0 ? "text-bloomberg-green" : "text-bloomberg-red"}`}>
                      {formatPct(returnsData.return_1y)}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-[9px] text-bloomberg-dim">3Y CAGR</div>
                    <div className={`text-xs font-mono font-semibold ${(returnsData.cagr_3y ?? 0) >= 0 ? "text-bloomberg-green" : "text-bloomberg-red"}`}>
                      {formatPct(returnsData.cagr_3y)}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-[9px] text-bloomberg-dim">5Y CAGR</div>
                    <div className={`text-xs font-mono font-semibold ${(returnsData.cagr_5y ?? 0) >= 0 ? "text-bloomberg-green" : "text-bloomberg-red"}`}>
                      {formatPct(returnsData.cagr_5y)}
                    </div>
                  </div>
                </>
              )}
              <div className="text-[9px] text-bloomberg-dim">
                {fund.nav != null ? `NAV: ₹${fund.nav.toFixed(2)}` : ""}
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="grid md:grid-cols-2 gap-6">
        {/* Input panel */}
        <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-4 space-y-4">
          {/* Mode toggle */}
          <div className="flex bg-bloomberg-bg rounded p-0.5">
            <button
              onClick={() => setMode("fixed_withdrawal")}
              className={`flex-1 text-[10px] py-1.5 rounded font-medium transition-colors ${
                mode === "fixed_withdrawal"
                  ? "bg-bloomberg-cyan/20 text-bloomberg-cyan"
                  : "text-bloomberg-dim hover:text-bloomberg-text"
              }`}
            >
              Fixed Withdrawal
            </button>
            <button
              onClick={() => setMode("max_withdrawal")}
              className={`flex-1 text-[10px] py-1.5 rounded font-medium transition-colors ${
                mode === "max_withdrawal"
                  ? "bg-bloomberg-cyan/20 text-bloomberg-cyan"
                  : "text-bloomberg-dim hover:text-bloomberg-text"
              }`}
            >
              Max Withdrawal
            </button>
          </div>

          <div>
            <label className="text-[10px] text-bloomberg-dim uppercase block mb-1">Corpus / Investment (₹)</label>
            <input type="number" value={corpus} onChange={(e) => setCorpus(Number(e.target.value))}
              className="w-full bg-bloomberg-bg border border-bloomberg-border rounded px-3 py-2 text-sm text-bloomberg-text outline-none focus:border-bloomberg-cyan font-mono" />
          </div>

          {mode === "fixed_withdrawal" ? (
            <div>
              <label className="text-[10px] text-bloomberg-dim uppercase block mb-1">Monthly Withdrawal (₹)</label>
              <input type="number" value={monthlyWithdrawal} onChange={(e) => setMonthlyWithdrawal(Number(e.target.value))}
                className="w-full bg-bloomberg-bg border border-bloomberg-border rounded px-3 py-2 text-sm text-bloomberg-text outline-none focus:border-bloomberg-cyan font-mono" />
            </div>
          ) : (
            <div>
              <label className="text-[10px] text-bloomberg-dim uppercase block mb-1">Duration (Years)</label>
              <input type="number" value={durationYears} onChange={(e) => setDurationYears(Number(e.target.value))}
                className="w-full bg-bloomberg-bg border border-bloomberg-border rounded px-3 py-2 text-sm text-bloomberg-text outline-none focus:border-bloomberg-cyan font-mono" />
            </div>
          )}

          <div>
            <label className="text-[10px] text-bloomberg-dim uppercase block mb-1">
              Expected Return (%)
              {fund && returnsData && (
                <span className="text-bloomberg-green font-normal ml-1">
                  (pre-filled from fund data)
                </span>
              )}
            </label>
            <input type="number" value={expectedReturn} onChange={(e) => setExpectedReturn(Number(e.target.value))} step="0.5"
              className="w-full bg-bloomberg-bg border border-bloomberg-border rounded px-3 py-2 text-sm text-bloomberg-text outline-none focus:border-bloomberg-cyan font-mono" />
          </div>

          <button onClick={calculate} disabled={loading}
            className="w-full bg-bloomberg-cyan text-black font-semibold text-sm py-2 rounded hover:opacity-90 disabled:opacity-30 transition-opacity">
            {loading ? "Calculating..." : "Calculate SWP"}
          </button>
        </div>

        {/* Results panel */}
        {result && (
          <div className="space-y-3">
            <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-4">
              <h2 className="text-[10px] text-bloomberg-dim uppercase mb-3">
                {mode === "fixed_withdrawal" ? `Projection at ${expectedReturn}%` : "Max Withdrawal Projection"}
              </h2>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <div className="text-[10px] text-bloomberg-dim">
                    {mode === "fixed_withdrawal" ? "Monthly Withdrawal" : "Max Monthly Withdrawal"}
                  </div>
                  <div className="text-lg font-mono font-semibold text-bloomberg-text">
                    {formatInr(result.monthly_withdrawal)}
                  </div>
                </div>
                <div>
                  <div className="text-[10px] text-bloomberg-dim">Total Withdrawn</div>
                  <div className="text-lg font-mono font-semibold text-bloomberg-cyan">
                    {formatInr(result.total_withdrawn)}
                  </div>
                </div>
                <div>
                  <div className="text-[10px] text-bloomberg-dim">Final Value</div>
                  <div className={`text-lg font-mono font-semibold ${(result.final_value ?? 0) > 0 ? "text-bloomberg-green" : result.final_value === 0 ? "text-bloomberg-red" : "text-bloomberg-text"}`}>
                    {formatInr(result.final_value)}
                  </div>
                </div>
                <div>
                  <div className="text-[10px] text-bloomberg-dim">Total Returns</div>
                  <div className={`text-lg font-mono font-semibold ${(result.total_returns ?? 0) >= 0 ? "text-bloomberg-green" : "text-bloomberg-red"}`}>
                    {formatInr(result.total_returns)}
                  </div>
                </div>
                {withdrawalRate != null && (
                  <div>
                    <div className="text-[10px] text-bloomberg-dim">Annual Withdrawal Rate</div>
                    <div className="text-lg font-mono font-semibold text-bloomberg-yellow">
                      {withdrawalRate.toFixed(1)}%
                    </div>
                  </div>
                )}
                {result.longevity && (
                  <div>
                    <div className="text-[10px] text-bloomberg-dim">Corpus Lasts</div>
                    <div className="text-lg font-mono font-semibold text-bloomberg-text">
                      {result.longevity.total_years < 100
                        ? `${result.longevity.total_years}Y (${result.longevity.total_months}M)`
                        : "100+ years"}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Line chart */}
      {result && result.yearly_snapshots && result.yearly_snapshots.length > 0 && (
        <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-4">
          <h2 className="text-sm font-semibold text-bloomberg-text mb-3">Portfolio Balance Over Time</h2>
          <div ref={chartRef} className="h-72 w-full" />
        </div>
      )}

      {/* Yearly projection table */}
      {result && result.yearly_snapshots && result.yearly_snapshots.length > 0 && (
        <div className="bg-bloomberg-surface border border-bloomberg-border rounded overflow-x-auto">
          <div className="px-3 py-2 border-b border-bloomberg-border">
            <span className="text-xs font-semibold text-bloomberg-text">Yearly Projection</span>
          </div>
          <table className="w-full text-xs">
            <thead>
              <tr className="text-bloomberg-dim border-b border-bloomberg-border">
                <th className="text-left py-2.5 px-3 font-medium">Year</th>
                <th className="text-right py-2.5 px-3 font-medium">Start Balance</th>
                <th className="text-right py-2.5 px-3 font-medium">Annual Withdrawal</th>
                <th className="text-right py-2.5 px-3 font-medium">Returns Earned</th>
                <th className="text-right py-2.5 px-3 font-medium">End Balance</th>
              </tr>
            </thead>
            <tbody>
              {result.yearly_snapshots.map((s: any) => (
                <tr key={s.year} className="border-b border-bloomberg-border hover:bg-bloomberg-highlight transition-colors">
                  <td className="py-2.5 px-3 text-bloomberg-dim font-medium">{s.year}</td>
                  <td className="py-2.5 px-3 text-right font-mono text-bloomberg-text">{formatInr(s.start_balance)}</td>
                  <td className="py-2.5 px-3 text-right font-mono text-bloomberg-dim">{formatInr(s.annual_withdrawn)}</td>
                  <td className={`py-2.5 px-3 text-right font-mono ${(s.returns_earned ?? 0) >= 0 ? "text-bloomberg-green" : "text-bloomberg-red"}`}>
                    {formatInr(s.returns_earned)}
                  </td>
                  <td className={`py-2.5 px-3 text-right font-mono font-semibold ${s.end_balance > 0 ? "text-bloomberg-text" : s.end_balance === 0 ? "text-bloomberg-red" : "text-bloomberg-text"}`}>
                    {formatInr(s.end_balance)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Stress test */}
      {stressResult && (
        <>
          <h2 className="text-sm font-semibold text-bloomberg-text -mb-4">Stress Test Scenarios</h2>
          <div className="grid md:grid-cols-3 gap-3">
            {Object.entries(stressResult.scenarios).map(([key, s]: [string, any]) => (
              <div key={key} className="bg-bloomberg-surface border border-bloomberg-border rounded p-3">
                <div className={`text-sm font-semibold ${
                  key === "bull" ? "text-bloomberg-green" : key === "bear" ? "text-bloomberg-red" : "text-bloomberg-yellow"
                }`}>{s.label}</div>
                <div className="text-[10px] text-bloomberg-dim mt-1">{s.description}</div>
                <div className="mt-3 space-y-1 text-[11px]">
                  <div className="flex justify-between">
                    <span className="text-bloomberg-dim">Return</span>
                    <span className={`font-mono ${(s.annual_return ?? 0) >= 0 ? "text-bloomberg-green" : "text-bloomberg-red"}`}>
                      {formatPct(s.annual_return)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-bloomberg-dim">Monthly Withdrawal</span>
                    <span className="font-mono">{formatInr(s.monthly_withdrawal)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-bloomberg-dim">Total Withdrawn</span>
                    <span className="font-mono">{formatInr(s.total_withdrawn)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-bloomberg-dim">Final Value</span>
                    <span className={`font-mono ${(s.final_value ?? 0) > 0 ? "text-bloomberg-green" : "text-bloomberg-red"}`}>
                      {formatInr(s.final_value)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-bloomberg-dim">Total Returns</span>
                    <span className={`font-mono ${(s.total_returns ?? 0) >= 0 ? "text-bloomberg-green" : "text-bloomberg-red"}`}>
                      {formatInr(s.total_returns)}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      <div className="text-[10px] text-bloomberg-dim border-t border-bloomberg-border pt-3">
        SWP projections are for illustrative purposes only. Actual returns depend on market conditions.
        Past performance does not guarantee future returns.
      </div>
    </div>
  );
}

export default function SWPPage() {
  return (
    <Suspense fallback={<div className="p-4 md:p-6 space-y-4"><div className="skeleton h-5 w-48" /><div className="skeleton h-64 w-full" /></div>}>
      <SWPPageInner />
    </Suspense>
  );
}
