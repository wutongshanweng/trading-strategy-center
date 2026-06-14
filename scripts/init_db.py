#!/usr/bin/env python3
"""
Trading Strategy Center — 数据库初始化脚本
==========================================

功能:
  1. 创建数据库（PostgreSQL 或 SQLite）
  2. 运行 Alembic 迁移（创建所有表结构）
  3. 写入种子数据（品种合约、默认配置等）
  4. 验证表结构完整性

用法:
  # 本地开发 (SQLite):
  python scripts/init_db.py --db sqlite

  # 生产部署 (PostgreSQL):
  python scripts/init_db.py --db postgresql

  # 仅运行迁移（表已存在时）:
  python scripts/init_db.py --migrate-only

  # 仅写入种子数据:
  python scripts/init_db.py --seed-only

环境变量:
  DB_HOST, DB_PORT, DB_USER, DB_PASS, DB_NAME — PostgreSQL 连接参数
  详情见 .env 文件
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# 将项目根目录加入 sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))


# ============================================================
# 种子数据 — 品种合约
# ============================================================
SEED_CONTRACTS = [
    # ===== 上海期货交易所 (SHFE) =====
    {"symbol": "CU", "name": "沪铜", "exchange": "SHFE", "category": "metal",
     "multiplier": 5, "min_tick": 10.0, "margin_rate": 0.12, "commission": 0.00005,
     "delivery_months": "1,2,3,4,5,6,7,8,9,10,11,12"},
    {"symbol": "AL", "name": "沪铝", "exchange": "SHFE", "category": "metal",
     "multiplier": 5, "min_tick": 5.0, "margin_rate": 0.10, "commission": 3.0,
     "delivery_months": "1,2,3,4,5,6,7,8,9,10,11,12"},
    {"symbol": "ZN", "name": "沪锌", "exchange": "SHFE", "category": "metal",
     "multiplier": 5, "min_tick": 5.0, "margin_rate": 0.10, "commission": 3.0,
     "delivery_months": "1,2,3,4,5,6,7,8,9,10,11,12"},
    {"symbol": "PB", "name": "沪铅", "exchange": "SHFE", "category": "metal",
     "multiplier": 5, "min_tick": 5.0, "margin_rate": 0.10, "commission": 0.00004,
     "delivery_months": "1,2,3,4,5,6,7,8,9,10,11,12"},
    {"symbol": "NI", "name": "沪镍", "exchange": "SHFE", "category": "metal",
     "multiplier": 1, "min_tick": 10.0, "margin_rate": 0.12, "commission": 3.0,
     "delivery_months": "1,2,3,4,5,6,7,8,9,10,11,12"},
    {"symbol": "SN", "name": "沪锡", "exchange": "SHFE", "category": "metal",
     "multiplier": 1, "min_tick": 10.0, "margin_rate": 0.12, "commission": 3.0,
     "delivery_months": "1,2,3,4,5,6,7,8,9,10,11,12"},
    {"symbol": "AU", "name": "黄金", "exchange": "SHFE", "category": "metal",
     "multiplier": 1000, "min_tick": 0.02, "margin_rate": 0.08, "commission": 10.0,
     "delivery_months": "1,2,3,4,5,6,7,8,9,10,11,12"},
    {"symbol": "AG", "name": "白银", "exchange": "SHFE", "category": "metal",
     "multiplier": 15, "min_tick": 1.0, "margin_rate": 0.10, "commission": 0.00005,
     "delivery_months": "1,2,3,4,5,6,7,8,9,10,11,12"},
    {"symbol": "RB", "name": "螺纹钢", "exchange": "SHFE", "category": "metal",
     "multiplier": 10, "min_tick": 1.0, "margin_rate": 0.10, "commission": 0.0001,
     "delivery_months": "1,2,3,4,5,6,7,8,9,10,11,12"},
    {"symbol": "HC", "name": "热轧卷板", "exchange": "SHFE", "category": "metal",
     "multiplier": 10, "min_tick": 1.0, "margin_rate": 0.10, "commission": 0.0001,
     "delivery_months": "1,2,3,4,5,6,7,8,9,10,11,12"},
    {"symbol": "RU", "name": "天然橡胶", "exchange": "SHFE", "category": "chemical",
     "multiplier": 10, "min_tick": 5.0, "margin_rate": 0.10, "commission": 3.0,
     "delivery_months": "1,3,4,5,6,7,8,9,10,11"},
    {"symbol": "FU", "name": "燃料油", "exchange": "SHFE", "category": "energy",
     "multiplier": 10, "min_tick": 1.0, "margin_rate": 0.15, "commission": 0.00005,
     "delivery_months": "1,2,3,4,5,6,7,8,9,10,11,12"},
    {"symbol": "BU", "name": "沥青", "exchange": "SHFE", "category": "energy",
     "multiplier": 10, "min_tick": 2.0, "margin_rate": 0.10, "commission": 0.0001,
     "delivery_months": "1,2,3,4,5,6,7,8,9,10,11,12"},

    # ===== 大连商品交易所 (DCE) =====
    {"symbol": "C", "name": "玉米", "exchange": "DCE", "category": "agri",
     "multiplier": 10, "min_tick": 1.0, "margin_rate": 0.08, "commission": 1.2,
     "delivery_months": "1,3,5,7,9,11"},
    {"symbol": "CS", "name": "玉米淀粉", "exchange": "DCE", "category": "agri",
     "multiplier": 10, "min_tick": 1.0, "margin_rate": 0.08, "commission": 1.5,
     "delivery_months": "1,3,5,7,9,11"},
    {"symbol": "A", "name": "豆一", "exchange": "DCE", "category": "agri",
     "multiplier": 10, "min_tick": 1.0, "margin_rate": 0.10, "commission": 2.0,
     "delivery_months": "1,3,5,7,9,11"},
    {"symbol": "B", "name": "豆二", "exchange": "DCE", "category": "agri",
     "multiplier": 10, "min_tick": 1.0, "margin_rate": 0.10, "commission": 1.0,
     "delivery_months": "1,3,5,7,9,11"},
    {"symbol": "M", "name": "豆粕", "exchange": "DCE", "category": "agri",
     "multiplier": 10, "min_tick": 1.0, "margin_rate": 0.08, "commission": 1.5,
     "delivery_months": "1,3,5,7,9,11"},
    {"symbol": "Y", "name": "豆油", "exchange": "DCE", "category": "agri",
     "multiplier": 10, "min_tick": 2.0, "margin_rate": 0.08, "commission": 2.5,
     "delivery_months": "1,3,5,7,9,11"},
    {"symbol": "P", "name": "棕榈油", "exchange": "DCE", "category": "agri",
     "multiplier": 10, "min_tick": 2.0, "margin_rate": 0.08, "commission": 2.5,
     "delivery_months": "1,3,5,7,9,11"},
    {"symbol": "I", "name": "铁矿石", "exchange": "DCE", "category": "metal",
     "multiplier": 100, "min_tick": 0.5, "margin_rate": 0.12, "commission": 0.0001,
     "delivery_months": "1,2,3,4,5,6,7,8,9,10,11,12"},
    {"symbol": "J", "name": "焦炭", "exchange": "DCE", "category": "energy",
     "multiplier": 100, "min_tick": 0.5, "margin_rate": 0.20, "commission": 0.0001,
     "delivery_months": "1,2,3,4,5,6,7,8,9,10,11,12"},
    {"symbol": "JM", "name": "焦煤", "exchange": "DCE", "category": "energy",
     "multiplier": 60, "min_tick": 0.5, "margin_rate": 0.20, "commission": 0.0001,
     "delivery_months": "1,2,3,4,5,6,7,8,9,10,11,12"},
    {"symbol": "L", "name": "聚乙烯(LLDPE)", "exchange": "DCE", "category": "chemical",
     "multiplier": 5, "min_tick": 1.0, "margin_rate": 0.10, "commission": 1.0,
     "delivery_months": "1,2,3,4,5,6,7,8,9,10,11,12"},
    {"symbol": "PP", "name": "聚丙烯", "exchange": "DCE", "category": "chemical",
     "multiplier": 5, "min_tick": 1.0, "margin_rate": 0.10, "commission": 1.0,
     "delivery_months": "1,2,3,4,5,6,7,8,9,10,11,12"},
    {"symbol": "V", "name": "聚氯乙烯(PVC)", "exchange": "DCE", "category": "chemical",
     "multiplier": 5, "min_tick": 1.0, "margin_rate": 0.10, "commission": 1.0,
     "delivery_months": "1,2,3,4,5,6,7,8,9,10,11,12"},
    {"symbol": "EG", "name": "乙二醇", "exchange": "DCE", "category": "chemical",
     "multiplier": 10, "min_tick": 1.0, "margin_rate": 0.10, "commission": 3.0,
     "delivery_months": "1,2,3,4,5,6,7,8,9,10,11,12"},

    # ===== 郑州商品交易所 (CZCE) =====
    {"symbol": "TA", "name": "PTA", "exchange": "CZCE", "category": "chemical",
     "multiplier": 5, "min_tick": 2.0, "margin_rate": 0.08, "commission": 3.0,
     "delivery_months": "1,2,3,4,5,6,7,8,9,10,11,12"},
    {"symbol": "MA", "name": "甲醇", "exchange": "CZCE", "category": "chemical",
     "multiplier": 10, "min_tick": 1.0, "margin_rate": 0.10, "commission": 2.0,
     "delivery_months": "1,2,3,4,5,6,7,8,9,10,11,12"},
    {"symbol": "RM", "name": "菜籽粕", "exchange": "CZCE", "category": "agri",
     "multiplier": 10, "min_tick": 1.0, "margin_rate": 0.08, "commission": 1.5,
     "delivery_months": "1,3,5,7,9,11"},
    {"symbol": "OI", "name": "菜籽油", "exchange": "CZCE", "category": "agri",
     "multiplier": 10, "min_tick": 1.0, "margin_rate": 0.08, "commission": 2.0,
     "delivery_months": "1,3,5,7,9,11"},
    {"symbol": "SR", "name": "白糖", "exchange": "CZCE", "category": "agri",
     "multiplier": 10, "min_tick": 1.0, "margin_rate": 0.08, "commission": 3.0,
     "delivery_months": "1,3,5,7,9,11"},
    {"symbol": "CF", "name": "棉花", "exchange": "CZCE", "category": "agri",
     "multiplier": 5, "min_tick": 5.0, "margin_rate": 0.08, "commission": 4.3,
     "delivery_months": "1,3,5,7,9,11"},
    {"symbol": "FG", "name": "玻璃", "exchange": "CZCE", "category": "chemical",
     "multiplier": 20, "min_tick": 1.0, "margin_rate": 0.10, "commission": 3.0,
     "delivery_months": "1,2,3,4,5,6,7,8,9,10,11,12"},
    {"symbol": "ZC", "name": "动力煤", "exchange": "CZCE", "category": "energy",
     "multiplier": 100, "min_tick": 0.2, "margin_rate": 0.20, "commission": 4.0,
     "delivery_months": "1,2,3,4,5,6,7,8,9,10,11,12"},
    {"symbol": "AP", "name": "苹果", "exchange": "CZCE", "category": "agri",
     "multiplier": 10, "min_tick": 1.0, "margin_rate": 0.10, "commission": 5.0,
     "delivery_months": "1,3,5,7,10,11,12"},

    # ===== 中国金融期货交易所 (CFFEX) =====
    {"symbol": "IF", "name": "沪深300股指期货", "exchange": "CFFEX", "category": "equity",
     "multiplier": 300, "min_tick": 0.2, "margin_rate": 0.12, "commission": 0.000023,
     "delivery_months": "当月,下月,随后两个季月"},
    {"symbol": "IH", "name": "上证50股指期货", "exchange": "CFFEX", "category": "equity",
     "multiplier": 300, "min_tick": 0.2, "margin_rate": 0.12, "commission": 0.000023,
     "delivery_months": "当月,下月,随后两个季月"},
    {"symbol": "IC", "name": "中证500股指期货", "exchange": "CFFEX", "category": "equity",
     "multiplier": 200, "min_tick": 0.2, "margin_rate": 0.14, "commission": 0.000023,
     "delivery_months": "当月,下月,随后两个季月"},
    {"symbol": "T", "name": "10年期国债期货", "exchange": "CFFEX", "category": "rate",
     "multiplier": 10000, "min_tick": 0.005, "margin_rate": 0.02, "commission": 3.0,
     "delivery_months": "3,6,9,12"},
    {"symbol": "TF", "name": "5年期国债期货", "exchange": "CFFEX", "category": "rate",
     "multiplier": 10000, "min_tick": 0.005, "margin_rate": 0.012, "commission": 3.0,
     "delivery_months": "3,6,9,12"},
    {"symbol": "TS", "name": "2年期国债期货", "exchange": "CFFEX", "category": "rate",
     "multiplier": 20000, "min_tick": 0.005, "margin_rate": 0.005, "commission": 3.0,
     "delivery_months": "3,6,9,12"},

    # ===== 上海国际能源交易中心 (INE) =====
    {"symbol": "SC", "name": "原油", "exchange": "INE", "category": "energy",
     "multiplier": 1000, "min_tick": 0.1, "margin_rate": 0.10, "commission": 20.0,
     "delivery_months": "1,2,3,4,5,6,7,8,9,10,11,12"},
    {"symbol": "NR", "name": "20号胶", "exchange": "INE", "category": "chemical",
     "multiplier": 10, "min_tick": 5.0, "margin_rate": 0.10, "commission": 3.0,
     "delivery_months": "1,2,3,4,5,6,7,8,9,10,11,12"},

    # ===== 广州期货交易所 (GFEX) =====
    {"symbol": "SI", "name": "工业硅", "exchange": "GFEX", "category": "metal",
     "multiplier": 5, "min_tick": 5.0, "margin_rate": 0.10, "commission": 0.0001,
     "delivery_months": "1,2,3,4,5,6,7,8,9,10,11,12"},
    {"symbol": "LC", "name": "碳酸锂", "exchange": "GFEX", "category": "metal",
     "multiplier": 1, "min_tick": 50.0, "margin_rate": 0.12, "commission": 0.0001,
     "delivery_months": "1,2,3,4,5,6,7,8,9,10,11,12"},
]


# ============================================================
# 种子数据 — 监控规则 (默认)
# ============================================================
SEED_MONITOR_RULES = [
    {"name": "最大回撤告警", "rule_type": "drawdown", "params": {"threshold": 0.10},
     "level": "WARNING", "enabled": True},
    {"name": "VaR 风险告警", "rule_type": "var", "params": {"alpha": 0.05, "threshold": 0.02},
     "level": "CRITICAL", "enabled": True},
    {"name": "成交量异常监控", "rule_type": "volume", "params": {"zscore_threshold": 3.0},
     "level": "WARNING", "enabled": True},
    {"name": "信号频率监控", "rule_type": "signal", "params": {"max_signals_per_hour": 10},
     "level": "INFO", "enabled": True},
    {"name": "极端波动预警", "rule_type": "drawdown", "params": {"threshold": 0.20},
     "level": "EMERGENCY", "enabled": True},
]


# ============================================================
# 种子数据 — 默认策略参数
# ============================================================
SEED_STRATEGY_PARAMS = {
    "strategy_name": "default_trend",
    "version": 1,
    "params": {
        "ema_fast": 9,
        "ema_slow": 26,
        "atr_period": 14,
        "atr_multiplier": 2.0,
        "rsi_period": 14,
        "rsi_overbought": 70,
        "rsi_oversold": 30,
        "bollinger_period": 20,
        "bollinger_std": 2.0,
    },
    "score": 0.0,
    "timestamp": 0.0
}


# ============================================================
# 数据库初始化逻辑
# ============================================================

def color(text: str, code: str) -> str:
    """终端颜色辅助函数 (仅使用 ASCII 字符, 兼容 Windows GBK)"""
    colors = {
        "green": "\033[92m",
        "yellow": "\033[93m",
        "red": "\033[91m",
        "cyan": "\033[96m",
        "reset": "\033[0m",
    }
    return f"{colors.get(code, '')}{text}{colors['reset']}"


def log_info(msg: str):
    print(f"  {color('[>]', 'cyan')} {msg}")


def log_ok(msg: str):
    print(f"  {color('[OK]', 'green')} {msg}")


def log_warn(msg: str):
    print(f"  {color('[!]', 'yellow')} {msg}")


def log_error(msg: str):
    print(f"  {color('[X]', 'red')} {msg}")


async def create_database_if_not_exists(db_type: str) -> bool:
    """
    检查并创建数据库 (仅 PostgreSQL).

    SQLite 会自动创建 .db 文件, 无需此步骤.
    """
    if db_type != "postgresql":
        return True

    try:
        import asyncpg

        host = os.getenv("DB_HOST", "localhost")
        port = int(os.getenv("DB_PORT", "5432"))
        user = os.getenv("DB_USER", "trading")
        password = os.getenv("DB_PASS", "trading_pass")
        dbname = os.getenv("DB_NAME", "trading_strategy_center")

        # 连接到默认 postgres 数据库
        conn = await asyncpg.connect(
            host=host, port=port, user=user, password=password, database="postgres"
        )
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", dbname
        )
        if not exists:
            await conn.execute(f'CREATE DATABASE "{dbname}"')
            log_ok(f"数据库 '{dbname}' 已创建")
        else:
            log_info(f"数据库 '{dbname}' 已存在，跳过创建")
        await conn.close()
        return True
    except Exception as e:
        log_error(f"无法连接 PostgreSQL: {e}")
        log_info("请确保 PostgreSQL 已启动并且连接参数正确")
        log_info(f"  DB_HOST={os.getenv('DB_HOST', 'localhost')}")
        log_info(f"  DB_PORT={os.getenv('DB_PORT', '5432')}")
        log_info(f"  DB_USER={os.getenv('DB_USER', 'trading')}")
        return False


def run_migrations_sync(db_type: str) -> bool:
    """
    运行 Alembic 迁移 (同步子进程方式, 避免 asyncio.run() 嵌套问题).

    Alembic 的 env.py 使用 asyncio.run(), 在异步上下文中会报错.
    改用 subprocess 调用 alembic 命令行.
    """
    log_info("运行数据库迁移...")

    # 如果是 SQLite, 设置 SQLALCHEMY_SILENCE_UBER_WARNING
    if db_type == "sqlite":
        os.environ["SQLALCHEMY_SILENCE_UBER_WARNING"] = "1"

    try:
        env = os.environ.copy()
        # 移除可能干扰的 PYTHONPATH (防止重复导入)
        env.pop("PYTHONPATH", None)

        if db_type == "sqlite":
            db_path = project_root / "data" / "futures.db"
            (project_root / "data").mkdir(parents=True, exist_ok=True)
            sqlite_url = f"sqlite+aiosqlite:///{db_path}"
            env["SQLALCHEMY_URL"] = sqlite_url
            log_info(f"SQLite 数据库路径: {db_path}")

        # 通过子进程运行 alembic
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "--config", str(project_root / "alembic.ini"), "upgrade", "head"],
            capture_output=True, text=True, cwd=project_root, env=env,
        )

        if result.returncode != 0:
            log_error(f"迁移命令失败 (code={result.returncode})")
            if result.stderr:
                for line in result.stderr.strip().split("\n"):
                    log_error(f"  {line}")
            return False

        if result.stdout:
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    log_info(f"  {line}")

        log_ok("数据库迁移完成，所有表已创建")
        return True
    except Exception as e:
        log_error(f"迁移失败: {e}")
        return False


async def seed_contracts(db_type: str) -> bool:
    """写入品种合约种子数据"""
    log_info("写入品种合约数据...")
    try:
        from sqlalchemy import text
        from core.db.session import get_engine

        engine = get_engine()
        async with engine.begin() as conn:
            # 检查是否已有数据
            result = await conn.execute(text("SELECT COUNT(*) FROM contracts"))
            count = result.scalar()
            if count and count > 0:
                log_info(f"品种合约表已有 {count} 条记录，跳过写入")
                return True

            for contract in SEED_CONTRACTS:
                await conn.execute(
                    text("""
                        INSERT INTO contracts
                            (symbol, name, exchange, category, multiplier, min_tick,
                             margin_rate, commission, is_active, delivery_months)
                        VALUES
                            (:symbol, :name, :exchange, :category, :multiplier, :min_tick,
                             :margin_rate, :commission, :is_active, :delivery_months)
                        ON CONFLICT (symbol) DO NOTHING
                    """),
                    {
                        "symbol": contract["symbol"],
                        "name": contract["name"],
                        "exchange": contract["exchange"],
                        "category": contract["category"],
                        "multiplier": contract["multiplier"],
                        "min_tick": contract["min_tick"],
                        "margin_rate": contract["margin_rate"],
                        "commission": contract["commission"],
                        "is_active": True,
                        "delivery_months": contract.get("delivery_months"),
                    },
                )
            log_ok(f"已写入 {len(SEED_CONTRACTS)} 个品种合约")
        return True
    except Exception as e:
        log_error(f"写入品种合约失败: {e}")
        return False


async def seed_monitor_rules(db_type: str) -> bool:
    """写入默认监控规则"""
    log_info("写入默认监控规则...")
    try:
        from sqlalchemy import text
        from core.db.session import get_engine

        engine = get_engine()
        async with engine.begin() as conn:
            # 检查是否已有数据
            result = await conn.execute(text("SELECT COUNT(*) FROM monitor_rules"))
            count = result.scalar()
            if count and count > 0:
                log_info(f"监控规则表已有 {count} 条记录，跳过写入")
                return True

            for rule in SEED_MONITOR_RULES:
                rule_data = dict(rule)
                rule_data["params"] = json.dumps(rule["params"])
                await conn.execute(
                    text("""
                        INSERT INTO monitor_rules
                            (name, rule_type, params, level, enabled)
                        VALUES
                            (:name, :rule_type, :params, :level, :enabled)
                    """),
                    rule_data,
                )
            log_ok(f"已写入 {len(SEED_MONITOR_RULES)} 条默认监控规则")
        return True
    except Exception as e:
        log_error(f"写入监控规则失败: {e}")
        return False


async def seed_strategy_params(db_type: str) -> bool:
    """写入默认策略参数"""
    log_info("写入默认策略参数...")
    try:
        from sqlalchemy import text
        from core.db.session import get_engine

        engine = get_engine()
        async with engine.begin() as conn:
            # 检查是否已有数据
            result = await conn.execute(text("SELECT COUNT(*) FROM parameter_versions"))
            count = result.scalar()
            if count and count > 0:
                log_info(f"策略参数表已有 {count} 条记录，跳过写入")
                return True

            params = dict(SEED_STRATEGY_PARAMS)
            params["timestamp"] = time.time()
            params["params"] = json.dumps(params["params"])

            await conn.execute(
                text("""
                    INSERT INTO parameter_versions
                        (strategy_name, version, params, score, timestamp)
                    VALUES
                        (:strategy_name, :version, :params, :score, :timestamp)
                """),
                params,
            )
            log_ok("已写入默认策略参数")
        return True
    except Exception as e:
        log_error(f"写入策略参数失败: {e}")
        return False


async def verify_tables() -> bool:
    """验证所有预期的表是否已创建"""
    expected_tables = [
        "contracts", "klines", "signals", "parameter_versions",
        "positions", "trade_records", "backtest_results",
        "performance_snapshots", "model_versions",
        "tournament_strategies", "tournament_records",
        "monitor_rules", "monitor_alerts",
    ]

    log_info("验证表结构完整性...")
    try:
        from sqlalchemy import text
        from core.db.session import get_engine

        engine = get_engine()
        async with engine.connect() as conn:
            # PostgreSQL / SQLite 兼容的表名查询
            result = await conn.execute(
                text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
                if engine.dialect.name == "postgresql"
                else text("SELECT name FROM sqlite_master WHERE type='table'")
            )
            actual_tables = {row[0].lower() for row in result.fetchall()
                            if not row[0].startswith("alembic_")}

        missing = [t for t in expected_tables if t not in actual_tables]
        if missing:
            log_warn(f"缺少表: {', '.join(missing)}")
            return False

        log_ok(f"全部 {len(expected_tables)} 个表已就绪")
        return True
    except Exception as e:
        log_error(f"验证失败: {e}")
        return False


async def init_database(args: argparse.Namespace) -> int:
    """主初始化流程"""
    db_type = args.db

    print(f"""
{color('╔═══════════════════════════════════════════════════╗', 'cyan')}
{color('║     Trading Strategy Center — 数据库初始化          ║', 'cyan')}
{color('╚═══════════════════════════════════════════════════╝', 'cyan')}
    """)

    if db_type not in ("sqlite", "postgresql"):
        log_error(f"不支持的数据库类型: {db_type}，请使用 sqlite 或 postgresql")
        return 1

    log_info(f"数据库类型: {db_type.upper()}")

    # Step 1: 创建数据库
    if not args.migrate_only and not args.seed_only:
        if not await create_database_if_not_exists(db_type):
            return 1
        print()

    # Step 2: 运行迁移 (同步子进程, 避免 Alembic + asyncio 冲突)
    if not args.seed_only:
        # run_migrations_sync 是同步函数, 需要在事件循环外运行
        # 使用 asyncio.to_thread 避免阻塞
        if not await asyncio.to_thread(run_migrations_sync, db_type):
            return 1
        print()

    # Step 3: 验证表结构
    if not args.seed_only:
        if not await verify_tables():
            log_warn("部分表未创建，请检查迁移日志")
        print()

    # Step 4: 写入种子数据
    if not args.migrate_only:
        log_info("写入种子数据...")
        await seed_contracts(db_type)
        await seed_monitor_rules(db_type)
        await seed_strategy_params(db_type)
        print()

    # 完成
    print(f"""
{color('╔═══════════════════════════════════════════════════╗', 'green')}
{color('║     数据库初始化完成！                              ║', 'green')}
{color('╚═══════════════════════════════════════════════════╝', 'green')}

  {color('[>]', 'cyan')} 表数量: {color('13', 'green')}
  {color('[>]', 'cyan')} 品种合约: {color(f'{len(SEED_CONTRACTS)}', 'green')} 个
  {color('[>]', 'cyan')} 监控规则: {color(f'{len(SEED_MONITOR_RULES)}', 'green')} 条

  {color('后续操作:', 'yellow')}
    启动服务:  {color('uvicorn main:app --reload --port 8000', 'cyan')}
    回滚迁移:  {color('alembic downgrade -1', 'cyan')}
    查看状态:  {color('alembic current', 'cyan')}
    """)

    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Trading Strategy Center — 数据库初始化工具"
    )
    parser.add_argument(
        "--db", choices=["sqlite", "postgresql"], default="sqlite",
        help="数据库类型 (默认: sqlite)"
    )
    parser.add_argument(
        "--migrate-only", action="store_true",
        help="仅运行迁移，不写入种子数据"
    )
    parser.add_argument(
        "--seed-only", action="store_true",
        help="仅写入种子数据，不运行迁移"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # 设置数据库 URL 覆盖，确保 seed 函数使用正确的数据库引擎
    if args.db == "sqlite":
        db_path = project_root / "data" / "futures.db"
        (project_root / "data").mkdir(parents=True, exist_ok=True)
        sqlite_url = f"sqlite+aiosqlite:///{db_path}"
        os.environ["DB_URL_OVERRIDE"] = sqlite_url
        os.environ["SQLALCHEMY_SILENCE_UBER_WARNING"] = "1"

    exit_code = asyncio.run(init_database(args))

    # 清理环境变量
    os.environ.pop("DB_URL_OVERRIDE", None)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
