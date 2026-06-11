import type { Metadata } from "next";
import DataStatus from "@/components/DataStatus";
import "./globals.css";

export const metadata: Metadata = {
  title: "Anvesha — Mutual Fund Intelligence",
  description: "Institutional-grade mutual fund research platform for Indian markets",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased">
        <div className="flex flex-col h-screen bg-bloomberg-bg">
          {/* Top header bar */}
          <header className="flex items-center justify-between px-4 h-10 bg-bloomberg-surface border-b border-bloomberg-border shrink-0">
            <div className="flex items-center gap-4">
              <span className="text-bloomberg-green font-black text-lg tracking-widest font-mono">
                ANVESHA
              </span>
              <nav className="hidden md:flex items-center gap-3 text-xs text-bloomberg-dim">
                <a href="/" className="hover:text-bloomberg-text transition-colors">Dashboard</a>
                <a href="/funds" className="hover:text-bloomberg-text transition-colors">Fund Screener</a>
                <a href="/categories" className="hover:text-bloomberg-text transition-colors">Categories</a>
                <a href="/sip" className="hover:text-bloomberg-text transition-colors">SIP Calculator</a>
                <a href="/swp" className="hover:text-bloomberg-text transition-colors">SWP Calculator</a>
              </nav>
            </div>
            <div className="flex items-center gap-3 text-[11px] text-white text-right leading-tight">
              <span className="hidden md:inline">For research purposes only · Not SEBI registered RIA</span>
            </div>
          </header>

          {/* Main content */}
          <main className="flex-1 overflow-auto">
            {children}
          </main>

          {/* Bottom status bar */}
          <footer className="flex items-center justify-between px-4 h-7 bg-bloomberg-surface border-t border-bloomberg-border shrink-0 text-[10px] text-bloomberg-dim font-mono">
            <span>Rev 84fc43b</span>
            <span>Data: MFAPI.in | Not investment advice. For research purposes only.</span>
            <span className="flex items-center gap-1"><DataStatus /></span>
          </footer>
        </div>
      </body>
    </html>
  );
}
