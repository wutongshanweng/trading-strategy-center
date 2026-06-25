-- 交易系统统一数据库 — DuckDB Schema
-- 对应设计文档: 交易系统统一数据库设计.md
-- 原则: 具体合约不搞合成; 品种/合约两层; 统一多周期 kline 表

-- ============================================================
-- 序列 (DuckDB 自增主键)
-- ============================================================
CREATE SEQUENCE IF NOT EXISTS seq_product_id START 1;
CREATE SEQUENCE IF NOT EXISTS seq_symbol_id START 1;
CREATE SEQUENCE IF NOT EXISTS seq_mapping_id START 1;
CREATE SEQUENCE IF NOT EXISTS seq_switch_id START 1;

-- ============================================================
-- 2.1 品种表 products
-- ============================================================
CREATE TABLE IF NOT EXISTS products (
    product_id      INTEGER PRIMARY KEY DEFAULT nextval('seq_product_id'),
    code            VARCHAR NOT NULL UNIQUE,
    name            VARCHAR NOT NULL,
    asset_type      VARCHAR NOT NULL,            -- 'futures','stock','option','index','macro'
    exchange        VARCHAR,
    sector          VARCHAR,                     -- '黑色','有色','化工','农产品'
    sub_sector      VARCHAR,
    multiplier      INTEGER,                     -- 合约乘数
    tick_size       DECIMAL(10,4),
    tick_value      DECIMAL(10,2),
    margin_rate     DECIMAL(6,4),
    trading_hours   VARCHAR,
    list_date       DATE,
    status          VARCHAR DEFAULT 'active'
);

