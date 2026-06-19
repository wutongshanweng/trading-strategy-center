import { useEffect, useState } from "react";
import {
  Row, Col, Card, Table, Tag, Typography, Statistic, Badge,
  Input, Button, Tabs, message, Select, Space, Progress, DatePicker, Popconfirm,
} from "antd";
import dayjs from "dayjs";
import {
  DatabaseOutlined, CheckCircleOutlined, WarningOutlined,
  CloseCircleOutlined, SearchOutlined, DownloadOutlined,
  SyncOutlined, BookOutlined, DeleteOutlined, FileExcelOutlined,
  ApiOutlined, RiseOutlined, SafetyOutlined,
} from "@ant-design/icons";
import axios from "axios";

const { Text, Title } = Typography;
const { TabPane } = Tabs;

/* ── API client ── */
const API = axios.create({ baseURL: "/api/v1/data-center", timeout: 15000 });
const WH = axios.create({ baseURL: "/api/v1/warehouse", timeout: 30000 });

/* 价格格式化: 最多 3 位小数, 去掉多余的 0 (前复权价常带 7 位小数) */
const fmtPrice = (v: any): string => {
  const n = Number(v);
  if (v == null || isNaN(n)) return "-";
  return n.toFixed(3).replace(/\.?0+$/, "");
};
const fmtVol = (v: any): string => {
  const n = Number(v);
  if (v == null || isNaN(n)) return "-";
  return n.toLocaleString();
};

/* 股票代码归一化: 600019 -> 600019.SH (6/9开头=SH, 0/3开头=SZ); 已带后缀原样 */
const normStockCode = (code: string): string => {
  const c = (code || "").trim().toUpperCase();
  if (c.includes(".")) return c;
  if (/^\d{6}$/.test(c)) return `${c}.${"69".includes(c[0]) ? "SH" : "SZ"}`;
  return c;
};

/* 带悬浮提示的收盘价走势图 — 鼠标移动显示该点日期 + 收盘价 */
function PriceChart({ dates, closes }: { dates: string[]; closes: number[] }) {
  const [hover, setHover] = useState<number | null>(null);
  const W = 800, H = 180, pad = 8;
  const nums = closes.filter((v) => typeof v === "number" && !isNaN(v));
  if (nums.length < 2) return null;
  const min = Math.min(...nums), max = Math.max(...nums);
  const span = max - min || 1;
  const xAt = (i: number) => pad + (i / (nums.length - 1)) * (W - 2 * pad);
  const yAt = (v: number) => H - pad - ((v - min) / span) * (H - 2 * pad);
  const pts = nums.map((v, i) => `${xAt(i).toFixed(1)},${yAt(v).toFixed(1)}`).join(" ");

  const onMove = (e: React.MouseEvent<SVGSVGElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const rel = (e.clientX - rect.left) / rect.width;     // 0..1
    const i = Math.round(rel * (nums.length - 1));
    setHover(Math.max(0, Math.min(nums.length - 1, i)));
  };

  const hx = hover != null ? xAt(hover) : 0;
  const hy = hover != null ? yAt(nums[hover]) : 0;
  const tipLeft = hover != null ? `${(hx / W) * 100}%` : "0";
  const tipFlip = hover != null && hx > W * 0.6;          // 右侧时提示框翻到左边

  return (
    <div style={{ position: "relative" }}>
      <svg width="100%" height={H} viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none"
        onMouseMove={onMove} onMouseLeave={() => setHover(null)}
        style={{ display: "block", height: H, border: "1px solid #f0f0f0", borderRadius: 4, cursor: "crosshair" }}>
        <polyline points={pts} fill="none" stroke="#1677ff" strokeWidth={1.5} vectorEffect="non-scaling-stroke" />
        {hover != null && (
          <>
            <line x1={hx} y1={pad} x2={hx} y2={H - pad} stroke="#faad14" strokeWidth={1} strokeDasharray="3,3" vectorEffect="non-scaling-stroke" />
            <circle cx={hx} cy={hy} r={3} fill="#1677ff" stroke="#fff" strokeWidth={1} />
          </>
        )}
      </svg>
      {hover != null && (
        <div style={{
          position: "absolute", top: 4, left: tipLeft,
          transform: tipFlip ? "translateX(-105%)" : "translateX(5%)",
          background: "rgba(0,0,0,0.78)", color: "#fff", fontSize: 12,
          padding: "4px 8px", borderRadius: 4, pointerEvents: "none", whiteSpace: "nowrap",
        }}>
          <div>{String(dates[hover] ?? "").slice(0, 10)}</div>
          <div>收盘: <b>{fmtPrice(nums[hover])}</b></div>
        </div>
      )}
    </div>
  );
}

