import { useEffect, useState } from "react";
import { Row, Col, Card, Statistic, Spin, Tag, Table, Typography, Space, Button, message, Progress, List, Badge, Tabs, Timeline, Tooltip, Input } from "antd";
import {
  ThunderboltOutlined,
  FundOutlined,
  RiseOutlined,
  FallOutlined,
  SyncOutlined,
  RobotOutlined,
  ExperimentOutlined,
  DollarOutlined,
  SafetyCertificateOutlined,
  AimOutlined,
  CloudServerOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ClockCircleOutlined,
  LineChartOutlined,
  PieChartOutlined,
} from "@ant-design/icons";
import { newsApi } from "../services/newsApi";
import { marketApi } from "../services/marketApi";
import { vstockApi, VStockReport } from "../services/vstockApi";
import { vibeApi } from "../services/vibeApi";
import { chinaFinanceApi } from "../services/chinaFinanceApi";
import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts";

const { Title, Text, Paragraph } = Typography;

const VERDICT_COLORS: Record<string, string> = {
  "强烈买入": "red", "买入": "orange", "中性": "default", "卖出": "blue", "强烈卖出": "purple",
};
const SENTIMENT_COLORS: Record<string, string> = {
  positive: "green", neutral: "default", negative: "red",
};
const STATUS_COLORS: Record<string, string> = {
  available: "green", connected: "green", idle: "green", processing: "orange", connecting: "orange", disconnected: "red", error: "red", default: "default",
};

