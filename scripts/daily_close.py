#!/usr/bin/env python3
"""
Trading Strategy Center — 收盘后处理脚本
========================================

功能:
  1. 计算当日 PnL → 写入 performance_snapshots (按策略)
  2. 清理过期信号 (默认 > 7 天)
  3. 触发 ML 模型重训 (如需)
  4. 生成收盘日报

用法:
  # 完整收盘处理
  python scripts/daily_close.py

  # 仅 PnL 计算
  python scripts/daily_close.py --pnl-only

  # 仅信号清理
  python scripts/daily_close.py --cleanup-only

  # 强制 ML 重训
  python scripts/daily_close.py --retrain

  # 使用 PostgreSQL (默认 SQLite)
  python scripts/daily_close.py --db postgresql

  # 指定日期 (默认昨天)
  python scripts/daily_close.py --date 2026-06-12

环境变量:
  DB_HOST, DB_PORT, DB_USER, DB_PASS, DB_NAME — PostgreSQL 连接参数
  SIGNAL_RETENTION_DAYS — 信号保留天数 (默认 7)
  ML_RETRAIN_INTERVAL_DAYS — ML 重训间隔 (默认 7)
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

# 将项目根目录加入 sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# 日志颜色
_RESET = "\033[0m"
_GREEN = "\033[92m"
_YELLOW = "\033[93m"
_RED = "\033[91m"
_CYAN = "\033[96m"


def _color(text: str, code: str) -> str:
    return f"{code}{text}{_RESET}"


def log_info(msg: str):
    print(f"  {_color('→', _CYAN)} {msg}")


def log_ok(msg: str):
    print(f"  {_color('✓', _GREEN)} {msg}")


def log_warn(msg: str):
    print(f"  {_color('⚠', _YELLOW)} {msg}")


def log_error(msg: str):
    print(f"  {_color('✗', _RED)} {msg}")


# ============================================================
# 数据模型
# ============================================================

@dataclass
class DailyPnL:
    """按策略汇总的每日 PnL"""
    strategy_name: str
    daily_realized_pnl: float = 0.0
    daily_unrealized_pnl: float = 0.0
    trades_closed: int = 0
    trades_opened: int = 0
    positions_open: int = 0
    position_value: float = 0.0
    cash: float = 0.0
    total_equity: float = 0.0
    total_pnl: float = 0.0
    drawdown: float = 0.0


# ============================================================
# 步骤 1: 计算当日 PnL
# ============================================================

async def calculate_daily_pnl(
    db_type: str, target_date: date
) -> Dict[str, DailyPnL]:
    """
    计算指定日期的 PnL:
      - 已平仓盈亏: trade_records 中 exit_time=target_date 的记录
      - 未平仓浮动盈亏: positions 中 status=OPEN 的记录
      - 按 strategy 分组汇总
    """
    from sqlalchemy import text
    from core.db.session import get_session_maker
    from core.config.settings import get_settings

    log_info(f"计算 {target_date} 日的 PnL ...")
    Session = get_session_maker()

    settings = get_settings()
    initial_capital = settings.initial_capital

    by_strategy: Dict[str, DailyPnL] = {}

    async with Session() as session:
        # ---- 1. 已平仓交易(当日平仓) ----
        realized_rows = await session.execute(
            text("""
                SELECT
                    strategy,
                    COUNT(*) AS closed_count,
                    COALESCE(SUM(pnl), 0.0) AS realized_pnl
                FROM trade_records
                WHERE DATE(exit_time) = :target_date
                  AND status = 'closed'
                GROUP BY strategy
            """),
            {"target_date": target_date.isoformat()},
        )
        for row in realized_rows:
            name = row[0]
            if name not in by_strategy:
                by_strategy[name] = DailyPnL(strategy_name=name)
            by_strategy[name].daily_realized_pnl = float(row[2])
            by_strategy[name].trades_closed = int(row[1])

        realized_count = sum(p.trades_closed for p in by_strategy.values())

        # ---- 2. 当日新开仓交易 ----
        opened_rows = await session.execute(
            text("""
                SELECT
                    strategy,
                    COUNT(*) AS opened_count
                FROM trade_records
                WHERE DATE(entry_time) = :target_date
                GROUP BY strategy
            """),
            {"target_date": target_date.isoformat()},
        )
        for row in opened_rows:
            name = row[0]
            if name not in by_strategy:
                by_strategy[name] = DailyPnL(strategy_name=name)
            by_strategy[name].trades_opened = int(row[1])

        # ---- 3. 当前持仓(浮动盈亏) — 按 strategy 分组 ----
        pos_rows = await session.execute(
            text("""
                SELECT
                    COALESCE(strategy, '') AS strategy,
                    COUNT(*) AS pos_count,
                    COALESCE(SUM(quantity * current_price), 0.0) AS pos_value,
                    COALESCE(SUM(pnl), 0.0) AS unrealized_pnl
                FROM positions
                WHERE status = 'OPEN'
                GROUP BY strategy
            """)
        )
        global_pos_count = 0
        global_pos_value = 0.0
        global_unrealized_pnl = 0.0
        for row in pos_rows:
            sname = row[0] or "aggregate"
            pos_cnt = int(row[1])
            pos_val = float(row[2])
            unrealized = float(row[3])
            global_pos_count += pos_cnt
            global_pos_value += pos_val
            global_unrealized_pnl += unrealized
            if sname not in by_strategy:
                by_strategy[sname] = DailyPnL(strategy_name=sname)
            by_strategy[sname].positions_open = pos_cnt
            by_strategy[sname].position_value = round(pos_val, 2)
            by_strategy[sname].daily_unrealized_pnl = round(unrealized, 2)

        pos_count = global_pos_count

        # ---- 4. 历史累计 PnL (所有 closed 交易) ----
        total_rows = await session.execute(
            text("""
                SELECT
                    strategy,
                    COALESCE(SUM(pnl), 0.0) AS total_pnl
                FROM trade_records
                WHERE status = 'closed'
                GROUP BY strategy
            """)
        )
        for row in total_rows:
            name = row[0]
            if name not in by_strategy:
                by_strategy[name] = DailyPnL(strategy_name=name)
            by_strategy[name].total_pnl = float(row[1])

        # ---- 5. 回撤计算 ----
        # 查询最近 365 天的快照记录
        lookback_date = target_date - timedelta(days=365)
        snap_rows = await session.execute(
            text("""
                SELECT strategy_name, total_equity, snapshot_date
                FROM performance_snapshots
                WHERE snapshot_date >= :lookback
                ORDER BY strategy_name, snapshot_date ASC
            """),
            {"lookback": lookback_date.isoformat()},
        )
        equity_history: Dict[str, list] = {}
        for row in snap_rows:
            name, eq, snap_dt = row[0], float(row[1]), row[2]
            if name not in equity_history:
                equity_history[name] = []
            equity_history[name].append((snap_dt, eq))

        # 计算各策略的当前权益和回撤
        for name, dpnl in by_strategy.items():
            dpnl.total_equity = initial_capital + dpnl.total_pnl + dpnl.daily_unrealized_pnl
            dpnl.cash = dpnl.total_equity - dpnl.position_value

            # 回撤 = 从峰值下跌百分比
            hist = equity_history.get(name, [])
            if hist:
                peak = max(eq for _, eq in hist)
                dpnl.drawdown = round(
                    (peak - dpnl.total_equity) / peak * 100 if peak > 0 else 0.0, 4
                )

        # 如果没有策略记录 (空数据)，创建一个汇总
        if not by_strategy:
            # 尝试获取全局 PnL
            total_pnl_result = await session.execute(
                text("SELECT COALESCE(SUM(pnl), 0.0) FROM trade_records WHERE status = 'closed'")
            )
            global_total = float(total_pnl_result.scalar())
            total_equity = initial_capital + global_total

            by_strategy["aggregate"] = DailyPnL(
                strategy_name="aggregate",
                total_equity=total_equity,
                cash=total_equity,
                total_pnl=global_total,
                daily_unrealized_pnl=global_unrealized_pnl,
                positions_open=global_pos_count,
                position_value=global_pos_value,
            )

        log_ok(
            f"  → {len(by_strategy)} 个策略, "
            f"{realized_count} 笔平仓, {pos_count} 个持仓"
        )

    return by_strategy


# ============================================================
# 步骤 2: 写入 PerformanceSnapshot
# ============================================================

async def write_performance_snapshots(
    by_strategy: Dict[str, DailyPnL], target_date: date
) -> int:
    """将每日 PnL 写入 performance_snapshots 表"""
    from sqlalchemy import text
    from core.db.session import get_session_maker

    log_info("写入 performance_snapshots ...")
    Session = get_session_maker()

    written = 0
    async with Session() as session:
        async with session.begin():
            for name, dpnl in by_strategy.items():
                # 检查是否已存在当日记录
                existing = await session.execute(
                    text("""
                        SELECT id FROM performance_snapshots
                        WHERE DATE(snapshot_date) = :dt AND strategy_name = :name
                    """),
                    {"dt": target_date.isoformat(), "name": name},
                )
                if existing.first():
                    log_info(f"  {name} 当日快照已存在，跳过")
                    continue

                metrics = {
                    "realized_pnl": round(dpnl.daily_realized_pnl, 2),
                    "unrealized_pnl": round(dpnl.daily_unrealized_pnl, 2),
                    "trades_closed": dpnl.trades_closed,
                    "trades_opened": dpnl.trades_opened,
                    "positions_open": dpnl.positions_open,
                    "position_value": round(dpnl.position_value, 2),
                }

                snapshot_dt = datetime.combine(target_date, datetime.min.time())

                await session.execute(
                    text("""
                        INSERT INTO performance_snapshots
                            (snapshot_date, strategy_name, total_equity, cash,
                             positions_value, daily_pnl, total_pnl, drawdown, metrics)
                        VALUES
                            (:dt, :name, :equity, :cash, :pos_val,
                             :daily_pnl, :total_pnl, :drawdown, :metrics)
                    """),
                    {
                        "dt": snapshot_dt,
                        "name": name,
                        "equity": round(dpnl.total_equity, 2),
                        "cash": round(dpnl.cash, 2),
                        "pos_val": round(dpnl.position_value, 2),
                        "daily_pnl": round(
                            dpnl.daily_realized_pnl + dpnl.daily_unrealized_pnl, 2
                        ),
                        "total_pnl": round(dpnl.total_pnl, 2),
                        "drawdown": dpnl.drawdown,
                        "metrics": json.dumps(metrics),
                    },
                )
                written += 1

        log_ok(f"  → 写入 {written} 条快照记录")
    return written


# ============================================================
# 步骤 3: 清理过期信号
# ============================================================

async def cleanup_expired_signals(
    retention_days: int = 7, target_date: Optional[date] = None
) -> int:
    """
    删除 signals 表中超过 retention_days 天的旧记录。

    参数:
        retention_days: 信号保留天数 (默认 7)
        target_date: 基准日期 (默认今天)
    """
    from sqlalchemy import text
    from core.db.session import get_session_maker

    if target_date is None:
        target_date = date.today()

    cutoff = datetime.combine(
        target_date - timedelta(days=retention_days), datetime.min.time()
    )

    log_info(f"清理 {cutoff} 之前的过期信号 ...")
    Session = get_session_maker()

    deleted = 0
    async with Session() as session:
        async with session.begin():
            result = await session.execute(
                text("""
                    DELETE FROM signals
                    WHERE created_at < :cutoff
                """),
                {"cutoff": cutoff},
            )
            deleted = result.rowcount

    log_ok(f"  → 删除 {deleted} 条过期信号")
    return deleted


# ============================================================
# 步骤 4: ML 模型重训
# ============================================================

async def retrain_ml_models(
    force: bool = False, symbols: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    检查 ML 模型是否需要重训，并按需触发。

    如果 force=True 或距上次训练超过 ML_RETRAIN_INTERVAL_DAYS 天，则触发重训。

    尝试使用 Celery 异步任务; 如果 Celery 不可用，回退到同步训练。
    """
    from sqlalchemy import text
    from core.db.session import get_session_maker

    interval_days = int(os.getenv("ML_RETRAIN_INTERVAL_DAYS", "7"))
    log_info("ML 模型重训检查 ...")

    Session = get_session_maker()

    async with Session() as session:
        # 查询每个 ML 模型的最新训练时间
        result = await session.execute(
            text("""
                SELECT model_name, MAX(trained_at) AS last_train
                FROM model_versions
                WHERE is_active = true
                GROUP BY model_name
            """)
        )
        model_status: Dict[str, Any] = {row[0]: row[1] for row in result}

    # 决定哪些模型需要重训
    needs_retrain = []
    now = datetime.utcnow()

    if force:
        needs_retrain = list(model_status.keys()) if model_status else ["default"]
        log_info("  强制重训所有模型")
    else:
        for name, last_train in model_status.items():
            if last_train is None:
                needs_retrain.append(name)
            elif (now - last_train).days >= interval_days:
                needs_retrain.append(name)
        if not needs_retrain:
            log_info("  无需重训 (所有模型在间隔期内)")
            return {"retrained": False, "models": []}

    if not needs_retrain:
        needs_retrain = ["default"]

    log_info(f"  需要重训: {', '.join(needs_retrain)}")

    # 尝试 Celery 异步任务
    try:
        from tasks.training_tasks import train_pipeline, train_all_models

        if force:
            # 使用 Celery 异步分发
            symbols_to_train = symbols or ["SYNTHETIC"]
            for sym in symbols_to_train:
                train_all_models.delay(symbol=sym)
            log_ok(f"  Celery 任务已分发 ({len(symbols_to_train)} 个品种)")
            return {"retrained": True, "mode": "async_celery", "symbols": symbols_to_train}
        else:
            # 单模型异步重训
            for model_name in needs_retrain:
                train_pipeline.delay(symbol=model_name)
            log_ok(f"  Celery 任务已分发 ({len(needs_retrain)} 个模型)")
            return {"retrained": True, "mode": "async_celery", "models": needs_retrain}

    except Exception as e:
        log_warn(f"  Celery 不可用 ({e}), 回退到同步训练 ...")

    # 回退: 同步训练
    try:
        from ml.pipeline import MLPipeline
        import pandas as pd
        import numpy as np

        for model_name in needs_retrain:
            log_info(f"    同步训练: {model_name}")
            pipe = MLPipeline()
            # 生成模拟训练数据 (在没有真实数据时)
            np.random.seed(hash(f"train_{model_name}") % (2**31))
            dates = pd.date_range(end=now, periods=365)
            returns = np.random.normal(0.0005, 0.015, 365)
            close = 100.0 * np.exp(np.cumsum(returns))
            df = pd.DataFrame({"close": close, "volume": np.random.randint(10000, 1000000, 365)}, index=dates)
            result = await pipe.train(df, model_name)

            # 记录到 model_versions
            async with Session() as session:
                async with session.begin():
                    # 获取当前版本号
                    # 查询当前最大版本号 (兼容 PostgreSQL 和 SQLite)
                    ver_result = await session.execute(
                        text("""
                            SELECT COALESCE(MAX(CAST(version AS INTEGER)), 0) + 1
                            FROM model_versions
                            WHERE model_name = :name
                        """),
                        {"name": model_name},
                    )
                    new_version = str(ver_result.scalar())

                    # 取消旧版的 active 状态
                    await session.execute(
                        text("""
                            UPDATE model_versions
                            SET is_active = false
                            WHERE model_name = :name
                        """),
                        {"name": model_name},
                    )

                    # 写入新版本
                    await session.execute(
                        text("""
                            INSERT INTO model_versions
                                (model_name, version, description, metrics, is_active, trained_at)
                            VALUES
                                (:name, :ver, :desc, :metrics, true, :trained_at)
                        """),
                        {
                            "name": model_name,
                            "ver": new_version,
                            "desc": f"Auto-trained by daily_close ({now.strftime('%Y-%m-%d')})",
                            "metrics": json.dumps(result),
                            "trained_at": now,
                        },
                    )
            log_ok(f"    ✓ {model_name} v{new_version} 训练完成")

        return {"retrained": True, "mode": "sync", "models": needs_retrain}

    except Exception as e:
        log_error(f"  同步训练失败: {e}")
        return {"retrained": False, "error": str(e)}


