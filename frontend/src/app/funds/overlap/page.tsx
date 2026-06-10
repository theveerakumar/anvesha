"use client";

import { useState } from "react";
import Link from "next/link";
import { searchFunds, getFundOverlap, Fund, OverlapResponse } from "@/lib/api";

export default function OverlapPage() {
  const [fundA, setFundA] = useState<Fund | null>(null);
  const [fundB, setFundB] = useState<Fund | null>(null);
  const [queryA, setQueryA] = useState("");
  const [queryB, setQueryB] = useState("");
  const [resultsA, setResultsA] = useState<Fund[]>([]);
  const [resultsB, setResultsB] = useState<Fund[]>([]);
  const [overlap, setOverlap] = useState<OverlapResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (side: "A" | "B", q: string) => {
    if (side === "A") setQueryA(q);
    else setQueryB(q);
    if (q.length >= 2) {
      try {
        const data = await searchFunds(q, 1, 5);
        if (side === "A") setResultsA(data.results);
        else setResultsB(data.results);
      } catch { /* ignore */ }
    } else {
      if (side === "A") setResultsA([]);
      else setResultsB([]);
    }
  };

  const selectFund = (side: "A" | "B", fund: Fund) => {
    if (side === "A") {
      setFundA(fund);
      setQueryA(fund.scheme_name);
      setResultsA([]);
    } else {
      setFundB(fund);
      setQueryB(fund.scheme_name);
      setResultsB([]);
    }
  };

  const doOverlap = async () => {
    if (!fundA || !fundB) {
      setError("Select both funds");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await getFundOverlap(fundA.scheme_code, fundB.scheme_code);
      setOverlap(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Overlap check failed");
    } finally {
      setLoading(false);
    }
  };

  const diverColor = (score: number) => {
    if (score >= 80) return "text-bloomberg-green";
    if (score >= 60) return "text-bloomberg-cyan";
    if (score >= 40) return "text-bloomberg-yellow";
    return "text-bloomberg-red";
  };

  return (
    <div className="p-4 md:p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-sm font-semibold text-bloomberg-text">Portfolio Overlap Detector</h1>
        <Link href="/funds" className="text-[11px] text-bloomberg-cyan hover:underline">← Back</Link>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        {/* Fund A */}
        <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-3">
          <div className="text-[10px] text-bloomberg-dim uppercase mb-2">Fund A</div>
          <input
            type="text"
            value={queryA}
            onChange={(e) => handleSearch("A", e.target.value)}
            placeholder="Search first fund..."
            className="w-full bg-bloomberg-bg border border-bloomberg-border rounded px-2 py-1.5 text-xs text-bloomberg-text placeholder:text-bloomberg-dim/50 outline-none focus:border-bloomberg-cyan"
          />
          {resultsA.length > 0 && (
            <div className="mt-1 border border-bloomberg-border rounded max-h-32 overflow-y-auto">
              {resultsA.map((f) => (
                <div
                  key={f.id}
                  className="px-2 py-1.5 text-[10px] text-bloomberg-text hover:bg-bloomberg-highlight cursor-pointer border-b border-bloomberg-border last:border-0 truncate"
                  onClick={() => selectFund("A", f)}
                >
                  {f.scheme_name}
                </div>
              ))}
            </div>
          )}
          {fundA && <div className="mt-2 text-[10px] text-bloomberg-green">✓ {fundA.scheme_name.slice(0, 50)}</div>}
        </div>

        {/* Fund B */}
        <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-3">
          <div className="text-[10px] text-bloomberg-dim uppercase mb-2">Fund B</div>
          <input
            type="text"
            value={queryB}
            onChange={(e) => handleSearch("B", e.target.value)}
            placeholder="Search second fund..."
            className="w-full bg-bloomberg-bg border border-bloomberg-border rounded px-2 py-1.5 text-xs text-bloomberg-text placeholder:text-bloomberg-dim/50 outline-none focus:border-bloomberg-cyan"
          />
          {resultsB.length > 0 && (
            <div className="mt-1 border border-bloomberg-border rounded max-h-32 overflow-y-auto">
              {resultsB.map((f) => (
                <div
                  key={f.id}
                  className="px-2 py-1.5 text-[10px] text-bloomberg-text hover:bg-bloomberg-highlight cursor-pointer border-b border-bloomberg-border last:border-0 truncate"
                  onClick={() => selectFund("B", f)}
                >
                  {f.scheme_name}
                </div>
              ))}
            </div>
          )}
          {fundB && <div className="mt-2 text-[10px] text-bloomberg-green">✓ {fundB.scheme_name.slice(0, 50)}</div>}
        </div>
      </div>

      <button
        onClick={doOverlap}
        disabled={loading || !fundA || !fundB}
        className="text-[11px] bg-bloomberg-cyan text-black font-semibold px-4 py-1.5 rounded hover:opacity-90 disabled:opacity-30 transition-opacity"
      >
        {loading ? "Checking..." : "Check Overlap"}
      </button>

      {error && (
        <div className="bg-bloomberg-surface border border-bloomberg-red/30 rounded p-3 text-sm text-bloomberg-red">{error}</div>
      )}

      {overlap && (
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-3">
              <div className="text-[10px] text-bloomberg-dim uppercase">Overlap</div>
              <div className="text-lg font-mono font-semibold text-bloomberg-text">{overlap.overlap_percentage}%</div>
            </div>
            <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-3">
              <div className="text-[10px] text-bloomberg-dim uppercase">Common Holdings</div>
              <div className="text-lg font-mono font-semibold text-bloomberg-text">{overlap.common_holdings.length}</div>
            </div>
            <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-3">
              <div className="text-[10px] text-bloomberg-dim uppercase">Diversification</div>
              <div className={`text-lg font-mono font-semibold ${diverColor(overlap.diversification_score)}`}>
                {overlap.diversification_score}/100
              </div>
            </div>
          </div>

          {overlap.common_holdings.length > 0 && (
            <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-4">
              <h2 className="text-sm font-semibold text-bloomberg-text mb-3">Common Holdings</h2>
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-bloomberg-dim border-b border-bloomberg-border">
                    <th className="text-left py-2 px-2 font-medium">Stock</th>
                    <th className="text-left py-2 px-2 font-medium">Sector</th>
                    <th className="text-right py-2 px-2 font-medium">Weight (A)</th>
                    <th className="text-right py-2 px-2 font-medium">Weight (B)</th>
                  </tr>
                </thead>
                <tbody>
                  {overlap.common_holdings.map((h, i) => (
                    <tr key={i} className="border-b border-bloomberg-border">
                      <td className="py-2 px-2 text-bloomberg-text">{h.stock}</td>
                      <td className="py-2 px-2 text-bloomberg-dim">{h.sector || "—"}</td>
                      <td className="py-2 px-2 text-right font-mono">{h.weight_a != null ? `${h.weight_a.toFixed(2)}%` : "—"}</td>
                      <td className="py-2 px-2 text-right font-mono">{h.weight_b != null ? `${h.weight_b.toFixed(2)}%` : "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <div className="text-[10px] text-bloomberg-dim border-t border-bloomberg-border pt-3">
            ⚠ Portfolio overlap analysis is based on latest available holdings data. High overlap may indicate concentration risk.
          </div>
        </div>
      )}
    </div>
  );
}
