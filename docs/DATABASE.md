# 数据库设计文档

> 版本: v1.0  
> 更新时间: 2026-06-13  
> 数据库: PostgreSQL 16 (生产) / SQLite (开发)

---

## 目录

1. [概述](#1-概述)
2. [表结构总览](#2-表结构总览)
3. [核心数据表](#3-核心数据表)
4. [策略与信号表](#4-策略与信号表)
5. [交易与持仓表](#5-交易与持仓表)
6. [回测与表现表](#6-回测与表现表)
7. [ML 模型表](#7-ml-模型表)
8. [锦标赛表](#8-锦标赛表)
9. [监控告警表](#9-监控告警表)
10. [ER 关系图](#10-er-关系图)
11. [迁移指南](#11-迁移指南)
12. [运维命令](#12-运维命令)
13. [常见问题](#13-常见问题)

---

## 1. 概述

### 1.1 设计原则

- **规范化到 3NF**：减少数据冗余，保证数据一致性
- **异步驱动**: 使用 `sqlalchemy[asyncio]` + `asyncpg`，所有数据库操作均为异步
- **迁移管理**: 使用 Alembic 管理 Schema 版本，支持自动生成迁移
- **种子数据**: 预置品种合约、监控规则、默认策略参数

### 1.2 技术栈

| 组件 | 开发环境 | 生产环境 |
|------|---------|---------|
| 数据库引擎 | SQLite + aiosqlite | PostgreSQL 16 + asyncpg |
| ORM | SQLAlchemy 2.0 (Declarative) | SQLAlchemy 2.0 |
| 迁移工具 | Alembic 1.13+ | Alembic 1.13+ |
| 连接池 | 无 (SQLite 线程安全) | asyncpg pool (5-20 连接) |

### 1.3 数据库连接

```python
# 配置位置: core/config/settings.py
@property
def db_url(self) -> str:
    return f"postgresql+asyncpg://{self.db_user}:{self.db_pass}@{self.db_host}:{self.db_port}/{self.db_name}"

# 开发环境 SQLite 替代:
# sqlite+aiosqlite:///data/futures.db
```

### 1.4 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DB_HOST` | `localhost` | 数据库主机 |
| `DB_PORT` | `5432` | 数据库端口 |
| `DB_USER` | `trading` | 数据库用户 |
| `DB_PASS` | `trading_pass` | 数据库密码 |
| `DB_NAME` | `trading_strategy_center` | 数据库名称 |

---

## 2. 表结构总览

系统共包含 **13 张数据表**，按功能分为 6 组：

| 分组 | 表名 | 说明 | 行数预估 |
|------|------|------|---------|
| **核心数据** | `contracts` | 品种合约信息 | 50+ |
| | `klines` | K 线数据 | 数亿 |
| **策略与信号** | `signals` | 交易信号 | 百万级 |
| | `parameter_versions` | 策略参数版本 | 千级 |
| **交易与持仓** | `positions` | 持仓记录 | 百级 |
| | `trade_records` | 成交记录 | 万级 |
| **回测与表现** | `backtest_results` | 回测结果 | 千级 |
| | `performance_snapshots` | 每日表现快照 | 万级 |
| **ML 模型** | `model_versions` | ML 模型版本管理 | 百级 |
| **锦标赛** | `tournament_strategies` | 参赛策略注册 | 千级 |
| | `tournament_records` | 锦标赛轮次记录 | 百级 |
| **监控告警** | `monitor_rules` | 告警规则 | 十级 |
| | `monitor_alerts` | 告警记录 | 万级 |

---

## 3. 核心数据表

### 3.1 `contracts` — 品种合约信息

品种主表，记录所有可交易期货合约的元数据。

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INTEGER | PK, AUTO | 主键 |
| `symbol` | VARCHAR(20) | **UNIQUE**, NOT NULL, INDEX | 品种代码，如 CU、RB |
| `name` | VARCHAR(100) | NOT NULL | 品种中文名，如 沪铜、螺纹钢 |
| `exchange` | VARCHAR(20) | NOT NULL, INDEX | 交易所: SHFE/DCE/CZCE/CFFEX/INE/GFEX |
| `category` | VARCHAR(20) | NOT NULL, INDEX | 分类: metal/energy/chemical/agri/equity/rate |
| `multiplier` | INTEGER | DEFAULT 1 | 合约乘数 |
| `min_tick` | FLOAT | DEFAULT 0.01 | 最小变动价位 |
| `margin_rate` | FLOAT | DEFAULT 0.1 | 保证金比例 |
| `commission` | FLOAT | DEFAULT 0.0 | 手续费（按手或按比例） |
| `is_active` | BOOLEAN | DEFAULT true | 是否启用 |
| `delivery_months` | VARCHAR(50) | NULLABLE | 交割月份列表，逗号分隔 |
| `created_at` | DATETIME | DEFAULT now() | 创建时间 |

**索引**:
- `idx_contract_exchange`: exchange
- `idx_contract_category`: category

**常见查询**:
```sql
-- 按交易所查询活跃品种
SELECT * FROM contracts WHERE exchange = 'SHFE' AND is_active = true;

-- 按分类查询
SELECT * FROM contracts WHERE category = 'metal';
```

### 3.2 `klines` — K 线数据

存储所有时间周期的 K 线数据。

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | BIGINT | PK, AUTO | 主键 |
| `symbol` | VARCHAR(20) | NOT NULL | 品种代码 |
| `period` | VARCHAR(10) | NOT NULL | 周期: 1m/5m/15m/30m/1h/4h/1d |
| `timestamp` | DATETIME | NOT NULL | K 线时间 |
| `open` | FLOAT | NOT NULL | 开盘价 |
| `high` | FLOAT | NOT NULL | 最高价 |
| `low` | FLOAT | NOT NULL | 最低价 |
| `close` | FLOAT | NOT NULL | 收盘价 |
| `volume` | FLOAT | NOT NULL | 成交量 |
| `open_interest` | FLOAT | NULLABLE | 持仓量 |
| `created_at` | DATETIME | DEFAULT now() | 创建时间 |

**约束**:
- `UNIQUE(symbol, period, timestamp)` — 同一品种同一周期同一时间仅一条记录
- `INDEX idx_kline_symbol_period(symbol, period)` — 加速按品种+周期的查询

**分区建议** (PostgreSQL):
```sql
-- 按 symbol + period 分区
CREATE TABLE klines (...) PARTITION BY LIST (symbol);
-- 或按时间范围分区
CREATE TABLE klines (...) PARTITION BY RANGE (timestamp);
```

**常见查询**:
```sql
-- 查询某品种最近 N 条日线
SELECT * FROM klines
WHERE symbol = 'CU' AND period = '1d'
ORDER BY timestamp DESC LIMIT 20;

-- 查询时间范围
SELECT * FROM klines
WHERE symbol = 'RB'
  AND period = '1h'
  AND timestamp BETWEEN '2024-01-01' AND '2024-01-31'
ORDER BY timestamp;
```

---

## 4. 策略与信号表

### 4.1 `signals` — 交易信号

记录每个策略在每个品种和 K 线时间点上生成的交易信号。

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | BIGINT | PK, AUTO | 主键 |
| `contract` | VARCHAR(20) | NOT NULL | 品种 |
| `period` | VARCHAR(10) | NOT NULL | 周期 |
| `timestamp` | DATETIME | NOT NULL | 信号时间 |
| `strategy_name` | VARCHAR(50) | NOT NULL | 策略名称 |
| `direction` | VARCHAR(10) | NOT NULL | BUY/SELL/HOLD |
| `confidence` | FLOAT | NOT NULL | 置信度 0.0~1.0 |
| `price` | FLOAT | NULLABLE | 信号触发价格 |
| `reason` | TEXT | NULLABLE | 生成原因 |
| `extra` | JSON | NULLABLE | 扩展数据 |
| `created_at` | DATETIME | DEFAULT now() | 创建时间 |

**约束**: `UNIQUE(contract, period, timestamp, strategy_name)` — 同策略同时间点不重复信号

### 4.2 `parameter_versions` — 策略参数版本

记录策略参数的每次版本变更，用于回调和性能追踪。

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INTEGER | PK, AUTO | 主键 |
| `strategy_name` | VARCHAR(100) | NOT NULL, INDEX | 策略名称 |
| `version` | INTEGER | NOT NULL | 版本号 |
| `params` | JSON | NOT NULL | 参数 JSON |
| `score` | FLOAT | NOT NULL | 性能评分 |
| `timestamp` | FLOAT | NOT NULL | Unix 时间戳 |
| `metadata` | JSON | NULLABLE | 扩展元数据 |
| `created_at` | DATETIME | DEFAULT now() | 创建时间 |

**约束**: `UNIQUE(strategy_name, version)` — 同一策略版本号唯一

---

## 5. 交易与持仓表

### 5.1 `positions` — 持仓记录

当前所有未平仓和已平仓的持仓记录。

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | BIGINT | PK, AUTO | 主键 |
| `symbol` | VARCHAR(20) | NOT NULL | 品种代码 |
| `direction` | VARCHAR(10) | NOT NULL | LONG/SHORT |
| `quantity` | INTEGER | NOT NULL | 持仓数量 |
| `entry_price` | FLOAT | NOT NULL | 开仓均价 |
| `current_price` | FLOAT | NOT NULL | 当前价格 |
| `stop_loss` | FLOAT | NULLABLE | 止损价 |
| `take_profit` | FLOAT | NULLABLE | 止盈价 |
| `pnl` | FLOAT | DEFAULT 0.0 | 浮动盈亏 |
| `status` | VARCHAR(20) | DEFAULT 'OPEN' | OPEN/CLOSED |
| `opened_at` | DATETIME | DEFAULT now() | 开仓时间 |
| `closed_at` | DATETIME | NULLABLE | 平仓时间 |

### 5.2 `trade_records` — 成交记录

每一笔完整的交易记录（开仓→平仓为一条记录）。

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | BIGINT | PK, AUTO | 主键 |
| `symbol` | VARCHAR(20) | NOT NULL | 品种 |
| `direction` | VARCHAR(10) | NOT NULL | LONG/SHORT |
| `entry_price` | FLOAT | NOT NULL | 开仓价 |
| `exit_price` | FLOAT | NULLABLE | 平仓价 |
| `quantity` | INTEGER | NOT NULL | 数量 |
| `entry_time` | DATETIME | NOT NULL | 开仓时间 |
| `exit_time` | DATETIME | NULLABLE | 平仓时间 |
| `pnl` | FLOAT | DEFAULT 0.0 | 盈亏金额 |
| `pnl_pct` | FLOAT | DEFAULT 0.0 | 盈亏百分比 |
| `strategy` | VARCHAR(100) | NOT NULL | 策略名称 |
| `stop_loss` | FLOAT | NULLABLE | 止损价 |
| `take_profit` | FLOAT | NULLABLE | 止盈价 |
| `status` | VARCHAR(20) | DEFAULT 'open' | open/closed |
| `reason` | VARCHAR(500) | NULLABLE | 平仓原因 |
| `created_at` | DATETIME | DEFAULT now() | 创建时间 |

**索引**: `idx_trade_symbol_time(symbol, entry_time)`

---

## 6. 回测与表现表

### 6.1 `backtest_results` — 回测结果

存储策略回测的完整指标。

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | BIGINT | PK, AUTO | 主键 |
| `name` | VARCHAR(100) | NOT NULL | 回测名称 |
| `strategy` | VARCHAR(50) | NOT NULL | 策略名称 |
| `symbol` | VARCHAR(20) | NOT NULL | 品种 |
| `start_date` | VARCHAR(10) | NOT NULL | 开始日期 |
| `end_date` | VARCHAR(10) | NOT NULL | 结束日期 |
| `total_return` | FLOAT | NOT NULL | 总收益率 |
| `sharpe_ratio` | FLOAT | NOT NULL | 夏普比率 |
| `max_drawdown` | FLOAT | NOT NULL | 最大回撤 |
| `win_rate` | FLOAT | NOT NULL | 胜率 |
| `total_trades` | INTEGER | NOT NULL | 总交易次数 |
| `params` | JSON | NULLABLE | 使用的参数 |
| `created_at` | DATETIME | DEFAULT now() | 创建时间 |

**约束**: `UNIQUE(symbol, strategy, start_date, end_date)` — 同参数不重复回测

### 6.2 `performance_snapshots` — 每日表现快照

每日收盘后记录账户和策略的净值快照。

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INTEGER | PK, AUTO | 主键 |
| `snapshot_date` | DATETIME | NOT NULL | 快照日期 |
| `strategy_name` | VARCHAR(100) | NOT NULL | 策略名称 |
| `total_equity` | FLOAT | DEFAULT 0.0 | 总权益 |
| `cash` | FLOAT | DEFAULT 0.0 | 现金 |
| `positions_value` | FLOAT | DEFAULT 0.0 | 持仓市值 |
| `daily_pnl` | FLOAT | DEFAULT 0.0 | 日盈亏 |
| `total_pnl` | FLOAT | DEFAULT 0.0 | 累计盈亏 |
| `drawdown` | FLOAT | DEFAULT 0.0 | 当前回撤 |
| `metrics` | JSON | NULLABLE | 扩展指标 |
| `created_at` | DATETIME | DEFAULT now() | 创建时间 |

**约束**: `UNIQUE(snapshot_date, strategy_name)` — 每日每策略一条快照

---

## 7. ML 模型表

### 7.1 `model_versions` — ML 模型版本管理

管理 ML 模型的版本、指标和存储路径。

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INTEGER | PK, AUTO | 主键 |
| `model_name` | VARCHAR(100) | NOT NULL | 模型名称 |
| `version` | VARCHAR(20) | NOT NULL | 版本号 |
| `description` | TEXT | NULLABLE | 描述 |
| `metrics` | JSON | NULLABLE | 训练指标 |
| `file_path` | VARCHAR(500) | NULLABLE | 模型文件路径 |
| `is_active` | BOOLEAN | DEFAULT false | 是否为当前活跃版本 |
| `trained_at` | DATETIME | NULLABLE | 训练完成时间 |
| `created_at` | DATETIME | DEFAULT now() | 创建时间 |

**约束**: `UNIQUE(model_name, version)` — 同一模型版本唯一

---

## 8. 锦标赛表

### 8.1 `tournament_strategies` — 参赛策略注册

策略锦标赛中每个参赛策略的得分和状态。

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INTEGER | PK, AUTO | 主键 |
| `strategy_name` | VARCHAR(100) | NOT NULL | 策略名称 |
| `tournament_round` | INTEGER | DEFAULT 1 | 当前轮次 |
| `score` | FLOAT | DEFAULT 0.0 | 综合评分 |
| `sharpe` | FLOAT | DEFAULT 0.0 | 夏普比率 |
| `win_rate` | FLOAT | DEFAULT 0.0 | 胜率 |
| `total_trades` | INTEGER | DEFAULT 0 | 总交易数 |
| `total_pnl` | FLOAT | DEFAULT 0.0 | 总盈亏 |
| `rank` | INTEGER | NULLABLE | 当前排名 |
| `is_active` | BOOLEAN | DEFAULT true | 是否活跃 |
| `is_eliminated` | BOOLEAN | DEFAULT false | 是否已被淘汰 |
| `created_at` | DATETIME | DEFAULT now() | 创建时间 |

**约束**: `UNIQUE(strategy_name, tournament_round)`

### 8.2 `tournament_records` — 锦标赛轮次记录

每轮锦标赛的汇总信息。

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INTEGER | PK, AUTO | 主键 |
| `round` | INTEGER | NOT NULL | 轮次号 |
| `mode` | VARCHAR(20) | NOT NULL | 模式: DUEL/TOURNAMENT/EXPLORATION |
| `total_strategies` | INTEGER | DEFAULT 0 | 参赛策略数 |
| `eliminated_count` | INTEGER | DEFAULT 0 | 被淘汰数 |
| `summary` | JSON | NULLABLE | 轮次汇总数据 |
| `created_at` | DATETIME | DEFAULT now() | 创建时间 |

---

## 9. 监控告警表

### 9.1 `monitor_rules` — 告警规则

定义监控告警的规则配置。

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INTEGER | PK, AUTO | 主键 |
| `name` | VARCHAR(100) | NOT NULL | 规则名称 |
| `rule_type` | VARCHAR(50) | NOT NULL | 类型: drawdown/var/volume/signal |
| `symbol` | VARCHAR(20) | NULLABLE | 关联品种 (空 = 全局) |
| `params` | JSON | NOT NULL | 规则参数 |
| `level` | VARCHAR(20) | DEFAULT 'WARNING' | 告警级别 |
| `enabled` | BOOLEAN | DEFAULT true | 是否启用 |
| `created_at` | DATETIME | DEFAULT now() | 创建时间 |

### 9.2 `monitor_alerts` — 告警记录

所有触发的告警事件记录。

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | BIGINT | PK, AUTO | 主键 |
| `rule_id` | INTEGER | NULLABLE | 关联规则 ID |
| `rule_name` | VARCHAR(100) | NOT NULL | 规则名称 |
| `level` | VARCHAR(20) | NOT NULL, INDEX | 告警级别 |
| `title` | VARCHAR(200) | NOT NULL | 告警标题 |
| `message` | TEXT | NOT NULL | 告警详情 |
| `symbol` | VARCHAR(20) | NULLABLE | 相关品种 |
| `metric_value` | FLOAT | NULLABLE | 触发指标值 |
| `threshold` | FLOAT | NULLABLE | 阈值 |
| `acknowledged` | BOOLEAN | DEFAULT false | 是否已确认 |
| `created_at` | DATETIME | DEFAULT now(), INDEX | 触发时间 |

**索引**: `idx_alert_level_time(level, created_at)`

---

## 10. ER 关系图

```ascii
┌────────────────┐       ┌─────────────────┐
│   contracts    │       │    klines        │
│  (品种主表)    │       │  (K线数据)       │
│                │◄──────│                  │
│ symbol (PK)    │       │ symbol (FK)      │
│ name           │       │ period           │
│ exchange       │       │ timestamp        │
│ category       │       │ OHLCV            │
│ multiplier     │       └─────────────────┘
│ margin_rate    │
└───────┬────────┘
        │
        │ 1:N
        ▼
┌────────────────┐       ┌─────────────────┐
│   signals      │       │ positions       │
│  (交易信号)    │       │  (持仓)          │
│                │       │                  │
│ contract (FK)  │       │ symbol (FK)      │
│ strategy_name  │       │ direction        │
│ direction      │       │ quantity         │
│ confidence     │       │ entry_price      │
│ price          │       │ status           │
└────────────────┘       └────────┬─────────┘
                                  │
                                  │
                    ┌─────────────▼──────────────┐
                    │    trade_records            │
                    │   (成交记录)                 │
                    │                             │
                    │ symbol (FK)                 │
                    │ direction                   │
                    │ entry/exit price/time       │
                    │ pnl / pnl_pct               │
                    │ strategy                    │
                    └─────────────────────────────┘

┌─────────────────────┐   ┌───────────────────────┐
│  parameter_versions │   │  backtest_results     │
│  (参数版本)          │   │  (回测结果)            │
│                     │   │                       │
│ strategy_name       │   │ strategy              │
│ version             │   │ symbol                │
│ params (JSON)       │   │ total_return          │
│ score               │   │ sharpe_ratio          │
└─────────────────────┘   │ max_drawdown          │
                          └───────────────────────┘

┌─────────────────────┐   ┌───────────────────────┐
│  performance_snapshots │  model_versions        │
│  (每日快照)           │  (ML模型版本)            │
│                      │  │                       │
│ snapshot_date        │  │ model_name            │
│ strategy_name        │  │ version               │
│ total_equity         │  │ metrics (JSON)         │
│ drawdown             │  │ is_active             │
└──────────────────────┘  └───────────────────────┘

┌─────────────────────┐   ┌───────────────────────┐
│  tournament_strategies│  tournament_records     │
│  (参赛策略)          │  │ (轮次记录)             │
│                     │   │                       │
│ strategy_name       │   │ round                 │
│ tournament_round    │   │ mode (DUEL/...)       │
│ score / sharpe      │   │ total_strategies      │
│ rank / is_eliminated│   │ eliminated_count      │
└─────────────────────┘   └───────────────────────┘

┌─────────────────────┐   ┌───────────────────────┐
│   monitor_rules     │   │  monitor_alerts       │
│  (告警规则)         │   │  (告警记录)            │
│                     │   │                       │
│ name                │──►│ rule_id (FK)          │
│ rule_type           │   │ level / title         │
│ params (JSON)       │   │ message               │
│ level / enabled     │   │ acknowledged          │
└─────────────────────┘   └───────────────────────┘
```

---

## 11. 迁移指南

### 11.1 首次初始化

```bash
# 本地开发 (SQLite)
python scripts/init_db.py --db sqlite

# 生产部署 (PostgreSQL)
python scripts/init_db.py --db postgresql
```

### 11.2 手动运行迁移

```bash
# 升级到最新版本
alembic upgrade head

# 查看当前版本
alembic current

# 查看历史
alembic history

# 回退一步
alembic downgrade -1

# 回退到指定版本
alembic downgrade <revision_id>
```

### 11.3 生成新迁移

```bash
# 自动检测模型变更
alembic revision --autogenerate -m "description_of_change"

# 手动创建空白迁移
alembic revision -m "description_of_change"
```

### 11.4 SQLite ↔ PostgreSQL 迁移

如果需要从 SQLite 开发环境迁移到 PostgreSQL 生产环境：

```bash
# 1. 从 SQLite 导出数据
# TODO: 实现导出脚本
sqlite3 data/futures.db .dump > backup.sql

# 2. 初始化 PostgreSQL
python scripts/init_db.py --db postgresql

# 3. 导入数据 (使用 pgloader 或自定义脚本)
pgloader sqlite:///data/futures.db postgresql://trading:trading_pass@localhost:5432/trading_strategy_center
```

---

## 12. 运维命令

### 12.1 Docker 环境

```bash
# 启动 PostgreSQL
docker compose up -d postgres

# 查看数据库日志
docker compose logs -f postgres

# 备份数据库
docker compose exec postgres pg_dump -U trading trading_strategy_center > backup.sql

# 恢复数据库
docker compose exec -T postgres psql -U trading trading_strategy_center < backup.sql
```

### 12.2 常用 SQL 查询

```sql
-- 查看各表数据量
SELECT table_name, (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public') as total;

-- PostgreSQL 表大小
SELECT
    relname as table_name,
    pg_size_pretty(pg_total_relation_size(relid)) as total_size
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC;

-- 查询最近交易
SELECT * FROM trade_records
ORDER BY created_at DESC LIMIT 20;

-- 查询当前持仓
SELECT * FROM positions WHERE status = 'OPEN';

-- 查询最近告警
SELECT * FROM monitor_alerts
WHERE acknowledged = false
ORDER BY created_at DESC LIMIT 10;

-- 查询策略表现
SELECT strategy_name, SUM(pnl), COUNT(*) as trades, AVG(pnl_pct) as avg_pnl_pct
FROM trade_records
WHERE status = 'closed'
GROUP BY strategy_name
ORDER BY SUM(pnl) DESC;
```

### 12.3 日常维护

```bash
# 每日收盘后运行 (TODO: 实现 daily_close.py)
# 1. 计算当日 PnL → 写入 performance_snapshots
# 2. 清理过期信号
# 3. 更新 ML 模型 (如需)
# python scripts/daily_close.py

# 数据归档 (PostgreSQL)
# 将 90 天前的 klines 按年分区归档
```

---

## 13. 常见问题

### Q: 迁移时提示 "Target database is not up to date"

```bash
# 方法 1: 强制升级到最新
alembic upgrade head

# 方法 2: 标记当前版本为最新
alembic stamp head
```

### Q: PostgreSQL 连接失败

```bash
# 1. 检查 PostgreSQL 是否运行
docker compose ps

# 2. 检查连接参数
echo "DB_HOST=$DB_HOST DB_PORT=$DB_PORT DB_USER=$DB_USER"

# 3. 测试连接
docker compose exec postgres pg_isready -U trading
```

### Q: SQLite 并发写入冲突

SQLite 不适合高并发写入。开发环境中：

- 连接参数设置 `check_same_thread=False`
- 避免多个 worker 同时写入
- 生产环境请使用 PostgreSQL

### Q: 表结构变更后数据不兼容

```bash
# 1. 备份数据
pg_dump -U trading trading_strategy_center > pre_migration_backup.sql

# 2. 回退迁移
alembic downgrade <previous_revision>

# 3. 生成新迁移
alembic revision --autogenerate -m "fix_schema"

# 4. 升级
alembic upgrade head
```