# ============================================================
# 步骤 5: 生成收盘日报
# ============================================================

def generate_report(
    by_strategy: Dict[str, DailyPnL],
    target_date: date,
    cleanup_count: int = 0,
    retrain_result: Optional[Dict[str, Any]] = None,
) -> str:
    """生成收盘日报纯文本"""
    lines = []
    lines.append("=" * 62)
    lines.append(f"  收盘日报 — {target_date.isoformat()}")
    lines.append("=" * 62)
    lines.append("")

    if not by_strategy:
        lines.append("  [无交易数据]")
        lines.append("")
    else:
        # 汇总行
        total_realized = sum(p.daily_realized_pnl for p in by_strategy.values())
        total_unrealized = sum(p.daily_unrealized_pnl for p in by_strategy.values())
        total_daily_pnl = total_realized + total_unrealized
        total_trades = sum(p.trades_closed for p in by_strategy.values())
        open_positions = sum(p.positions_open for p in by_strategy.values())
        total_equity = max(p.total_equity for p in by_strategy.values())
        max_drawdown = max(p.drawdown for p in by_strategy.values())

        sign = "+" if total_daily_pnl >= 0 else ""
        lines.append(f"  📊 汇总")
        lines.append(f"     当日盈亏:      {sign}{total_daily_pnl:>10.2f}")
        lines.append(f"     已平仓盈亏:    {total_realized:>10.2f}")
        lines.append(f"     浮动盈亏:      {total_unrealized:>10.2f}")
        lines.append(f"     总权益:        {total_equity:>10.2f}")
        lines.append(f"     总回撤:        {max_drawdown:>8.2f}%")
        lines.append(f"     平仓笔数:      {total_trades}")
        lines.append(f"     持仓品种数:    {open_positions}")
        lines.append("")

        # 各策略详情
        lines.append(f"  📈 策略详情")
        lines.append(f"  {'策略名称':<20} {'当日盈亏':>10} {'总盈亏':>10} {'持仓':>6} {'回撤':>8}")
        lines.append(f"  {'-'*20} {'-'*10} {'-'*10} {'-'*6} {'-'*8}")
        for name in sorted(by_strategy.keys()):
            p = by_strategy[name]
            daily = p.daily_realized_pnl + p.daily_unrealized_pnl
            s = "+" if daily >= 0 else ""
            lines.append(
                f"  {name:<20} {s}{daily:>9.2f} "
                f"{p.total_pnl:>10.2f} {p.positions_open:>4}  {p.drawdown:>7.2f}%"
            )
        lines.append("")

    # 清理信息
    if cleanup_count > 0:
        lines.append(f"  🧹 信号清理: 删除 {cleanup_count} 条过期信号")
    else:
        lines.append(f"  🧹 信号清理: 无过期信号")
    lines.append("")

    # ML 重训信息
    if retrain_result:
        if retrain_result.get("retrained"):
            mode = retrain_result.get("mode", "unknown")
            models = retrain_result.get("models", [])
            lines.append(f"  🤖 ML 重训: 已触发 ({mode})")
            if models:
                lines.append(f"     模型: {', '.join(models)}")
        else:
            err = retrain_result.get("error", "未知错误")
            lines.append(f"  ❌ ML 重训失败: {err}")
    else:
        lines.append(f"  🤖 ML 重训: 跳过")

    lines.append("")
    lines.append("=" * 62)
    return "\n".join(lines)


