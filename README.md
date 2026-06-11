# Anvesha — Mutual Fund Intelligence Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Anvesha (Sanskrit: अन्वेष, "inquiry" / "research") is a self-hosted mutual fund research platform with a Bloomberg-terminal aesthetic. It ingests the full AMFI mutual fund master (>37K schemes), computes rolling returns, SMART ratings, composite scores, and risk metrics, and exposes them through a FastAPI backend and a Next.js dashboard.

**Intended audience:** retail investors, research analysts, and anyone who wants data-driven mutual fund analysis without relying on black-box ratings.

**Project status:** active development. See [CHANGELOG](CHANGELOG.md) for release history and [Roadmap](#roadmap) for planned features.

---

## Architecture

```
docker-compose up    # starts all services
```

| Service  | Tech                                                  | Port |
| -------- | ----------------------------------------------------- | ---- |
| Postgres | PostgreSQL 16                                         | 5433 |
| Redis    | Redis 7 (caching)                                     | 6379 |
| Backend  | FastAPI / Python 3.12 / SQLAlchemy async / Uvicorn    | 8000 |
| Frontend | Next.js 14 / React 18 / Tailwind CSS / ECharts / Radix | 3000 |

---

## Packages

### Docker Images

Two container images are built from this repository:

| Image                    | Base            | Description                |
| ------------------------ | --------------- | -------------------------- |
| `anvesha-backend`        | `python:3.12-slim` | FastAPI + Uvicorn server |
| `anvesha-frontend`       | `node:20-alpine`   | Next.js standalone server |

Images are built locally via `docker compose build`. On tagged releases, the CI workflow ([`.github/workflows/docker-build.yml`](.github/workflows/docker-build.yml)) automatically builds and pushes both images to `ghcr.io/theveerakumar/anvesha-{backend,frontend}`.

### Python (Backend)

The backend is an async Python application managed via `backend/requirements.txt`.

| Package            | Purpose                            |
| ------------------ | ---------------------------------- |
| `fastapi`          | API framework                      |
| `sqlalchemy[asyncio]` | ORM with async support          |
| `asyncpg`          | PostgreSQL async driver            |
| `alembic`          | Database migrations                |
| `redis[hiredis]`   | Caching layer                      |
| `httpx`            | HTTP client for MFAPI.in           |
| `pandas` / `numpy` | Data manipulation for analytics    |
| `scikit-learn`     | Factor backtesting and scoring     |

Full list: [`backend/requirements.txt`](backend/requirements.txt)

### npm (Frontend)

The frontend is a Next.js application defined in `frontend/package.json` (`anvesha-frontend@0.1.0`).

| Package                   | Purpose                      |
| ------------------------- | ---------------------------- |
| `next`                    | React framework (SSR/SSG)    |
| `react` / `react-dom`     | UI library                   |
| `echarts` / `echarts-for-react` | Interactive NAV charts |
| `tailwindcss`             | Utility-first CSS            |
| `@radix-ui/*`             | Accessible UI primitives     |
| `@tanstack/react-query`   | Server state management      |
| `lucide-react`            | Icon library                 |

Full list: [`frontend/package.json`](frontend/package.json)

---

## Data Pipeline

1. **`seed_funds.py`** — syncs the full fund master from `api.mfapi.in` (37,631 schemes)
2. **`enrich.py`** — fetches NAV history for each fund, computes 1y/3y/5y/7y/10y CAGR returns, risk metrics (std dev, beta, alpha, Sharpe, Sortino, Treynor, information ratio, max drawdown)
3. **`compute_rolling_and_scores.py`** — computes rolling 1y/3y/5y averages (min, max, mean) and positive-return percentages, then generates composite SMART scores
4. **`compute_future_indicator.py`** — runs factor backtesting to produce forward-looking return indicators and confidence levels
5. **`compute_risk_level.py`** — assigns risk-level labels (Very Low through Very High)

---

## Features

### Dashboard
- Tabbed fund browser (All / Equity / Hybrid / Index / Debt / Gold & Silver / Global / Solution / Others)
- Sub-category filter pills for Equity (Large Cap, Mid Cap, Small Cap, Flexi Cap, Multi Cap, ELSS, etc.)
- Top Picks per category (highest composite score per sub-category)
- Recommendation engine: **Top SWP Picks** (capital preservation) and **Top SIP Picks** (wealth creation)
- Data freshness indicator with last-update timestamp
- Sortable fund table (Score, Future, 1Y/3Y/5Y Rolling returns, AUM, Expense, NAV, Age, Confidence)

### Fund Analysis
- **Fund Detail** — NAV chart (ECharts with interactive tooltips), returns table, risk metrics, SMART score breakdown
- **SMART Rating** — multi-factor star rating (Performance, Consistency, Risk, Cost, Portfolio Quality)
- **Fund Comparison** — side-by-side metric comparison for up to 5 funds (click context menu, select, compare)
- **Portfolio Overlap** — overlap analysis between any two funds
- **Fund Holdings** — stock-level holdings, sector allocation, market-cap breakdown

### Calculators
- **SIP Calculator** — project SIP growth with stress tests (bull/bear/sideways), XIRR computation
- **SWP Calculator** — Systematic Withdrawal Plan: longevity projection, max withdrawal (PMT), stress testing, integrated with fund context (pre-fills expected return from 3Y CAGR)

### Screening & Discovery
- **Fund Screener** — filter by category group, sub-category, returns, expense ratio, AUM, risk level
- **Categories** — browse by SEBI scheme category with avg returns and top funds
- **Fund Managers** — aggregated stats by fund manager (total funds, avg returns, AUM, categories managed)

---

## Scoring Methodology

### Composite Score (0–100)
Multi-factor peer-relative scoring within each category group:
- **Performance** — trailing and rolling return percentiles
- **Risk** — downside deviation, max drawdown percentile
- **Consistency** — rolling return positive-period percentage
- **Cost** — inverse expense ratio percentile
- **Scale** — AUM percentile

### Recommendation Scoring

**SWP (capital preservation):**
- `rolling_return_positive_pct` × 30% — consistency
- `score_consistency` × 25% — reliability
- `rolling_return_3y_avg` × 1.5 (15%) — sustainable return
- `100 + rolling_return_1y_min` × 15% — worst-case protection
- `score_cost` × 15% — low expense ratio

**SIP (wealth creation):**
- `score_performance` × 30% — raw performance
- `rolling_return_5y_avg` × 1.5 (30%) — long-term growth
- `future_return_indicator` × 20% — predicted potential
- `rolling_return_positive_pct` × 15% — consistency
- `score_consistency` × 15% — reliability

---

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/dashboard` | Tabbed dashboard with fund table, sub-categories, top picks |
| `GET /api/v1/dashboard/data-status` | Last data update timestamp |
| `GET /api/v1/funds` | List/search funds with filters |
| `GET /api/v1/funds/{code}` | Single fund detail |
| `GET /api/v1/funds/{code}/detail` | Full fund detail (fund + returns + risk + rating + recommendation + NAV history) |
| `GET /api/v1/funds/{code}/returns` | CAGR returns (1m through 10y) |
| `GET /api/v1/funds/{code}/risk` | Risk metrics (std dev, beta, alpha, Sharpe, Sortino, Treynor, info ratio, max DD) |
| `GET /api/v1/funds/{code}/rating` | SMART star rating |
| `GET /api/v1/funds/{code}/recommendation` | Buy/Hold/Sell with reasoning |
| `GET /api/v1/funds/{code}/nav-history` | Daily NAV time series |
| `GET /api/v1/funds/{code}/holdings` | Portfolio holdings |
| `POST /api/v1/funds/compare` | Compare up to 5 funds |
| `GET /api/v1/funds/overlap` | Overlap analysis for two funds |
| `GET /api/v1/funds/top-performers` | Top funds by 1Y/3Y/5Y return and AUM |
| `GET /api/v1/categories` | List SEBI scheme categories |
| `GET /api/v1/categories/{name}` | Category detail with top funds |
| `GET /api/v1/screener/funds` | Advance fund screener |
| `GET /api/v1/managers` | Fund manager analytics |
| `GET /api/v1/recommendations/swp` | Top SWP fund picks |
| `GET /api/v1/recommendations/sip` | Top SIP fund picks |
| `POST /api/v1/sip/calculate` | SIP projection |
| `POST /api/v1/sip/stress-test` | SIP stress test |
| `POST /api/v1/sip/xirr` | XIRR calculation |
| `POST /api/v1/swp/calculate` | SWP projection |
| `POST /api/v1/swp/longevity` | SWP depletion timeline |
| `POST /api/v1/swp/max-withdrawal` | Max sustainable withdrawal (PMT) |
| `POST /api/v1/swp/stress-test` | SWP stress test |

---

## Releases

Releases are versioned using [Semantic Versioning](https://semver.org/) (`v0.1.0`, `v0.2.0`, etc.) and tagged in git.

### Current release

- **v0.1.0** — Full dashboard, recommendation engine, SWP/SIP calculators, fund analysis suite. See [CHANGELOG](CHANGELOG.md) for details.

### Creating a new release

```bash
# Tag and push
git tag v0.2.0
git push origin v0.2.0

# This triggers the CI workflow (docker-build.yml) to:
# 1. Build backend and frontend Docker images
# 2. Push them to ghcr.io/theveerakumar/anvesha-{backend,frontend}
# 3. Tag as :v0.2.0 and :latest
```

### Docker images

Pre-built images are published to GitHub Container Registry:

```bash
docker pull ghcr.io/theveerakumar/anvesha-backend:v0.1.0
docker pull ghcr.io/theveerakumar/anvesha-frontend:v0.1.0
```

---

## Quick Start

```bash
# Clone and start
git clone https://github.com/theveerakumar/anvesha
cd anvesha
docker compose up -d

# Seed the database
docker compose exec backend python3 scripts/seed_funds.py

# Enrich with NAV history, returns, risk metrics
docker compose exec backend python3 scripts/enrich.py

# Compute rolling returns and composite scores
docker compose exec backend python3 scripts/compute_rolling_and_scores.py

# Compute future indicator and risk levels
docker compose exec backend python3 scripts/compute_future_indicator.py
docker compose exec backend python3 scripts/compute_risk_level.py

# Open browser
open http://localhost:3000
```

---

## Roadmap

- [ ] Live market snapshot (integrate MintByte or NSE/BSE API)
- [ ] Portfolio tracker with XIRR tracking
- [ ] Fund manager data enrichment (currently all NULL)
- [ ] Export reports (PDF/CSV)
- [ ] Dark/light theme toggle
- [ ] Automated data refresh via cron
- [ ] Mobile-responsive refinements
- [ ] API documentation (OpenAPI/Swagger already available at `/docs`)

---

## Data Sources

- **`api.mfapi.in`** — public MF API for scheme master and NAV history
- **AMFI India** — official NAV declarations
- Computed analytics (rolling returns, risk metrics, scores, ratings) are generated locally

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -am 'Add my feature'`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a Pull Request

### Development setup

```bash
docker compose up -d
# Backend hot-reloads at :8000
# Frontend hot-reloads at :3000
```

---

## License

[MIT](LICENSE) © 2026 Veerakumar

---

## Disclaimer

**For research purposes only. Not SEBI registered.**
Past performance does not guarantee future returns. Composite scores are peer-relative within each category group. Data may be delayed. Consult a SEBI-registered investment advisor before making investment decisions.