-- ============================================================
-- 2.2 合约表 symbols
-- ============================================================
CREATE TABLE IF NOT EXISTS symbols (
    symbol_id       INTEGER PRIMARY KEY DEFAULT nextval('seq_symbol_id'),
    product_id      INTEGER REFERENCES products(product_id),
    code            VARCHAR NOT NULL UNIQUE,
    name            VARCHAR,
    contract_year   INTEGER,                     -- 2025
    contract_month  VARCHAR,                     -- '09'
    is_main         BOOLEAN DEFAULT false,       -- 当前主力
    -- 期权专有
    option_type     VARCHAR,                     -- 'call','put'
    strike_price    DECIMAL(12,2),
    option_style    VARCHAR,                     -- '欧式','美式'
    underlying_id   INTEGER,                     -- 期权标的 symbol_id
    -- 时间
    list_date       DATE,
    expire_date     DATE,
    last_trade_date DATE,
    delivery_date   DATE,
    status          VARCHAR DEFAULT 'active',
    created_at      TIMESTAMP DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_sym_product ON symbols(product_id);
CREATE INDEX IF NOT EXISTS idx_sym_main ON symbols(product_id, is_main);

-- ============================================================
-- 2.3 K线表 kline (统一多周期)
-- ============================================================
CREATE TABLE IF NOT EXISTS kline (
    datetime        TIMESTAMP NOT NULL,          -- bar 开始时间
    symbol_id       INTEGER NOT NULL REFERENCES symbols(symbol_id),
    timeframe       VARCHAR NOT NULL,            -- 'M5','M15','M30','H1','H4','D1','W1','M1'
    open            DECIMAL(12,4),
    high            DECIMAL(12,4),
    low             DECIMAL(12,4),
    close           DECIMAL(12,4),
    volume          BIGINT,
    amount          BIGINT,                      -- 成交额
    open_interest   BIGINT,                      -- 持仓量 (期货/期权)
    settlement      DECIMAL(12,4),               -- 期货结算价
    pre_settlement  DECIMAL(12,4),
    created_at      TIMESTAMP DEFAULT now(),
    PRIMARY KEY (datetime, symbol_id, timeframe)
);
CREATE INDEX IF NOT EXISTS idx_kline_sym ON kline(symbol_id, timeframe, datetime);
CREATE INDEX IF NOT EXISTS idx_kline_date ON kline(datetime);

-- 主力合约关系表 (单独存, 避免 UPDATE 被 kline 外键引用的 symbols 行 — DuckDB 限制)
CREATE TABLE IF NOT EXISTS main_contracts (
    product_id      INTEGER PRIMARY KEY,
    symbol_code     VARCHAR NOT NULL,
    updated_at      TIMESTAMP DEFAULT now()
);

-- ============================================================
-- 2.4 期权专有表 options_daily
-- ============================================================
CREATE TABLE IF NOT EXISTS options_daily (
    date                DATE NOT NULL,
    symbol_id           INTEGER NOT NULL REFERENCES symbols(symbol_id),
    iv                  DECIMAL(8,4),
    iv_percentile       DECIMAL(8,4),
    hv_30               DECIMAL(8,4),            -- 30日历史波动率
    delta               DECIMAL(8,4),
    gamma               DECIMAL(12,6),
    theta               DECIMAL(12,4),
    vega                DECIMAL(12,4),
    rho                 DECIMAL(12,4),
    theoretical_price   DECIMAL(12,4),           -- BS理论价
    time_value          DECIMAL(12,4),
    intrinsic_value     DECIMAL(12,4),
    underlying_close    DECIMAL(12,4),
    underlying_id       INTEGER,
    PRIMARY KEY (date, symbol_id)
);
CREATE INDEX IF NOT EXISTS idx_opt_sym ON options_daily(symbol_id);

-- ============================================================
-- 2.5 股票信息表 stocks_info
-- ============================================================
CREATE TABLE IF NOT EXISTS stocks_info (
    symbol_id       INTEGER PRIMARY KEY REFERENCES symbols(symbol_id),
    company_name    VARCHAR,
    industry        VARCHAR,                     -- 申万行业
    listing_date    DATE,
    total_shares    BIGINT,
    float_shares    BIGINT,
    market_cap      DECIMAL(20,2),
    pe_ttm          DECIMAL(10,2),
    pb              DECIMAL(10,2),
    dividend_yield  DECIMAL(6,4),
    beta            DECIMAL(6,4)
);

-- ============================================================
-- 2.6 股票财报表 stocks_financial
-- ============================================================
CREATE TABLE IF NOT EXISTS stocks_financial (
    symbol_id       INTEGER REFERENCES symbols(symbol_id),
    report_date     DATE NOT NULL,
    report_type     VARCHAR,                     -- 'Q1','Q2','Q3','Q4','annual'
    revenue         DECIMAL(20,2),
    revenue_yoy     DECIMAL(6,4),
    net_profit      DECIMAL(20,2),
    net_profit_yoy  DECIMAL(6,4),
    eps             DECIMAL(10,4),
    bvps            DECIMAL(10,4),
    roe             DECIMAL(6,4),
    gross_margin    DECIMAL(6,4),
    net_margin      DECIMAL(6,4),
    debt_ratio      DECIMAL(6,4),
    PRIMARY KEY (symbol_id, report_date)
);

-- ============================================================
-- 2.7 主力合约切换记录 futures_main_switches
-- ============================================================
CREATE TABLE IF NOT EXISTS futures_main_switches (
    switch_id           INTEGER PRIMARY KEY DEFAULT nextval('seq_switch_id'),
    product_id          INTEGER REFERENCES products(product_id),
    old_symbol_id       INTEGER REFERENCES symbols(symbol_id),
    new_symbol_id       INTEGER REFERENCES symbols(symbol_id),
    switch_date         DATE NOT NULL,
    reason              VARCHAR,                 -- '自然换月','异常换月'
    volume_ratio        DECIMAL(6,4),
    open_interest_ratio DECIMAL(6,4),
    price_gap           DECIMAL(12,4),
    created_at          TIMESTAMP DEFAULT now()
);

-- ============================================================
-- 2.8 宏观数据表 macro_data
-- ============================================================
CREATE TABLE IF NOT EXISTS macro_data (
    date            DATE NOT NULL,
    product_id      INTEGER REFERENCES products(product_id),
    value           DECIMAL(16,4),
    value_prev      DECIMAL(16,4),
    value_yoy       DECIMAL(6,4),
    value_mom       DECIMAL(6,4),
    unit            VARCHAR,
    source          VARCHAR,
    importance      INTEGER,                     -- 1-5
    created_at      TIMESTAMP DEFAULT now(),
    PRIMARY KEY (date, product_id)
);

-- ============================================================
-- 2.9 跨市场映射表 cross_market_mapping (核心)
-- ============================================================
CREATE TABLE IF NOT EXISTS cross_market_mapping (
    mapping_id      INTEGER PRIMARY KEY DEFAULT nextval('seq_mapping_id'),
    product_id_a    INTEGER REFERENCES products(product_id),
    asset_type_a    VARCHAR,
    product_id_b    INTEGER REFERENCES products(product_id),
    asset_type_b    VARCHAR,
    relation_type   VARCHAR,                     -- '成本传导','利润联动','同业','上下游'
    logic_desc      VARCHAR,
    direction       VARCHAR DEFAULT 'bidirectional',
    corr_20d        DECIMAL(6,4),
    corr_60d        DECIMAL(6,4),
    lag_days        INTEGER,
    lead_lag_corr   DECIMAL(6,4),
    status          VARCHAR DEFAULT 'active',
    created_at      TIMESTAMP DEFAULT now(),
    updated_at      TIMESTAMP DEFAULT now(),
    UNIQUE(product_id_a, product_id_b, relation_type)
);

-- ============================================================
-- 2.10 因子性能表 factor_performance (IC/IR实时计算)
-- ============================================================
CREATE TABLE IF NOT EXISTS factor_performance (
    id              INTEGER PRIMARY KEY DEFAULT nextval('seq_symbol_id'),
    factor_name     VARCHAR NOT NULL,
    symbol          VARCHAR NOT NULL,
    calc_date       DATE NOT NULL,
    ic              DECIMAL(8,4),                  -- 信息系数 (Information Coefficient)
    ir              DECIMAL(8,4),                  -- 信息比率 (IC均值/IC标准差)
    ic_series       VARCHAR,                       -- JSON格式的IC时间序列
    risk_adj_return DECIMAL(10,4),                 -- 风险调整收益
    ic_mean_short   DECIMAL(8,4),                  -- 近20日IC均值
    ic_mean_long    DECIMAL(8,4),                  -- 近60日IC均值
    updated_at      TIMESTAMP DEFAULT now(),
    UNIQUE(factor_name, symbol, calc_date)
);
CREATE INDEX IF NOT EXISTS idx_fp_factor ON factor_performance(factor_name);
CREATE INDEX IF NOT EXISTS idx_fp_symbol ON factor_performance(symbol);
CREATE INDEX IF NOT EXISTS idx_fp_date ON factor_performance(calc_date);