export default function DataCenter() {
  const [activeTab, setActiveTab] = useState("overview");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);

  // Data sources
  const [sources, setSources] = useState<any[]>([]);
  const [sourceHealth, setSourceHealth] = useState<Record<string, string>>({});

  // Knowledge / Exchanges
  const [exchanges, setExchanges] = useState<any[]>([]);
  const [contracts, setContracts] = useState<any[]>([]);
  const [selectedSymbol, setSelectedSymbol] = useState<string>("M");
  const [contractDetail, setContractDetail] = useState<any>(null);
  const [mainContract, setMainContract] = useState<any>(null);

  // Download
  const [downloadHistory, setDownloadHistory] = useState<any[]>([]);
  const [downloadStats, setDownloadStats] = useState<any>(null);
  const [dlStartDate, setDlStartDate] = useState<string>("");
  const [dlEndDate, setDlEndDate] = useState<string>("");
  const [dlInterval, setDlInterval] = useState<string>("1d");
  const [dlContract, setDlContract] = useState<string>("");
  const [dlResult, setDlResult] = useState<any>(null);

  // Batch download
  const [batchSymbols, setBatchSymbols] = useState<string[]>(["M", "RB", "CU"]);
  const [batchRunning, setBatchRunning] = useState(false);
  const [batchResults, setBatchResults] = useState<any>(null);

  // Sync
  const [syncStatus, setSyncStatus] = useState<any>(null);

  // Asset class for download (futures/stock/option)
  const [assetType, setAssetType] = useState<"futures" | "stock" | "option">("futures");
  const [stockSymbol, setStockSymbol] = useState<string>("600019.SH");
  const [stockList, setStockList] = useState<{ value: string; label: string }[]>([]);
  const [stockListLoading, setStockListLoading] = useState(false);
  const [optUnderlying, setOptUnderlying] = useState<string>("510050");
  const [optCodes, setOptCodes] = useState<string[]>([]);
  const [optContract, setOptContract] = useState<string>("");

  // Preview
  const [pvAsset, setPvAsset] = useState<"futures" | "stock" | "option">("futures");
  const [pvFiles, setPvFiles] = useState<any[]>([]);
  const [pvFile, setPvFile] = useState<string>("");
  const [pvData, setPvData] = useState<any>(null);
  const [pvLoading, setPvLoading] = useState(false);

  // Warehouse: 期货按品种+年份采集
  const [whProduct, setWhProduct] = useState<string>("RB");
  const [whYear, setWhYear] = useState<number>(new Date().getFullYear());
  const [whEndYear, setWhEndYear] = useState<number>(new Date().getFullYear());

  // Warehouse: 全量/批量采集 + 进度
  const [fullPhase, setFullPhase] = useState<string>("futures");
  const [fullStart, setFullStart] = useState<string>("");
  const [stockLimit, setStockLimit] = useState<number>(50);
  const [collectProgress, setCollectProgress] = useState<any>(null);
  const [whContracts, setWhContracts] = useState<any[]>([]);
  const [whContractsLoading, setWhContractsLoading] = useState(false);
  const [mainContracts, setMainContracts] = useState<any[]>([]);

  // Warehouse: 仓库预览 (按合约代码)
  const [whPvCode, setWhPvCode] = useState<string>("");
  const [whPvTf, setWhPvTf] = useState<string>("D1");
  const [whPvData, setWhPvData] = useState<any>(null);
  const [whPvLoading, setWhPvLoading] = useState(false);

  // Storage
  const [storage, setStorage] = useState<any>(null);

  // Warehouse stats (overview cards: 股票/期权 品种数)
  const [whStats, setWhStats] = useState<any>(null);
  const [dbSize, setDbSize] = useState<any>(null);

  // 按年同步面板
  const [yearStatus, setYearStatus] = useState<any[]>([]);
  const [yearSyncLoading, setYearSyncLoading] = useState(false);
  const [verifyResult, setVerifyResult] = useState<any>(null);

  // Stock knowledge base
  const [stockSectors, setStockSectors] = useState<any[]>([]);
  const [stockRelations, setStockRelations] = useState<any[]>([]);
  const [fundSymbol, setFundSymbol] = useState<string>("600019.SH");
  const [fundData, setFundData] = useState<any>(null);
  const [fundLoading, setFundLoading] = useState(false);

  // Options knowledge base
  const [optProducts, setOptProducts] = useState<any[]>([]);
  const [optStrategies, setOptStrategies] = useState<any[]>([]);

  // Load data on mount
  useEffect(() => {
    loadSources();
    loadExchanges();
    loadWhStats();
  }, []);

  const loadWhStats = async () => {
    try {
      const res = await WH.get("/stats");
      setWhStats(res.data || null);
    } catch { /* warehouse may be empty */ }
    try {
      const res = await WH.get("/db-size");
      setDbSize(res.data || null);
    } catch { /* ignore */ }
  };

  const loadSources = async () => {
    try {
      const [srcRes, healthRes] = await Promise.all([
        API.get("/sources"),
        API.get("/sources/health"),
      ]);
      setSources(srcRes.data?.sources || []);
      setSourceHealth(healthRes.data || {});
    } catch { /* backend may not be running */ }
  };

  const loadExchanges = async () => {
    try {
      const res = await API.get("/exchanges");
      setExchanges(res.data?.exchanges || []);
    } catch { /* ignore */ }
  };

  const loadContractInfo = async (symbol: string) => {
    if (!symbol) return;
    try {
      const [info, main] = await Promise.all([
        API.get(`/contracts/${symbol}`),
        API.get(`/contracts/${symbol}/main`),
      ]);
      setContractDetail(info.data);
      setMainContract(main.data);
    } catch { /* ignore */ }
  };

  const loadDownloadData = async () => {
    try {
      const [histRes, statsRes] = await Promise.all([
        API.get("/download/history"),
        API.get("/download/stats"),
      ]);
      setDownloadHistory(histRes.data?.history || []);
      setDownloadStats(statsRes.data?.stats || null);
    } catch { /* ignore */ }
  };

  const loadSyncStatus = async () => {
    try {
      const res = await API.get("/sync/status");
      setSyncStatus(res.data);
    } catch { /* ignore */ }
  };

  const loadStorage = async () => {
    try {
      const res = await API.get("/storage");
      setStorage(res.data);
    } catch { /* ignore */ }
  };

  // 从文件 path 推断资产类别 (data/market/{futures|stock|options}/...)
  const assetFromPath = (p: string): "futures" | "stock" | "option" => {
    const s = (p || "").replace(/\\/g, "/");
    if (s.includes("/stock/")) return "stock";
    if (s.includes("/options/")) return "option";
    return "futures";
  };

  const exportFile = (row: any) => {
    const asset = assetFromPath(row.path);
    const params = new URLSearchParams({
      symbol: row.symbol, interval: row.interval, asset_type: asset,
    });
    if (row.contract) params.set("contract", row.contract);
    // 浏览器直接下载 (后端返回 attachment)
    window.open(`/api/v1/data-center/data-files/export?${params.toString()}`, "_blank");
  };

  const deleteFile = async (row: any) => {
    const asset = assetFromPath(row.path);
    try {
      await API.delete("/data-files", {
        params: { symbol: row.symbol, interval: row.interval, asset_type: asset,
          contract: row.contract || undefined },
      });
      message.success(`已删除 ${row.symbol}${row.contract ? "/" + row.contract : ""} ${row.interval}`);
      loadStorage();
    } catch (err: any) {
      message.error(`删除失败: ${err.response?.data?.detail || err.message}`);
    }
  };

  // ── Render: Source Status Cards ──
  const renderSources = () => (
    <Row gutter={[12, 12]}>
      {sources.length === 0 ? (
        <Col span={24}><Text type="secondary">后端 API 未运行，显示模拟数据</Text></Col>
      ) : (
        sources.map((s: any) => {
          const status = sourceHealth[s.name] || "unknown";
          const isOk = status === "healthy" || status === "active";
          return (
            <Col xs={24} sm={12} lg={6} key={s.name}>
              <Card size="small" hoverable>
                <Space direction="vertical" style={{ width: "100%" }}>
                  <Space>
                    {isOk ? <CheckCircleOutlined style={{ color: "#52c41a" }} />
                      : <WarningOutlined style={{ color: "#faad14" }} />}
                    <Text strong>{s.display_name || s.name}</Text>
                  </Space>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {s.description || ""}
                  </Text>
                  <div>
                    <Tag color={isOk ? "green" : "orange"}>{status}</Tag>
                    {s.requires_api_key && <Tag color="blue">需API Key</Tag>}
                  </div>
                </Space>
              </Card>
            </Col>
          );
        })
      )}
      {/* Static source cards — 仅当后端未启动时显示 (16个数据源) */}
      {sources.length === 0 && [
        "AKShare", "Yahoo Finance", "TDX (通达信)", "FRED", "Alpha Vantage",
        "CFTC", "EIA", "Quandl", "Tushare", "Wind",
        "IEX Cloud", "Polygon.io", "CSMAR", "CRSP", "Compustat", "Bloomberg"
      ].map((name) => (
        <Col xs={24} sm={12} lg={6} key={name}>
          <Card size="small" hoverable>
            <Space>
              <ApiOutlined style={{ color: "#1677ff" }} />
              <Text strong>{name}</Text>
            </Space>
            <div style={{ marginTop: 8 }}>
              <Tag color="default">就绪</Tag>
            </div>
          </Card>
        </Col>
      ))}
    </Row>
  );

  // ── Render: Knowledge / Contract Info ──
  const renderKnowledge = () => (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col span={12}>
          <Select
            showSearch
            style={{ width: "100%" }}
            placeholder="选择品种 (如 M, RB, CU)"
            value={selectedSymbol}
            onChange={(v) => { setSelectedSymbol(v); loadContractInfo(v); }}
          >
            {["M","RB","CU","AU","AG","I","SC","CF","TA","MA","IF","C","Y","P","SR","RM","FG","SA","J","JM","HC","RU","NI","ZN","AL","PB","SN","EG","PP","L","V","PG","LH","AP","PK","CJ","SF","SM","UR","SP","SS","SI","LC","FU","BU","NR","LU","BC","A","B","CS","JD","EB","IH","IC","IM","T","TF","TS"].map(sym => (
              <Select.Option key={sym} value={sym}>{sym}</Select.Option>
            ))}
          </Select>
        </Col>
        <Col span={12}>
          <Button icon={<SyncOutlined />} onClick={() => loadContractInfo(selectedSymbol)}>查询</Button>
        </Col>
      </Row>

      {contractDetail && (
        <Card title={`${contractDetail.symbol} - ${contractDetail.name_cn}`} style={{ marginBottom: 16 }}>
          <Row gutter={[16, 16]}>
            <Col span={8}><Statistic title="交易所" value={contractDetail.exchange_cn} /></Col>
            <Col span={8}><Statistic title="合约乘数" value={contractDetail.contract_multiplier} suffix="元/点" /></Col>
            <Col span={8}><Statistic title="最小变动" value={contractDetail.min_tick} suffix="元" /></Col>
            <Col span={8}><Statistic title="保证金率" value={`${(contractDetail.margin_rate * 100).toFixed(0)}%`} /></Col>
            <Col span={8}><Statistic title="涨跌停板" value={`${(contractDetail.price_limit_pct * 100).toFixed(0)}%`} /></Col>
            <Col span={8}>
              <Statistic title="手续费(开)" value={contractDetail.commission_open}
                suffix={contractDetail.commission_type === "ratio" ? " (比例)" : "元/手"} />
            </Col>
          </Row>
          <div style={{ marginTop: 12 }}>
            <Text type="secondary">交易时间: {contractDetail.trading_hours}</Text>
          </div>
          {contractDetail.night_trading && contractDetail.night_trading !== "无夜盘" && (
            <div><Text type="secondary">夜盘: {contractDetail.night_trading}</Text></div>
          )}
        </Card>
      )}

      {mainContract && (
        <Card title="主力合约信息" size="small">
          <Row gutter={16}>
            <Col span={6}><Statistic title="当前主力" value={mainContract.main_contract} /></Col>
            <Col span={6}><Statistic title="交割月份" value={mainContract.parsed?.month || "-"} suffix="月" /></Col>
            <Col span={6}><Statistic title="交割年份" value={mainContract.parsed?.year || "-"} /></Col>
            <Col span={6}>
              <Text strong>后续合约:</Text>
              <div>{mainContract.contract_cycle?.join("  ") || "-"}</div>
            </Col>
          </Row>
        </Card>
      )}
    </div>
  );

  // ── Render: Exchanges ──
  const renderExchanges = () => (
    <Table
      dataSource={exchanges}
      columns={[
        { title: "交易所代码", dataIndex: "exchange", key: "exchange" },
        { title: "名称", dataIndex: "exchange_cn", key: "exchange_cn" },
        { title: "品种数", dataIndex: "count", key: "count" },
        {
          title: "品种列表", dataIndex: "symbols", key: "symbols",
          render: (v: string[]) => v?.map(s => <Tag key={s}>{s}</Tag>),
        },
      ]}
      rowKey="exchange"
      size="small"
      pagination={false}
    />
  );

  // ── Quick download helper ──
  const quickDownload = async (interval: string) => {
    message.loading({ content: `下载 ${interval}...`, key: "dl" });
    try {
      const res = await API.post("/download", null, {
        params: { symbol: selectedSymbol, interval },
      });
      message.success({ content: `${interval} 任务已创建`, key: "dl" });
      loadDownloadData();
    } catch { message.error({ content: "创建失败", key: "dl" }); }
  };

  const rangeDownload = async () => {
    if (!dlStartDate || !dlEndDate) {
      message.warning("请选择开始和结束日期");
      return;
    }
    message.loading({ content: "范围下载中...", key: "range" });
    try {
      const res = await API.post("/download/range", null, {
        params: {
          symbol: selectedSymbol,
          interval: dlInterval,
          start_date: dlStartDate,
          end_date: dlEndDate,
          contract: dlContract || undefined,
        },
      });
      setDlResult(res.data);
      if (res.data.bars > 0) {
        message.success({ content: `成功下载 ${res.data.bars} 条数据`, key: "range" });
      } else {
        message.info({ content: "未获取到数据（非交易时段或无数据）", key: "range" });
      }
      loadDownloadData();
    } catch (err: any) {
      message.error({ content: `下载失败: ${err.response?.data?.detail || err.message}`, key: "range" });
    }
  };

  // ── Batch download helpers ──
  const ALL_SYMBOLS = ["M","RB","CU","AU","AG","I","SC","CF","TA","MA","IF","C","Y","P","SR","RM","FG","SA","J","JM","HC","RU","NI","ZN","AL","PB","SN","EG","PP","L","V","PG","LH","AP","PK","CJ","SF","SM","UR","SP","SS","SI","LC","FU","BU","NR","LU","BC","A","B","CS","JD","EB","IH","IC","IM","T","TF","TS"];

  const startBatchDownload = async (daily: boolean, minute: boolean) => {
    if (batchSymbols.length === 0) {
      message.warning("请至少选择一个品种");
      return;
    }
    const label = daily && minute ? "全部" : daily ? "日周月" : "分钟小时";
    setBatchRunning(true);
    setBatchResults(null);
    message.loading({ content: `批量下载 ${label} 中...`, key: "batch" });
    try {
      const res = await API.post("/download/batch", null, {
        params: {
          symbols: batchSymbols.join(","),
          daily: daily ? "true" : "false",
          minute: minute ? "true" : "false",
        },
        timeout: 120000, // 2 min timeout for batch
      });
      setBatchResults(res.data);
      const totalBars = (res.data.daily_total_bars || 0) + (res.data.minute_total_bars || 0);
      message.success({ content: `批量完成！共下载 ${totalBars} 条数据`, key: "batch" });
      loadDownloadData();
    } catch (err: any) {
      message.error({ content: `批量下载失败: ${err.response?.data?.detail || err.message}`, key: "batch" });
    } finally {
      setBatchRunning(false);
    }
  };

  const selectAllSymbols = () => setBatchSymbols([...ALL_SYMBOLS]);
  const clearSymbols = () => setBatchSymbols([]);
  const addCommon = (group: string[]) => {
    const merged = [...new Set([...batchSymbols, ...group])];
    setBatchSymbols(merged);
  };

  // ── Stock / Option download helpers ──
  const STOCK_SEED = ["600019.SH","002110.SZ","601969.SH","601636.SH","000683.SZ",
    "601899.SH","600547.SH","002311.SZ","600737.SH","000800.SZ"];

  // 加载全部 A 股代码 (akshare 全市场枚举)
  const loadStockList = async () => {
    setStockListLoading(true);
    try {
      const res = await WH.get("/stocks/symbols", { params: { source: "akshare" }, timeout: 60000 });
      const codes: string[] = res.data?.symbols || [];
      setStockList(codes.map((c) => ({ value: c, label: c })));
      message.success(`已加载 ${codes.length} 只 A 股代码`);
    } catch (err: any) {
      message.error(`加载股票列表失败 (网络?): ${err.response?.data?.detail || err.message}`);
    } finally {
      setStockListLoading(false);
    }
  };

  // 单只股票全量下载 (从上市日起到当日) -> Parquet, 自动预览
  const downloadStockFull = async (symbol: string, interval = "1d") => {
    if (!symbol) { message.warning("请选择或填写代码"); return; }
    symbol = normStockCode(symbol);
    const end = dayjs().format("YYYY-MM-DD");
    message.loading({ content: "全量下载中 (上市日至今, 可能较久)...", key: "asset" });
    try {
      const res = await API.post("/download/range", null, {
        params: { symbol, interval, start_date: "1990-01-01", end_date: end, asset_type: "stock" },
        timeout: 180000,
      });
      if (res.data.bars > 0) {
        message.success({ content: `全量下载 ${res.data.bars} 条 (${res.data.source})，已加载预览`, key: "asset" });
        await autoPreview("stock", symbol, interval);
      } else {
        message.info({ content: "未获取到数据", key: "asset" });
      }
    } catch (err: any) {
      message.error({ content: `全量下载失败: ${err.response?.data?.detail || err.message}`, key: "asset" });
    }
  };

  // 全市场全量下载 -> DuckDB 仓库 (后台任务, 断点续传)
  const startMarketFullDownload = async (resetCheckpoint = false) => {
    try {
      const res = await WH.post("/collect/full", null, {
        params: { phase: "stocks", full_history: true, reset_checkpoint: resetCheckpoint },
      });
      message.success(`全市场全量采集已启动 (后台): ${res.data.job}`);
      pollProgress();
    } catch (err: any) {
      message.error(`启动失败: ${err.response?.data?.detail || err.message}`);
    }
  };

  // 单期权合约全量下载 (上市至今) -> Parquet, 自动预览
  const downloadOptionFull = async (contract: string) => {
    if (!contract) { message.warning("请选择或填写期权合约"); return; }
    const end = dayjs().format("YYYY-MM-DD");
    message.loading({ content: "期权全量下载中...", key: "asset" });
    try {
      const res = await API.post("/download/range", null, {
        params: { symbol: contract, interval: "1d", start_date: "2015-01-01",
          end_date: end, contract, asset_type: "option" },
        timeout: 120000,
      });
      if (res.data.bars > 0) {
        message.success({ content: `全量下载 ${res.data.bars} 条 (${res.data.source})，已加载预览`, key: "asset" });
        await autoPreview("option", contract, "1d", contract);
      } else {
        message.info({ content: "未获取到数据 (期权合约可能已到期/非交易时段)", key: "asset" });
      }
    } catch (err: any) {
      message.error({ content: `全量下载失败: ${err.response?.data?.detail || err.message}`, key: "asset" });
    }
  };

  // 全市场期权全量 -> DuckDB 仓库 (50/300/500ETF 全合约, 后台)
  const startOptionMarketFull = async (resetCheckpoint = false) => {
    try {
      const res = await WH.post("/collect/full", null, {
        params: { phase: "options", full_history: true, reset_checkpoint: resetCheckpoint },
      });
      message.success(`期权全市场全量采集已启动 (后台): ${res.data.job}`);
      pollProgress();
    } catch (err: any) {
      message.error(`启动失败: ${err.response?.data?.detail || err.message}`);
    }
  };

  const downloadAsset = async (symbol: string, interval: string,
    asset: "stock" | "option", contract?: string) => {
    if (!symbol) { message.warning("请填写代码"); return; }
    symbol = asset === "stock" ? normStockCode(symbol) : symbol;
    const end = dayjs().format("YYYY-MM-DD");
    const start = dayjs().subtract(5, "year").format("YYYY-MM-DD");
    message.loading({ content: "下载中...", key: "asset" });
    try {
      const res = await API.post("/download/range", null, {
        params: { symbol, interval, start_date: start, end_date: end,
          contract: contract || undefined, asset_type: asset },
        timeout: 60000,
      });
      if (res.data.bars > 0) {
        message.success({ content: `成功下载 ${res.data.bars} 条 (${res.data.source})，已自动加载预览`, key: "asset" });
        await autoPreview(asset, symbol, interval, contract);
      } else {
        message.info({ content: "未获取到数据", key: "asset" });
      }
    } catch (err: any) {
      message.error({ content: `下载失败: ${err.response?.data?.detail || err.message}`, key: "asset" });
    }
  };

  // 下载成功后: 预览类别跟随下载类别, 并直接拉取预览数据
  const autoPreview = async (asset: "futures" | "stock" | "option",
    symbol: string, interval: string, contract?: string) => {
    setPvAsset(asset);
    await loadPreviewFiles(asset);
    setPvLoading(true);
    try {
      const res = await API.get("/preview", {
        params: { symbol, interval, asset_type: asset, contract: contract || undefined, limit: 500 },
      });
      setPvData(res.data);
      // 选中文件下拉, 便于二次"预览"
      const path = res.data?.rows ? `data/market/${asset}/${symbol}/${contract || "main"}/${interval}.parquet` : "";
      if (path) setPvFile(path);
    } catch (err: any) {
      message.error(`自动预览失败: ${err.response?.data?.detail || err.message}`);
    } finally {
      setPvLoading(false);
    }
  };

  const loadOptionCodes = async (underlying: string) => {
    try {
      const res = await API.get("/options/codes", { params: { underlying } });
      setOptCodes(res.data?.codes || []);
      if (!res.data?.codes?.length) message.info("未获取到合约代码 (可能非交易时段)");
    } catch { message.error("获取期权合约失败"); }
  };

  // ── Preview helpers ──
  const loadPreviewFiles = async (asset: string) => {
    try {
      const res = await API.get("/data-files", { params: { asset_type: asset } });
      setPvFiles(res.data?.files || []);
    } catch { setPvFiles([]); }
  };

  const runPreview = async () => {
    const f = pvFiles.find((x) => x.path === pvFile);
    if (!f) { message.warning("请选择已下载的数据文件"); return; }
    setPvLoading(true);
    try {
      const res = await API.get("/preview", {
        params: { symbol: f.symbol, interval: f.interval, asset_type: pvAsset,
          contract: f.contract || undefined, limit: 200, offset: 0 },
      });
      setPvData(res.data);
    } catch (err: any) {
      message.error(`预览失败: ${err.response?.data?.detail || err.message}`);
      setPvData(null);
    } finally { setPvLoading(false); }
  };

  // ── Warehouse: 期货按品种+年份采集 ──
  const collectProduct = async () => {
    if (!whProduct) { message.warning("请选择品种"); return; }
    message.loading({ content: `采集 ${whProduct} ${whYear}-${whEndYear} 合约中...`, key: "wh" });
    try {
      await WH.post("/collect/product", null, {
        params: { product: whProduct, year: whYear, end_year: whEndYear,
          with_minute: false, start_date: fullStart || undefined },
      });
      message.success({ content: `${whProduct} 采集任务已启动`, key: "wh" });
      pollProgress();
    } catch (err: any) {
      const detail = err.response?.data?.detail || err.message;
      message.error({ content: `采集失败: ${detail}`, key: "wh" });
    }
  };

  // ── Warehouse: 枚举品种子合约 (含状态) ──
  const discoverContracts = async () => {
    setWhContractsLoading(true);
    try {
      const res = await WH.get("/contracts/discover", { params: { product: whProduct }, timeout: 30000 });
      setWhContracts(res.data?.contracts || []);
      if (!res.data?.contracts?.length) message.info("未枚举到合约 (网络?或非交易时段)");
    } catch (err: any) {
      message.error(`枚举失败: ${err.response?.data?.detail || err.message}`);
    } finally { setWhContractsLoading(false); }
  };

  // ── Warehouse: 刷新主力合约 (独立于下载) ──
  const refreshMain = async (product?: string) => {
    message.loading({ content: "刷新主力合约中...", key: "main" });
    try {
      const res = await WH.post("/main-contracts/refresh", null, {
        params: { product: product || undefined },
      });
      message.success({ content: `已刷新 ${res.data.count} 个品种主力`, key: "main" });
      loadMainContracts();
    } catch (err: any) {
      message.error({ content: `刷新失败: ${err.response?.data?.detail || err.message}`, key: "main" });
    }
  };

  const loadMainContracts = async () => {
    try {
      const res = await WH.get("/main-contracts");
      setMainContracts(res.data?.main_contracts || []);
    } catch { /* ignore */ }
  };

  // ── Warehouse: 全量/批量采集 ──
  const startFullCollect = async () => {
    message.loading({ content: "全量采集任务启动中...", key: "full" });
    try {
      await WH.post("/collect/full", null, {
        params: { phase: fullPhase, year: fullPhase === "futures" || fullPhase === "all" ? whYear : undefined,
          end_year: fullPhase === "futures" || fullPhase === "all" ? whEndYear : undefined,
          start_date: fullStart || undefined, with_minute: false, stock_limit: stockLimit },
      });
      message.success({ content: "全量采集任务已启动", key: "full" });
      pollProgress();
    } catch (err: any) {
      const detail = err.response?.data?.detail || err.message;
      message.error({ content: `启动失败: ${detail}`, key: "full" });
    }
  };

  const pollProgress = async () => {
    try {
      const res = await WH.get("/collect/progress");
      setCollectProgress(res.data);
      // 若仍在运行, 3秒后再查
      if (res.data?.job?.running) setTimeout(pollProgress, 3000);
    } catch { /* ignore */ }
  };

  // ── Warehouse: 按合约代码预览 ──
  const runWhPreview = async (code?: string) => {
    const c = code || whPvCode;
    if (!c) { message.warning("请输入合约代码"); return; }
    setWhPvLoading(true);
    try {
      const res = await WH.get("/preview", { params: { code: c, timeframe: whPvTf, limit: 200 } });
      setWhPvData(res.data);
      setWhPvCode(c);
    } catch (err: any) {
      message.error(`预览失败: ${err.response?.data?.detail || err.message}`);
      setWhPvData(null);
    } finally { setWhPvLoading(false); }
  };

  // ── Stock Knowledge Base ──
  const whAssetCount = (asset: string): number => {
    const row = (whStats?.by_asset_type || []).find((r: any) => r.asset_type === asset);
    return row?.symbols || 0;
  };

  const loadStockKnowledge = async () => {
    try {
      const res = await WH.get("/stocks/knowledge");
      setStockSectors(res.data?.sectors || []);
      setStockRelations(res.data?.relations || []);
    } catch (err: any) {
      message.error(`加载股票知识库失败: ${err.response?.data?.detail || err.message}`);
    }
  };

  const loadOptionsKnowledge = async () => {
    try {
      const res = await WH.get("/options/knowledge");
      setOptProducts(res.data?.products || []);
      setOptStrategies(res.data?.strategies || []);
    } catch (err: any) {
      message.error(`加载期权知识库失败: ${err.response?.data?.detail || err.message}`);
    }
  };

  const loadFundamental = async (symbol: string) => {
    if (!symbol) { message.warning("请填写股票代码"); return; }
    symbol = normStockCode(symbol);
    setFundLoading(true);
    try {
      const res = await WH.get("/stocks/fundamental", { params: { symbol } });
      setFundData(res.data);
      if (!res.data?.info && !res.data?.financial?.length) {
        message.info("仓库暂无该股基本面，点击「采集基本面」获取");
      }
    } catch (err: any) {
      setFundData(null);
      message.error(`查询失败: ${err.response?.data?.detail || err.message}`);
    } finally { setFundLoading(false); }
  };

  const collectFundamental = async (symbol: string) => {
    if (!symbol) { message.warning("请填写股票代码"); return; }
    symbol = normStockCode(symbol);
    message.loading({ content: "采集基本面中...", key: "fund" });
    try {
      const res = await WH.post("/stocks/fundamental/collect", null, { params: { symbol }, timeout: 60000 });
      message.success({ content: `信息${res.data.info_written}行 / 财务${res.data.financial_periods}期，已刷新`, key: "fund" });
      await loadFundamental(symbol);
    } catch (err: any) {
      message.error({ content: `采集失败 (网络?): ${err.response?.data?.detail || err.message}`, key: "fund" });
    }
  };

  // ── Render: Stock Knowledge Base ──
  const renderStockKnowledge = () => (
    <div>
      {/* 个股基本面查询 */}
      <Card title={<span><RiseOutlined /> 个股基本面 (K线之外的分析维度)</span>}
        size="small" style={{ marginBottom: 16 }}>
        <Space style={{ marginBottom: 12 }} wrap>
          <Input style={{ width: 200 }} placeholder="股票代码 如 600019.SH" value={fundSymbol}
            onChange={(e) => setFundSymbol(e.target.value.trim())} allowClear />
          <Button type="primary" loading={fundLoading} onClick={() => loadFundamental(fundSymbol)}>查询</Button>
          <Button onClick={() => collectFundamental(fundSymbol)}>采集基本面</Button>
        </Space>
        {fundData?.info && (
          <Row gutter={16} style={{ marginBottom: 12 }}>
            <Col span={5}><Statistic title="公司" valueStyle={{ fontSize: 14 }}
              value={fundData.info.company_name || "-"} /></Col>
            <Col span={4}><Statistic title="行业" valueStyle={{ fontSize: 14 }}
              value={fundData.info.industry || "-"} /></Col>
            <Col span={5}><Statistic title="上市日" valueStyle={{ fontSize: 14 }}
              value={String(fundData.info.listing_date || "-").slice(0, 10)} /></Col>
            <Col span={5}><Statistic title="总市值(亿)" valueStyle={{ fontSize: 14 }}
              value={fundData.info.market_cap ? (Number(fundData.info.market_cap) / 1e8).toFixed(1) : "-"} /></Col>
            <Col span={5}><Statistic title="总股本(亿)" valueStyle={{ fontSize: 14 }}
              value={fundData.info.total_shares ? (Number(fundData.info.total_shares) / 1e8).toFixed(2) : "-"} /></Col>
          </Row>
        )}
        {fundData?.financial?.length > 0 && (
          <Table size="small" dataSource={fundData.financial} rowKey={(_: any, i?: number) => String(i)}
            pagination={{ pageSize: 8 }}
            columns={[
              { title: "报告期", dataIndex: "report_date", render: (v: string) => String(v).slice(0, 10) },
              { title: "类型", dataIndex: "report_type" },
              { title: "营收", dataIndex: "revenue", render: fmtPrice },
              { title: "净利润", dataIndex: "net_profit", render: fmtPrice },
              { title: "EPS", dataIndex: "eps", render: fmtPrice },
              { title: "ROE%", dataIndex: "roe", render: fmtPrice },
              { title: "毛利率%", dataIndex: "gross_margin", render: fmtPrice },
              { title: "净利率%", dataIndex: "net_margin", render: fmtPrice },
            ]} />
        )}
      </Card>

      {/* 行业板块 ↔ 期货联动 */}
      <Card title={<span><BookOutlined /> 行业板块知识库 + 期货联动映射</span>} size="small"
        extra={<Button size="small" onClick={loadStockKnowledge}>加载/刷新</Button>}>
        {stockSectors.length === 0 && (
          <Text type="secondary">点击右上角「加载/刷新」查看行业知识库</Text>
        )}
        {stockSectors.map((s) => (
          <Card key={s.code} size="small" style={{ marginBottom: 10 }}
            title={<span>{s.name} <Text type="secondary" style={{ fontSize: 12 }}>({s.index_code})</Text></span>}>
            <div style={{ marginBottom: 6 }}>
              <Text strong>关联期货: </Text>
              {(s.related_futures || []).map((f: string) => <Tag key={f} color="blue">{f}</Tag>)}
            </div>
            {s.chars?.length > 0 && (
              <div style={{ marginBottom: 6 }}>
                <Text strong>特点: </Text>
                {s.chars.map((c: string, i: number) => <Tag key={i}>{c}</Tag>)}
              </div>
            )}
            {s.macro_sensitivity && Object.keys(s.macro_sensitivity).length > 0 && (
              <div style={{ marginBottom: 6 }}>
                <Text strong>宏观敏感度: </Text>
                {Object.entries(s.macro_sensitivity).map(([k, v]: any) =>
                  <Tag key={k} color={v >= 0.8 ? "red" : "orange"}>{k}: {v}</Tag>)}
              </div>
            )}
            {(stockRelations.filter((r) => r.sector === s.name)).map((r, i) => (
              <div key={i} style={{ fontSize: 12, color: "#888", marginTop: 4 }}>
                <Tag color="purple">{r.lead_lag}</Tag>相关性≈{r.correlation} — {r.logic}
              </div>
            ))}
          </Card>
        ))}
      </Card>
    </div>
  );

  // ── Render: Options Knowledge Base ──
  const renderOptionsKnowledge = () => (
    <div>
      <Card title={<span><SafetyOutlined /> 期权知识库 (标的特征 + 策略)</span>} size="small"
        extra={<Button size="small" onClick={loadOptionsKnowledge}>加载/刷新</Button>}>
        {optProducts.length === 0 && (
          <Text type="secondary">点击右上角「加载/刷新」查看期权标的特征与策略库</Text>
        )}
        {optProducts.length > 0 && (
          <>
            <Text strong style={{ fontSize: 13 }}>标的市场特征</Text>
            <Table size="small" style={{ marginTop: 8, marginBottom: 16 }}
              dataSource={optProducts} rowKey="underlying" pagination={false}
              columns={[
                { title: "标的", dataIndex: "underlying" },
                { title: "类型", dataIndex: "underlying_type" },
                { title: "行权", dataIndex: "exercise_style" },
                { title: "IV区间%", key: "iv", render: (_: any, r: any) =>
                    r.iv_range ? `${r.iv_range[0]}~${r.iv_range[1]}` : "-" },
                { title: "流动性", dataIndex: "liquidity" },
                { title: "关联期货", key: "rf", render: (_: any, r: any) =>
                    (r.related_futures || []).join(",") || "-" },
                { title: "特点", key: "chars", render: (_: any, r: any) =>
                    (r.chars || []).map((c: string, i: number) => <Tag key={i}>{c}</Tag>) },
              ]} />
            <Text strong style={{ fontSize: 13 }}>策略库 (适用场景 / IV环境)</Text>
            <Table size="small" style={{ marginTop: 8 }}
              dataSource={optStrategies} rowKey="name" pagination={false}
              columns={[
                { title: "策略", dataIndex: "chinese_name" },
                { title: "适用市场", dataIndex: "market_view" },
                { title: "IV环境", dataIndex: "iv_env" },
                { title: "构成", key: "comp", render: (_: any, r: any) =>
                    (r.components || []).join(" + ") },
                { title: "Greeks", key: "g", render: (_: any, r: any) =>
                    Object.entries(r.greeks_profile || {}).map(([k, v]: any) =>
                      <Tag key={k}>{k}:{v}</Tag>) },
              ]} />
          </>
        )}
      </Card>
    </div>
  );

  // ── Render: Download Manager ──
  const renderDownload = () => (
    <div>
      <Card size="small" style={{ marginBottom: 16 }}>
        <Space align="center">
          <Text strong>资产类别:</Text>
          <Select value={assetType} onChange={(v) => setAssetType(v)} style={{ width: 140 }}>
            <Select.Option value="futures">期货</Select.Option>
            <Select.Option value="stock">股票</Select.Option>
            <Select.Option value="option">期权</Select.Option>
          </Select>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {assetType === "futures" ? "中国期货 (akshare)"
              : assetType === "stock" ? "A股 (BaoStock 前复权日线)"
              : "中国期权 (ETF/股指期权日线)"}
          </Text>
        </Space>
      </Card>

      {/* 股票下载 */}
      {assetType === "stock" && (
        <Card title="股票下载" size="small" style={{ marginBottom: 16 }}>
          <Row gutter={[12, 12]} align="middle">
            <Col span={2}><Text strong>代码:</Text></Col>
            <Col span={6}>
              <Select
                style={{ width: "100%" }}
                showSearch
                value={stockSymbol}
                onChange={setStockSymbol}
                loading={stockListLoading}
                placeholder="选择股票 (可搜索代码)"
                filterOption={(input, opt) =>
                  String(opt?.value ?? "").toLowerCase().includes(input.toLowerCase())}
                options={stockList.length ? stockList : STOCK_SEED.map((s) => ({ value: s, label: s }))}
              />
            </Col>
            <Col>
              <Button size="small" loading={stockListLoading} onClick={loadStockList}>
                加载全部代码
              </Button>
            </Col>
            <Col span={4}>
              <Input placeholder="或输入 600519.SH"
                onPressEnter={(e) => setStockSymbol((e.target as HTMLInputElement).value.trim())}
                onBlur={(e) => e.target.value && setStockSymbol(e.target.value.trim())}
                allowClear />
            </Col>
          </Row>
          <Row gutter={[12, 12]} align="middle" style={{ marginTop: 10 }}>
            <Col span={2}><Text type="secondary" style={{ fontSize: 12 }}>近5年:</Text></Col>
            <Col>
              <Button type="primary" size="small" icon={<DownloadOutlined />}
                onClick={() => downloadAsset(stockSymbol, "1d", "stock")}>日线</Button>
            </Col>
            <Col>
              <Button size="small" icon={<DownloadOutlined />}
                onClick={() => downloadAsset(stockSymbol, "1w", "stock")}>周线</Button>
            </Col>
            <Col>
              <Button size="small" icon={<DownloadOutlined />}
                onClick={() => downloadAsset(stockSymbol, "30m", "stock")}>M30</Button>
            </Col>
            <Col span={3}><Text type="secondary" style={{ fontSize: 12 }}>全历史:</Text></Col>
            <Col>
              <Button size="small" icon={<DownloadOutlined />}
                style={{ background: "#722ed1", borderColor: "#722ed1", color: "#fff" }}
                onClick={() => downloadStockFull(stockSymbol, "1d")}>本只全量 (上市至今)</Button>
            </Col>
          </Row>
          <Row style={{ marginTop: 10 }}>
            <Col span={24}>
              <Card size="small" style={{ background: "#f9f0ff", borderColor: "#d3adf7" }}>
                <Space wrap>
                  <Text strong style={{ color: "#722ed1" }}>全市场全量下载</Text>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    全部 A 股从上市日至今 → DuckDB 仓库 (断点续传, 防限流/中断)。初始化或定期校验用，耗时较长。
                  </Text>
                  <Button size="small" type="primary"
                    style={{ background: "#722ed1", borderColor: "#722ed1" }}
                    onClick={() => startMarketFullDownload(false)}>启动全市场全量</Button>
                  <Button size="small" danger onClick={() => startMarketFullDownload(true)}>
                    清空进度后全量 (校验补漏)
                  </Button>
                  <Button size="small" onClick={pollProgress}>刷新进度</Button>
                </Space>
                {collectProgress && (
                  <div style={{ marginTop: 8 }}>
                    <Badge status={collectProgress.job?.running ? "processing" : "success"}
                      text={collectProgress.job?.running
                        ? `运行中: ${collectProgress.job?.name || ""}` : "空闲"} />
                    <Text type="secondary" style={{ marginLeft: 12 }}>
                      已完成 {collectProgress.checkpoint?.done || 0} 项
                      {collectProgress.checkpoint?.failures > 0
                        ? ` · 失败 ${collectProgress.checkpoint.failures}` : ""}
                    </Text>
                  </div>
                )}
              </Card>
            </Col>
          </Row>
        </Card>
      )}

      {/* 期权下载 */}
      {assetType === "option" && (
        <Card title="期权下载" size="small" style={{ marginBottom: 16 }}>
          <Row gutter={[12, 12]} align="middle">
            <Col span={2}><Text strong>标的:</Text></Col>
            <Col span={4}>
              <Select style={{ width: "100%" }} value={optUnderlying}
                onChange={(v) => { setOptUnderlying(v); setOptContract(""); }}>
                <Select.Option value="510050">50ETF (510050)</Select.Option>
                <Select.Option value="510300">300ETF (510300)</Select.Option>
                <Select.Option value="510500">500ETF (510500)</Select.Option>
                <Select.Option value="IO">沪深300股指 (IO)</Select.Option>
                <Select.Option value="HO">上证50股指 (HO)</Select.Option>
              </Select>
            </Col>
            <Col>
              <Button size="small" onClick={() => loadOptionCodes(optUnderlying)}>
                获取合约列表
              </Button>
            </Col>
            <Col span={6}>
              <Select style={{ width: "100%" }} showSearch placeholder="选择期权合约"
                value={optContract || undefined} onChange={setOptContract}
                options={optCodes.map((c) => ({ value: c, label: c }))} />
            </Col>
            <Col span={4}>
              <Input placeholder="或直接输入合约代码"
                onBlur={(e) => e.target.value && setOptContract(e.target.value.trim())}
                allowClear />
            </Col>
            <Col>
              <Button type="primary" size="small" icon={<DownloadOutlined />}
                onClick={() => downloadAsset(optContract, "1d", "option", optContract)}>
                下载日线 (近5年)
              </Button>
            </Col>
            <Col>
              <Button size="small" icon={<DownloadOutlined />}
                style={{ background: "#722ed1", borderColor: "#722ed1", color: "#fff" }}
                onClick={() => downloadOptionFull(optContract)}>本合约全量</Button>
            </Col>
          </Row>
          <Row style={{ marginTop: 10 }}>
            <Col span={24}>
              <Card size="small" style={{ background: "#f9f0ff", borderColor: "#d3adf7" }}>
                <Space wrap>
                  <Text strong style={{ color: "#722ed1" }}>期权全市场全量下载</Text>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    50/300/500ETF 全部期权合约 (看涨+看跌) → DuckDB 仓库 (断点续传)。初始化或定期校验用。
                  </Text>
                  <Button size="small" type="primary"
                    style={{ background: "#722ed1", borderColor: "#722ed1" }}
                    onClick={() => startOptionMarketFull(false)}>启动期权全量</Button>
                  <Button size="small" danger onClick={() => startOptionMarketFull(true)}>
                    清空进度后全量 (校验补漏)
                  </Button>
                  <Button size="small" onClick={pollProgress}>刷新进度</Button>
                </Space>
                {collectProgress && (
                  <div style={{ marginTop: 8 }}>
                    <Badge status={collectProgress.job?.running ? "processing" : "success"}
                      text={collectProgress.job?.running
                        ? `运行中: ${collectProgress.job?.name || ""}` : "空闲"} />
                    <Text type="secondary" style={{ marginLeft: 12 }}>
                      已完成 {collectProgress.checkpoint?.done || 0} 项
                      {collectProgress.checkpoint?.failures > 0
                        ? ` · 失败 ${collectProgress.checkpoint.failures}` : ""}
                    </Text>
                  </div>
                )}
              </Card>
            </Col>
          </Row>
        </Card>
      )}

      {/* 快捷下载 (期货) */}
      {assetType === "futures" && (
      <>
      {/* 期货按品种+年份采集 → 统一仓库 */}
      <Card title="按品种采集 → 统一仓库" size="small" style={{ marginBottom: 16 }}
        extra={<Text type="secondary" style={{ fontSize: 11 }}>选品种+年份 → 生成 M2601~M2612 全月份合约，无数据的自然为空</Text>}>
        <Row gutter={[12, 12]} align="middle">
          <Col span={2}><Text strong>品种:</Text></Col>
          <Col span={3}>
            <Select style={{ width: "100%" }} showSearch value={whProduct} onChange={setWhProduct}
              options={ALL_SYMBOLS.map((s) => ({ value: s, label: s }))} />
          </Col>
          <Col span={2}><Text strong>年份:</Text></Col>
          <Col span={3}>
            <Select style={{ width: "100%" }} value={whYear} onChange={setWhYear}
              options={Array.from({ length: 17 }, (_, i) => 2010 + i).map((y) => ({ value: y, label: String(y) }))} />
          </Col>
          <Col><Text type="secondary">至</Text></Col>
          <Col span={3}>
            <Select style={{ width: "100%" }} value={whEndYear} onChange={setWhEndYear}
              options={Array.from({ length: 17 }, (_, i) => 2010 + i).map((y) => ({ value: y, label: String(y) }))} />
          </Col>
          <Col>
            <Button type="primary" icon={<DownloadOutlined />} onClick={collectProduct}>
              采集到仓库
            </Button>
          </Col>
          <Col>
            <Button loading={whContractsLoading} onClick={discoverContracts}>
              枚举合约 (看状态)
            </Button>
          </Col>
        </Row>
        <Row style={{ marginTop: 8 }}>
          <Col span={3}><Text type="secondary" style={{ fontSize: 12 }}>起始日期(可选):</Text></Col>
          <Col span={4}>
            <DatePicker size="small" style={{ width: "100%" }} placeholder="测试可填近1月"
              value={fullStart ? dayjs(fullStart) : null}
              onChange={(d) => setFullStart(d ? d.format("YYYY-MM-DD") : "")} />
          </Col>
          <Col><Text type="secondary" style={{ fontSize: 11 }}>留空=该年全部数据；不判断主力</Text></Col>
        </Row>
        {whContracts.length > 0 && (
          <div style={{ marginTop: 12 }}>
            <Text type="secondary" style={{ fontSize: 12 }}>
              {whProduct} 当前合约 ({whContracts.length}个) — 点代码可预览:
            </Text>
            <div style={{ marginTop: 6 }}>
              {whContracts.map((c: any) => (
                <Tag key={c.code} style={{ marginBottom: 6, cursor: "pointer" }}
                  color={c.is_main ? "gold" : c.status === "已到期" ? "default" : "blue"}
                  onClick={() => runWhPreview(c.code)}>
                  {c.code}
                  {c.is_main ? " ★主力" : ""}
                  <span style={{ marginLeft: 4, opacity: 0.7 }}>
                    {c.status === "已到期" ? "·已到期" : "·在挂"}
                  </span>
                </Tag>
              ))}
            </div>
          </div>
        )}
      </Card>

      {/* 主力合约 (独立于下载, 供交易流程判断) */}
      <Card title="主力合约标注" size="small" style={{ marginBottom: 16 }}
        extra={<Text type="secondary" style={{ fontSize: 11 }}>按最新持仓量计算，与下载解耦</Text>}>
        <Space style={{ marginBottom: 8 }}>
          <Button onClick={() => refreshMain(whProduct)}>刷新 {whProduct} 主力</Button>
          <Button type="primary" ghost onClick={() => refreshMain()}>刷新全部品种主力</Button>
          <Button onClick={loadMainContracts}>查看当前主力</Button>
        </Space>
        {mainContracts.length > 0 && (
          <div>
            {mainContracts.map((m: any) => (
              <Tag key={m.product} color="gold" style={{ cursor: "pointer", marginBottom: 4 }}
                onClick={() => runWhPreview(m.main)}>
                {m.product} → {m.main}
              </Tag>
            ))}
          </div>
        )}
      </Card>

      {/* 全量/批量采集 → 仓库 (带进度) */}
      <Card title="全量历史采集 → 统一仓库" size="small" style={{ marginBottom: 16 }}>
        <Row gutter={[12, 12]} align="middle">
          <Col span={2}><Text strong>范围:</Text></Col>
          <Col span={4}>
            <Select style={{ width: "100%" }} value={fullPhase} onChange={setFullPhase}>
              <Select.Option value="futures">期货 (全品种)</Select.Option>
              <Select.Option value="stocks">股票</Select.Option>
              <Select.Option value="options">期权</Select.Option>
              <Select.Option value="all">全部</Select.Option>
            </Select>
          </Col>
          <Col span={3}>
            <DatePicker style={{ width: "100%" }} placeholder="起始(留空=近1月)"
              value={fullStart ? dayjs(fullStart) : null}
              onChange={(d) => setFullStart(d ? d.format("YYYY-MM-DD") : "")} />
          </Col>
          <Col span={3}>
            <Input type="number" addonBefore="股票限量" value={stockLimit}
              onChange={(e) => setStockLimit(Number(e.target.value) || 0)} />
          </Col>
          <Col>
            <Button type="primary" style={{ background: "#722ed1", borderColor: "#722ed1" }}
              icon={<DownloadOutlined />} onClick={startFullCollect}>
              开始全量采集
            </Button>
          </Col>
          <Col>
            <Button onClick={pollProgress}>刷新进度</Button>
          </Col>
          <Col><Text type="secondary" style={{ fontSize: 11 }}>测试: 起始留空=近1月, 股票限量50; 生产填0=全市场</Text></Col>
        </Row>

        {collectProgress && (
          <div style={{ marginTop: 12 }}>
            <Space>
              <Badge status={collectProgress.job?.running ? "processing" : "success"}
                text={collectProgress.job?.running ? `运行中: ${collectProgress.job?.name || ""}` : "空闲"} />
              <Text type="secondary">已完成 {collectProgress.checkpoint?.done || 0} 项</Text>
              {collectProgress.checkpoint?.failures > 0 &&
                <Text type="danger">失败 {collectProgress.checkpoint.failures} 项</Text>}
            </Space>
            {collectProgress.job?.error &&
              <div><Text type="danger" style={{ fontSize: 12 }}>错误: {collectProgress.job.error}</Text></div>}
            {!collectProgress.job?.running && collectProgress.job?.result &&
              <div><Text type="success" style={{ fontSize: 12 }}>
                结果: {JSON.stringify(collectProgress.job.result)}</Text></div>}
          </div>
        )}
      </Card>

      {/* 仓库数据预览 (按合约代码) */}
      <Card title={<span><SearchOutlined /> 仓库数据预览 (校验子合约数据)</span>}
        size="small" style={{ marginBottom: 16 }}>
        <Row gutter={[12, 12]} align="middle">
          <Col span={4}>
            <Input placeholder="合约代码 如 RB2610" value={whPvCode}
              onChange={(e) => setWhPvCode(e.target.value.trim())} allowClear />
          </Col>
          <Col span={3}>
            <Select style={{ width: "100%" }} value={whPvTf} onChange={setWhPvTf}>
              <Select.Option value="D1">日线</Select.Option>
              <Select.Option value="M5">5分钟</Select.Option>
            </Select>
          </Col>
          <Col>
            <Button type="primary" loading={whPvLoading} onClick={() => runWhPreview()}>预览</Button>
          </Col>
        </Row>
        {whPvData && renderWhPreviewBody(whPvData)}
      </Card>

      {/* 快捷下载 (期货) */}
      <Card title="快捷下载" size="small" style={{ marginBottom: 16 }}>
        <Row gutter={[12, 12]} align="middle">
          <Col span={2}>
            <Text strong>品种:</Text>
          </Col>
          <Col span={3}>
            <Select
              style={{ width: "100%" }}
              value={selectedSymbol}
              onChange={setSelectedSymbol}
            >
              {["M","RB","CU","AU","AG","I","SC","CF","TA","MA","IF","C","Y","P","SR","RM","FG","SA","J","JM","HC","RU","NI","ZN","AL","PB","SN","EG","PP","L","V","PG","LH","AP","PK","CJ","SF","SM","UR","SP","SS","SI","LC","FU","BU","NR","LU","BC","A","B","CS","JD","EB","IH","IC","IM","T","TF","TS"].map(sym => (
                <Select.Option key={sym} value={sym}>{sym}</Select.Option>
              ))}
            </Select>
          </Col>
          <Col>
            <Button type="primary" size="small" icon={<DownloadOutlined />}
              onClick={() => quickDownload("1d")}>
              日线
            </Button>
          </Col>
          <Col>
            <Button size="small" icon={<DownloadOutlined />}
              onClick={() => quickDownload("5m")}>
              M5
            </Button>
          </Col>
          <Col>
            <Button size="small" icon={<DownloadOutlined />}
              onClick={() => quickDownload("15m")}>
              M15
            </Button>
          </Col>
          <Col>
            <Button size="small" icon={<DownloadOutlined />}
              onClick={() => quickDownload("30m")}>
              M30
            </Button>
          </Col>
          <Col>
            <Button size="small" icon={<DownloadOutlined />}
              onClick={() => quickDownload("60m")}>
              1H
            </Button>
          </Col>
          <Col>
            <Button size="small" icon={<DownloadOutlined />}
              onClick={() => quickDownload("1w")}>
              周线
            </Button>
          </Col>
        </Row>
      </Card>

      {/* 日期范围下载 */}
      <Card title="范围下载 (精确日期选择)" size="small" style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col span={4}>
            <div>
              <Text type="secondary" style={{ fontSize: 12 }}>开始日期</Text>
              <DatePicker
                style={{ width: "100%" }}
                value={dlStartDate ? dayjs(dlStartDate) : null}
                onChange={(d) => setDlStartDate(d ? d.format("YYYY-MM-DD") : "")}
                placeholder="选择开始日期"
              />
            </div>
          </Col>
          <Col span={4}>
            <div>
              <Text type="secondary" style={{ fontSize: 12 }}>结束日期</Text>
              <DatePicker
                style={{ width: "100%" }}
                value={dlEndDate ? dayjs(dlEndDate) : null}
                onChange={(d) => setDlEndDate(d ? d.format("YYYY-MM-DD") : "")}
                placeholder="选择结束日期"
              />
            </div>
          </Col>
          <Col span={3}>
            <div>
              <Text type="secondary" style={{ fontSize: 12 }}>周期</Text>
              <Select
                style={{ width: "100%" }}
                value={dlInterval}
                onChange={setDlInterval}
              >
                <Select.Option value="1d">日线</Select.Option>
                <Select.Option value="5m">5分钟</Select.Option>
                <Select.Option value="15m">15分钟</Select.Option>
                <Select.Option value="30m">30分钟</Select.Option>
                <Select.Option value="60m">60分钟</Select.Option>
                <Select.Option value="1w">周线</Select.Option>
                <Select.Option value="1M">月线</Select.Option>
              </Select>
            </div>
          </Col>
          <Col span={3}>
            <div>
              <Text type="secondary" style={{ fontSize: 12 }}>合约 (可选)</Text>
              <Input
                placeholder="如 M2609"
                value={dlContract}
                onChange={(e) => setDlContract(e.target.value)}
                allowClear
              />
            </div>
          </Col>
          <Col>
            <Space direction="vertical" style={{ marginTop: 14 }}>
              <Button type="primary" icon={<DownloadOutlined />} onClick={rangeDownload}>
                开始范围下载
              </Button>
              <Text type="secondary" style={{ fontSize: 11 }}>
                分钟级支持近3个月
              </Text>
            </Space>
          </Col>

          {/* 下载结果展示 */}
          {dlResult && (
            <Col span={24}>
              <Card size="small" style={{ background: "#f6ffed", borderColor: "#b7eb8f" }}>
                <Row gutter={24}>
                  <Col span={4}>
                    <Statistic title="下载数据量" value={dlResult.bars} suffix="条" valueStyle={{ color: "#52c41a" }} />
                  </Col>
                  <Col span={4}>
                    <Statistic title="数据源" value={dlResult.source || "-"} />
                  </Col>
                  <Col span={6}>
                    <Statistic title="时间范围"
                      value={dlResult.start ? `${dlResult.start?.slice(0, 10)} ~ ${dlResult.end?.slice(0, 10)}` : "-"} />
                  </Col>
                  <Col span={4}>
                    <Statistic title="状态" value={dlResult.status === "completed" ? "✅ 成功" : "⚠️ 无数据"}
                      valueStyle={{ color: dlResult.status === "completed" ? "#52c41a" : "#faad14" }} />
                  </Col>
                  <Col>
                    <Button size="small" onClick={() => setDlResult(null)}>关闭</Button>
                  </Col>
                </Row>
              </Card>
            </Col>
          )}
        </Row>
      </Card>

      {/* 批量下载 — 多品种 × 多周期 */}
      <Card title="批量下载 (多品种)" size="small" style={{ marginBottom: 16 }}
        extra={
          <Space size="small">
            <Button size="small" onClick={selectAllSymbols}>全选</Button>
            <Button size="small" onClick={clearSymbols}>清空</Button>
            <Button size="small" onClick={() => addCommon(["M","RB","CU","AU","AG","I","SC"])}>热门</Button>
            <Button size="small" onClick={() => addCommon(["IF","IH","IC","IM","T","TF"])}>金融</Button>
            <Button size="small" onClick={() => addCommon(["MA","TA","SA","FG","RM","OI","CF","SR"])}>化工</Button>
          </Space>
        }>
        <Row gutter={[12, 12]}>
          <Col span={24}>
            <Select
              mode="multiple"
              style={{ width: "100%" }}
              placeholder="选择需要批量下载的品种"
              value={batchSymbols}
              onChange={setBatchSymbols}
              maxTagCount={8}
            >
              {ALL_SYMBOLS.map(sym => (
                <Select.Option key={sym} value={sym}>{sym}</Select.Option>
              ))}
            </Select>
          </Col>
          <Col>
            <Space size="middle" align="center">
              <Button
                type="primary"
                icon={<DownloadOutlined />}
                loading={batchRunning}
                onClick={() => startBatchDownload(true, false)}
              >
                下载日周月 (近1年)
              </Button>
              <Button
                type="primary"
                ghost
                icon={<DownloadOutlined />}
                loading={batchRunning}
                onClick={() => startBatchDownload(false, true)}
              >
                下载分钟小时 (近3月)
              </Button>
              <Button
                type="primary"
                style={{ background: "#722ed1", borderColor: "#722ed1" }}
                icon={<DownloadOutlined />}
                loading={batchRunning}
                onClick={() => startBatchDownload(true, true)}
              >
                下载全部
              </Button>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {batchSymbols.length} 个品种 → 共 {batchSymbols.length * 3} (日周月) + {batchSymbols.length * 4} (分钟级) 个任务
              </Text>
            </Space>
          </Col>

          {/* 批量下载结果 */}
          {batchResults && (
            <Col span={24}>
              <Card size="small" style={{ background: batchResults.daily_success + batchResults.minute_success > 0 ? "#f6ffed" : "#fff7e6", borderColor: "#b7eb8f" }}>
                <Row gutter={[16, 16]}>
                  <Col span={4}>
                    <Statistic title="品种数" value={batchResults.total_symbols} />
                  </Col>
                  <Col span={5}>
                    <Statistic title="日周月 成功/总数"
                      value={`${batchResults.daily_success || 0} / ${batchResults.daily_total || 0}`}
                      valueStyle={{ color: batchResults.daily_success === batchResults.daily_total ? "#52c41a" : "#faad14" }} />
                  </Col>
                  <Col span={5}>
                    <Statistic title="分钟级 成功/总数"
                      value={`${batchResults.minute_success || 0} / ${batchResults.minute_total || 0}`}
                      valueStyle={{ color: batchResults.minute_success === batchResults.minute_total ? "#52c41a" : "#faad14" }} />
                  </Col>
                  <Col span={4}>
                    <Statistic title="日周月 数据量" value={batchResults.daily_total_bars || 0} suffix="条" />
                  </Col>
                  <Col span={4}>
                    <Statistic title="分钟级 数据量" value={batchResults.minute_total_bars || 0} suffix="条" />
                  </Col>
                  <Col span={24}>
                    <Table
                      dataSource={[
                        ...(batchResults.daily || []),
                        ...(batchResults.minute || []),
                      ]}
                      columns={[
                        { title: "品种", dataIndex: "symbol", key: "symbol", width: 60 },
                        { title: "周期", dataIndex: "interval", key: "interval", width: 60 },
                        { title: "合约", dataIndex: "contract", key: "contract", width: 70,
                          render: (v: any) => v || "主力" },
                        { title: "数据量", dataIndex: "bars", key: "bars", width: 70 },
                        { title: "状态", dataIndex: "status", key: "status", width: 80,
                          render: (v: string) =>
                            <Tag color={v === "completed" ? "green" : v === "failed" ? "red" : "blue"}>
                              {v === "completed" ? "✅" : v === "failed" ? "❌" : v}
                            </Tag> },
                        { title: "日期范围", key: "range",
                          render: (_: any, r: any) =>
                            r.start_date && r.end_date ? `${r.start_date} ~ ${r.end_date}` : "-" },
                      ]}
                      rowKey={(r: any) => `${r.symbol}_${r.interval}`}
                      size="small"
                      pagination={{ pageSize: 10 }}
                    />
                  </Col>
                  <Col>
                    <Button size="small" onClick={() => setBatchResults(null)}>关闭结果</Button>
                  </Col>
                </Row>
              </Card>
            </Col>
          )}
        </Row>
      </Card>
      </>
      )}

      {/* 统计和同步操作 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col>
          <Button icon={<SyncOutlined />}
            onClick={async () => {
              try {
                await API.post("/sync/start");
                message.success("实时同步已启动");
              } catch { message.error("启动失败"); }
            }}>
            启动同步
          </Button>
        </Col>
        <Col>
          <Button onClick={loadDownloadData}>刷新状态</Button>
        </Col>
      </Row>

      {/* 统计卡片 */}
      {downloadStats && (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}><Statistic title="总任务" value={downloadStats.total_tasks} /></Col>
          <Col span={6}><Statistic title="已完成" value={downloadStats.completed} valueStyle={{ color: "#52c41a" }} /></Col>
          <Col span={6}><Statistic title="失败" value={downloadStats.failed} valueStyle={{ color: "#ff4d4f" }} /></Col>
          <Col span={6}><Statistic title="数据条数" value={downloadStats.total_bars_downloaded} /></Col>
        </Row>
      )}

      {/* 下载历史表格 */}
      <Table
        dataSource={downloadHistory}
        columns={[
          { title: "品种", dataIndex: "symbol", key: "symbol" },
          { title: "周期", dataIndex: "interval", key: "interval" },
          { title: "合约", dataIndex: "contract", key: "contract", render: (v: any) => v || "主力" },
          { title: "日期范围", key: "range",
            render: (_: any, r: any) => r.start_date && r.end_date ? `${r.start_date} ~ ${r.end_date}` : "-" },
          { title: "状态", dataIndex: "status", key: "status",
            render: (v: string) => <Tag color={v === "completed" ? "green" : v === "failed" ? "red" : "blue"}>{v}</Tag> },
          { title: "数据条数", dataIndex: "downloaded_bars", key: "bars" },
          { title: "进度", dataIndex: "progress", key: "progress",
            render: (v: number) => <Progress percent={v} size="small" /> },
        ]}
        rowKey="id"
        size="small"
        pagination={{ pageSize: 5 }}
      />

      {renderPreview()}
    </div>
  );

  // ── Render: Data Preview (table + chart + quality) ──
  const renderPreview = () => {
    const q = pvData?.quality;
    const closes: number[] = pvData?.chart?.close || [];
    return (
      <Card title={<span><SearchOutlined /> 数据预览 (校验下载数据)</span>}
        size="small" style={{ marginTop: 16 }}>
        <Row gutter={[12, 12]} align="middle" style={{ marginBottom: 12 }}>
          <Col span={3}>
            <Select value={pvAsset} style={{ width: "100%" }}
              onChange={(v) => { setPvAsset(v); setPvFile(""); setPvData(null); loadPreviewFiles(v); }}>
              <Select.Option value="futures">期货</Select.Option>
              <Select.Option value="stock">股票</Select.Option>
              <Select.Option value="option">期权</Select.Option>
            </Select>
          </Col>
          <Col span={8}>
            <Select style={{ width: "100%" }} showSearch placeholder="选择已下载数据文件"
              value={pvFile || undefined} onChange={setPvFile}
              options={pvFiles.map((f) => ({
                value: f.path,
                label: `${f.symbol}${f.contract ? "/" + f.contract : ""} · ${f.interval} · ${f.size_kb}KB`,
              }))} />
          </Col>
          <Col>
            <Button size="small" onClick={() => loadPreviewFiles(pvAsset)}>刷新文件</Button>
          </Col>
          <Col>
            <Button type="primary" size="small" loading={pvLoading} onClick={runPreview}>预览</Button>
          </Col>
        </Row>

        {q && (
          <Row gutter={16} style={{ marginBottom: 12 }}>
            <Col span={3}><Statistic title="总条数" value={q.rows} /></Col>
            <Col span={6}><Statistic title="日期范围"
              valueStyle={{ fontSize: 13 }}
              value={`${String(q.start).slice(0, 10)} ~ ${String(q.end).slice(0, 10)}`} /></Col>
            <Col span={3}><Statistic title="收盘NaN" value={q.nan_close}
              valueStyle={{ color: q.nan_close ? "#ff4d4f" : "#52c41a" }} /></Col>
            <Col span={3}><Statistic title="负值" value={q.negative_values}
              valueStyle={{ color: q.negative_values ? "#ff4d4f" : "#52c41a" }} /></Col>
            <Col span={3}><Statistic title="高<低" value={q.high_lt_low}
              valueStyle={{ color: q.high_lt_low ? "#ff4d4f" : "#52c41a" }} /></Col>
            <Col span={3}><Statistic title="重复时间" value={q.duplicate_timestamps}
              valueStyle={{ color: q.duplicate_timestamps ? "#ff4d4f" : "#52c41a" }} /></Col>
            <Col span={3}>
              <Statistic title="质量" value={q.is_clean ? "正常" : "异常"}
                valueStyle={{ color: q.is_clean ? "#52c41a" : "#faad14" }} />
            </Col>
          </Row>
        )}

        {closes.length > 1 && (
          <div style={{ marginBottom: 12 }}>
            <Text type="secondary" style={{ fontSize: 12 }}>收盘价走势 (鼠标悬停查看日期/价格)</Text>
            <PriceChart dates={pvData?.chart?.datetime || []} closes={closes} />
          </div>
        )}

        {pvData?.rows?.length > 0 && (
          <Table
            dataSource={pvData.rows}
            columns={[
              { title: "时间", dataIndex: "datetime", key: "datetime",
                render: (v: string) => String(v).slice(0, 19) },
              { title: "开", dataIndex: "open", key: "open", render: fmtPrice },
              { title: "高", dataIndex: "high", key: "high", render: fmtPrice },
              { title: "低", dataIndex: "low", key: "low", render: fmtPrice },
              { title: "收", dataIndex: "close", key: "close", render: fmtPrice },
              { title: "量", dataIndex: "volume", key: "volume", render: fmtVol },
            ]}
            rowKey={(_: any, i?: number) => String(i)}
            size="small"
            pagination={{ pageSize: 10 }}
          />
        )}
      </Card>
    );
  };

  // 仓库预览内容 (质量 + 走势 + 表格)，被仓库预览卡片复用
  const renderWhPreviewBody = (data: any) => {
    const q = data?.quality;
    const closes: number[] = data?.chart?.close || [];
    return (
      <div style={{ marginTop: 12 }}>
        {q && (
          <Row gutter={16} style={{ marginBottom: 12 }}>
            <Col span={3}><Statistic title="总条数" value={q.rows} /></Col>
            <Col span={6}><Statistic title="日期范围" valueStyle={{ fontSize: 13 }}
              value={`${String(q.start).slice(0, 10)} ~ ${String(q.end).slice(0, 10)}`} /></Col>
            <Col span={3}><Statistic title="收盘NaN" value={q.nan_close}
              valueStyle={{ color: q.nan_close ? "#ff4d4f" : "#52c41a" }} /></Col>
            <Col span={3}><Statistic title="负值" value={q.negative_values}
              valueStyle={{ color: q.negative_values ? "#ff4d4f" : "#52c41a" }} /></Col>
            <Col span={3}><Statistic title="高<低" value={q.high_lt_low}
              valueStyle={{ color: q.high_lt_low ? "#ff4d4f" : "#52c41a" }} /></Col>
            <Col span={3}><Statistic title="重复时间" value={q.duplicate_timestamps}
              valueStyle={{ color: q.duplicate_timestamps ? "#ff4d4f" : "#52c41a" }} /></Col>
            <Col span={3}><Statistic title="质量" value={q.is_clean ? "正常" : "异常"}
              valueStyle={{ color: q.is_clean ? "#52c41a" : "#faad14" }} /></Col>
          </Row>
        )}
        {closes.length > 1 && (
          <div style={{ marginBottom: 12 }}>
            <Text type="secondary" style={{ fontSize: 12 }}>收盘价走势 (鼠标悬停查看日期/价格)</Text>
            <PriceChart dates={data?.chart?.datetime || []} closes={closes} />
          </div>
        )}
        {data?.rows?.length > 0 && (
          <Table
            dataSource={data.rows}
            columns={[
              { title: "时间", dataIndex: "datetime", key: "datetime",
                render: (v: string) => String(v).slice(0, 19) },
              { title: "开", dataIndex: "open", key: "open", render: fmtPrice },
              { title: "高", dataIndex: "high", key: "high", render: fmtPrice },
              { title: "低", dataIndex: "low", key: "low", render: fmtPrice },
              { title: "收", dataIndex: "close", key: "close", render: fmtPrice },
              { title: "量", dataIndex: "volume", key: "volume", render: fmtVol },
            ]}
            rowKey={(_: any, i?: number) => String(i)}
            size="small"
            pagination={{ pageSize: 10 }}
          />
        )}
      </div>
    );
  };

  // ── Render: Storage ──
  // ── 按年同步面板 ──
  const loadYearStatus = async () => {
    try {
      const res = await WH.get("/sync/year-status");
      setYearStatus(res.data?.years || []);
    } catch (err: any) {
      message.error(`加载同步状态失败: ${err.response?.data?.detail || err.message}`);
    }
  };

  const syncYear = async (asset: string, year: number, reset = false) => {
    setYearSyncLoading(true);
    try {
      const res = await WH.post("/sync/year", null,
        { params: { asset_type: asset, year, reset_checkpoint: reset } });
      message.success(`${year}年${asset}同步已启动 (后台): ${res.data.job}`);
      setTimeout(loadYearStatus, 1500);
    } catch (err: any) {
      message.error(`启动失败: ${err.response?.data?.detail || err.message}`);
    } finally { setYearSyncLoading(false); }
  };

  const verifyYear = async (asset: string, year: number) => {
    message.loading({ content: "校验中...", key: "verify" });
    try {
      const res = await WH.get("/sync/year/verify", { params: { asset_type: asset, year } });
      setVerifyResult(res.data);
      const d = res.data;
      message.success({ content: `${year}年${asset}: ${d.symbols}个合约/${d.total_bars}条 ${d.is_clean ? "✓干净" : "⚠有问题"}`, key: "verify" });
    } catch (err: any) {
      message.error({ content: `校验失败: ${err.response?.data?.detail || err.message}`, key: "verify" });
    }
  };

  const renderSyncPanel = () => {
    const cell = (asset: string, year: number, c: any) => {
      const color = c?.status === "已同步" ? "#52c41a" : c?.status === "同步中" ? "#1677ff" : "#999";
      return (
        <div>
          <Tag color={c?.status === "已同步" ? "green" : c?.status === "同步中" ? "blue" : "default"}>
            {c?.status || "未同步"}
            {c?.status === "同步中" && c?.checkpoint_done != null ? ` (${c.checkpoint_done})` : ""}
          </Tag>
          <div style={{ fontSize: 11, color }}>
            {asset === "stock" ? `${c?.with_data || 0} 只` : `${c?.with_data || 0}/${c?.contracts || 0} 合约`}
          </div>
          <Space size={4} style={{ marginTop: 4 }}>
            <Button size="small" type="link" style={{ padding: 0 }}
              loading={yearSyncLoading} onClick={() => syncYear(asset, year)}>同步</Button>
            <Button size="small" type="link" style={{ padding: 0 }}
              onClick={() => verifyYear(asset, year)}>校验</Button>
          </Space>
        </div>
      );
    };
    return (
      <div>
        <Card size="small" style={{ marginBottom: 12 }}>
          <Space wrap>
            <Text strong>按年全量同步 (生产)</Text>
            <Text type="secondary" style={{ fontSize: 12 }}>
              具体合约 (非品类), 生命周期守卫保证挂牌/交割范围。断点续传防限流/中断。一年一行倒序。
            </Text>
            <Button size="small" onClick={loadYearStatus}>刷新状态</Button>
            <Button size="small" onClick={pollProgress}>刷新进度</Button>
          </Space>
          {collectProgress?.job?.running && (
            <div style={{ marginTop: 8 }}>
              <Badge status="processing" text={`运行中: ${collectProgress.job.name}`} />
              <Text type="secondary" style={{ marginLeft: 12 }}>
                已完成 {collectProgress.checkpoint?.done || 0} 项
              </Text>
            </div>
          )}
        </Card>
        <Table size="small" rowKey="year" pagination={false}
          dataSource={yearStatus}
          columns={[
            { title: "年份", dataIndex: "year", width: 70,
              render: (y: number) => <Text strong>{y}</Text> },
            { title: "期货", key: "futures", render: (_: any, r: any) => cell("futures", r.year, r.futures) },
            { title: "股票", key: "stock", render: (_: any, r: any) => cell("stock", r.year, r.stock) },
            { title: "期权", key: "option", render: (_: any, r: any) => cell("option", r.year, r.option) },
          ]} />
        {verifyResult && (
          <Card size="small" style={{ marginTop: 12 }}
            title={`校验结果: ${verifyResult.year}年 ${verifyResult.asset_type}`}
            extra={<Button size="small" onClick={() => setVerifyResult(null)}>关闭</Button>}>
            <Space wrap>
              <Statistic title="合约/股票数" value={verifyResult.symbols} />
              <Statistic title="总条数" value={verifyResult.total_bars} />
              <Statistic title="收盘NaN" value={verifyResult.nan_close}
                valueStyle={{ color: verifyResult.nan_close ? "#ff4d4f" : "#52c41a" }} />
              <Statistic title="质量" value={verifyResult.is_clean ? "干净" : "有问题"}
                valueStyle={{ color: verifyResult.is_clean ? "#52c41a" : "#faad14" }} />
            </Space>
          </Card>
        )}

        {/* 实时增量同步 (轮询调度器) */}
        <Card size="small" title="实时增量同步 (轮询调度器)" style={{ marginTop: 12 }}>
          {syncStatus ? (
            <Space>
              <Badge status={syncStatus.running ? "processing" : "default"}
                text={syncStatus.running ? "运行中" : "已停止"} />
              <Text type="secondary">监控品种: {syncStatus.symbols || 0}</Text>
              <Button size="small" type="primary" icon={<SyncOutlined />}
                onClick={async () => { await API.post("/sync/start"); loadSyncStatus(); }}>启动</Button>
              <Button size="small" danger icon={<CloseCircleOutlined />}
                onClick={async () => { await API.post("/sync/stop"); loadSyncStatus(); }}>停止</Button>
              <Button size="small" onClick={loadSyncStatus}>刷新</Button>
            </Space>
          ) : (
            <Space><Text type="secondary">后端未运行</Text>
              <Button size="small" onClick={loadSyncStatus}>刷新状态</Button></Space>
          )}
        </Card>
      </div>
    );
  };

  const renderStorage = () => {
    if (!storage) return <Button onClick={loadStorage}>加载存储信息</Button>;
    return (
      <div>
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={8}><Statistic title="文件数" value={storage.usage?.total_files || 0} /></Col>
          <Col span={8}><Statistic title="存储空间" value={storage.usage?.total_size_mb || 0} suffix="MB" /></Col>
        </Row>
        <Table
          dataSource={storage.available || []}
          columns={[
            { title: "品种", dataIndex: "symbol", key: "symbol" },
            { title: "周期", dataIndex: "interval", key: "interval" },
            { title: "合约", dataIndex: "contract", key: "contract", render: (v: any) => v || "主力" },
            { title: "大小", dataIndex: "size_kb", key: "size", render: (v: number) => `${v}KB` },
            { title: "操作", key: "actions", render: (_: any, r: any) => (
              <Space>
                <Button size="small" icon={<FileExcelOutlined />} onClick={() => exportFile(r)}>
                  导出xlsx
                </Button>
                <Popconfirm title="确认删除该文件?" okText="删除" cancelText="取消"
                  onConfirm={() => deleteFile(r)}>
                  <Button size="small" danger icon={<DeleteOutlined />}>删除</Button>
                </Popconfirm>
              </Space>
            ) },
          ]}
          rowKey="path"
          size="small"
          pagination={false}
        />
      </div>
    );
  };

  // ── Main Render ──
  return (
    <div>
      <div className="page-header">
        <h2>数据中心</h2>
        <Input
          prefix={<SearchOutlined />}
          placeholder="搜索品种、合约..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ width: 240 }}
          allowClear
        />
      </div>

      {/* Stats Overview */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={12} sm={8} lg={3}>
          <Card size="small" hoverable>
            <Statistic title="数据源" value={sources.length || 11} prefix={<ApiOutlined />} valueStyle={{ color: "#1677ff" }} />
          </Card>
        </Col>
        <Col xs={12} sm={8} lg={3}>
          <Card size="small" hoverable>
            <Statistic title="期货品种" value={70} prefix={<RiseOutlined />} valueStyle={{ color: "#52c41a" }} />
          </Card>
        </Col>
        <Col xs={12} sm={8} lg={3}>
          <Card size="small" hoverable>
            <Statistic title="股票(已入库)" value={whAssetCount("stock")} prefix={<RiseOutlined />}
              valueStyle={{ color: "#13c2c2" }} />
          </Card>
        </Col>
        <Col xs={12} sm={8} lg={3}>
          <Card size="small" hoverable>
            <Statistic title="期权(已入库)" value={whAssetCount("option")} prefix={<SafetyOutlined />}
              valueStyle={{ color: "#eb2f96" }} />
          </Card>
        </Col>
        <Col xs={12} sm={8} lg={3}>
          <Card size="small" hoverable>
            <Statistic title="交易所" value={6} prefix={<SafetyOutlined />} valueStyle={{ color: "#722ed1" }} />
          </Card>
        </Col>
        <Col xs={12} sm={8} lg={3}>
          <Card size="small" hoverable>
            <Statistic title="K线总条数" value={whStats?.kline_rows || 0} prefix={<DatabaseOutlined />}
              valueStyle={{ color: "#fa8c16" }} />
          </Card>
        </Col>
        <Col xs={12} sm={8} lg={3}>
          <Card size="small" hoverable>
            <Statistic title="数据库物理大小" value={dbSize?.total_mb ?? 0} suffix="MB"
              prefix={<DatabaseOutlined />} valueStyle={{ color: "#cf1322" }} />
          </Card>
        </Col>
      </Row>

      {/* Tabs */}
      <Card bordered={false}>
        <Tabs activeKey={activeTab} onChange={(k) => {
          setActiveTab(k);
          if (k === "sources") loadSources();
          if (k === "knowledge") loadExchanges();
          if (k === "download") { loadDownloadData(); loadPreviewFiles(pvAsset); }
          if (k === "stock-knowledge" && stockSectors.length === 0) loadStockKnowledge();
          if (k === "option-knowledge" && optProducts.length === 0) loadOptionsKnowledge();
          if (k === "storage") loadStorage();
          if (k === "sync") { loadSyncStatus(); loadYearStatus(); pollProgress(); }
        }}>
          <TabPane tab={<span><ApiOutlined /> 数据源</span>} key="sources">
            {renderSources()}
          </TabPane>
          <TabPane tab={<span><BookOutlined /> 合约知识库</span>} key="knowledge">
            {renderKnowledge()}
            <div style={{ marginTop: 16 }}>{renderExchanges()}</div>
          </TabPane>
          <TabPane tab={<span><RiseOutlined /> 股票知识库</span>} key="stock-knowledge">
            {renderStockKnowledge()}
          </TabPane>
          <TabPane tab={<span><SafetyOutlined /> 期权知识库</span>} key="option-knowledge">
            {renderOptionsKnowledge()}
          </TabPane>
          <TabPane tab={<span><DownloadOutlined /> 数据下载</span>} key="download">
            {renderDownload()}
          </TabPane>
          <TabPane tab={<span><DatabaseOutlined /> 存储管理</span>} key="storage">
            {renderStorage()}
          </TabPane>
          <TabPane tab={<span><SyncOutlined /> 实时同步</span>} key="sync">
            {renderSyncPanel()}
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
}
