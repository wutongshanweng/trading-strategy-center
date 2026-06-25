import { useEffect, useState } from "react";
import { Card, Table, Tag, Space, Button, Typography, Input, Spin, message, Row, Col, Statistic, Select, List, Badge, Progress, Tabs, Empty, Tooltip, Popover } from "antd";
import { ExperimentOutlined, SyncOutlined, RobotOutlined, PlayCircleOutlined, CloudServerOutlined, LineChartOutlined, HeatMapOutlined, AimOutlined, ThunderboltOutlined } from "@ant-design/icons";
import { Line, LineChart, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, Legend, BarChart, Bar } from "recharts";
import { vibeApi, FactorInfo, BacktestResult } from "../services/vibeApi";

const { Title, Text, Paragraph } = Typography;
const CATEGORY_COLORS: Record<string, string> = {
  momentum: "blue", value: "green", quality: "purple", size: "orange",
  volatility: "cyan", liquidity: "magenta", sentiment: "gold", technical: "red",
};

// Sample backtest chart data generator
const generateChartData = (result: BacktestResult) => {
  const days = result.trades * 3;
  let value = 100000;
  const data = [];
  for (let i = 0; i <= days; i++) {
    value = value * (1 + (Math.random() - 0.45) * 0.02);
    data.push({ day: i, value: Math.round(value), benchmark: 100000 * (1 + (i / days) * (result.total_return / 100)) });
  }
  return data;
};

