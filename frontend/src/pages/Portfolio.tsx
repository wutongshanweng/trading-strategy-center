import { useEffect, useState } from "react";
import {
  Row, Col, Card, Table, Typography, Statistic, Tag, Progress, Button,
  Modal, Form, InputNumber, message, Empty, Spin,
} from "antd";
import {
  PieChartOutlined, ArrowUpOutlined, ArrowDownOutlined,
  ReloadOutlined, SwapOutlined,
} from "@ant-design/icons";
import { getPortfolio, rebalancePortfolio } from "../api/client";
import type { PortfolioSummary } from "../api/client";
import { usePortfolioStore } from "../store/useAppStore";

const { Text, Title } = Typography;

const MOCK_PORTFOLIO: PortfolioSummary = {
  total_value: 12500000,
  cash: 3500000,
  invested: 9000000,
  daily_pnl: 85000,
  total_pnl: 2500000,
  positions: [
    { symbol: "RB2401", direction: "long", volume: 100, entry_price: 3890, current_price: 3950, pnl: 6000, pnl_pct: 1.54, open_time: "2024-06-01" },
    { symbol: "CU2402", direction: "short", volume: 20, entry_price: 72000, current_price: 71500, pnl: 10000, pnl_pct: 0.69, open_time: "2024-06-03" },
    { symbol: "AU2406", direction: "long", volume: 50, entry_price: 552, current_price: 558, pnl: 3000, pnl_pct: 1.09, open_time: "2024-06-05" },
    { symbol: "MA2409", direction: "short", volume: 200, entry_price: 2610, current_price: 2635, pnl: -5000, pnl_pct: -0.96, open_time: "2024-06-07" },
    { symbol: "SC2403", direction: "long", volume: 15, entry_price: 628, current_price: 635, pnl: 1050, pnl_pct: 1.11, open_time: "2024-06-02" },
  ],
  allocation: [
    { symbol: "RB2401", percent: 25 },
    { symbol: "CU2402", percent: 20 },
    { symbol: "AU2406", percent: 15 },
    { symbol: "MA2409", percent: 10 },
    { symbol: "SC2403", percent: 10 },
    { symbol: "Cash", percent: 20 },
  ],
};

const posColumns = [
  { title: "合约", dataIndex: "symbol", key: "symbol", render: (v: string) => <Text strong>{v}</Text> },
  {
    title: "方向", dataIndex: "direction", key: "direction",
    render: (v: string) => <Tag color={v === "long" ? "red" : "green"}>{v === "long" ? "多头" : "空头"}</Tag>,
  },
  { title: "数量", dataIndex: "volume", key: "volume" },
  { title: "开仓价", dataIndex: "entry_price", key: "entry_price", render: (v: number) => v.toFixed(1) },
  { title: "现价", dataIndex: "current_price", key: "current_price", render: (v: number) => v.toFixed(1) },
  {
    title: "盈亏", dataIndex: "pnl", key: "pnl",
    render: (v: number) => <span className={v >= 0 ? "text-green" : "text-red"}>{v >= 0 ? "+" : ""}{v.toLocaleString()}</span>,
    sorter: (a: any, b: any) => a.pnl - b.pnl,
  },
  {
    title: "盈亏%", dataIndex: "pnl_pct", key: "pnl_pct",
    render: (v: number) => <span className={v >= 0 ? "text-green" : "text-red"}>{(v * 100).toFixed(2)}%</span>,
  },
];

