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
- [2026-06-20] 装 Python 包必须用 `python -m pip install`（项目跑在 C:\Program Files\Python310），裸 `pip` 默认指向 Python314 会装错解释器，且会顺带升级 3.14 的 numpy/scipy。验证安装也要用项目的 python。
- [2026-06-20] **Spec 的"现状描述"可能严重过时,落地前必须核实真实文件**。Phase4 spec 声称 signals/strategies/ 全是 0 字节空文件需补齐,实际已有 54 个实现完整的策略——若照搬会覆盖大量已有代码。教训:对 spec 里"现状/缺口"类断言,先用 wc -c / grep / Explore 核实,再决定做什么。用户已确认"spec 只是参考,按实际情况发挥"。
- [2026-06-21] **Direction 是 `class Direction(str, Enum)` — `str(Direction.BUY)` 返回 "Direction.BUY" 不是 "BUY"**。比较要么直接 `s.direction == "BUY"`(继承 str 可行), 要么用 `s.direction.value`。signals/base.py。
- [2026-06-21] **akshare 新闻/实时接口在本环境会长时间挂起(2026 时钟+慢端点), 必须加超时**。news/fetchers/cls.py 用 ThreadPoolExecutor + future.result(timeout=12) 包每个数据源, 且 `ex.shutdown(wait=False)`(默认 wait=True 会等挂起调用, 抵消超时)。财联社 stock_info_global_cls 超时, 但东财 stock_info_global_em 能返回真实新闻。CLS 官网 nodeapi/updateTelegraphList 直连签名已失效(404)。
- [2026-06-21] **macro_data 真有数据**: DuckDB 里 CPI/PMI/M2/GDP/PPI/LPR1Y 各 221 月点(2008 起)。但 akshare 存的是原始指数/绝对值: CPI=101.2 表示同比+1.2%, GDP/M2 是绝对额(非百分比), PMI/LPR 才是直读值。展示时要注意语义(spec mock 里的干净百分比是理想化的)。查询走 `get_store().query` JOIN products ON product_id, 必须在 API 进程内(DuckDB 单进程独占锁)。
- [2026-06-21] **Windows 控制台 GBK 编码无法打印 emoji(🟢等)**, 测试脚本 print 含 emoji 会 UnicodeEncodeError。用 `PYTHONIOENCODING=utf-8 python -X utf8` 运行, 或测试里避免直接 print emoji。
- [2026-06-21] **pytest 全量约 2.5 分钟(1116 passed/5 skipped)**, 用 run_in_background + 长超时, 不要短轮询。
- [2026-06-21] **策略未自动加载的陷阱**: signals/registry.get_strategy 只在 `import signals.strategies` 触发 @register 后才有数据。独立调用方(tournament_runner/promotion_gate/retrain_orchestrator)和单测必须自己 `import signals.strategies`, 否则 get_strategy 返回 None(活服务器里因 StrategyEngine.load_all 已加载才偶然可用)。
- [2026-06-21] **BaseStrategy.params 是类级可变 dict, 多实例共享**。参数优化/回测实例化策略后必须 `inst.params = copy.deepcopy(type(inst).params)` 隔离, 否则不同参数组互相污染。
- [2026-06-21] **scoring.calculate_composite_score 把负夏普截断为 0 贡献** → 高胜率策略可盖过正夏普策略, 会"奖励实际亏钱的策略"。晋级决策不能只看 composite score, 必须叠加 walk-forward 样本外验证(promotion_gate)。
- [2026-06-21] **WalkForwardValidator.validate 不接受"跑回测的 callable", 而是 `objective(params, data_slice)->float` 评分函数**; 它内部用 optimizer_class(只传 param_space/objective/random_state) 自己建优化器跑 IS/OOS。回测要包装成"给参数+数据切片返回夏普"的评分函数。
- [2026-06-21] **OptimizationScheduler 无定时能力**(纯内存同步任务队列), 周期触发要外部循环驱动。HMMDetector.predict 返回 List[str] 需取 last 适配单标签; pct_change 产 inf 要 replace+dropna 再喂 HMM(见 buglog)。

## Decision Log


