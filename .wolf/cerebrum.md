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
- [2026-06-18] **Unified DuckDB Data Center**: Per 交易系统统一数据库设计.md, building a unified market-data warehouse in DuckDB (data_center/data_center.db). Design rules: store REAL contracts (RB2509), NOT synthetic continuous (RB0); two-layer products→symbols; single unified `kline` table keyed (datetime,symbol_id,timeframe). DuckDB chosen for columnar/vectorized cross-product correlation + multi-timeframe aggregation. Operational tables (signals/trades/positions/backtest) stay on existing SQLite/SQLAlchemy — DuckDB is market-data only.
- [2026-06-18] **DuckDB single-writer**: DuckDBStore serializes writes via threading.Lock; reads use conn.cursor(). upsert_df does DELETE-then-INSERT (no cross-version native UPSERT). The long bulk download and live API share the write lock.
- [2026-06-18] **Data sources chosen by user**: akshare (have) + port TDX/ChinaOptions from download_date/market_data_fetcher + add BaoStock (no key), Tushare Pro (token), TqSdk (account). TqSdk free=recent only → use Tushare/akshare for deep history, TqSdk for tick/realtime.
- [2026-06-18] **Network resilience required**: user's network maintenance causes API ECONNRESET interruptions — fetchers and download orchestrator must have retry/backoff and resumable checkpoints.
- [2026-06-18] **DuckDB is single-process exclusive-lock**: only ONE OS process can open data_center.db (even read-only is blocked while another holds the write lock). Implication: the bulk download script and the FastAPI server CANNOT both touch the DB simultaneously. Production pattern → run downloads as in-process background tasks inside the API server (one process owns the DB), OR take the warehouse API offline during the one-time bulk historical load. Discovered when a 2nd python proc hit `IO Error: File is already open in ... (PID)`.
- [2026-06-18 仓库接入] **期货下载改走 DuckDB 仓库采集器（不再是 Parquet）**。网页选 RB → /warehouse/contracts/discover 枚举真实子合约+主力判定（按持仓量）→ /warehouse/collect/product 后台任务采集入库。关键点：(1) main.py reload 改为 DEV_RELOAD 环境变量，默认单进程（双进程会和 DuckDB 独占锁冲突）。(2) 采集后台任务走 collect_jobs.py 单实例 + full_downloader.py（asyncio.to_thread 包同步采集），进度写 download_checkpoint.json。(3) 主力标注用独立表 main_contracts（不能 UPDATE symbols.is_main，DuckDB 禁止 UPDATE 被外键引用的行，见 buglog bug-014）。(4) 测试环境只下近1月：start_date 参数透传，collect_contract 用 _trim 按日期过滤（sina 日线接口不支持日期参数，只能下载后过滤）。预览走 /warehouse/preview（按合约代码）。SyncScheduler 之前的 bug：execute_task 不落盘 + result.status==\"completed\" 是枚举比字符串永远 False，已改为调 collector 写仓库。 `DataStore` already supports `market` dirs futures/stock/options. Threaded `market_type` through `DataSourceManager.get_kline`→`get_best_source`; akshare `get_kline` detects A-share codes (has '.' or 6-digit) → `get_stock_daily`; `ChinaOptionsFetcher.get_kline` routes by code prefix (IO/HO→index option, digits→ETF option). Frontend asset-class selector in download tab; stock/option use `/download/range?asset_type=`. Added `/preview`, `/data-files`, `/options/codes` endpoints (note: `/download/list` collides with `/download/{task_id}` dynamic route — used `/data-files` instead).
- [2026-06-19] **两套存储分工（重要）**：单股/单合约下载走 `/api/v1/data-center/download/range` → **Parquet 文件** (`data/market/{asset}/{code}/main/{interval}.parquet`)，前端"数据预览"卡片读这里。全市场/批量全量走 `/api/v1/warehouse/collect/full` → **DuckDB 仓库**，前端"仓库数据预览"读这里。两者并存，不要混用。
- [2026-06-19] **远程数据滞后系统时钟**：环境系统日期是 2026，但 akshare/DCE/东财远程数据只到现实当前日期。商品期权历史(option_hist_dce)、东财 Greeks 快照(option_risk_analysis_em)在 2026 日期下拉不到实盘数据。结论：涉及"当日/近期"实盘的功能无法端到端联调，必须用合成数据单测验证逻辑，实盘拉取在数据可用时自然生效。akshare 交易日历(tool_trade_date_hist_sina)本身覆盖到 2026-12-31。
- [2026-06-19] **商品期权 Greeks akshare 不直接提供** → 必须 Black76 自算。复用已有 options/pricing/black76.py + options/greeks/analytical_greeks.black76_greeks + options/volatility/iv_solver.implied_vol_newton(futures=True)。编排在 data_center/options_analytics.compute_option_greeks (纯函数) + OptionsCollector.collect_commodity_greeks。合约代码 m2608-C-2500 内嵌标的/类型/行权价，标的期货收盘取自仓库 kline。ETF/股指期权则用东财 option_risk_analysis_em 直接给 Greeks (collect_greeks_snapshot 已改为真正落库 options_daily)。
- [2026-06-19] **评分引擎已存在,勿重建**：用户知识库文档规划的 scoring_engine.py = 已有 resonance/engine.py + core/resonance/voter.py (confidence 加权投票,已按观山G/楚风C/听海T 分组)。文档规划的季节性/持仓情绪/跨市场/IV/技术指标/宏观采集模块在本仓库均已存在 (analysis/seasonality.py, analysis/oifactors.py, data_center/cross_market.py, options/volatility/, signals/indicators.py, macro_collector.py)。真缺口只有：合约知识库结构化字段(已扩 ContractDetail) + 股票知识库(已建 stock_knowledge.py 行业↔期货映射)。决策层 观山/楚风/听海/牧野 是站外 agent,利用本系统信号数据按自己思路跑。
- [2026-06-19] **用户协作偏好**：架构扩充而非重复堆叠 — 提需求时若已实现,告知即可不重做。边测边改 (本地 :3000/:8000 常驻)。文档式需求 (futures_knowledge.md) 是讨论稿,可整合/出更优方案。
