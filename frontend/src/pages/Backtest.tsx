import { useEffect, useState } from "react";
import {
  Row, Col, Card, Table, Button, Form, Select, DatePicker, InputNumber,
  Typography, Statistic, Tag, Spin, Divider, Progress, Tooltip, Space,
} from "antd";
import {
  ExperimentOutlined, PlayCircleOutlined, CheckCircleOutlined,
  CloseCircleOutlined, ArrowUpOutlined, ArrowDownOutlined,
} from "@ant-design/icons";
import { runBacktest, getBacktestHistory } from "../api/client";
import type { BacktestResult } from "../api/client";
import { useBacktestStore } from "../store/useAppStore";

const { Text, Title } = Typography;
const { RangePicker } = DatePicker;

const MOCK_RESULTS: BacktestResult[] = [
  {
    id: "bt001", strategy_id: "1", symbol: "RB2401",
    start_date: "2024-01-01", end_date: "2024-06-01",
    total_return: 0.342, sharpe_ratio: 1.82, max_drawdown: -0.12, win_rate: 0.58, total_trades: 156,
    equity_curve: Array.from({ length: 120 }, (_, i) => ({
      date: new Date(2024, 0, i + 1).toISOString().split("T")[0],
      value: 1000000 * (1 + i * 0.003 + (Math.random() - 0.5) * 0.02),
    })),
  },
  {
    id: "bt002", strategy_id: "4", symbol: "CU2402",
    start_date: "2024-01-01", end_date: "2024-06-01",
    total_return: 0.521, sharpe_ratio: 2.10, max_drawdown: -0.10, win_rate: 0.55, total_trades: 89,
    equity_curve: [],
  },
  {
    id: "bt003", strategy_id: "2", symbol: "AU2406",
    start_date: "2024-02-01", end_date: "2024-06-01",
    total_return: 0.186, sharpe_ratio: 1.15, max_drawdown: -0.09, win_rate: 0.62, total_trades: 203,
    equity_curve: [],
  },
];

