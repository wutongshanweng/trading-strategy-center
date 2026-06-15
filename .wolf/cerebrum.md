# Cerebrum

> OpenWolf's learning memory. Updated automatically as the AI learns from interactions.
> Do not edit manually unless correcting an error.
> Last updated: 2026-06-15

## User Preferences

- User prefers to continue development and upgrades incrementally
- User values token efficiency and performance optimization
- User wants functional features over placeholders ("under development" warnings)
- User language: Chinese for documentation and UI, English for code

## Key Learnings

- **Project:** trading-strategy-center - Enterprise Quantitative Trading Platform
- **Tech Stack:** 
  - Backend: Python 3.10+, FastAPI, PostgreSQL
  - Frontend: React 18 + TypeScript, Ant Design 5, Vite
  - Data: pandas, numpy, scipy for quant analysis
- **Architecture:** Full-stack with backend on :8000, frontend on :3000
- **Git:** Main branch is "main", remote is GitHub (wutongshanweng/trading-strategy-center)
- **Project Structure:**
  - Backend APIs in `api/routes/`
  - Frontend pages in `frontend/src/pages/`
  - Core quant logic in `core/alpha/`, `research/factor_lab/`
  - Factor analysis uses `FactorAnalyzer` from `research.factor_lab.factor_analyzer`
- **Development workflow:**
  - Backend changes trigger auto-reload (uvicorn with --reload)
  - Frontend uses Vite hot module replacement
  - Always test APIs with curl before committing
  - Commit messages follow conventional commits format

## Do-Not-Repeat

- [2026-06-15] Never commit node_modules to git - always add to .gitignore. Already fixed once, caused 19,284 tracked files bloat
- [2026-06-15] When adding new routes, must import and register in main.py (e.g., factor_router). Server needs restart to pick up new routes
- [2026-06-15] Windows paths in bash: use forward slashes or escape backslashes properly

## Decision Log

- [2026-06-15] **OpenWolf Integration**: Integrated OpenWolf v1.0.4 to reduce token consumption by ~80%. Creates .wolf/ directory with anatomy.md (file index), cerebrum.md (learning memory), and 6 hooks for automatic tracking
- [2026-06-15] **Factor Research Module**: Implemented three complete modules (IC Analysis, Stratified Backtesting, Factor Combination) with backend APIs and SVG-based frontend visualizations. Used mock data for demonstration until real data pipeline is connected
- [2026-06-15] **Chart Strategy**: Used custom SVG charts instead of heavyweight chart libraries to keep bundle size small and maintain full control over rendering
