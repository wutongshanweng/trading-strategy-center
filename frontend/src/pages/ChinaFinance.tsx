import { useEffect, useState } from "react";
import { Card, Table, Tag, Space, Button, Typography, Input, Spin, message, Row, Col, Statistic, Select, List, Badge, Descriptions, Tabs, Progress, Tooltip, Alert } from "antd";
import { DollarOutlined, SyncOutlined, ExperimentOutlined, BankOutlined, FundOutlined, AppstoreOutlined, ThunderboltOutlined, CheckCircleOutlined, ClockCircleOutlined, PlayCircleOutlined, PieChartOutlined } from "@ant-design/icons";
import { chinaFinanceApi, SkillInfo } from "../services/chinaFinanceApi";
import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts";

const { Title, Text } = Typography;
const CATEGORY_LABELS: Record<string, string> = {
  investment_banking: "投行", pe: "私募股权", wealth: "财富管理", fund_ops: "基金运营",
};
const CATEGORY_COLORS: Record<string, string> = {
  investment_banking: "blue", pe: "purple", wealth: "green", fund_ops: "orange",
};
const CATEGORY_ICONS: Record<string, React.ReactNode> = {
  investment_banking: <BankOutlined />,
  pe: <FundOutlined />,
  wealth: <DollarOutlined />,
  fund_ops: <AppstoreOutlined />,
};

const QUICK_SKILLS = [
  { name: "calc_irr", description: "计算IRR", category: "investment_banking" },
  { name: "stress_test", description: "压力测试", category: "pe" },
  { name: "risk_assessment", description: "风险评估", category: "wealth" },
  { name: "nav_calculation", description: "净值计算", category: "fund_ops" },
];

const DATA_STATUS_COLORS: Record<string, string> = {
  connected: "green", connecting: "orange", disconnected: "red", unknown: "default",
};

