# Changelog

## v0.1.0 (2026-06-12)

### Phase 7 — Recommendation Engine & SWP Calculator
- Recommendation engine with SQL-based scoring for SWP (capital preservation) and SIP (wealth creation)
- SWP calculator: longevity projection, max withdrawal (PMT), stress testing, fund-integrated pre-fill
- Dashboard: Top SWP/SIP Picks cards, data freshness indicator, recommendation section
- Context menu with Add to SWP Calculator option
- UI polish: Bloomberg terminal refinements, extended top picks, tooltips on fund detail

### Phase 6 — Dashboard & Scoring Pipeline
- Tabbed dashboard with category groups (equity/hybrid/index/debt/gold_silver/global/solution/other)
- Top Picks per sub-category and scheme category
- Rolling returns computation (1y/3y/5y avg, min, max, positive %)
- Composite SMART scoring (Performance, Risk, Consistency, Cost, Scale)
- Future return indicator via factor backtesting
- Enrichment pipeline scripts

### Phase 5 — Holdings & Manager Analysis
- Portfolio holdings generator with sector and market-cap allocation
- Fund manager analysis page with aggregated stats (total funds, avg returns, AUM)
- Top-performing funds endpoint (by 1Y/3Y/5Y return and AUM)

### Phase 4 — SIP Calculator & Screener
- SIP calculator with growth projection and stress tests (bull/bear/sideways)
- XIRR computation
- Advanced fund screener (category, returns, expense ratio, AUM, risk level filters)
- Frontend navigation integration

### Phase 3 — Ratings, Comparison & Overlap
- SMART rating engine (1–5 star rating across 5 factors)
- Recommendation engine with buy/hold/sell signals and reasoning
- Compliance audit logging for recommendations
- Fund comparison (up to 5 funds, side-by-side metrics)
- Portfolio overlap detector

### Phase 2 — Analytics Engine
- CAGR returns computation (1m through 10y)
- Risk metrics: std dev, beta, alpha, Sharpe, Sortino, Treynor, information ratio, max drawdown
- NAV history caching in Redis
- ECharts interactive NAV chart on fund detail page
- Category breakdown page with avg returns

### Phase 1 — Foundation
- FastAPI backend scaffold with SQLAlchemy async + PostgreSQL
- Next.js 14 frontend with Bloomberg-terminal dark theme
- Docker Compose (Postgres, Redis, Backend, Frontend)
- MFAPI.in data provider integration
- Search API for funds

## v0.0.1 (2026-06-10)

- Initial project scaffold and repository setup