export default function Portfolio() {
  const { summary, setSummary, status, setStatus } = usePortfolioStore();
  const [rebalanceOpen, setRebalanceOpen] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    setStatus("loading");
    getPortfolio()
      .then((res) => setSummary(res.data))
      .catch(() => setSummary(MOCK_PORTFOLIO))
      .finally(() => setStatus("success"));
  }, []);

  const totalPnl = summary?.positions?.reduce((s, p) => s + p.pnl, 0) ?? 0;
  const winCount = summary?.positions?.filter((p) => p.pnl >= 0).length ?? 0;
  const totalPos = summary?.positions?.length ?? 0;

  const handleRebalance = async () => {
    message.success("再平衡指令已提交");
    setRebalanceOpen(false);
  };

  return (
    <Spin spinning={status === "loading"}>
      <div className="page-header">
        <h2>投资组合</h2>
        <Button icon={<ReloadOutlined />} onClick={() => setRebalanceOpen(true)}>
          再平衡
        </Button>
      </div>

      {/* Stats */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card size="small" bordered={false}>
            <Statistic title="总资产" value={summary?.total_value ?? 0} precision={0} prefix="¥" valueStyle={{ color: "#00d4aa" }} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card size="small" bordered={false}>
            <Statistic title="持仓市值" value={summary?.invested ?? 0} precision={0} prefix="¥" valueStyle={{ color: "#4096ff" }} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card size="small" bordered={false}>
            <Statistic title="可用资金" value={summary?.cash ?? 0} precision={0} prefix="¥" />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card size="small" bordered={false}>
            <Statistic
              title="累计盈亏"
              value={summary?.total_pnl ?? 0}
              precision={0}
              prefix={summary?.total_pnl != null && summary.total_pnl >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
              suffix="¥"
              valueStyle={{ color: (summary?.total_pnl ?? 0) >= 0 ? "#00d4aa" : "#ff4d6a" }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {/* Allocation */}
        <Col xs={24} lg={8}>
          <Card title="资产配置" bordered={false}>
            {(summary?.allocation ?? []).map((a) => (
              <div key={a.symbol} style={{ marginBottom: 12 }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                  <Text>{a.symbol}</Text>
                  <Text type="secondary">{a.percent}%</Text>
                </div>
                <Progress
                  percent={a.percent}
                  size="small"
                  strokeColor={a.symbol === "Cash" ? "#8c8c8c" : ["#1677ff", "#00d4aa", "#b37feb", "#ffd666", "#ff4d6a"][
                    (summary?.allocation ?? []).indexOf(a) % 5
                  ]}
                  showInfo={false}
                />
              </div>
            ))}
            <div style={{ marginTop: 16, textAlign: "center" }}>
              <Text type="secondary">
                使用率: {summary ? ((summary.invested / summary.total_value) * 100).toFixed(1) : 0}%
              </Text>
            </div>
          </Card>
        </Col>

        {/* Performance Metrics */}
        <Col xs={24} lg={8}>
          <Card title="风险指标" bordered={false}>
            <Row gutter={[16, 24]}>
              <Col span={12}>
                <Statistic title="夏普比率" value={1.86} precision={2} valueStyle={{ color: "#00d4aa" }} />
              </Col>
              <Col span={12}>
                <Statistic title="最大回撤" value={-8.42} precision={2} suffix="%" valueStyle={{ color: "#ff4d6a" }} />
              </Col>
              <Col span={12}>
                <Statistic title="日盈亏" value={summary?.daily_pnl ?? 0} precision={0} prefix="¥" valueStyle={{ color: (summary?.daily_pnl ?? 0) >= 0 ? "#00d4aa" : "#ff4d6a" }} />
              </Col>
              <Col span={12}>
                <Statistic title="持仓胜率" value={totalPos > 0 ? (winCount / totalPos) * 100 : 0} precision={1} suffix="%" valueStyle={{ color: "#ffd666" }} />
              </Col>
            </Row>
          </Card>
        </Col>

        {/* VaR / Correlation preview */}
        <Col xs={24} lg={8}>
          <Card title="风险预算" bordered={false}>
            <div style={{ marginBottom: 16 }}>
              <Text type="secondary" style={{ display: "block", marginBottom: 4 }}>VaR (95%, 1日)</Text>
              <Tag color="red" style={{ fontSize: 16, padding: "4px 12px" }}>¥-285,000</Tag>
              <Text type="secondary" style={{ marginLeft: 12 }}>2.3%</Text>
            </div>
            <div style={{ marginBottom: 16 }}>
              <Text type="secondary" style={{ display: "block", marginBottom: 4 }}>组合β</Text>
              <Tag color="blue" style={{ fontSize: 16, padding: "4px 12px" }}>0.87</Tag>
            </div>
            <div>
              <Text type="secondary" style={{ display: "block", marginBottom: 4 }}>相关性</Text>
              <Tag color="purple" style={{ fontSize: 16, padding: "4px 12px" }}>0.32</Tag>
              <Text type="secondary" style={{ marginLeft: 12 }}>平均</Text>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Positions */}
      <Card title={<span><SwapOutlined style={{ marginRight: 8 }} />持仓明细</span>} bordered={false}>
        <Table
          dataSource={summary?.positions ?? []}
          columns={posColumns}
          rowKey="symbol"
          pagination={false}
          size="middle"
        />
      </Card>

      {/* Rebalance Modal */}
      <Modal title="组合再平衡" open={rebalanceOpen} onOk={handleRebalance} onCancel={() => setRebalanceOpen(false)}>
        <Form form={form} layout="vertical">
          <Text type="secondary" style={{ display: "block", marginBottom: 16 }}>
            设置目标权重（合计 100%）
          </Text>
          {(summary?.allocation ?? []).filter((a) => a.symbol !== "Cash").map((a) => (
            <Form.Item key={a.symbol} label={a.symbol} initialValue={a.percent}>
              <InputNumber min={0} max={100} style={{ width: "100%" }} suffix="%" />
            </Form.Item>
          ))}
        </Form>
      </Modal>
    </Spin>
  );
}
