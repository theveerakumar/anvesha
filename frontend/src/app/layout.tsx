import type { Metadata } from "next";
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
              <span className="text-bloomberg-green font-bold text-sm tracking-wider font-mono">
                ANVESHA
              </span>
              <nav className="hidden md:flex items-center gap-3 text-xs text-bloomberg-dim">
                <a href="/" className="hover:text-bloomberg-text transition-colors">Dashboard</a>
                <a href="/funds" className="hover:text-bloomberg-text transition-colors">Fund Screener</a>
                <a href="/funds/compare" className="hover:text-bloomberg-text transition-colors">Compare</a>
                <a href="/categories" className="hover:text-bloomberg-text transition-colors">Categories</a>
                <a href="/sip" className="hover:text-bloomberg-text transition-colors">SIP Calculator</a>
              </nav>
            </div>
            <div className="flex items-center gap-3 text-xs text-bloomberg-dim">
              <span className="text-bloomberg-cyan font-mono">SEBI RIA</span>
              <span className="w-2 h-2 rounded-full bg-bloomberg-green" title="Data feed active" />
            </div>
          </header>

          {/* Main content */}
          <main className="flex-1 overflow-auto">
            {children}
          </main>

          {/* Bottom status bar */}
          <footer className="flex items-center justify-between px-4 h-7 bg-bloomberg-surface border-t border-bloomberg-border shrink-0 text-[10px] text-bloomberg-dim font-mono">
            <span>ANVESHA v0.1.0</span>
            <span>Data: MFAPI.in | Not investment advice. For research purposes only.</span>
            <span id="market-status">Live</span>
          </footer>
        </div>
      </body>
    </html>
  );
}