const columns = [
  { title: "策略", dataIndex: "strategy_id", key: "strategy_id", render: (v: string) => <Text strong>策略 #{v}</Text> },
  { title: "合约", dataIndex: "symbol", key: "symbol" },
  { title: "周期", key: "period", render: (_: any, r: BacktestResult) => `${r.start_date} ~ ${r.end_date}` },
  {
    title: "累计收益", dataIndex: "total_return", key: "total_return",
    render: (v: number) => <span className={v >= 0 ? "text-green" : "text-red"}>{(v * 100).toFixed(1)}%</span>,
    sorter: (a: any, b: any) => a.total_return - b.total_return,
  },
  {
    title: "夏普", dataIndex: "sharpe_ratio", key: "sharpe_ratio",
    render: (v: number) => <span className={v >= 1 ? "text-green" : v >= 0 ? "text-yellow" : "text-red"}>{v.toFixed(2)}</span>,
    sorter: (a: any, b: any) => a.sharpe_ratio - b.sharpe_ratio,
  },
  {
    title: "最大回撤", dataIndex: "max_drawdown", key: "max_drawdown",
    render: (v: number) => <span className="text-red">{(v * 100).toFixed(1)}%</span>,
  },
  {
    title: "胜率", dataIndex: "win_rate", key: "win_rate",
    render: (v: number) => `${(v * 100).toFixed(0)}%`,
  },
  { title: "交易次数", dataIndex: "total_trades", key: "total_trades" },
  {
    title: "评分", key: "score",
    render: (_: any, r: BacktestResult) => {
      const score = Math.min(100, Math.round((r.sharpe_ratio * 20 + r.total_return * 50 + r.win_rate * 30) * 10));
      return <Tag color={score >= 70 ? "green" : score >= 50 ? "gold" : "red"}>{score}</Tag>;
    },
  },
];

export default function Backtest() {
  const { results, setResults, running, setRunning, status, setStatus } = useBacktestStore();
  const [form] = Form.useForm();
  const [selectedResult, setSelectedResult] = useState<BacktestResult | null>(null);

  useEffect(() => {
    setStatus("loading");
    getBacktestHistory()
      .then((res) => setResults(res.data))
      .catch(() => setResults(MOCK_RESULTS))
      .finally(() => setStatus("success"));
  }, []);

  const handleRun = async () => {
    setRunning(true);
    try {
      const values = await form.validateFields();
      const [start, end] = values.dateRange;
      await runBacktest({
        strategy_id: values.strategy_id,
        symbol: values.symbol,
        start_date: start.format("YYYY-MM-DD"),
        end_date: end.format("YYYY-MM-DD"),
        initial_capital: values.capital || 1000000,
      });
      // Reload results
      const res = await getBacktestHistory();
      setResults(res.data);
    } catch {
      // Mock result for demo
      setRunning(false);
    }
    setRunning(false);
  };

  return (
    <div>
      <div className="page-header">
        <h2>策略回测</h2>
      </div>

      {/* Run Backtest Card */}
      <Card bordered={false} style={{ marginBottom: 24 }}>
        <Form form={form} layout="inline" size="middle">
          <Form.Item name="strategy_id" label="策略" rules={[{ required: true }]}>
            <Select
              style={{ width: 200 }}
              options={[
                { label: "双均线趋势跟踪", value: "1" },
                { label: "RSI均值回归", value: "2" },
                { label: "Alpha因子组合", value: "4" },
                { label: "套利动量策略", value: "6" },
              ]}
            />
          </Form.Item>
          <Form.Item name="symbol" label="合约" rules={[{ required: true }]}>
            <Select style={{ width: 120 }} options={["RB2401", "CU2402", "AU2406", "MA2409"].map(s => ({ label: s, value: s }))} />
          </Form.Item>
          <Form.Item name="dateRange" label="日期范围" rules={[{ required: true }]}>
            <RangePicker />
          </Form.Item>
          <Form.Item name="capital" label="初始资金">
            <InputNumber min={100000} step={100000} defaultValue={1000000} style={{ width: 140 }} prefix="¥" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" icon={<PlayCircleOutlined />} onClick={handleRun} loading={running}>
              运行回测
            </Button>
          </Form.Item>
        </Form>
      </Card>

      {/* Result Summary */}
      {selectedResult && (
        <Card bordered={false} style={{ marginBottom: 24 }}>
          <Row gutter={[24, 16]}>
            <Col span={6}>
              <Statistic title="累计收益" value={selectedResult.total_return * 100} precision={1} suffix="%" valueStyle={{ color: "#00d4aa" }} prefix={<ArrowUpOutlined />} />
            </Col>
            <Col span={6}>
              <Statistic title="夏普比率" value={selectedResult.sharpe_ratio} precision={2} valueStyle={{ color: selectedResult.sharpe_ratio >= 1 ? "#00d4aa" : "#ffd666" }} />
            </Col>
            <Col span={6}>
              <Statistic title="最大回撤" value={selectedResult.max_drawdown * 100} precision={1} suffix="%" valueStyle={{ color: "#ff4d6a" }} prefix={<ArrowDownOutlined />} />
            </Col>
            <Col span={6}>
              <Statistic title="交易次数" value={selectedResult.total_trades} />
            </Col>
          </Row>
          <Divider />
          <Row gutter={[24, 16]}>
            <Col span={12}>
              <Text type="secondary">胜率</Text>
              <Progress percent={Math.round(selectedResult.win_rate * 100)} strokeColor="#00d4aa" size="small" />
            </Col>
            <Col span={12}>
              <Text type="secondary">卡玛比率</Text>
              <Progress
                percent={Math.min(100, Math.round((selectedResult.total_return / Math.abs(selectedResult.max_drawdown)) * 50))}
                strokeColor="#4096ff"
                size="small"
              />
            </Col>
          </Row>
        </Card>
      )}

      {/* History Table */}
      <Card
        title={<span><ExperimentOutlined style={{ marginRight: 8 }} />回测历史</span>}
        bordered={false}
      >
        <Table
          dataSource={results}
          columns={columns}
          rowKey="id"
          loading={status === "loading"}
          pagination={{ pageSize: 10 }}
          size="middle"
          onRow={(record) => ({
            onClick: () => setSelectedResult(record),
            style: { cursor: "pointer" },
          })}
        />
      </Card>
    </div>
  );
}
