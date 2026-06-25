import { useEffect, useState } from "react";
import { Card, Table, Tag, Space, Button, Typography, Input, Spin, message, Row, Col, Statistic, Progress, Divider, List, Select, Tabs, Empty, Tooltip, Badge } from "antd";
import {
  SafetyCertificateOutlined,
  RobotOutlined,
  DollarOutlined,
  ExperimentOutlined,
  SyncOutlined,
  ExclamationCircleOutlined,
  FundOutlined,
  ThunderboltOutlined,
  PieChartOutlined,
  AimOutlined,
} from "@ant-design/icons";
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Cell } from "recharts";
import { vstockApi, VStockReport } from "../services/vstockApi";

const { Title, Text, Paragraph } = Typography;
const VERDICT_COLORS: Record<string, string> = {
  "强烈买入": "red", "买入": "orange", "中性": "default", "卖出": "blue", "强烈卖出": "purple",
};
const VERDICT_BG: Record<string, string> = {
  "强烈买入": "#fff1f0", "买入": "#fff7e6", "中性": "#f5f5f5", "卖出": "#e6f7ff", "强烈卖出": "#f0f5ff",
};
const RISK_COLORS: Record<string, string> = { "低": "green", "中": "orange", "高": "red" };
const SCHOOL_COLORS: Record<string, string> = {
  "价值投资": "#52c41a", "成长投资": "#1890ff", "技术分析": "#722ed1",
  "量化分析": "#fa8c16", "事件驱动": "#eb2f96", "宏观策略": "#13c2c2",
  "行业研究": "#faad14", "财务分析": "#a0d911", "趋势跟踪": "#2f54eb",
};

