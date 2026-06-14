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
      {/* Static source cards — 仅当后端未启动时显示 */}
      {sources.length === 0 && ["AKShare", "Yahoo Finance", "TDX (通达信)", "FRED", "Alpha Vantage", "CFTC"].map((name) => (
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

  // ── Render: Download Manager ──
  const renderDownload = () => (
    <div>
      {/* 快捷下载操作栏 */}
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
    </div>
  );

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
          if (k === "download") loadDownloadData();
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