- [2026-06-21] **外部项目能力移植**: 用户提供 3 个 GitHub 项目 (chan.py-main/abu-master/ai_quant_trade)。决策: (1) **chan.py (MIT)** vendored 整个核心算法簇到 vendor/chanpy/, 写 DataFrame→CKLine_Unit 适配器 (vendor/chanpy/DataAPI/chan_df_api.py 经 data_src="custom:..." 加载) + analysis/chan_pro.py 包装, 产专业买卖点 (一/二/三买卖+盘整背驰), 接成 signals/strategies/chan_strategies.py 的 chan_bsp 策略 (第55个)。注意: chan.py 用 `from typing import Self` (3.11+), 3.10 需 try/except 回退 TypeVar; CKLine_Unit 严格校验 OHLC, 喂数据用 autofix=True; 买卖点取 `chan[0].bs_point_lst.getSortedBspList()` (get_bsp 已弃用)。(2) **abu (GPL v3)**: 用户选"只重写不拷代码"。UMP 裁判机制按思想全新实现于 core/ump/ (GMM 主裁标坏簇 + 相似度边裁投票, 交易级否决闸门, 叠加任意策略)。(3) **empyrical (Apache)**: 装上游而非从 abu 拷, numpy 2.0 需 shim (np.NINF 等已移除), 包装在 backtest/risk_metrics_ext.py。(4) **ai_quant_trade (Apache)**: 仅摘东财股吧舆情采集器到 news/fetchers/eastmoney_guba.py, 其余 DL/RL 比本系统弱。
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
- [2026-06-21] **新闻宏观仪表盘 (SPEC_MACRO_NEWS) 落地**。新增模块: news/(fetchers/cls.py 多源容错快讯采集, sentiment.py 改为中文词典法, calendar.py 规则化事件日历, pipeline.py 采集→标签→情绪→data/news_cache.json), macro/(aggregator.py 查 DuckDB macro_data 算最新值+趋势, regime_adapter.py 规则引擎联动/市态/展望), signals/alert_aggregator.py (查 DuckDB kline→StrategyEngine.compute_all→ResonanceEngineV2→AlertSignal, 存 data/alert_signals.json), simulation/simulated_trading.py (持仓/历史/关注 JSON 持久化), data_center/realtime_quote.py (akshare→warehouse 最新收盘兜底)。API: api/routes/{macro_news,alert,simulated_trading}_routes.py。前端: pages/{MacroNews,SignalDetail}.tsx + Trading.tsx 改 4 Tab, services/macroNewsApi.ts。main.py lifespan 加 daemon 后台线程(新闻30min/信号15min)。关键约束/经验见 Do-Not-Repeat 与 Decision Log 同日条目。
- [2026-06-21] **ML 自我迭代闭环四阶段落地 (锦标赛→反馈→重训→晋级)**。核心洞察: 所有积木(锦标赛评分/反馈闭环/回测引擎/walk-forward/调度器/模型监控/市态检测/策略目录)早已存在且各自可用, 缺的只是"编排层"。**两个锦标赛系统**: core/tournament/tournament_system.py(np.random 假数据)是**死代码未注册**; tournament/tournament_manager.py(TournamentManager, 真评分)才是 /standings 背后的活路由——之前误判过, 务必看活的那个。阶段1: tournament/tournament_runner.py 对目录策略取真实 kline 跑 VectorizedBacktest→喂 feedback_loop(回填目录)+TournamentManager.record_result(新增方法, 接受聚合绩效, JSON 持久化 data/tournament_state.json)。阶段2: core/adaptive/promotion_gate.py 用 WalkForwardValidator 样本外验证 + detect_overfitting 决定晋级(纠偏 composite score 把负夏普截断为0的问题), HMMDetector 按市态分组冠军。阶段3: core/adaptive/retrain_orchestrator.py 触发式三层重训(参数层 OptimizationScheduler 贝叶斯再优化真 kline / 因子层 FactorDecayDetector / 模型层 ModelMonitor→AutoMLPipeline), 缺输入则跳过该层。阶段4: core/adaptive/champion_challenger.py 生命周期 challenger→champion→retired, 毕业需 ≥3 次评估+通过率≥67%+平均OOS夏普≥0.3+人工批准(安全闸门, data/champion_challenger.json)。API 端点: /tournament/{run-backtest,promote,lifecycle,graduate,retire-champion}, /intelligence/retrain/cycle。前端 Tournament.tsx 加"跑真实回测/晋升验证"按钮 + 生命周期面板 + 毕业弹窗。新增 42 个单测(全量 1158 passed)。
- [2026-06-19] **用户协作偏好**：架构扩充而非重复堆叠 — 提需求时若已实现,告知即可不重做。边测边改 (本地 :3000/:8000 常驻)。文档式需求 (futures_knowledge.md) 是讨论稿,可整合/出更优方案。