export default function VibeResearch() {
  const [loading, setLoading] = useState(true);
  const [factors, setFactors] = useState<FactorInfo[]>([]);
  const [factorSource, setFactorSource] = useState<string>("");
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string | undefined>();
  const [backtests, setBacktests] = useState<BacktestResult[]>([]);
  const [datasources, setDatasources] = useState<{ name: string; type: string; status: string }[]>([]);
  const [swarmStatus, setSwarmStatus] = useState<{ agents: { name: string; status: string; tasks: number }[]; total_agents: number } | null>(null);
  const [btSymbol, setBtSymbol] = useState("000001");
  const [btStrategy, setBtStrategy] = useState("ma_cross");
  const [running, setRunning] = useState(false);
  const [researchQuery, setResearchQuery] = useState("");
  const [researching, setResearching] = useState(false);
  const [researchResult, setResearchResult] = useState<{ findings: string[]; signals: string[]; confidence: number; top_factors?: string[] } | null>(null);
  const [selectedBacktest, setSelectedBacktest] = useState<BacktestResult | null>(null);
  const [chartData, setChartData] = useState<{ day: number; value: number; benchmark: number }[]>([]);
  const [factorSearch, setFactorSearch] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const fc = await vibeApi.factors(selectedCategory ? { category: selectedCategory } : {});
      const cc = await vibeApi.factorCategories();
      const ds = await vibeApi.datasources();
      const ss = await vibeApi.swarmStatus();
      setFactors(fc.data.factors);
      setFactorSource(fc.data.source || "mock");
      setCategories(cc.data.categories);
      setDatasources(ds.data.datasources);
      setSwarmStatus(ss.data);
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [selectedCategory]);

  useEffect(() => {
    vibeApi.backtests({ limit: 10 }).then(r => {
      setBacktests(r.data.backtests);
      if (r.data.backtests[0]) {
        setSelectedBacktest(r.data.backtests[0]);
        setChartData(generateChartData(r.data.backtests[0]));
      }
    }).catch(() => {});
  }, []);

  const handleBacktest = async () => {
    if (!btSymbol) { message.warning("请输入股票代码"); return; }
    setRunning(true);
    try {
      const res = await vibeApi.backtest({ symbol: btSymbol, strategy: btStrategy, start_date: "2023-01-01", end_date: "2024-01-01", initial_capital: 100000 });
      const result = res.data.result;
      setBacktests(prev => [result, ...prev]);
      setSelectedBacktest(result);
      setChartData(generateChartData(result));
      message.success("回测完成");
    } catch { message.error("回测失败"); }
    finally { setRunning(false); }
  };

  const handleResearch = async () => {
    if (!researchQuery) return;
    setResearching(true);
    try {
      const res = await vibeApi.research(researchQuery, btSymbol);
      setResearchResult(res.data);
      message.success("研究完成");
    } catch { message.error("研究失败"); }
    finally { setResearching(false); }
  };

  // Filter factors by search
  const filteredFactors = factors.filter(f =>
    f.name.toLowerCase().includes(factorSearch.toLowerCase()) ||
    f.description.toLowerCase().includes(factorSearch.toLowerCase())
  );

  // Factor performance overview (mock data for display)
  const factorPerformance = factors.slice(0, 10).map(f => ({
    name: f.name,
    performance: f.risk_adj_return,
  }));

  const performanceTab = (
    <Card size="small" title={<><LineChartOutlined /> 因子表现</>}>
      <Row gutter={16}>
        <Col span={12}>
          <Title level={5} style={{ marginTop: 0 }}>Top因子收益分布</Title>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={factorPerformance} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" domain={[-1, 2]} tickFormatter={(v) => `${v}%`} />
              <YAxis type="category" dataKey="name" width={80} tick={{ fontSize: 11 }} />
              <RechartsTooltip formatter={(v: unknown) => [`${Number(v).toFixed(3)}`, "风险调整收益"]} />
              <Bar dataKey="performance" fill="#1890ff" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Col>
        <Col span={12}>
          <Title level={5} style={{ marginTop: 0 }}>分类统计</Title>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {categories.map(cat => (
              <Tooltip key={cat} title={`查看 ${cat} 因子`}>
                <Tag
                  color={CATEGORY_COLORS[cat] || "default"}
                  style={{ cursor: "pointer", padding: "4px 12px" }}
                  onClick={() => setSelectedCategory(cat)}
                >
                  {cat}: {factors.filter(f => f.category === cat).length}
                </Tag>
              </Tooltip>
            ))}
          </div>
          <div style={{ marginTop: 16 }}>
            <Text type="secondary" style={{ fontSize: 12 }}>
              共 {factors.length} 个因子，来源: {factorSource === "alpha101" ? `✅ 真实${factors.length}因子库` : "⚠️ 模拟数据"}
            </Text>
          </div>
        </Col>
      </Row>
    </Card>
  );

  const factorsTab = (
    <Card size="small" title={<><ExperimentOutlined /> Alpha因子库</>}>
      <Space style={{ marginBottom: 8 }}>
        <Input.Search
          placeholder="搜索因子"
          value={factorSearch}
          onChange={e => setFactorSearch(e.target.value)}
          style={{ width: 200 }}
        />
        <Text type="secondary" style={{ fontSize: 11 }}>共 {filteredFactors.length} 个因子</Text>
      </Space>
      <Table
        size="small"
        loading={loading}
        dataSource={filteredFactors}
        rowKey="name"
        pagination={{ pageSize: 10, showSizeChanger: true, pageSizeOptions: [10, 20, 50, 100] }}
        scroll={{ x: 600 }}
        columns={[
          { title: "因子名", dataIndex: "name", width: 120, fixed: "left",
            render: (v) => <Text code style={{ fontSize: 11 }}>{v}</Text> },
          { title: "分类", dataIndex: "category", width: 100,
            render: (v) => <Tag color={CATEGORY_COLORS[v] || "default"}>{v}</Tag> },
          { title: "描述", dataIndex: "description", ellipsis: true },
          { title: "风险调整收益", dataIndex: "risk_adj_return", width: 130,
            render: (v) => (
              <Text style={{ color: v > 0 ? "#3f8600" : "#cf1322", fontWeight: "bold" }}>
                {v > 0 ? "+" : ""}{v.toFixed(3)}
              </Text>
            )
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
            <Title level={4} style={{ margin: 0 }}><ExperimentOutlined /> 量化研究平台</Title>
            <Tag color={factorSource === "alpha101" ? "green" : "orange"}>
              {factorSource === "alpha101" ? `✅ ${factors.length}真实因子` : "⚠️ 模拟"}
            </Tag>
          </Space>
          <Button icon={<SyncOutlined />} onClick={load} loading={loading}>刷新</Button>
        </div>

        <Row gutter={16}>
          {/* Data Sources */}
          <Col span={6}>
            <Card size="small" title={<><CloudServerOutlined /> 数据源</>}>
              <List size="small" dataSource={datasources} renderItem={(ds) => (
                <List.Item style={{ padding: "4px 0" }}>
                  <Space>
                    <Badge status={ds.status === "available" ? "success" : "default"} />
                    <Text style={{ fontSize: 12 }}>{ds.name}</Text>
                    <Tag color={ds.status === "available" ? "green" : "default"} style={{ fontSize: 10 }}>{ds.type}</Tag>
                  </Space>
                </List.Item>
              )} />
            </Card>
          </Col>

          {/* Swarm */}
          <Col span={6}>
            <Card size="small" title={<><RobotOutlined /> 多Agent ({swarmStatus?.total_agents ?? 0})</>}>
              <List size="small" dataSource={swarmStatus?.agents ?? []} renderItem={(agent) => (
                <List.Item style={{ padding: "4px 0" }}>
                  <Space>
                    <Badge status={agent.status === "idle" ? "success" : "processing"} />
                    <Text style={{ fontSize: 12 }}>{agent.name}</Text>
                    {agent.tasks > 0 && <Tag color="blue" style={{ fontSize: 10 }}>{agent.tasks}任务</Tag>}
                  </Space>
                </List.Item>
              )} />
            </Card>
          </Col>

          {/* Quick Backtest */}
          <Col span={12}>
            <Card size="small" title={<><PlayCircleOutlined /> 快速回测</>}>
              <Space>
                <Input placeholder="股票代码" value={btSymbol} onChange={e => setBtSymbol(e.target.value)} style={{ width: 100 }} />
                <Select value={btStrategy} onChange={setBtStrategy} style={{ width: 120 }}>
                  <Select.Option value="ma_cross">均线交叉</Select.Option>
                  <Select.Option value="rsi_rev">RSI反转</Select.Option>
                  <Select.Option value="momentum">动量策略</Select.Option>
                </Select>
                <Button type="primary" onClick={handleBacktest} loading={running}>运行</Button>
                {backtests.length > 0 && (
                  <Select
                    placeholder="选择历史"
                    style={{ width: 150 }}
                    onChange={(id) => {
                      const bt = backtests.find(b => b.id === id);
                      if (bt) {
                        setSelectedBacktest(bt);
                        setChartData(generateChartData(bt));
                      }
                    }}
                  >
                    {backtests.slice(0, 5).map(b => (
                      <Select.Option key={b.id} value={b.id}>{b.symbol} {b.strategy}</Select.Option>
                    ))}
                  </Select>
                )}
              </Space>
            </Card>
          </Col>
        </Row>

        {/* Research Agent */}
        <Card size="small" title={<><ThunderboltOutlined /> 研究智能体</>}>
          <Space>
            <Input
              placeholder="研究问题，如: 分析特斯拉近期走势和投资价值"
              value={researchQuery}
              onChange={e => setResearchQuery(e.target.value)}
              style={{ width: 500 }}
              onPressEnter={handleResearch}
            />
            <Button type="primary" onClick={handleResearch} loading={researching}>研究</Button>
          </Space>
          {researchResult && (
            <div style={{ marginTop: 12 }}>
              <Space style={{ marginBottom: 8 }}>
                <Text type="secondary">置信度: </Text>
                <Progress percent={Math.round(researchResult.confidence * 100)} size="small" style={{ width: 200 }} />
                {researchResult.top_factors && researchResult.top_factors.length > 0 && (
                  <>
                    <Text type="secondary">推荐因子: </Text>
                    {researchResult.top_factors.slice(0, 3).map(f => (
                      <Tag key={f} color="blue">{f}</Tag>
                    ))}
                  </>
                )}
              </Space>
              <Row gutter={12}>
                <Col span={12}>
                  <Text strong style={{ fontSize: 12 }}>研究结论:</Text>
                  <List size="small" dataSource={researchResult.findings}
                    renderItem={f => <List.Item style={{ padding: "2px 0" }}><Text style={{ fontSize: 12 }}>{f}</Text></List.Item>}
                  />
                </Col>
                <Col span={12}>
                  <Text strong style={{ fontSize: 12 }}>信号:</Text>
                  <Space style={{ marginTop: 4 }}>
                    {researchResult.signals.map((s, i) => <Tag key={i} color={s === "买入" ? "green" : "default"}>{s}</Tag>)}
                  </Space>
                </Col>
              </Row>
            </div>
          )}
        </Card>

        {/* Backtest Result */}
        {selectedBacktest && (
          <Card size="small" title={<><LineChartOutlined /> 回测结果: {selectedBacktest.symbol}</>}>
            <Row gutter={16}>
              <Col span={6}>
                <Statistic
                  title="总收益"
                  value={selectedBacktest.total_return}
                  suffix="%"
                  precision={2}
                  valueStyle={{ color: selectedBacktest.total_return > 0 ? "#3f8600" : "#cf1322" }}
                />
              </Col>
              <Col span={6}>
                <Statistic title="夏普比率" value={selectedBacktest.sharpe_ratio} precision={2} />
              </Col>
              <Col span={6}>
                <Statistic title="最大回撤" value={selectedBacktest.max_drawdown} suffix="%" valueStyle={{ color: "#cf1322" }} />
              </Col>
              <Col span={6}>
                <Statistic title="胜率" value={selectedBacktest.win_rate} suffix="%" precision={1} />
              </Col>
            </Row>
            <ResponsiveContainer width="100%" height={250} style={{ marginTop: 16 }}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="day" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 10 }} />
                <RechartsTooltip formatter={(value: unknown) => [`¥${Number(value).toLocaleString()}`, ""]} />
                <Legend />
                <Line type="monotone" dataKey="value" stroke="#1890ff" name="策略" dot={false} />
                <Line type="monotone" dataKey="benchmark" stroke="#999" name="基准" dot={false} strokeDasharray="5 5" />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        )}

        {/* Tabs for Factors */}
        <Tabs
          defaultActiveKey="factors"
          items={[
            { key: "factors", label: "📊 因子库", children: factorsTab },
            { key: "performance", label: "📈 因子表现", children: performanceTab },
          ]}
        />
      </Space>
    </div>
  );
}
