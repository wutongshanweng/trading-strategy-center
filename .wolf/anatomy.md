# anatomy.md

> Auto-maintained by OpenWolf. Last scanned: 2026-06-20T15:11:28.676Z
> Files: 601 tracked | Anatomy hits: 0 | Misses: 0

## ./

- `.dockerignore` — Docker ignore rules (~26 tok)
- `.gitignore` — Git ignore rules (~93 tok)
- `alembic.ini` (~162 tok)
- `api.log` (~177 tok)
- `ARCHITECTURE.md` — 交易策略中心 — 架构设计文档 (~18087 tok)
- `CHANGELOG.md` — 更新日志 (~1272 tok)
- `CLAUDE.md` — OpenWolf (~575 tok)
- `CONTRIBUTING.md` — 交易策略中心 - 贡献指南 (~1419 tok)
- `DELIVERY_REPORT.md` — 🎉 系统交付报告 (~1508 tok)
- `diagnose_frontend.py` (~370 tok)
- `docker-compose.yml` — Docker Compose services (~454 tok)
- `Dockerfile` — Docker container definition (~257 tok)
- `ENHANCEMENT_COMPLETION_REPORT.md` — 🎉 功能扩展完成报告 (~2003 tok)
- `FACTOR_RESEARCH_IMPLEMENTATION.md` — Factor Research Module - Implementation Complete (~1485 tok)
- `FINAL_SUMMARY.md` — 🎉 项目完成总结报告 (~1585 tok)
- `FRONTEND_DATA_SYNC_FIX.md` — 前端数据同步修复方案 (~1860 tok)
- `FRONTEND_FIX_COMPLETE.md` — ✅ 前端修复完成！ (~768 tok)
- `FRONTEND_ISSUES_SUMMARY.md` — Web界面问题总结与修复方案 (~1642 tok)
- `FRONTEND_UPGRADE_REPORT.md` — 前端Web界面升级完成报告 (~1774 tok)
- `GIT_UPLOAD_GUIDE.md` — 🚀 Git上传完成指南 (~1682 tok)
- `GITHUB_PUSH_GUIDE.md` — GitHub推送指南 (~641 tok)
- `IMPLEMENTATION_COMPLETE_PHASE1.md` — 🎉 用户需求全面实施完成报告 (~1770 tok)
- `IMPLEMENTATION_COMPLETE_PHASE2.md` — 🎉 Phase 2 实施完成报告 (~1631 tok)
- `LICENSE` — Project license (~292 tok)
- `main.py` — lifespan (~930 tok)
- `nginx.conf` — Nginx configuration (~605 tok)
- `OPENWOLF_INTEGRATION.md` — OpenWolf Integration Report (~1788 tok)
- `PROJECT_CLEANUP_REPORT.md` — 项目文件整理完成报告 (~1813 tok)
- `PROJECT_FINAL_REPORT.md` — 🎊 项目全面完成报告 (~2240 tok)
- `pyproject.toml` — Python project configuration (~258 tok)
- `QUICK_START_PHASE1.md` — 🚀 立即启动指南 - Phase 1 功能使用 (~1814 tok)
- `QUICK_START.md` — 交易策略中心 - 快速入门指南 (~2397 tok)
- `README.md` — Project documentation (~1365 tok)
- `requirements-dev.txt` — 可选依赖（development环境） (~135 tok)
- `signal_adapter.py` — SignalAdapter: process_symbol, process_batch (~461 tok)
- `SYSTEM_COMPLETION_REPORT.md` — 交易策略中心 - 系统升级完成报告 (~1244 tok)
- `THEME_SWITCH_GUIDE.md` — 🎨 主题切换功能使用指南 (~1001 tok)
- `UPGRADE_STATUS.md` — 系统升级状态报告 (~1325 tok)
- `UPGRADE_SUMMARY.md` — 交易策略中心 - 系统升级完成总结 (~1162 tok)
- `USER_REQUIREMENTS_ANALYSIS.md` — 用户需求分析与实施方案 (~3362 tok)
- `WEB_STARTUP_GUIDE.md` — Web服务启动指南 (~992 tok)

## .claude/

- `settings.json` (~491 tok)
- `settings.local.json` — Declares AKShareFetcher (~1121 tok)

## .claude/rules/

- `openwolf.md` (~313 tok)

## .github/workflows/

- `main.yml` — Trading Strategy Center — CI/CD Pipeline (~1131 tok)

## .pytest_cache/

- `.gitignore` — Git ignore rules (~11 tok)
- `CACHEDIR.TAG` (~51 tok)
- `README.md` — Project documentation (~78 tok)

## .pytest_cache/v/cache/

- `nodeids` (~20678 tok)
- `stepwise` (~1 tok)

## C:/Users/Administrator/.claude/

- `.mcp.json` (~252 tok)
- `CLAUDE.md` — Global Guidelines (~601 tok)
- `settings.json` (~1284 tok)

## C:/Users/Administrator/.claude/projects/d-------trading-strategy-center/memory/

- `feedback-communication-language.md` (~84 tok)
- `feedback-github-token-defer.md` (~114 tok)
- `MEMORY.md` — Memory Index (~44 tok)

## C:/Users/Administrator/.claude/rules/

- `openwolf.md` (~318 tok)

## analysis/

- `__init__.py` (~0 tok)
- `bayesian_inference.py` — BayesianInference: update, get_probability, get_credible_interval (~425 tok)
- `chan_theory.py` — ChanTheory: detect_bi, detect_zhongshu, classify_trend (~927 tok)
- `divergence_detector.py` — DivergenceDetector: detect (~929 tok)
- `factor_eval.py` — FactorEvaluator: compute_ic, turnover, factor_decay (~306 tok)
- `fourier_analyzer.py` — FourierAnalyzer: fit, get_cycles, reconstruct (~514 tok)
- `monte_carlo.py` — MonteCarloStrategyEvaluator: evaluate, confidence_interval (~357 tok)
- `oifactors.py` — OIAnalyzer: analyze, detect_divergence (~287 tok)
- `seasonality.py` — SeasonalityAnalyzer: day_of_week_effect, month_effect, get_seasonal_adjustment (~427 tok)

## api/

- `__init__.py` (~0 tok)

## api/middleware/

- `__init__.py` (~0 tok)
- `error_handler.py` — app_exception_handler, unhandled_exception_handler (~281 tok)

## api/routes/

- `__init__.py` (~0 tok)
- `agent_routes.py` — API: POST, GET (12 endpoints) (~2926 tok)
- `backtest_routes.py` — API: POST, GET (2 endpoints) (~583 tok)
- `data_routes.py` — API: GET (3 endpoints) (~593 tok)
- `db_routes.py` — API: GET, POST (9 endpoints) (~5290 tok)
- `factor_routes.py` — API: 4 endpoints (~6354 tok)
- `feedback_routes.py` — 反馈闭环 API — 处理锦标赛结果 / 查询反馈历史与排名。 (~311 tok)
- `health_routes.py` — API: GET (1 endpoints) (~76 tok)
- `intelligence_routes.py` — API routes for intelligence upgrade: RL, risk monitoring, monitoring. (~2371 tok)
- `llm_routes.py` — API routes for LLM-powered market analysis and strategy generation. (~1591 tok)
- `ml_routes.py` — API: GET, POST (3 endpoints) (~662 tok)
- `mlopts_routes.py` — API: 1 endpoints (~1880 tok)
- `phase3_routes.py` — API: 4 endpoints (~1463 tok)
- `portfolio_routes.py` — API: GET, POST (3 endpoints) (~372 tok)
- `strategy_routes.py` — API: 5 endpoints (~790 tok)
- `tournament_routes.py` — API routes for Strategy Tournament — rankings, scoring, and elimination. (~817 tok)
- `trading_routes.py` — API: GET, POST (4 endpoints) (~528 tok)

## api/websocket/

- `__init__.py` (~0 tok)
- `manager.py` — ConnectionManager: connect, disconnect, broadcast, send_personal + 1 more (~577 tok)
- `realtime_signals.py` — ConnectionManager: connect, disconnect, send_personal_message, broadcast + 10 more (~2092 tok)
- `trading_stream.py` — WebSocket endpoints for real-time trading data streaming. (~1195 tok)

## backtest/

- `__init__.py` (~0 tok)
- `metrics.py` — sharpe_ratio, max_drawdown, calmar_ratio, win_rate + 2 more (~418 tok)
- `threshold_optimizer.py` — ThresholdOptimizer: optimize (~311 tok)
- `vectorized_engine.py` — class: run, compare_strategies (~1237 tok)
- `walkforward.py` — WalkForward: run (~314 tok)

## config/

- `models.yaml` — Trading Strategy Center — 多模型配置 (~895 tok)

## core/

