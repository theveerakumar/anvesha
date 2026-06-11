"use client";

import { useEffect, useRef } from "react";
import { type FundRow } from "@/lib/api";

export default function ContextMenu({
  fund,
  x,
  y,
  isSelected,
  compareSelection,
  onCompare,
  onRemoveFromCompare,
  onCompareNow,
  onSwp,
  comparing,
  onClose,
}: {
  fund: FundRow;
  x: number;
  y: number;
  isSelected: boolean;
  compareSelection: FundRow[];
  onCompare: (fund: FundRow) => void;
  onRemoveFromCompare: (fund: FundRow) => void;
  onCompareNow: () => void;
  onSwp: (fund: FundRow) => void;
  comparing: boolean;
  onClose: () => void;
}) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        onClose();
      }
    };
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("mousedown", handleClick);
    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("mousedown", handleClick);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [onClose]);

  const others = compareSelection.filter(s => s.scheme_code !== fund.scheme_code);
  const MAX_VISIBLE = 3;
  const extraCount = others.length > MAX_VISIBLE ? others.length - MAX_VISIBLE : 0;
  const visible = extraCount > 0 ? others.slice(0, MAX_VISIBLE) : others;

  const menuW = 220;
  const menuH = 80 + Math.min(others.length, MAX_VISIBLE + 1) * 28 + 10;
  const menuX = Math.min(x, window.innerWidth - menuW);
  const menuY = Math.min(y, window.innerHeight - menuH);

  return (
    <div
      ref={ref}
      className="fixed z-50 bg-bloomberg-surface border border-bloomberg-border rounded-lg shadow-xl py-1"
      style={{ left: menuX, top: menuY, width: menuW }}
    >
      {/* Fund name header */}
      <div className="px-3 py-2 text-xs font-medium text-bloomberg-text border-b border-bloomberg-border truncate">
        {fund.scheme_name.length > 40 ? fund.scheme_name.slice(0, 40) + "…" : fund.scheme_name}
      </div>

      {/* Action: Add/Remove from Compare */}
      <button
        className="w-full text-left px-3 py-2 text-xs text-bloomberg-text hover:bg-bloomberg-highlight transition-colors flex items-center gap-2.5 font-medium"
        onClick={() => { onCompare(fund); onClose(); }}
      >
        <span
          className={`w-5 h-5 rounded flex items-center justify-center text-[11px] font-bold ${
            isSelected
              ? "bg-bloomberg-green/20 text-bloomberg-green"
              : "bg-bloomberg-cyan/15 text-bloomberg-cyan"
          }`}
        >
          {isSelected ? "✓" : "+"}
        </span>
        {isSelected ? "Remove from Compare" : "Add to Compare"}
      </button>

      {/* Action: View Details */}
      <button
        className="w-full text-left px-3 py-2 text-xs text-bloomberg-text/70 hover:bg-bloomberg-highlight hover:text-bloomberg-text transition-colors flex items-center gap-2.5"
        onClick={() => { window.location.href = `/funds/${fund.scheme_code}`; }}
      >
        <span className="w-5 h-5 rounded flex items-center justify-center text-[11px] text-bloomberg-dim">→</span>
        View Details
      </button>

      {/* Action: SWP Calculator */}
      <button
        className="w-full text-left px-3 py-2 text-xs text-bloomberg-yellow/80 hover:bg-bloomberg-highlight hover:text-bloomberg-yellow transition-colors flex items-center gap-2.5"
        onClick={() => { onSwp(fund); onClose(); }}
      >
        <span className="w-5 h-5 rounded flex items-center justify-center text-[11px] text-bloomberg-yellow">↻</span>
        Add to SWP Calculator
      </button>

      {/* Selected for compare section */}
      {compareSelection.length > 0 && (
        <div className="border-t border-bloomberg-border/40 mt-1">
          <div className="px-3 pt-2 pb-1 text-[10px] font-semibold text-bloomberg-dim tracking-wider uppercase flex items-center gap-1.5">
            <span>Compare List</span>
            <span className="text-[9px] font-mono text-bloomberg-dim/70">({compareSelection.length}/5)</span>
          </div>
          <div className="max-h-[160px] overflow-y-auto pb-1">
            {visible.map(s => (
              <div
                key={s.scheme_code}
                className="flex items-center gap-2 px-3 py-1.5 text-[11px] text-bloomberg-text hover:bg-bloomberg-highlight transition-colors"
              >
                <span
                  className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                    s.scheme_code === fund.scheme_code ? "bg-bloomberg-green shadow-sm shadow-bloomberg-green/50" : "bg-bloomberg-cyan"
                  }`}
                />
                <span className="truncate flex-1">{s.scheme_name}</span>
                <button
                  onClick={(e) => { e.stopPropagation(); onRemoveFromCompare(s); }}
                  className="text-bloomberg-dim/60 hover:text-bloomberg-red text-xs transition-colors shrink-0 leading-none px-0.5"
                  title={`Remove ${s.scheme_name}`}
                >
                  ✕
                </button>
              </div>
            ))}
            {extraCount > 0 && (
              <div className="px-3 py-1 text-[9px] text-bloomberg-dim/60 italic">
                +{extraCount} more...
              </div>
            )}
            {compareSelection.length >= 2 && (
              <div className="px-3 pt-1.5 pb-2">
                <button
                  onClick={onCompareNow}
                  disabled={comparing}
                  className="w-full text-[11px] bg-bloomberg-cyan text-black font-semibold py-1.5 rounded hover:opacity-90 disabled:opacity-30 transition-opacity"
                >
                  {comparing ? "Comparing..." : `Compare ${compareSelection.length} Funds →`}
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