# ============================================================
# 主流程
# ============================================================

async def run_daily_close(args: argparse.Namespace) -> int:
    """执行收盘后处理主流程"""
    db_type = args.db
    pnl_only = args.pnl_only
    cleanup_only = args.cleanup_only
    do_retrain = args.retrain
    do_report = not (pnl_only or cleanup_only) or args.report

    # 确定处理日期
    if args.date:
        target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    else:
        target_date = date.today() - timedelta(days=1)

    signal_retention = int(os.getenv("SIGNAL_RETENTION_DAYS", "7"))

    print(f"""
{_color('╔═══════════════════════════════════════════════════╗', _CYAN)}
{_color('║     Trading Strategy Center — 收盘后处理           ║', _CYAN)}
{_color('╚═══════════════════════════════════════════════════╝', _CYAN)}
    """)
    log_info(f"处理日期: {target_date}")
    log_info(f"数据库类型: {db_type.upper()}")
    print()

    # ---- Step 1: PnL 计算 + 快照写入 ----
    if not cleanup_only:
        log_info("步骤 1/4: PnL 计算")
        try:
            by_strategy = await calculate_daily_pnl(db_type, target_date)
            if not by_strategy:
                log_warn("  无交易数据")
            print()

            log_info("步骤 2/4: 写入 PerformanceSnapshot")
            try:
                await write_performance_snapshots(by_strategy, target_date)
            except Exception as e:
                log_error(f"写入快照失败: {e}")
            print()
        except Exception as e:
            log_error(f"PnL 计算失败: {e}")
            by_strategy = {}
            print()
    else:
        by_strategy = {}

    # ---- Step 2: 清理过期信号 ----
    if not pnl_only:
        log_info("步骤 3/4: 清理过期信号")
        try:
            cleanup_count = await cleanup_expired_signals(
                retention_days=signal_retention, target_date=target_date
            )
        except Exception as e:
            log_error(f"信号清理失败: {e}")
            cleanup_count = 0
        print()
    else:
        cleanup_count = 0

    # ---- Step 3: ML 重训 ----
    if do_retrain or (not pnl_only and not cleanup_only):
        log_info("步骤 4/4: ML 模型重训")
        try:
            retrain_result = await retrain_ml_models(force=do_retrain)
        except Exception as e:
            log_error(f"ML 重训失败: {e}")
            retrain_result = {"retrained": False, "error": str(e)}
        print()
    else:
        retrain_result = None

    # ---- Step 4: 日报 ----
    if do_report:
        report = generate_report(by_strategy, target_date, cleanup_count, retrain_result)
        print()
        print(report)
        print()

        # 写入日志文件
        log_dir = project_root / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        report_path = log_dir / f"daily_report_{target_date.isoformat()}.txt"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        log_ok(f"日报已保存: {report_path}")

    # ---- 完成 ----
    print(f"""
{_color('╔═══════════════════════════════════════════════════╗', _GREEN)}
{_color('║     收盘后处理完成！                              ║', _GREEN)}
{_color('╚═══════════════════════════════════════════════════╝', _GREEN)}
    """)

    return 0


