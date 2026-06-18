import { useEffect, useState } from "react";
import {
  Row, Col, Card, Table, Tag, Typography, Statistic, Badge,
  Input, Button, Tabs, message, Select, Space, Progress, DatePicker,
} from "antd";
import dayjs from "dayjs";
import {
  DatabaseOutlined, CheckCircleOutlined, WarningOutlined,
  CloseCircleOutlined, SearchOutlined, DownloadOutlined,
  SyncOutlined, BookOutlined,
  ApiOutlined, RiseOutlined, SafetyOutlined,
} from "@ant-design/icons";
import axios from "axios";

const { Text, Title } = Typography;
const { TabPane } = Tabs;

/* ── API client ── */
const API = axios.create({ baseURL: "/api/v1/data-center", timeout: 15000 });
const WH = axios.create({ baseURL: "/api/v1/warehouse", timeout: 30000 });

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
  const [mainContracts, setMainContracts] = useState<any[]>([]);

  // Warehouse: 仓库预览 (按合约代码)
  const [whPvCode, setWhPvCode] = useState<string>("");
  const [whPvTf, setWhPvTf] = useState<string>("D1");
  const [whPvData, setWhPvData] = useState<any>(null);
  const [whPvLoading, setWhPvLoading] = useState(false);

  // Storage
  const [storage, setStorage] = useState<any>(null);

  // Load data on mount
  useEffect(() => {
    loadSources();
    loadExchanges();
  }, []);

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

  const downloadAsset = async (symbol: string, interval: string,
    asset: "stock" | "option", contract?: string) => {
    if (!symbol) { message.warning("请填写代码"); return; }
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
        message.success({ content: `成功下载 ${res.data.bars} 条 (${res.data.source})`, key: "asset" });
      } else {
        message.info({ content: "未获取到数据", key: "asset" });
      }
    } catch (err: any) {
      message.error({ content: `下载失败: ${err.response?.data?.detail || err.message}`, key: "asset" });
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

  // ── Render: Download Manager ──
  const renderDownload = () => (
    <div>
      {/* 资产类别选择 */}
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
            <Col span={5}>
              <Select
                style={{ width: "100%" }}
                showSearch
                value={stockSymbol}
                onChange={setStockSymbol}
                options={STOCK_SEED.map((s) => ({ value: s, label: s }))}
              />
            </Col>
            <Col span={5}>
              <Input placeholder="或输入代码 如 600519.SH"
                onPressEnter={(e) => setStockSymbol((e.target as HTMLInputElement).value.trim())}
                onBlur={(e) => e.target.value && setStockSymbol(e.target.value.trim())}
                allowClear />
            </Col>
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
            <Col><Text type="secondary" style={{ fontSize: 11 }}>日/周线取近5年</Text></Col>
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
                下载日线
              </Button>
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
            <Text type="secondary" style={{ fontSize: 12 }}>收盘价走势</Text>
            {renderSparkline(closes)}
          </div>
        )}

        {pvData?.rows?.length > 0 && (
          <Table
            dataSource={pvData.rows}
            columns={[
              { title: "时间", dataIndex: "datetime", key: "datetime",
                render: (v: string) => String(v).slice(0, 19) },
              { title: "开", dataIndex: "open", key: "open" },
              { title: "高", dataIndex: "high", key: "high" },
              { title: "低", dataIndex: "low", key: "low" },
              { title: "收", dataIndex: "close", key: "close" },
              { title: "量", dataIndex: "volume", key: "volume" },
            ]}
            rowKey={(_: any, i?: number) => String(i)}
            size="small"
            pagination={{ pageSize: 10 }}
          />
        )}
      </Card>
    );
  };

  // 轻量 SVG 折线图 (匹配项目自绘 SVG 约定)
  const renderSparkline = (vals: number[]) => {
    const W = 800, H = 120, pad = 4;
    const nums = vals.filter((v) => typeof v === "number" && !isNaN(v));
    if (nums.length < 2) return null;
    const min = Math.min(...nums), max = Math.max(...nums);
    const span = max - min || 1;
    const pts = nums.map((v, i) => {
      const x = pad + (i / (nums.length - 1)) * (W - 2 * pad);
      const y = H - pad - ((v - min) / span) * (H - 2 * pad);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    }).join(" ");
    return (
      <svg width="100%" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none"
        style={{ display: "block", border: "1px solid #f0f0f0", borderRadius: 4 }}>
        <polyline points={pts} fill="none" stroke="#1677ff" strokeWidth={1.5} />
      </svg>
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
            <Text type="secondary" style={{ fontSize: 12 }}>收盘价走势</Text>
            {renderSparkline(closes)}
          </div>
        )}
        {data?.rows?.length > 0 && (
          <Table
            dataSource={data.rows}
            columns={[
              { title: "时间", dataIndex: "datetime", key: "datetime",
                render: (v: string) => String(v).slice(0, 19) },
              { title: "开", dataIndex: "open", key: "open" },
              { title: "高", dataIndex: "high", key: "high" },
              { title: "低", dataIndex: "low", key: "low" },
              { title: "收", dataIndex: "close", key: "close" },
              { title: "量", dataIndex: "volume", key: "volume" },
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
        <Col xs={24} sm={6}>
          <Card size="small" hoverable>
            <Statistic title="数据源" value={sources.length || 11} prefix={<ApiOutlined />} valueStyle={{ color: "#1677ff" }} />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card size="small" hoverable>
            <Statistic title="期货品种" value={70} prefix={<RiseOutlined />} valueStyle={{ color: "#52c41a" }} />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card size="small" hoverable>
            <Statistic title="交易所" value={6} prefix={<SafetyOutlined />} valueStyle={{ color: "#722ed1" }} />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card size="small" hoverable>
            <Statistic title="下载任务" value={downloadStats?.total_tasks || 0} prefix={<DownloadOutlined />} />
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
          if (k === "storage") loadStorage();
          if (k === "sync") loadSyncStatus();
        }}>
          <TabPane tab={<span><ApiOutlined /> 数据源</span>} key="sources">
            {renderSources()}
          </TabPane>
          <TabPane tab={<span><BookOutlined /> 合约知识库</span>} key="knowledge">
            {renderKnowledge()}
            <div style={{ marginTop: 16 }}>{renderExchanges()}</div>
          </TabPane>
          <TabPane tab={<span><DownloadOutlined /> 数据下载</span>} key="download">
            {renderDownload()}
          </TabPane>
          <TabPane tab={<span><DatabaseOutlined /> 存储管理</span>} key="storage">
            {renderStorage()}
          </TabPane>
          <TabPane tab={<span><SyncOutlined /> 实时同步</span>} key="sync">
            <Card title="同步调度器状态">
              {syncStatus ? (
                <Row gutter={16}>
                  <Col span={8}><Statistic title="运行中" value={syncStatus.running ? "是" : "否"} /></Col>
                  <Col span={8}><Statistic title="监控品种" value={syncStatus.symbols || 0} /></Col>
                  <Col span={8}>
                    <Space>
                      <Button type="primary" icon={<SyncOutlined />}
                        onClick={async () => { await API.post("/sync/start"); loadSyncStatus(); }}>
                        启动
                      </Button>
                      <Button danger icon={<CloseCircleOutlined />}
                        onClick={async () => { await API.post("/sync/stop"); loadSyncStatus(); }}>
                        停止
                      </Button>
                    </Space>
                  </Col>
                </Row>
              ) : (
                <Space direction="vertical">
                  <Text type="secondary">后端未运行，点击刷新</Text>
                  <Button onClick={loadSyncStatus}>刷新状态</Button>
                </Space>
              )}
            </Card>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
}