- `__init__.py` (~0 tok)
- `exceptions.py` — Declares AppException (~349 tok)
- `feedback_config.py` — 反馈闭环参数配置。 (~130 tok)
- `feedback_loop.py` — class: to_dict, process_tournament_results, get_strategy_rankings, get_history + 1 more (~1699 tok)

## core/adaptive/

- `__init__.py` (~115 tok)
- `bayesian_optimizer.py` — class: suggest_next, update, optimize, best + 1 more (~1715 tok)
- `parameter_store.py` — from: save, load_latest, load_version, list_versions + 5 more (~1899 tok)
- `regime_aware_optimizer.py` — RegimeAwareOptimizer: suggest_next, update, optimize, get_regime_params + 1 more (~720 tok)
- `scheduler.py` — class: submit_task, run_task, run_all, get_task_status + 2 more (~1151 tok)
- `walk_forward_validator.py` — class: split, validate, check_robustness, detect_overfitting (~1338 tok)

## core/alpha/

- `__init__.py` (~58 tok)
- `factor_advisor.py` — class: summary, to_dict, advise, advise_from_report (~1563 tok)
- `factor_cli.py` — load_market_data, cmd_report, cmd_combine, cmd_mine (~3614 tok)
- `factor_combiner.py` — FactorCombiner: set_factors, equal_weight, ic_weight, regime_weight + 1 more (~1038 tok)
- `factor_evaluator.py` — class: set_forward_returns, calculate_ic, calculate_ir, calculate_turnover + 1 more (~1000 tok)
- `factor_library.py` — class: register, get_factor, list_factors, compute_all + 2 more (~738 tok)

## core/alpha/alpha101/