# ============================================================
# CLI 入口
# ============================================================

def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """
    解析命令行参数。

    Args:
        argv: 参数列表 (用于测试)。为 None 时使用 sys.argv。
    """
    parser = argparse.ArgumentParser(
        description="Trading Strategy Center — 收盘后处理工具"
    )
    parser.add_argument(
        "--db", choices=["sqlite", "postgresql"], default="sqlite",
        help="数据库类型 (默认: sqlite)"
    )
    parser.add_argument(
        "--date", type=str, default=None,
        help="处理日期 YYYY-MM-DD (默认: 昨天)"
    )
    parser.add_argument(
        "--pnl-only", action="store_true",
        help="仅计算 PnL 并写入快照"
    )
    parser.add_argument(
        "--cleanup-only", action="store_true",
        help="仅清理过期信号"
    )
    parser.add_argument(
        "--retrain", action="store_true",
        help="强制触发 ML 模型重训"
    )
    parser.add_argument(
        "--report", action="store_true",
        help="生成日报 (默认自动)"
    )
    return parser.parse_args(argv)


def main():
    # 配置日志
    os.environ.setdefault("SQLALCHEMY_SILENCE_UBER_WARNING", "1")

    args = parse_args()
    exit_code = asyncio.run(run_daily_close(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
