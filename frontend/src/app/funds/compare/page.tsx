"use client";

import { useState } from "react";
import Link from "next/link";
import { compareFunds, searchFunds, Fund, CompareRow } from "@/lib/api";

export default function ComparePage() {
  const [codes, setCodes] = useState<(number | null)[]>([null, null]);
  const [searchResults, setSearchResults] = useState<Fund[][]>([[], []]);
  const [searchQueries, setSearchQueries] = useState<string[]>(["", ""]);
  const [result, setResult] = useState<{ schemes: number[]; funds: Fund[]; comparison: CompareRow[] } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const addFund = () => {
    if (codes.length < 5) setCodes([...codes, null]);
  };

  const removeFund = (i: number) => {
    if (codes.length <= 2) return;
    const newCodes = codes.filter((_, idx) => idx !== i);
    setCodes(newCodes);
    setSearchResults(searchResults.filter((_, idx) => idx !== i));
    setSearchQueries(searchQueries.filter((_, idx) => idx !== i));
  };

  const handleSearch = async (i: number, q: string) => {
    const newQueries = [...searchQueries];
    newQueries[i] = q;
    setSearchQueries(newQueries);

    if (q.length >= 2) {
      try {
        const data = await searchFunds(q, 1, 5);
        const newResults = [...searchResults];
        newResults[i] = data.results;
        setSearchResults(newResults);
      } catch { /* ignore */ }
    } else {
      const newResults = [...searchResults];
      newResults[i] = [];
      setSearchResults(newResults);
    }
  };

  const selectFund = (i: number, fund: Fund) => {
    const newCodes = [...codes];
    newCodes[i] = fund.scheme_code;
    setCodes(newCodes);
    const newQueries = [...searchQueries];
    newQueries[i] = fund.scheme_name;
    setSearchQueries(newQueries);
    const newResults = [...searchResults];
    newResults[i] = [];
    setSearchResults(newResults);
  };

  const doCompare = async () => {
    const validCodes = codes.filter((c): c is number => c !== null);
    if (validCodes.length < 2) {
      setError("Select at least 2 funds to compare");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await compareFunds(validCodes);
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Comparison failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 md:p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-sm font-semibold text-bloomberg-text">Fund Comparison</h1>
        <Link href="/funds" className="text-[11px] text-bloomberg-cyan hover:underline">← Back to Screener</Link>
      </div>

      <div className="grid gap-3" style={{ gridTemplateColumns: `repeat(${codes.length}, 1fr)` }}>
        {codes.map((code, i) => (
          <div key={i} className="bg-bloomberg-surface border border-bloomberg-border rounded p-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] text-bloomberg-dim uppercase">Fund {i + 1}</span>
              {codes.length > 2 && (
                <button onClick={() => removeFund(i)} className="text-[10px] text-bloomberg-red hover:underline">Remove</button>
              )}
            </div>
            <input
              type="text"
              value={searchQueries[i]}
              onChange={(e) => handleSearch(i, e.target.value)}
              placeholder="Search fund..."
              className="w-full bg-bloomberg-bg border border-bloomberg-border rounded px-2 py-1.5 text-xs text-bloomberg-text placeholder:text-bloomberg-dim/50 outline-none focus:border-bloomberg-cyan"
            />
            {searchResults[i].length > 0 && (
              <div className="mt-1 border border-bloomberg-border rounded max-h-32 overflow-y-auto">
                {searchResults[i].map((f) => (
                  <div
                    key={f.id}
                    className="px-2 py-1.5 text-[10px] text-bloomberg-text hover:bg-bloomberg-highlight cursor-pointer border-b border-bloomberg-border last:border-0 truncate"
                    onClick={() => selectFund(i, f)}
                  >
                    {f.scheme_name}
                  </div>
                ))}
              </div>
            )}
            {code && (
              <div className="mt-2 text-[10px] text-bloomberg-green truncate">✓ {searchQueries[i].slice(0, 40)}</div>
            )}
          </div>
        ))}
      </div>

      <div className="flex items-center gap-3">
        {codes.length < 5 && (
          <button onClick={addFund} className="text-[11px] text-bloomberg-cyan border border-dashed border-bloomberg-border rounded px-3 py-1.5 hover:border-bloomberg-cyan transition-colors">
            + Add Fund
          </button>
        )}
        <button
          onClick={doCompare}
          disabled={loading || codes.filter(Boolean).length < 2}
          className="text-[11px] bg-bloomberg-cyan text-black font-semibold px-4 py-1.5 rounded hover:opacity-90 disabled:opacity-30 transition-opacity"
        >
          {loading ? "Comparing..." : "Compare"}
        </button>
      </div>

      {error && (
        <div className="bg-bloomberg-surface border border-bloomberg-red/30 rounded p-3 text-sm text-bloomberg-red">{error}</div>
      )}

      {result && (
        <div className="bg-bloomberg-surface border border-bloomberg-border rounded overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-bloomberg-dim border-b border-bloomberg-border">
                <th className="text-left py-2.5 px-3 font-medium w-32">Metric</th>
                {result.funds.map((f, i) => (
                  <th key={i} className="text-left py-2.5 px-3 font-medium text-bloomberg-text min-w-[160px]">
                    <Link href={`/funds/${f.scheme_code}`} className="hover:text-bloomberg-cyan">
                      {f.scheme_name.length > 30 ? f.scheme_name.slice(0, 30) + "…" : f.scheme_name}
                    </Link>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {result.comparison.map((row) => (
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

      <div className="text-[10px] text-bloomberg-dim border-t border-bloomberg-border pt-3">
        ⚠ Comparison data is for research purposes only. Highlighted values indicate the best among selected funds for each metric. Past performance does not guarantee future returns.
      </div>
    </div>
  );
}