- `__init__.py` (~1300 tok)
- `alpha001.py` — Real WorldQuant Alpha101 formula — Momentum alpha001: (rank(Ts_ArgMax(...))) (~326 tok)
- `alpha002.py` — Real WorldQuant Alpha101 formula — Alpha002: (-1 * correlation(rank(delta(log(volume), 2)), rank(((close - open) / open)), 6)) (~353 tok)
- `alpha003.py` — Real WorldQuant Alpha101 formula — Alpha003: (-1 * correlation(rank(open), rank(volume), 10)) (~291 tok)
- `alpha004.py` — Real WorldQuant Alpha101 formula — Alpha004: (-1 * Ts_Rank(rank(low), 9)) (~266 tok)
- `alpha005.py` — Real WorldQuant Alpha101 formula — Alpha005: (rank((open - (sum(vwap, 10) / 10))) * (-1 * abs(rank((close - vwap))))) (~352 tok)
- `alpha006.py` — Real WorldQuant Alpha101 formula — Alpha006: (-1 * correlation(open, volume, 10)) (~277 tok)
- `alpha007.py` — Real WorldQuant Alpha101 formula — Alpha007: ((adv20 < volume) ? ((-1 * ts_rank(abs(delta(close, 7)), 60)) * sign(delta(close, 7))) : (-1 * 1)) (~386 tok)
- `alpha008.py` — Real WorldQuant Alpha101 formula — Alpha008: (-1 * rank(((sum(open, 5) * sum(returns, 5)) - delay((sum(open, 5) * sum(returns, 5)), 10)))) (~363 tok)
- `alpha009.py` — Real WorldQuant Alpha101 formula — Alpha009: ((0 < ts_min(delta(close, 1), 5)) ? delta(close, 1) : ((ts_max(delta(close, 1), 5) < 0) ? delta(close,... (~402 tok)
- `alpha010.py` — Real WorldQuant Alpha101 formula — Alpha010: rank(((0 < ts_min(delta(close, 1), 4)) ? delta(close, 1) : ((ts_max(delta(close, 1), 4) < 0) ? delta(c... (~408 tok)
- `alpha011.py` — Real WorldQuant Alpha101 formula — Alpha011: ((rank(Ts_LogMax(rank(((close - open) / open)), 5)) + rank(Ts_LogMin(rank(((close - open) / open)), 5)... (~373 tok)
- `alpha012.py` — Real WorldQuant Alpha101 formula — Alpha012: (rank(open) - rank(high)) * 0.5 + (rank(low) - rank(close)) * 0.5 (~374 tok)
- `alpha013.py` — Real WorldQuant Alpha101 formula — Alpha013: (((rank(delta(high, 1)) + rank(delta(low, 1))) / 2 + rank(delta(close, 1)) + rank(delta(volume, 1))) / 4) (~378 tok)
- `alpha014.py` — Real WorldQuant Alpha101 formula — Alpha014: (-1 * correlation(rank(high), rank(volume), 5)) (~290 tok)
- `alpha015.py` — Real WorldQuant Alpha101 formula — Alpha015: (-1 * correlation(rank(close), rank(volume), 3)) (~291 tok)
- `alpha016.py` — Real WorldQuant Alpha101 formula — Alpha016: (-1 * correlation(rank(high), rank(volume), 3)) (~290 tok)
- `alpha017.py` — Real WorldQuant Alpha101 formula — Alpha017: (-1 * correlation(rank(low), rank(volume), 5)) (~289 tok)
- `alpha018.py` — Real WorldQuant Alpha101 formula — Alpha018: (-1 * correlation(rank(open), rank(volume), 1)) (~290 tok)
- `alpha019.py` — Real WorldQuant Alpha101 formula — Alpha019: ((-1 * sign(((close - delay(close, 7)) + (close - delay(close, 14))))) * (1 + rank(1 - rank(1 + sum(re... (~410 tok)
- `alpha020.py` — Real WorldQuant Alpha101 formula — Alpha020: (((-1 * correlation(rank(open), rank(volume), 8)) + correlation(rank(high), rank(volume), 8)) / 2) (~362 tok)
- `alpha021.py` — Real WorldQuant Alpha101 formula — Alpha021: (regression_slope(rank(close), 60) + correlation(rank(close), rank(volume), 10)) (~368 tok)
- `alpha022.py` — Real WorldQuant Alpha101 formula — Alpha022: (-1 * rank(delta(rank(close), 6)) * rank(delta(rank(volume), 6))) (~320 tok)
- `alpha023.py` — Real WorldQuant Alpha101 formula — Alpha023: ((sum(high, 20) / 20) < high) ? (-1 * delta(high, 2)) : 0 (~326 tok)
- `alpha024.py` — Real WorldQuant Alpha101 formula — Alpha024: (((sum(close, 100) / 100) > close) ? (sign(-1 * delta(close, 7))) : (-1 * rank(1 + sum(returns, 250)))) (~405 tok)
- `alpha025.py` — Real WorldQuant Alpha101 formula — Alpha025: rank(-1 * ((close - delay(close, 5)) / delay(close, 5) * volume - (close - delay(close, 5)) / delay(cl... (~355 tok)
- `alpha026.py` — Real WorldQuant Alpha101 formula — Alpha026: (-1 * correlation(rank(close), rank(volume), 5)) (~291 tok)
- `alpha027.py` — Real WorldQuant Alpha101 formula — Alpha027: ((0.5 < rank(sum(correlation(rank(volume), rank(close), 6), 2))) ? (-1 * rank(delta(close, 5))) : 1) (~389 tok)
- `alpha028.py` — Real WorldQuant Alpha101 formula — Alpha028: scale(((close - ts_min(close, 100)) / (ts_max(close, 100) - ts_min(close, 100) + 1e-8))) (~353 tok)
- `alpha029.py` — Real WorldQuant Alpha101 formula — Alpha029: (rank(1 - rank(close)) + rank(rank(correlation(rank(close), rank(volume), 5)))) (~344 tok)
- `alpha030.py` — Real WorldQuant Alpha101 formula — Alpha030: (-1 * correlation(rank(high), rank(volume), 3)) (~290 tok)
- `alpha031.py` — Real WorldQuant Alpha101 formula — Alpha031: (rank(rank(rank(decay_linear((-1 * rank(rank(delta(close, 10)))), 10)))) + rank((-1 * delta(close, 3))... (~450 tok)
- `alpha032.py` — Real WorldQuant Alpha101 formula — Alpha032: (scale(((sma(close, 7) / 7) - close)) + (20 * scale(correlation(vwap, delay(close, 5), 230)))) (~390 tok)
- `alpha033.py` — Real WorldQuant Alpha101 formula — Alpha033: rank((-1 * ((1 - (open / close))))) (~274 tok)
- `alpha034.py` — Real WorldQuant Alpha101 formula — Alpha034: rank(((1 - rank((stddev(returns, 2) / stddev(returns, 5)))) + (1 - rank(delta(close, 1))))) (~371 tok)
- `alpha035.py` — Real WorldQuant Alpha101 formula — Alpha035: ((Ts_Rank(volume, 32) * (1 - Ts_Rank(((close + high) - low), 16))) * (1 - Ts_Rank(returns, 32))) (~370 tok)
- `alpha036.py` — Real WorldQuant Alpha101 formula — Alpha036: (((((2.21 * rank(correlation((close - open), delay(volume, 1), 15))) + (0.7 * rank((open - close)))) +... (~651 tok)
- `alpha037.py` — Real WorldQuant Alpha101 formula — Alpha037: (rank(correlation(delay((open - close), 1), close, 200)) + rank((open - close))) (~350 tok)
- `alpha038.py` — Real WorldQuant Alpha101 formula — Alpha038: (-1 * rank(Ts_Rank(close, 10))) * rank((close / open)) (~324 tok)
- `alpha039.py` — Real WorldQuant Alpha101 formula — Alpha039: ((-1 * rank((delta(close, 7) * (1 - rank(decay_linear((volume / adv20), 9)))))) * (1 + rank(sma(return... (~426 tok)
- `alpha040.py` — Real WorldQuant Alpha101 formula — Alpha040: ((-1 * rank(stddev(high, 10))) * correlation(high, volume, 10)) (~310 tok)
- `alpha041.py` — Real WorldQuant Alpha101 formula — Alpha041: (((high * low)^0.5) - vwap) (~297 tok)
- `alpha042.py` — Real WorldQuant Alpha101 formula — Alpha042: (rank((vwap - close)) / rank((vwap + close))) (~316 tok)
- `alpha043.py` — Real WorldQuant Alpha101 formula — Alpha043: (ts_rank((volume / adv20), 20) * ts_rank((-1 * delta(close, 7)), 8)) (~327 tok)
- `alpha044.py` — Real WorldQuant Alpha101 formula — Alpha044: (-1 * correlation(high, rank(volume), 5)) (~305 tok)
- `alpha045.py` — Real WorldQuant Alpha101 formula — Alpha045: (-1 * ((rank((sma(delay(close, 5), 20))) * correlation(close, volume, 2)) * rank(correlation(ts_sum(cl... (~426 tok)
- `alpha046.py` — Real WorldQuant Alpha101 formula — Alpha046: ((0.25 < (((delay(close, 20) - delay(close, 10)) / 10) - ((delay(close, 10) - close) / 10))) ? (-1 * 1... (~410 tok)
- `alpha047.py` — Real WorldQuant Alpha101 formula — Alpha047: ((((rank((1 / close)) * volume) / adv20) * ((high * rank((high - close))) / (sma(high, 5) / 5))) - ran... (~450 tok)
- `alpha048.py` — Real WorldQuant Alpha101 formula — Alpha048: (indneutralize(((correlation(delta(close, 1), delta(delay(close, 1), 1), 250) * delta(close, 1)) / clo... (~388 tok)
- `alpha049.py` — Real WorldQuant Alpha101 formula — Alpha049: (((((delay(close, 20) - delay(close, 10)) / 10) - ((delay(close, 10) - close) / 10)) < (-1 * 0.1)) ? 1... (~370 tok)
- `alpha050.py` — Real WorldQuant Alpha101 formula — Alpha050: (-1 * ts_max(rank(correlation(rank(volume), rank(vwap), 5)), 5)) (~336 tok)
- `alpha051.py` — Real WorldQuant Alpha101 formula — Alpha051: (((((delay(close, 20) - delay(close, 10)) / 10) - ((delay(close, 10) - close) / 10)) < (-1 * 0.05)) ? ... (~370 tok)
- `alpha052.py` — Real WorldQuant Alpha101 formula — Alpha052: ((((-1 * ts_min(low, 5)) + delay(ts_min(low, 5), 5)) * rank(((sum(returns, 240) - sum(returns, 20)) / ... (~423 tok)
- `alpha053.py` — Real WorldQuant Alpha101 formula — Alpha053: (-1 * delta((((close - low) - (high - close)) / (close - low)), 9)) (~341 tok)
- `alpha054.py` — Real WorldQuant Alpha101 formula — Alpha054: ((-1 * ((low - close) * (open^5))) / ((low - high) * (close^5))) (~333 tok)
- `alpha055.py` — Real WorldQuant Alpha101 formula — Alpha055: (-1 * correlation(rank(((close - ts_min(low, 12)) / (ts_max(high, 12) - ts_min(low, 12)))), rank(volum... (~408 tok)
- `alpha056.py` — Real WorldQuant Alpha101 formula — Alpha056: (0 - (1 * (rank((sma(returns, 10) / sma(sma(returns, 2), 3))) * rank((returns * cap))))) (~347 tok)
- `alpha057.py` — Real WorldQuant Alpha101 formula — Alpha057: (0 - (1 * ((close - vwap) / decay_linear(rank(ts_argmax(close, 30)), 2)))) (~361 tok)
- `alpha058.py` — Real WorldQuant Alpha101 formula — Alpha058: (-1 * Ts_Rank(decay_linear(correlation(IndNeutralize(vwap, IndClass.sector), volume, 3.92795), 7.89291... (~388 tok)
- `alpha059.py` — Real WorldQuant Alpha101 formula — Alpha059: (-1 * Ts_Rank(decay_linear(correlation(IndNeutralize(((vwap * 0.728317) + (vwap * (1 - 0.728317))), In... (~404 tok)
- `alpha060.py` — Real WorldQuant Alpha101 formula — Alpha060: (0 - (1 * ((2 * scale(rank(((((close - low) - (high - close)) / (high - low)) * volume)))) - scale(ran... (~414 tok)
- `alpha061.py` — Real WorldQuant Alpha101 formula — Alpha061: (rank((vwap - ts_min(vwap, 16.1219))) < rank(correlation(vwap, adv180, 17.9282))) (~386 tok)
- `alpha062.py` — Real WorldQuant Alpha101 formula — Alpha062: ((rank(correlation(vwap, sum(adv20, 22.4101), 9.91009)) < rank(((rank(open) + rank(open)) < (rank(((hi... (~478 tok)
- `alpha063.py` — Real WorldQuant Alpha101 formula — Alpha063: ((rank(decay_linear(delta(IndNeutralize(close, IndClass.industry), 2.25164), 8.22237)) - rank(decay_li... (~469 tok)
- `alpha064.py` — Real WorldQuant Alpha101 formula — Alpha064: ((rank(correlation(sum(((open * 0.178404) + (low * (1 - 0.178404))), 12.7054), sum(adv120, 12.7054), 1... (~543 tok)
- `alpha065.py` — Real WorldQuant Alpha101 formula — Alpha065: ((rank(correlation(((open * 0.00817205) + (vwap * (1 - 0.00817205))), sum(adv60, 8.6911), 6.40374)) < ... (~474 tok)
- `alpha066.py` — Real WorldQuant Alpha101 formula — Alpha066: ((rank(decay_linear(delta(vwap, 3.51013), 7.23052)) + Ts_Rank(decay_linear(((((low * 0.96633) + (low *... (~473 tok)
- `alpha067.py` — Real WorldQuant Alpha101 formula — Alpha067: Requires proprietary industry data. Simplified momentum-based implementation. (~322 tok)
- `alpha068.py` — Real WorldQuant Alpha101 formula — Alpha068: (-1 * (ts_rank(correlation(rank(high), rank(adv15), 9), 14) < rank(delta((close * 0.518371) + (low * (... (~424 tok)
- `alpha069.py` — Real WorldQuant Alpha101 formula — Alpha069: Momentum-volatility composite (~295 tok)
- `alpha070.py` — Real WorldQuant Alpha101 formula — Alpha070: Price-volume interaction composite (~293 tok)
- `alpha071.py` — Real WorldQuant Alpha101 formula — Alpha071: max(ts_rank(decay_linear(correlation(ts_rank(close, 4), ts_rank(adv180, 12), 18), 4), 16), ts_rank(dec... (~517 tok)
- `alpha072.py` — Real WorldQuant Alpha101 formula — Alpha072: (rank(decay_linear(correlation(((high + low) / 2), adv40, 9), 10)) / rank(decay_linear(correlation(ts_... (~490 tok)
- `alpha073.py` — Real WorldQuant Alpha101 formula — Alpha073: -1 * max(rank(decay_linear(delta(vwap, 5), 3)), ts_rank(decay_linear((delta((open * 0.147155) + (low *... (~454 tok)
- `alpha074.py` — Real WorldQuant Alpha101 formula — Alpha074: (-1 * (rank(correlation(close, sma(adv30, 37), 15)) < rank(correlation(rank((high * 0.0261661) + (vwap... (~487 tok)
- `alpha075.py` — Real WorldQuant Alpha101 formula — Alpha075: (rank(correlation(vwap, volume, 4)) < rank(correlation(rank(low), rank(adv50), 12))) (~405 tok)
- `alpha076.py` — Real WorldQuant Alpha101 formula — Alpha076: Volume-price trend composite (~283 tok)
- `alpha077.py` — Real WorldQuant Alpha101 formula — Alpha077: min(rank(decay_linear(((((high + low) / 2) + high) - (vwap + high)), 20)), rank(decay_linear(correlati... (~487 tok)
- `alpha078.py` — Real WorldQuant Alpha101 formula — Alpha078: (rank(correlation(ts_sum(((low * 0.352233) + (vwap * (1 - 0.352233))), 20), ts_sum(adv40, 20), 7)) ^ r... (~467 tok)
- `alpha079.py` — Real WorldQuant Alpha101 formula — Alpha079: Return momentum composite (~276 tok)
- `alpha080.py` — Real WorldQuant Alpha101 formula — Alpha080: Price-volume divergence score (~282 tok)
- `alpha081.py` — Real WorldQuant Alpha101 formula — Alpha081: (-1 * (rank(log(product(rank((rank(correlation(vwap, ts_sum(adv10, 50), 8))^4)), 15))) < rank(correlat... (~485 tok)
- `alpha082.py` — Real WorldQuant Alpha101 formula — Alpha082: Momentum correlation composite (~286 tok)
- `alpha083.py` — Real WorldQuant Alpha101 formula — Alpha083: (rank(delay((high - low) / (ts_sum(close, 5) / 5), 2)) * rank(rank(volume))) / ((high - low) / (ts_sum... (~461 tok)
- `alpha084.py` — Real WorldQuant Alpha101 formula — Alpha084: pow(ts_rank(vwap - ts_max(vwap, 15), 21), delta(close, 5)) (~340 tok)
- `alpha085.py` — Real WorldQuant Alpha101 formula — Alpha085: (rank(correlation((high * 0.876703) + (close * (1 - 0.876703)), adv30, 10)) ^ rank(correlation(ts_rank... (~453 tok)
- `alpha086.py` — Real WorldQuant Alpha101 formula — Alpha086: (-1 * (ts_rank(correlation(close, sma(adv20, 15), 6), 20) < rank((open + close) - (vwap + open)))) (~437 tok)
- `alpha087.py` — Real WorldQuant Alpha101 formula — Alpha087: Volume-price momentum composite (~295 tok)
- `alpha088.py` — Real WorldQuant Alpha101 formula — Alpha088: min(rank(decay_linear(((rank(open) + rank(low)) - (rank(high) + rank(close))), 8)), ts_rank(decay_line... (~521 tok)
- `alpha089.py` — Real WorldQuant Alpha101 formula — Alpha089: Volatility-adjusted momentum (~292 tok)
- `alpha090.py` — Real WorldQuant Alpha101 formula — Alpha090: Price dispersion: ts_std(close, 10) / ts_mean(close, 10) (~300 tok)
- `alpha091.py` — Real WorldQuant Alpha101 formula — Alpha091: Return-volume correlation composite (~294 tok)
- `alpha092.py` — Real WorldQuant Alpha101 formula — Alpha092: min(ts_rank(decay_linear((((high + low) / 2 + close) < (low + open)), 15), 19), ts_rank(decay_linear(c... (~487 tok)
- `alpha093.py` — Real WorldQuant Alpha101 formula — Alpha093: Volume-price rank divergence (~286 tok)
- `alpha094.py` — Real WorldQuant Alpha101 formula — Alpha094: (-1 * rank(vwap - ts_min(vwap, 12)) ^ ts_rank(correlation(ts_rank(vwap, 20), ts_rank(adv60, 4), 18), 3)) (~412 tok)
- `alpha095.py` — Real WorldQuant Alpha101 formula — Alpha095: (rank(open - ts_min(open, 12)) < ts_rank((rank(correlation(sma((high + low) / 2, 19), sma(adv40, 19), ... (~434 tok)
- `alpha096.py` — Real WorldQuant Alpha101 formula — Alpha096: (-1 * max(ts_rank(decay_linear(correlation(rank(vwap), rank(volume), 4), 4), 8), ts_rank(decay_linear(... (~549 tok)
- `alpha097.py` — Real WorldQuant Alpha101 formula — Alpha097: Volume-weighted return momentum (~295 tok)
- `alpha098.py` — Real WorldQuant Alpha101 formula — Alpha098: (rank(decay_linear(correlation(vwap, sma(adv5, 26), 5), 7)) - rank(decay_linear(ts_rank(ts_argmin(corr... (~529 tok)
- `alpha099.py` — Real WorldQuant Alpha101 formula — Alpha099: (-1 * (rank(correlation(ts_sum((high + low) / 2, 20), ts_sum(adv60, 20), 9)) < rank(correlation(low, v... (~424 tok)
- `alpha100.py` — Real WorldQuant Alpha101 formula — Alpha100: Return-volume momentum composite (~294 tok)
- `alpha101.py` — Real WorldQuant Alpha101 formula — Alpha101: ((close - open) / ((high - low) + 0.001)) (~288 tok)
- `base.py` — Required columns for alpha factor computation (~587 tok)
- `factor_descriptions.py` (~7390 tok)
- `factor_pipeline.py` — FactorPipeline: compute_factors (~311 tok)
- `factor_registry.py` — FactorRegistry: ensure_initialized, reset, register, get + 2 more (~960 tok)
- `operators.py` — WorldQuant Alpha101 operators — building blocks for complex factor expressions. (~1259 tok)

## core/alpha/management/

- `__init__.py` — Factor Management System. (~2726 tok)
- `factor_decay.py` — FactorHealth: check, batch_check (~1529 tok)
- `industry_neutral.py` — IndustryNeutralizer: neutralize_by_mean, neutralize_by_zscore, neutralize_by_regression, neutralize_ (~850 tok)
- `report_generator.py` — class: generate, save_json, to_dict, save_html + 1 more (~2746 tok)

## core/alpha/mining/

- `__init__.py` — Genetic Programming Factor Mining Engine. (~3561 tok)
- `genetic_programming.py` — class: mine, save_factors, load_factors (~1513 tok)
- `operator_set.py` — ts_rank, ts_sum, ts_mean, ts_std (~1310 tok)

## core/config/

- `__init__.py` (~0 tok)
- `settings.py` — Settings: db_url, get_settings (~576 tok)

## core/data/

- `__init__.py` — Data Layer — unified market data access, caching, and quality control. (~123 tok)
- `cache_manager.py` — Two-level cache: in-memory LRU + Redis. (~1053 tok)
- `cache.py` — View: get, delete, get, delete (~696 tok)
- `continuous_contract.py` — ContinuousContract: build, get_roll_schedule, calculate_roll_yield, is_in_contango + 3 more (~3513 tok)
- `contract_resolver.py` — Contract metadata resolver — symbol↔contract mapping with main-contract detection. (~1646 tok)
- `data_quality.py` — Data quality guard — six checks every incoming dataframe must pass. (~1499 tok)
- `history_store.py` — Historical data store — save, query, repair. (~2212 tok)
- `market_data_manager.py` — Unified market data entry point with cache, quality guard, and multi-source routing. (~3043 tok)
- `realtime_sync_service.py` — API: POST, GET (6 endpoints) (~2255 tok)

## core/db/

- `__init__.py` (~0 tok)
- `models.py` — SQLAlchemy: Base (contracts) (~3826 tok)
- `session.py` — get_db_url, get_engine, get_session_maker, get_session (~373 tok)

## core/db/migrations/

- `__init__.py` (~0 tok)
- `env.py` — Alembic environment configuration — async support for PostgreSQL + SQLite fallback. (~702 tok)
- `script.py.mako` (~170 tok)

## core/db/migrations/versions/

- `5622da4f0062_initial_schema.py` — initial_schema (~4719 tok)

## core/llm/

- `__init__.py` — LLM Integration: Multi-provider LLM support (OpenAI, Anthropic, DeepSeek, Ollama, etc.). (~275 tok)
- `code_reviewer.py` — LLM-powered code reviewer: analyze code quality, bugs, and improvements. (~1198 tok)
- `comparator.py` — Model comparator — run the same prompt across multiple models and compare results. (~1692 tok)
- `deepseek_client.py` — DeepSeek API client — OpenAI-compatible interface for DeepSeek models. (~1746 tok)
- `llm_client.py` — Generic LLMClient — multi-provider LLM client with auto-discovery. (~1478 tok)
- `market_analyzer.py` — LLM-powered market analyzer: interpret market data and generate insights. (~1691 tok)
- `strategy_advisor.py` — LLMStrategyAdvisor: ask, generate_strategy, compute (~1541 tok)
- `strategy_factory.py` — LLM Strategy Factory — generate, validate, and register complete strategies from natural language. (~3370 tok)
- `strategy_generator.py` — LLM-powered strategy generator: generate, optimize, and evolve trading strategies. (~1504 tok)

## core/llm/providers/

- `__init__.py` — LLM Provider abstraction layer — supports OpenAI-compatible, Anthropic, and Ollama protocols. (~137 tok)
- `anthropic_provider.py` — Anthropic Claude provider — uses Anthropic Messages API. (~1072 tok)
- `base.py` — Abstract base class for all LLM providers. (~655 tok)
- `ollama_provider.py` — Ollama provider — local models via Ollama API. (~944 tok)
- `openai_provider.py` — OpenAI-compatible provider — works for OpenAI, DeepSeek, Groq, Together, Moonshot, etc. (~1174 tok)
- `registry.py` — Provider registry — manages multiple LLM providers from YAML config. (~2108 tok)

## core/resonance/

- `__init__.py` (~82 tok)
- `engine_v2.py` — class: calculate (~1132 tok)
- `matrix.py` — MatrixEngine: calculate (~333 tok)
- `scanner.py` — ScannerEngine: calculate (~292 tok)
- `voter.py` — VoterEngine: calculate (~220 tok)

## core/risk/

- `__init__.py` — Risk management: monitoring, position sizing, and risk controls. (~119 tok)

## core/risk/monitoring/

- `__init__.py` — Risk monitoring: VaR, CVaR, stress testing, risk attribution. (~94 tok)
- `cvar_calculator.py` — Conditional Value at Risk (CVaR / Expected Shortfall). (~258 tok)
- `risk_attribution.py` — Risk attribution: factor-based and asset-based. (~464 tok)
- `stress_testing.py` — Portfolio stress testing. (~603 tok)
- `var_calculator.py` — Value at Risk (VaR) calculator. (~404 tok)

## core/risk/position/

- `__init__.py` — Dynamic position management: Kelly, volatility targeting, regime-based. (~86 tok)
- `kelly_criterion.py` — Kelly criterion for optimal position sizing. (~222 tok)
- `regime_based.py` — Market-regime-based position sizing. (~132 tok)
- `volatility_targeting.py` — Volatility-targeting position sizing. (~278 tok)

## core/rl/

- `__init__.py` (~47 tok)
- `agents.py` — class: forward, get_params, set_params, buffer_size + 6 more (~2704 tok)
- `config.py` (~333 tok)
- `environments.py` — class: action_space_size, observation_space_size, reset, step (~1960 tok)

## core/rl/advanced/

- `__init__.py` — Advanced RL algorithms: SAC, TD3, DDPG. (~42 tok)
- `ddpg.py` — Deep Deterministic Policy Gradient (DDPG) — NumPy implementation. (~624 tok)
- `sac.py` — Soft Actor-Critic (SAC) — NumPy implementation. (~838 tok)
- `td3.py` — Twin Delayed DDPG (TD3) — NumPy implementation. (~748 tok)

## core/rl/deep/

- `__init__.py` — Deep RL neural networks and replay buffers. (~86 tok)
- `networks.py` — Neural network building blocks for deep RL algorithms. (~1529 tok)
- `optim.py` — Shared gradient helpers for NumPy-based RL algorithms. (~657 tok)
- `replay_buffer.py` — Experience replay buffers for deep RL. (~765 tok)
- `trainers.py` — DQN Trainer with experience replay and target network. (~1101 tok)

## core/rl/multi_agent/

- `__init__.py` — Multi-agent RL: MADDPG. (~26 tok)

## core/rl/multi_agent/algorithms/

- `__init__.py` (~14 tok)
- `maddpg.py` — Multi-Agent DDPG (MADDPG) — NumPy implementation. (~1276 tok)

## core/rl/offline/

- `__init__.py` — Offline RL: Conservative Q-Learning (CQL). (~44 tok)
- `conservative.py` — Conservative Q-Learning (CQL) for offline RL — NumPy implementation. (~706 tok)
- `dataset.py` — Offline dataset management for CQL. (~444 tok)

## core/tasks/

- `__init__.py` — Celery async task layer — backtest, training, and reporting workers. (~88 tok)
- `backtest_tasks.py` — Celery task: run vectorized backtest asynchronously. (~508 tok)
- `celery_app.py` — Celery application instance with queue routing and concurrency settings. (~313 tok)
- `training_tasks.py` — Celery task: train ML models asynchronously. (~385 tok)

## core/tournament/

- `tournament_system.py` — API: POST, GET (3 endpoints) (~3443 tok)

## core/utils/

- `__init__.py` (~0 tok)
- `decorators.py` — retry, decorator, async_wrapper, timed + 3 more (~435 tok)
- `logger.py` — setup_logger (~131 tok)

## cross_symbol/

- `__init__.py` (~0 tok)
- `cross_market.py` — CrossMarketAnalyzer: rolling_correlation, analyze, detect_regime_shift (~435 tok)
- `pair_trading.py` — class: compute_cointegration, generate_signals (~694 tok)
- `spread_analyzer.py` — compute_spread, zscore, half_life, generate_signals (~442 tok)

## data_center/

- `__init__.py` (~216 tok)
- `aggregator.py` — aggregate_symbol, aggregate_all (~1186 tok)
- `cross_market.py` — compute_all (~1208 tok)
- `options_analytics.py` — compute_option_greeks (~656 tok)

## data_center/ (DuckDB 统一仓库 — 2026-06-18 新增)


## data_center/api/

- `__init__.py` — API: 10 endpoints (~6540 tok)
- `warehouse.py` — API: 11 endpoints (~7761 tok)

## data_center/collectors/

- `__init__.py` — 资产类别采集器 — 编排 fetch -> normalize -> DuckDB 写入。 (~114 tok)
- `base_collector.py` — BaseCollector: col, store_kline (~668 tok)
- `futures_collector.py` — FuturesCollector: discover_contracts, collect_contract, mark_main_contract, collect_product + 2 more (~2525 tok)
- `macro_collector.py` — MacroCollector: collect, conv, collect_all (~962 tok)
- `options_collector.py` — OptionsCollector: collect_etf_option_daily, collect_index_option_daily, collect_greeks_snapshot, col (~4082 tok)
- `stocks_collector.py` — StocksCollector: list_all_symbols, collect_kline, collect_info, collect_financial + 1 more (~2905 tok)

## data_center/collectors/ (资产类别采集器 — 2026-06-18 新增)


## data_center/core/

- `__init__.py` (~24 tok)
- `base_fetcher.py` — KlineInterval: name, display_name, info, get_kline + 3 more (~1337 tok)
- `data_source.py` — DataSourceManager: register, unregister, list_sources, get_source + 7 more (~3107 tok)
- `retry.py` — retry_sync (~431 tok)

## data_center/db/

- `__init__.py` — 统一数据库 schema 与品种/合约注册表。 (~28 tok)
- `init_schema.sql` — 交易系统统一数据库 — DuckDB Schema (~2237 tok)
- `registry.py` — SymbolRegistry: get_or_create_product, parse_contract, get_or_create_symbol (~1489 tok)
- `seed_loader.py` — load_products, load_cross_market, load_all (~744 tok)

## data_center/db/seeds/

- `cross_market_seed.csv` (~146 tok)
- `macro_indicators.csv` (~98 tok)
- `products.csv` (~457 tok)

## data_center/fetchers/

- `__init__.py` (~102 tok)
- `akshare_fetcher.py` — AKShareFetcher: get_futures_daily, get_futures_hist_em, get_kline, get_futures_minute + 4 more (~3034 tok)
- `alpha_vantage_fetcher.py` — AlphaVantageFetcher: get_stock_daily, get_forex_rate, get_forex_daily, get_crypto_daily + 4 more (~1881 tok)
- `baostock_fetcher.py` — BaoStockFetcher: get_kline, get_realtime, get_trade_dates, validate (~1456 tok)
- `ctp_fetcher.py` — CTPFetcher: get_kline, get_realtime, ticks_to_bars, validate (~836 tok)
- `eia_cftc_fetcher.py` — EIAFetcher: get_crude_oil_inventories, get_gasoline_inventories, get_natural_gas_storage, get_kline + 6 more (~1822 tok)
- `fmp_fetcher.py` — FMPFetcher: get_company_profile, get_income_statement, get_balance_sheet, get_cash_flow + 5 more (~1331 tok)
- `fred_fetcher.py` — FREDFetcher: get_series, get_series_df, get_multiple_series, get_gdp + 8 more (~1496 tok)
- `options_fetcher.py` — ChinaOptionsFetcher: get_etf_option_daily, get_etf_option_realtime, get_etf_option_codes, get_index_ (~3868 tok)
- `tdx_fetcher.py` — TDXFetcher: get_kline, get_realtime, get_batch_quotes (~4860 tok)
- `tiingo_fetcher.py` — TiingoFetcher: get_stock_daily, get_forex_prices, get_crypto_prices, get_ticker_metadata + 3 more (~1435 tok)
- `tqsdk_fetcher.py` — TqSdkFetcher: get_kline, get_realtime, close, validate + 1 more (~1837 tok)
- `tushare_fetcher.py` — TushareFetcher: get_kline, get_realtime, get_trade_dates, get_financial + 2 more (~1543 tok)
- `unified_fetcher.py` — UnifiedFetcher: get_kline, get_realtime, get_source_name, validate + 1 more (~1618 tok)
- `yfinance_fetcher.py` — YFinanceFetcher: get_kline, get_realtime, get_info, validate + 1 more (~1946 tok)

## data_center/history/

- `__init__.py` (~71 tok)
- `collect_jobs.py` — CollectJobs: is_running, start, status, get_jobs (~604 tok)
- `data_store.py` — URL configuration (~1622 tok)
- `download_manager.py` — DownloadStatus: display_name, create_task, execute_task, execute_batch + 7 more (~3198 tok)
- `full_downloader.py` — reset_ckpt, collect_futures_product, run_full, default_test_start (~2155 tok)
- `sync_scheduler.py` — class: add_symbol, remove_symbol, start, stop + 3 more (~1248 tok)

## data_center/knowledge/

- `__init__.py` (~47 tok)
- `contract_knowledge.py` — class: exchange_display (~6905 tok)
- `contract_lifecycle.py` — parse_expiry, status, lifecycle_window, lifecycle_guard (~597 tok)
- `exchanges.py` — from: get_exchange, list_exchanges (~384 tok)
- `main_contract.py` — MainContractResolver: parse_contract_code, is_valid_contract_month, get_main_contract_month, get_main_contract_code + 2 more (~2260 tok)
- `options_knowledge.py` — class: get_product, list_products, get_strategy, list_strategies + 2 more (~1986 tok)
- `stock_knowledge.py` — class: get_sector, list_sectors, relations_for_sector, sectors_for_futures + 2 more (~1681 tok)

## data_center/storage/

- `__init__.py` — DuckDB 统一数据仓库存储层。 (~33 tok)
- `duckdb_store.py` — DuckDBStore: execute, upsert_df, query, close + 1 more (~942 tok)

## data_center/verification/

- `__init__.py` (~21 tok)
- `verifier.py` — class: check_quality, cross_validate, cross_validate_all (~2295 tok)

## docs/

- `数据采集系统升级说明.md` — 数据采集系统升级说明 (~2320 tok)
- `API_REFERENCE.md` — Trading Strategy Center — API 参考文档 (~866 tok)
- `DATABASE.md` — 数据库设计文档 (~4433 tok)
- `IMPLEMENTATION_PROGRESS.md` — Strategy Intelligence V2 - Implementation Progress (~1747 tok)
- `INTELLIGENCE_UPGRADE.md` — Intelligence Upgrade Documentation (~3125 tok)
- `USAGE_FACTOR.md` — 因子系统使用指南 (USAGE) (~1130 tok)

## docs/superpowers/plans/

- `2026-06-12-alpha-factor-extension.md` — Alpha因子扩展实施计划 (~28245 tok)
- `2026-06-12-rl-risk-monitoring-plan.md` — Strategy Intelligence V2 Implementation Plan (~10101 tok)
- `2026-06-12-strategy-intelligence-upgrade.md` — 策略智能化全栈升级实现计划 (~21810 tok)

## docs/superpowers/specs/

- `2026-06-12-strategy-intelligence-upgrade-design.md` — 策略智能化全栈升级设计文档 (~9657 tok)
- `2026-06-12-strategy-intelligence-v2-design.md` — 策略智能化V2升级设计文档 (~16872 tok)

## evolution/

- `__init__.py` (~0 tok)
- `strategy_evolution.py` — StrategyEvolution: create_initial_population, select, crossover, mutate + 1 more (~1012 tok)

## frontend/

- `FRONTEND_UPGRADE_PLAN.md` — 前端升级计划 - 用户体验优化 (~1055 tok)
- `index.html` — Trading Strategy Center (~84 tok)
- `package-lock.json` — npm lock file (~31394 tok)
- `package.json` — Node.js package manifest (~195 tok)
- `tsconfig.json` — TypeScript configuration (~177 tok)
- `tsconfig.tsbuildinfo` (~155 tok)
- `vite.config.ts` — Vite build configuration (~212 tok)

## frontend/src/

- `App.css` — Styles: 12 rules, 2 media queries, 2 animations (~557 tok)
- `App.tsx` — 动态导入页面组件 (~988 tok)
- `main.tsx` (~145 tok)

## frontend/src/api/

- `client.ts` — API routes: GET, DELETE, POST (4 endpoints) (~1785 tok)

## frontend/src/components/

- `DataSyncPanel.tsx` — DataSyncPanel — renders table — uses useState, useEffect (~3177 tok)
- `Layout.tsx` — menuItems (~1831 tok)
- `RealtimeSignalPanel.tsx` — generateMockSignal — uses useState, useEffect (~3281 tok)
- `StrategyBuilder.tsx` — StrategyBuilder — renders form — uses useForm, useState (~2711 tok)

## frontend/src/pages/

- `Backtest.tsx` — MOCK_RESULTS — renders form, table — uses useForm, useEffect (~2193 tok)
- `Dashboard.tsx` — MOCK_EQUITY — renders table, chart — uses useEffect, useState (~2593 tok)
- `DataCenter.tsx` — API (~24615 tok)
- `FactorResearch.tsx` — mockFactors (~14734 tok)
- `Feedback.tsx` — Feedback — renders table (~943 tok)
- `LLMConfig.tsx` — LLMConfig (~1056 tok)
- `ML.tsx` — MOCK_MODELS — renders form, table, modal — uses useState, useForm, useEffect (~2184 tok)
- `MLAnalyzer.tsx` — DIR_COLOR (~1462 tok)
- `Monitoring.tsx` — METRICS — renders table, chart — uses useState, useEffect (~3049 tok)
- `Phase3.tsx` — DIR_COLOR — renders table (~4391 tok)
- `Portfolio.tsx` — MOCK_PORTFOLIO — renders form, table, chart, modal — uses useState, useForm, useEffect (~2601 tok)
- `Settings.tsx` — Settings — renders form — uses useState, useForm (~2262 tok)
- `Strategy.tsx` — statusMap — renders form, table, modal — uses useState, useForm, useEffect (~2352 tok)
- `StrategyLibrary.tsx` — TYPE_CN — renders table (~1374 tok)
- `Tournament.tsx` — MOCK_STANDINGS — renders table — uses useEffect (~1740 tok)
- `Trading.tsx` — MOCK_POSITIONS — renders form, table, chart, modal — uses useEffect, useState, useForm (~3626 tok)

## frontend/src/services/

- `factorApi.ts` — API routes: POST, GET (10 endpoints) (~850 tok)
- `phase3Api.ts` — API routes: GET, POST (4 endpoints) (~254 tok)
- `phase4Api.ts` — API routes: POST, GET (7 endpoints) (~383 tok)
- `strategyApi.ts` — API routes: GET (2 endpoints) (~128 tok)

## frontend/src/store/

- `useAppStore.ts` — Exports useStrategyStore, useTradingStore, useBacktestStore, usePortfolioStore + 3 more (~1369 tok)

## frontend/src/styles/

- `global.css` — Styles: 77 rules, 31 vars, 1 animations (~3779 tok)

## fundamental/

- `__init__.py` (~0 tok)
- `fundamental_analyzer.py` — FundamentalAnalyzer: basis, cost_of_carry, fair_value, analyze_futures (~523 tok)

## logs/

- `trading_2026-06-13.log` (~149 tok)
- `trading_2026-06-14.log` (~50 tok)
- `trading_2026-06-15.log` (~50 tok)

## market_state/

- `__init__.py` (~30 tok)
- `entropy_analyzer.py` — EntropyAnalyzer: compute_entropy, approximate_entropy, compute_market_efficiency (~665 tok)
- `regime_detector_v2.py` — RegimeV2: fit, predict, predict_proba, detect_change_point (~1350 tok)
- `regime_detector.py` — from: detect (~1189 tok)
- `state_machine_v2.py` — EnhancedStateMachine: reset, next_state, get_transition_probability, get_current_state + 2 more (~1332 tok)
- `state_machine.py` — StateMachine: update, predict_next, transition_probs (~388 tok)

## microstructure/

- `__init__.py` (~0 tok)
- `market_depth.py` — MarketDepthAnalyzer: estimate_spread, impact_cost (~263 tok)
- `order_flow.py` — OrderFlowAnalyzer: analyze, imbalance (~322 tok)
- `spread_impact.py` — SpreadImpactAnalyzer: effective_spread, realized_spread, adverse_selection (~296 tok)

## ml/

- `__init__.py` — ML 模块统一导出。 (~205 tok)
- `auto_pipeline.py` — class: to_dict, run (~1657 tok)
- `demo.py` — demo_ml, train_fn, demo_options (~1470 tok)
- `ensemble.py` — ModelEnsemble: add_model, fit, predict, weights_info (~651 tok)
- `hyperopt.py` — HyperoptSearcher: search, objective (~1444 tok)
- `model_monitor.py` — from: to_dict, check, batch_check (~1151 tok)
- `model_selector.py` — ModelSelector: score_model, select, select_with_hyperopt, train_fn (~1262 tok)
- `pipeline.py` — class: train, predict, get_pipeline_summary (~1333 tok)
- `registry.py` — class: save, load, list_models, delete + 1 more (~1488 tok)
- `signal_adapter.py` — MLSignalAdapter: to_signals, to_combined_signal (~662 tok)
- `strategy_evolution.py` — StrategyEvolutionEngine: evolve_parameters, objective, combine_strategies, objective + 2 more (~3980 tok)
- `train.py` — train_all_models, train_pipeline_for_symbol, retrain_if_needed (~242 tok)

## ml/features/

- `__init__.py` — ML 特征工程子包。 (~95 tok)
- `cross_sectional_features.py` — CrossSectionalFeatureSet: get_features (~650 tok)
- `pipeline.py` — class: register_fn, register, register_module, compute_all + 5 more (~1630 tok)
- `technical_features.py` — TechnicalFeatureSet: get_features (~1620 tok)

## ml/models/

- `__init__.py` (~0 tok)
- `nbeats_model.py` — NBeatsBlock: forward, fit, predict, save + 3 more (~2463 tok)
- `sklearn_wrapper.py` — SklearnModel: fit, predict, get_params, feature_importance (~1145 tok)
- `tft_model.py` — TFTModel: fit, predict, get_attention_weights, save + 3 more (~1858 tok)

## monitoring/

- `__init__.py` — Monitoring & Alerting System. (~123 tok)

## monitoring/alerting/

- `__init__.py` (~57 tok)
- `alert_manager.py` — Alert lifecycle manager. (~392 tok)
- `anomaly_detection.py` — Anomaly detection: zscore, IQR. (~291 tok)
- `threshold_rules.py` — Threshold-based alert rules engine. (~396 tok)

## monitoring/channels/

- `__init__.py` (~34 tok)
- `email_channel.py` — Email notification channel. (~302 tok)
- `feishu.py` — Feishu (Lark) notification channel. (~301 tok)

## monitoring/dashboard/

- `__init__.py` (~40 tok)
- `metrics_collector.py` — Real-time metrics collector. (~252 tok)
- `time_series_db.py` — SQLite-backed time-series storage for metrics. (~536 tok)

## monitoring/performance/

- `__init__.py` (~44 tok)
- `performance_report.py` — Performance report generation. (~284 tok)
- `return_attribution.py` — Return attribution: Brinson model. (~285 tok)

## news/

- `__init__.py` (~0 tok)
- `news_fetcher.py` — NewsFetcher: fetch (~366 tok)
- `sentiment.py` — NewsSentimentAnalyzer: analyze (~387 tok)

## options/

- `__init__.py` — 期权专属层 — 定价 / 希腊字母 / 波动率 / 策略 / 风险 / 分析。 (~112 tok)
- `base.py` — 期权策略基础数据结构与基类。 (~760 tok)
- `registry.py` — 期权策略注册表,镜像 signals/registry.py 的设计。 (~151 tok)

## options/analysis/

- `__init__.py` — 期权链分析工具 — PCR / Max Pain / 持仓量分布。 (~488 tok)

## options/greeks/

- `__init__.py` — 希腊字母引擎:解析解、数值差分、组合级聚合。 (~247 tok)
- `analytical_greeks.py` — BSM 解析希腊字母(也适用于 Black76:传 F 替代 S,设 q=r)。 (~885 tok)
- `numerical_greeks.py` — 数值差分希腊字母 — 高阶 Greeks(vanna/volga/charm/speed)。 (~1650 tok)
- `portfolio_greeks.py` — 组合级希腊字母聚合 — 把多腿期权/期货持仓的 Greeks 加权汇总。 (~648 tok)

## options/pricing/

- `__init__.py` — 期权定价引擎。 (~73 tok)
- `binomial_tree.py` — 二叉树期权定价 — 支持欧式与美式。 (~346 tok)
- `black_scholes.py` — Black-Scholes-Merton 解析定价。 (~410 tok)
- `black76.py` — Black-76 模型 — 期货期权定价(国内商品/股指期权主流)。 (~242 tok)

## options/risk/

- `__init__.py` — 期权风险层 — 组合 Greeks 限额 + 情景压力测试。 (~24 tok)
- `greeks_limits.py` — 组合 Greeks 风险限额检查。 (~658 tok)
- `stress_test.py` — 期权组合情景压力测试。 (~869 tok)

## options/strategies/

- `__init__.py` — 期权策略子包。 (~154 tok)
- `directional.py` — 方向性期权策略:Long Call / Long Put / Covered Call / Protective Put。 (~1555 tok)
- `futures_combo.py` — class: combine, compute_from_signals (~1333 tok)
- `term_arbitrage.py` — class: compute (~1384 tok)
- `term_structure.py` — 期限结构策略:Calendar Spread(日历价差)。 (~536 tok)
- `volatility_long.py` — 买波动率策略:Long Straddle / Long Strangle。 (~909 tok)
- `volatility_short.py` — 卖波动率策略:Short Straddle / Short Strangle / Iron Condor / Iron Butterfly。 (~2146 tok)

## options/volatility/

- `__init__.py` — 期权波动率体系:IV 反求、已实现波动率、SVI 曲面、IV Rank/Percentile。 (~235 tok)
- `iv_rank.py` — IV Rank / IV Percentile / 波动率锥 — 期权择时核心指标。 (~450 tok)
- `iv_solver.py` — 隐含波动率反求 — Newton-Raphson + Brent fallback。 (~646 tok)
- `realized_vol.py` — 已实现波动率 — 5 种主流估计量。 (~568 tok)
- `surface.py` — from: set_forward, add_slice, build, get_iv + 5 more (~1462 tok)
- `svi_surface.py` — SVI (Stochastic Volatility Inspired) 隐含波动率曲面。 (~440 tok)

## portfolio/

- `__init__.py` (~0 tok)
- `capital_allocation.py` — CapitalAllocation: allocate, risk_parity (~237 tok)
- `correlation_matrix.py` — CorrelationMatrix: add_price, compute, diversify_score (~338 tok)
- `portfolio_manager.py` — PortfolioManager: update_prices, get_portfolio_stats, rebalance (~649 tok)

## quant_models/

- `__init__.py` — QuantModel: fit, predict, get_params (~90 tok)

## quant_models/models/

- `__init__.py` (~0 tok)
- `arima_model.py` — ARIMAModel: fit, predict, predict_next, get_params (~428 tok)
- `cluster_model.py` — ClusterModel: fit, predict, get_params (~568 tok)
- `copula_model.py` — CopulaModel: fit, predict, tail_dependence, get_params (~464 tok)
- `garch_model.py` — GARCHModel: fit, predict, predict_volatility, get_params (~488 tok)
- `har_rv_model.py` — HAR-RV (Heterogeneous Autoregressive Realized Volatility) 模型。 (~1018 tok)
- `heston_model.py` — Heston 随机波动率模型 — 半解析期权定价 + 蒙特卡洛路径模拟。 (~1233 tok)
- `hmm_model.py` — HMModel: fit, predict, predict_proba, get_params (~504 tok)
- `hurst_exponent.py` — HurstExponentModel: fit, predict, classify, get_params (~548 tok)
- `kalman_filter.py` — KalmanFilterModel: fit, predict, get_params (~505 tok)
- `linear_regression_model.py` — LinearRegressionModel: fit, predict, predict_next, get_params (~458 tok)
- `markov_regime.py` — MarkovRegimeModel: fit, predict, get_params (~444 tok)
- `monte_carlo_sim.py` — MonteCarloModel: fit, predict, summary, get_params (~466 tok)
- `pca_model.py` — PCAModel: fit, predict, get_params (~392 tok)
- `portfolio_optimization.py` — 组合优化模型 — 风险平价 / HRP / 最小方差 / 最大分散化 / 逆波动率。 (~1452 tok)
- `random_forest_model.py` — RandomForestModel: fit, predict, get_params (~697 tok)
- `risk_models.py` — 风险度量模型 — VaR / CVaR / EVT / 最大回撤 / 相关性破裂。 (~1412 tok)
- `sabr_model.py` — SABR 随机波动率模型 — Hagan (2002) 隐含波动率近似 + 校准。 (~763 tok)
- `short_rate_models.py` — 短期利率模型 — Vasicek 与 CIR(国债期货、利率衍生品定价基础)。 (~1008 tok)
- `svm_model.py` — SVMModel: fit, predict, get_params (~749 tok)
- `wavelet_denoiser.py` — WaveletDenoiserModel: fit, predict, get_params (~457 tok)

## research/

- `README.md` — Project documentation (~1115 tok)

## research/factor_lab/

- `factor_analyzer.py` — FactorAnalyzer: calculate_ic, calculate_ic_series, calculate_icir, layered_backtest + 3 more (~2082 tok)

## resonance/

- `__init__.py` (~0 tok)
- `engine.py` — class: adjust_weights_for_regime, calculate, set_weights (~1362 tok)

## risk/

- `__init__.py` (~0 tok)
- `drawdown_controller.py` — DrawdownController: update, locked, reset (~238 tok)
- `position_sizer.py` — calculate_kelly, calculate_position_size (~196 tok)
- `risk_manager.py` — from: check_signal (~517 tok)

## scripts/

- `daily_close.py` — class: log_info, log_ok, log_warn, log_error + 3 more (~7163 tok)
- `deploy.sh` (~289 tok)
- `download_all.py` — Checkpoint: save, is_done, mark_done, mark_fail + 6 more (~1586 tok)
- `generate_alpha_factors.py` — Generate alpha033-101 factor files with real WorldQuant-style formulas. (~6326 tok)
- `init_db.py` (~7008 tok)
- `init_vps.sh` (~362 tok)
- `setup.sh` — Trading Strategy Center — 一键启动脚本 (Local Dev) (~1166 tok)
- `upgrade_alpha001_030.py` — Batch upgrade Alpha001-030 to real WorldQuant Alpha101 formulas. (~3078 tok)

## signals/

- `__init__.py` (~0 tok)
- `base.py` — Direction: compute (~347 tok)
- `catalog.py` — StrategyType: to_dict, register, build_from_registry, query + 7 more (~3229 tok)
- `engine.py` — View: get (~573 tok)
- `indicators.py` — SMA, EMA, RSI, MACD + 29 more (~3418 tok)
- `price_action.py` — detect_engulfing, detect_doji, detect_hammer, detect_shooting_star + 3 more (~610 tok)
- `registry.py` — register, get_strategy, list_strategies, get_all_strategies (~129 tok)

## signals/layering/

- `__init__.py` (~51 tok)
- `layer_strategies.py` — FilterMarketNoise: compute, compute, compute (~1625 tok)

## signals/strategies/

- `__init__.py` — 策略包自动加载器。 (~243 tok)
- `arbitrage_carry.py` — 套利 / Carry / 期限结构 / 季节性策略。 (~3118 tok)
- `arbitrage_extended.py` — 套利策略增强版 — 补充 arbitrage_carry.py 之外的套利变体。 (~1103 tok)
- `breakout_extended.py` — 突破类策略扩展。 (~1939 tok)
- `breakout_strategies.py` — BreakoutDonchian: compute, compute, compute (~1422 tok)
- `filter_strategies.py` — FilterVolatility: compute, compute, compute (~1447 tok)
- `mean_reversion_extended.py` — 均值回归类策略扩展。 (~2775 tok)
- `momentum_extended.py` — 动量类策略扩展。 (~2149 tok)
- `momentum_strategies.py` — MomentumRoc: compute, compute, compute (~1635 tok)
- `reversal_strategies.py` — ReversalRsi: compute, compute, compute (~1410 tok)
- `trend_extended.py` — 趋势类策略扩展(CTA 主力)。 (~3911 tok)
- `trend_strategies.py` — TrendMaCross: compute, compute, compute, compute (~1930 tok)

## simulation/

- `__init__.py` (~0 tok)
- `pnl_calculator.py` — PnLCalculator: update, close_trade, summary (~453 tok)
- `position_manager.py` — View: get (~749 tok)
- `rule_engine.py` — RuleEngine: add_rule, check, check_all, min_confidence_rule + 3 more (~280 tok)
- `scoring.py` — score_positions (~194 tok)
- `sim_engine.py` — class: execute_signal, close_position, get_portfolio_summary (~974 tok)

## tasks/

- `__init__.py` (~0 tok)
- `backtest_tasks.py` — run_backtest, compare_strategies (~1286 tok)
- `celery_app.py` (~185 tok)
- `training_tasks.py` — train_pipeline, train_all_models (~1079 tok)

## tests/

- `__init__.py` (~0 tok)
- `test_backtest.py` — Tests: run_returns_result, fields (~379 tok)
- `test_commodity_option_year.py` — 商品期权按年逐日采集 — 单测 (内存库, 合成三所格式日线)。 (~700 tok)
- `test_contract_lifecycle.py` — 合约生命周期 — 单测 (纯函数, 合成数据)。 (~565 tok)
- `test_data_layer_hardening.py` — 数据层加固 — H1 upsert原子性 / H4 夜盘聚合 单测。 (~1126 tok)
- `test_futures_strategies.py` — 期货策略行为正确性测试。 (~1604 tok)
- `test_options_analytics.py` — compute_option_greeks 单测 — 合成输入, 不触网/不触库。 (~562 tok)
- `test_options_collector_greeks.py` — OptionsCollector 商品期权 Greeks 编排 — 集成测试 (内存库, 注入合成数据)。 (~741 tok)
- `test_options.py` — 期权层单元测试 — 定价 / Greeks / 波动率 / 策略 / 风险 / 分析。 (~2686 tok)
- `test_quant_models_extended.py` — 扩展量化模型的单元测试。 (~2414 tok)
- `test_resonance.py` — Tests: detect, empty, output_type, strong_buy + 7 more (~851 tok)
- `test_signals.py` — Tests: sma_shape, rsi_bounds, macd_three_series, atr_positive + 22 more (~2208 tok)
- `test_stocks_incremental.py` — StocksCollector.incremental_sync — 单测 (内存库, mock 网络)。 (~688 tok)
- `test_stocks_info_financial.py` — StocksCollector 信息/财务落库 — 单测 (内存库, 合成 akshare 格式)。 (~603 tok)
- `test_warehouse_helpers_options_kb.py` — warehouse API 辅助函数 + 期权知识库 — 单测。 (~380 tok)

## tests/integration/

- `__init__.py` (~0 tok)
- `test_alpha_pipeline.py` — Integration tests for the Alpha101 factor pipeline. (~1080 tok)
- `test_api_endpoints.py` — Integration tests for all API endpoints. (~1668 tok)
- `test_intelligence_upgrade.py` — Tests: full_alpha_pipeline, alpha101_classes, ic_weight_combination, regime_weight_combination + 10 more (~7086 tok)

## tests/unit/

- `__init__.py` (~0 tok)
- `test_adaptive.py` — Tests: create_space, default_log_scale, init, normalize_in_range + 32 more (~5476 tok)
- `test_alpha.py` — Tests: init, register_factor, register_multiple, get_factor + 30 more (~3109 tok)
- `test_alpha001_010.py` — Tests: alpha_factor, alpha_factor_description, alpha_factor_compute_with_lookback, alpha004_edge_case_high_equals_low + 1 more (~738 tok)
- `test_alpha011_030.py` — Tests: alpha_factor, alpha_factor_description, alpha_factor_compute_with_lookback, alpha011_correlation_momentum + 4 more (~1156 tok)
- `test_alpha031_060.py` — Tests: alpha_factor, alpha_factor_description, alpha_factor_compute_with_lookback, alpha_factor_not_all_nan + 1 more (~741 tok)
- `test_alpha061_101.py` — Tests: alpha_factor, alpha_factor_description, alpha_factor_compute_with_lookback, alpha_factor_not_all_nan + 1 more (~739 tok)
- `test_alpha101_base.py` — Tests: is_abstract, subclass_interface, validate_with_complete_data, validate_with_missing_columns + 6 more (~1521 tok)
- `test_alpha101.py` — Tests: is_abstract, subclass_interface, is_alpha_base, properties + 8 more (~1053 tok)
- `test_catalog_feedback.py` — Phase4 A篇 — 策略目录 + C篇 反馈闭环 测试。 (~1205 tok)
- `test_factor_cli.py` — factor_cli 统一入口 — 单元测试 (CSV 路径, 不依赖仓库/网络)。 (~819 tok)
- `test_factor_mining.py` — 因子挖掘 — 单元测试 (Spec §7.1)。 (~1087 tok)
- `test_factor_phase2.py` — 因子管理 Phase2 — 算子集/健康检测/行业中性化/报告 单元测试。 (~1395 tok)
- `test_ml_auto_advisor.py` — Phase4 B篇 ML自动迭代 + D篇 LLM建议器 测试。 (~1181 tok)
- `test_ml_features.py` — ML 特征工程测试。 (~726 tok)
- `test_ml_registry.py` — ML 模型注册中心 / sklearn 包装 / 超参搜索 / 集成 测试。 (~980 tok)
- `test_options_strategies_extended.py` — 期权-期货联合策略 / ML 信号适配器 扩展测试。 (~689 tok)
- `test_options_surface.py` — 期权波动率曲面 / 期限结构套利 测试。 (~996 tok)
- `test_warehouse.py` — TestDuckDBStore: store, test_schema_tables_created, test_upsert_dedup, test_upsert_empty_df + 8 more (~1540 tok)