export default function ResearchCenter() {
  const [loading, setLoading] = useState(true);
  const [newsStats, setNewsStats] = useState<{ total: number; avg_sentiment: number; by_source?: Record<string, number> } | null>(null);
  const [marketStats, setMarketStats] = useState<{ total: number; positive_pct: number; positive?: number; neutral?: number; negative?: number } | null>(null);
  const [swarmStatus, setSwarmStatus] = useState<{ agents: { name: string; status: string; tasks?: number }[]; total_agents: number } | null>(null);
  const [vibeStatus, setVibeStatus] = useState<{ datasources: { name: string; status: string }[] } | null>(null);
  const [cfStatus, setCfStatus] = useState<{ skills_count: number; data_status?: Record<string, string> } | null>(null);
  const [factors, setFactors] = useState<{ count: number } | null>(null);
  const [analyzing, setAnalyzing] = useState<string | null>(null);
  const [report, setReport] = useState<VStockReport | null>(null);
  const [researchResult, setResearchResult] = useState<string | null>(null);
  const [quickAnalysis, setQuickAnalysis] = useState<string>("000001");
  const [analysisHistory, setAnalysisHistory] = useState<{ symbol: string; verdict: string; time: Date }[]>([]);
  const [activeTab, setActiveTab] = useState("overview");

  // Sentiment distribution for pie chart
  const sentimentData = marketStats ? [
    { name: "正向", value: marketStats.positive ?? 0, color: "#3f8600" },
    { name: "中性", value: marketStats.neutral ?? 0, color: "#999" },
    { name: "负向", value: marketStats.negative ?? 0, color: "#cf1322" },
  ] : [];

  // Data source status summary
  const dsStatusCounts = {
    available: vibeStatus?.datasources?.filter(d => d.status === "available").length ?? 0,
    total: vibeStatus?.datasources?.length ?? 0,
  };

  const loadAll = async () => {
    setLoading(true);
    try {
      const ns = await newsApi.stats();
      const ms = await marketApi.sentiment();
      const ss = await vibeApi.swarmStatus();
      const vs = await vibeApi.datasources();
      const cf = await chinaFinanceApi.dashboard();
      const fc = await vibeApi.factors({ limit: 3 });
      setNewsStats(ns.data);
      setMarketStats(ms.data);
      setSwarmStatus(ss.data);
      setVibeStatus(vs.data);
      setCfStatus(cf.data);
      setFactors({ count: fc.data.total || fc.data.count || 0 });
    } catch (e) {
      console.error("Failed to load data:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadAll(); }, []);

  const handleAnalyze = async (symbol: string) => {
    setAnalyzing(symbol);
    setReport(null);
    setResearchResult(null);
    try {
      const r1 = await vstockApi.analyze(symbol);
      const r2 = await vibeApi.research(`分析${symbol}的投资价值和技术形态`, symbol);
      setReport(r1.data.report);
      setResearchResult(r2.data.findings?.join(" | "));
      setAnalysisHistory(prev => [{ symbol, verdict: r1.data.report?.jury_vote || "中性", time: new Date() }, ...prev.slice(0, 9)]);
      message.success(`${symbol} 分析完成`);
    } catch {
      message.error("分析失败，请检查后端服务");
    } finally {
      setAnalyzing(null);
    }
  };

  // Data source tab content
  const dataSourceTab = (
    <Card size="small" title={<><CloudServerOutlined /> 数据源监控</>}>
      <Row gutter={16}>
        <Col span={12}>
          <Title level={5} style={{ marginTop: 0 }}>量化数据源</Title>
          <List
            size="small"
            dataSource={vibeStatus?.datasources ?? []}
            renderItem={(ds: { name: string; status: string }) => (
              <List.Item style={{ padding: "6px 0" }}>
                <Space>
                  <Badge status={ds.status === "available" ? "success" : "warning"} />
                  <Text>{ds.name}</Text>
                  <Tag color={STATUS_COLORS[ds.status] || "default"}>{ds.status}</Tag>
                </Space>
              </List.Item>
            )}
          />
        </Col>
        <Col span={12}>
          <Title level={5} style={{ marginTop: 0 }}>金融数据源</Title>
          <List
            size="small"
            dataSource={Object.entries(cfStatus?.data_status || {})}
            renderItem={([name, status]: [string, string]) => (
              <List.Item style={{ padding: "6px 0" }}>
                <Space>
                  <Badge status={status === "connected" ? "success" : status === "connecting" ? "processing" : "error"} />
                  <Text>{name}</Text>
                  <Tag color={STATUS_COLORS[status] || "default"}>{status}</Tag>
                </Space>
              </List.Item>
            )}
          />
        </Col>
      </Row>
    </Card>
  );

  // Analysis history tab content
  const historyTab = (
    <Card size="small" title={<><ClockCircleOutlined /> 分析历史</>}>
      {analysisHistory.length === 0 ? (
        <Text type="secondary">暂无分析记录</Text>
      ) : (
        <Timeline
          items={analysisHistory.map(h => ({
            color: VERDICT_COLORS[h.verdict] === "red" || VERDICT_COLORS[h.verdict] === "orange" ? "green" : VERDICT_COLORS[h.verdict] === "blue" ? "blue" : "gray",
            children: (
              <Space>
                <Tag color="blue">{h.symbol}</Tag>
                <Tag color={VERDICT_COLORS[h.verdict]}>{h.verdict}</Tag>
                <Text type="secondary" style={{ fontSize: 11 }}>{h.time.toLocaleTimeString("zh-CN")}</Text>
              </Space>
            ),
          }))}
        />
      )}
    </Card>
  );

  return (
    <div style={{ padding: 0 }}>
      <Space direction="vertical" size="large" style={{ width: "100%" }}>
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <Title level={4} style={{ margin: 0 }}>
              <ThunderboltOutlined style={{ marginRight: 8 }} />
              综合研究中枢
            </Title>
            <Text type="secondary">数据采集 → AI分析 → 多Agent决策 → 信号输出</Text>
          </div>
          <Space>
            <Input
              placeholder="股票代码"
              value={quickAnalysis}
              onChange={e => setQuickAnalysis(e.target.value)}
              style={{ width: 100 }}
            />
            <Button
              type="primary"
              icon={<RobotOutlined />}
              onClick={() => handleAnalyze(quickAnalysis || "000001")}
              loading={analyzing === (quickAnalysis || "000001")}
            >
              分析
            </Button>
            <Button icon={<SyncOutlined />} onClick={loadAll} loading={loading}>刷新</Button>
          </Space>
        </div>

        {loading && !newsStats ? (
          <div style={{ textAlign: "center", padding: 60 }}><Spin size="large" /></div>
        ) : (
          <>
            {/* Quick Analyze Cards */}
            <Card size="small" title={<><AimOutlined /> 快捷分析</>}>
              <Space wrap>
                {["000001", "600519", "000858", "601318", "000002", "600036", "300750", "688981"].map(sym => (
                  <Tooltip key={sym} title={`分析 ${sym}`}>
                    <Button
                      size="small"
                      type={sym === quickAnalysis ? "primary" : "default"}
                      loading={analyzing === sym}
                      onClick={() => {
                        setQuickAnalysis(sym);
                        handleAnalyze(sym);
                      }}
                    >
                      {sym}
                    </Button>
                  </Tooltip>
                ))}
              </Space>
            </Card>

            {/* Stats Row with Charts */}
            <Row gutter={16}>
              <Col span={4}>
                <Card size="small">
                  <Statistic title="新闻总量" value={newsStats?.total ?? 0} prefix={<FundOutlined />} />
                </Card>
              </Col>
              <Col span={4}>
                <Card size="small">
                  <Statistic
                    title="平均情感"
                    value={newsStats?.avg_sentiment ?? 5}
                    suffix="/ 10"
                    precision={1}
                    valueStyle={{ color: (newsStats?.avg_sentiment ?? 5) > 6 ? "#3f8600" : (newsStats?.avg_sentiment ?? 5) < 4 ? "#cf1322" : "#999" }}
                  />
                </Card>
              </Col>
              <Col span={4}>
                <Card size="small">
                  <Statistic
                    title="舆情正向率"
                    value={marketStats?.positive_pct ?? 0}
                    suffix="%"
                    prefix={<RiseOutlined />}
                    valueStyle={{ color: (marketStats?.positive_pct ?? 0) > 50 ? "#3f8600" : "#cf1322" }}
                  />
                </Card>
              </Col>
              <Col span={4}>
                <Card size="small">
                  <Statistic
                    title="因子库"
                    value={factors?.count ?? 0}
                    suffix="个"
                    prefix={<ExperimentOutlined />}
                  />
                </Card>
              </Col>
              <Col span={4}>
                <Card size="small">
                  <Statistic title="金融Skills" value={cfStatus?.skills_count ?? 0} prefix={<DollarOutlined />} />
                </Card>
              </Col>
              <Col span={4}>
                <Card size="small">
                  <Statistic
                    title="多Agent状态"
                    value={swarmStatus?.total_agents ?? swarmStatus?.agents?.length ?? 0}
                    suffix="个在线"
                    prefix={<RobotOutlined />}
                    valueStyle={{ color: "#1890ff" }}
                  />
                </Card>
              </Col>
            </Row>

            {/* Sentiment Pie Chart */}
            {sentimentData.some(d => d.value > 0) && (
              <Card size="small" title={<><PieChartOutlined /> 市场舆情分布</>}>
                <Row gutter={16} align="middle">
                  <Col span={8}>
                    <ResponsiveContainer width="100%" height={150}>
                      <PieChart>
                        <Pie
                          data={sentimentData}
                          cx="50%"
                          cy="50%"
                          innerRadius={30}
                          outerRadius={60}
                          dataKey="value"
                          label={({ name, value }: { name?: string; value?: number }) => `${name || ""}: ${value ?? 0}`}
                        >
                          {sentimentData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                      </PieChart>
                    </ResponsiveContainer>
                  </Col>
                  <Col span={16}>
                    <Space wrap>
                      {sentimentData.map(d => (
                        <Tag key={d.name} color={d.value > 0 ? "default" : "default"} style={{ background: d.color, color: "#fff", border: "none" }}>
                          {d.name}: {d.value}
                        </Tag>
                      ))}
                    </Space>
                  </Col>
                </Row>
              </Card>
            )}

            {/* Data Source and Agent Status */}
            <Row gutter={16}>
              <Col span={8}>
                <Card size="small" title={<><CloudServerOutlined /> 数据源状态</>}>
                  <Space style={{ marginBottom: 8 }}>
                    <Badge status={dsStatusCounts.available === dsStatusCounts.total ? "success" : "warning"} />
                    <Text>已连接: {dsStatusCounts.available}/{dsStatusCounts.total}</Text>
                  </Space>
                  <List
                    size="small"
                    dataSource={vibeStatus?.datasources ?? []}
                    renderItem={(ds: { name: string; status: string }) => (
                      <List.Item style={{ padding: "4px 0" }}>
                        <Space>
                          <Badge status={ds.status === "available" ? "success" : "warning"} />
                          <Text style={{ fontSize: 12 }}>{ds.name}</Text>
                          <Tag color={STATUS_COLORS[ds.status] || "default"} style={{ fontSize: 10 }}>{ds.status}</Tag>
                        </Space>
                      </List.Item>
                    )}
                  />
                </Card>
              </Col>

              <Col span={8}>
                <Card size="small" title={<><RobotOutlined /> 多Agent团队 ({swarmStatus?.total_agents ?? 0})</>}>
                  <List
                    size="small"
                    dataSource={swarmStatus?.agents ?? []}
                    renderItem={(agent: { name: string; status: string; tasks?: number }) => (
                      <List.Item style={{ padding: "4px 0" }}>
                        <Space>
                          <Badge status={agent.status === "idle" ? "success" : "processing"} />
                          <Text style={{ fontSize: 12 }}>{agent.name}</Text>
                          {agent.tasks && agent.tasks > 0 && <Tag color="blue" style={{ fontSize: 10 }}>{agent.tasks}任务</Tag>}
                        </Space>
                      </List.Item>
                    )}
                  />
                </Card>
              </Col>

              <Col span={8}>
                <Card size="small" title={<><LineChartOutlined /> 分析历史</>}>
                  {analysisHistory.length === 0 ? (
                    <Text type="secondary" style={{ fontSize: 12 }}>暂无分析记录</Text>
                  ) : (
                    <List
                      size="small"
                      dataSource={analysisHistory.slice(0, 5)}
                      renderItem={(h) => (
                        <List.Item style={{ padding: "4px 0" }}>
                          <Space>
                            <Tag color="blue" style={{ fontSize: 10 }}>{h.symbol}</Tag>
                            <Tag color={VERDICT_COLORS[h.verdict]} style={{ fontSize: 10 }}>{h.verdict}</Tag>
                          </Space>
                        </List.Item>
                      )}
                    />
                  )}
                </Card>
              </Col>
            </Row>

            {/* Analysis Result */}
            {(report || researchResult) && (
              <Card
                title={<><SafetyCertificateOutlined /> 研报结果 {report?.symbol}</>}
                extra={<Space>
                  <Tag color={VERDICT_COLORS[report?.jury_vote ?? "中性"]}>{report?.jury_vote}</Tag>
                  <Button size="small" icon={<SyncOutlined />} onClick={() => report && handleAnalyze(report.symbol)} loading={analyzing === report?.symbol}>
                    重新分析
                  </Button>
                </Space>}
              >
                {researchResult && (
                  <Paragraph type="secondary" style={{ marginBottom: 16 }}>
                    <Text type="secondary">研究结论: </Text>{researchResult}
                  </Paragraph>
                )}
                {report && (
                  <Row gutter={16}>
                    <Col span={4}><Statistic title="评审团" value={report.jury_count} suffix="人" /></Col>
                    <Col span={4}><Statistic title="主流派" value={report.dominant_school} /></Col>
                    <Col span={4}><Statistic title="估值分" value={report.valuation_score} suffix="/ 10" precision={1} /></Col>
                    <Col span={4}><Statistic title="风险" value={report.risk_level} valueStyle={{ color: report.risk_level === "低" ? "#3f8600" : report.risk_level === "高" ? "#cf1322" : "#999" }} /></Col>
                    <Col span={4}><Statistic title="杀猪盘指数" value={report.scam_score} suffix="/ 10" precision={1} /></Col>
                    <Col span={4}>
                      <Progress
                        percent={report.scam_score * 10}
                        size="small"
                        status={report.scam_score > 5 ? "exception" : "normal"}
                        showInfo={false}
                      />
                      <Text type="secondary" style={{ fontSize: 11 }}>可疑度</Text>
                    </Col>
                  </Row>
                )}
                {report?.opinions && (
                  <Table
                    size="small"
                    dataSource={report.opinions.slice(0, 6)}
                    rowKey="juror"
                    pagination={false}
                    style={{ marginTop: 12 }}
                    columns={[
                      { title: "分析师", dataIndex: "juror", width: 100 },
                      { title: "流派", dataIndex: "school", width: 100 },
                      {
                        title: "判断", dataIndex: "verdict", width: 90,
                        render: (v: string) => <Tag color={VERDICT_COLORS[v]}>{v}</Tag>,
                      },
                      {
                        title: "置信度", dataIndex: "confidence", width: 80,
                        render: (v: number) => <Progress percent={v * 100} size="small" showInfo={false} />,
                      },
                      { title: "理由", dataIndex: "reasoning", ellipsis: true },
                    ]}
                  />
                )}
              </Card>
            )}

            {/* Detail Tabs */}
            <Tabs
              activeKey={activeTab}
              onChange={setActiveTab}
              items={[
                { key: "overview", label: "📊 系统概览", children: null },
                { key: "datasource", label: "🔗 数据源", children: dataSourceTab },
                { key: "history", label: "🕐 分析历史", children: historyTab },
              ]}
            />
          </>
        )}
      </Space>
    </div>
  );
}