export default function VStockAdvisor() {
  const [loading, setLoading] = useState(true);
  const [schools, setSchools] = useState<string[]>([]);
  const [reports, setReports] = useState<VStockReport[]>([]);
  const [selected, setSelected] = useState<VStockReport | null>(null);
  const [symbol, setSymbol] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [compareMode, setCompareMode] = useState(false);
  const [compareSymbols, setCompareSymbols] = useState<string[]>([]);

  const load = async () => {
    setLoading(true);
    try {
      const s = await vstockApi.schools();
      const r = await vstockApi.reports({ limit: 20 });
      setSchools(s.data.schools);
      const reportData = r.data.reports;
      setReports(reportData);
      if (!selected && reportData[0]) setSelected(reportData[0]);
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const handleAnalyze = async () => {
    if (!symbol) { message.warning("请输入股票代码"); return; }
    setAnalyzing(true);
    try {
      const res = await vstockApi.analyze(symbol);
      const report = res.data.report;
      setSelected(report);
      setReports(prev => [report, ...prev]);
      message.success("分析完成");
    } catch { message.error("分析失败"); }
    finally { setAnalyzing(false); }
  };

  const handleQuickAnalyze = async (sym: string) => {
    setAnalyzing(true);
    try {
      const res = await vstockApi.analyze(sym);
      const report = res.data.report;
      setSelected(report);
      setReports(prev => [report, ...prev]);
      message.success(`${sym} 分析完成`);
    } catch { message.error(`${sym} 分析失败`); }
    finally { setAnalyzing(false); }
  };

  // Calculate school distribution
  const schoolCounts: Record<string, number> = {};
  if (selected) {
    selected.opinions.forEach(o => { schoolCounts[o.school] = (schoolCounts[o.school] || 0) + 1; });
  }

  // Radar chart data for opinions
  const radarData = selected?.opinions.slice(0, 9).map(o => ({
    school: o.school,
    confidence: Math.round(o.confidence * 100),
    value: 100,
  })) || [];

  // Comparison data
  const compareData = reports.slice(0, 5).map(r => ({
    symbol: r.symbol,
    verdict: r.jury_vote,
    valuation: r.valuation_score,
    risk: r.risk_level === "低" ? 2 : r.risk_level === "中" ? 1 : 0,
    scam: r.scam_score,
  }));

  const verdictSummary = selected ? {
    "强烈买入": selected.opinions.filter(o => o.verdict === "强烈买入").length,
    "买入": selected.opinions.filter(o => o.verdict === "买入").length,
    "中性": selected.opinions.filter(o => o.verdict === "中性").length,
    "卖出": selected.opinions.filter(o => o.verdict === "卖出").length,
    "强烈卖出": selected.opinions.filter(o => o.verdict === "强烈卖出").length,
  } : null;

  const verdictTab = (
    <Card size="small" title={<><PieChartOutlined /> 评审团投票分布</>}>
      <Row gutter={16}>
        <Col span={12}>
          <div style={{ display: "flex", justifyContent: "space-around", marginTop: 20 }}>
            {verdictSummary && Object.entries(verdictSummary).map(([k, v]) => (
              <div key={k} style={{ textAlign: "center" }}>
                <div style={{
                  width: 50, height: 50, borderRadius: "50%",
                  background: VERDICT_COLORS[k] === "default" ? "#f0f0f0" : VERDICT_COLORS[k],
                  color: "#fff", lineHeight: "50px", fontWeight: "bold", fontSize: 18,
                  display: "inline-block"
                }}>{v}</div>
                <div style={{ marginTop: 4, fontSize: 11, color: "#666" }}>{k}</div>
              </div>
            ))}
          </div>
        </Col>
        <Col span={12}>
          <ResponsiveContainer width="100%" height={200}>
            <RadarChart data={radarData}>
              <PolarGrid />
              <PolarAngleAxis dataKey="school" tick={{ fontSize: 10 }} />
              <PolarRadiusAxis angle={30} domain={[0, 100]} />
              <Radar name="置信度" dataKey="confidence" stroke="#1890ff" fill="#1890ff" fillOpacity={0.6} />
            </RadarChart>
          </ResponsiveContainer>
        </Col>
      </Row>
    </Card>
  );

  const detailsTab = (
    <Card size="small" title={<><RobotOutlined /> 66人评审团详情</>}>
      <Table
        size="small"
        dataSource={selected?.opinions}
        rowKey="juror"
        pagination={{ pageSize: 10, showSizeChanger: true }}
        columns={[
          { title: "分析师", dataIndex: "juror", width: 100,
            render: (v) => <Tag>{v}</Tag> },
          { title: "流派", dataIndex: "school", width: 100,
            render: (v) => <Tag color={SCHOOL_COLORS[v] || "default"}>{v}</Tag> },
          {
            title: "判断", dataIndex: "verdict", width: 90,
            render: (v: string) => <Tag color={VERDICT_COLORS[v]}>{v}</Tag>,
          },
          {
            title: "置信度", dataIndex: "confidence", width: 150,
            render: (v: number) => <Progress percent={Math.round(v * 100)} size="small" format={(p) => `${p}%`} />,
          },
          { title: "理由", dataIndex: "reasoning", ellipsis: true },
        ]}
      />
    </Card>
  );

  const comparisonTab = (
    <Card size="small" title={<><AimOutlined /> 研报对比</>}>
      <Table
        size="small"
        dataSource={compareData}
        rowKey="symbol"
        pagination={false}
        columns={[
          { title: "股票", dataIndex: "symbol", width: 100, render: (v) => <Tag color="blue">{v}</Tag> },
          { title: "判断", dataIndex: "verdict", width: 100,
            render: (v) => <Tag color={VERDICT_COLORS[v]}>{v}</Tag> },
          { title: "估值分", dataIndex: "valuation", width: 100,
            render: (v) => <Progress percent={v * 10} size="small" format={() => `${v}/10`} /> },
          { title: "风险", dataIndex: "risk", width: 100,
            render: (v) => {
              const labels = ["高", "中", "低"];
              return <Tag color={RISK_COLORS[labels[v] || "中"]}>{labels[v] || "中"}</Tag>;
            }},
          { title: "杀猪盘", dataIndex: "scam", width: 100,
            render: (v) => <Progress percent={v * 10} size="small" status={v > 5 ? "exception" : "normal"} /> },
          {
            title: "操作",
            width: 80,
            render: (_: unknown, record: typeof compareData[0]) => (
              <Button size="small" onClick={() => {
                const r = reports.find(r => r.symbol === record.symbol);
                if (r) setSelected(r);
              }}>查看</Button>
            ),
          },
        ]}
      />
    </Card>
  );

  return (
    <div>
      <Space direction="vertical" size="large" style={{ width: "100%" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <Space>
            <Title level={4} style={{ margin: 0 }}><SafetyCertificateOutlined /> 游资股票分析引擎</Title>
            <Tooltip title="九大流派66位分析师评审">
              <Badge count={reports.length} showZero color="#1890ff">
                <Tag>研报 {reports.length}</Tag>
              </Badge>
            </Tooltip>
          </Space>
          <Space>
            <Input placeholder="股票代码 如: 000001" value={symbol} onChange={e => setSymbol(e.target.value)} style={{ width: 180 }} />
            <Button type="primary" icon={<ExperimentOutlined />} onClick={handleAnalyze} loading={analyzing}>分析</Button>
            <Button icon={<SyncOutlined />} onClick={load}>刷新</Button>
          </Space>
        </div>

        {/* Quick Analyze */}
        <Card size="small" title={<><ThunderboltOutlined /> 快捷分析</>}>
          <Space wrap>
            {["000001", "600519", "000858", "601318", "000002", "600036", "300750", "688981"].map(sym => (
              <Button
                key={sym}
                size="small"
                loading={analyzing}
                onClick={() => handleQuickAnalyze(sym)}
              >
                {sym}
              </Button>
            ))}
          </Space>
        </Card>

        {/* Schools Distribution */}
        <Card size="small" title={<><FundOutlined /> 九大分析流派</>}>
          <Space wrap>
            {schools.map(s => (
              <Tooltip key={s} title={`流派: ${s} | 投票数: ${schoolCounts[s] ?? 0}`}>
                <Tag
                  color={SCHOOL_COLORS[s] || "default"}
                  style={{ padding: "4px 12px", cursor: "pointer" }}
                >
                  {s} ({schoolCounts[s] ?? 0})
                </Tag>
              </Tooltip>
            ))}
          </Space>
        </Card>

        {loading && !selected ? (
          <Spin style={{ display: "block", margin: "40px auto" }} />
        ) : (
          <Row gutter={16}>
            {/* Report List */}
            <Col span={7}>
              <Card size="small" title="📋 历史研报">
                <List
                  size="small"
                  dataSource={reports}
                  locale={{ emptyText: "暂无研报" }}
                  renderItem={(r) => (
                    <List.Item
                      key={r.id}
                      style={{
                        cursor: "pointer",
                        padding: "8px 4px",
                        background: selected?.id === r.id ? "#e6f7ff" : undefined,
                        borderRadius: 4,
                      }}
                      onClick={() => setSelected(r)}
                    >
                      <Space direction="vertical" size={2}>
                        <Space>
                          <Text strong>{r.symbol}</Text>
                          <Tag color={VERDICT_COLORS[r.jury_vote]} style={{ marginLeft: 4 }}>{r.jury_vote}</Tag>
                        </Space>
                        <Space>
                          <Text type="secondary" style={{ fontSize: 10 }}>{new Date(r.timestamp).toLocaleString("zh-CN")}</Text>
                          <Tooltip title="估值分">
                            <Text style={{ fontSize: 10, color: "#1890ff" }}>估值 {r.valuation_score}</Text>
                          </Tooltip>
                        </Space>
                      </Space>
                    </List.Item>
                  )}
                />
              </Card>
            </Col>

            {/* Detail */}
            {selected && (
              <Col span={17}>
                <Card
                  title={
                    <Space>
                      <Text strong style={{ fontSize: 16 }}>{selected.symbol}</Text>
                      <Tag color={VERDICT_COLORS[selected.jury_vote]} style={{ fontSize: 14, padding: "2px 12px" }}>
                        {selected.jury_vote}
                      </Tag>
                    </Space>
                  }
                  extra={<Text type="secondary">{new Date(selected.timestamp).toLocaleString("zh-CN")}</Text>}
                >
                  <Row gutter={12}>
                    <Col span={4}><Statistic title="评审团" value={selected.jury_count} suffix="人" prefix={<RobotOutlined />} /></Col>
                    <Col span={4}><Statistic title="主流派" value={selected.dominant_school} /></Col>
                    <Col span={4}>
                      <Statistic title="估值分" value={selected.valuation_score} suffix="/ 10" precision={1} prefix={<DollarOutlined />} />
                    </Col>
                    <Col span={4}>
                      <Statistic title="风险等级" value={selected.risk_level} valueStyle={{ color: RISK_COLORS[selected.risk_level] }} />
                    </Col>
                    <Col span={4}>
                      <div><Text type="secondary">杀猪盘指数</Text></div>
                      <Progress percent={selected.scam_score * 10} size="small" status={selected.scam_score > 5 ? "exception" : "normal"} />
                      <Text type="secondary" style={{ fontSize: 11 }}>{selected.scam_score}/10</Text>
                    </Col>
                    <Col span={4}>
                      <Statistic
                        title="综合置信度"
                        value={Math.round(selected.opinions.reduce((s, o) => s + o.confidence, 0) / selected.opinions.length * 100)}
                        suffix="%"
                      />
                    </Col>
                  </Row>

                  <Divider />

                  {/* Verdict Summary */}
                  <Row gutter={8}>
                    {verdictSummary && Object.entries(verdictSummary).filter(([_, v]) => v > 0).map(([k, v]) => (
                      <Col span={4} key={k}>
                        <div style={{ textAlign: "center", padding: "8px 0", background: VERDICT_BG[k], borderRadius: 4 }}>
                          <Text strong style={{ fontSize: 20, color: VERDICT_COLORS[k] === "default" ? "#666" : VERDICT_COLORS[k] }}>{v}</Text>
                          <div style={{ fontSize: 11 }}>{k}</div>
                        </div>
                      </Col>
                    ))}
                  </Row>
                </Card>

                {/* Tabs */}
                <Tabs
                  style={{ marginTop: 12 }}
                  items={[
                    { key: "verdict", label: "📊 投票分布", children: verdictTab },
                    { key: "details", label: "👥 评审详情", children: detailsTab },
                    { key: "compare", label: "📈 研报对比", children: comparisonTab },
                  ]}
                />
              </Col>
            )}
          </Row>
        )}
      </Space>
    </div>
  );
}