export default function ChinaFinance() {
  const [loading, setLoading] = useState(true);
  const [skills, setSkills] = useState<SkillInfo[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string | undefined>();
  const [dashboard, setDashboard] = useState<{ data_status: Record<string, string>; skills_count: number; categories: string[] } | null>(null);
  const [runningSkill, setRunningSkill] = useState<string | null>(null);
  const [skillResult, setSkillResult] = useState<Record<string, unknown> | null>(null);
  const [selectedSkill, setSelectedSkill] = useState<SkillInfo | null>(null);
  const [symbol, setSymbol] = useState("000001");
  const [financialData, setFinancialData] = useState<Record<string, unknown> | null>(null);
  const [skillHistory, setSkillHistory] = useState<{ skill: string; time: Date; status: string }[]>([]);
  const [activeTab, setActiveTab] = useState("skills");

  // Category distribution for pie chart
  const categoryDistribution = categories.map(cat => ({
    name: CATEGORY_LABELS[cat] || cat,
    value: skills.filter(s => s.category === cat).length,
    color: CATEGORY_COLORS[cat] || "#999",
  }));

  const load = async () => {
    setLoading(true);
    try {
      const s = await chinaFinanceApi.skills(selectedCategory || undefined);
      const sc = await chinaFinanceApi.skillCategories();
      const d = await chinaFinanceApi.dashboard();
      setSkills(s.data.skills);
      setCategories(sc.data.categories);
      setDashboard(d.data);
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [selectedCategory]);

  const handleRunSkill = async (skill: SkillInfo) => {
    setRunningSkill(skill.name);
    setSelectedSkill(skill);
    setSkillResult(null);
    setActiveTab("result");
    try {
      const res = await chinaFinanceApi.runSkill(skill.name, { symbol });
      setSkillResult(res.data.result);
      setSkillHistory(prev => [{ skill: skill.description, time: new Date(), status: "success" }, ...prev.slice(0, 9)]);
      message.success(`${skill.description} 执行完成`);
    } catch {
      setSkillHistory(prev => [{ skill: skill.description, time: new Date(), status: "failed" }, ...prev.slice(0, 9)]);
      message.error("执行失败");
    }
    finally { setRunningSkill(null); }
  };

  const handleGetData = async () => {
    if (!symbol) return;
    try {
      const res = await chinaFinanceApi.financialData(symbol);
      setFinancialData(res.data as unknown as Record<string, unknown>);
      message.success("数据获取成功");
    } catch { message.error("获取失败"); }
  };

  const tabItems = categories.map(cat => ({
    key: cat,
    label: <span><Tag color={CATEGORY_COLORS[cat]}>{CATEGORY_LABELS[cat] || cat}</Tag></span>,
    children: (
      <Table
        size="small"
        dataSource={skills.filter(s => s.category === cat)}
        rowKey="name"
        pagination={{ pageSize: 10, showSizeChanger: true }}
        columns={[
          { title: "技能", dataIndex: "description", width: 180 },
          { title: "参数", dataIndex: "params", width: 200,
            render: (v: string[]) => <Space wrap>{v.map(p => <Tag key={p}>{p}</Tag>)}</Space> },
          {
            title: "操作", width: 100,
            render: (_: unknown, record: SkillInfo) => (
              <Button size="small" type="primary" loading={runningSkill === record.name}
                onClick={() => handleRunSkill(record)}>执行</Button>
            ),
          },
        ]}
      />
    ),
  }));

  const dataStatusTab = (
    <Card size="small" title={<><PieChartOutlined /> 数据源状态</>}>
      <Row gutter={16}>
        <Col span={12}>
          <Title level={5} style={{ marginTop: 0 }}>数据连接状态</Title>
          <List
            size="small"
            dataSource={Object.entries(dashboard?.data_status || {})}
            renderItem={([name, status]) => (
              <List.Item style={{ padding: "8px 0" }}>
                <Space>
                  <Badge status={status === "connected" ? "success" : status === "connecting" ? "processing" : "error"} />
                  <Text>{name}</Text>
                  <Tag color={DATA_STATUS_COLORS[status] || "default"}>{status}</Tag>
                </Space>
              </List.Item>
            )}
          />
        </Col>
        <Col span={12}>
          <Title level={5} style={{ marginTop: 0 }}>技能分类分布</Title>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={categoryDistribution}
                cx="50%"
                cy="50%"
                innerRadius={40}
                outerRadius={80}
                dataKey="value"
                label={({ name, value }: { name?: string; value?: number }) => `${name || ""}: ${value ?? 0}`}
              >
                {categoryDistribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        </Col>
      </Row>
    </Card>
  );

  const quickSkillsTab = (
    <Card size="small" title={<><ThunderboltOutlined /> 快捷执行</>}>
      <Space direction="vertical" style={{ width: "100%" }}>
        <Alert
          message="快速执行常用技能"
          description={`当前股票代码: ${symbol}`}
          type="info"
          showIcon
        />
        <Row gutter={12} style={{ marginTop: 12 }}>
          {QUICK_SKILLS.map(qs => {
            const skill = skills.find(s => s.name === qs.name);
            return (
              <Col span={6} key={qs.name}>
                <Card size="small" style={{ textAlign: "center" }}>
                  <div style={{ fontSize: 24, marginBottom: 8 }}>
                    {CATEGORY_ICONS[qs.category]}
                  </div>
                  <Text strong>{qs.description}</Text>
                  <div style={{ marginTop: 8 }}>
                    <Button
                      size="small"
                      type="primary"
                      icon={<PlayCircleOutlined />}
                      loading={runningSkill === qs.name}
                      onClick={() => skill && handleRunSkill(skill)}
                    >
                      执行
                    </Button>
                  </div>
                </Card>
              </Col>
            );
          })}
        </Row>
      </Space>
    </Card>
  );

  const historyTab = (
    <Card size="small" title={<><ClockCircleOutlined /> 执行历史</>}>
      {skillHistory.length === 0 ? (
        <Text type="secondary">暂无执行记录</Text>
      ) : (
        <List
          size="small"
          dataSource={skillHistory}
          renderItem={(h) => (
            <List.Item style={{ padding: "6px 0" }}>
              <Space>
                <Badge status={h.status === "success" ? "success" : "error"} />
                <Text>{h.skill}</Text>
                <Text type="secondary" style={{ fontSize: 11 }}>
                  {h.time.toLocaleString("zh-CN")}
                </Text>
                <Tag color={h.status === "success" ? "green" : "red"}>
                  {h.status === "success" ? "成功" : "失败"}
                </Tag>
              </Space>
            </List.Item>
          )}
        />
      )}
    </Card>
  );

  return (
    <div>
      <Space direction="vertical" size="large" style={{ width: "100%" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <Space>
            <Title level={4} style={{ margin: 0 }}><BankOutlined /> A股金融研究框架</Title>
            {dashboard && (
              <Tooltip title="技能总数">
                <Badge count={dashboard.skills_count} showZero color="#1890ff">
                  <Tag icon={<AppstoreOutlined />}>Skills</Tag>
                </Badge>
              </Tooltip>
            )}
          </Space>
          <Space>
            <Input placeholder="股票代码" value={symbol} onChange={e => setSymbol(e.target.value)} style={{ width: 120 }} />
            <Button onClick={handleGetData} icon={<FundOutlined />}>财务数据</Button>
            <Button icon={<SyncOutlined />} onClick={load} loading={loading}>刷新</Button>
          </Space>
        </div>

        {/* Quick Skills Row */}
        {!loading && skills.length > 0 && (
          <Card size="small" title={<><ThunderboltOutlined /> 快捷技能</>}>
            <Space wrap>
              {QUICK_SKILLS.map(qs => {
                const skill = skills.find(s => s.name === qs.name);
                return (
                  <Tooltip key={qs.name} title={`${qs.description} (${CATEGORY_LABELS[qs.category] || qs.category})`}>
                    <Button
                      icon={CATEGORY_ICONS[qs.category]}
                      loading={runningSkill === qs.name}
                      onClick={() => skill && handleRunSkill(skill)}
                    >
                      {qs.description}
                    </Button>
                  </Tooltip>
                );
              })}
            </Space>
          </Card>
        )}

        {/* Data Status Indicators */}
        {dashboard && dashboard.data_status && Object.keys(dashboard.data_status).length > 0 && (
          <Card size="small" title={<><PieChartOutlined /> 数据源状态</>}>
            <Space wrap>
              {Object.entries(dashboard.data_status).map(([name, status]) => (
                <Tooltip key={name} title={`${name}: ${status}`}>
                  <Tag
                    color={DATA_STATUS_COLORS[status] || "default"}
                    icon={status === "connected" ? <CheckCircleOutlined /> : status === "disconnected" ? <ClockCircleOutlined /> : undefined}
                  >
                    {name}
                  </Tag>
                </Tooltip>
              ))}
            </Space>
          </Card>
        )}

        {/* Stats Row */}
        {dashboard && (
          <Row gutter={12}>
            <Col span={4}><Card size="small"><Statistic title="Skills总数" value={dashboard.skills_count} prefix={<AppstoreOutlined />} /></Card></Col>
            {categories.map(cat => (
              <Col span={4} key={cat}>
                <Card size="small">
                  <Statistic
                    title={CATEGORY_LABELS[cat] || cat}
                    value={skills.filter(s => s.category === cat).length}
                    prefix={<Tag color={CATEGORY_COLORS[cat]}>{cat}</Tag>}
                  />
                </Card>
              </Col>
            ))}
          </Row>
        )}

        {/* Financial Data */}
        {financialData && (
          <Card size="small" title={<><FundOutlined /> {symbol} 财务数据</>}>
            <Descriptions size="small" column={4}>
              {Object.entries(financialData).map(([k, v]) => (
                <Descriptions.Item key={k} label={k}>
                  <Text>{typeof v === "number" ? (Number.isInteger(v) ? v : v.toFixed(2)) : String(v)}</Text>
                </Descriptions.Item>
              ))}
            </Descriptions>
          </Card>
        )}

        {/* Skill Result */}
        {skillResult && selectedSkill && (
          <Card size="small" title={<><ExperimentOutlined /> {selectedSkill.description} 结果</>} extra={<Tag>{selectedSkill.name}</Tag>}>
            <Descriptions size="small" column={3}>
              {Object.entries(skillResult).map(([k, v]) => (
                <Descriptions.Item key={k} label={k}>
                  {typeof v === "object" ? (
                    <pre style={{ margin: 0, fontSize: 11 }}>{JSON.stringify(v, null, 1)}</pre>
                  ) : (
                    <Text style={{ color: typeof v === "number" && v > 0 ? "#3f8600" : undefined }}>
                      {typeof v === "number" ? (Number.isInteger(v) ? v : (v as number).toFixed(2)) : String(v)}
                    </Text>
                  )}
                </Descriptions.Item>
              ))}
            </Descriptions>
          </Card>
        )}

        {/* Skills Tabs */}
        <Card size="small">
          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            items={[
              { key: "skills", label: "📊 技能列表", children: (
                loading ? <Spin /> : <Tabs items={tabItems} />
              )},
              { key: "status", label: "📈 状态监控", children: dataStatusTab },
              { key: "history", label: "🕐 执行历史", children: historyTab },
            ]}
          />
        </Card>
      </Space>
    </div>
  );
}
